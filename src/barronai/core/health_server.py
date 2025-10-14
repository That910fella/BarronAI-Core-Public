from fastapi import FastAPI
from .config import settings
from .logger import setup_logger

logger = setup_logger()
app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok", "env": settings.ENV}
