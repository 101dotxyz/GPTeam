from enum import Enum
import random
import re
import time

import numpy as np
from colorama import Fore, Style

from .colors import LogColor


def print_to_console(
    title: str,
    title_color: LogColor,
    content,
    min_typing_speed=0.06,
    max_typing_speed=0.04,
):
    print(title_color.value + title + " " + Style.RESET_ALL, end="")
    if content:
        if isinstance(content, list):
            content = " ".join(content)
        lines = str(content).split("\n")
        for line in lines:
            words = line.split()
            for i, word in enumerate(words):
                print(word, end="", flush=True)
                if i < len(words) - 1:
                    print(" ", end="", flush=True)
                typing_speed = random.uniform(min_typing_speed, max_typing_speed)
                time.sleep(typing_speed)
                # type faster after each word
                min_typing_speed = min_typing_speed * 0.97
                max_typing_speed = max_typing_speed * 0.97
            print()


class AgentLogColor(Enum):
    GENERAL = Fore.WHITE
    CALVIN = Fore.LIGHTCYAN_EX
    REBECCA = Fore.YELLOW
    MARTY = Fore.BLUE
    RICARDO = Fore.MAGENTA
    JACQUELIN = Fore.RED
    ERROR = Fore.RED
    ANNOUNCEMENT = Fore.LIGHTMAGENTA_EX
    CLI_INPUT = Fore.LIGHTBLACK_EX

def print_to_console2(
    title: str,
    agent_name: str,
    content,
    min_typing_speed=0.06,
    max_typing_speed=0.04,
):
    title_color = AgentLogColor[agent_name.upper()]
    print(title_color.value + title + " " + Style.RESET_ALL, end="")
    if content:
        if isinstance(content, list):
            content = " ".join(content)
        lines = str(content).split("\n")
        for line in lines:
            words = line.split()
            for i, word in enumerate(words):
                print(word, end="", flush=True)
                if i < len(words) - 1:
                    print(" ", end="", flush=True)
                typing_speed = random.uniform(min_typing_speed, max_typing_speed)
                time.sleep(typing_speed)
                # type faster after each word
                min_typing_speed = min_typing_speed * 0.97
                max_typing_speed = max_typing_speed * 0.97
            print()


def parse_array(s: str) -> np.ndarray:
    # Split the string by comma
    elements = s.strip()[1:-1].split(",")

    # Convert each element to a float and create a NumPy array
    arr = np.array([float(e) for e in elements])

    return arr
