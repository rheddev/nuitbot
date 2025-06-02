# ANSI color codes
GREEN = "\033[32m"
RED = "\033[31m"
BLUE = "\033[34m"
CYAN = "\033[36m"
YELLOW = "\033[33m"
MAGENTA = "\033[35m"
RESET = "\033[0m"

# Helper functions for colored text
def green(text): return f"{GREEN}{text}{RESET}"
def red(text): return f"{RED}{text}{RESET}"
def blue(text): return f"{BLUE}{text}{RESET}"
def cyan(text): return f"{CYAN}{text}{RESET}"
def yellow(text): return f"{YELLOW}{text}{RESET}"
def magenta(text): return f"{MAGENTA}{text}{RESET}"