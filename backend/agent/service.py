import hashlib, json, time
from datetime import datetime, timezone
from sqlalchemy import select
from backend.models import (Customer, Subscription, Payment, Order, Shipment, FraudFlag, PolicyException, Case, Action, Refund, Credit, Approval, Audit, now)
from backend.schemas import Plan, CaseRequest, CaseView
from backend.policies.engine import decide
from backend.policies.retrieval import Retriever
from backend.risk.engine import assess, authority
from backend.agent.planner import RulesPlanner, LLMPlanner, Reviewer
from backend.tools.audit import audit, Faults
from backend.payments.provider import StripeTestProvider

class DomainError(Exception):
    def __init__(self, message, status=409): self.message=message; self.status=status

def digest(value): return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def row(obj):
    return {c.name:getattr(obj,c.name) for c in obj.__table__.columns} if obj else {}
def view(case): return CaseView(**{k:getattr(case,k) for k in CaseView.model_fields}).model_dump()

TRANSITIONS={
 'UNDERSTAND':{'GATHER','ASK_USER','ESCALATE'}, 'GATHER':{'CHECK_POLICY','RETRY','ASK_USER','ESCALATE'},
 'RETRY':{'GATHER','EXECUTE','VERIFY','ESCALATE'}, 'CHECK_POLICY':{'PLAN','ESCALATE'},
 'PLAN':{'AUTHORIZE'}, 'AUTHORIZE':{'CONFIRM','ESCALATE','EXECUTE','RESPOND','SHADOW'},
 'CONFIRM':{'GATHER','REJECTED'}, 'ESCALATE':{'GATHER','REJECTED'},
 'EXECUTE':{'VERIFY','RETRY','RECONCILE'}, 'VERIFY':{'RESPOND','RECONCILE','RETRY'},
 'RECONCILE':{'GATHER','VERIFY','ESCALATE','RESPOND'}, 'ASK_USER':{'UNDERSTAND'},
 'RESPOND':set(), 'SHADOW':set(), 'REJECTED':set()
}

def transition(s,c,state,detail=None):
    if state not in TRANSITIONS.get(c.state,set()): raise DomainError(f'Invalid transition {c.state} → {state}')
    c.state=state; audit(s,c,'state',result={'state':state,**(detail or {})})

