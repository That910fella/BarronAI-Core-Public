from __future__ import annotations
import time, glob, os
import pandas as pd
from .utils import now_et, is_power_hour
from .preset_loader import load_yaml, run_preset
from ..agents.signal_builder import SignalBuilder
from ..agents.risk_engine import RiskEngine, RiskConfig
from ..agents.trade_executor import TradeExecutor
from ..agents.journal import journal_signal, journal_plan
from .config import settings
from ..data.provider import get_provider
from ..nlp.catalyst_nlp import fetch_news as fetch_yf_news, score_catalyst
from ..nlp.benzinga import fetch_benzinga
from ..integrations.alerts import maybe_alert

WATCHLIST = os.getenv("WATCHLIST","AAPL,AMD,TSLA,NVDA,PLTR,SOFI").split(",")
PROVIDER = os.getenv("PROVIDER","yahoo").lower()

def market_snapshot() -> pd.DataFrame:
    prov = get_provider(PROVIDER)
    return prov.quote_snapshot(WATCHLIST)

def news_for(ticker: str):
    provider = os.getenv("NEWS_PROVIDER","rss").lower()
    if provider == "benzinga_direct":
        from ..nlp.benzinga import fetch_benzinga
        items = fetch_benzinga(ticker, limit=20) or []
        return items or fetch_yf_news(ticker, limit=15)
    elif provider == "polygon_benzinga":
        from ..nlp.benzinga import fetch_benzinga
        items = fetch_benzinga(ticker, limit=20) or []
        return items or fetch_yf_news(ticker, limit=15)
    else:
        return fetch_yf_news(ticker, limit=15)

def tick_once():
    df = market_snapshot()
    if df.empty:
        print(now_et(), "no data"); return

    cand = []
    for path in glob.glob("scans/presets/*.yml"):
        preset = load_yaml(path)
        hits = run_preset(df, preset)
        if not hits.empty:
            cand.append(hits)
    if not cand:
        print(now_et(), "no candidates"); return

    candidates = pd.concat(cand, ignore_index=True).drop_duplicates(subset=["ticker"])
    sb = SignalBuilder()
    rk = RiskEngine(RiskConfig(account_equity=float(os.getenv("ACCOUNT_EQUITY","50000"))))
    ex = TradeExecutor(paper_only=bool(settings.PAPER_ONLY))

    for _, row in candidates.iterrows():
        items = news_for(row["ticker"])
        cat = score_catalyst(items)
        sig = sb.build(
            ticker=row["ticker"], structure_score=0.6 + (0.1 if (float(row.get("last",0))>=float(row.get("vwap",1)) and float(row.get("last",0))>=float(row.get("ema20",1))) else 0.0), catalyst_score=cat["score"], narrative_score=0.4,
            reasons={"catalyst_reason": cat["reason"], "examples": cat["examples"][:5]}
        )
        journal_signal(sig)
        _ = maybe_alert(sig, reasons=sig.reasons)

        if not rk.can_enter():
            print(now_et(), row["ticker"], "blocked by risk/circuit"); continue

        plan = rk.make_plan(entry=float(row["last"]), atr=float(row.get("atr", 0.0) or 0.0))
        journal_plan(row["ticker"], plan)
        order = ex.submit_bracket(symbol=row["ticker"], qty=plan.size_shares,
                                  entry=float(row["last"]), stop=plan.stop, take=plan.tp1)
        print(now_et(), row["ticker"], "score=", sig.score, "|", order.get("status"))

def run_loop(interval_seconds: int = 60):
    while True:
        now = now_et()
        if is_power_hour(now):
            tick_once()
        else:
            print(now, "outside power hours — idle")
        time.sleep(interval_seconds)
