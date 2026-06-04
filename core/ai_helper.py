# core/ai_helper.py
# ─────────────────────────────────────────────
# Offline rule-based study advisor
# No API key or internet connection required.
# All responses are generated from Python logic
# using days_left, priority, hours, and subject.
# ─────────────────────────────────────────────

import random
import pandas as pd
from datetime import date

from utils.helpers import days_until_exam, format_hours


# ══════════════════════════════════════════════
# Internal rule-based building blocks
# ══════════════════════════════════════════════

def _urgency_band(days_left: int) -> str:
    """Classify days_left into a named urgency band."""
    if days_left <= 2:
        return "critical"
    if days_left <= 7:
        return "urgent"
    if days_left <= 14:
        return "soon"
    return "comfortable"


def _completion_band(pct: float) -> str:
    """Classify completion percentage into a named band."""
    if pct == 0:
        return "not_started"
    if pct < 30:
        return "early"
    if pct < 60:
        return "midway"
    if pct < 85:
        return "strong"
    return "nearly_done"


def _pick(pool: list, seed_val) -> str:
    """Deterministically pick from a list using a seed value.
    Using a seed keeps the message stable within the same day
    but lets it vary across days and subjects."""
    idx = hash(str(seed_val) + str(date.today())) % len(pool)
    return pool[idx]


# ══════════════════════════════════════════════
# Feature 1 — get_study_tips()
# ══════════════════════════════════════════════

# Tip banks keyed by (urgency_band, session_type)
_TIPS: dict[tuple, list[list[str]]] = {

    # ── Study session tips ──────────────────
    ("comfortable", "Study"): [
        [
            "Start with a **mind map** of everything you already know about {subject} — it reveals gaps faster than re-reading notes.",
            "Use the **Feynman Technique**: explain a concept aloud as if teaching a 10-year-old. If you stumble, that's your weak spot.",
            "End the session by writing **3 questions** you'd ask on an exam. Answering them tomorrow is your warm-up.",
        ],
        [
            "Break {subject} into **chunks of 25 minutes** with 5-minute breaks (Pomodoro). Your focus will outlast a single long sitting.",
            "**Interleave** topics rather than blocking — switch between concepts every 25 min to strengthen long-term recall.",
            "Summarise each section in **your own words** before moving on. Passive reading fools you into thinking you know more than you do.",
        ],
    ],
    ("comfortable", "Review"): [
        [
            "Convert your notes into **flashcards** — even handwriting them forces active recall.",
            "Cover your notes and try to **reproduce the key points** from memory. Re-read only what you missed.",
            "Read your summary from the last session first — this **primes your memory** before adding new material.",
        ],
    ],
    ("soon", "Study"): [
        [
            "Prioritise **high-weight topics** in {subject} first — check past papers or a syllabus to confirm what carries the most marks.",
            "Don't start new chapters today. Consolidate what you have using **spaced repetition**: revisit material from 3 days ago.",
            "Do a **timed practice question** — even one. Exam conditions now will feel familiar later.",
        ],
    ],
    ("soon", "Review"): [
        [
            "Write a **one-page cheat sheet** for {subject}: only the formulas, dates, or definitions you'd lose marks without.",
            "Quiz yourself with **past paper questions** — mark your answers strictly and note every mistake.",
            "Focus on **transferable patterns**: in most subjects, 20% of the concepts appear in 80% of the questions.",
        ],
    ],
    ("urgent", "Review"): [
        [
            "Switch to **active recall only** — close your notes and write out everything you remember. Look up only what's truly blank.",
            "Do **past paper questions under timed conditions** today. Marking your own answers teaches more than re-reading ever will.",
            "Build an **error log**: every question you get wrong goes in a list. The list IS your revision for tomorrow.",
        ],
    ],
    ("urgent", "Practice"): [
        [
            "Simulate the real exam: **full timed attempt**, no notes, phone off. Treat every minute as real.",
            "After your practice, go through each wrong answer and write **one sentence** explaining what you should have done.",
            "Prioritise **mark-scheme language** — knowing how answers are phrased often earns extra marks even if your content is close.",
        ],
    ],
    ("critical", "Practice"): [
        [
            "Do **one full timed past paper** today — this is the single highest-ROI activity with 2 days left.",
            "Review **only your error log** — no new topics. Fixing known mistakes is more valuable than exploring unknowns.",
            "Tonight: write out the **10 most important facts/formulas** for {subject} on a card and read it before sleeping.",
        ],
    ],
    ("critical", "Review"): [
        [
            "Focus entirely on **high-frequency topics** — look at 3 past papers and note which themes appear every time.",
            "Write your **key formulae/definitions** from memory, then check. Repeat until you miss nothing.",
            "Get to bed on time. **Sleep consolidates memory** more effectively than a late-night cram — this is not a platitude, it's neuroscience.",
        ],
    ],
}

