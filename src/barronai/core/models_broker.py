from __future__ import annotations
from typing import Literal, Optional
from pydantic import BaseModel, Field, conint, confloat

Side = Literal["buy", "sell"]
TIF = Literal["day", "gtc"]

class BracketPercentRequest(BaseModel):
    ticker: str = Field(..., examples=["TSLA"])
    side: Side
    qty: conint(gt=0) = 1
    basis: confloat(gt=0) = Field(..., description="Entry price reference")
    take_profit_pct: confloat(gt=0) = 0.03
    stop_loss_pct: confloat(gt=0) = 0.02
    tif: TIF = "day"
    extended_hours: bool = False

class BracketAbsoluteRequest(BaseModel):
    ticker: str
    side: Side
    qty: conint(gt=0) = 1
    take_profit: confloat(gt=0)
    stop_loss: confloat(gt=0)
    stop_limit: Optional[confloat(gt=0)] = None
    tif: TIF = "day"
    extended_hours: bool = False

class TrailingStopRequest(BaseModel):
    ticker: str
    side: Side
    qty: conint(gt=0) = 1
    trail_percent: confloat(gt=0) | None = None
    trail_price: confloat(gt=0) | None = None
    tif: TIF = "day"
    extended_hours: bool = False
