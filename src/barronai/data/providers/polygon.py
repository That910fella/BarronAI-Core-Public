from __future__ import annotations
import os, requests, math, time, json
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone, date
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from ..float_enricher import pick_float, yahoo_float

try:
    import yfinance as yf
except Exception:
    yf = None

API = "https://api.polygon.io"
CACHE_DIR = Path("tmp/cache/aggs"); CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL_SECONDS = int(os.getenv("AGGS_CACHE_TTL","90"))
DEBUG = os.getenv("DEBUG","0") in {"1","true","True","YES","yes"}
SNAPSHOT_OK = os.getenv("SNAPSHOT_OK","0") in {"1","true","True","YES","yes"}    # polygon snapshot off on free tier
POLY_INTRADAY = os.getenv("POLY_INTRADAY","1") in {"1","true","True","YES","yes"}  # set 0 to force yf

def _log(*a): 
    if DEBUG: print("[polygon]", *a)

@retry(reraise=True, stop=stop_after_attempt(2), wait=wait_exponential(multiplier=0.5, max=2),
       retry=retry_if_exception_type(Exception))
def _get(path: str, params: dict | None=None):
    params = params or {}; params["apiKey"] = os.getenv("POLYGON_API_KEY","")
    r = requests.get(API+path, params=params, timeout=8)
    if not r.ok: _log(f"HTTP {r.status_code}", path, r.text[:160])
    r.raise_for_status()
    return r.json()

def _today_range_ms() -> tuple[int,int]:
    now = datetime.now(timezone.utc)
    start = int(datetime(now.year, now.month, now.day, tzinfo=timezone.utc).timestamp() * 1000)
    end   = int(now.timestamp() * 1000)
    return start, end

def _save_cache_json(path: Path, rows: list[dict]):
    try:
        tmp = path.with_suffix(".tmp"); tmp.write_text(json.dumps(rows)); tmp.replace(path)
    except Exception as e: _log("cache write failed", path, e)

def _load_cache_json(path: Path) -> list[dict]:
    try: return json.loads(path.read_text())
    except Exception: return []

