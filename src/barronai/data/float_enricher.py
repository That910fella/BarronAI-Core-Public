from __future__ import annotations
from typing import Optional
import math
import yfinance as yf

def yahoo_float(ticker: str) -> Optional[float]:
    try:
        info = yf.Ticker(ticker).get_info()
        f = info.get("floatShares") or info.get("sharesOutstanding")
        return float(f) if f else None
    except Exception:
        return None

def pick_float(*values) -> Optional[float]:
    for v in values:
        if v is None: continue
        try:
            x = float(v)
            if x and not math.isnan(x): return x
        except Exception:
            continue
    return None
