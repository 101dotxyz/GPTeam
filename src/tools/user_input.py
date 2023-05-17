from colorama import Fore
from langchain.agents import Tool

from ..utils.colors import LogColor
from ..utils.formatting import print_to_console


class UserInputTool(Tool):
    def __init__(self):
        super().__init__(
            name="Ask User A Question",
            func=self.get_user_input,
            description="Get an answer from the user to a question.",
        )

    @staticmethod
    def get_user_input(question):
        print_to_console("\nQuestion", LogColor.CLI_INPUT, question)
        i = input()
        return i
