import enum
from enum import Enum
from typing import Any, List, Optional

from langchain import GoogleSearchAPIWrapper
from langchain.agents import Tool, load_tools
from langchain.llms import OpenAI
from langchain.tools import BaseTool
from typing_extensions import override

from src.tools.company_directory import look_up_company_directory
from src.tools.context import ToolContext
from src.utils.prompt import PromptString

from .directory import consult_directory
from .name import ToolName
from .send_message import send_message


class CustomTool(Tool):
    requires_context: Optional[bool] = False
    requires_authorization: bool = False
    worldwide: bool = True
    summarize: Optional[PromptString] = None

    def __init__(
        self,
        name: str,
        func,
        description: str,
        requires_context: Optional[bool],
        worldwide: bool,
        requires_authorization: bool,
        summarize: Optional[PromptString] = None,
        **kwargs: Any,
    ):
        super().__init__(name, func, description, **kwargs)

        self.requires_context = requires_context
        self.requires_authorization = requires_authorization
        self.worldwide = worldwide
        self.summarize = summarize

    @override
    def run(self, agent_input: str | dict, tool_context: ToolContext) -> List[BaseTool]:
        # if the tool requires context
        if self.requires_context:
            input = {"agent_input": str(agent_input), "tool_context": tool_context}

        else:
            input = str(agent_input)

        return super().run(input)


def load_built_in_tool(
    tool: str,
    worldwide=True,
    requires_authorization=False,
    summarize: Optional[PromptString] = None,
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
        summarize=summarize,
        requires_context=False,
    )


TOOLS: dict[ToolName, CustomTool] = {
    ToolName.SEARCH: CustomTool(
        name="search",
        func=GoogleSearchAPIWrapper().run,
        description="useful for when you need to search for information you do not know. the input to this should be a single search term.",
        summarize="You have just searched Google with the following search input: {tool_input} and got the following result {tool_result}. Write a single sentence with useful information to share with others in your location about how the result can help you accomplish your plan: {plan_description}.",
        requires_context=False,
        requires_authorization=False,
        worldwide=True,
    ),
    ToolName.SPEAK: CustomTool(
        name="speak",
        func=send_message,
        description="useful for when you need to speak to someone at your location. the input to this should be a single message, including the name of the person you want to speak to. e.g. David Summers: Do you know the printing code?",
        summarize="You have just said {tool_input}. Write a single sentence with useful information to share with others in your location about how the result can help you accomplish your plan: {plan_description}.",
        requires_context=True,
        requires_authorization=False,
        worldwide=True,
    ),
    ToolName.WOLFRAM_APLHA: load_built_in_tool(
        "wolfram-alpha", requires_authorization=False, worldwide=True
    ),
    ToolName.HUMAN: load_built_in_tool(
        "human",
        summarize="You have just asked a human for help by saying {tool_input}. This is what they replied: {tool_result}. Write a single sentence with useful information to share with others in your location about how the result can help you accomplish your plan: {plan_description}.",
        requires_authorization=False,
        worldwide=True,
    ),
    ToolName.COMPANY_DIRECTORY: CustomTool(
        name=ToolName.COMPANY_DIRECTORY.value,
        func=consult_directory,
        description="A directory of all the people you can speak with, detailing their full names, roles, and current locations. Useful for when you need find out information about other people working at the company.",
        summarize="You have just consulted the company directory and found out the following: {tool_result}. Write a single sentence with useful information to share with others in your location about how what you found out from the company directory can help you accomplish your plan: {plan_description}.",
        requires_context=True,  # this tool requires location_id as context
        requires_authorization=False,
        worldwide=True,
    ),
}


def get_tools(tools: List[ToolName], include_worldwide=False) -> List[CustomTool]:
    if not include_worldwide:
        return [TOOLS[tool] for tool in tools]

    return [tool for tool in TOOLS.values() if (tool.name in tools or tool.worldwide)]
