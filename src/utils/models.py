from enum import Enum

from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI
from langchain.llms import OpenAI
from langchain.schema import BaseMessage

from .cache import json_cache
from .spinner import Spinner

load_dotenv()


class ChatModelName(Enum):
    TURBO = "gpt-3.5-turbo"
    GPT4 = "gpt-4"


class ChatModel(ChatOpenAI):
    def __init__(self, model_name: ChatModelName, **kwargs):
        super().__init__(model_name=model_name.value, **kwargs)

    @json_cache(sleep_range=(0, 0))
    def get_chat_completion(self, messages: list[BaseMessage], **kwargs) -> str:
        with Spinner(kwargs.get("loading_text", "🤔 Thinking... ")):
            resp = super().generate([messages])

        return resp.generations[0][0].text


class CompletionModel(OpenAI):
    def __init__(self, model_name: str, **kwargs):
        super().__init__(model_name=model_name, **kwargs)


def get_chat_model(model_name: ChatModelName, **kwargs) -> ChatModel:
    kwargs.setdefault("temperature", 0)
    return ChatModel(model_name, **kwargs)
