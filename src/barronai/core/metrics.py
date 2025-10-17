
from __future__ import annotations
import json, time, threading
from pathlib import Path

_METRICS_PATH = Path("tmp/metrics.json")
_LOCK = threading.Lock()

def _read() -> dict:
    if not _METRICS_PATH.exists():
        return {"ts": time.time(), "polygon_calls":0, "polygon_429":0, "cache_hits":0}
    try:
        return json.loads(_METRICS_PATH.read_text())
    except Exception:
        return {"ts": time.time(), "polygon_calls":0, "polygon_429":0, "cache_hits":0}

def _write(d: dict):
    tmp = _METRICS_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(d))
    tmp.replace(_METRICS_PATH)

def bump(key: str, by: int = 1):
    d = _read()
    d[key] = int(d.get(key, 0)) + by
    d["ts"] = time.time()
    _write(d)

def snapshot() -> dict:
    return _read()
