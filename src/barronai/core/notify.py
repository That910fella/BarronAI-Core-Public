from __future__ import annotations
import os, json, requests

WEBHOOK = os.getenv("WEBHOOK_URL","").strip()

def post(msg: str, extra: dict | None=None):
    if not WEBHOOK: return
    payload = {"text": msg}
    if extra: payload["extra"] = extra
    try:
        requests.post(WEBHOOK, json=payload, timeout=5)
    except Exception:
        pass
