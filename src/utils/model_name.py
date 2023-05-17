from enum import Enum


class ChatModelName(Enum):
    TURBO = "gpt-3.5-turbo"
    GPT4 = "gpt-4"
    CLAUDE = "claude-v1"
    CLAUDE_INSTANT = "claude-instant-v1"
