from __future__ import annotations
import json, csv, os
from dataclasses import asdict
from datetime import datetime
from typing import Any

def _ensure_dir(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)

def log_jsonl(path: str, record: dict[str, Any]):
    _ensure_dir(path)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, default=str) + "\n")

def log_csv(path: str, record: dict[str, Any]):
    _ensure_dir(path)
    write_header = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=record.keys())
        if write_header: w.writeheader()
        w.writerow(record)

def journal_signal(signal, where="tmp/journal/signals.jsonl"):
    rec = {
        "ts": datetime.utcnow().isoformat(),
        "ticker": signal.ticker,
        "score": signal.score,
        "breakdown": signal.breakdown,
        "reasons": signal.reasons,
        "gated_power_hour": signal.gated,
    }
    log_jsonl(where, rec)

def journal_plan(ticker: str, plan, where="tmp/journal/plans.csv"):
    rec = {
        "ts": datetime.utcnow().isoformat(),
        "ticker": ticker,
        "size": plan.size_shares,
        "stop": plan.stop,
        "tp1": plan.tp1,
        "tp2": plan.tp2,
        "notes": plan.notes,
    }
    log_csv(where, rec)
