from __future__ import annotations
import os, requests, math
import pandas as pd
from ..float_enricher import pick_float, yahoo_float
from datetime import datetime, timezone

API = "https://api.polygon.io"

def _get(path: str, params: dict | None=None):
    params = params or {}
    params["apiKey"] = os.getenv("POLYGON_API_KEY","")
    r = requests.get(API+path, params=params, timeout=12)
    r.raise_for_status()
    return r.json()

def _today_range_ms() -> tuple[int,int]:
    now = datetime.now(timezone.utc)
    start = int(datetime(now.year, now.month, now.day, tzinfo=timezone.utc).timestamp() * 1000)
    end   = int(now.timestamp() * 1000)
    return start, end

def _intraday_vwap(t: str) -> float:
    try:
        start, end = _today_range_ms()
        res = _get(f"/v2/aggs/ticker/{t}/range/1/min/{start}/{end}", {"adjusted":"true", "sort":"asc", "limit":"50000"})
        bars = res.get("results", [])
        if not bars: return math.nan
        vol_sum = 0.0; numer = 0.0
        for b in bars:
            v = float(b.get("v") or 0.0)
            vw = float(b.get("vw") or 0.0)
            if v > 0 and vw > 0:
                vol_sum += v
                numer += vw * v
        return (numer/vol_sum) if vol_sum > 0 else math.nan
    except Exception:
        return math.nan

def _shares_outstanding(t: str) -> float | None:
    try:
        res = _get(f"/v3/reference/tickers/{t}", {"date": datetime.utcnow().date().isoformat()})
        r = res.get("results", {}) or {}
        return float(r.get("weighted_shares_outstanding") or r.get("share_class_shares") or 0.0) or None
    except Exception:
        return None

class PolygonProvider:
    def __init__(self): ...

    def _one(self, t: str) -> dict:
        snap = _get(f"/v2/snapshot/locale/us/markets/stocks/tickers/{t}")
        s = snap.get("ticker", {}) or {}
        last = float(s.get("lastTrade", {}).get("p") or s.get("lastQuote", {}).get("P") or math.nan)
        day_high = float(s.get("day", {}).get("h") or math.nan)
        volume = int(s.get("day", {}).get("v") or 0)
        prev_close = float(s.get("prevDay", {}).get("c") or math.nan)
        pct_change = ((last - prev_close)/prev_close*100.0) if (prev_close and not math.isnan(prev_close) and last) else math.nan
        vwap = _intraday_vwap(t)
        if math.isnan(vwap):
            vwap = float(s.get("day", {}).get("vw") or math.nan)
        fifty_two_week_high = math.nan
        float_shares = _shares_outstanding(t)
        dollar_volume = (last or 0.0) * (volume or 0)
        rel_volume = 1.0
        spread_pct = 0.5
        atr = math.nan
        return {
            "ticker": t, "last": last, "volume": volume, "float": pick_float(float_shares, yahoo_float(t)),
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
