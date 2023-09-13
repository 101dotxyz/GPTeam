from enum import Enum
from litellm import BudgetManager
from dotenv import load_dotenv
from langchain.chat_models import ChatAnthropic, ChatOpenAI
from langchain.chat_models.base import BaseChatModel
from langchain.llms import OpenAI
from langchain.schema import BaseMessage
from utils.windowai_model import ChatWindowAI

from .cache import chat_json_cache, json_cache
from .model_name import ChatModelName
from .parameters import DEFAULT_FAST_MODEL, DEFAULT_SMART_MODEL
from .spinner import Spinner

load_dotenv()

budget_manager = BudgetManager(project_name="test_project")
user = "12345"
budget_manager.create_budget(total_budget=10, user=user, duration="daily")


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
    elif name == ChatModelName.CLAUDE_INSTANT:
        return ChatAnthropic(model=name.value, **kwargs)
    elif name == ChatModelName.WINDOW:
        return ChatWindowAI(model_name=name.value, **kwargs)
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
        self.default_model_name = default_model_name
        self.backup_model_name = backup_model_name
        self.defaultModel = get_chat_model(default_model_name, **kwargs)
        self.backupModel = get_chat_model(backup_model_name, **kwargs)

    @chat_json_cache(sleep_range=(0, 0))
    async def get_chat_completion(self, messages: list[BaseMessage], **kwargs) -> str:
        # check if a given call can be made
        if budget_manager.get_current_cost(user=user) <= budget_manager.get_total_budget(user):
            input_text = "".join(message["content"] for message in messages)
            model_used = ""
            try:
                model_used = self.default_model_name
                resp = await self.defaultModel.agenerate([messages])
            except Exception:
                model_used = self.backup_model_name
                resp = await self.backupModel.agenerate([messages])

            response = resp.generations[0][0].text
            budget_manager.update_cost(user=user, model=model_name, input_text=input_text, output_text=response)

            return response
        else:
            raise Exception("User budget limit exceeded")

    def get_chat_completion_sync(self, messages: list[BaseMessage], **kwargs) -> str:
        # check if a given call can be made
        if budget_manager.get_current_cost(user=user) <= budget_manager.get_total_budget(user):
            input_text = "".join(message["content"] for message in messages)
            model_used = ""
            try:
                model_used = self.default_model_name
                resp = self.defaultModel.generate([messages])
            except Exception:
                model_used = self.backup_model_name
                resp = self.backupModel.generate([messages])

            response = resp.generations[0][0].text
            budget_manager.update_cost(user=user, model=model_name, input_text=input_text, output_text=response)

            return response
        else:
            raise Exception("User budget limit exceeded")
