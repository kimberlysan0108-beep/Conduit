import pytest
from concurrent.futures import ThreadPoolExecutor
from hypothesis import given, strategies as st, settings as hs, HealthCheck
from sqlalchemy import select,func
from backend.agent.service import Service,DomainError
from backend.schemas import CaseRequest,DecisionRequest
from backend.models import Payment,Case,Refund
from tests.conftest import create_run

@given(st.integers(min_value=1,max_value=12))
@hs(max_examples=15,suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_repeat_no_duplicate(db,config,repeats):
    req=CaseRequest(message='Refund my payment.',target_id='pay_demo',request_key='same-logical-action')
    for _ in range(repeats):
        with db.begin() as s: id=Service(s,config).create('cus_demo',req).id
        with db.begin() as s:
            c=s.get(Case,id);svc=Service(s,config);svc.run(c)
            if c.state=='CONFIRM': svc.approve(c,'customer','cus_demo',DecisionRequest(decision='approve'))
    with db() as s: assert s.scalar(select(func.count()).select_from(Refund))==1

def test_conflicting_request_key(db,config):
    create_run(db,config)
    with db.begin() as s:
        with pytest.raises(DomainError): Service(s,config).create('cus_demo',CaseRequest(message='different',request_key='request-0001'))

def test_concurrent_cases_single_balance(db,config):
    with db.begin() as s: s.get(Payment,'pay_demo').amount_cents=2000
    def call(i): return create_run(db,config,key='concurrent-'+str(i))
    with ThreadPoolExecutor(max_workers=4) as pool: list(pool.map(call,range(4)))
    with db() as s:
        assert s.scalar(select(func.count()).select_from(Refund))==1
        assert s.get(Payment,'pay_demo').refunded_cents==2000
