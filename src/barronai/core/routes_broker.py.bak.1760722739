from __future__ import annotations
from dotenv import load_dotenv
load_dotenv()
import os, json
from typing import Any, Dict, Optional
from fastapi import APIRouter, Body, Path, Query, Depends, HTTPException, Header
from fastapi.responses import HTMLResponse
import requests

BROKER_API_KEY = os.getenv("BROKER_API_KEY")

def require_broker_key(x_api_key: Optional[str] = Header(default=None)):
    # if BROKER_API_KEY not set, allow (dev mode); otherwise require exact match
    if BROKER_API_KEY and x_api_key != BROKER_API_KEY:
        raise HTTPException(status_code=401, detail="invalid API key")

router = APIRouter(dependencies=[Depends(require_broker_key)])

# ---------- Minimal Alpaca client ----------
class Alpaca:
    def __init__(self, base_url: str, key: str, secret: str):
        self.base_url = base_url.rstrip("/")
        self.hdrs = {
            "APCA-API-KEY-ID": key,
            "APCA-API-SECRET-KEY": secret,
            "Content-Type": "application/json",
        }

    def _req(self, method: str, path: str, **kw) -> requests.Response:
        url = f"{self.base_url}{path}"
        return requests.request(method, url, headers=self.hdrs, timeout=20, **kw)

    @staticmethod
    def _ok(payload: Dict[str, Any]) -> Dict[str, Any]:
        return {"ok": True, **payload}

    @staticmethod
    def _bad(r: requests.Response) -> Dict[str, Any]:
        try:
            j = r.json()
            msg = j.get("message") or j.get("error") or j
        except Exception:
            msg = r.text
        return {"ok": False, "status_code": r.status_code, "error": str(msg).strip(".") + "."}
    # ---- account / health
    def health(self) -> Dict[str, Any]:
        r = self._req("GET", "/account")
        if r.ok:
            j = r.json()
            return self._ok({
                "status": j.get("status"),
                "buying_power": j.get("buying_power"),
                "account_id": j.get("id"),
            })
        return self._bad(r)

    # ---- orders
    def submit_bracket_order(self, symbol: str, side: str, qty: int, take_profit: float, stop_loss: float, stop_limit: Optional[float] = None, tif: str = "day", extended_hours: bool = False) -> Dict[str, Any]:
        body: Dict[str, Any] = {"symbol": symbol.upper(), "side": side.lower(), "qty": qty, "type": "market", "time_in_force": tif, "extended_hours": extended_hours, "order_class": "bracket", "take_profit": {"limit_price": float(take_profit)}, "stop_loss": {"stop_price": float(stop_loss)}}
        if stop_limit is not None: body["stop_loss"]["limit_price"] = float(stop_limit)
        r = self._req("POST", "/orders", data=json.dumps(body))
        return self._ok({"raw": r.json()}) if r.ok else self._bad(r)

    def submit_oco_order(self, symbol: str, side: str, qty: int, take_profit: float, stop_loss: float, stop_limit: Optional[float] = None, tif: str = "day", extended_hours: bool = False) -> Dict[str, Any]:
        body: Dict[str, Any] = {"symbol": symbol.upper(), "side": side.lower(), "qty": qty, "type": "market", "time_in_force": tif, "extended_hours": extended_hours, "order_class": "oco", "take_profit": {"limit_price": float(take_profit)}, "stop_loss": {"stop_price": float(stop_loss)}}
        if stop_limit is not None: body["stop_loss"]["limit_price"] = float(stop_limit)
        r = self._req("POST", "/orders", data=json.dumps(body))
        return self._ok({"raw": r.json()}) if r.ok else self._bad(r)

    def submit_trailing_stop(self, symbol: str, side: str, qty: int, trail_price: Optional[float] = None, trail_percent: Optional[float] = None, tif: str = "day", extended_hours: bool = False) -> Dict[str, Any]:
        body: Dict[str, Any] = {"symbol": symbol.upper(), "side": side.lower(), "qty": qty, "type": "trailing_stop", "time_in_force": tif, "extended_hours": extended_hours}
        if trail_price is None and trail_percent is None: return self._bad(type("obj",(),{"status_code":422,"json":lambda:{"error":"need trail_price or trail_percent"},"text":"need trail_price or trail_percent"})())
        if trail_price is not None: body["trail_price"] = float(trail_price)
        if trail_percent is not None: body["trail_percent"] = float(trail_percent)
        r = self._req("POST", "/orders", data=json.dumps(body))
        return self._ok({"raw": r.json()}) if r.ok else self._bad(r)
    def submit_bracket_order(self, symbol: str, side: str, qty: int, take_profit: float, stop_loss: float, stop_limit: Optional[float] = None, tif: str = "day", extended_hours: bool = False) -> Dict[str, Any]:
        body: Dict[str, Any] = {
            "symbol": symbol.upper(),
            "side": side.lower(),
            "qty": qty,
            "type": "market",
            "time_in_force": tif,
            "extended_hours": extended_hours,
            "order_class": "bracket",
            "take_profit": {"limit_price": float(take_profit)},
            "stop_loss": {"stop_price": float(stop_loss)}
        }
        if stop_limit is not None:
            body["stop_loss"]["limit_price"] = float(stop_limit)
        r = self._req("POST", "/orders", data=json.dumps(body))
        return self._ok({"raw": r.json()}) if r.ok else self._bad(r)
    def submit_order(self, symbol: str, side: str, qty: int,
                     limit: Optional[float] = None, tif: str = "day",
                     extended_hours: bool = False) -> Dict[str, Any]:
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
        return self._ok({"raw": r.json()}) if r.ok else self._bad(r)

    def list_orders(self, status: str = "all", limit: int = 50) -> Dict[str, Any]:
        r = self._req("GET", f"/orders?status={status}&limit={limit}")
        return self._ok({"orders": r.json()}) if r.ok else self._bad(r)

    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        r = self._req("DELETE", f"/orders/{order_id}")
        return {"ok": True} if r.ok else self._bad(r)

    def cancel_all_orders(self) -> Dict[str, Any]:
        r = self._req("DELETE", "/orders")
        return {"ok": True} if r.ok else self._bad(r)

    # ---- positions
    def positions(self) -> Dict[str, Any]:
        r = self._req("GET", "/positions")
        return self._ok({"positions": r.json()}) if r.ok else self._bad(r)

    def close_position(self, symbol: str) -> Dict[str, Any]:
        r = self._req("DELETE", f"/positions/{symbol.upper()}", params={"qty": "all"})
        return {"ok": True} if r.ok else self._bad(r)

    def close_all_positions(self) -> Dict[str, Any]:
        r = self._req("DELETE", "/positions")
        return {"ok": True} if r.ok else self._bad(r)

