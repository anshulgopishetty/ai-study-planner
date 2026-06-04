# components/progress_tracker.py
# ─────────────────────────────────────────────
# Progress tracking page
# Mark sessions complete, view history, AI review
# ─────────────────────────────────────────────

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta

from core.data_manager import (
    load_schedule, load_sessions,
    mark_session_complete, unmark_session_complete,
    get_completion_stats, get_completed_schedule_ids,
)
from core.ai_helper import get_study_tips, get_weekly_review
from utils.helpers import format_date, format_hours, days_until_exam


def render_progress_page():
    """Progress tracking page."""
    st.title("✅ Progress Tracker")
    st.markdown("Mark sessions complete and track your study history.")

    schedule_df = load_schedule()

    if schedule_df.empty:
        st.warning(
            "⚠️ No schedule found. "
            "Generate one in the **📅 Schedule** tab first."
        )
        return

    tab1, tab2, tab3 = st.tabs([
        "📌 Today & Upcoming",
        "📜 History",
        "📊 My Stats"
    ])

    with tab1:
        _render_upcoming_sessions(schedule_df)

    with tab2:
        _render_history(schedule_df)

    with tab3:
        _render_stats_tab()


def _render_upcoming_sessions(schedule_df: pd.DataFrame):
    """Show today's and next 7 days sessions to mark complete."""
    st.markdown("### Mark Sessions Complete")

    today = date.today()
    end_date = today + timedelta(days=7)
    completed_ids = get_completed_schedule_ids()

    # Filter to today + next 7 days, incomplete first
    upcoming = schedule_df[
        (schedule_df["date"].dt.date >= today) &
        (schedule_df["date"].dt.date <= end_date)
    ].copy()
    upcoming["done"] = upcoming["id"].isin(completed_ids)
    upcoming = upcoming.sort_values(["date", "done"])

    if upcoming.empty:
        st.info("No sessions in the next 7 days.")
        return

    for day, group in upcoming.groupby("date"):
        day_str = pd.Timestamp(day).strftime("%A, %B %d")
        is_today = pd.Timestamp(day).date() == today

        header = f"{'📌 TODAY — ' if is_today else '📅 '}{day_str}"
        with st.expander(header, expanded=is_today):
            for _, row in group.iterrows():
                done = row["id"] in completed_ids
                _render_session_card(row, done)


def _render_session_card(row: pd.Series, done: bool):
    """Render a single session with complete/uncomplete toggle."""
    col1, col2, col3 = st.columns([3, 2, 1])

    status_icon = "✅" if done else "⏳"
    subject_style = "text-decoration:line-through;color:gray;" if done else ""

    with col1:
        st.markdown(
            f"{status_icon} <span style='{subject_style}'>"
            f"**{row['subject_name']}** · {row['session_type']}</span>",
            unsafe_allow_html=True
        )
        st.caption(f"{row['start_time']} – {row['end_time']} · {format_hours(row['duration_hours'])}")

    with col2:
        if not done:
            # Show AI tip button
            if st.button(
                "💡 Study Tips",
                key=f"tip_{row['id']}",
                use_container_width=True
            ):
                with st.spinner("Getting tips..."):
                    tips = get_study_tips(
                        subject_name=row["subject_name"],
                        days_left=max(0, (pd.Timestamp(row["date"]).date() - date.today()).days),
                        session_type=row["session_type"],
                    )
                st.markdown(tips)

    with col3:
        if not done:
            if st.button(
                "✅ Done",
                key=f"done_{row['id']}",
                use_container_width=True,
                type="primary"
            ):
                mark_session_complete(row["id"])
                st.rerun()
        else:
            if st.button(
                "↩️ Undo",
                key=f"undo_{row['id']}",
                use_container_width=True,
                type="secondary"
            ):
                unmark_session_complete(row["id"])
                st.rerun()


