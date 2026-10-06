import secrets, logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select, text
from backend.db import Session
from backend.config import settings
from backend.models import Case, Audit, Customer, Subscription, Payment, Order, ProviderEvent
from backend.schemas import CaseRequest, DecisionRequest, MutationRequest, CaseView
from backend.agent.service import Service, DomainError, row, view, transition
from backend.webhooks.handler import ingest, apply

logging.basicConfig(level=logging.INFO,format='%(message)s')
app=FastAPI(title='Conduit',version='0.1.0',description='Risk-aware support resolution. Test/simulator data only.')

@app.exception_handler(DomainError)
async def domain_error(request,exc): return JSONResponse(status_code=exc.status,content={'detail':exc.message})

def principal(authorization: str = Header(default='')):
    token=authorization.removeprefix('Bearer ')
    cfg=settings()
    if secrets.compare_digest(token,cfg.operator_token): return {'role':'operator','id':'operator_demo'}
    if secrets.compare_digest(token,cfg.customer_token): return {'role':'customer','id':cfg.customer_id}
    raise HTTPException(401,'Valid bearer token required')

def operator(p=Depends(principal)):
    if p['role']!='operator': raise HTTPException(403,'Operator required')
    return p

def owned(s,id,p):
    c=s.get(Case,id)
    if not c or (p['role']!='operator' and c.customer_id!=p['id']): raise HTTPException(404,'Case not found')
    return c

@app.get('/health')
def health():
    with Session() as s: s.execute(text('SELECT 1'))
    return {'status':'ok','provider':settings().payment_provider,'shadow':settings().shadow_mode}

@app.post('/cases',response_model=CaseView)
def create_case(body:CaseRequest,p=Depends(principal)):
    if p['role']!='customer': raise HTTPException(403,'Use a customer credential to create a case')
    # Persist the stable case/action key BEFORE any provider call.
    with Session.begin() as s: id=Service(s,settings()).create(p['id'],body).id
    with Session.begin() as s:
        c=s.get(Case,id); Service(s,settings()).run(c); return view(c)

@app.get('/cases',response_model=list[CaseView])
def cases(p=Depends(principal)):
    with Session() as s:
        q=select(Case).order_by(Case.created_at.desc()).limit(200)
        if p['role']=='customer': q=q.where(Case.customer_id==p['id'])
        return [view(c) for c in s.scalars(q)]

@app.get('/cases/{id}',response_model=CaseView)
def case_detail(id:str,p=Depends(principal)):
    with Session() as s: return view(owned(s,id,p))

@app.get('/cases/{id}/trajectory')
def trajectory(id:str,p=Depends(principal)):
    with Session() as s:
        owned(s,id,p)
        return [row(x) for x in s.scalars(select(Audit).where(Audit.case_id==id).order_by(Audit.timestamp,Audit.id))]

@app.post('/cases/{id}/decision',response_model=CaseView)
def decision(id:str,body:DecisionRequest,p=Depends(principal)):
    with Session.begin() as s:
        c=owned(s,id,p); Service(s,settings()).approve(c,p['role'],p['id'],body); return view(c)

@app.post('/cases/{id}/reconcile',response_model=CaseView)
def reconcile(id:str,p=Depends(principal)):
    with Session.begin() as s:
        c=owned(s,id,p)
        if c.state!='RECONCILE': raise DomainError('Case is not awaiting reconciliation')
        Service(s,settings()).run(c); return view(c)

@app.post('/cases/{id}/clarify',response_model=CaseView)
def clarify(id:str,body:CaseRequest,p=Depends(principal)):
    with Session.begin() as s:
        c=owned(s,id,p); svc=Service(s,settings()); svc.lock(c)
        if c.state!='ASK_USER': raise DomainError('Case is not awaiting clarification')
        c.message=body.message; c.target_id=body.target_id; c.address=body.address
        transition(s,c,'UNDERSTAND'); svc.run(c); return view(c)

@app.get('/customers/{id}')
def customer(id:str,p=Depends(principal)): return get_owned(Customer,id,p)
@app.get('/subscriptions/{id}')
def subscription(id:str,p=Depends(principal)): return get_owned(Subscription,id,p)
@app.get('/payments/{id}')
def payment(id:str,p=Depends(principal)): return get_owned(Payment,id,p)
@app.get('/orders/{id}')
def order(id:str,p=Depends(principal)): return get_owned(Order,id,p)

def get_owned(model,id,p):
    with Session() as s:
        obj=s.get(model,id)
        owner=obj.id if model==Customer and obj else getattr(obj,'customer_id',None)
        if not obj or (p['role']!='operator' and owner!=p['id']): raise HTTPException(404,'Not found')
        return row(obj)

# Business mutation APIs cannot bypass the case policy/approval state machine.
def execute_bound(body,p,action,target=None):
    with Session.begin() as s:
        c=owned(s,body.case_id,p)
        if c.plan.get('action')!=action or (target and c.target_id!=target): raise DomainError('Proposal does not match endpoint')
        Service(s,settings()).run(c); return view(c)
@app.post('/refunds',response_model=CaseView)
def refund(body:MutationRequest,p=Depends(principal)): return execute_bound(body,p,'refund')
@app.post('/subscriptions/{id}/cancel',response_model=CaseView)
def cancel(id:str,body:MutationRequest,p=Depends(principal)): return execute_bound(body,p,'cancel',id)
@app.post('/orders/{id}/replace',response_model=CaseView)
def replace(id:str,body:MutationRequest,p=Depends(principal)): return execute_bound(body,p,'replace',id)
@app.post('/orders/{id}/address',response_model=CaseView)
def address(id:str,body:MutationRequest,p=Depends(principal)): return execute_bound(body,p,'address',id)
@app.post('/credits',response_model=CaseView)
def credit(body:MutationRequest,p=Depends(principal)): return execute_bound(body,p,'credit')

@app.post('/webhooks/stripe')
async def stripe_webhook(request:Request,stripe_signature:str=Header(default='')):
    import stripe
    cfg=settings()
    if not cfg.stripe_webhook_secret: raise HTTPException(503,'Webhook secret not configured')
    payload=await request.body()
    if len(payload)>1_000_000: raise HTTPException(413,'Event too large')
    try: event=stripe.Webhook.construct_event(payload,stripe_signature,cfg.stripe_webhook_secret)
    except (ValueError,stripe.SignatureVerificationError): raise HTTPException(400,'Invalid signature')
    with Session.begin() as s: return ingest(s,event.to_dict())

@app.post('/provider-events/{id}/replay')
def replay(id:str,p=Depends(operator)):
    with Session.begin() as s:
        rec=s.scalar(select(ProviderEvent).where(ProviderEvent.id==id).with_for_update())
        if not rec: raise HTTPException(404,'Event not found')
        if rec.status in {'unmatched','pending'}: apply(s,rec)
        return {'id':id,'status':rec.status}
