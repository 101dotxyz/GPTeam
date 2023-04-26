import enum
from typing import Any, List, Optional
from uuid import UUID

from langchain import GoogleSearchAPIWrapper
from langchain.agents import Tool, load_tools
from langchain.llms import OpenAI
from langchain.tools import BaseTool
from typing_extensions import override

from src.tools.company_directory import look_up_company_directory
from src.tools.context import ToolContext
from src.world.context import WorldContext

from .directory import consult_directory
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
    def run(self, agent_input: str | dict, tool_context: ToolContext) -> List[BaseTool]:
        # if the tool requires context
        if self.requires_context:
            input = {"agent_input": str(agent_input), "tool_context": tool_context}

        else:
            input = str(agent_input)

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


def get_tools(
    tools: List[ToolName],
    context: WorldContext,
    agent_id: str | UUID,
    include_worldwide=False,
) -> List[CustomTool]:
    if isinstance(agent_id, str):
        agent_id = UUID(agent_id)

    location_id = context.get_agent_location_id(agent_id=agent_id)

    location_name = context.get_location_name(location_id=location_id)

    agents_at_location = context.get_agents_at_location(location_id=location_id)

    other_agents = [a for a in agents_at_location if a["id"] != agent_id]

    # names of other agents at location
    other_agent_names = ", ".join([a["full_name"] for a in other_agents])

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
            description=f"say something in the {location_name}. {other_agent_names} are also in the {location_name} and will hear what you say. You can say something to everyone, or address one of the other people at your location (one of {other_agent_names}). The input should be what you want to say. If you want to address someone, the input should be of the format full_name:message (e.g. David Summers:How are you doing today?).",
            requires_context=True,
            requires_authorization=False,
            worldwide=True,
        ),
        ToolName.PRIVATE_MESSAGE: CustomTool(
            name="private-message",
            func=send_message,
            description="privately message anyone in the company. The input should be of the form full_name:message (e.g. David Summers:How are you doing today?)",
            requires_context=True,
            requires_authorization=False,
            worldwide=True,
        ),
        ToolName.WOLFRAM_APLHA: load_built_in_tool(
            "wolfram-alpha", requires_authorization=False, worldwide=True
        ),
        ToolName.HUMAN: load_built_in_tool(
            "human", requires_authorization=False, worldwide=True
        ),
        ToolName.COMPANY_DIRECTORY: CustomTool(
            name=ToolName.COMPANY_DIRECTORY.value,
            func=consult_directory,
            description="A directory of all the people you can speak with, detailing their full names, roles, and current locations. Useful for when you need help from another person.",
            requires_context=True,  # this tool requires location_id as context
            requires_authorization=False,
            worldwide=True,
        ),
    }

    if not include_worldwide:
        return [TOOLS[tool] for tool in tools]

    return [tool for tool in TOOLS.values() if (tool.name in tools or tool.worldwide)]
