from enum import Enum

from colorama import Fore


class LogColor(Enum):
    GENERAL = Fore.WHITE
    PLAN = Fore.GREEN
    MOVE = Fore.LIGHTCYAN_EX
    REACT = Fore.YELLOW
    ACT = Fore.BLUE
    MESSAGE = Fore.LIGHTBLUE_EX
    REFLECT = Fore.MAGENTA
    MEMORY = Fore.RED
    THOUGHT = Fore.LIGHTBLACK_EX
    ERROR = Fore.RED
    ANNOUNCEMENT = Fore.LIGHTMAGENTA_EX