# ---------- single shared client ----------
AK = os.getenv("ALPACA_KEY_ID")
AS = os.getenv("ALPACA_SECRET_KEY")
AU = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets/v2")
ALPACA_CLIENT: Optional[Alpaca] = Alpaca(AU, AK, AS) if (AK and AS) else None
# ---------- API routes ----------
@router.get("/api/broker/debug")
def api_broker_debug():
    kid = os.getenv("ALPACA_KEY_ID", "")
    return {
        "base_url": os.getenv("ALPACA_BASE_URL"),
        "key_loaded": bool(kid),
        "key_preview": f"{kid[:4]}...{kid[-4:]}" if kid else None,
    }

@router.get("/api/broker/health")
def api_broker_health():
    if not ALPACA_CLIENT: return {"ok": False, "error": "alpaca not configured"}
    return ALPACA_CLIENT.health()

@router.get("/api/broker/positions")
def api_broker_positions():
    if not ALPACA_CLIENT: return {"ok": False, "error": "alpaca not configured"}
    return ALPACA_CLIENT.positions()

@router.post("/api/broker/orders")
def api_broker_orders(payload: Dict[str, Any] = Body(...)):
    if not ALPACA_CLIENT: return {"ok": False, "error": "alpaca not configured"}
    sym   = str(payload.get("ticker", "")).upper()
    side  = str(payload.get("side", "")).lower()
    qty   = int(payload.get("qty", 0))
    limit = payload.get("limit", None)
    ext   = bool(payload.get("extended_hours", False))
    if not sym or side not in ("buy","sell") or qty <= 0:
        return {"ok": False, "error": "invalid params"}
    return ALPACA_CLIENT.submit_order(sym, side, qty, limit, extended_hours=ext)

