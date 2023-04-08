from colorama import Fore
from langchain.agents import Tool
from langchain.utilities import SerpAPIWrapper

from ..utils.formatting import print_to_console
from . import AgentTool


class SearchTool(Tool):
    def __init__(self):
        search = SerpAPIWrapper()
        super().__init__(
            name=AgentTool.Search.value,
            func=search.run,
            description="Useful when you need to find information online. The input to this should be a single search term."
        )

