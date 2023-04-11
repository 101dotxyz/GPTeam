"""An agent designed to hold a conversation in addition to using tools."""
from __future__ import annotations

import json
import re
from typing import Any, List, Tuple, Union

from langchain.agents import (BaseMultiActionAgent, ConversationalChatAgent,
                              Tool)
from langchain.agents.agent import Agent, AgentOutputParser
from langchain.agents.conversational_chat.prompt import FORMAT_INSTRUCTIONS
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.schema import AgentAction, AgentFinish

from ..tools import AgentTool
from ..tools.main import get_tools
from ..utils.prompts.task_definition import \
    TASK_DEFINITION_SYSTEM_PROMPT_TEMPLATE


class TaskDefinitionAgent(ConversationalChatAgent):
    def plan(
        self, intermediate_steps: List[Tuple[AgentAction, str]], **kwargs: Any
    ) -> Union[AgentAction, AgentFinish]:
        """Given input, decided what to do.

        Args:
            intermediate_steps: Steps the LLM has taken to date,
                along with observations
            **kwargs: User inputs.

        Returns:
            Action specifying what tool to use.
        """

        if len(intermediate_steps) > 0:
            [last_action, response] = intermediate_steps[-1]

            print("Last action:", last_action.tool)

            if last_action.tool == AgentTool.EvaluateCode.value:
                print("Agent has recently evaluated code and is suggesting we improve it.")
                return AgentAction(tool=AgentTool.ImproveCode.value, tool_input=f"[{response}, {last_action.tool_input}]", log="log here")
            

        suggested_action = super().plan(intermediate_steps, **kwargs)
        
        if isinstance(suggested_action, AgentFinish):
            print("Agent is suggesting we finish the conversation. Initiating reflection instead.")
        return suggested_action

    async def aplan(
        self, intermediate_steps: List[Tuple[AgentAction, str]], **kwargs: Any
    ) -> Union[AgentAction, AgentFinish]:
        """Given input, decided what to do.

        Args:
            intermediate_steps: Steps the LLM has taken to date,
                along with observations
            **kwargs: User inputs.

        Returns:
            Action specifying what tool to use.
        """
        return AgentAction(tool="Search", tool_input="foo", log="")


def get_task_definition_agent() -> Agent:

    tools = get_tools([AgentTool.AskUserQuestion, AgentTool.Search, AgentTool.MissingInformation])
    
    llm=ChatOpenAI(temperature=0)

    agent = TaskDefinitionAgent.from_llm_and_tools(llm=llm, tools=tools, verbose=True, system_message="You are a engineering manager for a software development team. Your job is to translate high-level app concepts, given by users, into a well-defined technical specification for a developer to implement.\n\nFor each app concept, you should start by asking clarifying questions of the user so that a developer can implement the idea with zero additional guidance or outside resources.\n\nThe developer will be writing their implementation in typescript. They will not have access to any paid API services. If the app requires one, ask the user for an API key.\n\nThe final output should loosely follow this structure:\n---\nBACKEND ENDPOINTS: \n- list of endpoints and corresponding detailed pseudocode for the backend web-server that will be triggered by cron tasks or frontend interactions\n\nTABLES:\n- list of database tables with schema for each table\n\nCRON JOBS:\n- list of necessary cron jobs and which functions they call\n\nENV VARIABLES:\n- list all necessary environment variables\n\nFRONTEND:\n- list of necessary frontend components\n---\n\nDo not write your specification without first echoing your understanding of the task back to the user, and receiving a confirmation.")

    return agent

class TaskDefinitionOutputParser(AgentOutputParser):
    
    def parse(self, llm_output: str) -> Union[AgentAction, AgentFinish]:
        # Check if agent should finish
        if "Final Answer:" in llm_output:
            return AgentFinish(
                # Return values is generally always a dictionary with a single `output` key
                # It is not recommended to try anything else at the moment :)
                return_values={"output": llm_output.split("Final Answer:")[-1].strip()},
                log=llm_output,
            )
        # Parse out the action and action input
        regex = r"Action: (.*?)[\n]*Action Input:[\s]*(.*)"
        match = re.search(regex, llm_output, re.DOTALL)
        if not match:
            raise ValueError(f"Could not parse LLM output: `{llm_output}`")
        action = match.group(1).strip()
        action_input = match.group(2)
        # Return the action and action input
        return AgentAction(tool=action, tool_input=action_input.strip(" ").strip('"'), log=llm_output)