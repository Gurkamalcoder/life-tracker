from app.core.player import Player,display_status,display_quests,ask_quests
from app.core.quests import collect_xp,Quests,scale_quests
from app.core.stats import from_file
from app.core.phase_log import phase_main
from app.core.wra_phases import display_current_phase,total_progress,day_number
from colorama import Fore, Style, init
init()

from app.core.display import type_print

type_print("Booting Life OS...", 0.02)
type_print("System Ready.", 0.03)



print("=" * 60)
print(Style.BRIGHT + Fore.BLUE + "WELCOME TO LIFE OS".center(60) + Style.RESET_ALL)
print("=" * 60)




def main():
    #Call functions from other files
    print("=" * 60)
    total_progress()
    print("=" * 60)
    display_status()


    scale_quests(day_number, Quests)
    print("=" * 30)
    print(Style.BRIGHT + Fore.LIGHTGREEN_EX, "TODAY's QUEST's".center(30) + Style.RESET_ALL)
    print("=" * 30)
    display_quests()

    print("="*30)
    print(Style.BRIGHT + Fore.LIGHTGREEN_EX, "PHASE LOG".center(30) + Style.RESET_ALL)
    print("="*30)
    phase_main()

    print("="*30)
    player = Player("Ryuji")
    # gained_xp = collect_xp()
    player.xp_reward(collect_xp())
    print("="*30)
    

if __name__ == "__main__":
    main()
