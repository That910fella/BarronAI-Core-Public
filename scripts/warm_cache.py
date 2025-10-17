from barronai.data.providers.polygon import PolygonProvider
import os

wl = os.getenv("WATCHLIST","TSLA,NVDA,PLTR").split(",")
wl = [t.strip() for t in wl if t.strip()]
print("warming", wl)
print(PolygonProvider().quote_snapshot(wl))
