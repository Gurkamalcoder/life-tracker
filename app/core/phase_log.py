# phase_log.py
import json
import os
from .stats import Stat,stats,to_file,from_file
from .player import Player
from datetime import datetime
from .wra_phases import day_number,formattime


# Initialize player
player = Player("Ryuji")


from_file()
def phase_main():
    predefined_logs = [
        {"name": "Wakeup early", "stat": "Willpower"},
        {"name": "Subject study", "stat": "Intelligence"},
        {"name": "Coding", "stat": "Skills"},
        {"name": "Elevate", "stat": "Intelligence"},
        {"name": "Reading", "stat": "Intelligence"},
        {"name": "Running", "stat": "Vitality"},
    ]

    ask = input(("Ready for entering Phase logs? (YES/NO) >>> "))
    while ask.lower() == "yes":
        # Wakeup Log
        wakeup_time = input("Enter exact wakeup time (e.g. 5:00 AM): ")
        while True:
            try:
                xp = int(input(f"Enter XP for Wakeup early at {wakeup_time}: "))
                if type(xp) is int:
                    break
            except ValueError:
                print("Invalid input! Please enter a valid number.")
        stats["Willpower"].add_xp(xp)
        player.xp_reward(xp)  # Add XP to player
        phase_log_save({
            "Phase Day": day_number,
            "Entry-time": formattime,
            "Description": f"Wakeup early at {wakeup_time}",
            "XP": xp,
            "Stat": "Willpower"
        })

        # Running Log
        morning_session = input("Enter Morning session : ")
        while True:
            try:
                xp = int(input(f"Enter XP for Morning session at {morning_session}: "))
                if type(xp) is int:
                    break
            except ValueError:
                print("Invalid input! Please enter a valid number.")
        stats["Willpower"].add_xp(xp)
        player.xp_reward(xp)  # Add XP to player
        phase_log_save({
            "Phase Day": day_number,
            "Entry-time": formattime,
            "Description": f"Morning session : {morning_session}",
            "XP": xp,
            "Stat": "Willpower"
        })

        
        # Running Log
        Afternoon_session = input("Enter Afternoon session : ")
        while True:
            try:
                xp = int(input(f"Enter XP for Afternoon session at {Afternoon_session}: "))
                if type(xp) is int:
                    break
            except ValueError:
                print("Invalid input! Please enter a valid number.")
        stats["Willpower"].add_xp(xp)
        player.xp_reward(xp)  # Add XP to player
        phase_log_save({
            "Phase Day": day_number,
            "Entry-time": formattime,
            "Description": f"Afternoon session : {Afternoon_session}",
            "XP": xp,
            "Stat": "Willpower"
        })


        # Running Log
        Night_session = input("Enter Night session : ")
        while True:
            try:
                xp = int(input(f"Enter XP for Night session at {Night_session}: "))
                if type(xp) is int:
                    break
            except ValueError:
                print("Invalid input! Please enter a valid number.")
        stats["Willpower"].add_xp(xp)
        player.xp_reward(xp)  # Add XP to player
        phase_log_save({
            "Phase Day": day_number,
            "Entry-time": formattime,
            "Description": f"Night session : {Night_session}",
            "XP": xp,
            "Stat": "Willpower"
        })


        # Running Log
        running_distance = input("Enter exact running distance(eg: 5 km): ")
        while True:
            try:
                xp = int(input(f"Enter XP for Running at {running_distance}: "))
                if type(xp) is int:
                    break
            except ValueError:
                print("Invalid input! Please enter a valid number.")
        stats["Vitality"].add_xp(xp)
        player.xp_reward(xp)  # Add XP to player
        phase_log_save({
            "Phase Day": day_number,
            "Entry-time": formattime,
            "Description": f"Running distance : {running_distance}",
            "XP": xp,
            "Stat": "Vitality"
        })

        # Study Log
        subject = input("Enter subject studied: ")
        while True:
            try:
                xp = int(input(f"Enter XP for Subject study - {subject}: "))
                if type(xp) is int:
                    break
            except ValueError:
                print("Invalid input! Please enter a valid number.")
        stats["Intelligence"].add_xp(xp)
        player.xp_reward(xp)  # Add XP to player
        phase_log_save({
            "Phase Day": day_number,
            "Entry-time": formattime,
            "Description": f"Subject study - {subject}",
            "XP": xp,
            "Stat": "Intelligence"
        })

        # Coding Log
        while True:
            try:
                xp = int(input("Enter XP for Coding: "))
                if type(xp) is int:
                    break
            except ValueError:
                print("Invalid input! Please enter a valid number.")
        stats["Skills"].add_xp(xp)
        player.xp_reward(xp)  # Add XP to player
        phase_log_save({
            "Phase Day": day_number,
            "Entry-time": formattime,
            "Description": "Coding",
            "XP": xp,
            "Stat": "Skills"
        })

        # Elevate Log
        while True:
            try:
                xp = int(input("Enter XP for playing Volleyball: "))
                if type(xp) is int:
                    break
            except ValueError:
                print("Invalid input! Please enter a valid number.")
        stats["Skills"].add_xp(xp)
        player.xp_reward(xp)  # Add XP to player
        phase_log_save({
            "Phase Day": day_number,
            "Entry-time": formattime,
            "Description": "Volleyball",
            "XP": xp,
            "Stat": "Skills"
        })

        # Reading Log
        while True:
            try:
                xp = int(input("Enter XP for Reading: "))
                if type(xp) is int:
                    break
            except ValueError:
                print("Invalid input! Please enter a valid number.")
        stats["Intelligence"].add_xp(xp)
        player.xp_reward(xp)  # Add XP to player
        phase_log_save({
            "Phase Day": day_number,
            "Entry-time": formattime,
            "Description": "Reading",
            "XP": xp,
            "Stat": "Intelligence"
        })

        # Save updated stats
        to_file(stats)

        print("✅ All logs recorded.\n")

        # 📊 FINAL STATS SUMMARY
        print("==============================")
        print("     FINAL STATS SUMMARY     ")
        print("==============================")
        for stat in stats.values():
            print(f"{stat.stat:<13} → Level: {stat.level:<3} | XP: {stat.xp:<4} | XP Required: {stat.xp_required}")
        print("==============================")
        print(f"\nPlayer Level: {player.level} | Total XP: {player.xp}/{player.xp_required} | Rank: {player.rank}")
        print("==============================")
        break

def phase_log_save(entry,filename = "app/storage/phase_log.json"):
    os.makedirs(os.path.dirname(filename),exist_ok=True)

    if os.path.exists(filename):
        with open(filename,'r')as f :
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []

    else:
        data = []
        
    data.append(entry)
    
    with open(filename,"w")as f:
        json.dump(data,f,indent=4)

