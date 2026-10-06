import json, logging, time
from backend.models import Audit
log=logging.getLogger('conduit')

def audit(session, case, tool, arguments=None, result=None, authorization='READ', key=None, error=None, latency=0):
    record=Audit(case_id=case.id,tool_name=tool,arguments=arguments or {},result=result or {},authorization=authorization,idempotency_key=key,error=error,latency_ms=latency)
    session.add(record)
    # Structured operational logs exclude customer messages, addresses and tokens.
    log.info(json.dumps({'case_id':case.id,'tool':tool,'authorization':authorization,'latency_ms':latency,'error':error}))

class Faults:
    """Only constructed by tests/benchmark; no public API accepts fault controls."""
    def __init__(self, names=()): self.names=list(names); self.used=set()
    def hit(self,name):
        if name in self.names and name not in self.used:
            self.used.add(name); raise TimeoutError(name)
