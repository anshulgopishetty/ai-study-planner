# components/sidebar.py
# ─────────────────────────────────────────────
# Sidebar navigation and app info
# ─────────────────────────────────────────────

import streamlit as st
from datetime import date

from utils.constants import APP_TITLE, APP_ICON, APP_VERSION, PAGES
from utils.helpers import days_until_exam, get_urgency_label
from core.data_manager import load_subjects, get_completion_stats


def render_sidebar() -> str:
    """
    Render the sidebar and return the name of the
    currently selected page.
    """
    with st.sidebar:
        # ── App header ───────────────────────
        st.markdown(f"# {APP_ICON} {APP_TITLE}")
        st.markdown(f"*v{APP_VERSION} — Your AI Study Partner*")
        st.divider()

        # ── Navigation ───────────────────────
        st.markdown("### Navigation")
        selected_page = st.radio(
            label="Go to",
            options=list(PAGES.keys()),
            label_visibility="collapsed",
        )

        st.divider()

        # ── Quick stats ──────────────────────
        _render_quick_stats()

        st.divider()

        # ── Upcoming exams ───────────────────
        _render_upcoming_exams()

        # ── Footer ───────────────────────────
        st.markdown(
            "<br><small style='color:gray'>Built with Streamlit + Claude AI</small>",
            unsafe_allow_html=True
        )

    return PAGES[selected_page]


def _render_quick_stats():
    """Show a compact progress overview in the sidebar."""
    st.markdown("### 📊 Quick Stats")
    stats = get_completion_stats()

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Done", f"{stats['completed_sessions']}")
        st.metric("Hours", f"{stats['total_hours_done']}h")
    with col2:
        st.metric("Pending", f"{stats['pending_sessions']}")
        st.metric("Progress", f"{stats['completion_pct']}%")


def _render_upcoming_exams():
    """Show a mini countdown list of upcoming exams."""
    st.markdown("### 🗓️ Exam Countdown")
    subjects_df = load_subjects()

    if subjects_df.empty:
        st.caption("No subjects added yet.")
        return

    today = date.today()
    upcoming = subjects_df.copy()
    upcoming["days_left"] = upcoming["exam_date"].apply(
        lambda d: (d.date() - today).days
    )
    upcoming = upcoming[upcoming["days_left"] >= 0].sort_values("days_left")

    if upcoming.empty:
        st.caption("No upcoming exams.")
        return

    for _, row in upcoming.head(5).iterrows():
        label, color = get_urgency_label(int(row["days_left"]))
        st.markdown(
            f"<div style='margin-bottom:6px'>"
            f"<b>{row['name']}</b><br>"
            f"<small>{label} — {row['days_left']}d left</small>"
            f"</div>",
            unsafe_allow_html=True
        )
