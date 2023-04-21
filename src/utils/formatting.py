import random
import time

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
        words = str(content).split()
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
