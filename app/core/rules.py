# app/core/rules.py
"""
Single source of truth for all WRA game rules.
Imported by both server.py (Flask) and main.py (CLI).

Nothing in here does I/O or printing — pure data and pure functions only.
"""

from datetime import datetime

# ── Phase names ────────────────────────────────────────────────────────────
PHASE_NAMES = {
    1: "NULL — System Purge",
    2: "IRON MIND",
    3: "TITAN BODY",
    4: "PREDATOR FORM",
    5: "MACHINE INTELLIGENCE",
    6: "SHADOW ARCHITECT",
    7: "LIMITLESS TECHNIQUE",
    8: "APEX BEING",
}

# ── Minimum deep-work session duration per phase (minutes) ─────────────────
PHASE_MIN_SESSION = {
    1: 90,
    2: 120, 3: 120, 4: 120, 5: 120, 6: 120, 7: 120, 8: 120,
}

# ── Phase day boundaries (inclusive) ──────────────────────────────────────
PHASE_BOUNDARIES = [90, 180, 270, 360, 450, 540, 630, 720]

# ── Task type → secondary stat mapping ────────────────────────────────────
TASK_STAT_MAP = {
    "Study":        "Intelligence",
    "Coding":       "Skills",
    "Research":     "Intelligence",
    "Reading":      "Intelligence",
    "Presentation": "Skills",
}

# ── Pillar → stat mapping ──────────────────────────────────────────────────
PILLAR_STAT = {
    "Push-ups":   "Strength",
    "Sit-ups":    "Strength",
    "Squats":     "Strength",
    "Pull-ups":   "Strength",
    "Meditation": "Willpower",
    "Reading":    "Intelligence",
}

# ── Pillar daily targets ───────────────────────────────────────────────────
PILLAR_TARGETS = {
    "Push-ups":   100,
    "Sit-ups":    100,
    "Squats":     100,
    "Pull-ups":   100,
    "Meditation": 60,
    "Reading":    5,   # base — scales +5 every 30 days
}

def reading_target(day: int) -> int:
    """Reading pages target: starts at 5, increases +5 every 30 days."""
    return 5 + (((day - 1) // 30) * 5)

PILLAR_UNITS = {
    "Push-ups":   "reps",
    "Sit-ups":    "reps",
    "Squats":     "reps",
    "Pull-ups":   "reps",
    "Meditation": "min",
    "Reading":    "pages",
}

# ── XP formulas ───────────────────────────────────────────────────────────
def session_xp(duration_minutes: int) -> int:
    """Deep work: 1 minute = 3 XP. Goes to Willpower AND secondary stat."""
    return max(0, duration_minutes * 3)

def pillar_xp(amount: int) -> int:
    """Reps/minutes/pages: 1 unit = 3 XP."""
    return max(0, amount * 3)

def running_xp(meters: float) -> int:
    """Running: 1 meter = 0.3 XP → Vitality only."""
    return int(max(0, meters * 0.3))

def wakeup_xp(time_str: str) -> int:
    """
    Wakeup bonus XP by time window.
    time_str format: 'HH:MM' (24h)
    4:00–4:30  → 60 XP
    4:30–5:00  → 55 XP
    5:00–5:30  → 50 XP
    5:30–6:00  → 45 XP
    After 6:00 → 0 XP
    """
    try:
        h, m = map(int, time_str.split(":"))
        mins = h * 60 + m
        if   240 <= mins < 270: return 60
        elif 270 <= mins < 300: return 55
        elif 300 <= mins < 330: return 50
        elif 330 <= mins < 360: return 45
        else:                   return 0
    except Exception:
        return 0

# ── Phase calculation ──────────────────────────────────────────────────────
def get_phase(day: int) -> int:
    """Return phase number (1–8) for a given arc day."""
    for i, boundary in enumerate(PHASE_BOUNDARIES):
        if day <= boundary:
            return i + 1
    return 8

def get_phase_info(day: int) -> dict:
    """Return full phase context for a given arc day."""
    phase       = get_phase(day)
    phase_end   = PHASE_BOUNDARIES[phase - 1]
    phase_start = (PHASE_BOUNDARIES[phase - 2] if phase > 1 else 0) + 1
    phase_day   = day - phase_start + 1
    phase_total = phase_end - phase_start + 1
    return {
        "phase":       phase,
        "phase_name":  PHASE_NAMES[phase],
        "phase_start": phase_start,
        "phase_end":   phase_end,
        "phase_day":   phase_day,
        "phase_total": phase_total,
        "min_session": PHASE_MIN_SESSION.get(phase, 90),
    }

def get_day_number(arc_start: datetime) -> int:
    """Calculate current arc day from a given start datetime."""
    return max(1, (datetime.now() - arc_start).days + 1)