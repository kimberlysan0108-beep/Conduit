from sqlalchemy import select,func
from backend.models import *
from backend.webhooks.handler import ingest,apply
from backend.agent.service import DomainError
import pytest

def event(id='evt_1',created=10,status='succeeded'):
    return {'id':id,'created':created,'livemode':False,'type':'refund.updated','data':{'object':{'id':'re_test','object':'refund','status':status}}}

def test_dedup_out_of_order_and_replay(db):
    with db.begin() as s:
        c=Case(customer_id='cus_demo',request_key='wh-case',request_hash='x',message='refund');s.add(c);s.flush()
        a=Action(case_id=c.id,idempotency_key='wh-action',request_hash='x',action='refund');s.add(a);s.flush()
        s.add(Refund(payment_id='pay_demo',action_id=a.id,amount_cents=100,provider_reference='re_test',status='pending'))
        s.get(Payment,'pay_demo').refunded_cents=100;s.flush()
        assert ingest(s,event())['status']=='applied'
        assert ingest(s,event())['duplicate']
        assert ingest(s,event('evt_old',1,'pending'))['status']=='stale'
        assert s.scalar(select(Refund)).status=='succeeded'
        assert s.scalar(select(func.count()).select_from(ProviderEvent))==2

def test_unmatched_event_durable(db):
    with db.begin() as s: assert ingest(s,event())['status']=='unmatched'
    with db() as s: assert s.get(ProviderEvent,'evt_1').status=='unmatched'

def test_live_event_denied(db):
    e=event();e['livemode']=True
    with db.begin() as s:
        with pytest.raises(DomainError): ingest(s,e)
