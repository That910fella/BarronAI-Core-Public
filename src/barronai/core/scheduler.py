from __future__ import annotations
import time, glob
import pandas as pd
from .utils import now_et, is_power_hour
from .preset_loader import load_yaml, run_preset
from ..agents.signal_builder import SignalBuilder
from ..agents.risk_engine import RiskEngine, RiskConfig
from ..agents.trade_executor import TradeExecutor
from ..agents.journal import journal_signal, journal_plan
from .config import settings

def market_snapshot() -> pd.DataFrame:
    # TODO: replace with real feed; keep columns consistent with scanners
    return pd.DataFrame([
        {"ticker":"ABC","last":4.2,"float":9_000_000,"pct_change":18,"volume":1_200_000,
         "day_high":4.25,"vwap":4.1,"spread_pct":0.5,"dollar_volume":5_000_000,"rel_volume":3.1,
         "yesterday_volume":2_000_000,"fifty_two_week_high":4.3, "atr":0.35},
    ])

def tick_once():
    df = market_snapshot()
    # run all presets
    cand = []
    for path in glob.glob("scans/presets/*.yml"):
        preset = load_yaml(path)
        hits = run_preset(df, preset)
        if not hits.empty:
            cand.append(hits)
    if not cand:
        return
    candidates = pd.concat(cand, ignore_index=True).drop_duplicates(subset=["ticker"])
    sb = SignalBuilder()
    rk = RiskEngine(RiskConfig(account_equity=50_000))
    ex = TradeExecutor(paper_only=bool(settings.PAPER_ONLY))

    for _, row in candidates.iterrows():
        sig = sb.build(
            ticker=row["ticker"], structure_score=0.7, catalyst_score=0.6, narrative_score=0.4,
            reasons={"pattern":"preset","note":"yaml preset match"}
        )
        journal_signal(sig)
        if not rk.can_enter():
            continue
        plan = rk.make_plan(entry=float(row["last"]), atr=float(row.get("atr", 0.0) or 0.0))
        journal_plan(row["ticker"], plan)
        order = ex.submit_bracket(symbol=row["ticker"], qty=plan.size_shares,
                                  entry=float(row["last"]), stop=plan.stop, take=plan.tp1)
        print(now_et(), "ORDER:", order.get("status"), order.get("order", {}))

def run_loop(interval_seconds: int = 60):
    while True:
        now = now_et()
        if is_power_hour(now):
            tick_once()
        else:
            print(now, "outside power hours — idle")
        time.sleep(interval_seconds)
