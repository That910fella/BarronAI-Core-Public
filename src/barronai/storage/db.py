from __future__ import annotations
import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DEFAULT_URL = os.getenv("DATABASE_URL", "sqlite:///tmp/barronai.db")

class Base(DeclarativeBase): pass

_engine = create_engine(DEFAULT_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False, expire_on_commit=False)

@contextmanager
def session():
    s = SessionLocal()
    try:
        yield s
        s.commit()
    except:
        s.rollback()
        raise
    finally:
        s.close()

def create_all():
    from .models import SignalRow, PlanRow  # noqa
    Base.metadata.create_all(_engine)
