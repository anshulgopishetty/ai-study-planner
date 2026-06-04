# core/data_manager.py
# ─────────────────────────────────────────────
# Handles all data loading and saving via Pandas
# This is the ONLY place that reads/writes CSVs
# ─────────────────────────────────────────────

import os
import pandas as pd
from datetime import datetime

from utils.constants import (
    DATA_DIR,
    SUBJECTS_FILE, SCHEDULE_FILE, SESSIONS_FILE,
    SUBJECTS_COLUMNS, SCHEDULE_COLUMNS, SESSIONS_COLUMNS,
)
from utils.helpers import generate_id


# ── Initialisation ───────────────────────────

def init_data_files():
    """
    Create the data directory and empty CSV files
    if they don't already exist.
    Called once when the app starts.
    """
    os.makedirs(DATA_DIR, exist_ok=True)

    if not os.path.exists(SUBJECTS_FILE):
        pd.DataFrame(columns=SUBJECTS_COLUMNS).to_csv(SUBJECTS_FILE, index=False)

    if not os.path.exists(SCHEDULE_FILE):
        pd.DataFrame(columns=SCHEDULE_COLUMNS).to_csv(SCHEDULE_FILE, index=False)

    if not os.path.exists(SESSIONS_FILE):
        pd.DataFrame(columns=SESSIONS_COLUMNS).to_csv(SESSIONS_FILE, index=False)


# ── Subject CRUD ─────────────────────────────

def load_subjects() -> pd.DataFrame:
    """Load all subjects from CSV.

    Safely handles mixed date formats that may exist in older data
    (e.g. '2026-06-18 00:00:00' vs '2026-06-18').
    All exam_date values are normalised to timezone-naive datetime
    so downstream comparisons never raise a parsing error.
    """
    try:
        df = pd.read_csv(SUBJECTS_FILE)
        if df.empty:
            return pd.DataFrame(columns=SUBJECTS_COLUMNS)
        # infer_datetime_format=False + errors='coerce' gracefully handles
        # every Pandas-recognised format; NaT rows are dropped so the rest
        # of the app never receives an unparseable date.
        df["exam_date"] = pd.to_datetime(df["exam_date"], errors="coerce")
        df = df.dropna(subset=["exam_date"])
        # Strip any time component — dates only, no tz offset.
        df["exam_date"] = df["exam_date"].dt.normalize()
        return df
    except Exception:
        return pd.DataFrame(columns=SUBJECTS_COLUMNS)


