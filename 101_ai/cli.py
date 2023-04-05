import asyncio

from colorama import Fore, Style, init
from dotenv import load_dotenv
from langchain.schema import HumanMessage

from .utils.chat import get_chat_completion
from .utils.formatting import print_to_console
from .utils.models import ChatModel
from .utils.prompts.task_specification import \
    TASK_SPECIFICATION_CHAT_PROMPT_TEMPLATE

load_dotenv()


async def main():
    init()
    print_to_console("Introduction", Fore.BLUE, "\nHi there 👋\n\nI'm Lixir, your AI programming assistant. Together we will create an application without writing a single line of code!\n\nLet's get started.\n")
    print_to_console("Question", Fore.GREEN, "What are we building today?")
    task_description = input()
    print_to_console("Question", Fore.GREEN, "Got it. What shall we call this app?")
    app_name = input()

    messages = TASK_SPECIFICATION_CHAT_PROMPT_TEMPLATE.format_prompt(task_description=task_description).to_messages()
    result = await get_chat_completion(messages, ChatModel.GPT4)

    print_to_console("Task Specification", Fore.MAGENTA, f"Here's what I came up with: {result}")

    

asyncio.run(main())