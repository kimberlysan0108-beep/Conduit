import pytest
from sqlalchemy import select,func
from backend.tools.audit import Faults
from backend.models import Payment,Case,Refund,Action
from backend.agent.service import Service
from tests.conftest import create_run

@pytest.mark.parametrize('fault',['payment_timeout','database_timeout','rate_limit','malformed_response','retrieval_failure'])
def test_safe_gather_retry(db,config,fault):
    with db.begin() as s: s.get(Payment,'pay_demo').amount_cents=2000
    id=create_run(db,config,faults=Faults([fault]))
    with db() as s: assert s.get(Case,id).state=='RESPOND'

@pytest.mark.parametrize('fault',['after_commit_timeout','delayed_webhook','verification_timeout'])
def test_uncertain_then_reconcile_once(db,config,fault):
    with db.begin() as s: s.get(Payment,'pay_demo').amount_cents=2000
    faults=Faults([fault]);id=create_run(db,config,faults=faults)
    with db.begin() as s:
        c=s.get(Case,id);assert c.state=='RECONCILE'
        Service(s,config,faults=faults).run(c);assert c.state=='RESPOND'
        assert s.scalar(select(func.count()).select_from(Refund))==1

def test_stale_authoritative_source_escalates(db,config):
    id=create_run(db,config,faults=Faults(['stale_crm']))
    with db() as s: assert s.get(Case,id).state=='ESCALATE'

def test_other_uncertain_action_blocks_spending(db,config):
    with db.begin() as s: s.get(Payment,'pay_demo').amount_cents=2000
    with db.begin() as s:
        from backend.schemas import CaseRequest
        c=Service(s,config).create('cus_demo',CaseRequest(message='Refund',target_id='pay_demo',request_key='old-action'))
        s.add(Action(case_id=c.id,idempotency_key='uncertain',request_hash='x',action='refund',status='pending'))
    id=create_run(db,config)
    with db() as s:
        assert s.get(Case,id).state=='ESCALATE';assert s.get(Payment,'pay_demo').refunded_cents==0

def test_provider_processed_then_lost_response(db,config,monkeypatch):
    accepted={};calls=[]
    class Provider:
        def __init__(self,cfg): pass
        def refund(self,payment_id,amount,key):
            calls.append(key)
            if key not in accepted:
                accepted[key]={'id':'re_mock','status':'succeeded'}
                raise TimeoutError('response lost after acceptance')
            return accepted[key]
        def verify(self,reference): return {'id':reference,'status':'succeeded'}
    monkeypatch.setattr('backend.agent.service.StripeTestProvider',Provider)
    config.payment_provider='stripe';config.stripe_secret_key='sk_test_mock'
    with db.begin() as s:
        p=s.get(Payment,'pay_demo');p.amount_cents=2000;p.provider_id='pi_mock'
    id=create_run(db,config)
    with db.begin() as s:
        c=s.get(Case,id);assert c.state=='RECONCILE'
        Service(s,config).run(c);assert c.state=='RESPOND'
        assert s.get(Payment,'pay_demo').refunded_cents==2000
        assert s.scalar(select(func.count()).select_from(Refund))==1
    assert len(accepted)==1 and len(calls)==2 and calls[0]==calls[1]
