from __future__ import annotations
from .providers.yahoo import YahooProvider
from .providers.polygon import PolygonProvider

def get_provider(name: str = "yahoo"):
    name = (name or "yahoo").lower()
    if name == "yahoo":
        return YahooProvider()
    if name == "polygon":
        return PolygonProvider()
    raise ValueError(f"Unknown provider {name}")
