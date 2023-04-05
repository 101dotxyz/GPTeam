from typing import List

from langchain import LLMChain, PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.schema import BaseMessage

from .models import ChatModel


async def get_chat_completion(messages: list[BaseMessage], model: ChatModel):
   chat = ChatOpenAI(model=model.value)
   response = chat(messages)

   return response.content
    

    