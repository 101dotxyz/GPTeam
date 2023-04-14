import argparse
import asyncio
import time
from typing import Optional

from colorama import Fore, Style, init
from dotenv import load_dotenv
from langchain.schema import AIMessage, BaseMessage, HumanMessage, SystemMessage

from .parsers.task_definition_parser import TaskDefinition, get_task_definition_parser
from .utils.chat import get_chat_completion
from .utils.formatting import print_to_console
from .utils.models import ChatModel
from .utils.spinner import Spinner

load_dotenv()

REFLECTION_ITERATIONS = 2
MAX_ITERATIONS_PER_REFLECTION = 10


async def main(use_defaults=True):
    init()
    print_to_console(
        "Introduction",
        Fore.BLUE,
        "\nHi there 👋\n\nI'm Lixir, your AI programming assistant. Together we will create an application without writing a single line of code!\n\nLet's get started.\n",
    )

    print_to_console("Question", Fore.GREEN, "What are we building today?")
    goal = None
    key_objectives = None
    if use_defaults:
        time.sleep(1)
        goal = "A Gmail bot that sends a daily email with a summary of the user's unread emails."
        key_objectives = "1. Send a summary email every day\n2. Help me to save time reading my emails"
        print(f"Goal: {goal}")
        print(f"Key Objectives: {key_objectives}")
    else:
        goal = input()

    task_description = f"Goal: {goal}, Key Objectives: {key_objectives}"

    parser = get_task_definition_parser()

    system_message = SystemMessage(
        content=f"As an engineering manager, you are talking with a Product Manager to create a well-defined technical specification for a new standalone app. The Product Manager knows what the app should do, but does not have any technical knowledge. You should ask them a question when you need to know something about the product, but remember that this is a conversation so you shouldn't ask them too much at once and you'll have to figure out technical stuff yourself based on their answers. The technical specification should be complete and self-sufficient, allowing a developer to implement it in TypeScript without needing additional guidance or external resources. The developer won't have access to any paid API services, so if the app requires one, you should ask the Product Manager for an API key. IMPORTANT: Format your final answer according to the following instructions: {parser.get_format_instructions()}"
    )

    human_message = HumanMessage(
        content=f"Here is my new app concept: {task_description}"
    )

    messages: list[BaseMessage] = [system_message, human_message]

    result: Optional[TaskDefinition] = None

    for reflection_iteration in range(REFLECTION_ITERATIONS + 1):
        if reflection_iteration > 0:
            print_to_console(
                "Answer",
                Fore.CYAN,
                f"Here is my new app concept: {result}",
            )
            print_to_console(
                "Reflection",
                Fore.MAGENTA,
                "Initiating reflection.",
            )

            reflection_message = HumanMessage(
                content=f"Now you have provided your {nth(reflection_iteration)} draft of a technical specification, please reflect on ways that you could improve it. Remember, the description of the task is: {task_description}. You can ask me questions to help you think of improvements. Only when you are ready, give me an improved task definition that corresponds to the previously provided formatting requirements."
            )

            messages.append(reflection_message)

        for _ in range(MAX_ITERATIONS_PER_REFLECTION):
            response = get_chat_completion(messages, ChatModel.TURBO)
            messages.append(AIMessage(content=response))

            if "backend_endpoints" in response:
                initial_result = parser.parse(response)

                if initial_result:
                    variant_message = HumanMessage(
                        content="Based on the information I have provided to you, create a different technical specification that uses a different approach, so that I can compare both technical specifications. Do not ask any questions and immediately provide a technical specification. You must use the same formatting requirements as before."
                    )

                    response = get_chat_completion(
                        [*messages, variant_message], ChatModel.TURBO
                    )

                    variant_result = parser.parse(response)

                    print_to_console("Original", Fore.GREEN, initial_result)

                    print_to_console("Variant", Fore.GREEN, variant_result)

                    comparison_message = HumanMessage(
                        content=f"Compare the following two technical specifications for the following task: {task_description}\n\n1. {initial_result}\n\n2. {variant_result}\n\nWhich technical specification do you think is better? Respond with a number 1 or 2 based on the variant you think is best."
                    )

                    response = get_chat_completion(
                        [*messages, comparison_message], ChatModel.TURBO
                    )

                    print_to_console("Comparison", Fore.GREEN, response)

                    result = initial_result if "1" in response else variant_result
                    break

            print_to_console("Question", Fore.GREEN, response)
            human_response = input("Answer: ")
            human_message = HumanMessage(content=human_response)
            messages.append(human_message)

        if not result:
            print_to_console(
                "Max iterations reached",
                Fore.RED,
                f"I reached the maximum number of allowed iterations ({MAX_ITERATIONS_PER_REFLECTION}) and gave up trying.",
            )
            return

    print_to_console("Task Specification", Fore.MAGENTA, "Here's what I came up with:")
    print_to_console("Backend Endpoints", Fore.BLUE, str(result.backend_endpoints))
    print_to_console("CRON Jobs", Fore.BLUE, str(result.cron_jobs))
    print_to_console("Environment Variables", Fore.BLUE, str(result.env_variables))
    print_to_console("Implementation Notes", Fore.BLUE, result.implementation_notes)


def nth(n: int) -> str:
    if n == 1:
        return "first"
    if n == 2:
        return "second"
    if n == 3:
        return "third"
    return f"{n}th"


asyncio.run(main())
