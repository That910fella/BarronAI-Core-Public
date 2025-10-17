from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import String, Float, Integer, Boolean, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

def now_utc():
    return datetime.now(timezone.utc)

class SignalRow(Base):
    __tablename__ = "signals"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    ticker: Mapped[str] = mapped_column(String(12), index=True)
    score: Mapped[float] = mapped_column(Float)
    gated: Mapped[bool] = mapped_column(Boolean)
    breakdown: Mapped[dict] = mapped_column(JSON)
    reasons: Mapped[dict] = mapped_column(JSON)

class PlanRow(Base):
    __tablename__ = "plans"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    ticker: Mapped[str] = mapped_column(String(12), index=True)
    size: Mapped[int] = mapped_column(Integer)
    entry: Mapped[float] = mapped_column(Float)
    stop: Mapped[float] = mapped_column(Float)
    tp1: Mapped[float] = mapped_column(Float)
    tp2: Mapped[float] = mapped_column(Float)
    notes: Mapped[str] = mapped_column(String(64))
