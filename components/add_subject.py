# components/add_subject.py
# ─────────────────────────────────────────────
# Subjects management page
# Add, view, delete subjects + AI strategy tips
# ─────────────────────────────────────────────

import streamlit as st
from datetime import date, timedelta

from core.data_manager import (
    load_subjects, add_subject, delete_subject
)
from core.ai_helper import get_subject_strategy
from utils.constants import PRIORITY_LEVELS, SUBJECT_COLORS
from utils.helpers import days_until_exam, get_urgency_label, format_date


def render_subjects_page():
    """Subjects management page."""
    st.title("📖 Subjects")
    st.markdown("Manage your subjects, exam dates, and study hours.")

    tab1, tab2 = st.tabs(["➕ Add Subject", "📋 My Subjects"])

    with tab1:
        _render_add_form()

    with tab2:
        _render_subjects_list()


def _render_add_form():
    """Form to add a new subject."""
    st.markdown("### Add a New Subject")

    with st.form("add_subject_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input(
                "Subject Name *",
                placeholder="e.g. Mathematics, Physics...",
                help="Enter the name of the subject"
            )
            exam_date = st.date_input(
                "Exam Date *",
                min_value=date.today() + timedelta(days=1),
                value=date.today() + timedelta(days=14),
                help="When is your exam?"
            )

        with col2:
            daily_hours = st.slider(
                "Daily Study Hours",
                min_value=0.5,
                max_value=8.0,
                value=2.0,
                step=0.5,
                help="How many hours per day can you study this subject?"
            )
            priority = st.selectbox(
                "Priority Level",
                PRIORITY_LEVELS,
                help="High priority subjects get more study time"
            )

        # Color picker
        st.markdown("**Subject Color** (for your schedule)")
        color_cols = st.columns(len(SUBJECT_COLORS))
        selected_color = SUBJECT_COLORS[0]
        if "selected_color" not in st.session_state:
            st.session_state.selected_color = SUBJECT_COLORS[0]

        for i, color in enumerate(SUBJECT_COLORS):
            with color_cols[i]:
                st.markdown(
                    f"<div style='width:24px;height:24px;"
                    f"background:{color};border-radius:50%;"
                    f"margin:auto;'></div>",
                    unsafe_allow_html=True
                )

        color_choice = st.selectbox(
            "Pick a color",
            SUBJECT_COLORS,
            format_func=lambda c: f"Color {SUBJECT_COLORS.index(c)+1}",
            label_visibility="collapsed"
        )

        submitted = st.form_submit_button("✅ Add Subject", use_container_width=True)

        if submitted:
            if not name.strip():
                st.error("Please enter a subject name.")
            else:
                success = add_subject(
                    name=name,
                    exam_date=str(exam_date),
                    daily_hours=daily_hours,
                    priority=priority,
                    color=color_choice,
                )
                if success:
                    st.success(f"✅ **{name}** added successfully!")
                    st.rerun()
                else:
                    st.error(f"A subject named **{name}** already exists.")


def _render_subjects_list():
    """Display all subjects with options to view tips or delete."""
    st.markdown("### My Subjects")
    subjects_df = load_subjects()

    if subjects_df.empty:
        st.info("No subjects added yet. Use the **Add Subject** tab to get started.")
        return

    # Sort by exam date (soonest first)
    subjects_df = subjects_df.sort_values("exam_date")

    for _, row in subjects_df.iterrows():
        days_left = days_until_exam(str(row["exam_date"]))
        urgency_label, urgency_color = get_urgency_label(days_left)

        with st.expander(
            f"{row['name']} — {urgency_label} ({days_left} days left)",
            expanded=False
        ):
            col1, col2, col3 = st.columns(3)
            col1.metric("📅 Exam Date", format_date(str(row["exam_date"])))
            col2.metric("⏰ Daily Hours", f"{row['daily_hours']}h")
            col3.metric("🎯 Priority", row["priority"])

            # Color swatch
            st.markdown(
                f"<div style='display:inline-block;width:16px;height:16px;"
                f"background:{row['color']};border-radius:3px;"
                f"vertical-align:middle;margin-right:8px;'></div>"
                f"<small>Subject color</small>",
                unsafe_allow_html=True
            )

            st.markdown("")

            btn_col1, btn_col2 = st.columns(2)

            with btn_col1:
                if st.button(
                    "🤖 Get AI Study Strategy",
                    key=f"strategy_{row['id']}",
                    use_container_width=True
                ):
                    with st.spinner("Generating your personalised strategy..."):
                        strategy = get_subject_strategy(
                            subject_name=row["name"],
                            exam_date_str=str(row["exam_date"]),
                            daily_hours=float(row["daily_hours"]),
                            priority=row["priority"],
                        )
                    st.markdown(strategy)

            with btn_col2:
                if st.button(
                    "🗑️ Delete Subject",
                    key=f"delete_{row['id']}",
                    use_container_width=True,
                    type="secondary"
                ):
                    delete_subject(row["id"])
                    st.success(f"Deleted **{row['name']}**.")
                    st.rerun()
