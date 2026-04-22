from app.core.player import Player,display_status,display_quests,ask_quests
from app.core.quests import collect_xp,Quests,scale_quests
from app.core.stats import from_file
from app.core.phase_log import phase_main
from app.core.wra_phases import display_current_phase,total_progress,day_number
from colorama import Fore, Style, init
import os
init()

from app.core.display import type_print, Colors,get_terminal_width,print_separator,print_centered,print_title,print_section

type_print("Booting Life OS...", 0.02)
type_print("System Ready.", 0.03)




print_title(Style.BRIGHT + Fore.LIGHTGREEN_EX + "WELCOME TO LIFE OS".center(60) + Style.RESET_ALL)





def main():
    #Call functions from other files
    total_progress()
    print_separator("═")
    display_status()


    scale_quests(day_number, Quests)
    print_title("TODAY's QUEST's")
    display_quests()

    print_centered("PHASE LOG")
    print_separator("═")
    phase_main()
    # print_separator("═")
    # print_centered(Style.BRIGHT + Fore.LIGHTGREEN_EX, "PHASE LOG".center(30) + Style.RESET_ALL)
    # print_separator("═")

    print_separator("═")
    player = Player("Ryuji")
    # prompt about quests and show updated player/stats automatically
    ask_quests()
    print_separator("═")
    

if __name__ == "__main__":
    main()
