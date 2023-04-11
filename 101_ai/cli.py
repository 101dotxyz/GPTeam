import asyncio

from colorama import Fore, Style, init
from dotenv import load_dotenv
from langchain.agents import Agent, AgentExecutor
from langchain.memory import ConversationBufferMemory
from langchain.schema import HumanMessage

from .agents.task_definition import get_task_definition_agent
from .tools.main import get_tools
from .utils.formatting import print_to_console
from .utils.prompts.task_definition import TASK_DEFINITION_CHAT_PROMPT_TEMPLATE

load_dotenv()


async def main():
    init()
    print_to_console("Introduction", Fore.BLUE, "\nHi there 👋\n\nI'm Lixir, your AI programming assistant. Together we will create an application without writing a single line of code!\n\nLet's get started.\n")
    # print_to_console("Question", Fore.GREEN, "What are we building today?")
    # task_description = input()
    # # print_to_console("Question", Fore.GREEN, "Got it. What shall we call this app?")
    # # app_name = input()

    # messages = TASK_DEFINITION_CHAT_PROMPT_TEMPLATE.format_prompt(task_description=task_description).to_messages()

    # message_input = ', '.join([str(message) for message in messages])

    # print(message_input)

    memory = ConversationBufferMemory()
    agent: Agent = get_task_definition_agent()

    agent_executor = AgentExecutor(agent=agent, memory=ConversationBufferMemory(), tools=get_tools())
    

    agent_executor.run(input="Write a function that takes in a number and returns the number squared.")

    # result = await get_chat_completion(messages, ChatModel.GPT4)

    # print_to_console("Task Specification", Fore.MAGENTA, f"Here's what I came up with: {result}")

    

asyncio.run(main())