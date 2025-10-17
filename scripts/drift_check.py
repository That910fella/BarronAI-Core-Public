from __future__ import annotations
import os, json, subprocess, datetime as dt
from pathlib import Path

TICKER = os.getenv("TICKER","TSLA")
PRESET = os.getenv("PRESET","")
RISK   = os.getenv("RISK","0.5")
SLIP   = os.getenv("SLIPPAGE_BPS","5")
LAT    = os.getenv("LATENCY_S","0.25")

def run_day(d):
    start = d; end = (dt.date.fromisoformat(d)+dt.timedelta(days=1)).isoformat()
    cmd = ["python","-m","barronai.backtest.replay_cli","--ticker",TICKER,"--start",start,"--end",end,
           "--risk_atr",RISK,"--slippage_bps",SLIP,"--latency_s",LAT]
    if PRESET: cmd += ["--preset", PRESET]
    if Path("tmp/params/current_params.json").exists():
        over = Path("tmp/params/current_params.json").read_text()
        cmd += ["--override", over]
    out = subprocess.check_output(cmd, text=True)
    import re
    m1 = re.search(r"win%=(\d+\.?\d*)", out); m2 = re.search(r"avgPnL=(\-?\d+\.?\d*)", out); m3 = re.search(r"trades=(\d+)", out)
    return {"win": float(m1.group(1)) if m1 else 0.0,
            "pnl": float(m2.group(1)) if m2 else 0.0,
            "trades": int(m3.group(1)) if m3 else 0}

def eval_list(path):
    days = [d.strip() for d in Path(path).read_text().splitlines() if d.strip()]
    if not days: return {"win":0, "pnl":0, "trades":0}
    wins, pnls, trades = 0.0, 0.0, 0
    for d in days:
        r = run_day(d); wins += r["win"]; pnls += r["pnl"]; trades += r["trades"]
    return {"win": round(wins/len(days),2), "pnl": round(pnls/len(days),4), "trades": trades, "days": len(days)}

cal = eval_list("configs/calibration_dates.txt")
hl  = eval_list("configs/holdout_dates.txt")
delta = round(hl["win"] - cal["win"], 2)

Path("tmp").mkdir(exist_ok=True)
with open("tmp/drift.json","w",encoding="utf-8") as f:
    json.dump({"calibration": cal, "holdout": hl, "delta_win_pct": delta,
               "ts": dt.datetime.now(dt.timezone.utc).isoformat()}, f, indent=2)
print("drift:", json.dumps({"delta_win_pct":delta,"cal":cal,"hold":hl}, indent=2))