@router.get("/api/broker/orders")
def api_broker_list_orders(status: str = Query("all"), limit: int = Query(50, ge=1, le=500)):
    if not ALPACA_CLIENT: return {"ok": False, "error": "alpaca not configured"}
    return ALPACA_CLIENT.list_orders(status=status, limit=limit)

@router.delete("/api/broker/orders/{order_id}")
def api_broker_cancel(order_id: str = Path(..., min_length=8)):
    if not ALPACA_CLIENT: return {"ok": False, "error": "alpaca not configured"}
    return ALPACA_CLIENT.cancel_order(order_id)

@router.post("/api/broker/close/{symbol}")
def api_broker_close_position(symbol: str = Path(..., min_length=1)):
    if not ALPACA_CLIENT: return {"ok": False, "error": "alpaca not configured"}
    return ALPACA_CLIENT.close_position(symbol)

@router.post("/api/broker/flatten")
def api_broker_flatten():
    if not ALPACA_CLIENT: return {"ok": False, "error": "alpaca not configured"}
    cancel = ALPACA_CLIENT.cancel_all_orders()
    close  = ALPACA_CLIENT.close_all_positions()
    return {"ok": cancel.get("ok") and close.get("ok"), "cancel": cancel, "close": close}
# ---------- Tiny HTML UI ----------
@router.get("/ui/broker", response_class=HTMLResponse)
def ui_broker():
    return """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Broker Controls</title>
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; padding: 20px; max-width: 820px; margin: 0 auto; }
    h1 { margin-top: 0; }
    .row { display: flex; gap: 8px; margin: 8px 0; align-items: center; }
    input, button { padding: 8px 10px; font-size: 14px; }
    pre { background: #111; color: #eee; padding: 12px; border-radius: 8px; overflow: auto; max-height: 360px; }
    .card { border: 1px solid #ddd; border-radius: 10px; padding: 12px; margin: 16px 0; }
  </style>
</head>
<body>
  <h1>Broker Controls</h1>

  <div class="card">
    <h3>Health</h3>
    <div class="row">
      <button onclick="hit('/api/broker/health')">Check Health</button>
    </div>
  </div>

  <div class="card">
    <h3>Close Position (Market)</h3>
    <div class="row">
      <input id="sym" placeholder="Ticker e.g. TSLA" />
      <button onclick="closeOne()">Close</button>
    </div>
  </div>

  <div class="card">
    <h3>Flatten (Cancel All + Close All)</h3>
    <div class="row">
      <button onclick="flattenAll()">FLATTEN</button>
    </div>
  </div>

  <pre id="out"></pre>

  <script>
    const out = document.getElementById('out');
    function show(x){ out.textContent = JSON.stringify(x, null, 2); }
    async function hit(url, opts){ const r = await fetch(url, opts); const j = await r.json(); show(j); }
    async function closeOne(){
      const sym = document.getElementById('sym').value.trim().toUpperCase();
      if(!sym) return alert('Enter a ticker');
      await hit('/api/broker/close/' + encodeURIComponent(sym), {method:'POST'});
    }
    async function flattenAll(){
      if(!confirm('Are you sure? This cancels ALL orders and closes ALL positions.')) return;
      await hit('/api/broker/flatten', {method:'POST'});
    }
  </script>
</body>
</html>
"""

