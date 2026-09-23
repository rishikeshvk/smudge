from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo


def unlock_at(start_date: date, day: int, study_time: time, tz: ZoneInfo) -> datetime:
    local = datetime.combine(start_date + timedelta(days=day - 1), study_time, tz)
    return local.astimezone(UTC)
