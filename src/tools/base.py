from typing import List

from langchain import GoogleSearchAPIWrapper
from langchain.agents import Tool, load_tools
from langchain.llms import OpenAI
from langchain.tools import BaseTool

custom_tools: List[BaseTool] = [
    Tool(
        name="search",
        func=GoogleSearchAPIWrapper().run,
        description="useful for when you need to search for information you do not know. the input to this should be a single search term.",
    )
]

built_in_tools: List[BaseTool] = load_tools(
    tool_names=["wolfram-alpha", "human"], llm=OpenAI()
)

all_tools = custom_tools + built_in_tools
