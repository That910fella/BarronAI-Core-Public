from __future__ import annotations
import os, json, subprocess, datetime as dt, sys
from pathlib import Path

# Config
TICKER = os.getenv("TICKER","TSLA")
RISK   = os.getenv("RISK","0.6")
SLIP   = os.getenv("SLIPPAGE_BPS","5")
LAT    = os.getenv("LATENCY_S","0.25")
PRESET = os.getenv("PRESET","")
PARAMS_OUT = Path("tmp/params/current_params.json")

def run(cmd: list[str]) -> str:
    return subprocess.check_output(cmd, text=True)

def step_tune():
    env = os.environ.copy()
    env.setdefault("TICKER", TICKER)
    env.setdefault("RISK", RISK)
    env.setdefault("SLIPPAGE_BPS", SLIP)
    env.setdefault("LATENCY_S", LAT)
    out = run(["python","scripts/tuner.py"])
    return out

def step_drift():
    out = run(["python","scripts/drift_check.py"])
    return out

def post_webhook(text: str, extra: dict | None=None):
    url = os.getenv("WEBHOOK_URL","").strip()
    if not url: return
    import requests
    payload = {"text": text}
    if extra: payload["extra"] = extra
    try:
        requests.post(url, json=payload, timeout=8)
    except Exception:
        pass

def main():
    # 1) tune
    tune_out = step_tune()
    best = {}
    try:
        best = json.loads(Path("tmp/params/current_params.json").read_text())
    except Exception: pass

    # 2) drift
    drift_out = step_drift()
    drift = {}
    try:
        drift = json.loads(Path("tmp/drift.json").read_text())
    except Exception: pass

    # 3) announce & done
    post_webhook(
        f"Nightly complete for {TICKER}",
        {"best_params": best, "drift": drift}
    )
    print("nightly OK")

if __name__ == "__main__":
    main()
