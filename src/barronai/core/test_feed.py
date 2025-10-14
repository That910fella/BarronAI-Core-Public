from ..data.provider import get_provider
from ..agents import pattern_scanner as ps
import pandas as pd

TICKERS = ["AAPL","AMD","TSLA","NVDA","PLTR","SOFI"]  # swap for your watchlist

def main():
    prov = get_provider("yahoo")
    df = prov.quote_snapshot(TICKERS).fillna(method="ffill")
    print("RAW COLS:", list(df.columns))
    # run one scan just to see shape
    out = ps.scan_basic_gainer(df)
    print("BASIC_GAINER:", list(out.get("ticker", [])))

if __name__ == "__main__":
    main()
