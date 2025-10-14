from dataclasses import dataclass
from typing import Dict, Any
from datetime import datetime
from ..core.utils import is_power_hour, now_et

# Default weights: structure 50, catalyst 35, narrative 15
DEFAULT_WEIGHTS = {"structure": 0.50, "catalyst": 0.35, "narrative": 0.15}

@dataclass
class Signal:
    ticker: str
    score: float
    breakdown: Dict[str, float]
    reasons: Dict[str, Any]
    gated: bool

class SignalBuilder:
    def __init__(self, weights: Dict[str, float] | None = None):
        self.w = weights or DEFAULT_WEIGHTS

    def _gate_time(self, ts: datetime | None = None) -> bool:
        return is_power_hour(ts or now_et())

    def build(self, *, ticker: str,
                    structure_score: float,
                    catalyst_score: float,
                    narrative_score: float,
                    reasons: Dict[str, Any],
                    ts: datetime | None = None) -> Signal:
        gated = self._gate_time(ts)
        raw = (self.w["structure"]*structure_score +
               self.w["catalyst"] *catalyst_score  +
               self.w["narrative"]*narrative_score)
        score = raw if gated else raw * 0.5  # half credit outside power hours
        return Signal(
            ticker=ticker,
            score=round(score,4),
            breakdown={
                "structure": round(structure_score,4),
                "catalyst":  round(catalyst_score,4),
                "narrative": round(narrative_score,4),
                "weights":   self.w.copy()
            },
            reasons=reasons,
            gated=gated
        )
