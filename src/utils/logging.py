import atexit
import json
import logging
import os
import re
from datetime import datetime
from typing import List

import pytz
from json_log_formatter import JSONFormatter


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


class LLMRequestFilter(logging.Filter):
    def filter(self, record):
        return "processing_ms=" not in record.message


class CustomJsonFormatter(JSONFormatter):
    def json_record(self, message, extra, record):
        json_data = super().json_record(message, extra, record)

        message_dict = {}

        matches = get_completion_data(json_data["message"])
        if len(matches) == 3:
            for match in matches:
                key = match.split("=")[0]
                value = match.split("=")[1]

                # Remove initial and ending quote marks, if they exist
                if value[0] in ("'", '"') and value[-1] in ("'", '"'):
                    value = value[1:-1]

                cleaned = clean_json_string(value)

                try:
                    value = json.loads(cleaned)
                except:
                    value = value

                message_dict[key] = value

        json_data["message"] = message_dict

        return json_data


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


def set_up_logging():
    # Set up logging to a file
    logger = logging.getLogger()
    # set path to be this current directory
    timestamp = datetime.now(pytz.utc).strftime("%H-%M__%m-%d-%y")
    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        f"logs/{timestamp}_logs.json",
    )
    file_handler = JsonArrayFileHandler(path)
    file_handler.setLevel(logging.DEBUG)
    file_handler.addFilter(OpenAIFilter())

    # Add the custom JSON formatter to the file handler
    formatter = CustomJsonFormatter()
    # formatter = JSONFormatter()
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    # Set minimum logging level for langchain.llms to avoid info messages about API response times
    logger.addFilter(LLMRequestFilter())