def _render_history(schedule_df: pd.DataFrame):
    """Show all past completed sessions."""
    st.markdown("### Completed Sessions")
    sessions_df = load_sessions()

    if sessions_df.empty:
        st.info("No completed sessions yet. Start marking sessions as done!")
        return

    completed = sessions_df[sessions_df["completed"] == True].copy()
    completed = completed.sort_values("completed_at", ascending=False)

    # Summary
    st.markdown(
        f"**{len(completed)}** sessions completed · "
        f"**{format_hours(completed['duration_hours'].sum())}** total"
    )
    st.divider()

    for _, row in completed.head(50).iterrows():
        col1, col2 = st.columns([4, 1])
        with col1:
            completed_at = pd.to_datetime(row["completed_at"]).strftime("%b %d, %Y %H:%M")
            st.markdown(
                f"✅ **{row['subject_name']}** · "
                f"{format_date(str(row['date']), '%b %d')} · "
                f"{format_hours(row['duration_hours'])}"
            )
            st.caption(f"Completed at {completed_at}")
            if row["notes"]:
                st.caption(f"📝 {row['notes']}")
        with col2:
            pass
        st.divider()


def _render_stats_tab():
    """Charts and AI weekly review."""
    sessions_df = load_sessions()
    stats = get_completion_stats()

    # ── KPIs ─────────────────────────────────
    st.markdown("### 📊 Your Study Stats")
    c1, c2, c3 = st.columns(3)
    c1.metric("Sessions Done", stats["completed_sessions"])
    c2.metric("Hours Studied", f"{stats['total_hours_done']}h")
    c3.metric("Completion Rate", f"{stats['completion_pct']}%")

    if sessions_df.empty:
        st.info("Complete some sessions to see charts.")
        return

    st.divider()

    # ── Hours per day chart ───────────────────
    completed = sessions_df[sessions_df["completed"] == True].copy()
    daily = (
        completed.groupby(completed["date"].dt.date)["duration_hours"]
        .sum()
        .reset_index()
    )
    daily.columns = ["date", "hours"]

    st.markdown("#### Daily Study Hours")
    fig = px.bar(
        daily,
        x="date",
        y="hours",
        color="hours",
        color_continuous_scale="Teal",
        labels={"date": "Date", "hours": "Hours Studied"},
    )
    fig.update_layout(showlegend=False, height=250, margin=dict(t=0, b=0))
    st.plotly_chart(fig, use_container_width=True)

    # ── Per-subject breakdown ─────────────────
    st.markdown("#### Hours by Subject")
    by_subject = (
        completed.groupby("subject_name")["duration_hours"]
        .sum()
        .reset_index()
        .sort_values("duration_hours", ascending=True)
    )
    fig2 = px.bar(
        by_subject,
        x="duration_hours",
        y="subject_name",
        orientation="h",
        color="duration_hours",
        color_continuous_scale="Viridis",
        labels={"duration_hours": "Hours", "subject_name": "Subject"},
    )
    fig2.update_layout(showlegend=False, height=250, margin=dict(t=0, b=0))
    st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    # ── AI Weekly Review ──────────────────────
    st.markdown("### 🤖 AI Weekly Review")
    if st.button("📝 Generate My Weekly Review", use_container_width=True):
        # Get this week's sessions
        one_week_ago = pd.Timestamp(date.today() - timedelta(days=7))
        this_week = completed[completed["date"] >= one_week_ago]

        subjects_studied = this_week["subject_name"].unique().tolist()
        hours_this_week = this_week["duration_hours"].sum()

        schedule_df = load_schedule()
        planned_this_week = schedule_df[
            schedule_df["date"] >= one_week_ago
        ]

        with st.spinner("Generating your weekly review..."):
            review = get_weekly_review(
                completed_sessions=len(this_week),
                planned_sessions=len(planned_this_week),
                subjects_studied=subjects_studied,
                hours_studied=hours_this_week,
            )
        st.markdown(review)
