import json
from types import SimpleNamespace
from backend.agent.planner import LLMPlanner,Reviewer
from backend.config import Settings
from backend.payments.provider import StripeTestProvider

class Reply:
    def raise_for_status(self): pass
    def json(self): return {'choices':[{'message':{'content':json.dumps({'intent':'refund','confidence':.9,'explanation':'Refund requested'})}}],'usage':{'total_tokens':31}}

def test_llm_schema_and_usage(monkeypatch):
    monkeypatch.setattr('httpx.post',lambda *a,**k:Reply())
    p=LLMPlanner(Settings(_env_file=None,llm_api_key='test',llm_model='test-model'))
    assert p.understand('Refund please').intent=='refund';assert p.usage['total_tokens']==31

def test_stripe_idempotency_key(monkeypatch):
    calls=[]
    class Object:
        def to_dict(self): return {'id':'re_123','status':'succeeded','livemode':False}
    class Refunds:
        def create(self,params,options): calls.append((params,options));return Object()
        def retrieve(self,ref): return Object()
    monkeypatch.setattr('stripe.StripeClient',lambda key:SimpleNamespace(v1=SimpleNamespace(refunds=Refunds())))
    p=StripeTestProvider(Settings(_env_file=None,payment_provider='stripe',stripe_secret_key='sk_test_fake'))
    assert p.refund('pi_test',100,'stable-key')['id']=='re_123'
    assert calls[0][1]['idempotency_key']=='stable-key'
    assert p.verify('re_123')['status']=='succeeded'
