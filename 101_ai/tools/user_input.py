from colorama import Fore
from langchain.agents import Tool

from ..utils.formatting import print_to_console
from . import AgentTool


class UserInputTool(Tool):
    def __init__(self):
        super().__init__(
            name=AgentTool.AskUserQuestion.value,
            func=self.get_user_input,
            description="Get an answer from the user to a question. Questions should be simple and not require multiple answers, otherwise they should be split into multiple questions."
        )
    
    @staticmethod
    def get_user_input(question):
        print_to_console("\nQuestion", Fore.MAGENTA, question)
        i = input()
        return i
