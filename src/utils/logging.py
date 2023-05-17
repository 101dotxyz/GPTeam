import atexit
import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import List

import openai
import pytz


def clean_json_string(json_string):
    cleaned_string = re.sub(r"\\\'", r"'", json_string)  # replace \' with '
    cleaned_string = re.sub(
        r'\\"', r'"', cleaned_string
    )  # replace \" with " on cleaned_string
    return cleaned_string


def get_completion_data(text) -> List[str]:
    pattern = r"(api_version=[^\s]+)|(data=(.+?)(?= [^\s]+=))|(message='(.+?)')"
    matches = re.findall(pattern, text)
    cleaned_matches = []

    for match in matches:
        for item in match:
            if item != "":
                cleaned_matches.append(item)
                break

    return cleaned_matches


def get_key_value(text):
    pattern = r"(\w+)=((?:\"(?:\\\"|[^\"])*\")|(?:\'(?:\\\'|[^'])*\'))"
    matches = re.findall(pattern, text)
    result = {}

    for match in matches:
        key, value = match[0], match[1]
        # Remove the outer quotes and unescape the inner quotes
        if value.startswith('"'):
            value = value[1:-1].replace('\\"', '"')
        else:
            value = value[1:-1].replace("\\'", "'")
        result[key] = value

    return result


class OpenAIFilter(logging.Filter):
    def filter(self, record):
        return "openai" in record.name


class JsonArrayFileHandler(logging.FileHandler):
    def __init__(self, filename, mode="a", encoding=None, delay=False):
        super().__init__(filename, mode, encoding, delay)
        self.closed_properly = False
        self.stream.write("[")
        atexit.register(self.close)

    def close(self):
        self.acquire()
        try:
            if not self.closed_properly:
                self.stream.write("]")
                self.closed_properly = True
            super().close()
        finally:
            self.release()

    def emit(self, record):
        if self.stream.tell() > 1:
            self.stream.write(",\n")
        super().emit(record)


class LoggingFilter(logging.Filter):
    def filter(self, record):
        print("logging filter", record)
        return True


def init_logging():
    openai.util.logger.setLevel(logging.WARNING)
    open("src/web/logs/agent.txt", "w").close()


def get_agent_logger():
    # Create a logger
    logger = logging.getLogger("agent")
    logger.setLevel(logging.INFO)

    # Prevent log messages from being passed to the root logger or any other ancestor logger
    logger.propagate = False

    # Remove all handlers associated with the logger object.
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create a file handler
    Path("src/web/logs/").mkdir(parents=True, exist_ok=True)

    handler = logging.FileHandler("src/web/logs/agent.txt")
    handler.setLevel(logging.INFO)

    # Add the handlers to the logger
    logger.addHandler(handler)

    return logger


agent_logger = get_agent_logger()