_DEFAULT_TIPS = [
    [
        "Start with the topic you **least** want to study — that's the one most likely to cost you marks.",
        "Use **spaced repetition**: review material from yesterday before adding today's new content.",
        "After the session, write **one paragraph summary** without looking at your notes.",
    ],
]


def get_study_tips(subject_name: str, days_left: int, session_type: str) -> str:
    """
    Return 3 personalised study tips based on subject, days remaining,
    and session type. Fully offline — no API required.
    """
    band = _urgency_band(days_left)

    # Try exact match, then fallback by urgency only, then default
    key = (band, session_type)
    fallback_key = (band, "Review")
    pool = _TIPS.get(key) or _TIPS.get(fallback_key) or _DEFAULT_TIPS

    tips = _pick(pool, subject_name)

    # Personalise {subject} placeholder
    formatted = [t.replace("{subject}", subject_name) for t in tips]

    urgency_note = {
        "critical": f"⚠️ **{days_left} day(s) to go** — focus only on high-impact work.",
        "urgent":   f"🟠 **{days_left} days left** — prioritise ruthlessly.",
        "soon":     f"🟡 **{days_left} days left** — good time to consolidate.",
        "comfortable": f"🟢 **{days_left} days left** — build strong foundations now.",
    }[band]

    lines = [
        f"### 💡 Study Tips for {subject_name}",
        f"{urgency_note}",
        "",
        f"**Session type:** {session_type}",
        "",
    ]
    for i, tip in enumerate(formatted, 1):
        lines.append(f"{i}. {tip}")

    return "\n".join(lines)


# ══════════════════════════════════════════════
# Feature 2 — get_daily_motivation()
# ══════════════════════════════════════════════

_MOTIVATION: dict[str, list[str]] = {
    "not_started": [
        "Every expert was once a beginner who decided to start. Open your notes and do just **10 minutes** — momentum builds from there.",
        "The hardest part of any study session is sitting down. You've already done that by opening the planner — keep going. 📖",
        "Today is the best day to begin. Your future self will thank you for every hour you put in now.",
    ],
    "early": [
        "You're in the early stages — this is when habits form. Keep showing up consistently and the compound effect will surprise you. 💪",
        "Progress looks slow at first, then suddenly it doesn't. Stay the course — you're building the foundation everything else sits on.",
        "**{hours_done}** of studying already logged. Small wins matter. Each session makes the next one easier.",
    ],
    "midway": [
        "You're past the halfway mark mentally — that's where many students lose focus. Stay sharp; the effort you've put in deserves a strong finish. 🎯",
        "**{pct}% complete** and climbing. You know the material better than you think. Trust your preparation and keep pushing.",
        "The middle is the hardest part of any journey. You're in it and still going — that counts for a lot. 🚀",
    ],
    "strong": [
        "**{pct}% done** — you're in the final stretch now. Consistency this week will separate a good result from a great one. ⭐",
        "Strong progress! With {closest_exam} coming up, keep the momentum you've built and avoid the temptation to coast.",
        "You've done the hard work. Now it's about **converting preparation into performance**. Believe the hours you've logged.",
    ],
    "nearly_done": [
        "Almost there — **{pct}% complete**. This is the time to review rather than cram. Trust what you know. 🏁",
        "You've put in serious work. With {closest_exam} on the horizon, a calm, focused review beats a last-minute panic every time.",
        "**The preparation is done.** Use these final sessions to build confidence, not anxiety. You've earned this. 🎓",
    ],
}


