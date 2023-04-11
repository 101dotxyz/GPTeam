import asyncio
from typing import Optional

from colorama import Fore, Style, init
from dotenv import load_dotenv
from langchain.schema import (AIMessage, BaseMessage, HumanMessage,
                              SystemMessage)

from .parsers.task_definition_parser import (TaskDefinition,
                                             get_task_definition_parser)
from .utils.chat import get_chat_completion
from .utils.formatting import print_to_console
from .utils.models import ChatModel
from .utils.spinner import Spinner

load_dotenv()

# Used to avoid spamming the API in case things go wrong.
MAX_ITERATIONS = 20

async def main():
    init()
    print_to_console("Introduction", Fore.BLUE, "\nHi there 👋\n\nI'm Lixir, your AI programming assistant. Together we will create an application without writing a single line of code!\n\nLet's get started.\n")
    print_to_console("Question", Fore.GREEN, "What are we building today?")
    task_description = "A Gmail bot that sends a daily email with a summary of the user's unread emails."
    print_to_console("Answer", Fore.CYAN, task_description)

    parser = get_task_definition_parser()


    system_message = SystemMessage(content=f"You are a engineering manager for a software development team. Your job is to translate high-level app concepts, given by users, into a well-defined technical specification for a developer to implement.\n\nYou should start by asking clarifying questions of the user so that a developer can implement the idea with zero additional guidance or outside resources. When asking questions, you should do so one at a time.\n\nThe developer will be writing their implementation in typescript. They will not have access to any paid API services. If the app requires one, ask the user for an API key. \n\n Once you are ready to give a specification, your final answer should be formatted according to the following rules: {parser.get_format_instructions()}")

    human_message = HumanMessage(content=f"Here is my new app concept: {task_description}")

    messages: list[BaseMessage] = [system_message, human_message]

    result: Optional[TaskDefinition] = None

    i = 0

    for i in range(MAX_ITERATIONS):
        with Spinner("Thinking... "):
            response = get_chat_completion(messages, ChatModel.TURBO)
            messages.append(AIMessage(content=response))

            if "backend_endpoints" in response:
                print(f"Answer: {response}")
                result = parser.parse(response)
                break

        print_to_console("Question", Fore.GREEN, response)
        human_response = input("Answer: ")
        human_message = HumanMessage(content=human_response)
        messages.append(human_message)
        i += 1

    if not result:
        print_to_console("Max iterations reached", Fore.RED, f"I reached the maximum number of allowed iterations ({MAX_ITERATIONS}) and gave up trying.")
        return

    print_to_console("Task Specification", Fore.MAGENTA, f"Here's what I came up with: {result}")
    

asyncio.run(main())