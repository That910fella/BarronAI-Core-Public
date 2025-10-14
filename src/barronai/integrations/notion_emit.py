from __future__ import annotations
import os, requests

NOTION_API = "https://api.notion.com/v1/pages"

def send_signal_to_notion(signal, *, database_id: str | None = None):
    if not os.getenv("NOTION_ENABLED","False").lower() in {"1","true","yes"}:
        return {"status":"disabled"}
    token = os.getenv("NOTION_API_KEY")
    dbid  = database_id or os.getenv("NOTION_SIGNALS_DB_ID")
    if not token or not dbid:
        return {"status":"missing-config"}
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    payload = {
      "parent": {"database_id": dbid},
      "properties": {
        "Ticker": {"title": [{"text": {"content": signal.ticker}}]},
        "Score": {"number": signal.score},
        "PowerHour": {"checkbox": signal.gated},
      }
    }
    r = requests.post(NOTION_API, headers=headers, json=payload, timeout=15)
    return {"status": r.status_code, "text": r.text[:200]}
