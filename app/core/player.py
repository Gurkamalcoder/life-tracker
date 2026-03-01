# player.py

import json
import os
from .quests import Quests, collect_xp
from .stats import from_file as load_stats, to_file as save_stats

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
        return 100 + (self.level - 1) * 50

    def update_level(self):
        while self.xp >= self.xp_required:
            self.level += 1
            self.xp -= self.xp_required
            self.xp_required = self.calculate_xp_required()
            self.update_rank()

    def update_rank(self):
        if self.level <= 10:
            self.rank = "E"
        elif self.level <= 25:
            self.rank = "D"
        elif self.level <= 50:
            self.rank = "C"
        elif self.level <= 75:
            self.rank = "B"
        elif self.level <= 125:
            self.rank = "A"
        elif self.level <= 200:
            self.rank = "S"
        elif self.level <= 300:
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
    print("{:<13}{:<8}{:<21}{:<15}".format(
        f"||Level 🏹{player.level}||",
        f"XP 🏹{player.xp}||",
        f"XP required 🏹{player.xp_required}||",
        f"Rank 🏹{player.rank}||"
    ))
    print("=" * 60)


def display_quests():
    print("=" * 42)
    print("{:<18}{:<16}{:<15}".format("||Quest||", "||XP||", "||Stat||"))
    print("=" * 42)
    for key, quest in Quests.items():
        print("{:<20}{:<15}{:<15}".format(quest.name, quest.xp, f"{quest.target_stat}||"))
    print("=" * 42)


def ask_quests():
    gained = collect_xp()
    player.xp_reward(gained)
    save_stats()
