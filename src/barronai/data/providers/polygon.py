from __future__ import annotations
import os, requests
import pandas as pd
import math

API = "https://api.polygon.io"

def _get(path: str, params: dict=None):
    params = params or {}
    params["apiKey"] = os.getenv("POLYGON_API_KEY","")
    r = requests.get(API+path, params=params, timeout=10)
    r.raise_for_status()
    return r.json()

class PolygonProvider:
    def __init__(self): ...

    def _one(self, t: str) -> dict:
        # snapshot (quotes/last/hi/lo/vol)
        snap = _get(f"/v2/snapshot/locale/us/markets/stocks/tickers/{t}")
        s = snap.get("ticker", {})
        last = float(s.get("lastTrade", {}).get("p") or s.get("lastQuote", {}).get("P") or math.nan)
        day_high = float(s.get("day", {}).get("h") or math.nan)
        volume = int(s.get("day", {}).get("v") or 0)
        prev_close = float(s.get("prevDay", {}).get("c") or math.nan)
        pct_change = ((last - prev_close)/prev_close*100.0) if (prev_close and not math.isnan(prev_close) and last) else math.nan
        vwap = float(s.get("day", {}).get("vw") or math.nan)
        fifty_two_week_high = math.nan  # could use aggregates-range 52w if needed
        # float shares not in snapshot; leave None (can add /v3/reference/tickers later)
        float_shares = None
        dollar_volume = (last or 0.0) * (volume or 0)
        rel_volume = 1.0
        spread_pct = 0.6
        atr = math.nan
        return {
            "ticker": t, "last": last, "volume": volume, "float": float_shares,
            "day_high": day_high, "vwap": vwap, "pct_change": pct_change,
            "spread_pct": spread_pct, "dollar_volume": dollar_volume, "rel_volume": rel_volume,
            "yesterday_volume": 0, "fifty_two_week_high": fifty_two_week_high, "atr": atr,
        }

    def quote_snapshot(self, tickers):
        rows = []
        for t in tickers:
            try: rows.append(self._one(t))
            except Exception: continue
        return pd.DataFrame(rows)
