
from __future__ import annotations
from typing import Optional, Any, Dict
from fastapi import APIRouter, Body, Depends, Header, HTTPException
import os, json

# Header guard
BROKER_API_KEY = os.getenv("BROKER_API_KEY")
def require_broker_key(x_api_key: Optional[str] = Header(default=None)):
    if BROKER_API_KEY and x_api_key != BROKER_API_KEY:
        raise HTTPException(status_code=401, detail="invalid API key")

api = APIRouter(dependencies=[Depends(require_broker_key)])
ALPACA_CLIENT = None  # set by mount_dynamic_routes()

def _orders_post(body: Dict[str, Any]) -> Dict[str, Any]:
    try:
        r = ALPACA_CLIENT._req("POST", "/orders", data=json.dumps(body))  # type: ignore[attr-defined]
        return ALPACA_CLIENT._ok({"raw": r.json()}) if r.ok else ALPACA_CLIENT._bad(r)  # type: ignore[attr-defined]
    except Exception as e:
        return {"ok": False, "error": f"client_post_failed: {e}"}

def _submit_bracket(symbol: str, side: str, qty: int,
                    take_profit: float, stop_loss: float,
                    stop_limit: Optional[float],
                    tif: str, extended_hours: bool) -> Dict[str, Any]:
    take_profit = round(float(take_profit) + 1e-9, 2)
    stop_loss   = round(float(stop_loss)   + 1e-9, 2)
    if stop_limit is not None:
        stop_limit = round(float(stop_limit) + 1e-9, 2)
    body: Dict[str, Any] = {
        "symbol": symbol.upper(),
        "side": side.lower(),
        "qty": qty,
        "type": "market",
        "time_in_force": tif,
        "extended_hours": extended_hours,
        "order_class": "bracket",
        "take_profit": {"limit_price": take_profit},
        "stop_loss":   {"stop_price":  stop_loss},
    }
    if stop_limit is not None:
        body["stop_loss"]["limit_price"] = stop_limit
    return _orders_post(body)

def _submit_oco(symbol: str, side: str, qty: int,
                take_profit: float, stop_loss: float,
                stop_limit: Optional[float],
                tif: str, extended_hours: bool) -> Dict[str, Any]:
    take_profit = round(float(take_profit) + 1e-9, 2)
    stop_loss   = round(float(stop_loss)   + 1e-9, 2)
    if stop_limit is not None:
        stop_limit = round(float(stop_limit) + 1e-9, 2)
    body: Dict[str, Any] = {
        "symbol": symbol.upper(),
        "side": side.lower(),
        "qty": qty,
        "type": "limit",             # parent must be limit for OCO
        "limit_price": take_profit,  # TP as parent limit
        "time_in_force": tif,
        "extended_hours": extended_hours,
        "order_class": "oco",
        "take_profit": {"limit_price": take_profit},
        "stop_loss":   {"stop_price":  stop_loss},
    }
    if stop_limit is not None:
        body["stop_loss"]["limit_price"] = stop_limit
    return _orders_post(body)

def _submit_trailing(symbol: str, side: str, qty: int,
                     trail_price: Optional[float], trail_percent: Optional[float],
                     tif: str, extended_hours: bool) -> Dict[str, Any]:
    if trail_price is None and trail_percent is None:
        return {"ok": False, "error": "need trail_price or trail_percent"}
    body: Dict[str, Any] = {
        "symbol": symbol.upper(),
        "side": side.lower(),
        "qty": qty,
        "type": "trailing_stop",
        "time_in_force": tif,
        "extended_hours": extended_hours,
    }
    if trail_price  is not None: body["trail_price"]   = float(trail_price)
    if trail_percent is not None: body["trail_percent"] = float(trail_percent)
    return _orders_post(body)

