import json
from abc import abstractmethod
from typing import Any

from colorama import Fore
from langchain.agents import Tool
from langchain.schema import AIMessage, HumanMessage, SystemMessage

from ..utils.chat import get_chat_completion
from ..utils.formatting import print_to_console
from ..utils.models import ChatModel


class LLMFunctionTool(Tool):
    def __init__(self, name, definition, description, model=ChatModel.GPT4):

        def get_llm_response(args: dict[str, Any]):
            system_message = SystemMessage(content=f"You are now the following Python function: ```# {description}\n{definition}```\n\nOnly respond with your `return` value.")
            human_message = HumanMessage(content=f"{json.dumps(args)}")

            response = get_chat_completion([system_message, human_message], model)

            return response

        super().__init__(
            name=name,
            func=get_llm_response,
            description=description
        )

    
    

