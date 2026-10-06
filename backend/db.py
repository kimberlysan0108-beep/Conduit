import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from backend.config import settings

class Base(DeclarativeBase):
    pass

def make_engine(url):
    kw = {"connect_args": {"check_same_thread": False, "timeout": 30}} if url.startswith("sqlite") else {}
    engine = create_engine(url, **kw)
    if url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def sqlite_options(conn, record):
            conn.isolation_level = None
            conn.execute("PRAGMA foreign_keys=ON")
        @event.listens_for(engine, "begin")
        def begin(conn):
            # Serialize writers in local SQLite; PostgreSQL uses row locks.
            conn.exec_driver_sql("BEGIN IMMEDIATE")
    return engine

engine = make_engine(settings().database_url)
Session = sessionmaker(engine, expire_on_commit=False)
