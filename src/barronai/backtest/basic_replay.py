from __future__ import annotations
import os, math, requests, pandas as pd
from datetime import datetime, timezone
from ..core.preset_loader import run_preset, load_yaml

API = "https://api.polygon.io"

def _get(path: str, params: dict=None):
    params = params or {}
    params["apiKey"] = os.getenv("POLYGON_API_KEY","")
    r = requests.get(API+path, params=params, timeout=20)
    r.raise_for_status()
    return r.json()

def _to_ms(d: datetime) -> int:
    return int(d.replace(tzinfo=timezone.utc).timestamp()*1000)

def load_minute_bars(ticker: str, start: str, end: str) -> pd.DataFrame:
    s = datetime.fromisoformat(start); e = datetime.fromisoformat(end)
    res = _get(f"/v2/aggs/ticker/{ticker}/range/1/min/{_to_ms(s)}/{_to_ms(e)}",
               {"adjusted":"true", "sort":"asc", "limit":"50000"})
    rows = res.get("results", [])
    if not rows: return pd.DataFrame()
    df = pd.DataFrame([{
        "ts": pd.to_datetime(b["t"], unit="ms", utc=True),
        "last": b.get("c"), "vwap": b.get("vw"), "volume": b.get("v"),
        "day_high": b.get("h"), "pct_change": math.nan
    } for b in rows])
    df["day_high"] = df["last"].cummax()
    df["pct_change"] = (df["last"] / df["last"].iloc[0] - 1.0) * 100.0
    df["ticker"] = ticker
    return df

def run_backtest(ticker: str, start: str, end: str, preset_path: str):
    bars = load_minute_bars(ticker, start, end)
    if bars.empty:
        print("no bars"); return
    preset = load_yaml(preset_path)
    hits = []
    for i in range(len(bars)):
        snap = bars.iloc[:i+1].tail(1).copy()
        res = run_preset(snap, preset)
        if not res.empty:
            hits.append({"ts": snap["ts"].iloc[0], "last": snap["last"].iloc[0]})
    print(f"hits={len(hits)} over {len(bars)} minutes")
    if hits: print("first 5 hits:", hits[:5])

if __name__ == "__main__":
    run_backtest(ticker="PLTR", start="2025-10-01T13:30:00", end="2025-10-01T20:00:00", preset_path="scans/presets/vwap_hold.yml")
