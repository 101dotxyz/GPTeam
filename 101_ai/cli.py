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


async def main():
    init()
    print_to_console(
        "Introduction",
        Fore.BLUE,
        "\nHi there 👋\n\nI'm Lixir, your AI programming assistant. Together we will create an application without writing a single line of code!\n\nLet's get started.\n",
    )
    print_to_console("Question", Fore.GREEN, "What are we building today?")
    time.sleep(1)
    task_description = "A Gmail bot that sends a daily email with a summary of the user's unread emails."
    print_to_console("Answer", Fore.CYAN, task_description)

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
                content=f"Now you have provided a task definition, please reflect on ways that you should improve it. Remember, the description of the task is: {task_description}. You can ask me questions to help you think of improvements. Only when you are ready, give me an improved task definition that corresponds to the previously provided formatting requirements."
            )

            messages.append(reflection_message)

        for _ in range(MAX_ITERATIONS_PER_REFLECTION):
            with Spinner("🤔 Thinking... "):
                response = get_chat_completion(messages, ChatModel.TURBO)
                messages.append(AIMessage(content=response))

                if "backend_endpoints" in response:
                    result = parser.parse(response)
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


asyncio.run(main())