def _flatten_yf(df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """Make sure columns are 1-D (no MultiIndex). Select the 'ticker' slice if needed."""
    if isinstance(df.columns, pd.MultiIndex):
        # prefer selecting by ticker if present at any level
        for lvl in range(df.columns.nlevels)[::-1]:
            try:
                if ticker in df.columns.get_level_values(lvl):
                    df = df.xs(ticker, axis=1, level=lvl, drop_level=True)
                    break
            except Exception:
                pass
        # if still MultiIndex, drop to first level names only
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
    return df

def _yf_intraday_df(t: str) -> pd.DataFrame:
    """Fallback: yfinance 1m bars for today; returns columns t,o,h,l,c,v,vw."""
    if yf is None: return pd.DataFrame()
    try:
        df = yf.download(t, period="1d", interval="1m", prepost=False, progress=False, auto_adjust=False)
        if df is None or df.empty: return pd.DataFrame()
        df = _flatten_yf(df, t)

        # normalize timezone to UTC
        idx = df.index
        if getattr(idx, "tz", None) is None:
            idx = idx.tz_localize("UTC", nonexistent="shift_forward", ambiguous="NaT")
        else:
            idx = idx.tz_convert("UTC")

        # ensure 1-D arrays
        o = pd.Series(df["Open"], index=idx).astype(float).to_numpy().ravel()
        h = pd.Series(df["High"], index=idx).astype(float).to_numpy().ravel()
        l = pd.Series(df["Low"],  index=idx).astype(float).to_numpy().ravel()
        c = pd.Series(df["Close"],index=idx).astype(float).to_numpy().ravel()
        v = pd.Series(df["Volume"],index=idx).fillna(0).astype(float).to_numpy().ravel()
        tms = (pd.Index(idx).asi8 // 1_000_000).astype("int64")

        out = pd.DataFrame({"t": tms, "o": o, "h": h, "l": l, "c": c, "v": v})
        out["vw"] = (out["h"] + out["l"] + out["c"]) / 3.0
        # sort descending by time to match our downstream assumption
        out = out.sort_values("t", ascending=False).reset_index(drop=True)
        return out
    except Exception as e:
        _log("yfinance fallback failed", t, e)
        return pd.DataFrame()

def _aggs_today_cached(t: str) -> tuple[pd.DataFrame, str]:
    """Return (df, source) where source ∈ {'live','cache','yf','none'}."""
    cache_path = CACHE_DIR / f"{t.upper()}.json"
    now = time.time()

    # 1) fresh cache
    if cache_path.exists():
        age = now - cache_path.stat().st_mtime
        if age <= CACHE_TTL_SECONDS:
            rows = _load_cache_json(cache_path)
            if rows: return pd.DataFrame(rows), "cache"

    # 2) polygon live (free tier often 403/429)
    if POLY_INTRADAY:
        try:
            s,e = _today_range_ms()
            res = _get(f"/v2/aggs/ticker/{t}/range/1/minute/{s}/{e}",
                       {"adjusted":"true","sort":"desc","limit":390})
            rows = res.get("results", []) or []
            if rows:
                _save_cache_json(cache_path, rows)
                return pd.DataFrame(rows), "live"
        except requests.HTTPError as he:
            code = getattr(he.response, "status_code", 0)
            if code in (401,403,429,400):
                _log("live fetch blocked; using yfinance", t, code)
            else:
                _log("live fetch failed hard", t, he)
        except Exception as e:
            _log("live fetch failed; using yfinance", t, e)

    # 3) yfinance fallback
    df = _yf_intraday_df(t)
    if not df.empty:
        _save_cache_json(cache_path, df.to_dict(orient="records"))
        return df, "yf"

    # 4) stale cache last resort
    if cache_path.exists():
        rows = _load_cache_json(cache_path)
        if rows: return pd.DataFrame(rows), "cache"

    return pd.DataFrame(), "none"

def _shares_outstanding(t: str) -> float | None:
    try:
        res = _get(f"/v3/reference/tickers/{t}", {"date": date.today().isoformat()})
        r = res.get("results", {}) or {}
        return float(r.get("weighted_shares_outstanding") or r.get("share_class_shares") or 0.0) or None
    except Exception:
        return None

def _rvol_and_ema20(df: pd.DataFrame) -> tuple[float|float("nan"), float|float("nan")]:
    try:
        if df.empty: return math.nan, math.nan
        # df sorted desc: use first bar as "last"
        last_vol = float(df["v"].iloc[0])
        avg_vol  = float(df["v"].rolling(30).mean().iloc[0]) if len(df) >= 30 else float(df["v"].mean())
        rvol = (last_vol/avg_vol) if avg_vol else math.nan
        ema20 = float(df["c"].iloc[::-1].ewm(span=20, adjust=False).mean().iloc[-1])  # compute on asc
        return rvol, ema20
    except Exception:
        return math.nan, math.nan

class PolygonProvider:
    def __init__(self): ...

    def _one(self, t: str) -> dict:
        last = day_high = vwap_day = math.nan
        volume = 0
        prev_close = math.nan

        if SNAPSHOT_OK:
            try:
                snap = _get(f"/v2/snapshot/locale/us/markets/stocks/tickers/{t}")
                s = snap.get("ticker", {}) or {}
                last = float(s.get("lastTrade", {}).get("p") or s.get("lastQuote", {}).get("P") or math.nan)
                day_high = float(s.get("day", {}).get("h") or math.nan)
                vwap_day = float(s.get("day", {}).get("vw") or math.nan)
                volume = int(s.get("day", {}).get("v") or 0)
                prev_close = float(s.get("prevDay", {}).get("c") or math.nan)
            except Exception as e:
                _log("snapshot error; using aggs/yf", t, e)

        aggs, src = _aggs_today_cached(t)
        if not aggs.empty:
            aggs = aggs.sort_values("t", ascending=False).reset_index(drop=True)
            if math.isnan(last):
                last = float(aggs["c"].iloc[0])
            vwap_bar = float(aggs["vw"].iloc[0]) if "vw" in aggs and pd.notna(aggs["vw"].iloc[0]) else math.nan
            if math.isnan(day_high):
                try: day_high = float(aggs["h"].max())
                except Exception: pass
            if not volume:
                try: volume = int(float(aggs["v"].sum()))
                except Exception: pass
        else:
            vwap_bar = math.nan
            src = "none"

        float_shares = _shares_outstanding(t)
        dv = (last or 0.0) * (volume or 0)
        rvol, ema20 = _rvol_and_ema20(aggs if not aggs.empty else pd.DataFrame())
        pct_change = ((last - prev_close)/prev_close*100.0) if (prev_close and not math.isnan(prev_close) and last) else math.nan

        return {
            "ticker": t,
            "last": last,
            "volume": volume if volume else math.nan,
            "float": pick_float(float_shares, yahoo_float(t)),
            "day_high": day_high,
            "vwap": vwap_bar if not math.isnan(vwap_bar) else vwap_day,
            "pct_change": pct_change,
            "spread_pct": 0.6,
            "dollar_volume": dv if dv else math.nan,
            "rel_volume": rvol,
            "ema20": ema20,
            "yesterday_volume": 0,
            "fifty_two_week_high": math.nan,
            "atr": math.nan,
            "agg_source": src
        }

    def quote_snapshot(self, tickers):
        rows = []
        for t in tickers:
            try: rows.append(self._one(t))
            except Exception as e: _log("row error", t, e)
        return pd.DataFrame(rows)
