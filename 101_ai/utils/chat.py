from typing import List

from langchain import LLMChain, PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.schema import BaseMessage

from .models import ChatModel
from .spinner import Spinner


def get_chat_completion(
    messages: list[BaseMessage], model: ChatModel, loading_text="🤔 Thinking... "
) -> str:
    with Spinner(loading_text):
        chat = ChatOpenAI(model=model.value, temperature=0)
        response = chat(messages)

    return response.content
