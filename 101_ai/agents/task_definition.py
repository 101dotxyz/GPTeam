"""An agent designed to hold a conversation in addition to using tools."""
from __future__ import annotations

import json
from typing import Any, List, Optional, Sequence, Tuple, Union

from langchain import SerpAPIWrapper
from langchain.agents import AgentExecutor, ConversationalChatAgent, Tool
from langchain.agents.agent import Agent
from langchain.agents.conversational_chat.prompt import (
    FORMAT_INSTRUCTIONS, PREFIX, SUFFIX, TEMPLATE_TOOL_RESPONSE)
from langchain.callbacks.base import BaseCallbackManager
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.prompts.base import BasePromptTemplate
from langchain.prompts.chat import (ChatPromptTemplate,
                                    HumanMessagePromptTemplate,
                                    MessagesPlaceholder,
                                    SystemMessagePromptTemplate)
from langchain.schema import (AgentAction, AgentFinish, AIMessage,
                              BaseLanguageModel, BaseMessage, BaseOutputParser,
                              HumanMessage)
from langchain.tools.base import BaseTool

from ..tools.user_input import UserInputTool
from ..utils.input import get_user_input


class AgentOutputParser(BaseOutputParser):
    def get_format_instructions(self) -> str:
        return FORMAT_INSTRUCTIONS

    def parse(self, text: str) -> Any:
        cleaned_output = text.strip()
        if "```json" in cleaned_output:
            _, cleaned_output = cleaned_output.split("```json")
        if "```" in cleaned_output:
            cleaned_output, _ = cleaned_output.split("```")
        if cleaned_output.startswith("```json"):
            cleaned_output = cleaned_output[len("```json") :]
        if cleaned_output.startswith("```"):
            cleaned_output = cleaned_output[len("```") :]
        if cleaned_output.endswith("```"):
            cleaned_output = cleaned_output[: -len("```")]
        cleaned_output = cleaned_output.strip()
        response = json.loads(cleaned_output)
        return {"action": response["action"], "action_input": response["action_input"]}


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


def get_task_definition_agent():
    search = SerpAPIWrapper()

    tools = [
        Tool(
            name = "Search",
            func=search.run,
            description="Allows you to search the web. Input is a query. Output is a list of results."
        ),
        UserInputTool()
    ]

    # tools = load_tools(["human"])

    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    
    llm=ChatOpenAI(temperature=0)

    agent = TaskDefinitionAgent.from_llm_and_tools(llm=llm, tools=tools, verbose=True)

    agent_chain = AgentExecutor.from_agent_and_tools(agent=agent, tools=tools, verbose=True, memory=memory)

    return agent_chain