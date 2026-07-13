"""30-minute slot-grid math for generating available appointment times, in local clinic time"""

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

SLOT = timedelta(minutes=30)
UTC = ZoneInfo("UTC")


def slot_starts(day: date, start: time, end: time, tz: ZoneInfo) -> list[datetime]:
    """Whole 30-min slot starts for start and end times on day, returned in UTC"""
    cursor = datetime.combine(day, start, tzinfo=tz)
    limit = datetime.combine(day, end, tzinfo=tz)
    out = []
    while cursor + SLOT <= limit:
        out.append(cursor.astimezone(UTC))
        cursor += SLOT
    return out
