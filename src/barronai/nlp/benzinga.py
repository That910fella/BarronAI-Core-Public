from __future__ import annotations
import os, requests
from typing import List, Dict, Any
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

BENZ_API = "https://api.benzinga.com/api/v2/news"
analyzer = SentimentIntensityAnalyzer()

def fetch_benzinga(ticker: str, limit: int = 20) -> List[Dict[str, Any]]:
    token = os.getenv("BENZINGA_API_KEY","")
    if not token:
        return []
    params = {"token": token, "symbols": ticker, "pagesize": limit, "display_output": "full"}
    r = requests.get(BENZ_API, params=params, timeout=12)
    r.raise_for_status()
    out = []
    for item in r.json():
        title = item.get("title","")
        vs = analyzer.polarity_scores(title)
        tags = [cat.get("name","").lower() for cat in item.get("channels",[])]
        out.append({
            "id": item.get("id"),
            "ticker": ticker,
            "title": title,
            "link": item.get("url",""),
            "sentiment": vs["compound"],
            "tags": tags,
            "ts": item.get("created","")
        })
    return out
