from __future__ import annotations
import json, time, pathlib
from typing import Any, Dict

def log_order(payload: Dict[str, Any], status: str = "dry-run") -> None:
    """Append a line to tmp/journal/orders.jsonl for dashboard visibility."""
    pathlib.Path("tmp/journal").mkdir(parents=True, exist_ok=True)
    rec = {"ts": time.time(), "status": status, "payload": payload}
    with open("tmp/journal/orders.jsonl","a",encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
