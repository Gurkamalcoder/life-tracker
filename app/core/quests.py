import os
import json
from .stats import stats, from_file, to_file  # type:ignore
from colorama import Fore, Style, init
from .wra_phases import day_number

init()
from_file()

# Import Player lazily to avoid circular import
player = None

# ==========================================================
# QUEST CLASS
# ==========================================================
class Quest:
    def __init__(self, name, xp, target_stat, status="Incomplete"):
        self.name = name
        self.xp = xp
        self.target_stat = target_stat
        self.status = status  # ✅ new field

    def __str__(self):
        return f"{self.name} → XP: {self.xp}, Target: {self.target_stat}, Status: {self.status}"


# ==========================================================
# QUEST STORAGE PATHS
# ==========================================================
QUEST_FILE = "app/storage/quest_log.json"
STATE_FILE = "app/storage/quest_state.json"


# ==========================================================
# DEFAULT QUESTS
# ==========================================================
Quests = {
    "Push-ups": Quest(name="100 Push-ups", xp=300, target_stat="Strength"),
    "Sit-ups": Quest(name="100 Sit-ups", xp=300, target_stat="Strength"),
    "Squats": Quest(name="100 Squats", xp=300, target_stat="Strength"),
    "Pull-ups": Quest(name="100 Pull-ups", xp=300, target_stat="Strength"),
    "Meditation": Quest(name="60 min Meditation", xp=180, target_stat="Willpower"),
}


# ==========================================================
# LOAD AND SAVE QUEST STATE
# ==========================================================
def load_last_scaled_day():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f).get("last_scaled_day", 0)
    return 0


def save_last_scaled_day(day):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump({"last_scaled_day": day}, f, indent=4)


def load_saved_quests():
    """Load whatever is currently stored in the quest file.

    This function handles both the new single-snapshot format and the old
    log-style format that used to append daily records.  Only the most recent
    ``len(Quests)`` entries are ever applied.  Empty or invalid files are
    ignored, leaving the hard-coded defaults intact.
    """
    if not os.path.exists(QUEST_FILE):
        return

    try:
        with open(QUEST_FILE, "r") as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError):
        # unreadable or bad JSON; keep defaults
        return

    # legacy log format: a flat list of days.  Keep only the final snapshot.
    if (
        isinstance(data, list)
        and data
        and isinstance(data[0], dict)
        and "Day" in data[0]
    ):
        if len(data) < len(Quests):
            return
        data = data[-len(Quests) :]

    if not isinstance(data, list):
        return

    for rec, quest in zip(data, Quests.values()):
        quest.name = rec.get("name", quest.name)
        quest.xp = rec.get("xp", quest.xp)
        quest.target_stat = rec.get("target_stat", quest.target_stat)
        quest.status = rec.get("status", quest.status)


def save_all_quests(filename=QUEST_FILE):
    """Write a single snapshot of the current quests to disk.

    This overwrites any previous contents, preventing the file from growing
    indefinitely and ensuring manual edits are respected on the next load.
    """
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    snapshot = [
        {
            "name": q.name,
            "xp": q.xp,
            "target_stat": q.target_stat,
            "status": q.status,
        }
        for q in Quests.values()
    ]

    with open(filename, "w") as f:
        json.dump(snapshot, f, indent=4)


# ==========================================================
# QUEST SCALING
# ==========================================================
def scale_quests(day_number, quests):
    """Increase quest difficulty every 30 days persistently."""
    last_scaled_day = load_last_scaled_day()

    if day_number % 30 == 1 and day_number > 1 and day_number != last_scaled_day:
        for quest in quests.values():
            if "Meditation" in quest.name:
                continue

            parts = quest.name.split(" ", 1)
            if parts[0].isdigit():
                reps = int(parts[0]) + 10
                quest.name = f"{reps} {parts[1]}"
            quest.xp += 30

        save_last_scaled_day(day_number)
        save_all_quests()
        print(f"📈 Quests scaled for Day {day_number}! (+10 reps, +30 XP)")


# ==========================================================
# QUEST ACCESS FUNCTIONS
# ==========================================================
def get_quests_by_names(names):
    return [Quests[name] for name in names if name in Quests]


def get_all_quests_data():
    return [
        {
            "key": key,
            "name": q.name,
            "xp": q.xp,
            "target_stat": q.target_stat,
            "status": q.status,
        }
        for key, q in Quests.items()
    ]


# ==========================================================
# XP COLLECTION
# ==========================================================
def collect_xp():
    global player
    if player is None:
        from .player import Player
        player = Player("Ryuji")

    while True:
        try:
            n = input("All quests done? (YES/NO) 🏹 ").lower()
            if n in ("yes", "no"):
                break
            print("please answer YES or NO")
        except Exception as e:
            print(f"Error: {e}. Try again.")

    if n == "yes":
        total_xp = 0
        for quest in Quests.values():
            quest.status = "Complete"
            total_xp += quest.xp
            for stat_obj in stats.values():
                if stat_obj.stat == quest.target_stat:
                    stat_obj.add_xp(quest.xp)

        to_file(stats)
        save_all_quests()
        player.xp_reward(total_xp)

        # …print summary (unchanged) …
        return total_xp

    else:  # n == "no"
        print("=" * 42)
        print(
            "{:<5}{:<18}{:<10}{:<10}{:<15}".format(
                "No.", "Quest", "XP", "Stat", "Status"
            )
        )
        print("=" * 42)

        numbered = list(Quests.items())
        for idx, (key, q) in enumerate(numbered, start=1):
            print(
                "{:<5}{:<18}{:<10}{:<10}{:<15}".format(
                    idx, q.name, q.xp, q.target_stat, q.status
                )
            )
        print("=" * 42)

        incomplete = input("Enter incomplete quest numbers (comma-separated) 🏹 ")
        incomplete_idx = [
            int(i.strip()) - 1
            for i in incomplete.split(",")
            if i.strip().isdigit()
        ]

        gained_xp = 0
        for idx, (key, q) in enumerate(numbered):
            if idx in incomplete_idx:
                q.status = "Incomplete"
            else:
                q.status = "Complete"
                gained_xp += q.xp
                for stat_obj in stats.values():
                    if stat_obj.stat == q.target_stat:
                        stat_obj.add_xp(q.xp)

        to_file(stats)
        save_all_quests()
        player.xp_reward(gained_xp)

        # …print summary (unchanged) …
        return gained_xp


# ==========================================================
# INITIAL LOAD
# ==========================================================
load_saved_quests()
scale_quests(day_number, Quests)
save_all_quests()