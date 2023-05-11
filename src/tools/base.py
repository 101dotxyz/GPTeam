import asyncio
import enum
import inspect
import os
from enum import Enum
from typing import Any, Awaitable, Callable, List, Optional, Type, Union
from uuid import UUID

from langchain import GoogleSearchAPIWrapper, SerpAPIWrapper, WolframAlphaAPIWrapper
from langchain.agents import Tool, load_tools
from langchain.llms import OpenAI
from langchain.tools import BaseTool
from typing_extensions import override

from src.tools.context import ToolContext
from src.tools.document import (
    ReadDocumentToolInput,
    SaveDocumentToolInput,
    SearchDocumentsToolInput,
    read_document,
    save_document,
    search_documents,
)
from src.tools.human import ask_human, ask_human_async
from src.utils.models import ChatModel
from src.utils.parameters import DEFAULT_SMART_MODEL, DISCORD_ENABLED
from src.utils.prompt import Prompter, PromptString
from src.world.context import WorldContext

from .directory import consult_directory
from .name import ToolName
from .send_message import SpeakToolInput, send_message_async, send_message_sync
from .wait import wait_async, wait_sync


class CustomTool(Tool):
    name: str
    requires_context: Optional[bool] = False
    requires_authorization: bool = False
    worldwide: bool = True
    tool_usage_description: str = None
    tool_usage_summarization_prompt: PromptString = None

    def __init__(
        self,
        name: str,
        description: str,
        requires_context: Optional[bool],
        worldwide: bool,
        requires_authorization: bool,
        tool_usage_description: str,
        func: Optional[Any] = lambda x: x,
        coroutine: Optional[Any] = None,
        tool_usage_summarization_prompt: Optional[PromptString] = None,
        **kwargs: Any,
    ):
        super().__init__(
            name=name,
            func=func,
            description=description,
            coroutine=coroutine,
            **kwargs,
        )
        self.requires_context = requires_context
        self.requires_authorization = requires_authorization
        self.worldwide = worldwide
        self.tool_usage_description = tool_usage_description
        self.tool_usage_summarization_prompt = tool_usage_summarization_prompt

    @override
    async def run(self, agent_input: str | dict, tool_context: ToolContext) -> Any:
        # if the tool requires context
        if self.requires_context:
            input = (
                {"agent_input": agent_input, "tool_context": tool_context}
                if isinstance(agent_input, str)
                else {**agent_input, "tool_context": tool_context}
            )

        else:
            input = agent_input

        try:
            if self.coroutine:
                return await super().arun(input)
            else:
                return super().run(input)
        except Exception as e:
            return f"Error: {e}"

    async def summarize_usage(
        self,
        plan_description: str,
        tool_input: str,
        tool_result: str,
        agent_full_name: str,
    ) -> str:
        tool_usage_reflection = ""
        if self.tool_usage_summarization_prompt:
            reaction_prompter = Prompter(
                self.tool_usage_summarization_prompt,
                {
                    "plan_description": plan_description,
                    "tool_name": self.name,
                    "tool_input": tool_input,
                    "tool_result": tool_result,
                },
            )

            llm = ChatModel(DEFAULT_SMART_MODEL, temperature=0)

            tool_usage_reflection = await llm.get_chat_completion(
                reaction_prompter.prompt,
                loading_text="🤔 Summarizing tool usage",
            )

        return self.tool_usage_description.format(
            agent_full_name=agent_full_name,
            tool_name=self.name,
            tool_usage_reflection=tool_usage_reflection,
            recipient_full_name=(
                tool_input.split(";")[0]
                if len(tool_input.split(";")) > 0
                else "a colleague"
            )
            if self.name == ToolName.SPEAK.value
            else "",
        )


