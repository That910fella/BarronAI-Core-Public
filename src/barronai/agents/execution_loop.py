from __future__ import annotations
import os, math, requests, pandas as pd
from dataclasses import dataclass
from datetime import datetime, timezone
from .position_manager import Position, trail_stop_to_vwap

POLY_API = "https://api.polygon.io"

def _get(path: str, params: dict | None=None):
    params = params or {}
    params["apiKey"] = os.getenv("POLYGON_API_KEY","")
    r = requests.get(POLY_API+path, params=params, timeout=10)
    r.raise_for_status()
    return r.json()

def _today_range_ms():
    now = datetime.now(timezone.utc)
    start = int(datetime(now.year, now.month, now.day, tzinfo=timezone.utc).timestamp() * 1000)
    end   = int(now.timestamp() * 1000)
    return start, end

def ema(series: pd.Series, span: int = 20) -> float:
    if series.empty: return math.nan
    return float(series.ewm(span=span, adjust=False).mean().iloc[-1])

def latest_intraday(ticker: str):
    s,e = _today_range_ms()
    res = _get(f"/v2/aggs/ticker/{ticker}/range/1/min/{s}/{e}", {"adjusted":"true", "sort":"asc", "limit":50000})
    rows = res.get("results", [])
    if not rows: return None
    df = pd.DataFrame(rows)
    # c=close, v=volume, vw=bar VWAP
    last_close = float(df["c"].iloc[-1])
    bar_vwap   = float(df["vw"].iloc[-1]) if "vw" in df else math.nan
    ema20      = ema(df["c"], span=20)
    return {"last": last_close, "bar_vwap": bar_vwap, "ema20": ema20}

def manage_position(pos: Position, cushion_pct: float = 0.8) -> dict:
    data = latest_intraday(pos.ticker)
    if not data:
        return {"status":"no-data"}
    # trail stop to max(VWAP cushion, EMA20 cushion)
    vwap_stop = trail_stop_to_vwap(pos, data["bar_vwap"], cushion_pct)
    ema_stop  = round((data["ema20"] or pos.stop) * (1 - cushion_pct/100.0), 4) if data["ema20"] and not math.isnan(data["ema20"]) else pos.stop
    new_stop  = max(pos.stop, vwap_stop, ema_stop)
    changed   = new_stop > pos.stop
    return {"status":"ok", "last": data["last"], "vwap": data["bar_vwap"], "ema20": data["ema20"],
            "old_stop": pos.stop, "new_stop": new_stop, "changed": changed}
