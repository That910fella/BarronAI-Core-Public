import pandas as pd
from ..agents import pattern_scanner as ps
from ..agents.signal_builder import SignalBuilder
from ..agents.risk_engine import RiskEngine, RiskConfig

def main():
    # dummy market snapshot (normally from your data feed)
    df = pd.DataFrame([
        {"ticker":"ABC","last":4.2,"float":9_000_000,"pct_change":18,"volume":1_200_000,
         "day_high":4.25,"vwap":4.1,"spread_pct":0.5,"dollar_volume":5_000_000,"rel_volume":3.1,
         "yesterday_volume":2_000_000,"fifty_two_week_high":4.3},
        {"ticker":"XYZ","last":15.0,"float":60_000_000,"pct_change":12,"volume":2_500_000,
         "day_high":15.1,"vwap":14.9,"spread_pct":0.8,"dollar_volume":20_000_000,"rel_volume":2.2,
         "yesterday_volume":900_000,"fifty_two_week_high":15.9},
    ])

    scans = {
        "basic_gainer": ps.scan_basic_gainer(df).get("ticker", []),
        "low_float_hod": ps.scan_low_float_hod(df).get("ticker", []),
        "premarket_low_float": ps.scan_premarket_low_float(df).get("ticker", []),
        "vwap_hold": ps.scan_vwap_hold(df).get("ticker", []),
        "52w_hod": ps.scan_52w_hod(df).get("ticker", []),
    }
    print("SCANS:", {k:list(v) for k,v in scans.items()})

    sb = SignalBuilder()
    sig = sb.build(
        ticker="ABC",
        structure_score=0.7,   # from pattern strength (placeholder)
        catalyst_score=0.6,    # from NLP (placeholder)
        narrative_score=0.4,   # from theme model (placeholder)
        reasons={"pattern":"Low Float HOD","note":"near HOD & >10% with RVOL"},
    )
    print("SIGNAL:", sig)

    re = RiskEngine(RiskConfig(account_equity=50_000))
    print("CAN ENTER?", re.can_enter())
    plan = re.make_plan(entry=4.2, atr=0.35, overnight=False)
    print("PLAN:", plan)

if __name__ == "__main__":
    main()
