from typing import List

from langchain import LLMChain, PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.schema import BaseMessage

from .models import ChatModel


def get_chat_completion(messages: list[BaseMessage], model: ChatModel) -> str:
    chat = ChatOpenAI(model=model.value, temperature=0.6)
    response = chat(messages)

    return response.content
