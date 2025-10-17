from __future__ import annotations
import os, json
from typing import Optional
import requests

class OrderResult(dict): ...

class TradeExecutor:
    def __init__(self, base_url: Optional[str]=None,
                       key_id: Optional[str]=None,
                       secret: Optional[str]=None,
                       paper_only: bool=True):
        self.base_url = base_url or os.getenv("ALPACA_PAPER_BASE_URL","https://paper-api.alpaca.markets")
        self.key_id = key_id or os.getenv("ALPACA_API_KEY_ID")
        self.secret = secret or os.getenv("ALPACA_API_SECRET_KEY")
        self.paper_only = paper_only

    def _headers(self):
        return {
            "APCA-API-KEY-ID": self.key_id or "",
            "APCA-API-SECRET-KEY": self.secret or "",
            "Content-Type":"application/json",
        }

    def _post(self, path: str, payload: dict) -> OrderResult:
        url = f"{self.base_url}{path}"
        r = requests.post(url, headers=self._headers(), data=json.dumps(payload), timeout=10)
        r.raise_for_status()
        return OrderResult(r.json())

    def _log_order(self, payload: dict, status: str):
        pathlib.Path("tmp/journal").mkdir(parents=True, exist_ok=True)
        path = "tmp/journal/orders.jsonl"
        rec = {"ts": time.time(), "status": status, "payload": payload}
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")

    def submit_limit_buy(self, symbol: str, qty: int, limit_price: float, tif: str="day") -> OrderResult:
        payload = {
            "symbol": symbol, "qty": qty, "side": "buy", "type":"limit",
            "limit_price": round(limit_price,4), "time_in_force": tif
        }
        if self.paper_only or not (self.key_id and self.secret):
            self._log_order(payload, "dry-run"); return OrderResult({"status":"dry-run","order":payload})
        try:
            return self._post("/v2/orders", payload)
        except Exception as e:
            return OrderResult({"status":"error","error":str(e),"order":payload})

    def submit_bracket(self, symbol:str, qty:int, entry:float, stop:float, take:float, tif:str="day") -> OrderResult:
        payload = {
            "symbol": symbol, "qty": qty, "side": "buy", "type":"limit",
            "limit_price": round(entry,4), "time_in_force": tif,
            "order_class":"bracket",
            "take_profit":{"limit_price": round(take,4)},
            "stop_loss":{"stop_price": round(stop,4)}
        }
        if self.paper_only or not (self.key_id and self.secret):
            self._log_order(payload, "dry-run"); return OrderResult({"status":"dry-run","order":payload})
        try:
            return self._post("/v2/orders", payload)
        except Exception as e:
            return OrderResult({"status":"error","error":str(e),"order":payload})
