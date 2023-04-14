from langchain.chat_models import ChatOpenAI
from langchain.schema import AIMessage, BaseMessage, HumanMessage, SystemMessage

from .cache import json_cache
from .models import ChatModel
from .spinner import Spinner


@json_cache(sleep_range=(0.4, 0.8))
def get_chat_completion(
    messages: list[BaseMessage], model: ChatModel, loading_text="🤔 Thinking... "
):
    with Spinner(loading_text):
        chat = ChatOpenAI(model=model.value, temperature=0)
        response = chat(messages)

    return response.content
