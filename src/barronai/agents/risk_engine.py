from dataclasses import dataclass
from typing import Optional

@dataclass
class RiskConfig:
    account_equity: float
    risk_per_trade_pct: float = 0.0075   # 0.75%
    daily_stop_pct: float = 0.10         # -10% day halt
    max_positions: int = 3
    max_entries_per_day: int = 4
    overnight_size_factor: float = 0.6   # overnight <= 60% of intraday

@dataclass
class EntryPlan:
    size_shares: int
    stop: float
    tp1: float
    tp2: float
    notes: str

class RiskEngine:
    def __init__(self, cfg: RiskConfig):
        self.cfg = cfg
        self.entries_today = 0
        self.open_positions = 0
        self.day_pnl = 0.0

    def can_enter(self) -> bool:
        return (self.entries_today < self.cfg.max_entries_per_day
                and self.open_positions < self.cfg.max_positions
                and self.day_pnl > -self.cfg.account_equity * self.cfg.daily_stop_pct)

    def position_size(self, entry: float, stop: float, overnight: bool=False) -> int:
        risk_dollars = self.cfg.account_equity * self.cfg.risk_per_trade_pct
        per_share_risk = max(entry - stop, 0.01)
        shares = int(risk_dollars / per_share_risk)
        if overnight:
            shares = int(shares * self.cfg.overnight_size_factor)
        return max(shares, 0)

    def make_plan(self, entry: float, atr: Optional[float]=None,
                  overnight: bool=False) -> EntryPlan:
        # simple ATR-aware SL/TP template
        sl = round(entry - (atr*0.8 if atr else entry*0.02), 4)
        tp1 = round(entry + (atr*0.8 if atr else entry*0.02), 4)
        tp2 = round(entry + (atr*1.6 if atr else entry*0.04), 4)
        size = self.position_size(entry, sl, overnight)
        notes = "overnight" if overnight else "intraday"
        return EntryPlan(size_shares=size, stop=sl, tp1=tp1, tp2=tp2, notes=notes)