def get_daily_motivation(
    subjects_df: pd.DataFrame,
    completion_pct: float,
    total_hours_done: float,
) -> str:
    """
    Return a short personalised motivational message for the dashboard.
    Fully offline — no API required.
    """
    if subjects_df.empty:
        return "📚 Add your subjects to get started on your study journey! Every great result begins with a plan."

    # Find the most urgent exam for personalisation
    today = date.today()
    subjects_df = subjects_df.copy()
    subjects_df["days_left"] = subjects_df["exam_date"].apply(
        lambda d: days_until_exam(str(d))
    )
    closest = subjects_df.sort_values("days_left").iloc[0]
    closest_exam = f"{closest['name']} ({int(closest['days_left'])} days)"

    band = _completion_band(completion_pct)
    pool = _MOTIVATION[band]
    template = _pick(pool, f"{band}{closest['name']}")

    message = (
        template
        .replace("{pct}", str(round(completion_pct)))
        .replace("{hours_done}", format_hours(total_hours_done))
        .replace("{closest_exam}", closest_exam)
    )
    return message


# ══════════════════════════════════════════════
# Feature 3 — get_subject_strategy()
# ══════════════════════════════════════════════

_APPROACH: dict[str, str] = {
    "critical": (
        "With only **{days_left} days** remaining, shift entirely to active recall and past-paper practice. "
        "No new topics — deepen what you already know and fix identified weaknesses."
    ),
    "urgent": (
        "**{days_left} days** is enough to make a real difference if you focus. "
        "Move from learning mode to consolidation mode: review, practice questions, error correction."
    ),
    "soon": (
        "You have **{days_left} days** — a solid window to cover material thoroughly and begin practice. "
        "Aim to finish new content in the first half and dedicate the rest to review and mock questions."
    ),
    "comfortable": (
        "With **{days_left} days** ahead, build deep understanding rather than rushing. "
        "Structured daily study of {daily_hours}h will cover the syllabus with time to spare for review."
    ),
}

_WEEKLY_FOCUS: dict[str, list[str]] = {
    "critical": [
        "Complete **at least 2 timed past papers** and mark them strictly.",
        "Maintain a running **error log** — revisit every mistake daily.",
        "Final 24 hours: light review of key formulae/definitions only; prioritise sleep.",
    ],
    "urgent": [
        "**Days 1–3:** Close gaps identified by a diagnostic past paper.",
        "**Days 4–5:** Mixed practice questions across all major topics.",
        "**Days 6–7:** Full timed past paper + detailed error review.",
    ],
    "soon": [
        "**Week 1:** Complete coverage of remaining syllabus topics.",
        "**Week 2:** Flashcard review of all key content + first past paper.",
        "**Final days:** Error correction and confidence-building practice.",
    ],
    "comfortable": [
        "**Weeks 1–2:** Build foundational understanding, topic by topic.",
        "**Weeks 3–4:** Begin active recall and inter-topic connections.",
        "**Final 2 weeks:** Past papers, error logs, and targeted revision.",
    ],
}

_QUICK_WINS: dict[str, list[str]] = {
    "critical": [
        "Do **one past paper question** from the highest-weight topic right now.",
        "Write out all key formulae/definitions from memory — check and correct.",
    ],
    "urgent": [
        "Identify your **3 weakest topics** and write them down — tackle the worst one today.",
        "Do **5 practice questions** from a topic you think you know — prove it to yourself.",
    ],
    "soon": [
        "Create a **one-page topic map** of {subject} — everything you need to cover.",
        "Do a **20-minute timed quiz** on the last topic you studied to assess retention.",
    ],
    "comfortable": [
        "Read through your notes for **today's topic** and write a 5-sentence summary.",
        "Set up your **flashcard deck** for {subject} — even 10 cards today pays off for weeks.",
    ],
}

_PRIORITY_NOTE: dict[str, str] = {
    "High":   "🔴 **High priority** — this subject deserves the first and best hours of your day.",
    "Medium": "🟡 **Medium priority** — steady daily progress beats occasional long sessions.",
    "Low":    "🟢 **Lower priority** — keep it ticking over; don't let it drift until too late.",
}


def get_subject_strategy(
    subject_name: str,
    exam_date_str: str,
    daily_hours: float,
    priority: str,
) -> str:
    """
    Return a structured 3-section study strategy for a subject.
    Fully offline — no API required.
    """
    days_left = days_until_exam(exam_date_str)
    band = _urgency_band(days_left)

    approach = (
        _APPROACH[band]
        .replace("{days_left}", str(days_left))
        .replace("{daily_hours}", str(daily_hours))
        .replace("{subject}", subject_name)
    )

    focus_points = _WEEKLY_FOCUS[band]
    quick_wins = [
        w.replace("{subject}", subject_name)
        for w in _QUICK_WINS[band]
    ]

    priority_note = _PRIORITY_NOTE.get(priority, "")

    lines = [
        f"## 📋 Study Strategy: {subject_name}",
        "",
        priority_note,
        "",
        "### 1. Recommended Approach",
        approach,
        "",
        "### 2. Week-by-Week Focus",
    ]
    for point in focus_points:
        lines.append(f"- {point}")

    lines += [
        "",
        "### 3. Quick Wins — Do These Today",
        f"- {quick_wins[0]}",
        f"- {quick_wins[1]}",
        "",
        f"*Daily commitment: **{daily_hours}h** · Exam in **{days_left} days***",
    ]

    return "\n".join(lines)


