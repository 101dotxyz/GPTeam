from langchain import PromptTemplate
from langchain.prompts.chat import (ChatPromptTemplate,
                                    HumanMessagePromptTemplate,
                                    SystemMessagePromptTemplate)

from ..parsers.task_definition_parser import get_task_definition_parser

task_definition_parser = get_task_definition_parser()

TASK_DEFINITION_SYSTEM_PROMPT_TEMPLATE = SystemMessagePromptTemplate(prompt=PromptTemplate(
    template="You are a engineering manager for a software development team. Your job is to translate high-level app concepts, given by users, into a well-defined technical specification for a developer to implement.\n\nFor each app concept, you should start by asking clarifying questions of the user so that a developer can implement the idea with zero additional guidance or outside resources.\n\nThe developer will be writing their implementation in typescript. They will not have access to any paid API services. If the app requires one, ask the user for an API key. \n\n Once you are ready to give a specification, your final answer should be formatted according to the following rules: {format_instructions}",
    input_variables=[],
    partial_variables={"format_instructions": task_definition_parser.get_format_instructions()},
))

TASK_DEFINITION_SYSTEM_PROMPT_TEMPLATE
TASK_DEFINITION_HUMAN_PROMPT_TEMPLATE = HumanMessagePromptTemplate(prompt=PromptTemplate(
    template="Here is my new app concept: {task_description}",
    input_variables=["task_description"],
))

TASK_DEFINITION_CHAT_PROMPT_TEMPLATE = chat_prompt = ChatPromptTemplate.from_messages([TASK_DEFINITION_SYSTEM_PROMPT_TEMPLATE, TASK_DEFINITION_HUMAN_PROMPT_TEMPLATE])
