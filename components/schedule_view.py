# components/schedule_view.py
# ─────────────────────────────────────────────
# Schedule generation and viewing page
# ─────────────────────────────────────────────

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta

from core.data_manager import (
    load_subjects, load_schedule, save_schedule, clear_schedule
)
from core.scheduler import generate_schedule, get_schedule_summary
from utils.helpers import format_date, format_hours


def render_schedule_page():
    """Schedule generation and viewing page."""
    st.title("📅 Study Schedule")
    st.markdown("Generate and view your personalised study plan.")

    subjects_df = load_subjects()

    if subjects_df.empty:
        st.warning(
            "⚠️ No subjects found. "
            "Please add subjects in the **📖 Subjects** tab first."
        )
        return

    # ── Generate / Regenerate button ─────────
    _render_schedule_controls(subjects_df)

    st.divider()

    # ── Show schedule ─────────────────────────
    schedule_df = load_schedule()

    if schedule_df.empty:
        st.info("📋 No schedule yet. Click **Generate Schedule** above to create one.")
        return

    _render_schedule_summary(schedule_df)
    st.divider()
    _render_schedule_tabs(schedule_df, subjects_df)


def _render_schedule_controls(subjects_df: pd.DataFrame):
    """Generate / clear schedule buttons."""
    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown("### ⚡ Generate Your Schedule")
        st.caption(
            f"Based on **{len(subjects_df)}** subject(s) and their exam dates."
        )

    with col2:
        if st.button("🗑️ Clear Schedule", use_container_width=True, type="secondary"):
            clear_schedule()
            st.success("Schedule cleared.")
            st.rerun()

    if st.button(
        "🚀 Generate / Regenerate Schedule",
        use_container_width=True,
        type="primary"
    ):
        with st.spinner("Building your personalised schedule..."):
            new_schedule = generate_schedule(subjects_df)

        if new_schedule.empty:
            st.warning("Could not generate a schedule. Check your exam dates are in the future.")
        else:
            save_schedule(new_schedule)
            st.success(
                f"✅ Schedule generated! "
                f"{len(new_schedule)} sessions across "
                f"{new_schedule['date'].nunique()} days."
            )
            st.rerun()


def _render_schedule_summary(schedule_df: pd.DataFrame):
    """Summary metrics for the generated schedule."""
    summary = get_schedule_summary(schedule_df)
    st.markdown("### 📊 Schedule Overview")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📚 Sessions", summary["total_sessions"])
    c2.metric("⏰ Total Hours", f"{summary['total_hours']}h")
    c3.metric("📆 Days", summary["days_covered"])
    c4.metric("📖 Subjects", summary["subjects_covered"])


def _render_schedule_tabs(schedule_df: pd.DataFrame, subjects_df: pd.DataFrame):
    """Show schedule in different views."""
    tab1, tab2, tab3 = st.tabs(["📋 List View", "📆 Calendar View", "📊 Charts"])

    with tab1:
        _render_list_view(schedule_df)

    with tab2:
        _render_calendar_view(schedule_df)

    with tab3:
        _render_schedule_charts(schedule_df, subjects_df)


def _render_list_view(schedule_df: pd.DataFrame):
    """Day-by-day list of sessions."""
    st.markdown("#### Sessions by Day")

    # Filter controls
    col1, col2 = st.columns(2)
    with col1:
        subject_filter = st.multiselect(
            "Filter by subject",
            options=sorted(schedule_df["subject_name"].unique()),
            default=[],
            placeholder="All subjects"
        )
    with col2:
        type_filter = st.multiselect(
            "Filter by type",
            options=sorted(schedule_df["session_type"].unique()),
            default=[],
            placeholder="All types"
        )

    filtered = schedule_df.copy()
    if subject_filter:
        filtered = filtered[filtered["subject_name"].isin(subject_filter)]
    if type_filter:
        filtered = filtered[filtered["session_type"].isin(type_filter)]

    # Group by date
    for day, group in filtered.groupby("date"):
        day_str = pd.Timestamp(day).strftime("%A, %B %d, %Y")
        total_day_hours = group["duration_hours"].sum()

        with st.expander(
            f"📅 {day_str} — {len(group)} session(s), {format_hours(total_day_hours)}",
            expanded=(pd.Timestamp(day).date() == date.today())
        ):
            for _, row in group.iterrows():
                type_emoji = {
                    "Study": "📖",
                    "Review": "🔄",
                    "Practice": "✏️",
                    "Rest": "😴"
                }.get(row["session_type"], "📚")

                st.markdown(
                    f"{type_emoji} **{row['subject_name']}** &nbsp;·&nbsp; "
                    f"`{row['start_time']} – {row['end_time']}` &nbsp;·&nbsp; "
                    f"{format_hours(row['duration_hours'])} &nbsp;·&nbsp; "
                    f"*{row['session_type']}*"
                )


def _render_calendar_view(schedule_df: pd.DataFrame):
    """Heatmap-style calendar showing study load per day."""
    st.markdown("#### Study Load Calendar")

    daily_hours = (
        schedule_df.groupby(schedule_df["date"].dt.date)["duration_hours"]
        .sum()
        .reset_index()
    )
    daily_hours.columns = ["date", "hours"]
    daily_hours["date"] = pd.to_datetime(daily_hours["date"])
    daily_hours["week"] = daily_hours["date"].dt.isocalendar().week.astype(int)
    daily_hours["weekday"] = daily_hours["date"].dt.day_name()
    daily_hours["label"] = daily_hours.apply(
        lambda r: f"{r['date'].strftime('%b %d')}<br>{r['hours']:.1f}h", axis=1
    )

    fig = px.scatter(
        daily_hours,
        x="date",
        y="weekday",
        size="hours",
        color="hours",
        hover_data={"date": True, "hours": True, "weekday": False},
        color_continuous_scale="Teal",
        size_max=40,
        title="Daily Study Load",
    )
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="",
        height=350,
        coloraxis_colorbar_title="Hours",
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_schedule_charts(schedule_df: pd.DataFrame, subjects_df: pd.DataFrame):
    """Charts breaking down the schedule by subject and type."""
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Hours by Subject")
        by_subject = (
            schedule_df.groupby("subject_name")["duration_hours"]
            .sum()
            .reset_index()
            .sort_values("duration_hours", ascending=False)
        )
        # Merge colors from subjects_df
        color_map = dict(zip(subjects_df["name"], subjects_df["color"]))
        by_subject["color"] = by_subject["subject_name"].map(color_map)

        fig = px.pie(
            by_subject,
            names="subject_name",
            values="duration_hours",
            color="subject_name",
            color_discrete_map=color_map,
            hole=0.4,
        )
        fig.update_layout(margin=dict(t=0, b=0), height=280)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### Sessions by Type")
        by_type = (
            schedule_df.groupby("session_type")["id"]
            .count()
            .reset_index()
            .rename(columns={"id": "count"})
        )
        fig = px.bar(
            by_type,
            x="session_type",
            y="count",
            color="session_type",
            labels={"session_type": "Type", "count": "Sessions"},
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig.update_layout(
            showlegend=False,
            margin=dict(t=0, b=0),
            height=280
        )
        st.plotly_chart(fig, use_container_width=True)
