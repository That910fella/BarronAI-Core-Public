STATUS ?= all
LIMIT  ?= 50

.PHONY: dash broker-health broker-buy broker-sell broker-buy-mkt broker-sell-mkt broker-orders broker-order broker-cancel broker-close broker-flatten

dash:
	@bash -lc 'set -a; [[ -f .env ]] && source ./.env; set +a; PYTHONPATH=./src python -m uvicorn barronai.core.dashboard:app --host 0.0.0.0 --port 8010'
broker-health:
	@curl -s localhost:8010/api/broker/health | jq

broker-buy:
	@curl -s -X POST localhost:8010/api/broker/orders \
	  -H 'content-type: application/json' \
	  -d '{"ticker":"$(TICKER)","side":"buy","qty":$(QTY),"limit":$(LIMIT),"extended_hours":$(EXT)}' | jq

broker-sell:
	@curl -s -X POST localhost:8010/api/broker/orders \
	  -H 'content-type: application/json' \
	  -d '{"ticker":"$(TICKER)","side":"sell","qty":$(QTY),"limit":$(LIMIT),"extended_hours":$(EXT)}' | jq

broker-buy-mkt:
	@curl -s -X POST localhost:8010/api/broker/orders \
	  -H 'content-type: application/json' \
	  -d '{"ticker":"$(TICKER)","side":"buy","qty":$(QTY)}' | jq

broker-sell-mkt:
	@curl -s -X POST localhost:8010/api/broker/orders \
	  -H 'content-type: application/json' \
	  -d '{"ticker":"$(TICKER)","side":"sell","qty":$(QTY)}' | jq

broker-orders:
	@curl -s "localhost:8010/api/broker/orders?status=$(STATUS)&limit=$(LIMIT)" | jq

broker-order:
	@curl -s "localhost:8010/api/broker/orders/$(ID)" | jq

broker-cancel:
	@curl -s -X DELETE "localhost:8010/api/broker/orders/$(ID)" | jq

broker-close:
	@curl -s -X POST "localhost:8010/api/broker/close/$(TICKER)" | jq

broker-flatten:
	@curl -s -X POST "localhost:8010/api/broker/flatten" | jq

.PHONY: broker-close broker-flatten
broker-close:
	@curl -s -X POST "localhost:8010/api/broker/close/$(TICKER)" | jq

broker-flatten:
	@curl -s -X POST "localhost:8010/api/broker/flatten" | jq
SHELL := bash

smoke:
	./scripts/smoke.sh

