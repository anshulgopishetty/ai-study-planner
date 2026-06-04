# app.py
# ─────────────────────────────────────────────
# AI Study Planner — main entry point
# Run with: streamlit run app.py
# ─────────────────────────────────────────────

import streamlit as st
import os

from utils.constants import APP_TITLE, APP_ICON
from core.data_manager import init_data_files
from components.sidebar import render_sidebar
from components.dashboard import render_dashboard
from components.add_subject import render_subjects_page
from components.schedule_view import render_schedule_page
from components.progress_tracker import render_progress_page


# ── Page config (must be first Streamlit call) ──
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)


def load_custom_css():
    """Load custom CSS from assets/style.css if it exists."""
    css_path = os.path.join("assets", "style.css")
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def main():
    """
    Application entry point.
    1. Initialise data files
    2. Load custom styles
    3. Render sidebar (returns selected page)
    4. Render the selected page
    """
    # Ensure data directory and CSV files exist
    init_data_files()

    # Load custom styles
    load_custom_css()

    # Render sidebar and get current page selection
    current_page = render_sidebar()

    # Route to the correct page component
    if current_page == "dashboard":
        render_dashboard()

    elif current_page == "subjects":
        render_subjects_page()

    elif current_page == "schedule":
        render_schedule_page()

    elif current_page == "progress":
        render_progress_page()

    else:
        st.error(f"Unknown page: {current_page}")


if __name__ == "__main__":
    main()
