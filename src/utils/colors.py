from enum import Enum

from colorama import Fore

NUM_AGENT_COLORS = 10


class LogColor(Enum):
    GENERAL = Fore.WHITE
    ERROR = Fore.RED
    ANNOUNCEMENT = Fore.LIGHTMAGENTA_EX
    CLI_INPUT = Fore.LIGHTBLACK_EX
    AGENT_0 = Fore.LIGHTGREEN_EX
    AGENT_1 = Fore.YELLOW
    AGENT_2 = Fore.MAGENTA
    AGENT_3 = Fore.BLUE
    AGENT_4 = Fore.RED
    AGENT_5 = Fore.LIGHTCYAN_EX
    AGENT_6 = Fore.CYAN
    AGENT_7 = Fore.LIGHTYELLOW_EX
    AGENT_8 = Fore.LIGHTBLUE_EX
    AGENT_9 = Fore.GREEN
