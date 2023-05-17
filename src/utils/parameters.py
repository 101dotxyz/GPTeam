# Environment
import os
import sys
from enum import Enum

from .config import load_config
from .model_name import ChatModelName

config = load_config()


TIME_SPEED_MULTIPLIER = 1000
# Memory
RECENCY_WEIGHT = 1
SIMILARITY_WEIGHT = 1
IMPORTANCE_WEIGHT = 1
REFLECTION_MEMORY_COUNT = 50
PLAN_LENGTH = "24 hours"
DEFAULT_LOCATION_ID = config.default_location_id
DEFAULT_WORLD_ID = config.world_id
ANNOUNCER_DISCORD_TOKEN = os.getenv("ANNOUNCER_DISCORD_TOKEN")

DEFAULT_SMART_MODEL = (
    ChatModelName.TURBO if "--turbo" in sys.argv else ChatModelName.CLAUDE if "--claude" in sys.argv else ChatModelName.GPT4
)

DEFAULT_FAST_MODEL = (
     ChatModelName.CLAUDE_INSTANT if "--claude" in sys.argv else ChatModelName.TURBO
)


# Tools
DISCORD_ENABLED = (
    True
    if os.getenv("ANNOUNCER_DISCORD_TOKEN", None) is not None
    and len(os.getenv("ANNOUNCER_DISCORD_TOKEN")) > 0
    else False
)
