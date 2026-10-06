"""Optional Redis wakeups; SQL is authoritative. Polling recovers lost wakeups."""
import time
from sqlalchemy import select
from backend.db import Session
from backend.config import settings
from backend.models import Case, ProviderEvent
from backend.agent.service import Service
from backend.webhooks.handler import apply

def tick():
    with Session.begin() as s:
        for event in s.scalars(select(ProviderEvent).where(ProviderEvent.status.in_(['unmatched','pending'])).limit(50)):
            apply(s,event)
        for c in s.scalars(select(Case).where(Case.state.in_(['RECONCILE','UNDERSTAND'])).limit(25)):
            Service(s,settings()).run(c)

if __name__=='__main__':
    import redis
    queue=redis.Redis.from_url(settings().redis_url) if settings().redis_url else None
    while True:
        try:
            tick()
            if queue: queue.blpop('conduit:wakeups',timeout=10)
            else: time.sleep(10)
        except Exception as exc:
            print(type(exc).__name__,flush=True); time.sleep(10)
