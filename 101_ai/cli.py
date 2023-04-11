import asyncio
from typing import Optional

from colorama import Fore, Style, init
from dotenv import load_dotenv
from langchain.schema import (AIMessage, BaseMessage, HumanMessage,
                              SystemMessage)

from .parsers.task_definition_parser import (TaskDefinition,
                                             get_task_definition_parser)
from .prompts.task_definition import (TASK_DEFINITION_SYSTEM_PROMPT_TEMPLATE,
                                      task_definition_parser)
from .utils.chat import get_chat_completion
from .utils.formatting import print_to_console
from .utils.models import ChatModel

load_dotenv()

MAX_ITERATIONS = 5

async def main():
    init()
    print_to_console("Introduction", Fore.BLUE, "\nHi there 👋\n\nI'm Lixir, your AI programming assistant. Together we will create an application without writing a single line of code!\n\nLet's get started.\n")
    print_to_console("Question", Fore.GREEN, "What are we building today?")
    task_description = "A Gmail bot that sends a daily email with a summary of the user's unread emails."
    print_to_console("Answer", Fore.CYAN, task_description)


    system_message = SystemMessage(content=TASK_DEFINITION_SYSTEM_PROMPT_TEMPLATE.format().content)



    human_message = HumanMessage(content=f"Here is my new app concept: {task_description}")

    messages: list[BaseMessage] = [system_message, human_message]

    result: Optional[TaskDefinition] = None

    i = 0

    while not result or i < MAX_ITERATIONS:
        response = get_chat_completion(messages, ChatModel.TURBO)
        messages.append(AIMessage(content=response))
        try:
            if "backend_endpoints" in response:
                print(f"Answer: {response}")
                result = task_definition_parser.parse(response)
                break
            raise Exception
        except Exception:
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