from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from clinic.services.slots import slot_starts

NBO = ZoneInfo("Africa/Nairobi")
UTC = ZoneInfo("UTC")


def test_full_grid_9_to_17():
    slots = slot_starts(date(2026, 7, 15), time(9), time(17), NBO)
    assert len(slots) == 16
    assert slots[0].utcoffset().total_seconds() == 0  # returned in UTC
    assert slots[0] == datetime(2026, 7, 15, 6, 0, tzinfo=UTC)  # 09:00 Nairobi
    assert slots[-1] == datetime(2026, 7, 15, 13, 30, tzinfo=UTC)  # 16:30 Nairobi


def test_partial_tail_is_floored():
    slots = slot_starts(date(2026, 7, 15), time(9), time(17, 15), NBO)
    assert len(slots) == 16