# ══════════════════════════════════════════════
# Feature 4 — get_weekly_review()
# ══════════════════════════════════════════════

def get_weekly_review(
    completed_sessions: int,
    planned_sessions: int,
    subjects_studied: list[str],
    hours_studied: float,
) -> str:
    """
    Return a structured weekly review with personalised advice.
    Fully offline — no API required.
    """
    completion_rate = round(
        (completed_sessions / planned_sessions * 100) if planned_sessions > 0 else 0
    )
    hours_fmt = format_hours(hours_studied)
    subjects_str = ", ".join(subjects_studied) if subjects_studied else "none recorded"

    # ── Achievement sentence ─────────────────
    if completion_rate >= 90:
        achievement = (
            f"Outstanding week — you completed **{completed_sessions} of {planned_sessions} sessions** "
            f"({completion_rate}%) and logged **{hours_fmt}** of focused study. "
            f"That level of consistency is what separates good results from great ones."
        )
    elif completion_rate >= 70:
        achievement = (
            f"Solid week overall — **{completed_sessions}/{planned_sessions} sessions** done ({completion_rate}%) "
            f"and **{hours_fmt}** logged across {subjects_str}. "
            f"You're building real momentum."
        )
    elif completion_rate >= 40:
        achievement = (
            f"You showed up this week — **{completed_sessions} sessions** completed and **{hours_fmt}** studied. "
            f"Covering {subjects_str} is good progress, even if the full plan wasn't hit."
        )
    else:
        achievement = (
            f"A tough week — only **{completed_sessions} of {planned_sessions} sessions** completed. "
            f"That happens. What matters is diagnosing why and adjusting, not dwelling on the gap."
        )

    # ── Improvement note ─────────────────────
    missed = planned_sessions - completed_sessions
    if completion_rate >= 90:
        improvement = (
            "One refinement for next week: **vary your revision methods**. "
            "If you've been re-reading, switch to flashcards or practice questions to deepen retention."
        )
    elif completion_rate >= 70:
        improvement = (
            f"You missed **{missed} session(s)** — identify whether that was time, energy, or motivation. "
            "Blocking study time in your calendar the night before reduces missed sessions by ~40%."
        )
    elif completion_rate >= 40:
        improvement = (
            f"**{missed} sessions** were missed. Consider reducing your daily target slightly — "
            "a smaller plan you fully complete beats an ambitious one you partially skip. "
            "Consistency beats volume every time."
        )
    else:
        improvement = (
            "Start next week with just **one non-negotiable session per day** — short and certain. "
            "Rebuilding the habit matters more than catching up on volume right now."
        )

    # ── Forward-looking note ─────────────────
    if completion_rate >= 70:
        forward = (
            "Next week, keep the same rhythm and start introducing **timed practice questions** "
            "if you haven't already — the earlier you practise under exam conditions, the calmer you'll feel."
        )
    else:
        forward = (
            "Next week: pick your **two most important subjects** and protect their sessions above all else. "
            "Narrow focus now will compound into broader progress later."
        )

    # ── Rating badge ─────────────────────────
    if completion_rate >= 90:
        badge = "🏆 Excellent week"
    elif completion_rate >= 70:
        badge = "⭐ Good week"
    elif completion_rate >= 40:
        badge = "📈 Building week"
    else:
        badge = "🔄 Reset week"

    lines = [
        f"## {badge}",
        "",
        "### ✅ What You Achieved",
        achievement,
        "",
        "### 🔧 One Thing to Improve",
        improvement,
        "",
        "### 🚀 Next Week",
        forward,
        "",
        "---",
        f"*{completed_sessions}/{planned_sessions} sessions · {hours_fmt} studied · Subjects: {subjects_str}*",
    ]

    return "\n".join(lines)
