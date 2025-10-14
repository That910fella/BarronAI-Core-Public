from __future__ import annotations
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import json, csv, os
from datetime import datetime, timezone

app = FastAPI()

def _read_jsonl(path: str, limit: int = 200):
    out = []
    if not os.path.exists(path): return out
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                out.append(json.loads(line))
            except Exception:
                continue
    out = out[-limit:]
    return out

def _read_csv(path: str, limit: int = 200):
    out = []
    if not os.path.exists(path): return out
    with open(path, "r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        out = list(r)[-limit:]
    return out

@app.get("/api/signals")
def api_signals():
    return _read_jsonl("tmp/journal/signals.jsonl")

@app.get("/api/plans")
def api_plans():
    return _read_csv("tmp/journal/plans.csv")

@app.get("/", response_class=HTMLResponse)
def home():
    return """<!doctype html>
<html>
<head><meta charset="utf-8"><title>Barron.AI Dashboard</title></head>
<body style="font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; padding: 20px;">
  <h1>Barron.AI Dashboard</h1>
  <div id="signals"><h2>Signals (latest)</h2><pre>Loading...</pre></div>
  <div id="plans"><h2>Plans (latest)</h2><pre>Loading...</pre></div>
<script>
async function load() {
  const s = await fetch('/api/signals').then(r=>r.json());
  const p = await fetch('/api/plans').then(r=>r.json());
  document.querySelector('#signals pre').textContent = JSON.stringify(s.slice(-20), null, 2);
  document.querySelector('#plans pre').textContent = JSON.stringify(p.slice(-20), null, 2);
}
load(); setInterval(load, 10000);
</script>
</body></html>"""
