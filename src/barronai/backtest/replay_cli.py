from __future__ import annotations
import os, math, sys, argparse
import pandas as pd
from datetime import datetime, timezone
try:
    import yfinance as yf
except Exception:
    yf = None

# optional preset engine (if present, we use it)
try:
    from ..core.preset_loader import run_preset, load_yaml
    HAVE_PRESET = True
except Exception:
    HAVE_PRESET = False

import json, argparse, time
from pathlib import Path as _Path

def _apply_override(preset: dict, override: dict) -> dict:
    if not override: return preset
    import copy
    out = copy.deepcopy(preset)
    def merge(a, b):
        for k,v in b.items():
            if isinstance(v, dict) and isinstance(a.get(k), dict):
                merge(a[k], v)
            else:
                a[k] = v
    merge(out, override)
    return out

def _shift_for_latency(df: pd.DataFrame, latency_s: float) -> pd.DataFrame:
    if latency_s <= 0: return df
    # 1m bars => any latency shifts fills to next bar
    return df.shift(-1)

def _slip_price(px: float, bps: float, side: str) -> float:
    if bps <= 0: return px
    adj = px * (bps/10000.0)
    return px + (adj if side=="buy" else -adj)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticker", required=True)
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--preset", default="")
    ap.add_argument("--risk_atr", type=float, default=0.5)
    ap.add_argument("--slippage_bps", type=float, default=0.0)
    ap.add_argument("--latency_s", type=float, default=0.0)
    ap.add_argument("--override", default="")              # JSON string to override preset
    ap.add_argument("--out_jsonl", default="tmp/journal/replay_results.jsonl")
    args = ap.parse_args()

    df = _dl_bars(args.ticker, args.start, args.end)
    if df is None or df.empty:
        print("no bars"); return

    preset = {}
    if HAVE_PRESET and args.preset:
        preset = load_yaml(args.preset)
    over = {}
    if args.override:
        try: over = json.loads(args.override)
        except Exception: over = {}
    if preset and over:
        preset = _apply_override(preset, over)

    # Signals: use preset if available, else toy "single hit" at first third
    if HAVE_PRESET and preset:
        sig = run_preset(df.iloc[:], preset)
    else:
        k = max(1, len(df)//3)
        sig = df.iloc[k:k+1][["ts","last"]]
        sig = sig.rename(columns={"last":"price"})

    hits, trades = [], []
    in_pos = False
    entry = stop = tp1 = None

    df_lat = _shift_for_latency(df, args.latency_s)
    for i in range(len(df)):
        snap = df.iloc[i:i+1]
        # if preset produced signals, align by ts; else use toy hit above
        got_hit = False
        if HAVE_PRESET and preset:
            # align on timestamp if present
            if "ts" in sig.columns.values:
                ts = snap["ts"].iloc[0]
                got_hit = bool(len(sig[sig["ts"]==ts]))
        else:
            got_hit = (i==max(1, len(df)//3))

        if (not in_pos) and got_hit:
            px = float(snap["last"].iloc[0])
            entry = _slip_price(px, args.slippage_bps, "buy")
            stop  = entry - args.risk_atr
            tp1   = entry + 2*args.risk_atr
            in_pos = True
            hits.append({"ts": float(snap["ts"].iloc[0].timestamp()) if hasattr(snap["ts"].iloc[0],'timestamp') else None,
                         "price": entry})
            continue

        if in_pos:
            row = df_lat.iloc[i:i+1] if args.latency_s>0 else snap
            if row.empty: break
            price = float(row["last"].iloc[0])
            if price <= stop:
                exit_px = _slip_price(stop, args.slippage_bps, "sell")
                trades.append({"outcome":"stop", "entry":entry, "exit":exit_px})
                in_pos=False
            elif price >= tp1:
                exit_px = _slip_price(tp1, args.slippage_bps, "sell")
                trades.append({"outcome":"tp", "entry":entry, "exit":exit_px})
                in_pos=False

    win = sum(1 for t in trades if t["outcome"]=="tp")
    pnl = [t["exit"]-t["entry"] for t in trades]
    avg = sum(pnl)/max(1,len(pnl))
    out = {
        "ticker": args.ticker,
        "start": args.start, "end": args.end,
        "hits": len(hits), "trades": len(trades),
        "win_pct": round(100*win/max(1,len(trades)),1),
        "avgPnL": round(avg, 6),
        "slippage_bps": args.slippage_bps,
        "latency_s": args.latency_s,
        "risk_atr": args.risk_atr,
        "override": over if over else None,
    }
    _Path(args.out_jsonl).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out_jsonl,"a",encoding="utf-8") as f:
        f.write(json.dumps(out)+"\n")
    print(f"hits={out['hits']} trades={out['trades']} win%={out['win_pct']} avgPnL={out['avgPnL']} outcome={'tp' if win else 'stop'} jsonl={args.out_jsonl}")
