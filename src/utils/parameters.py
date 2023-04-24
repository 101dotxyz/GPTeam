# Environment
import os

from .model_name import ChatModelName

TIME_SPEED_MULTIPLIER = 1000
# Memory
RECENCY_WEIGHT = 1
SIMILARITY_WEIGHT = 1
IMPORTANCE_WEIGHT = 1
REFLECTION_MEMORY_COUNT = 100
PLAN_LENGTH = "24 hours"
DEFAULT_LOCATION_ID = os.getenv("DEFAULT_LOCATION_ID")
WORLD_ID = os.getenv("WORLD")

DEFAULT_SMART_MODEL = (
    ChatModelName.TURBO
)  # Change to ChatModelName.GPT4 in production, this is just for testing
DEFAULT_FAST_MODEL = ChatModelName.TURBO