def load_built_in_tool(
    tool_name: ToolName,
    tool_usage_description: str,
    worldwide=True,
    requires_authorization=False,
    tool_usage_summarization_prompt: Optional[PromptString] = None,
) -> CustomTool:
    tools = load_tools(tool_names=[tool_name.value], llm=OpenAI())

    tool = tools[0]

    return CustomTool(
        name=tool_name,
        func=tool.run,
        description=tool.description,
        worldwide=worldwide,
        requires_authorization=requires_authorization,
        args_schema=tool.args_schema,
        tool_usage_description=tool_usage_description,
        tool_usage_summarization_prompt=tool_usage_summarization_prompt,
        requires_context=False,
    )


SERPAPI_KEY = os.environ.get("SERPAPI_KEY")
WOLFRAM_ALPHA_APPID = os.environ.get("WOLFRAM_ALPHA_APPID")


def get_tools(
    tools: list[ToolName],
    context: WorldContext,
    agent_id: str | UUID,
    include_worldwide=False,
) -> List[CustomTool]:
    location_id = context.get_agent_location_id(agent_id=agent_id)

    location_name = context.get_location_name(location_id=location_id)

    agents_at_location = context.get_agents_at_location(location_id=location_id)

    other_agents = [a for a in agents_at_location if str(a["id"]) != str(agent_id)]

    # names of other agents at location
    other_agent_names = ", ".join([a["full_name"] for a in other_agents]) or "nobody"

    SEARCH_ENABLED = bool(os.getenv("SERPAPI_KEY"))
    WOLFRAM_ENABLED = bool(os.getenv("WOLFRAM_ALPHA_APPID"))

    TOOLS: dict[ToolName, CustomTool] = {
        ToolName.SEARCH: CustomTool(
            name=ToolName.SEARCH.value,
            func=SerpAPIWrapper().run,
            description="search the web for information. input should be the search query.",
            coroutine=SerpAPIWrapper().arun,
            tool_usage_summarization_prompt="You have just searched Google with the following search input: {tool_input} and got the following result {tool_result}. Write a single sentence with useful information about how the result can help you accomplish your plan: {plan_description}.",
            tool_usage_description="To make progress on their plans, {agent_full_name} searched Google and realised the following: {tool_usage_reflection}.",
            requires_authorization=False,
            requires_context=True,
            worldwide=True,
        )
        if SEARCH_ENABLED
        else None,
        ToolName.SPEAK: CustomTool(
            name=ToolName.SPEAK.value,
            func=send_message_sync,
            coroutine=send_message_async,
            description=f'say something in the {location_name}. The following people are also in the {location_name} and are the only people who will hear what you say: [{other_agent_names}] You can say something to everyone in the {location_name}, or address a specific person at your location. Input should be a json string with two keys: "recipient" and "message". The value of "recipient" should be a string of the recipients name or "everyone" if speaking to everyone, and the value of "message" should be a string. If you are waiting for a response, just keep using the \'wait\' tool. Example input: {{"recipient": "Jonathan", "message": "Hello Jonathan! 😄"}}',
            tool_usage_description="To make progress on their plans, {agent_full_name} spoke to {recipient_full_name}.",
            requires_context=True,
            args_schema=SpeakToolInput,
            requires_authorization=False,
            worldwide=True,
        ),
        ToolName.WAIT: CustomTool(
            name=ToolName.WAIT.value,
            func=wait_sync,
            coroutine=wait_async,
            description="Useful for when you are waiting for something to happen. Input a very detailed description of what exactly you are waiting for. Start your input with 'I am waiting for...' (e.g. I am waiting for any type of meeting to start in the conference room).",
            tool_usage_description="{agent_full_name} is waiting.",
            requires_context=True,
            requires_authorization=False,
            worldwide=True,
        ),
        ToolName.WOLFRAM_APLHA: CustomTool(
            name=ToolName.WOLFRAM_APLHA.value,
            description="A wrapper around Wolfram Alpha. Useful for when you need to answer questions about Math, Science, Technology, Culture, Society and Everyday Life. Input should be a search query.",
            func=WolframAlphaAPIWrapper().run,
            requires_authorization=False,
            worldwide=True,
            requires_context=False,
            tool_usage_summarization_prompt="You have just used Wolphram Alpha with the following input: {tool_input} and got the following result {tool_result}. Write a single sentence with useful information about how the result can help you accomplish your plan: {plan_description}.",
            tool_usage_description="In order to make progress on their plans, {agent_full_name} used Wolphram Alpha and realised the following: {tool_usage_reflection}.",
        )
        if WOLFRAM_ENABLED
        else None,
        ToolName.HUMAN: CustomTool(
            name=ToolName.HUMAN.value,
            func=ask_human,
            coroutine=ask_human_async,
            description=(
                "You can ask a human for guidance when you think you "
                "got stuck or you are not sure what to do next. "
                "The input should be a question for the human."
            ),
            tool_usage_summarization_prompt="You have just asked a human for help by saying {tool_input}. This is what they replied: {tool_result}. Write a single sentence with useful information about how the result can help you accomplish your plan: {plan_description}.",
            tool_usage_description="In order to make progress on their plans, {agent_full_name} spoke to a human.",
            requires_context=True,
            requires_authorization=False,
            worldwide=True,
        ),
        ToolName.COMPANY_DIRECTORY: CustomTool(
            name=ToolName.COMPANY_DIRECTORY.value,
            func=consult_directory,
            description="A directory of all the people you can speak with, detailing their names and bios. Useful for when you need help from another person. Takes an empty string as input.",
            tool_usage_summarization_prompt="You have just consulted the company directory and found out the following: {tool_result}. Write a single sentence with useful information about how the result can help you accomplish your plan: {plan_description}.",
            tool_usage_description="In order to make progress on their plans, {agent_full_name} consulted the company directory and realised the following: {tool_usage_reflection}.",
            requires_context=True,  # this tool requires location_id as context
            requires_authorization=False,
            worldwide=True,
        ),
        ToolName.SAVE_DOCUMENT: CustomTool(
            name=ToolName.SAVE_DOCUMENT.value,
            coroutine=save_document,
            description="""Write text to an existing document or create a new one. Useful for when you need to save a document for later use. Input should be a json string with two keys: "title" and "document". The value of "title" should be a string, and the value of "document" should be a string.""",
            tool_usage_description="In order to make progress on their plans, {agent_full_name} saved a document.",
            requires_context=True,  # this tool requires document_name and content as context
            args_schema=SaveDocumentToolInput,
            requires_authorization=False,
            worldwide=True,
        ),
        ToolName.READ_DOCUMENT: CustomTool(
            name=ToolName.READ_DOCUMENT.value,
            coroutine=read_document,
            description="""Read text from an existing document. Useful for when you need to read a document that you have saved.
Input should be a json string with one key: "title". The value of "title" should be a string.""",
            tool_usage_description="In order to make progress on their plans, {agent_full_name} read a document.",
            requires_context=True,  # this tool requires document_name and content as context
            args_schema=ReadDocumentToolInput,
            requires_authorization=False,
            worldwide=True,
        ),
        ToolName.SEARCH_DOCUMENTS: CustomTool(
            name=ToolName.SEARCH_DOCUMENTS.value,
            coroutine=search_documents,
            description="""Search previously saved documents. Useful for when you need to read a document who's exact name you forgot.
Input should be a json string with one key: "query". The value of "query" should be a string.""",
            tool_usage_description="In order to make progress on their plans, {agent_full_name} searched documents.",
            requires_context=True,  # this tool requires document_name and content as context
            args_schema=SearchDocumentsToolInput,
            requires_authorization=False,
            worldwide=True,
        ),
    }

    return [
        tool
        for tool in TOOLS.values()
        if tool
        and (
            tool.name in [t.value for t in tools]
            or (tool.worldwide and include_worldwide)
        )
    ]
