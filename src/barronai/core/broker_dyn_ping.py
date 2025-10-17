from fastapi import APIRouter, Depends
from .auth import require_broker_key  # uses your existing guard

api_ping = APIRouter(dependencies=[Depends(require_broker_key)])

@api_ping.get("/api/broker/ping")
def broker_ping():
    return {"ok": True, "routes": ["bracket", "oco", "trailing"]}

def mount_ping(app):
    # mount-only file; keeps changes small and safe
    app.include_router(api_ping)
