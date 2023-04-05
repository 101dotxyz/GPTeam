from langchain.tools.base import BaseTool
from langchain.agents import AgentType
from langchain.agents import initialize_agent
from langchain.utilities import SerpAPIWrapper
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.agents import Tool
import os
from typing import Callable

from pydantic import Field
os.environ["LANGCHAIN_HANDLER"] = "langchain"


def _print_func(text: str) -> None:
    print("\n")
    print(text)


class HumanInputRun(BaseTool):
    """Tool that adds the capability to ask user for input."""

    name = "Human"
    description = (
        "You can ask a human for guidance when you think you "
        "got stuck or you are not sure what to do next. "
        "The input should be a question for the human."
    )
    prompt_func: Callable[[str], None] = Field(
        default_factory=lambda: _print_func)
    input_func: Callable = Field(default_factory=lambda: input)

    def _run(self, query: str) -> str:
        """Use the Human input tool."""
        self.prompt_func(query)
        return self.input_func()

    async def _arun(self, query: str) -> str:
        """Use the Human tool asynchronously."""
        raise NotImplementedError("Human tool does not support async")


PREFIX = """Assistant is an engineering manager for a software development team. Assistant's job is to translate high-level app concepts, given by users, into a well-defined technical specification for a developer to implement. 

For each app concept, Assistant should start by asking clarifying questions of the user so that a developer can implement the idea with zero additional guidance or outside resources. 

The developer will be writing their implementation in typescript. They will not have access to any paid API services. If the app requires one, ask the user for an API key.

The final output should loosely follow this structure:
---
BACKEND ENDPOINTS: 
- list of endpoints and corresponding detailed pseudocode for the backend web-server that will be triggered by cron tasks or frontend interactions

TABLES:
- list of database tables with schema for each table

CRON JOBS:
- list of necessary cron jobs and which functions they call

ENV VARIABLES:
- list all necessary environment variables

FRONTEND:
- list of necessary frontend components
---

Do not write your specification without first echoing your understanding of the task back to the user, and receiving a confirmation."""


search = SerpAPIWrapper()
tools = [
    Tool(
        name="Current Search",
        func=search.run,
        description="useful for when you need to answer questions about current events or the current state of the world. the input to this should be a single search term."
    ),
    HumanInputRun(),
]

memory = ConversationBufferMemory(
    memory_key="chat_history", return_messages=True)
llm = ChatOpenAI(temperature=0.7, model_name="gpt-4", max_tokens=2048)
agent_chain = initialize_agent(
    tools, llm, agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION, verbose=True, memory=memory, agent_kwargs={'system_message': PREFIX})
print(agent_chain.run(input="hi I want to build a tool that will take the top 5 news stories and send them to my email every morning."))
