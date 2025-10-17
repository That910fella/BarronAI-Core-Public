#!/usr/bin/env bash
set -euo pipefail
: "${BROKER_API_KEY:?BROKER_API_KEY not set}"

base="${BROKER_BASE:-http://localhost:8010}"

echo "→ ping"
curl -fsS -H "x-api-key: $BROKER_API_KEY" "$base/api/broker/ping" | jq -r '.ok' | grep -q true

echo "→ openapi has dynamic endpoints"
curl -fsS "$base/openapi.json" | jq -r '.paths | keys[]' | grep -E 'broker/orders/(bracket|oco|trailing)' >/dev/null

echo "→ trailing stop (dry call; may be held/queued at broker)"
curl -fsS -X POST "$base/api/broker/orders/trailing" \
  -H "x-api-key: $BROKER_API_KEY" -H "content-type: application/json" \
  -d '{"ticker":"TSLA","side":"sell","qty":1,"trail_percent":1.2}' >/dev/null

echo "✓ smoke passed"
