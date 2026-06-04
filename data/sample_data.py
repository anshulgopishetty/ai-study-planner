# data/sample_data.py
# ─────────────────────────────────────────────
# Run this script to load sample data into
# the app so you can explore it immediately.
#
# Usage: python data/sample_data.py
# ─────────────────────────────────────────────

import sys
import os

# Make sure imports resolve from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date, timedelta
from core.data_manager import init_data_files, add_subject, load_subjects
from core.scheduler import generate_schedule
from core.data_manager import save_schedule, clear_schedule


def seed_sample_data():
    """Insert sample subjects and generate a schedule."""
    print("🌱 Seeding sample data...")

    init_data_files()

    # Only add if no subjects exist
    subjects_df = load_subjects()
    if not subjects_df.empty:
        print("⚠️  Subjects already exist. Skipping subject creation.")
    else:
        today = date.today()

        subjects = [
            {
                "name": "Mathematics",
                "exam_date": str(today + timedelta(days=10)),
                "daily_hours": 2.5,
                "priority": "High",
                "color": "#FF6B6B",
            },
            {
                "name": "Physics",
                "exam_date": str(today + timedelta(days=15)),
                "daily_hours": 2.0,
                "priority": "High",
                "color": "#45B7D1",
            },
            {
                "name": "History",
                "exam_date": str(today + timedelta(days=21)),
                "daily_hours": 1.5,
                "priority": "Medium",
                "color": "#96CEB4",
            },
            {
                "name": "English Literature",
                "exam_date": str(today + timedelta(days=28)),
                "daily_hours": 1.0,
                "priority": "Low",
                "color": "#FFEAA7",
            },
        ]

        for s in subjects:
            success = add_subject(**s)
            status = "✅" if success else "⚠️ (already exists)"
            print(f"  {status} Added subject: {s['name']}")

    # Regenerate schedule
    print("\n📅 Generating schedule from subjects...")
    subjects_df = load_subjects()
    schedule_df = generate_schedule(subjects_df)

    clear_schedule()
    save_schedule(schedule_df)
    print(
        f"  ✅ Schedule generated: "
        f"{len(schedule_df)} sessions across "
        f"{schedule_df['date'].nunique()} days."
    )

    print("\n🎉 Sample data loaded! Run the app with: streamlit run app.py")


if __name__ == "__main__":
    seed_sample_data()