def add_subject(name: str, exam_date: str, daily_hours: float,
                priority: str, color: str) -> bool:
    """Add a new subject. Returns True on success.

    exam_date is normalised to YYYY-MM-DD before writing so the CSV
    never accumulates mixed formats (e.g. '2026-06-18 00:00:00').
    """
    try:
        df = load_subjects()

        # Prevent duplicate subject names
        if name.strip().lower() in df["name"].str.lower().values:
            return False

        # Normalise to plain YYYY-MM-DD string — no time component.
        normalised_date = pd.to_datetime(exam_date).strftime("%Y-%m-%d")

        new_row = {
            "id": generate_id("SUB"),
            "name": name.strip(),
            "exam_date": normalised_date,
            "daily_hours": daily_hours,
            "priority": priority,
            "color": color,
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        # Write exam_date as plain string (already YYYY-MM-DD) so Pandas
        # does not add a time component when serialising datetime columns.
        df["exam_date"] = df["exam_date"].apply(
            lambda d: pd.to_datetime(d).strftime("%Y-%m-%d")
        )
        df.to_csv(SUBJECTS_FILE, index=False)
        return True
    except Exception as e:
        print(f"Error adding subject: {e}")
        return False


def delete_subject(subject_id: str) -> bool:
    """Delete a subject by ID."""
    try:
        df = load_subjects()
        df = df[df["id"] != subject_id]
        df.to_csv(SUBJECTS_FILE, index=False)
        return True
    except Exception:
        return False


def update_subject(subject_id: str, **kwargs) -> bool:
    """Update fields of an existing subject by ID."""
    try:
        df = load_subjects()
        for key, value in kwargs.items():
            if key in df.columns:
                df.loc[df["id"] == subject_id, key] = value
        df.to_csv(SUBJECTS_FILE, index=False)
        return True
    except Exception:
        return False


# ── Schedule CRUD ────────────────────────────

def load_schedule() -> pd.DataFrame:
    """Load the generated schedule from CSV."""
    try:
        df = pd.read_csv(SCHEDULE_FILE)
        if df.empty:
            return pd.DataFrame(columns=SCHEDULE_COLUMNS)
        df["date"] = pd.to_datetime(df["date"])
        return df
    except Exception:
        return pd.DataFrame(columns=SCHEDULE_COLUMNS)


def save_schedule(schedule_df: pd.DataFrame) -> bool:
    """Overwrite the schedule CSV with new data."""
    try:
        schedule_df.to_csv(SCHEDULE_FILE, index=False)
        return True
    except Exception:
        return False


def clear_schedule() -> bool:
    """Delete all schedule entries."""
    try:
        pd.DataFrame(columns=SCHEDULE_COLUMNS).to_csv(SCHEDULE_FILE, index=False)
        return True
    except Exception:
        return False


# ── Session CRUD ─────────────────────────────

def load_sessions() -> pd.DataFrame:
    """Load all tracked study sessions from CSV."""
    try:
        df = pd.read_csv(SESSIONS_FILE)
        if df.empty:
            return pd.DataFrame(columns=SESSIONS_COLUMNS)
        df["date"] = pd.to_datetime(df["date"])
        return df
    except Exception:
        return pd.DataFrame(columns=SESSIONS_COLUMNS)


def save_sessions(sessions_df: pd.DataFrame) -> bool:
    """Overwrite the sessions CSV with updated data."""
    try:
        sessions_df.to_csv(SESSIONS_FILE, index=False)
        return True
    except Exception:
        return False


def mark_session_complete(schedule_id: str, notes: str = "") -> bool:
    """
    Mark a scheduled session as completed.
    Creates a new entry in sessions.csv.
    """
    try:
        schedule_df = load_schedule()
        row = schedule_df[schedule_df["id"] == schedule_id]
        if row.empty:
            return False

        row = row.iloc[0]
        sessions_df = load_sessions()

        # Avoid duplicate completions
        already_done = sessions_df[
            (sessions_df["schedule_id"] == schedule_id) &
            (sessions_df["completed"] == True)
        ]
        if not already_done.empty:
            return False

        new_session = {
            "id": generate_id("SES"),
            "schedule_id": schedule_id,
            "subject_name": row["subject_name"],
            "date": row["date"],
            "duration_hours": row["duration_hours"],
            "completed": True,
            "notes": notes,
            "completed_at": datetime.now().isoformat(),
        }
        sessions_df = pd.concat(
            [sessions_df, pd.DataFrame([new_session])],
            ignore_index=True
        )
        return save_sessions(sessions_df)
    except Exception as e:
        print(f"Error marking session complete: {e}")
        return False


def unmark_session_complete(schedule_id: str) -> bool:
    """Remove a completion record for a session."""
    try:
        sessions_df = load_sessions()
        sessions_df = sessions_df[sessions_df["schedule_id"] != schedule_id]
        return save_sessions(sessions_df)
    except Exception:
        return False


# ── Stats helpers ────────────────────────────

def get_completion_stats() -> dict:
    """
    Return a summary dict of overall progress stats.
    Used by the dashboard and progress tracker.
    """
    schedule_df = load_schedule()
    sessions_df = load_sessions()

    total_sessions = len(schedule_df)
    completed_sessions = len(sessions_df[sessions_df["completed"] == True])
    total_hours_planned = schedule_df["duration_hours"].sum() if not schedule_df.empty else 0
    total_hours_done = sessions_df[sessions_df["completed"] == True]["duration_hours"].sum() \
        if not sessions_df.empty else 0

    return {
        "total_sessions": int(total_sessions),
        "completed_sessions": int(completed_sessions),
        "pending_sessions": int(total_sessions - completed_sessions),
        "total_hours_planned": round(float(total_hours_planned), 1),
        "total_hours_done": round(float(total_hours_done), 1),
        "completion_pct": round(
            (completed_sessions / total_sessions * 100) if total_sessions > 0 else 0, 1
        ),
    }


def get_completed_schedule_ids() -> set:
    """Return a set of schedule IDs that have been completed."""
    sessions_df = load_sessions()
    if sessions_df.empty:
        return set()
    return set(sessions_df[sessions_df["completed"] == True]["schedule_id"].tolist())
