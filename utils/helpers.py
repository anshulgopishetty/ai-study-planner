# utils/helpers.py
# ─────────────────────────────────────────────
# Shared helper functions used across the app
# ─────────────────────────────────────────────

from datetime import date, datetime, timedelta
import pandas as pd


def days_until_exam(exam_date_str: str) -> int:
    """Return how many days remain until the exam date."""
    try:
        exam_date = pd.to_datetime(exam_date_str).date()
        delta = exam_date - date.today()
        return max(delta.days, 0)
    except Exception:
        return 0


def format_date(date_str: str, fmt: str = "%B %d, %Y") -> str:
    """Convert a date string to a human-readable format."""
    try:
        return pd.to_datetime(date_str).strftime(fmt)
    except Exception:
        return str(date_str)


def format_hours(hours: float) -> str:
    """Convert decimal hours to a readable string like '1h 30m'."""
    total_minutes = int(hours * 60)
    h = total_minutes // 60
    m = total_minutes % 60
    if h > 0 and m > 0:
        return f"{h}h {m}m"
    elif h > 0:
        return f"{h}h"
    else:
        return f"{m}m"


def get_urgency_label(days_left: int) -> tuple[str, str]:
    """
    Return (label, color) based on days until exam.
    Used for UI badges and indicators.
    """
    if days_left <= 3:
        return "🔴 Critical", "#FF4444"
    elif days_left <= 7:
        return "🟠 Urgent", "#FF8C00"
    elif days_left <= 14:
        return "🟡 Soon", "#FFD700"
    else:
        return "🟢 Comfortable", "#32CD32"


def get_date_range(start: date, end: date) -> list[date]:
    """Return a list of dates from start to end (inclusive)."""
    dates = []
    current = start
    while current <= end:
        dates.append(current)
        current += timedelta(days=1)
    return dates


def is_valid_exam_date(exam_date_str: str) -> bool:
    """Check that the exam date is in the future."""
    try:
        exam_date = pd.to_datetime(exam_date_str).date()
        return exam_date > date.today()
    except Exception:
        return False


def calculate_progress_percentage(completed: int, total: int) -> float:
    """Safely calculate percentage without divide-by-zero."""
    if total == 0:
        return 0.0
    return round((completed / total) * 100, 1)


def generate_id(prefix: str = "") -> str:
    """Generate a simple timestamp-based unique ID."""
    ts = datetime.now().strftime("%Y%m%d%H%M%S%f")
    return f"{prefix}{ts}"
