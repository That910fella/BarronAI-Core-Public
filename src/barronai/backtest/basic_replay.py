
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
    df = pd.DataFrame(rows)
    df["ts"] = pd.to_datetime(df["t"], unit="ms", utc=True)
    df["last"] = df["c"]; df["vwap"] = df.get("vw"); df["volume"] = df["v"]
    df["day_high"] = df["last"].cummax()
    df["pct_change"] = (df["last"] / df["last"].iloc[0] - 1.0) * 100.0
    df["ticker"] = ticker
    return df[["ts","last","vwap","volume","day_high","pct_change","ticker"]]

def run_backtest(ticker: str, start: str, end: str, preset_path: str, risk_atr: float = 0.5):
    bars = load_minute_bars(ticker, start, end)
    if bars.empty:
        print("no bars"); return
    preset = load_yaml(preset_path)

    hits, trades = [], []
    in_pos = False
    entry = stop = tp1 = None

    for i in range(len(bars)):
        snap = bars.iloc[i:i+1]
        res = run_preset(snap, preset)
        if not in_pos and not res.empty:
            hits.append({"ts": snap["ts"].iloc[0], "last": float(snap["last"].iloc[0])})
            entry = float(snap["last"].iloc[0]); stop = entry - risk_atr; tp1 = entry + 2*risk_atr
            in_pos = True; continue
        if in_pos:
            price = float(bars["last"].iloc[i])
            if price <= stop or price >= tp1:
                trades.append({"entry": entry, "exit": price, "pnl": (price-entry)})
                in_pos = False

    win = sum(1 for t in trades if t["pnl"]>0)
    avg = (sum(t["pnl"] for t in trades)/len(trades)) if trades else 0.0
    print(f"hits={len(hits)} trades={len(trades)} win%={round(100*win/max(1,len(trades)),1)} avgPnL={round(avg,4)}")
    if hits: print("first 5 hits:", hits[:5])
    if trades: print("first 5 trades:", trades[:5])

if __name__ == "__main__":
    run_backtest(ticker="PLTR",
                 start="2025-10-01T13:30:00",
                 end="2025-10-01T20:00:00",
                 preset_path="scans/presets/vwap_hold.yml")
