import random
import time

from colorama import Fore, Style


def colored_text(text: str, color: str) -> str:
    return color + text + Style.RESET_ALL

def print_to_console(
        title,
        title_color,
        content,
        min_typing_speed=0.05,
        max_typing_speed=0.01):
    print(title_color + title + " " + Style.RESET_ALL, end="")
    if content:
        if isinstance(content, list):
            content = " ".join(content)
        words = content.split()
        for i, word in enumerate(words):
            print(word, end="", flush=True)
            if i < len(words) - 1:
                print(" ", end="", flush=True)
            typing_speed = random.uniform(min_typing_speed, max_typing_speed)
            time.sleep(typing_speed)
            # type faster after each word
            min_typing_speed = min_typing_speed * 0.95
            max_typing_speed = max_typing_speed * 0.95
    print()