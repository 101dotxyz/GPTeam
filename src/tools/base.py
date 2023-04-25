from typing import Any, List, Optional
from langchain import GoogleSearchAPIWrapper
from langchain.agents import Tool, load_tools
from langchain.llms import OpenAI
from langchain.tools import BaseTool
from typing_extensions import override


from .send_message import send_message
from .directory import consult_directory
from src.tools.context import ToolContext


class CustomTool(Tool):
    requires_context: Optional[bool] = False

    def __init__(
        self,
        name: str,
        func,
        description: str,
        requires_context: Optional[bool],
        **kwargs: Any,
    ):
        super().__init__(name, func, description, **kwargs)
        self.requires_context = requires_context

    @override
    def run(self, agent_input: str | dict, tool_context: ToolContext) -> List[BaseTool]:

        # if the tool requires context
        if self.requires_context:
            input = {
                "agent_input": str(agent_input),
                "tool_context": tool_context
            }

        else:
            input = str(agent_input)

        return super().run(input)


custom_tools: List[CustomTool] = [
    CustomTool(
        name="search",
        func=GoogleSearchAPIWrapper().run,
        description="useful for when you need to search for information you do not know. the input to this should be a single search term.",
        requires_context=False,
    ),
    CustomTool(
        name="speak",
        func=send_message,
        description="Useful for when you need to speak to someone at your location. The input to this should be a single message, always starting by addressing the person you are speaking to. Ex: 'Hey Jim, can you get me last month's sales report?'",
        requires_context=True,  # this tool requires events_manager as context
    ),
    CustomTool(
        name="directory",
        func=consult_directory,
        description="A directory of all the people you can speak with, detailing their full names, roles, and current locations. Useful for when you need help from another person.",
        requires_context=True,  # this tool requires location_id as context
    )
]

built_in_tools: List[BaseTool] = load_tools(
    tool_names=["wolfram-alpha", "human"], llm=OpenAI()
)

custom_built_in_tools = []
for tool in built_in_tools:
    custom_tool = CustomTool(
        name=tool.name,
        func=tool.run,
        description=tool.description,
        args_schema=tool.args_schema,
        requires_context=False,
    )
    custom_built_in_tools.append(custom_tool)


all_tools = custom_tools + custom_built_in_tools
