from __future__ import annotations
from .providers.yahoo import YahooProvider
# Future: polygon, alpaca-marketdata, finnhub adapters

def get_provider(name: str = "yahoo"):
    if name == "yahoo":
        return YahooProvider()
    raise ValueError(f"Unknown provider {name}")
