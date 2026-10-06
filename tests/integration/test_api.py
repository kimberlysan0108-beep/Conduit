import hashlib,hmac,time,json
from fastapi.testclient import TestClient
from backend import main
from backend.config import Settings

def client(db,monkeypatch):
    monkeypatch.setattr(main,'Session',db)
    monkeypatch.setattr(main,'settings',lambda:Settings(_env_file=None,stripe_webhook_secret='whsec_test'))
    return TestClient(main.app)

def test_authenticated_case_flow(db,monkeypatch):
    c=client(db,monkeypatch);h={'Authorization':'Bearer local-customer-change-me'}
    assert c.get('/cases').status_code==401
    r=c.post('/cases',headers=h,json={'message':'Refund my payment.','target_id':'pay_demo','request_key':'api-request'})
    assert r.status_code==200;id=r.json()['id'];assert r.json()['state']=='CONFIRM'
    assert c.post('/refunds',headers=h,json={'case_id':id}).json()['state']=='CONFIRM'
    r=c.post(f'/cases/{id}/decision',headers=h,json={'decision':'approve'})
    assert r.json()['state']=='RESPOND'
    assert len(c.get(f'/cases/{id}/trajectory',headers=h).json())>8

def test_webhook_signature(db,monkeypatch):
    c=client(db,monkeypatch)
    payload=json.dumps({'id':'evt_signed','created':10,'livemode':False,'type':'refund.updated','data':{'object':{'object':'refund','id':'re_unknown','status':'pending'}}})
    assert c.post('/webhooks/stripe',content=payload).status_code==400
    t=int(time.time());sig=hmac.new(b'whsec_test',f'{t}.{payload}'.encode(),hashlib.sha256).hexdigest()
    assert c.post('/webhooks/stripe',content=payload,headers={'Stripe-Signature':f't={t},v1={sig}'}).status_code==200

def test_mutation_endpoint_cannot_change_target(db,monkeypatch):
    c=client(db,monkeypatch);h={'Authorization':'Bearer local-customer-change-me'}
    id=c.post('/cases',headers=h,json={'message':'Refund my payment.','target_id':'pay_demo','request_key':'api-request'}).json()['id']
    assert c.post('/subscriptions/sub_demo/cancel',headers=h,json={'case_id':id}).status_code==409
