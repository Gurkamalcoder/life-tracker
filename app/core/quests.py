from .stats import stats, from_file, to_file
from colorama import Fore, Style, init
from .wra_phases import day_number
import json
import os

init()
from_file()

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
    "Meditation": Quest(name="60 min Meditation", xp=180, target_stat="Willpower")
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
    """Load quest data (including status) from JSON if exists"""
    if os.path.exists(QUEST_FILE):
        with open(QUEST_FILE, "r") as f:
            data = json.load(f)
            for i, (key, quest) in enumerate(Quests.items()):
                if i < len(data):
                    quest.name = data[i]["name"]
                    quest.xp = data[i]["xp"]
                    quest.target_stat = data[i]["target_stat"]
                    quest.status = data[i].get("status", "Incomplete")


def save_all_quests(filename=QUEST_FILE):
    """Save all current quest data (with status)"""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    data = [
        {
            "Day": day_number,
            "name": q.name,
            "xp": q.xp,
            "target_stat": q.target_stat,
            "status": q.status
        }
        for q in Quests.values()
    ]
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)


# ==========================================================
# QUEST SCALING
# ==========================================================
def scale_quests(day_number, quests):
    """Increase quest difficulty every 30 days persistently"""
    last_scaled_day = load_last_scaled_day()

    if day_number % 30 == 0 and day_number != 0 and day_number != last_scaled_day:
        for quest in quests.values():
            parts = quest.name.split(" ", 1)
            if parts[0].isdigit():
                new_count = int(parts[0]) + 10
                quest.name = f"{new_count} {parts[1]}"
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
            "status": q.status
        }
        for key, q in Quests.items()
    ]


# ==========================================================
# XP COLLECTION
# ==========================================================
def collect_xp():
    while True:
        try:
            n = input("All quests done? (YES/NO) 🏹 ").lower()
            if n in ["yes", "no"]:
                break
            else:
                print("Please enter 'YES' or 'NO'.")
        except Exception as e:
            print(f"Error: {e}. Try again.")

    if n == "yes":
        total_xp = 0
        for quest in Quests.values():
            quest.status = "Complete"  # ✅ mark all as complete
            total_xp += quest.xp
            for stat_obj in stats.values():
                if stat_obj.stat == quest.target_stat:
                    stat_obj.add_xp(quest.xp)
                    break

        to_file(stats)
        save_all_quests()

        print(f"Total XP collected 🏹 {total_xp}")
        print("=" * 30)
        print(Style.BRIGHT + Fore.BLUE + "STATS".center(30) + Style.RESET_ALL)
        print("=" * 30)
        for s in stats.values():
            print("=" * 30)
            print(f"{s.stat} → Level: {s.level}, XP: {s.xp}")
        return total_xp

    elif n == "no":
        print("=" * 42)
        print("{:<5}{:<18}{:<10}{:<10}{:<15}".format("No.", "Quest", "XP", "Stat", "Status"))
        print("=" * 42)

        numbered = list(Quests.items())
        for idx, (key, q) in enumerate(numbered, start=1):
            print("{:<5}{:<18}{:<10}{:<10}{:<15}".format(idx, q.name, q.xp, q.target_stat, q.status))
        print("=" * 42)

        incomplete = input("Enter incomplete quest numbers (comma-separated) 🏹 ")
        incomplete_idx = [int(i.strip()) - 1 for i in incomplete.split(",") if i.strip().isdigit()]

        gained_xp = 0
        for idx, (key, q) in enumerate(numbered):
            if idx in incomplete_idx:
                q.status = "Incomplete"
            else:
                q.status = "Complete"
                for stat_obj in stats.values():
                    if stat_obj.stat == q.target_stat:
                        stat_obj.add_xp(q.xp)
                        break
                gained_xp += q.xp

        to_file(stats)
        save_all_quests()

        print("=" * 30)
        print(f"Total XP collected 🏹 {gained_xp}")
        return gained_xp


# ==========================================================
# INITIAL LOAD
# ==========================================================
load_saved_quests()
scale_quests(day_number, Quests)
save_all_quests()
