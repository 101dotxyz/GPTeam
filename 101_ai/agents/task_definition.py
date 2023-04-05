import os

from colorama import Fore
from langchain.agents import AgentType, Tool, initialize_agent, load_tools
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.utilities import SerpAPIWrapper

from ..tools.user_input import UserInputTool


def get_task_specification_agent():
    search = SerpAPIWrapper()

    tools = [
        Tool(
            name = "Current Search",
            func=search.run,
            description="useful for when you need to answer questions about current events or the current state of the world. the input to this should be a single search term."
        ),
        UserInputTool()
    ]

    # tools = load_tools(["human"])

    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    llm=ChatOpenAI(temperature=0)
    agent_chain = initialize_agent(tools, llm, agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION, verbose=True, memory=memory)
    return agent_chain