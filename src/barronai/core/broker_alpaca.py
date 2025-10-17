from __future__ import annotations
import json
from typing import Any, Dict, Optional
import requests


class Alpaca:
    def __init__(self, base_url: str, key: str, secret: str):
        # base_url should already include /v2 (e.g., https://paper-api.alpaca.markets/v2)
        self.base_url = base_url.rstrip("/")
        self.hdrs = {
            "APCA-API-KEY-ID": key,
            "APCA-API-SECRET-KEY": secret,
            "Content-Type": "application/json",
        }

    # -------- low-level request
    def _req(self, method: str, path: str, **kw) -> requests.Response:
        url = f"{self.base_url}{path}"
        return requests.request(method, url, headers=self.hdrs, timeout=20, **kw)

    # -------- helpers
    @staticmethod
    def _safe_err(resp: requests.Response) -> str:
        try:
            j = resp.json()
            return j.get("message") or j.get("error") or str(j)
        except Exception:
            return f"http {resp.status_code}"

    # -------- account / health
    def health(self) -> Dict[str, Any]:
        r = self._req("GET", "/account")
        if r.ok:
            j = r.json()
            return {
                "ok": True,
                "status": j.get("status"),
                "buying_power": j.get("buying_power"),
                "account_id": j.get("id"),
            }
        return {"ok": False, "status_code": r.status_code, "error": self._safe_err(r)}

    # -------- orders
    def submit_order(
        self,
        symbol: str,
        side: str,
        qty: int,
        limit: Optional[float] = None,
        tif: str = "day",
        extended_hours: bool = False,
    ) -> Dict[str, Any]:
        body: Dict[str, Any] = {
            "symbol": symbol.upper(),
            "side": side.lower(),
            "qty": qty,
            "type": "limit" if limit is not None else "market",
            "time_in_force": tif,
            "extended_hours": extended_hours,
        }
        if limit is not None:
            body["limit_price"] = float(limit)
        r = self._req("POST", "/orders", data=json.dumps(body))
        if r.ok:
            j = r.json()
            return {"ok": True, "order_id": j.get("id"), "status": j.get("status"), "raw": j}
        return {"ok": False, "status_code": r.status_code, "error": self._safe_err(r)}

    def list_orders(self, status: str = "all", limit: int = 50) -> Dict[str, Any]:
        params = {"status": status, "limit": limit}
        r = self._req("GET", "/orders", params=params)
        if r.ok:
            return {"ok": True, "orders": r.json()}
        return {"ok": False, "status_code": r.status_code, "error": self._safe_err(r)}

    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        r = self._req("DELETE", f"/orders/{order_id}")
        if r.ok:
            return {"ok": True}
        return {"ok": False, "status_code": r.status_code, "error": self._safe_err(r)}

    def cancel_all_orders(self) -> Dict[str, Any]:
        r = self._req("DELETE", "/orders")
        if r.ok:
            return {"ok": True, "raw": r.json()}
        return {"ok": False, "status_code": r.status_code, "error": self._safe_err(r)}

    # -------- positions
    def positions(self) -> Dict[str, Any]:
        r = self._req("GET", "/positions")
        if r.ok:
            return {"ok": True, "positions": r.json()}
        return {"ok": False, "status_code": r.status_code, "error": self._safe_err(r)}

    def close_position(self, symbol: str) -> Dict[str, Any]:
        # Market close the entire position for a symbol
        r = self._req("DELETE", f"/positions/{symbol.upper()}")
        if r.ok:
            return {"ok": True, "raw": r.json()}
        return {"ok": False, "status_code": r.status_code, "error": self._safe_err(r)}

    def close_all_positions(self) -> Dict[str, Any]:
        r = self._req("DELETE", "/positions")
        if r.ok:
            return {"ok": True, "raw": r.json()}
        return {"ok": False, "status_code": r.status_code, "error": self._safe_err(r)}