class Service:
    def __init__(self, session, config, planner=None, faults=None):
        self.s=session; self.config=config; self.faults=faults or Faults()
        self.planner=planner or (LLMPlanner(config) if config.planner=='llm' else RulesPlanner())
    def policy_decision(self,p,e): return decide(p,e)
    def required_authority(self,p,policy,risk): return authority(p,policy,risk,self.config)
    def lock(self,c):
        # Same customer lock protects balances even across distinct support cases.
        self.s.scalar(select(Customer).where(Customer.id==c.customer_id).with_for_update())
        self.s.refresh(c)
    def create(self, customer_id, request: CaseRequest):
        if not self.s.get(Customer,customer_id): raise DomainError('Unknown customer',404)
        self.s.scalar(select(Customer).where(Customer.id==customer_id).with_for_update())
        h=digest(request.model_dump(exclude={'request_key'}))
        existing=self.s.scalar(select(Case).where(Case.customer_id==customer_id, Case.request_key==request.request_key))
        if existing:
            if existing.request_hash != h: raise DomainError('Idempotency key reused with different request')
            return existing
        c=Case(customer_id=customer_id,request_key=request.request_key,request_hash=h,message=request.message,target_id=request.target_id,address=request.address,shadow=self.config.shadow_mode)
        self.s.add(c); self.s.flush(); audit(self.s,c,'case_created',result={'state':'UNDERSTAND'})
        return c
    def read(self,c,model,id,tool):
        start=time.perf_counter(); obj=self.s.get(model,id)
        if not obj or (obj.id if model is Customer else getattr(obj,'customer_id',None))!=c.customer_id:
            audit(self.s,c,tool,{'id':id},error='not_found_or_not_owned')
            raise DomainError('Target not found for this customer',404)
        data=row(obj); audit(self.s,c,tool,{'id':id},data,latency=(time.perf_counter()-start)*1000)
        return data
    def gather(self,c,intent):
        self.faults.hit('database_timeout'); self.faults.hit('rate_limit'); self.faults.hit('malformed_response')
        e={'customer':self.read(c,Customer,c.customer_id,'get_customer')}
        flags=self.s.scalars(select(FraudFlag).where(FraudFlag.customer_id==c.customer_id)).all()
        e['fraud_score']=max([f.score for f in flags],default=0)
        audit(self.s,c,'fraud_check',result={'score':e['fraud_score']})
        if intent=='refund':
            self.faults.hit('payment_timeout')
            e['payment']=self.read(c,Payment,c.target_id,'get_payment')
            if e['payment']['subscription_id']:
                e['subscription']=self.read(c,Subscription,e['payment']['subscription_id'],'get_subscription')
            dup=e['payment'].get('duplicate_of')
            if dup:
                original=self.read(c,Payment,dup,'get_payment')
                e['duplicate_verified']=original['status']=='succeeded' and original['amount_cents']==e['payment']['amount_cents'] and original['id']!=c.target_id
        elif intent=='cancel': e['subscription']=self.read(c,Subscription,c.target_id,'get_subscription')
        elif intent in {'status','replace','address'}:
            e['order']=self.read(c,Order,c.target_id,'get_order')
            e['shipments']=[row(x) for x in self.s.scalars(select(Shipment).where(Shipment.order_id==c.target_id))]
            audit(self.s,c,'get_shipments',result={'shipments':e['shipments']})
        elif intent=='credit' and c.target_id!=c.customer_id: raise DomainError('Credit target must be own customer',404)
        ex=self.s.scalars(select(PolicyException).where(PolicyException.customer_id==c.customer_id,PolicyException.target_id==c.target_id,PolicyException.action==intent)).all()
        valid=[x for x in ex if datetime.fromisoformat(x.expires_at)>datetime.now(timezone.utc)]
        if valid: e['exception']=row(max(valid,key=lambda x:x.max_amount_cents))
        if intent=='credit':
            e['credits_already_issued']=sum(x.amount_cents for x in self.s.scalars(select(Credit).where(Credit.customer_id==c.customer_id)))
        if 'stale_crm' in self.faults.names:
            # A source freshness marker is authoritative operational metadata.
            e['stale']=True
        self.faults.hit('retrieval_failure')
        e['policy_documents']=Retriever(self.config).search(c.message)
        audit(self.s,c,'lookup_policy',{'query':c.message}, {'documents':e['policy_documents']})
        return e
    def run(self,c):
        self.lock(c)
        if c.state in {'RESPOND','REJECTED','SHADOW','ASK_USER','CONFIRM','ESCALATE'}: return c
        if c.state=='RECONCILE':
            existing=self.s.scalar(select(Action).where(Action.case_id==c.id))
            if existing:
                transition(self.s,c,'VERIFY')
                self.verify(c,existing); return c
            transition(self.s,c,'GATHER')
        if c.state=='UNDERSTAND':
            try:
                u=self.planner.understand(c.message)
                audit(self.s,c,'understand',result={**u.model_dump(),'usage':getattr(self.planner,'usage',{})})
            except Exception as ex:
                transition(self.s,c,'ESCALATE',{'reason':'Planner unavailable or malformed output'})
                c.result={'message':'A human must review this request.'}; return c
            c.evidence={'understanding':u.model_dump()}
            if u.intent=='clarify' or u.confidence<.7 or not c.target_id:
                transition(self.s,c,'ASK_USER'); c.result={'message':'Please specify one supported action and its payment, subscription, or order ID.'}; return c
            transition(self.s,c,'GATHER')
        u=c.evidence['understanding']; failures=0
        while True:
            try: e=self.gather(c,u['intent']); break
            except (TimeoutError, httpx_errors()) as ex:
                failures+=1; audit(self.s,c,'gather',error=type(ex).__name__)
                if failures>=2:
                    transition(self.s,c,'ESCALATE'); c.result={'message':'Business systems unavailable; human review required.'}; return c
                transition(self.s,c,'RETRY'); transition(self.s,c,'GATHER')
            except DomainError:
                transition(self.s,c,'ASK_USER'); c.result={'message':'Please provide a valid target belonging to your account.'}; return c
        c.evidence={**e,'understanding':u}
        if e.get('stale'):
            transition(self.s,c,'ESCALATE'); c.result={'message':'Source freshness is uncertain; human review required.'}; return c
        amount=0
        if u['intent']=='refund': amount=e['payment']['amount_cents']-e['payment']['refunded_cents']
        if u['intent']=='replace': amount=e['order']['amount_cents']
        if u['intent']=='credit': amount=max(0,e.get('exception',{}).get('max_amount_cents',0)-e.get('credits_already_issued',0))
        # A modified amount is bound to a plan and cannot be increased by an operator.
        if c.plan and c.plan.get('amount_cents',0)>0: amount=min(amount,c.plan['amount_cents'])
        p=Plan(action=u['intent'],target_id=c.target_id,amount_cents=amount,address=c.address)
        transition(self.s,c,'CHECK_POLICY')
        policy=self.policy_decision(p,e); audit(self.s,c,'policy',result=policy.json())
        transition(self.s,c,'PLAN'); c.plan=p.model_dump()
        risk=assess(amount,e['customer']['account_age_days'],e['fraud_score'],u['confidence'],failures)
        required=self.required_authority(p,policy,risk)
        c.evidence={**c.evidence,'policy':policy.json(),'risk':risk.json(),'authorization':required}
        transition(self.s,c,'AUTHORIZE',{'required':required,'risk':risk.json()})
        if required=='DENY':
            transition(self.s,c,'ESCALATE'); c.result={'message':policy.explanation}; return c
        if self.config.reviewer_model and (required=='HUMAN' or risk.score>=.3):
            try: review=Reviewer(self.config).review(c.plan,c.evidence)
            except Exception: review={'decision':'escalate','reason':'Reviewer unavailable'}
            audit(self.s,c,'reviewer',result=review)
            if review['decision']!='approve':
                transition(self.s,c,'ESCALATE'); c.result={'message':'Reviewer requested human investigation.'}; return c
        if c.shadow:
            transition(self.s,c,'SHADOW'); c.result={'message':'Prediction recorded; no business mutation performed.','predicted_action':c.plan}; return c
        approvals=self.s.scalars(select(Approval).where(Approval.case_id==c.id,Approval.plan_hash==digest(c.plan),Approval.decision=='approve')).all()
        roles={a.role for a in approvals}
        if required=='HUMAN' and 'operator' not in roles:
            transition(self.s,c,'ESCALATE'); c.result={'message':'Human approval is required.'}; return c
        if required=='CONFIRM' and not roles & {'customer','operator'}:
            transition(self.s,c,'CONFIRM'); c.result={'message':'Please confirm the proposed action.'}; return c
        if required=='READ':
            transition(self.s,c,'RESPOND'); c.result={'message':'Order status retrieved.','order':e['order'],'shipments':e['shipments']}; return c
        pending=self.s.scalar(select(Action).join(Case,Action.case_id==Case.id).where(Case.customer_id==c.customer_id,Action.case_id!=c.id,Action.status=='pending'))
        if pending:
            transition(self.s,c,'ESCALATE'); c.result={'message':'An earlier action has an uncertain outcome; reconcile it first.'}; return c
        transition(self.s,c,'EXECUTE')
        self.execute(c,p,required)
        return c
    def execute(self,c,p,required):
        key=f"conduit:{c.id}:{digest(c.plan)}"
        a=self.s.scalar(select(Action).where(Action.idempotency_key==key))
        if not a:
            a=Action(case_id=c.id,idempotency_key=key,request_hash=digest(c.plan),action=p.action)
            self.s.add(a); self.s.flush()
        if a.request_hash!=digest(c.plan): raise DomainError('Action idempotency conflict')
        start=time.perf_counter()
        try:
            if a.status=='pending':
                if p.action=='refund':
                    payment=self.s.get(Payment,p.target_id)
                    existing=self.s.scalar(select(Refund).where(Refund.action_id==a.id))
                    if not existing:
                        if self.config.payment_provider=='stripe':
                            if not payment.provider_id: raise ValueError('Stripe payment ID is missing')
                            remote=StripeTestProvider(self.config).refund(payment.provider_id,p.amount_cents,key)
                        else: remote={'id':'sim_'+a.id,'status':'succeeded'}
                        self.s.add(Refund(payment_id=payment.id,action_id=a.id,amount_cents=p.amount_cents,provider_reference=remote['id'],status=remote['status']))
                        payment.refunded_cents+=p.amount_cents
                        a.provider_reference=remote['id']
                elif p.action=='cancel':
                    sub=self.s.get(Subscription,p.target_id)
                    sub.status='cancelled'; sub.cancelled_at=sub.cancelled_at or now()
                elif p.action=='replace': self.s.get(Order,p.target_id).replaced=True
                elif p.action=='address': self.s.get(Order,p.target_id).address=p.address
                elif p.action=='credit': self.s.add(Credit(customer_id=c.customer_id,action_id=a.id,amount_cents=p.amount_cents))
                a.status='accepted'; a.result={'action':p.action,'amount_cents':p.amount_cents}
                self.s.flush()
                # Simulates timeout AFTER provider accepted the mutation.
                self.faults.hit('after_commit_timeout')
            audit(self.s,c,p.action,c.plan,a.result,required,key,latency=(time.perf_counter()-start)*1000)
            transition(self.s,c,'VERIFY'); self.verify(c,a)
        except Exception as ex:
            audit(self.s,c,p.action,c.plan,authorization=required,key=key,error=type(ex).__name__)
            transition(self.s,c,'RECONCILE'); c.result={'message':'Outcome uncertain; reconciliation is required before reporting success.'}
    def verify(self,c,a):
        p=Plan.model_validate(c.plan)
        try:
            self.faults.hit('delayed_webhook'); self.faults.hit('verification_timeout')
            if a.status=='pending':
                # A lost Stripe response is retried using the SAME provider key.
                if p.action=='refund' and self.config.payment_provider=='stripe':
                    if (datetime.now(timezone.utc)-datetime.fromisoformat(c.created_at)).total_seconds()>23*3600:
                        raise ValueError('Provider idempotency retry window exceeded; investigate manually')
                    payment=self.s.get(Payment,p.target_id)
                    remote=StripeTestProvider(self.config).refund(payment.provider_id,p.amount_cents,a.idempotency_key)
                    existing=self.s.scalar(select(Refund).where(Refund.action_id==a.id))
                    if not existing:
                        self.s.add(Refund(payment_id=payment.id,action_id=a.id,amount_cents=p.amount_cents,provider_reference=remote['id'],status=remote['status']))
                        payment.refunded_cents+=p.amount_cents
                    a.provider_reference=remote['id']; a.status='accepted'; self.s.flush()
                else: raise ValueError('No accepted action to verify')
            ok=False
            if p.action=='refund':
                refund=self.s.scalar(select(Refund).where(Refund.action_id==a.id))
                if refund and self.config.payment_provider=='stripe':
                    remote=StripeTestProvider(self.config).verify(a.provider_reference)
                    refund.status=remote['status']
                ok=bool(refund and refund.status=='succeeded' and refund.amount_cents==p.amount_cents)
            elif p.action=='cancel': ok=self.s.get(Subscription,p.target_id).status=='cancelled'
            elif p.action=='replace': ok=self.s.get(Order,p.target_id).replaced
            elif p.action=='address': ok=self.s.get(Order,p.target_id).address==p.address
            elif p.action=='credit': ok=bool(self.s.scalar(select(Credit).where(Credit.action_id==a.id)))
            audit(self.s,c,'verify',result={'verified':ok})
            if not ok: raise ValueError('Provider state not yet successful')
            a.status='verified'; transition(self.s,c,'RESPOND'); c.result={'message':'Action completed and verified.','action':p.action,'amount_cents':p.amount_cents,'provider_reference':a.provider_reference}
        except Exception as ex:
            audit(self.s,c,'verify',error=type(ex).__name__)
            transition(self.s,c,'RECONCILE'); c.result={'message':'Unable to verify completion. Retry reconciliation or request operator investigation.'}
    def approve(self,c,role,actor,request):
        self.lock(c)
        if c.state not in {'CONFIRM','ESCALATE'}: raise DomainError('Case is not awaiting approval')
        if role=='customer' and (c.state!='CONFIRM' or request.decision=='modify'): raise DomainError('Operator authority required',403)
        if request.decision=='reject':
            self.s.add(Approval(case_id=c.id,plan_hash=digest(c.plan),actor=actor,role=role,decision='reject'))
            audit(self.s,c,'operator_decision' if role=='operator' else 'customer_decision',result={'decision':'reject','note':request.note})
            transition(self.s,c,'REJECTED'); c.result={'message':'Proposed action rejected.'}; return c
        if not c.plan: raise DomainError('No actionable proposal; investigate this case first')
        if request.decision=='modify':
            if role!='operator' or c.plan['action'] not in {'refund','credit'}: raise DomainError('Only operator can reduce refund or credit',403)
            if not request.amount_cents or request.amount_cents>c.plan['amount_cents']: raise DomainError('Modified amount must be a positive reduction')
            c.plan={**c.plan,'amount_cents':request.amount_cents}
        self.s.add(Approval(case_id=c.id,plan_hash=digest(c.plan),actor=actor,role=role,decision='approve'))
        audit(self.s,c,'approval',result={'role':role,'actor':actor,'decision':request.decision,'note':request.note,'plan_hash':digest(c.plan)})
        self.s.flush(); transition(self.s,c,'GATHER')
        return self.run(c)

def httpx_errors():
    import httpx
    return httpx.HTTPError
