from datetime import datetime, timezone


def utc_now() -> datetime:
    """Return an aware UTC timestamp for persistence and runtime comparisons."""
    return datetime.now(timezone.utc)


def as_utc(value: datetime) -> datetime:
    """Normalize timestamps read from both timezone-aware and legacy-naive stores."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
