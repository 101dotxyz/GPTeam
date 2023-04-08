from enum import Enum

from langchain.agents import Tool

from . import AgentTool
from .evaluate_code import EvaluateCodeTool
from .improve_code import ImproveCodeTool
from .missing_information import MissingInformationTool
from .search import SearchTool
from .user_input import UserInputTool

tool_classes: dict[AgentTool, Tool] = {
    AgentTool.Search: SearchTool,
    AgentTool.AskUserQuestion: UserInputTool,
    AgentTool.EvaluateCode: EvaluateCodeTool,
    AgentTool.ImproveCode: ImproveCodeTool,
    AgentTool.MissingInformation: MissingInformationTool
}


def get_tools(agent_tools: list[AgentTool] = None) -> list[Tool]:

    if agent_tools is None:
        agent_tools = [tool for tool in AgentTool]

    return [tool_classes[tool]() for tool in agent_tools]