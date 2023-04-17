import json
import os
import random
import time
from functools import wraps

from .spinner import Spinner

CACHE_FILE = "cache.json"


def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)


def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {}


cache = load_cache()


def json_cache(sleep_range=(0, 0)):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            x, y = sleep_range
            sleep_seconds = random.uniform(x, y)
            loading_text = kwargs.get("loading_text", "🤔 Thinking... ")
            with Spinner(loading_text):
                time.sleep(sleep_seconds)
            key = f"{func.__name__}_{args}_{kwargs}"
            if key in cache:
                return cache[key]
            result = func(*args, **kwargs)
            cache[key] = result
            save_cache(cache)
            return result

        return wrapper

    return decorator
