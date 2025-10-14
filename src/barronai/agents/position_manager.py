from __future__ import annotations
from dataclasses import dataclass

@dataclass
class Position:
    ticker: str
    qty: int
    entry: float
    stop: float
    take1: float
    take2: float
    last_vwap: float | None = None

def trail_stop_to_vwap(pos: Position, vwap: float, cushion_pct: float = 0.8) -> float:
    """Move stop up to (vwap - cushion%) if higher than current stop."""
    if not vwap:
        return pos.stop
    candidate = round(vwap * (1 - cushion_pct/100.0), 4)
    return max(pos.stop, candidate)
