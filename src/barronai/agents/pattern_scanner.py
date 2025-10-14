import pandas as pd

# ---- Global universe gates (we also enforce in signal/risk) ----
PRICE_MIN = 0.50
PRICE_MAX = 20.00
FLOAT_MAX = 50_000_000

def _liq_guards(df: pd.DataFrame,
                spread_max_pct: float = 1.5,
                min_dollar_volume: int = 1_000_000,
                rel_volume_min: float = 1.5) -> pd.DataFrame:
    cols = {"spread_pct","dollar_volume","rel_volume"}
    missing = [c for c in cols if c not in df.columns]
    if missing:
        # if data source doesn't have these yet, return df unchanged (dev mode)
        return df.copy()
    m = (
        (df["spread_pct"] <= spread_max_pct) &
        (df["dollar_volume"] >= min_dollar_volume) &
        (df["rel_volume"] >= rel_volume_min)
    )
    return df[m].copy()

def _universe(df: pd.DataFrame) -> pd.DataFrame:
    cols = {"last","float"}
    missing = [c for c in cols if c not in df.columns]
    if missing:
        return df.copy()
    return df[(df["last"].between(PRICE_MIN, PRICE_MAX)) & (df["float"] <= FLOAT_MAX)].copy()

# -------- Presets you provided (cleaned) --------

def scan_basic_gainer(df: pd.DataFrame) -> pd.DataFrame:
    df = _universe(df)
    need = {"last","pct_change","volume"}
    if not need.issubset(df.columns): return df.iloc[0:0]
    m = (df["pct_change"] > 10) & (df["volume"] > 1_000_000)
    return _liq_guards(df[m])

def scan_low_float_hod(df: pd.DataFrame) -> pd.DataFrame:
    df = _universe(df)
    need = {"last","volume","float","pct_change","day_high"}
    if not need.issubset(df.columns): return df.iloc[0:0]
    m = (
        (df["volume"] >= 100_000) &
        (df["float"] <= 10_000_000) &
        (df["pct_change"] >= 10) &
        (df["last"] >= df["day_high"] * 0.98) &
        (df["last"] <= df["day_high"])
    )
    return _liq_guards(df[m])

def scan_premarket_low_float(df: pd.DataFrame) -> pd.DataFrame:
    df = _universe(df)
    need = {"last","pct_change","float","volume"}
    if not need.issubset(df.columns): return df.iloc[0:0]
    m = (
        (df["pct_change"] > 10) &
        (df["float"] < 10_000_000) &
        (df["volume"] > 1_000_000)
    )
    return _liq_guards(df[m], spread_max_pct=1.5)

def scan_vwap_hold(df: pd.DataFrame) -> pd.DataFrame:
    df = _universe(df)
    need = {"last","pct_change","volume","vwap"}
    if not need.issubset(df.columns): return df.iloc[0:0]
    m = (
        (df["pct_change"] >= 10) &
        (df["volume"] >= 1_000_000) &
        (abs((df["last"] - df["vwap"]) / df["vwap"]) <= 0.02)
    )
    return _liq_guards(df[m])

def scan_52w_hod(df: pd.DataFrame) -> pd.DataFrame:
    df = _universe(df)
    need = {"last","yesterday_volume","fifty_two_week_high"}
    if not need.issubset(df.columns): return df.iloc[0:0]
    m = (
        (df["yesterday_volume"] > 1_000_000) &
        (df["last"] >= df["fifty_two_week_high"] * 0.98) &
        (df["last"] <= df["fifty_two_week_high"])
    )
    return _liq_guards(df[m])
