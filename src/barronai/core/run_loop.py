import pandas as pd
from ..agents import pattern_scanner as ps
from ..agents.signal_builder import SignalBuilder
from ..agents.risk_engine import RiskEngine, RiskConfig
from ..agents.trade_executor import TradeExecutor
from ..agents.journal import journal_signal, journal_plan
from .config import settings

def market_snapshot() -> pd.DataFrame:
    return pd.DataFrame([
        {"ticker":"ABC","last":4.2,"float":9_000_000,"pct_change":18,"volume":1_200_000,
         "day_high":4.25,"vwap":4.1,"spread_pct":0.5,"dollar_volume":5_000_000,"rel_volume":3.1,
         "yesterday_volume":2_000_000,"fifty_two_week_high":4.3, "atr":0.35},
        {"ticker":"XYZ","last":15.0,"float":60_000_000,"pct_change":12,"volume":2_500_000,
         "day_high":15.1,"vwap":14.9,"spread_pct":0.8,"dollar_volume":20_000_000,"rel_volume":2.2,
         "yesterday_volume":900_000,"fifty_two_week_high":15.9, "atr":0.9},
    ])

def main():
    df = market_snapshot()
    candidates = pd.concat([
        ps.scan_basic_gainer(df),
        ps.scan_low_float_hod(df),
        ps.scan_premarket_low_float(df),
        ps.scan_vwap_hold(df),
        ps.scan_52w_hod(df),
    ], ignore_index=True).drop_duplicates(subset=["ticker"]) if not df.empty else df

    sb = SignalBuilder()
    rk = RiskEngine(RiskConfig(account_equity=50_000))
    ex = TradeExecutor(paper_only=bool(settings.PAPER_ONLY))

    for _, row in candidates.iterrows():
        # placeholder scoring until NLP/narratives are wired
        structure = 0.7
        catalyst  = 0.6
        narrative = 0.4
        sig = sb.build(
            ticker=row["ticker"],
            structure_score=structure,
            catalyst_score=catalyst,
            narrative_score=narrative,
            reasons={"pattern":"auto","note":"scanner match"}
        )
        journal_signal(sig)

        if not rk.can_enter():
            print("SKIP (risk/circuit) ->", row["ticker"]); continue

        plan = rk.make_plan(entry=float(row["last"]), atr=float(row.get("atr", 0.0) or 0.0))
        journal_plan(row["ticker"], plan)

        # bracket order (dry-run by default)
        order = ex.submit_bracket(symbol=row["ticker"], qty=plan.size_shares,
                                  entry=float(row["last"]), stop=plan.stop, take=plan.tp1)
        print("ORDER:", order.get("status"), order.get("order", {}))

if __name__ == "__main__":
    main()
