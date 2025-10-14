from __future__ import annotations
import os, json
from .notion_emit import send_signal_to_notion
from .email_emit import send_email

SCORE_THRESHOLD = float(os.getenv("ALERT_SCORE_THRESHOLD", "0.60"))
PRIORITY_TAGS = {t.strip().lower() for t in os.getenv("ALERT_PRIORITY_TAGS","fda,earnings,contract,upgrade").split(",") if t}

def maybe_alert(signal, *, reasons: dict):
    # reasons is expected to contain catalyst examples with any "tags"
    hit_tag = False
    for ex in reasons.get("examples", []):
        tags = {t.lower() for t in ex.get("tags", [])}
        if tags & PRIORITY_TAGS:
            hit_tag = True
            break

    if signal.score >= SCORE_THRESHOLD or hit_tag:
        # Notion
        notion_res = send_signal_to_notion(signal)
        # Email (optional)
        body = json.dumps({"ticker":signal.ticker, "score":signal.score, "gated":signal.gated, "reasons":reasons}, indent=2)[:5000]
        email_res = send_email(subject=f"[Barron.AI] {signal.ticker} score={signal.score}", body=body)
        return {"notion": notion_res, "email": email_res, "trigger": "tag" if hit_tag else "score"}
    return {"skipped": True}
