from __future__ import annotations
from dataclasses import dataclass
from typing import Literal, Optional

Side = Literal["buy", "sell"]

def round_to_tick(price: float, tick: float = 0.01) -> float:
    if tick <= 0:
        return float(price)
    steps = round(price / tick)
    return round(steps * tick, 10)

@dataclass
class ExitSpec:
    take_profit: Optional[float] = None
    stop_loss: Optional[float] = None
    stop_limit: Optional[float] = None

def _assert_pos(x: float | None, name: str) -> None:
    if x is None or x <= 0:
        raise ValueError(f"{name} must be > 0")

def compute_exits(
    *,
    side: Side,
    basis: float,
    mode: Literal["absolute", "percent", "atr"],
    take_profit: Optional[float] = None,
    stop_loss: Optional[float] = None,
    stop_limit: Optional[float] = None,
    take_profit_pct: Optional[float] = None,
    stop_loss_pct: Optional[float] = None,
    atr: Optional[float] = None,
    atr_mult_tp: Optional[float] = None,
    atr_mult_sl: Optional[float] = None,
    tick_size: float = 0.01,
) -> ExitSpec:
    _assert_pos(basis, "basis")
    _assert_pos(tick_size, "tick_size")
    sgn = 1 if side == "buy" else -1

    if mode == "absolute":
        if take_profit is None or stop_loss is None:
            raise ValueError("absolute mode requires take_profit and stop_loss")
        tp = round_to_tick(float(take_profit), tick_size)
        sl = round_to_tick(float(stop_loss), tick_size)
        sl_limit = round_to_tick(float(stop_limit), tick_size) if stop_limit else None
    elif mode == "percent":
        _assert_pos(abs(take_profit_pct or 0.0), "take_profit_pct")
        _assert_pos(abs(stop_loss_pct or 0.0), "stop_loss_pct")
        tp = round_to_tick(basis * (1 + sgn * float(take_profit_pct)), tick_size)
        sl = round_to_tick(basis * (1 - sgn * float(stop_loss_pct)), tick_size)
        sl_limit = None
    elif mode == "atr":
        _assert_pos(atr or 0.0, "atr")
        _assert_pos(abs(atr_mult_tp or 0.0), "atr_mult_tp")
        _assert_pos(abs(atr_mult_sl or 0.0), "atr_mult_sl")
        tp = round_to_tick(basis + sgn * float(atr_mult_tp) * float(atr), tick_size)
        sl = round_to_tick(basis - sgn * float(atr_mult_sl) * float(atr), tick_size)
        sl_limit = None
    else:
        raise ValueError(f"unknown mode: {mode}")

    if side == "buy" and not (tp > basis > sl):
        raise ValueError(f"invalid exits for long: tp={tp}, basis={basis}, sl={sl}")
    if side == "sell" and not (tp < basis < sl):
        raise ValueError(f"invalid exits for short: tp={tp}, basis={basis}, sl={sl}")

    if side == "buy" and not (tp > sl):
        raise ValueError("take_profit must be > stop_loss for long")
    if side == "sell" and not (tp < sl):
        raise ValueError("take_profit must be < stop_loss for short")

    return ExitSpec(take_profit=tp, stop_loss=sl, stop_limit=sl_limit)
