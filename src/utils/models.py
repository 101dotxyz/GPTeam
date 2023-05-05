from enum import Enum

from dotenv import load_dotenv
from langchain.chat_models import ChatAnthropic, ChatOpenAI
from langchain.chat_models.base import BaseChatModel
from langchain.llms import OpenAI
from langchain.schema import BaseMessage

from .cache import chat_json_cache, json_cache
from .model_name import ChatModelName
from .parameters import DEFAULT_FAST_MODEL, DEFAULT_SMART_MODEL
from .spinner import Spinner

load_dotenv()


def get_chat_model(name: ChatModelName, **kwargs) -> BaseChatModel:
    if "model_name" in kwargs:
        del kwargs["model_name"]
    if "model" in kwargs:
        del kwargs["model"]

    if name == ChatModelName.TURBO:
        return ChatOpenAI(model_name=name.value, **kwargs)
    elif name == ChatModelName.GPT4:
        return ChatOpenAI(model_name=name.value, **kwargs)
    elif name == ChatModelName.CLAUDE:
        return ChatAnthropic(model=name.value, **kwargs)
    else:
        raise ValueError(f"Invalid model name: {name}")


class ChatModel:
    """Wrapper around the ChatModel class."""
    defaultModel: BaseChatModel
    backupModel: BaseChatModel

    def __init__(
        self,
        default_model_name: ChatModelName = DEFAULT_SMART_MODEL,
        backup_model_name: ChatModelName = DEFAULT_FAST_MODEL,
        **kwargs,
    ):
        self.defaultModel = get_chat_model(default_model_name, **kwargs)
        self.backupModel = get_chat_model(backup_model_name, **kwargs)

    @chat_json_cache(sleep_range=(0, 0))
    async def get_chat_completion(self, messages: list[BaseMessage], **kwargs) -> str:
        try:
            resp = await self.defaultModel.agenerate([messages])
        except Exception:
            resp = await self.backupModel.agenerate([messages])

        return resp.generations[0][0].text

    def get_chat_completion_sync(self, messages: list[BaseMessage], **kwargs) -> str:
        try:
            resp = self.defaultModel.generate([messages])
        except Exception:
            resp = self.backupModel.generate([messages])

        return resp.generations[0][0].text
