from colorama import Fore
from langchain.agents import Tool
from langchain.schema import HumanMessage, SystemMessage

from ..utils.formatting import print_to_console
from ..utils.models import ChatModelName, ChatModel


class LLMFunctionTool(Tool):
    model_name: ChatModelName
    chat_llm: ChatModel
    function_definition: str
    function_description: str

    def __init__(self, name, definition, description, model_name=ChatModelName.GPT4):
        super().__init__(name=name, func=self.get_llm_response, description=description)

        self.model_name = model_name
        self.chat_llm = ChatModel(self.model_name)

    def get_llm_response(self, args: str) -> str:
        system_message = SystemMessage(
            content=f"You are now the following Python function: ```# {self.function_description}\n{self.function_definition}```\n\nOnly respond with your `return` value."
        )
        human_message = HumanMessage(content=f"{args}")

        response = self.chat_llm.get_chat_completion([system_message, human_message]) 

        return response
