import pytest
from sqlalchemy.orm import sessionmaker
from backend.db import Base,make_engine
from backend.config import Settings
from backend.seed import seed
from backend.agent.service import Service
from backend.schemas import CaseRequest

@pytest.fixture
def db(tmp_path):
    e=make_engine('sqlite:///'+str(tmp_path/'test.db'));Base.metadata.create_all(e)
    factory=sessionmaker(e,expire_on_commit=False)
    with factory.begin() as s: seed(s)
    yield factory
    e.dispose()

@pytest.fixture
def config(): return Settings(_env_file=None)

def create_run(db,config,message='Please refund my charge.',target='pay_demo',key='request-0001',faults=None):
    with db.begin() as s: id=Service(s,config).create('cus_demo',CaseRequest(message=message,target_id=target,request_key=key)).id
    with db.begin() as s:
        from backend.models import Case
        c=s.get(Case,id);Service(s,config,faults=faults).run(c)
        return id