@api.post("/api/broker/orders/bracket")
def api_broker_bracket(payload: Dict[str, Any] = Body(...)):
    if not ALPACA_CLIENT: return {"ok": False, "error": "alpaca not configured"}
    sym  = str(payload.get("ticker","")).upper()
    side = str(payload.get("side","buy")).lower()
    qty  = int(payload.get("qty", 0))
    tif  = str(payload.get("tif","day")).lower()
    ext  = bool(payload.get("extended_hours", False))
    if not sym or side not in ("buy","sell") or qty <= 0:
        return {"ok": False, "error": "invalid params (need ticker, side in {buy,sell}, qty>0)"}

    tp   = payload.get("take_profit")
    sl   = payload.get("stop_loss")
    sll  = payload.get("stop_limit")

    basis  = payload.get("basis")
    tppct  = payload.get("take_profit_pct")
    slpct  = payload.get("stop_loss_pct")
    atr    = payload.get("atr")
    m_tp   = payload.get("atr_mult_tp")
    m_sl   = payload.get("atr_mult_sl")

    if tp is not None and sl is not None:
        tp_f, sl_f = float(tp), float(sl)
    elif basis is not None and tppct is not None and slpct is not None:
        b = float(basis); tpp = float(tppct); slp = float(slpct)
        tp_f, sl_f = (b*(1+tpp), b*(1-slp)) if side=="buy" else (b*(1-tpp), b*(1+slp))
    elif basis is not None and atr is not None and m_tp is not None and m_sl is not None:
        b = float(basis); a = float(atr); mtp = float(m_tp); msl = float(m_sl)
        tp_f, sl_f = (b + mtp*a, b - msl*a) if side=="buy" else (b - mtp*a, b + msl*a)
    else:
        return {"ok": False, "error": "provide (take_profit & stop_loss) OR (basis & take_profit_pct & stop_loss_pct) OR (basis & atr & atr_mult_tp & atr_mult_sl)"}

    return _submit_bracket(sym, side, qty, tp_f, sl_f, float(sll) if sll is not None else None, tif, ext)

@api.post("/api/broker/orders/oco")
def api_broker_oco(payload: Dict[str, Any] = Body(...)):
    if not ALPACA_CLIENT: return {"ok": False, "error": "alpaca not configured"}
    sym  = str(payload.get("ticker","")).upper()
    side = str(payload.get("side","sell")).lower()
    qty  = int(payload.get("qty", 0))
    tif  = str(payload.get("tif","day")).lower()
    ext  = bool(payload.get("extended_hours", False))
    if not sym or side not in ("buy","sell") or qty <= 0:
        return {"ok": False, "error": "invalid params (need ticker, side in {buy,sell}, qty>0)"}

    tp   = payload.get("take_profit")
    sl   = payload.get("stop_loss")
    sll  = payload.get("stop_limit")

    basis  = payload.get("basis")
    tppct  = payload.get("take_profit_pct")
    slpct  = payload.get("stop_loss_pct")
    atr    = payload.get("atr")
    m_tp   = payload.get("atr_mult_tp")
    m_sl   = payload.get("atr_mult_sl")

    if tp is not None and sl is not None:
        tp_f, sl_f = float(tp), float(sl)
    elif basis is not None and tppct is not None and slpct is not None:
        b = float(basis); tpp = float(tppct); slp = float(slpct)
        tp_f, sl_f = (b*(1-tpp), b*(1+slp)) if side=="sell" else (b*(1+tpp), b*(1-slp))
    elif basis is not None and atr is not None and m_tp is not None and m_sl is not None:
        b = float(basis); a = float(atr); mtp = float(m_tp); msl = float(m_sl)
        tp_f, sl_f = (b - mtp*a, b + msl*a) if side=="sell" else (b + mtp*a, b - msl*a)
    else:
        return {"ok": False, "error": "provide (take_profit & stop_loss) OR (basis & take_profit_pct & stop_loss_pct) OR (basis & atr & atr_mult_tp & atr_mult_sl)"}

    return _submit_oco(sym, side, qty, tp_f, sl_f, float(sll) if sll is not None else None, tif, ext)

@api.post("/api/broker/orders/trailing")
def api_broker_trailing(payload: Dict[str, Any] = Body(...)):
    if not ALPACA_CLIENT: return {"ok": False, "error": "alpaca not configured"}
    sym  = str(payload.get("ticker","")).upper()
    side = str(payload.get("side","sell")).lower()
    qty  = int(payload.get("qty", 0))
    tif  = str(payload.get("tif","day")).lower()
    ext  = bool(payload.get("extended_hours", False))
    tprice = payload.get("trail_price")
    tpct   = payload.get("trail_percent")
    if not sym or side not in ("buy","sell") or qty <= 0:
        return {"ok": False, "error": "invalid params (need ticker, side in {buy,sell}, qty>0)"}
    return _submit_trailing(sym, side, qty,
                            float(tprice) if tprice is not None else None,
                            float(tpct)   if tpct   is not None else None,
                            tif, ext)

def mount_dynamic_routes(app, alpaca_client):
    global ALPACA_CLIENT
    ALPACA_CLIENT = alpaca_client
    app.include_router(api)
