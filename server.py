"""
Life Tracker — Flask Backend
Drop into life-tracker-main/ alongside main.py
Run:  python server.py
Open: http://localhost:5000 in Chrome
"""

import os, sys, json, time
from datetime import datetime, date
from flask import Flask, jsonify, request, send_from_directory

# ── Ensure app.core is importable ─────────────────────────────────────────
BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

# ── Patch builtins.print BEFORE importing app.core ────────────────────────
# display.py replaces print() with a slow type-animation effect at import
# time. We suppress it so Flask's stdout stays clean.
import builtins
_real_print = builtins.print

# ── Import from app.core — one source of truth ────────────────────────────
from app.core.rules import (          # ← new shared constants module
    PHASE_NAMES, PHASE_MIN_SESSION, TASK_STAT_MAP,
    PILLAR_STAT, PILLAR_TARGETS, PILLAR_UNITS,
    session_xp, pillar_xp, running_xp, wakeup_xp,
    get_phase, get_phase_info, get_day_number,
)
from app.core.stats import (
    Stat,
    to_file   as stats_to_file,
    from_file as stats_from_file,
)
from app.core.quests import (
    Quests, load_saved_quests, save_all_quests, scale_quests,
)
from app.core.player import Player

# Restore real print after app.core import
builtins.print = _real_print

# ── Storage paths ──────────────────────────────────────────────────────────
STORE    = os.path.join(BASE, "app", "storage")
LOGS_DIR = os.path.join(STORE, "session_logs")
os.makedirs(LOGS_DIR, exist_ok=True)

PLAYER_F  = os.path.join(STORE, "player.json")
STATS_F   = os.path.join(STORE, "stats.json")
PLOG_F    = os.path.join(STORE, "phase_log.json")
DAY_F     = os.path.join(STORE, "day_log.json")
SESSION_F = os.path.join(STORE, "sessions.json")
CONFIG_F  = os.path.join(STORE, "config.json")

app = Flask(__name__)

