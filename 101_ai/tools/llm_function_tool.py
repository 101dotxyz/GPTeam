import json
from abc import abstractmethod

from colorama import Fore
from langchain.agents import Tool
from langchain.schema import AIMessage, HumanMessage, SystemMessage

from ..utils.chat import get_chat_completion
from ..utils.formatting import print_to_console
from ..utils.models import ChatModel


class LLMFunctionTool(Tool):
    model: ChatModel
    function_definition: str
    function_description: str
    def __init__(self, name, definition, description, model=ChatModel.GPT4):
        super().__init__(
            name=name,
            func=self.get_llm_response,
            description=description
        )

        self.model = model

    def get_llm_response(self, args: str) -> str:
        
        system_message = SystemMessage(content=f"You are now the following Python function: ```# {self.function_description}\n{self.function_definition}```\n\nOnly respond with your `return` value.")
        human_message = HumanMessage(content=f"{args}")

        
        response = get_chat_completion([system_message, human_message], self.model)
        
        return response

    
    

