from colorama import Fore

from ..utils.formatting import print_to_console


def get_user_input(question: str):
    print_to_console("Question", Fore.MAGENTA, question)
    i = input()
    return i
