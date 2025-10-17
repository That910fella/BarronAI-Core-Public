from __future__ import annotations
import json
import os
from typing import Any, Dict, Literal, Optional
import requests

Side = Literal["buy", "sell"]

class BarronClient:
    def __init__(self, base: Optional[str] = None, api_key: Optional[str] = None, timeout: int = 15):
        self.base = base or os.getenv("BROKER_BASE", "http://localhost:8010")
        self.api_key = api_key or os.getenv("BROKER_API_KEY", "")
        self.timeout = timeout

    def _post(self, path: str, body: Dict[str, Any]) -> Dict[str, Any]:
        r = requests.post(
            f"{self.base}{path}",
            headers={"x-api-key": self.api_key, "content-type": "application/json"},
            data=json.dumps(body),
            timeout=self.timeout,
        )
        try:
            return r.json()
        except Exception:
            return {"status_code": r.status_code, "text": r.text}

    def bracket_percent(
        self, *, ticker: str, side: Side, qty: int, basis: float,
        take_profit_pct: float, stop_loss_pct: float, tif: str = "day", extended_hours: bool = False
    ):
        body = dict(ticker=ticker, side=side, qty=qty, basis=basis,
                    take_profit_pct=take_profit_pct, stop_loss_pct=stop_loss_pct,
                    tif=tif, extended_hours=extended_hours)
        return self._post("/api/broker/orders/bracket", body)

    def oco_absolute(
        self, *, ticker: str, side: Side, qty: int,
        take_profit: float, stop_loss: float, stop_limit: float | None = None,
        tif: str = "day", extended_hours: bool = False
    ):
        body = dict(ticker=ticker, side=side, qty=qty,
                    take_profit=take_profit, stop_loss=stop_loss,
                    stop_limit=stop_limit, tif=tif, extended_hours=extended_hours)
        return self._post("/api/broker/orders/oco", body)

    def trailing(
        self, *, ticker: str, side: Side, qty: int, trail_percent: float | None = None,
        trail_price: float | None = None, tif: str = "day", extended_hours: bool = False
    ):
        body = dict(ticker=ticker, side=side, qty=qty,
                    trail_percent=trail_percent, trail_price=trail_price,
                    tif=tif, extended_hours=extended_hours)
        return self._post("/api/broker/orders/trailing", body)
