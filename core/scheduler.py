# core/scheduler.py
# ─────────────────────────────────────────────
# Schedule generation algorithm
# Distributes study sessions across available
# days, weighted by priority and exam proximity
# ─────────────────────────────────────────────

from datetime import date, timedelta
import pandas as pd

from utils.constants import PRIORITY_WEIGHTS, SCHEDULE_COLUMNS
from utils.helpers import generate_id, get_date_range


def generate_schedule(subjects_df: pd.DataFrame) -> pd.DataFrame:
    """
    Main entry point.
    Given a DataFrame of subjects, produce a full
    day-by-day schedule DataFrame ready to save.

    Algorithm:
    1. For each subject, calculate study days available
       (today → day before exam)
    2. Allocate daily slots weighted by priority
    3. Fill each day with sessions across all active subjects
    """
    if subjects_df.empty:
        return pd.DataFrame(columns=SCHEDULE_COLUMNS)

    today = date.today()
    schedule_rows = []

    # ── Build per-subject study plan ─────────
    subject_plans = []
    for _, subj in subjects_df.iterrows():
        exam_date = pd.to_datetime(subj["exam_date"]).date()
        if exam_date <= today:
            continue  # skip past exams

        study_days = get_date_range(today, exam_date - timedelta(days=1))
        priority_weight = PRIORITY_WEIGHTS.get(subj["priority"], 1)
        daily_hours = float(subj["daily_hours"])

        subject_plans.append({
            "id": subj["id"],
            "name": subj["name"],
            "exam_date": exam_date,
            "daily_hours": daily_hours,
            "priority": subj["priority"],
            "priority_weight": priority_weight,
            "color": subj["color"],
            "study_days": study_days,
        })

    if not subject_plans:
        return pd.DataFrame(columns=SCHEDULE_COLUMNS)

    # ── Find overall date range ──────────────
    latest_exam = max(p["exam_date"] for p in subject_plans)
    all_days = get_date_range(today, latest_exam - timedelta(days=1))

    # ── Build schedule day by day ────────────
    current_start_hour = 8  # sessions start at 8 AM by default

    for day in all_days:
        # Which subjects are still active on this day?
        active = [
            p for p in subject_plans
            if day in p["study_days"]
        ]
        if not active:
            continue

        # Sort by urgency (closest exam first) then priority weight
        active.sort(
            key=lambda p: (
                (p["exam_date"] - day).days,
                -p["priority_weight"]
            )
        )

        slot_start = current_start_hour

        for plan in active:
            duration = _calculate_session_duration(
                plan["daily_hours"],
                plan["priority_weight"],
                (plan["exam_date"] - day).days,
            )
            session_type = _get_session_type(
                (plan["exam_date"] - day).days
            )

            start_time = f"{int(slot_start):02d}:00"
            end_hour = slot_start + duration
            end_time = f"{int(end_hour):02d}:{int((end_hour % 1) * 60):02d}"

            schedule_rows.append({
                "id": generate_id("SCH"),
                "subject_id": plan["id"],
                "subject_name": plan["name"],
                "date": day.isoformat(),
                "start_time": start_time,
                "end_time": end_time,
                "duration_hours": round(duration, 2),
                "session_type": session_type,
            })

            slot_start = end_hour + 0.25  # 15-min break between sessions

    if not schedule_rows:
        return pd.DataFrame(columns=SCHEDULE_COLUMNS)

    df = pd.DataFrame(schedule_rows)
    df["date"] = pd.to_datetime(df["date"])
    return df


def _calculate_session_duration(
    daily_hours: float,
    priority_weight: int,
    days_until_exam: int
) -> float:
    """
    Compute session length in hours.
    Sessions get slightly longer as exam approaches.
    Clamped between 0.5h and daily_hours cap.
    """
    base = daily_hours

    # Boost as exam gets close
    if days_until_exam <= 3:
        boost = 1.3
    elif days_until_exam <= 7:
        boost = 1.15
    else:
        boost = 1.0

    duration = base * boost

    # Clamp between 30 min and 3 hours per session
    return round(max(0.5, min(duration, 3.0)), 2)


def _get_session_type(days_until_exam: int) -> str:
    """
    Pick session type based on exam proximity.
    Far away → Study new material
    Getting close → Review
    Very close → Practice / mock tests
    """
    if days_until_exam <= 2:
        return "Practice"
    elif days_until_exam <= 7:
        return "Review"
    else:
        return "Study"


def get_schedule_summary(schedule_df: pd.DataFrame) -> dict:
    """
    Return summary statistics for a generated schedule.
    Used in the schedule view header.
    """
    if schedule_df.empty:
        return {
            "total_sessions": 0,
            "total_hours": 0,
            "days_covered": 0,
            "subjects_covered": 0,
        }

    return {
        "total_sessions": len(schedule_df),
        "total_hours": round(schedule_df["duration_hours"].sum(), 1),
        "days_covered": schedule_df["date"].nunique(),
        "subjects_covered": schedule_df["subject_name"].nunique(),
    }
