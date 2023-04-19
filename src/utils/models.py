from enum import Enum

from dotenv import load_dotenv
from langchain.chat_models import ChatAnthropic, ChatOpenAI
from langchain.chat_models.base import BaseChatModel
from langchain.llms import OpenAI
from langchain.schema import BaseMessage

from .cache import json_cache
from .spinner import Spinner

load_dotenv()


class ChatModelName(Enum):
    TURBO = "gpt-3.5-turbo"
    GPT4 = "gpt-4"
    CLAUDE = "claude-v1"


def get_chat_model(name: ChatModelName, **kwargs):
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


class ChatModel:
    def __init__(
        self,
        default_model_name: ChatModelName = ChatModelName.GPT4,
        backup_model_name: ChatModelName = ChatModelName.TURBO,
        **kwargs,
    ):
        self.defaultModel = get_chat_model(default_model_name, **kwargs)
        self.backupModel = get_chat_model(backup_model_name, **kwargs)

    @json_cache(sleep_range=(0, 0))
    def get_chat_completion(self, messages: list[BaseMessage], **kwargs) -> str:
        with Spinner(kwargs.get("loading_text", "🤔 Thinking... ")):
            try:
                resp = self.defaultModel.generate([messages])
            except Exception as e:
                print(f"Error with defaultModel: {e}")
                print("Trying with backupModel...")
                resp = self.backupModel.generate([messages])

        return resp.generations[0][0].text


class OpenAIChatModel(ChatOpenAI):
    def __init__(self, model_name: ChatModelName, **kwargs):
        super().__init__(model_name=model_name.value, **kwargs)

    @json_cache(sleep_range=(0, 0))
    def get_chat_completion(self, messages: list[BaseMessage], **kwargs) -> str:
        with Spinner(kwargs.get("loading_text", "🤔 Thinking... ")):
            resp = super().generate([messages])

        return resp.generations[0][0].text
