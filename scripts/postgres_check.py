"""CI-only PostgreSQL row-lock/concurrent balance regression."""
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy import select,func
from backend.db import Session
from backend.models import Payment,Case,Refund
from backend.config import settings
from backend.agent.service import Service
from backend.schemas import CaseRequest
with Session.begin() as s: s.get(Payment,'pay_demo').amount_cents=2000

def run(i):
    with Session.begin() as s: id=Service(s,settings()).create('cus_demo',CaseRequest(message='Refund my payment.',target_id='pay_demo',request_key='postgres-concurrent-'+str(i))).id
    with Session.begin() as s: Service(s,settings()).run(s.get(Case,id))
with ThreadPoolExecutor(max_workers=5) as p: list(p.map(run,range(5)))
with Session() as s:
    assert s.scalar(select(func.count()).select_from(Refund))==1
    assert s.get(Payment,'pay_demo').refunded_cents==2000
print('PostgreSQL concurrency invariant passed')
