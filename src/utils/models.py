from enum import Enum
from langchain.schema import BaseMessage
from langchain.chat_models import ChatOpenAI

from .cache import json_cache
from .spinner import Spinner
from .my_logging import set_up_logging
from dotenv import load_dotenv

# load env variables
load_dotenv()

# set up logging
set_up_logging()

class ChatModelName(Enum):
    TURBO = "gpt-3.5-turbo"
    GPT4 = "gpt-4"

class ChatModel(ChatOpenAI):
    def __init__(self, model_name: ChatModelName, **kwargs):
        super().__init__(model_name=model_name.value, **kwargs)

    @json_cache(sleep_range=(0.4, 1))
    def get_chat_completion(self, messages: list[BaseMessage], **kwargs) -> str:
        with Spinner(kwargs.get("loading_text", "🤔 Thinking... ")):
            resp = super().generate([messages])

        return resp.generations[0][0].text


def get_chat_model(model_name: ChatModelName, **kwargs) -> ChatModel:
    kwargs.setdefault('temperature', 0)
    return ChatModel(model_name, **kwargs)

