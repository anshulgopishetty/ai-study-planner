# components/dashboard.py
# ─────────────────────────────────────────────
# Main dashboard — overview, stats, AI motivation
# ─────────────────────────────────────────────

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import date, timedelta

from core.data_manager import (
    load_subjects, load_schedule, load_sessions, get_completion_stats
)
from core.ai_helper import get_daily_motivation
from utils.helpers import format_hours, days_until_exam, get_urgency_label


def render_dashboard():
    """Main dashboard page."""
    st.title("🏠 Dashboard")
    st.markdown("Your study overview at a glance.")

    subjects_df = load_subjects()
    schedule_df = load_schedule()
    sessions_df = load_sessions()
    stats = get_completion_stats()

    # ── Empty state ──────────────────────────
    if subjects_df.empty:
        _render_empty_state()
        return

    # ── AI Motivation banner ─────────────────
    _render_motivation_banner(subjects_df, stats)

    st.divider()

    # ── KPI metrics row ──────────────────────
    _render_kpi_row(stats)

    st.divider()

    # ── Charts row ───────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        _render_progress_donut(stats)
    with col2:
        _render_subject_hours_bar(schedule_df)

    st.divider()

    # ── Today's sessions ─────────────────────
    _render_todays_sessions(schedule_df, sessions_df)

    # ── Exam countdown cards ─────────────────
    st.divider()
    _render_exam_countdown_cards(subjects_df)


# ── Sub-components ───────────────────────────

def _render_empty_state():
    st.info(
        "👋 **Welcome to AI Study Planner!**\n\n"
        "Get started by adding your subjects in the **📖 Subjects** tab.\n"
        "Then generate your personalised schedule in **📅 Schedule**.",
        icon="📚"
    )


def _render_motivation_banner(subjects_df, stats):
    """Show an AI-generated motivational message."""
    with st.expander("💬 Your Daily AI Message", expanded=True):
        with st.spinner("Getting your daily message..."):
            message = get_daily_motivation(
                subjects_df,
                stats["completion_pct"],
                stats["total_hours_done"],
            )
        st.markdown(f"*{message}*")


def _render_kpi_row(stats: dict):
    """Four key metric cards."""
    st.markdown("### 📈 Overview")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("✅ Completed", stats["completed_sessions"], help="Sessions marked done")
    c2.metric("⏳ Remaining", stats["pending_sessions"], help="Sessions still to do")
    c3.metric("🕐 Hours Done", f"{stats['total_hours_done']}h")
    c4.metric("🎯 Progress", f"{stats['completion_pct']}%")


def _render_progress_donut(stats: dict):
    """Donut chart showing overall completion."""
    st.markdown("#### Overall Progress")
    if stats["total_sessions"] == 0:
        st.caption("No sessions scheduled yet.")
        return

    fig = go.Figure(data=[go.Pie(
        labels=["Completed", "Remaining"],
        values=[stats["completed_sessions"], stats["pending_sessions"]],
        hole=0.6,
        marker_colors=["#4ECDC4", "#E8E8E8"],
    )])
    fig.update_layout(
        showlegend=True,
        margin=dict(t=0, b=0, l=0, r=0),
        height=260,
        annotations=[dict(
            text=f"{stats['completion_pct']}%",
            x=0.5, y=0.5,
            font_size=22, showarrow=False
        )]
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_subject_hours_bar(schedule_df: pd.DataFrame):
    """Bar chart of planned hours per subject."""
    st.markdown("#### Planned Hours by Subject")
    if schedule_df.empty:
        st.caption("Generate a schedule to see this chart.")
        return

    grouped = (
        schedule_df.groupby("subject_name")["duration_hours"]
        .sum()
        .reset_index()
        .sort_values("duration_hours", ascending=True)
    )
    fig = px.bar(
        grouped,
        x="duration_hours",
        y="subject_name",
        orientation="h",
        labels={"duration_hours": "Hours", "subject_name": "Subject"},
        color="duration_hours",
        color_continuous_scale="Teal",
    )
    fig.update_layout(
        showlegend=False,
        margin=dict(t=0, b=0, l=0, r=0),
        height=260,
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_todays_sessions(schedule_df: pd.DataFrame, sessions_df: pd.DataFrame):
    """List today's scheduled study sessions."""
    st.markdown("### 📅 Today's Sessions")
    today = pd.Timestamp(date.today())

    if schedule_df.empty:
        st.caption("No schedule generated yet.")
        return

    today_sessions = schedule_df[schedule_df["date"].dt.date == date.today()]

    if today_sessions.empty:
        st.success("🎉 No sessions scheduled for today. Enjoy your break!")
        return

    completed_ids = set()
    if not sessions_df.empty:
        completed_ids = set(
            sessions_df[sessions_df["completed"] == True]["schedule_id"].tolist()
        )

    for _, row in today_sessions.iterrows():
        done = row["id"] in completed_ids
        status = "✅" if done else "⏳"
        st.markdown(
            f"{status} **{row['subject_name']}** — "
            f"{row['start_time']}–{row['end_time']} "
            f"({format_hours(row['duration_hours'])}) · *{row['session_type']}*"
        )


def _render_exam_countdown_cards(subjects_df: pd.DataFrame):
    """Cards showing days remaining until each exam."""
    st.markdown("### 🗓️ Exam Countdown")
    today = date.today()

    cols = st.columns(min(len(subjects_df), 4))
    for i, (_, row) in enumerate(subjects_df.iterrows()):
        days_left = days_until_exam(str(row["exam_date"]))
        label, color = get_urgency_label(days_left)
        with cols[i % 4]:
            st.markdown(
                f"""<div style="
                    background:{row['color']}22;
                    border-left: 4px solid {row['color']};
                    padding: 12px 16px;
                    border-radius: 8px;
                    margin-bottom: 8px;">
                    <b>{row['name']}</b><br>
                    <span style="font-size:2em; font-weight:bold;">{days_left}</span>
                    <span> days</span><br>
                    <small>{label}</small>
                </div>""",
                unsafe_allow_html=True
            )
