from enum import Enum

from colorama import Fore


class LogColor(Enum):
    GENERAL = Fore.WHITE
    PLAN = Fore.GREEN
    MOVE = Fore.CYAN
    REACT = Fore.YELLOW
    ACT = Fore.BLUE
    REFLECT = Fore.MAGENTA
    MEMORY = Fore.RED
