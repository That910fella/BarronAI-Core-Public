from datetime import datetime, time
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")

def now_et() -> datetime:
    return datetime.now(tz=ET)

def is_rth(dt: datetime) -> bool:
    t = dt.timetz()
    return time(9,30,0, tzinfo=ET) <= t <= time(16,0,0, tzinfo=ET)

def is_power_hour(dt: datetime) -> bool:
    t = dt.timetz()
    early = time(9,30,0, tzinfo=ET) <= t <= time(11,30,0, tzinfo=ET)
    late  = time(14,0,0, tzinfo=ET) <= t <= time(16,0,0, tzinfo=ET)
    return early or late
