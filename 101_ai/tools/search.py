from colorama import Fore
from langchain.agents import Tool

from ..utils.formatting import print_to_console


class SearchTool(Tool):
    def __init__(self):
        super().__init__(
            name="Current Search",
            func=search.run,
            description="useful for when you need to answer questions about current events or the current state of the world. the input to this should be a single search term."
        )
    
    @staticmethod
    def get_user_input(question):
        print_to_console("\nQuestion", Fore.MAGENTA, question)
        i = input()
        return i
