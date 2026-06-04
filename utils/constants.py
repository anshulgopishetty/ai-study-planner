# utils/constants.py
# ─────────────────────────────────────────────
# App-wide constants and configuration values
# ─────────────────────────────────────────────

APP_TITLE = "AI Study Planner"
APP_ICON = "📚"
APP_VERSION = "1.0.0"

# ── Data file paths ──────────────────────────
DATA_DIR = "data"
SUBJECTS_FILE = f"{DATA_DIR}/subjects.csv"
SCHEDULE_FILE = f"{DATA_DIR}/schedule.csv"
SESSIONS_FILE = f"{DATA_DIR}/sessions.csv"

# ── CSV column schemas ───────────────────────
SUBJECTS_COLUMNS = [
    "id", "name", "exam_date", "daily_hours", "priority", "color"
]

SCHEDULE_COLUMNS = [
    "id", "subject_id", "subject_name",
    "date", "start_time", "end_time",
    "duration_hours", "session_type"
]

SESSIONS_COLUMNS = [
    "id", "schedule_id", "subject_name",
    "date", "duration_hours",
    "completed", "notes", "completed_at"
]

# ── Priority levels ──────────────────────────
PRIORITY_LEVELS = ["High", "Medium", "Low"]

PRIORITY_WEIGHTS = {
    "High": 3,
    "Medium": 2,
    "Low": 1
}

# ── Subject color palette ────────────────────
SUBJECT_COLORS = [
    "#FF6B6B",  # Coral Red
    "#4ECDC4",  # Teal
    "#45B7D1",  # Sky Blue
    "#96CEB4",  # Sage Green
    "#FFEAA7",  # Pale Yellow
    "#DDA0DD",  # Plum
    "#98D8C8",  # Mint
    "#F7DC6F",  # Banana
    "#BB8FCE",  # Lavender
    "#F0B27A",  # Peach
]

# ── Session types ────────────────────────────
SESSION_TYPES = ["Study", "Review", "Practice", "Rest"]

# ── Study hour limits ────────────────────────
MIN_DAILY_HOURS = 0.5
MAX_DAILY_HOURS = 12.0

# ── UI navigation pages ──────────────────────
PAGES = {
    "🏠 Dashboard": "dashboard",
    "📖 Subjects": "subjects",
    "📅 Schedule": "schedule",
    "✅ Progress": "progress",
}
