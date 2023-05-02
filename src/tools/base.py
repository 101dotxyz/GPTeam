import enum
from typing import Any, List, Optional
from uuid import UUID

from langchain import GoogleSearchAPIWrapper
from langchain.agents import Tool, load_tools
from langchain.llms import OpenAI
from langchain.tools import BaseTool
from typing_extensions import override

from src.tools.context import ToolContext
from src.tools.document import ReadDocumentToolInput, SaveDocumentToolInput, SearchDocumentsToolInput, read_document, save_document, search_documents
from src.world.context import WorldContext

from .directory import consult_directory
from .name import ToolName
from .send_message import send_message
from .wait import wait


class CustomTool(Tool):
    requires_context: Optional[bool] = False
    requires_authorization: bool = False
    worldwide: bool = True

    def __init__(
        self,
        name: str,
        func,
        description: str,
        requires_context: Optional[bool],
        worldwide: bool,
        requires_authorization: bool,
        **kwargs: Any,
    ):
        super().__init__(name, func, description, **kwargs)

        self.requires_context = requires_context
        self.requires_authorization = requires_authorization
        self.worldwide = worldwide

    @override
    def run(self, agent_input: str | dict, tool_context: ToolContext) -> List[BaseTool]:
        # if the tool requires context
        if self.requires_context:
            input = {"agent_input": agent_input, "tool_context": tool_context} if isinstance(agent_input, str) else {**agent_input, "tool_context": tool_context}

        else:
            input = agent_input
        return super().run(input)


def load_built_in_tool(
    tool: str, worldwide=True, requires_authorization=False
) -> CustomTool:
    tools = load_tools(tool_names=[tool], llm=OpenAI())

    tool = tools[0]

    return CustomTool(
        name=tool.name,
        func=tool.run,
        description=tool.description,
        worldwide=worldwide,
        requires_authorization=requires_authorization,
        args_schema=tool.args_schema,
        requires_context=False,
    )


def get_tools(
    tools: List[ToolName],
    context: WorldContext,
    agent_id: str | UUID,
    include_worldwide=False,
) -> List[CustomTool]:
    location_id = context.get_agent_location_id(agent_id=agent_id)

    location_name = context.get_location_name(location_id=location_id)

    agents_at_location = context.get_agents_at_location(location_id=location_id)

    other_agents = [a for a in agents_at_location if str(a["id"]) != str(agent_id)]

    # names of other agents at location
    other_agent_names = ", ".join([a["full_name"] for a in other_agents])

    TOOLS: dict[ToolName, CustomTool] = {
        ToolName.SEARCH: CustomTool(
            name="search",
            func=GoogleSearchAPIWrapper().run,
            description="useful for when you need to search for information you do not know. the input to this should be a single search term.",
            requires_context=False,
            requires_authorization=False,
            worldwide=True,
        ),
        ToolName.SPEAK: CustomTool(
            name="speak",
            func=send_message,
            description=f"say something in the {location_name}. {other_agent_names} are also in the {location_name} and will hear what you say. No one else will hear you. You can say something to everyone nearby, or address a specific person at your location (one of {other_agent_names}). The input should be of the format <recipient's full name> OR everyone;'<message>' (e.g. David Summers;'Hi David! How are you doing today?') (e.g. everyone;'Let\'s get this meeting started.'). Do not use a semi-colon in your message.",
            requires_context=True,
            requires_authorization=False,
            worldwide=True,
        ),
        ToolName.WAIT: CustomTool(
            name="wait",
            func=wait,
            description="Don't do anything. Useful for when you are waiting for something to happen. Takes an empty string as input.",
            requires_context=False,
            requires_authorization=False,
            worldwide=True,
        ),
        ToolName.WOLFRAM_APLHA: load_built_in_tool(
            "wolfram-alpha", requires_authorization=False, worldwide=True
        ),
        ToolName.HUMAN: load_built_in_tool(
            "human", requires_authorization=False, worldwide=True
        ),
        ToolName.COMPANY_DIRECTORY: CustomTool(
            name=ToolName.COMPANY_DIRECTORY.value,
            func=consult_directory,
            description="A directory of all the people you can speak with, detailing their names, roles, and current locations. Useful for when you need help from another person.",
            requires_context=True,  # this tool requires location_id as context
            requires_authorization=False,
            worldwide=True,
        ),
        ToolName.SAVE_DOCUMENT: CustomTool(
            name=ToolName.SAVE_DOCUMENT.value,
            func=save_document,
            description="""Write text to an existing document or create a new one. Useful for when you need to save a document for later use.
Input should be a json string with two keys: "title" and "document".
The value of "title" should be a string, and the value of "document" should be a string.""",
            requires_context=True,  # this tool requires document_name and content as context
            args_schema=SaveDocumentToolInput,
            requires_authorization=False,
            worldwide=True,
        ),
        ToolName.READ_DOCUMENT: CustomTool(
            name=ToolName.READ_DOCUMENT.value,
            func=read_document,
            description="""Read text from an existing document. Useful for when you need to read a document that you have saved.
Input should be a json string with one key: "title". The value of "title" should be a string.""",
            requires_context=True,  # this tool requires document_name and content as context
            args_schema=ReadDocumentToolInput,
            requires_authorization=False,
            worldwide=True,
        ),
        ToolName.SEARCH_DOCUMENTS: CustomTool(
            name=ToolName.SEARCH_DOCUMENTS.value,
            func=search_documents,
            description="""Search previously saved documents. Useful for when you need to read a document who's exact name you forgot.
Input should be a json string with one key: "query". The value of "query" should be a string.""",
            requires_context=True,  # this tool requires document_name and content as context
            args_schema=SearchDocumentsToolInput,
            requires_authorization=False,
            worldwide=True,
        ),
    }

    if not include_worldwide:
        return [TOOLS[tool] for tool in tools]

    return [tool for tool in TOOLS.values() if (tool.name in tools or tool.worldwide)]
