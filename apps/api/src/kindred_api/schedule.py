from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo


def plan_moment(start_date: date, day: int, local_time: time, tz: ZoneInfo) -> datetime:
    """A local wall-clock time on day N of a plan, as UTC."""
    local = datetime.combine(start_date + timedelta(days=day - 1), local_time, tz)
    return local.astimezone(UTC)
