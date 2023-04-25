import enum
from typing import Any, List, Optional

from langchain import GoogleSearchAPIWrapper
from langchain.agents import Tool, load_tools
from langchain.llms import OpenAI
from langchain.tools import BaseTool
from typing_extensions import override

from .name import ToolName
from .send_message import send_message


class CustomTool(Tool):
    requires_context: Optional[bool] = False
    requires_authorization: bool = False
    worldwide: bool = True

    def __init__(
        self,
        name: str,
        func,
        description: str,
        requires_context: Optional[bool],
        worldwide: bool,
        requires_authorization: bool,
        **kwargs: Any,
    ):
        super().__init__(name, func, description, **kwargs)

        self.requires_context = requires_context
        self.requires_authorization = requires_authorization
        self.worldwide = worldwide

    @override
    def run(self, agent_input: str | dict, system_context: dict = {}) -> List[BaseTool]:
        # if the tool requires context, but none is provided, raise an error
        if self.requires_context and not bool(system_context):
            raise Exception(
                f"tool {self.name} requires system_context, but none was provided"
            )

        # if the tool requires context
        if self.requires_context:
            # Combine the agent input and context into a dict
            if isinstance(agent_input, str):
                agent_input = {"agent_input": agent_input}
            input = {**agent_input, **system_context}

        else:
            input = str(agent_input)

        # Run the Tool with the combined input
        return super().run(input)


def load_built_in_tool(
    tool: str, worldwide=True, requires_authorization=False
) -> CustomTool:
    tools = load_tools(tool_names=[tool], llm=OpenAI())

    tool = tools[0]

    return CustomTool(
        name=tool.name,
        func=tool.run,
        description=tool.description,
        worldwide=worldwide,
        requires_authorization=requires_authorization,
        args_schema=tool.args_schema,
        requires_context=False,
    )


TOOLS: dict[ToolName, CustomTool] = {
    ToolName.SEARCH: CustomTool(
        name="search",
        func=GoogleSearchAPIWrapper().run,
        description="useful for when you need to search for information you do not know. the input to this should be a single search term.",
        requires_context=False,
        requires_authorization=False,
        worldwide=True,
    ),
    ToolName.SPEAK: CustomTool(
        name="speak",
        func=send_message,
        description="useful for when you need to speak to someone at your location. the input to this should be a single message, including the name of the person you want to speak to. e.g. David Summers: Do you know the printing code?",
        requires_context=True,  # this tool requires events_manager as context
        requires_authorization=False,
        worldwide=True,
    ),
    ToolName.WOLFRAM_APLHA: load_built_in_tool(
        "wolfram-alpha", requires_authorization=False, worldwide=True
    ),
    ToolName.HUMAN: load_built_in_tool(
        "human", requires_authorization=False, worldwide=True
    ),
}


def get_tools(tools: List[ToolName], include_worldwide=False) -> List[CustomTool]:
    if not include_worldwide:
        return [TOOLS[tool] for tool in tools]

    return [tool for tool in TOOLS.values() if (tool.name in tools or tool.worldwide)]
