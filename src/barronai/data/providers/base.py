from __future__ import annotations
from typing import Protocol, Iterable
import pandas as pd

class MarketDataProvider(Protocol):
    def quote_snapshot(self, tickers: Iterable[str]) -> pd.DataFrame:
        """Return a row per ticker with at least these columns:
        ticker, last, volume, float, day_high, vwap, pct_change,
        spread_pct, dollar_volume, rel_volume, yesterday_volume,
        fifty_two_week_high, atr
        """
        ...
