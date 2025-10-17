from __future__ import annotations
import os, json, requests, pathlib, sys
from datetime import datetime, timezone

OK = "\u2705"; WARN = "\u26A0\uFE0F"; ERR = "\u274C"

def check_env(var: str, required: bool=True):
    val = os.getenv(var, "")
    ok = bool(val) if required else True
    return {"name": var, "present": bool(val), "required": required, "value_preview": (val[:4]+"***") if val else ""}

def check_polygon():
    key = os.getenv("POLYGON_API_KEY","")
    if not key: return {"service":"polygon","ok":False,"error":"missing key"}
    try:
        url = "https://api.polygon.io/v3/reference/exchanges"
        r = requests.get(url, params={"apiKey": key}, timeout=8)
        ok = r.ok
        return {"service":"polygon","ok":ok,"code":r.status_code}
    except Exception as e:
        return {"service":"polygon","ok":False,"error":str(e)}

def check_benzinga():
    key = os.getenv("BENZINGA_API_KEY","")
    if not key: return {"service":"benzinga","ok":False,"error":"missing key (optional)"}
    try:
        url = "https://api.benzinga.com/api/v2/news"
        r = requests.get(url, params={"token": key, "channels":"general", "pagesize":1}, timeout=8)
        return {"service":"benzinga","ok":r.ok,"code":r.status_code}
    except Exception as e:
        return {"service":"benzinga","ok":False,"error":str(e)}

def check_fs():
    paths = ["tmp","tmp/journal","scans/presets"]
    out=[]
    for p in paths:
        pathlib.Path(p).mkdir(parents=True, exist_ok=True)
        out.append({"path":p, "exists": pathlib.Path(p).exists(), "writable": os.access(p, os.W_OK)})
    return out

def main():
    report = {
        "time_utc": datetime.now(timezone.utc).isoformat(),
        "env": [
            check_env("POLYGON_API_KEY"),
            check_env("BENZINGA_API_KEY", required=False),
            check_env("NOTION_API_KEY", required=False),
            check_env("SMTP_HOST", required=False),
        ],
        "services": [check_polygon(), check_benzinga()],
        "filesystem": check_fs(),
    }
    print(json.dumps(report, indent=2))
    # non-zero exit if a required piece is missing
    bad_env = [e for e in report["env"] if e["required"] and not e["present"]]
    bad_services = [s for s in report["services"] if not s["ok"] and s.get("error")!="missing key (optional)"]
    sys.exit(1 if bad_env or bad_services else 0)

if __name__ == "__main__":
    main()
