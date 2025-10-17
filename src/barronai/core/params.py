from __future__ import annotations
import os, json, time
from pathlib import Path
from typing import Dict, Any

_PARAM_PATH = os.getenv("PARAMS_PATH", "tmp/params/current_params.json")
_cache: Dict[str, Any] | None = None
_cache_mtime: float | None = None

_DEFAULT = {
    "weights": {"structure": 0.5, "catalyst": 0.35, "narrative": 0.15},
    "threshold": 0.32,
}

def get_params() -> Dict[str, Any]:
    global _cache, _cache_mtime
    p = Path(_PARAM_PATH)
    if p.exists():
        mt = p.stat().st_mtime
        if _cache is None or _cache_mtime != mt:
            try:
                _cache = json.loads(p.read_text())
                _cache_mtime = mt
            except Exception:
                _cache = _DEFAULT
                _cache_mtime = time.time()
    else:
        _cache = _DEFAULT
        _cache_mtime = time.time()
    return _cache
