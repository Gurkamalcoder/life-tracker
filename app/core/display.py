import sys, time, builtins
import os

def type_print(*args, speed=0.01, end="\n", sep=" ", **kwargs):
    text = sep.join(str(a) for a in args)
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(speed)
    sys.stdout.write(end)
    sys.stdout.flush()

# Override the built-in print
builtins.print = type_print

class Colors:
    CYAN = '\033[96m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    MAGENTA = '\033[95m'
    BLUE = '\033[94m'
    WHITE = '\033[97m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def get_terminal_width():
    return os.get_terminal_size().columns

def print_separator(char="=", color=Colors.CYAN):
    width = get_terminal_width()
    print(f"{color}{char * width}{Colors.RESET}")

def print_centered(text, color=Colors.WHITE):
    width = get_terminal_width()
    # Remove ANSI codes for width calculation
    text_clean = text.replace('\033[96m', '').replace('\033[93m', '').replace('\033[91m', '').replace('\033[92m', '').replace('\033[95m', '').replace('\033[94m', '').replace('\033[97m', '').replace('\033[0m', '').replace('\033[1m', '')
    padding = (width - len(text_clean)) // 2
    print(f"{color}{' ' * padding}{text}{Colors.RESET}")

def print_title(text):
    print_separator("═")
    print_centered(text, f"{Colors.BOLD}{Colors.CYAN}")
    print_separator("═")

def print_section(text):
    print(f"{Colors.YELLOW}{Colors.BOLD}➤ {text}{Colors.RESET}")