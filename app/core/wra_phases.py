# wra_phases.py

import json
from datetime import datetime

wra_start = datetime(2026,1,1)
today = datetime.now()
day_number = (today - wra_start).days + 1
formattime = today.strftime("%H:%M:%S")

def total_progress():
    wra_start = datetime(2026,1,1)
    today = datetime.now()
    day_number = (today - wra_start).days + 1
    formattime = today.strftime("%H:%M:%S")
    if day_number <= 90:
        print(f"||White room ARC >>> [phase 1/Phase 8]||Day : {day_number}||")
    elif day_number <= 180:
            print(f"||White room ARC >>> [phase 2/Phase 8]||Day : {day_number}||")
    elif day_number <= 270:
            print(f"||White room ARC >>> [phase 3/Phase 8]||Day : {day_number}||")
    elif day_number <= 360:
            print(f"||White room ARC >>> [phase 4/Phase 8]||Day : {day_number}||")
    elif day_number <= 450:
            print(f"||White room ARC >>> [phase 5/Phase 8]||Day : {day_number}||")
    elif day_number <= 540:
            print(f"||White room ARC >>> [phase 6/Phase 8]||Day : {day_number}||")
    elif day_number <= 630:
            print(f"||White room ARC >>> [phase 7/Phase 8]||Day : {day_number}||")
    elif day_number <= 720:
            print(f"||White room ARC >>> [phase 8/Phase 8]||Day : {day_number}||")
    else:
            print("Phase complete!")

def display_current_phase():
    wra_start = datetime(2026,1,1)
    today = datetime.now()
    day_number = (today - wra_start).days + 1
    formattime = today.strftime("%H:%M:%S")


    phases = load_wra_phases()

    if day_number <= 90:
        print(f"Day :{day_number}")
        phase = phases["Phase 1"]
        print(f"Phase 1 : {phase['Title']}")
        print(f"Duration: {phase['Duration']}")
        for goal in phase['goals']:
            print(f"{goal}")
        for KPI in phase['KPIs']:
            print(f"{KPI}")

    elif day_number <= 180:
        print(f"Day :{day_number}")
        phase = phases["Phase 2"]
        print(f"Phase 2 : {phase['Title']}")
        print(f"Duration: {phase['Duration']}")
        for goal in phase['goals']:
            print(f"{goal}")
        for KPI in phase['KPIs']:
            print(f"{KPI}")

    elif day_number <=270:
        print(f"Day :{day_number}")
        phase = phases["Phase 3"]
        print(f"Phase 3 : {phase['Title']}")
        print(f"Duration: {phase['Duration']}")
        for goal in phase['goals']:
            print(f"{goal}")
        for KPI in phase['KPIs']:
            print(f"{KPI}")

    elif day_number <=360:
        print(f"Day :{day_number}")
        phase = phases["Phase 4"]
        print(f"Phase 4 : {phase['Title']}")
        print(f"Duration: {phase['Duration']}")
        for goal in phase['goals']:
            print(f"{goal}")
        for KPI in phase['KPIs']:
            print(f"{KPI}")

    elif day_number <=450:
        print(f"Day :{day_number}")
        phase = phases["Phase 5"]
        print(f"Phase 5 : {phase['Title']}")
        print(f"Duration: {phase['Duration']}")
        for goal in phase['goals']:
            print(f"{goal}")
        for KPI in phase['KPIs']:
            print(f"{KPI}")

    elif day_number <=540:
        print(f"Day :{day_number}")
        phase = phases["Phase 6"]
        print(f"Phase 6 : {phase['Title']}")
        print(f"Duration: {phase['Duration']}")
        for goal in phase['goals']:
            print(f"{goal}")
        for KPI in phase['KPIs']:
            print(f"{KPI}")

    elif day_number <=630:
        print(f"Day :{day_number}")
        phase = phases["Phase 7"]
        print(f"Phase 7 : {phase['Title']}")
        print(f"Duration: {phase['Duration']}")
        for goal in phase['goals']:
            print(f"{goal}")
        for KPI in phase['KPIs']:
            print(f"{KPI}")

    elif day_number <=720:
        print(f"Day :{day_number}")
        phase = phases["Phase 8"]
        print(f"Phase 8 : {phase['Title']}")
        print(f"Duration: {phase['Duration']}")
        for goal in phase['Key Goals']:
            print(f"{goal}")
        for KPI in phase['KPIs']:
            print(f"{KPI}")

    else:
        print("Phase complete!")


def load_wra_phases(filename = "app/storage/wra_phases.json"):
    with open(filename,'r')as f:
        return json.load(f)