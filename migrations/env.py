from alembic import context
from backend.db import make_engine, Base
from backend.config import settings
import backend.models
with make_engine(settings().database_url).connect() as connection:
    context.configure(connection=connection,target_metadata=Base.metadata,render_as_batch=connection.dialect.name=='sqlite')
    with context.begin_transaction(): context.run_migrations()
