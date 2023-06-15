import json
import os

def load_config():
    with open("metaconfig.json") as f:
        return json.load(f)

config = load_config()
