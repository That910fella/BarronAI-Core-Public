from __future__ import annotations
import os, json, subprocess, itertools, datetime as dt
from pathlib import Path

PRESET = os.getenv("PRESET","")  # optional path; if blank, toy signal path is used
TICKER = os.getenv("TICKER","TSLA")
DATES  = os.getenv("DATES","").split(",")  # e.g. 2025-10-10,2025-10-15 (inclusive range)
RISK   = os.getenv("RISK","0.5")
SLIP   = os.getenv("SLIPPAGE_BPS","5")
LAT    = os.getenv("LATENCY_S","0.25")

def daterange(a,b):
    s = dt.date.fromisoformat(a); e = dt.date.fromisoformat(b)
    d = s
    while d <= e:
        yield d.isoformat()
        d += dt.timedelta(days=1)

if len(DATES)>=2 and DATES[0] and DATES[1]:
    DAYLIST = list(daterange(DATES[0], DATES[1]))
else:
    # pick last 5 business days before today (Mon-Fri)
    import datetime as dt
    DAYLIST = []
    d = dt.date.today() - dt.timedelta(days=1)
    while len(DAYLIST) < 5:
        if d.weekday() < 5:  # 0=Mon..4=Fri
            DAYLIST.append(d.isoformat())
        d -= dt.timedelta(days=1)
    DAYLIST.reverse()

grid_weights = [ (0.6,0.3,0.1), (0.5,0.35,0.15), (0.45,0.4,0.15) ]
thresholds   = [0.28, 0.32, 0.36]

candidates = []
for (w_str, w_cat, w_nar), th in itertools.product(grid_weights, thresholds):
    override = {"weights":{"structure":w_str,"catalyst":w_cat,"narrative":w_nar},
                "threshold": th}
    pnl_all, trades_all, wins_all = 0.0, 0, 0
    for d in DAYLIST:
        start = d; end = (dt.date.fromisoformat(d)+dt.timedelta(days=1)).isoformat()
        cmd = [
            "python","-m","barronai.backtest.replay_cli",
            "--ticker",TICKER,"--start",start,"--end",end,"--risk_atr",RISK,
            "--slippage_bps",SLIP,"--latency_s",LAT,"--override", json.dumps(override)
        ]
        if PRESET: cmd += ["--preset", PRESET]
        try:
            out = subprocess.check_output(cmd, text=True)
            # parse: win%=X avgPnL=Y
            import re
            m1 = re.search(r"win%=(\d+\.?\d*)", out); m2 = re.search(r"avgPnL=(\-?\d+\.?\d*)", out); m3 = re.search(r"trades=(\d+)", out)
            winpct = float(m1.group(1)) if m1 else 0.0
            avgpnl = float(m2.group(1)) if m2 else 0.0
            trades = int(m3.group(1)) if m3 else 0
            pnl_all += avgpnl
            trades_all += trades
            wins_all += int(round(winpct/100.0*trades))
        except Exception as e:
            pass
    score = (wins_all/max(1,trades_all)) * 0.7 + (pnl_all/ max(1,len(DAYLIST))) * 0.3
    candidates.append({"override":override,"wins":wins_all,"trades":trades_all,"score":round(score,6)})

candidates.sort(key=lambda x: x["score"], reverse=True)
Path("tmp/exp").mkdir(parents=True, exist_ok=True)
with open("tmp/exp/tune_results.json","w",encoding="utf-8") as f:
    json.dump({"dates":DAYLIST,"candidates":candidates[:20]}, f, indent=2)

best = candidates[0] if candidates else {"override":{}}
Path("tmp/params").mkdir(parents=True, exist_ok=True)
with open("tmp/params/current_params.json","w",encoding="utf-8") as f:
    json.dump(best["override"], f, indent=2)
print("BEST:", json.dumps(best, indent=2))
print("Wrote: tmp/params/current_params.json and tmp/exp/tune_results.json")
