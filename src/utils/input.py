from colorama import Fore

from ..utils.formatting import print_to_console, AgentLogColor
from .colors import LogColor


def get_user_input(question: str):
    print_to_console("Question", AgentLogColor.CLI_INPUT, question)
    i = input()
    return i
