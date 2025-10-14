from __future__ import annotations
from typing import List, Dict, Any
import hashlib, time
import feedparser
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

YF_RSS = "https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}"

# lightweight keyword tagging (expand later)
TAG_MAP = {
    "offering": ["offering","registered direct","shelf","atm"],
    "fda": ["fda","phase","trial","endpoint","approval"],
    "earnings": ["earnings","guidance","eps","revenue"],
    "contract": ["contract","award","partnership","deal"],
    "upgrade": ["upgrade","downgrade","initiates","price target"],
}

analyzer = SentimentIntensityAnalyzer()

def _hash(txt: str) -> str:
    return hashlib.sha1(txt.encode("utf-8")).hexdigest()

def _tags(text: str) -> List[str]:
    tl = text.lower()
    out = []
    for tag, kws in TAG_MAP.items():
        if any(k in tl for k in kws):
            out.append(tag)
    return out

def fetch_news(ticker: str, limit: int = 15) -> List[Dict[str, Any]]:
    url = YF_RSS.format(ticker=ticker)
    feed = feedparser.parse(url)
    items = []
    for e in feed.entries[:limit]:
        title = e.get("title","")
        link = e.get("link","")
        sid = _hash(title+link)
        vs = analyzer.polarity_scores(title)
        items.append({
            "id": sid,
            "ticker": ticker,
            "title": title,
            "link": link,
            "sentiment": vs["compound"],
            "tags": _tags(title),
            "ts": e.get("published","")
        })
    return items

def score_catalyst(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Return an aggregate catalyst score [0..1] and explanation."""
    if not items:
        return {"score": 0.0, "reason": "no-recent-headlines", "examples": []}
    # simple: top 5 headlines avg sentiment; bonus for key tags
    top = items[:5]
    sent = sum(max(min(h["sentiment"],1),-1) for h in top) / len(top)
    tag_bonus = 0.0
    for h in top:
        if any(t in {"fda","contract","upgrade","earnings"} for t in h["tags"]):
            tag_bonus += 0.05
    raw = max(0.0, min(1.0, 0.5 + 0.5*sent + tag_bonus))
    return {"score": round(raw,3), "reason": f"avg_sent={round(sent,3)}, tag_bonus={round(tag_bonus,3)}",
            "examples": [{"title":h["title"], "sent": round(h["sentiment"],3), "tags":h["tags"]} for h in top]}