# ══════════════════════════════════════════════════════════════════════════
#  LOW-LEVEL I/O
# ══════════════════════════════════════════════════════════════════════════
def _load(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return default

def _save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

def today_str():
    return date.today().isoformat()

# ══════════════════════════════════════════════════════════════════════════
#  CONFIG  — arc start date overrides wra_phases.py hardcode
# ══════════════════════════════════════════════════════════════════════════
def get_config():
    if not os.path.exists(CONFIG_F):
        cfg = {"arc_start": "2026-03-01", "detox_start": "2026-03-01"}
        _save(CONFIG_F, cfg)
        return cfg
    return _load(CONFIG_F, {})

def arc_start_dt():
    return datetime.strptime(get_config().get("arc_start", "2026-03-01"), "%Y-%m-%d")

def get_skipped_days() -> list:
    return _load(get_config().get("skips_file", os.path.join(STORE, "skipped_days.json")), [])

SKIPS_F = os.path.join(STORE, "skipped_days.json")

def current_day():
    """Day number = calendar days since arc start - number of skipped days."""
    raw = get_day_number(arc_start_dt())    # ← app.core.rules.get_day_number
    skips = _load(SKIPS_F, [])
    if not isinstance(skips, list):
        skips = []
    # Only count skips that are before today
    today = today_str()
    past_skips = sum(1 for s in skips if s.get("date", "") < today)
    return max(1, raw - past_skips)

# ══════════════════════════════════════════════════════════════════════════
#  PLAYER  — app.core.player.Player
# ══════════════════════════════════════════════════════════════════════════
def load_player() -> Player:
    p = Player.__new__(Player)
    p.name = "Ryuji"; p.level = 1; p.xp = 0; p.xp_required = 100; p.rank = "E"
    p.load(PLAYER_F)
    return p

def save_player(p: Player):
    p.save(PLAYER_F)

def player_dict(p: Player) -> dict:
    return {"name": p.name, "level": p.level, "xp": p.xp,
            "xp_required": p.xp_required, "rank": p.rank}

# ══════════════════════════════════════════════════════════════════════════
#  STATS  — app.core.stats.Stat
# ══════════════════════════════════════════════════════════════════════════
STAT_NAMES = ["Strength", "Vitality", "Intelligence", "Willpower", "Skills"]

def load_stats() -> dict:
    """Return fresh Stat objects loaded from stats.json."""
    fresh = {n: Stat(n) for n in STAT_NAMES}
    for name, saved in _load(STATS_F, {}).items():
        if name in fresh:
            fresh[name].level       = saved.get("Level", 1)
            fresh[name].xp          = saved.get("XP", 0)
            fresh[name].xp_required = saved.get("xp-required", 100)
    return fresh

def save_stats(stat_dict: dict):
    stats_to_file(stat_dict, STATS_F)           # ← app.core.stats.to_file

def stats_dict(stat_dict: dict) -> dict:
    return {n: {"level": s.level, "xp": s.xx, "xp_required": s.xp_required}
            for n, s in stat_dict.items()}

def stats_json(stat_dict: dict) -> dict:
    return {n: {"level": s.level, "xp": s.xp, "xp_required": s.xp_required}
            for n, s in stat_dict.items()}

# ══════════════════════════════════════════════════════════════════════════
#  QUESTS  — app.core.quests
# ══════════════════════════════════════════════════════════════════════════
_QUEST_DEFAULTS = {
    "Push-ups":   ("100 Push-ups",      300, "Strength"),
    "Sit-ups":    ("100 Sit-ups",       300, "Strength"),
    "Squats":     ("100 Squats",        300, "Strength"),
    "Pull-ups":   ("100 Pull-ups",      300, "Strength"),
    "Meditation": ("60 min Meditation", 180, "Willpower"),
}

def load_quests() -> dict:
    """Reset Quests to defaults then reload from file via app.core.quests."""
    for key, q in Quests.items():
        if key in _QUEST_DEFAULTS:
            q.name, q.xp, q.target_stat = _QUEST_DEFAULTS[key]
            q.status = "Incomplete"
    load_saved_quests()                         # ← app.core.quests
    return Quests

def quests_json(quests: dict) -> list:
    return [{"key": k, "name": q.name, "xp": q.xp,
             "stat": q.target_stat, "done": q.status == "Complete"}
            for k, q in quests.items()]

# ══════════════════════════════════════════════════════════════════════════
#  DAY RECORDS
# ══════════════════════════════════════════════════════════════════════════
def get_today_record() -> dict | None:
    logs = _load(DAY_F, [])
    if not isinstance(logs, list):
        return None
    for r in logs:
        if r.get("date") == today_str():
            return r
    return None

def upsert_today_record(rec: dict):
    logs = _load(DAY_F, [])
    if not isinstance(logs, list):
        logs = []
    for i, r in enumerate(logs):
        if r.get("date") == today_str():
            logs[i] = rec
            _save(DAY_F, logs)
            return
    logs.append(rec)
    _save(DAY_F, logs)

def get_streaks() -> tuple[int, int]:
    streak = best = 0
    logs = _load(DAY_F, [])
    if not isinstance(logs, list):
        return 0, 0
    for rec in reversed(logs):
        if rec.get("date") == today_str():
            continue
        streak = (streak + 1) if rec.get("passed") else 0
        best   = max(best, streak)
    return streak, best

# ══════════════════════════════════════════════════════════════════════════
#  SERVE HTML
# ══════════════════════════════════════════════════════════════════════════
@app.route("/")
def index():
    return send_from_directory(BASE, "LIFE-tracker.html")

# ══════════════════════════════════════════════════════════════════════════
#  STATUS
# ══════════════════════════════════════════════════════════════════════════
@app.route("/api/status")
def api_status():
    day    = current_day()
    info   = get_phase_info(day)            # ← app.core.rules.get_phase_info
    cfg    = get_config()
    player = load_player()
    stats  = load_stats()
    quests = load_quests()
    today  = today_str()

    scale_quests(day, quests)               # ← app.core.quests.scale_quests
    save_all_quests()                       # ← app.core.quests.save_all_quests

    sessions_today = [s for s in _load(SESSION_F, []) if s.get("date") == today]
    pillars_today  = [p for p in _load(PLOG_F, [])
                      if p.get("date") == today and p.get("type") == "pillar"]
    day_rec        = get_today_record()
    streak, best   = get_streaks()

    return jsonify({
        "player":               player_dict(player),
        "stats":                stats_json(stats),
        "quests":               quests_json(quests),
        "day":                  day,
        "phase":                info["phase"],
        "phase_name":           info["phase_name"],
        "phase_start":          info["phase_start"],
        "phase_end":            info["phase_end"],
        "phase_day":            info["phase_day"],
        "arc_start":            cfg["arc_start"],
        "today":                today,
        "day_started":          day_rec is not None,
        "start_time":           day_rec.get("start_time") if day_rec else None,
        "sessions_today":       sessions_today,
        "pillars_today":        pillars_today,
        "streak":               streak,
        "best_streak":          best,
        "min_session_duration": info["min_session"],
    })

# ══════════════════════════════════════════════════════════════════════════
#  DAY FLOW
# ══════════════════════════════════════════════════════════════════════════
@app.route("/api/start_day", methods=["POST"])
def api_start_day():
    if get_today_record():
        return jsonify({"ok": False, "msg": "Day already started"})
    day    = current_day()
    player = load_player()
    now    = datetime.now().isoformat()
    upsert_today_record({
        "date":            today_str(),
        "day":             day,
        "phase":           get_phase(day),      # ← app.core.rules.get_phase
        "start_time":      now,
        "end_time":        None,
        "passed":          None,
        "player_before":   player_dict(player),
        "dopamine_intact": True,
        "streak_after":    0,
        "best_streak":     0,
    })
    return jsonify({"ok": True, "start_time": now})

@app.route("/api/end_day", methods=["POST"])
def api_end_day():
    data    = request.json or {}
    day_rec = get_today_record()
    if not day_rec:
        return jsonify({"ok": False, "msg": "Start the day first"})

    today    = today_str()
    day      = current_day()
    info     = get_phase_info(day)              # ← app.core.rules
    min_dur  = info["min_session"]
    now      = datetime.now().isoformat()

    sessions = [s for s in _load(SESSION_F, []) if s.get("date") == today]
    pillars  = [p for p in _load(PLOG_F, [])
                if p.get("date") == today and p.get("type") == "pillar"]
    player   = load_player()
    stats    = load_stats()

    # Pass/fail: 3 sessions total (any slots) each hitting min_dur
    passed = sum(1 for s in sessions if s.get("duration_mins", 0) >= min_dur) >= 3

    streak, best = get_streaks()
    new_streak   = (streak + 1) if passed else 0
    new_best     = max(new_streak, best)

    day_rec.update({
        "end_time":        now,
        "passed":          passed,
        "streak_after":    new_streak,
        "best_streak":     new_best,
        "player_after":    player_dict(player),
        "dopamine_intact": data.get("dopamine_intact", True),
        "sleep_prev":      data.get("sleep_prev", ""),
        "sleep_tonight":   data.get("sleep_tonight", ""),
    })
    upsert_today_record(day_rec)

    total_xp = (sum(s.get("xp_total", 0) for s in sessions) +
                sum(p.get("xp", 0) for p in pillars))

    return jsonify({
        "ok": True, "passed": passed, "end_time": now,
        "sessions": len(sessions), "min_duration": min_dur,
        "streak": new_streak, "best_streak": new_best, "total_xp": total_xp,
        "player": player_dict(player), "stats": stats_json(stats),
    })

# ══════════════════════════════════════════════════════════════════════════
#  SESSIONS
# ══════════════════════════════════════════════════════════════════════════
@app.route("/api/sessions")
def api_sessions():
    return jsonify([s for s in _load(SESSION_F, []) if s.get("date") == today_str()])

@app.route("/api/session/start", methods=["POST"])
def api_session_start():
    data      = request.json or {}
    slot      = data.get("slot", "Morning")
    task      = data.get("task", "")
    task_type = data.get("task_type", "Study")
    sessions  = _load(SESSION_F, [])

    if any(s.get("status") == "running" for s in sessions):
        return jsonify({"ok": False, "msg": "A session is already running — stop it first"})

    now = datetime.now().isoformat()
    sid = f"{today_str()}-{slot}-{int(time.time())}"
    sessions.append({
        "id":             sid,
        "date":           today_str(),
        "day":            current_day(),
        "slot":           slot,
        "task":           task,
        "task_type":      task_type,
        "secondary_stat": TASK_STAT_MAP.get(task_type, "Intelligence"),  # ← app.core.rules
        "start_time":     now,
        "end_time":       None,
        "duration_mins":  0,
        "output":         "",
        "key_wins":       "",
        "xp_total":       0,
        "status":         "running",
    })
    _save(SESSION_F, sessions)
    return jsonify({"ok": True, "session_id": sid, "start_time": now, "slot": slot, "task": task})

@app.route("/api/session/stop", methods=["POST"])
def api_session_stop():
    data     = request.json or {}
    sid      = data.get("session_id")
    output   = data.get("output", "")
    key_wins = data.get("key_wins", "")
    # Override: if user manually enters duration, use that instead of clock time
    manual_mins = data.get("manual_duration_mins")
    now      = datetime.now()

    sessions = _load(SESSION_F, [])
    target   = next((s for s in sessions if s["id"] == sid), None)
    if not target:
        return jsonify({"ok": False, "msg": "Session not found"})

    if manual_mins is not None:
        dur_mins = max(0, int(manual_mins))      # use manually entered duration
    else:
        dur_mins = max(0, int((now - datetime.fromisoformat(target["start_time"])).total_seconds() / 60))
    xp       = session_xp(dur_mins)            # ← app.core.rules.session_xp

    target.update({"end_time": now.isoformat(), "duration_mins": dur_mins,
                   "output": output, "key_wins": key_wins,
                   "xp_total": xp, "status": "done"})
    _save(SESSION_F, sessions)

    # XP duplication rule: Willpower + secondary stat both get 100%
    sec_stat = target["secondary_stat"]
    stats    = load_stats()
    stats["Willpower"].add_xp(xp)              # ← app.core.stats.Stat.add_xp
    if sec_stat != "Willpower":
        stats[sec_stat].add_xp(xp)
    save_stats(stats)

    player = load_player()
    player.xp_reward(xp)                       # ← app.core.player.Player.xp_reward
    save_player(player)

    phase   = get_phase(current_day())         # ← app.core.rules.get_phase
    md_text = _session_md(target, phase)
    fname   = f"Day{target['day']}-{target['slot']}-{sid[-6:]}.md"
    with open(os.path.join(LOGS_DIR, fname), "w") as f:
        f.write(md_text)

    return jsonify({
        "ok": True, "duration_mins": dur_mins, "xp": xp, "secondary_stat": sec_stat,
        "player": player_dict(player), "stats": stats_json(stats),
        "markdown": md_text, "session": target,
    })

@app.route("/api/session/cancel", methods=["POST"])
def api_session_cancel():
    sid      = (request.json or {}).get("session_id")
    sessions = _load(SESSION_F, [])
    before   = len(sessions)
    sessions = [s for s in sessions if s["id"] != sid]
    if len(sessions) == before:
        return jsonify({"ok": False, "msg": "Session not found"})
    _save(SESSION_F, sessions)
    return jsonify({"ok": True, "msg": "Session cancelled and removed"})

def _session_md(s, phase):
    pname = PHASE_NAMES.get(phase, "")         # ← app.core.rules.PHASE_NAMES
    sf    = s["start_time"][:16].replace("T", " ")
    ef    = (s.get("end_time") or "—")[:16].replace("T", " ")
    return (f"---\nPhase: {phase} — {pname}\n"
            f"Day: {s['day']} | Slot: {s['slot']} | Date: {s['date']}\n---\n\n"
            f"# Day {s['day']} — {s['slot']} Session\n\n"
            f"**Duration:** {sf} → {ef} = {s.get('duration_mins',0)} min\n"
            f"**Task:** {s.get('task','')}\n"
            f"**Output:** {s.get('output','')}\n"
            f"**Key Wins:** {s.get('key_wins','')}\n"
            f"**XP:** +{s.get('xp_total',0)} → Willpower + {s.get('secondary_stat','')} (both 100%)\n")

# ══════════════════════════════════════════════════════════════════════════
#  PILLARS
# ══════════════════════════════════════════════════════════════════════════
@app.route("/api/pillars")
def api_pillars():
    return jsonify([p for p in _load(PLOG_F, [])
                    if p.get("date") == today_str() and p.get("type") == "pillar"])

@app.route("/api/pillar/log", methods=["POST"])
def api_pillar_log():
    data   = request.json or {}
    name   = data.get("name")
    amount = int(data.get("amount", 0))

    if name not in PILLAR_STAT:                 # ← app.core.rules.PILLAR_STAT
        return jsonify({"ok": False, "msg": "Unknown pillar"})

    stat   = PILLAR_STAT[name]
    xp     = amount * 10 if name == "Reading" else pillar_xp(amount)  # Reading: 1 page = 10 XP
    stats  = load_stats()
    stats[stat].add_xp(xp)                      # ← app.core.stats.Stat.add_xp
    save_stats(stats)

    player = load_player()
    player.xp_reward(xp)                        # ← app.core.player.Player.xp_reward
    save_player(player)

    unit = PILLAR_UNITS.get(name, "reps")       # ← app.core.rules.PILLAR_UNITS
    log  = _load(PLOG_F, [])
    log.append({
        "type": "pillar", "date": today_str(), "day": current_day(),
        "name": name, "amount": amount, "unit": unit,
        "stat": stat, "xp": xp,
        "time": datetime.now().isoformat(), "book": data.get("book", ""),
    })
    _save(PLOG_F, log)
    return jsonify({"ok": True, "xp": xp, "stat": stat,
                    "player": player_dict(player), "stats": stats_json(stats)})

# ══════════════════════════════════════════════════════════════════════════
#  EXTRA LOGS
# ══════════════════════════════════════════════════════════════════════════
@app.route("/api/log/wakeup", methods=["POST"])
def api_log_wakeup():
    wt   = (request.json or {}).get("time", "")
    xp   = wakeup_xp(wt)                       # ← app.core.rules.wakeup_xp
    stats = load_stats()
    player = load_player()
    if xp > 0:
        stats["Willpower"].add_xp(xp)
        save_stats(stats)
        player.xp_reward(xp)
        save_player(player)
    day_rec = get_today_record()
    if day_rec:
        day_rec.update({"wakeup_time": wt, "wakeup_xp": xp})
        upsert_today_record(day_rec)
    log = _load(PLOG_F, [])
    log.append({"type": "wakeup", "date": today_str(), "day": current_day(),
                "wakeup_time": wt, "xp": xp, "stat": "Willpower" if xp > 0 else "",
                "name": f"Wakeup at {wt}", "time": datetime.now().isoformat()})
    _save(PLOG_F, log)
    return jsonify({"ok": True, "xp": xp,
                    "player": player_dict(player), "stats": stats_json(stats)})

@app.route("/api/log/running", methods=["POST"])
def api_log_running():
    data   = request.json or {}
    meters = float(data.get("meters", 0))
    mins   = float(data.get("minutes", 0))
    xp     = running_xp(meters)                # ← app.core.rules.running_xp
    stats  = load_stats()
    player = load_player()
    stats["Vitality"].add_xp(xp)
    save_stats(stats)
    player.xp_reward(xp)
    save_player(player)
    log = _load(PLOG_F, [])
    log.append({"type": "running", "date": today_str(), "day": current_day(),
                "meters": meters, "minutes": mins, "xp": xp, "stat": "Vitality",
                "name": f"Run {int(meters)}m", "time": datetime.now().isoformat()})
    _save(PLOG_F, log)
    return jsonify({"ok": True, "xp": xp,
                    "player": player_dict(player), "stats": stats_json(stats)})

@app.route("/api/log/dopamine_slip", methods=["POST"])
def api_log_dopamine_slip():
    day_rec = get_today_record()
    if day_rec:
        day_rec["dopamine_intact"] = False
        upsert_today_record(day_rec)
    cfg = get_config()
    cfg["detox_start"] = today_str()
    _save(CONFIG_F, cfg)
    return jsonify({"ok": True, "msg": "Detox counter reset to Day 1"})

@app.route("/api/log/custom", methods=["POST"])
def api_log_custom():
    data   = request.json or {}
    name   = data.get("name", "")
    stat   = data.get("stat", "Willpower")
    xp     = int(data.get("xp", 0))
    stats  = load_stats()
    player = load_player()
    if xp > 0 and stat in stats:
        stats[stat].add_xp(xp)
        save_stats(stats)
        player.xp_reward(xp)
        save_player(player)
    log = _load(PLOG_F, [])
    log.append({"type": "custom", "date": today_str(), "day": current_day(),
                "name": name, "stat": stat, "xp": xp, "time": datetime.now().isoformat()})
    _save(PLOG_F, log)
    return jsonify({"ok": True, "xp": xp,
                    "player": player_dict(player), "stats": stats_json(stats)})

# ══════════════════════════════════════════════════════════════════════════
#  QUESTS  — app.core.quests
# ══════════════════════════════════════════════════════════════════════════
@app.route("/api/quests")
def api_quests():
    return jsonify(quests_json(load_quests()))

@app.route("/api/quest/toggle", methods=["POST"])
def api_quest_toggle():
    idx    = (request.json or {}).get("index", 0)
    quests = load_quests()
    keys   = list(quests.keys())
    if idx >= len(keys):
        return jsonify({"ok": False, "msg": "Index out of range"})

    quest  = quests[keys[idx]]
    stats  = load_stats()
    player = load_player()

    if quest.status == "Complete":
        quest.status = "Incomplete"
    else:
        quest.status = "Complete"
        stats[quest.target_stat].add_xp(quest.xp)   # ← app.core.stats.Stat.add_xp
        save_stats(stats)
        player.xp_reward(quest.xp)                   # ← app.core.player.Player.xp_reward
        save_player(player)

    save_all_quests()                                 # ← app.core.quests.save_all_quests
    return jsonify({"ok": True, "quests": quests_json(quests),
                    "player": player_dict(player), "stats": stats_json(stats)})

# ══════════════════════════════════════════════════════════════════════════
#  HISTORY
# ══════════════════════════════════════════════════════════════════════════
@app.route("/api/history")
def api_history():
    return jsonify({
        "days":     list(reversed(_load(DAY_F, []))),
        "sessions": list(reversed(_load(SESSION_F, []))),
        "logs":     list(reversed(_load(PLOG_F, []))),
    })

# ══════════════════════════════════════════════════════════════════════════
#  SUMMARY
# ══════════════════════════════════════════════════════════════════════════
@app.route("/api/summary", methods=["POST"])
def api_summary():
    data   = request.json or {}
    today  = today_str()
    day    = current_day()
    info   = get_phase_info(day)                # ← app.core.rules.get_phase_info
    phase  = info["phase"]

    day_rec    = get_today_record() or {}
    streak, best = get_streaks()
    new_streak = day_rec.get("streak_after", streak)

    sessions   = [s for s in _load(SESSION_F, []) if s.get("date") == today]
    all_logs   = _load(PLOG_F, [])
    today_logs = [l for l in all_logs if l.get("date") == today]
    pillars    = [l for l in today_logs if l.get("type") == "pillar"]

    player = load_player()
    stats  = load_stats()
    quests = load_quests()
    pb     = day_rec.get("player_before", player_dict(player))

    cfg         = get_config()
    detox_start = cfg.get("detox_start", cfg.get("arc_start", "2026-03-01"))
    detox_day   = (date.today() - date.fromisoformat(detox_start)).days + 1

    wakeup_log  = next((l for l in today_logs if l.get("type") == "wakeup"), None)
    wakeup_time = wakeup_log["wakeup_time"] if wakeup_log else data.get("wakeup_time", "—")
    wu_xp       = wakeup_log["xp"] if wakeup_log else 0

    slots = {"Morning": [], "Afternoon": [], "Night": []}
    for s in sessions:
        if s.get("slot") in slots:
            slots[s["slot"]].append(s)

    def session_block(slot_name, sess_list):
        if not sess_list:
            return f"\n### {slot_name}\n- *No session logged*\n"
        out = f"\n### {slot_name}\n"
        for i, s in enumerate(sess_list, 1):
            sf = s["start_time"][:16].replace("T", " ")
            ef = (s.get("end_time") or "—")[:16].replace("T", " ")
            out += (f"\n**Session {i}**\n"
                    f"- Time: {sf} → {ef}\n"
                    f"- Duration: {s.get('duration_mins',0)} min\n"
                    f"- Task: {s.get('task','')}\n"
                    f"- Output: {s.get('output','')}\n"
                    f"- Key Wins: {s.get('key_wins','')}\n"
                    f"- XP: +{s.get('xp_total',0)} → Willpower + {s.get('secondary_stat','')}\n")
        return out

    total_session_xp = sum(s.get("xp_total", 0) for s in sessions)

    # Pillars table — uses PILLAR_TARGETS, PILLAR_UNITS from app.core.rules
    pillar_table = ""; total_pillar_xp = 0; pillars_done = 0
    for pname, target in PILLAR_TARGETS.items():
        entries = [p for p in pillars if p.get("name") == pname]
        amt     = sum(e.get("amount", 0) for e in entries)
        xp      = sum(e.get("xp", 0) for e in entries)
        unit    = PILLAR_UNITS[pname]
        chk     = "✅" if amt >= target else "❌"
        if amt >= target: pillars_done += 1
        label   = pname if pname != "Reading" else f"Reading — {amt} pages"
        pillar_table    += f"| {label} | {xp} XP | {amt} {unit} | {chk} |\n"
        total_pillar_xp += xp

    extra_lines = ""
    for l in today_logs:
        if l.get("type") == "running":
            extra_lines += f"- Run: {l.get('meters',0)}m in {l.get('minutes',0)} min → +{l.get('xp',0)} XP (Vitality)\n"
        elif l.get("type") == "custom":
            extra_lines += f"- {l.get('name','')}: +{l.get('xp',0)} XP ({l.get('stat','')})\n"
    if not extra_lines: extra_lines = "- None\n"

    quest_xp   = sum(q.xp for q in quests.values() if q.status == "Complete")
    min_dur    = info["min_session"]
    passed     = sum(1 for s in sessions if s.get("duration_mins", 0) >= min_dur) >= 3
    verdict    = "✅ CLEARED" if passed else "❌ FAILED"
    dopamine_ok = day_rec.get("dopamine_intact", True)
    sleep_prev  = data.get("sleep_prev",    day_rec.get("sleep_prev", "—"))
    sleep_night = data.get("sleep_tonight", day_rec.get("sleep_tonight", "—"))
    phase_name  = info["phase_name"]

    md = f"""---
tags:
  - WRA
  - Phase-{phase}
  - Day-{day}
  - {phase_name.replace(' ', '-').replace('—', '')}
  - {"CLEARED" if passed else "FAILED"}
  - {"DOPAMINE-INTACT" if dopamine_ok else "DOPAMINE-SLIPPED"}
  - LIFE-OS-ALIGNED
date: {today}
streak: {new_streak}
level_before: {pb.get('level', 1)}
level_after: {player.level}
rank: {player.rank}
status: {"CLEARED" if passed else "FAILED"}
dopamine_detox_day: {detox_day}/720
---

# Day {day} — Phase {phase}: {phase_name}
**Date:** {today}
**Day of Arc:** {day}/720
**Phase Progress:** {info['phase_day']}/{info['phase_total']}
**Streak:** {new_streak} days (Best: {best})
**Status:** {verdict}

---

## Wake & Circadian
- **Wake-up time:** {wakeup_time}
  → Bonus XP: +{wu_xp} XP
- **Sleep timing (Day {day-1} → Day {day}):** {sleep_prev}
- **Sleep timing (Day {day} →):** {sleep_night}

---

## Deep Work Sessions (3 required)
{session_block('Morning',   slots['Morning'])}
{session_block('Afternoon', slots['Afternoon'])}
{session_block('Night',     slots['Night'])}

**Deep Sessions Total:** {len(sessions)} executed
**Deep Work XP Total:** {total_session_xp} XP

---

## Six Pillars

| Pillar | XP | Amount | ✓ |
|---|---|---|---|
{pillar_table}
**Pillars Status:** {pillars_done}/6 ✅
**Total Pillar XP:** {total_pillar_xp} XP

---

## Additional Logs
{extra_lines}
---

## Dopamine Detox
- Day: **{detox_day}/720**
- Status: {"🟢 INTACT" if dopamine_ok else "🔴 SLIPPED — Counter Reset"}

---

## Final Player Data

**Level:** {player.level} | **XP:** {player.xp}/{player.xp_required} | **Rank:** {player.rank}

- Strength     → Lv {stats['Strength'].level}     | {stats['Strength'].xp}/{stats['Strength'].xp_required} XP
- Vitality     → Lv {stats['Vitality'].level}     | {stats['Vitality'].xp}/{stats['Vitality'].xp_required} XP
- Intelligence → Lv {stats['Intelligence'].level} | {stats['Intelligence'].xp}/{stats['Intelligence'].xp_required} XP
- Willpower    → Lv {stats['Willpower'].level}    | {stats['Willpower'].xp}/{stats['Willpower'].xp_required} XP
- Skills       → Lv {stats['Skills'].level}       | {stats['Skills'].xp}/{stats['Skills'].xp_required} XP

**Quest XP Collected:** {quest_xp} XP

---

## Verdict
Day {day} — {verdict}
Streak: **{new_streak} days**

[[Day {day-1}]] ← previous | [[Day {day+1}]] → next
"""

    fname = f"Day-{day}-Summary.md"
    with open(os.path.join(LOGS_DIR, fname), "w") as f:
        f.write(md)
    return jsonify({"ok": True, "markdown": md, "filename": fname})

# ══════════════════════════════════════════════════════════════════════════
#  CONFIG / SETTINGS / RESET
# ══════════════════════════════════════════════════════════════════════════
@app.route("/api/config")
def api_config():
    return jsonify(get_config())

@app.route("/api/config/save", methods=["POST"])
def api_config_save():
    data = request.json or {}
    cfg  = get_config()
    if "arc_start" in data:
        cfg["arc_start"]   = data["arc_start"]
        cfg["detox_start"] = data["arc_start"]
    if "player_name" in data:
        p = load_player(); p.name = data["player_name"]; save_player(p)
    _save(CONFIG_F, cfg)
    return jsonify({"ok": True})

@app.route("/api/reset", methods=["POST"])
def api_reset():
    kind  = (request.json or {}).get("kind")
    blank_stats = {n: {"Level":1,"XP":0,"xp-required":100} for n in STAT_NAMES}
    if kind == "stats":
        _save(STATS_F, blank_stats)
        p = load_player(); p.level=1; p.xp=0; p.xp_required=100; p.rank="E"; save_player(p)
    elif kind == "logs":
        _save(PLOG_F, [])
    elif kind == "sessions":
        _save(SESSION_F, [])
    elif kind == "all":
        for f in [PLOG_F, SESSION_F, DAY_F]: _save(f, [])
        _save(STATS_F, blank_stats)
        p = load_player(); p.level=1; p.xp=0; p.xp_required=100; p.rank="E"; save_player(p)
    return jsonify({"ok": True})

# ══════════════════════════════════════════════════════════════════════════
#  SKIP DAY
# ══════════════════════════════════════════════════════════════════════════
@app.route("/api/skip_day", methods=["POST"])
def api_skip_day():
    data   = request.json or {}
    reason = data.get("reason", "").strip()
    if not reason:
        return jsonify({"ok": False, "msg": "A reason is required to skip a day"})

    skips = _load(SKIPS_F, [])
    if not isinstance(skips, list):
        skips = []

    today = today_str()

    # Can't skip the same day twice
    if any(s.get("date") == today for s in skips):
        return jsonify({"ok": False, "msg": "Today is already marked as skipped"})

    day_before_skip = current_day()
    skips.append({
        "date":      today,
        "day":       day_before_skip,
        "reason":    reason,
        "logged_at": datetime.now().isoformat(),
    })
    _save(SKIPS_F, skips)

    return jsonify({
        "ok":          True,
        "skipped_date": today,
        "skipped_day":  day_before_skip,
        "msg":          f"Day {day_before_skip} skipped. Tomorrow will still be Day {day_before_skip}.",
        "total_skips":  len(skips),
    })

@app.route("/api/skips")
def api_skips():
    skips = _load(SKIPS_F, [])
    if not isinstance(skips, list):
        skips = []
    return jsonify(skips)

# ══════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("\n  ╔══════════════════════════════════╗")
    print("  ║   LIFE OS — Server Starting      ║")
    print("  ╚══════════════════════════════════╝")
    print(f"\n  Open Chrome → http://localhost:8080\n")
    app.run(host="0.0.0.0", port=8080, debug=False)
