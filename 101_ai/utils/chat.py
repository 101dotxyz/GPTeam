from langchain.chat_models import ChatOpenAI
from langchain.schema import (AIMessage, BaseMessage, HumanMessage,
                              SystemMessage)

from .cache import json_cache
from .models import ChatModel
from .spinner import Spinner


@json_cache(sleep_range=(0.4, 1))
def get_chat_completion(messages: list[BaseMessage], model: ChatModel, **kwargs):
    with Spinner(kwargs.get("loading_text", "🤔 Thinking... ")):
        chat = ChatOpenAI(model=model.value, temperature=0)
        response = chat(messages)

    return response.content
