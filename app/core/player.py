# player.py

import json
import os
from .quests import Quests, collect_xp
from .stats import from_file as load_stats, to_file as save_stats #type:ignore
from app.core.display import type_print, Colors,get_terminal_width,print_separator,print_centered,print_title,print_section

class Player:
    def __init__(self, name):
        self.name = name
        self.level = 1
        self.xp = 0
        self.xp_required = 100
        self.rank = "E"
        self.load()  # Load if file exists

    def xp_reward(self, amount):
        if amount <= 0:
            return
        self.xp += amount
        self.update_level()
        self.save()

    def calculate_xp_required(self):
        if self.rank == "E":  # levels 1-25
            return 100 + (self.level - 1) * 50
        elif self.rank == "D":  # levels 26-50
            return 100 + (self.level - 1) * 75
        elif self.rank == "C":  # levels 51-100
            return 100 + (self.level - 1) * 100
        elif self.rank == "B":  # levels 101-175
            return 100 + (self.level - 1) * 150
        elif self.rank == "A":  # levels 176-275
            return 100 + (self.level - 1) * 200
        elif self.rank == "S":  # levels 276-400
            return 100 + (self.level - 1) * 250
        elif self.rank == "SS":  # levels 401-550
            return 100 + (self.level - 1) * 300
        else:  # SSS+
            return 100 + (self.level - 1) * 350

    def update_level(self):
        while self.xp >= self.xp_required:
            self.level += 1
            self.xp -= self.xp_required
            self.xp_required = self.calculate_xp_required()
            self.update_rank()

    def update_rank(self):
        if self.level <= 25:
            self.rank = "E"
        elif self.level <= 50:
            self.rank = "D"
        elif self.level <= 100:
            self.rank = "C"
        elif self.level <= 175:
            self.rank = "B"
        elif self.level <= 275:
            self.rank = "A"
        elif self.level <= 400:
            self.rank = "S"
        elif self.level <= 550:
            self.rank = "SS"
        else:
            self.rank = "SSS+"

    def save(self, filename="app/storage/player.json"):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        data = {
            "name": self.name,
            "level": self.level,
            "xp": self.xp,
            "xp_required": self.xp_required,
            "rank": self.rank
        }
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)

    def load(self, filename="app/storage/player.json"):
        if not os.path.exists(filename):
            return
        with open(filename, 'r') as f:
            data = json.load(f)
        self.name = data.get("name", self.name)
        self.level = data.get("level", 1)
        self.xp = data.get("xp", 0)
        self.xp_required = data.get("xp_required", self.calculate_xp_required())
        self.rank = data.get("rank", "E")


# SINGLE GLOBAL PLAYER INSTANCE
player = Player("Ryuji")
load_stats()


def display_status():
    print_centered("{:<13}{:<8}{:<21}{:<15}".format(
        f"||Level 🏹{player.level}||",
        f"XP 🏹{player.xp}||",
        f"XP required 🏹{player.xp_required}||",
        f"Rank 🏹{player.rank}||"
    ))
    

def display_stats():
    """Show all player stats with current levels and xp."""
    from .stats import stats

    print_centered("{:<15}{:<10}{:<12}{:<15}".format("Stat", "Level", "XP", "XP required"))
    print_separator("═")
    for stat_obj in stats.values():
        print_centered("{:<15}{:<10}{:<12}{:<15}".format(
            stat_obj.stat,
            stat_obj.level,
            stat_obj.xp,
            stat_obj.xp_required,
        ))
    print_separator("═")


def display_quests():
    print_centered("{:<20}{:<20}{:<20}".format("||Quest||", "||XP||", "||Stat||"))
    print_separator("═")
    for key, quest in Quests.items():
        print_centered("{:<20}{:<20}{:<20}".format(quest.name, str(quest.xp), f"{quest.target_stat}||"))
    print_separator("═")


def ask_quests():
    """Prompt the user about quest completion, save progress and show stats.

    ``collect_xp`` handles the actual xp calculation and updates the player
    and stats objects.  Here we just persist and then display the updated
    information so the user can immediately see the results.
    """

    gained = collect_xp()
    # collect_xp already rewarded xp; just make sure the player data is saved
    player.save()

    # display new status for the player and all stats
    print_separator("═")
    print("\nUpdated player info:")
    display_status()
    print_separator("═")
    display_stats()

    return gained
