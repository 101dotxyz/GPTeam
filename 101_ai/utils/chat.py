from typing import List

from langchain import LLMChain, PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.schema import BaseMessage

from .models import ChatModel
from .spinner import Spinner


def get_chat_completion(messages: list[BaseMessage], model: ChatModel) -> str:
    with Spinner("🤔 Thinking... "):
        chat = ChatOpenAI(model=model.value, temperature=0)
        response = chat(messages)

    return response.content
