from __future__ import annotations
import os, time, json, pathlib

class PaperBroker:
    def __init__(self):
        self.dry = os.getenv("DRY_RUN","1") in {"1","true","True"}
        pathlib.Path("tmp/journal").mkdir(parents=True, exist_ok=True)

    def submit(self, side: str, ticker: str, qty: int, limit: float):
        payload = {"side":side,"ticker":ticker,"qty":qty,"limit":limit}
        status = "dry-run" if self.dry else "submitted"
        with open("tmp/journal/orders.jsonl","a",encoding="utf-8") as f:
            f.write(json.dumps({"ts":time.time(),"status":status,"payload":payload})+"\n")
        return {"ok": True, "status": status, "payload": payload}
