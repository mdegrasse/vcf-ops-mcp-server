from __future__ import annotations

from datetime import datetime, timezone


def to_epoch_millis(value: str | int | float) -> int:
    """Accept an ISO 8601 timestamp or an epoch value (seconds or millis) and
    return epoch milliseconds, as the VCF Operations API expects."""
    if isinstance(value, (int, float)):
        # Heuristic: treat 13-digit-scale numbers as already-millis.
        return int(value) if value > 10_000_000_000 else int(value * 1000)
    text = value.strip()
    if text.isdigit():
        return to_epoch_millis(int(text))
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def from_epoch_millis(value: int | float | None) -> str | None:
    if value is None:
        return None
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc).isoformat()
