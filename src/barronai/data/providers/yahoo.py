from __future__ import annotations
import yfinance as yf
import pandas as pd
import numpy as np
from ..float_enricher import pick_float, yahoo_float

def _safe(v, d=None):
    return d if v is None or (isinstance(v, float) and np.isnan(v)) else v

class YahooProvider:
    def __init__(self): ...

    def _one(self, t: str) -> dict:
        tk = yf.Ticker(t)
        info = tk.fast_info or {}
        last = float(_safe(info.get("last_price"), np.nan))
        close_prev = float(_safe(info.get("previous_close"), np.nan))
        pct_change = float(np.nan) if np.isnan(last) or np.isnan(close_prev) else (last-close_prev)/close_prev*100.0
        day_high = float(_safe(info.get("day_high"), np.nan))
        vwap = float(_safe(info.get("last_price"), np.nan))  # placeholder
        volume = int(_safe(info.get("last_volume"), 0))
        fifty_two_week_high = float(_safe(info.get("year_high"), np.nan))
        float_shares = np.nan
        try:
            closes = tk.history(period="1mo", interval="1d")["Close"]
            atr = float(closes.diff().abs().rolling(14).mean().iloc[-1])
        except Exception:
            atr = np.nan
        dollar_volume = float(last * volume) if last and volume else 0.0
        rel_volume = 1.0
        spread_pct = 0.8
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
