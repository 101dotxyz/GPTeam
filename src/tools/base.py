from typing import List, Optional, Any
from typing_extensions import override

from langchain import GoogleSearchAPIWrapper
from langchain.agents import Tool, load_tools
from langchain.llms import OpenAI
from langchain.tools import BaseTool

from .send_message import send_message

class CustomTool(Tool):
    requires_context: Optional[bool] = False

    def __init__(
        self, 
        name: str, 
        func, 
        description: str,
        requires_context: Optional[bool],
        **kwargs: Any
    ):
        super().__init__(name, func, description, **kwargs)
        self.requires_context = requires_context

    @override
    def run(self, agent_input: str | dict, system_context: dict = {}) -> List[BaseTool]:

        # if the tool requires context, but none is provided, raise an error
        if self.requires_context and not bool(system_context):
            raise Exception(f"tool {self.name} requires system_context, but none was provided")
        
        # if the tool requires context 
        if self.requires_context:
            
            # Combine the agent input and context into a dict
            if isinstance(agent_input, str):
                agent_input = {"agent_input": agent_input}
            input = {**agent_input, **system_context}

        else:
            input = str(agent_input)




        # Run the Tool with the combined input
        return super().run(input)



custom_tools: List[CustomTool] = [
    CustomTool(
        name="search",
        func=GoogleSearchAPIWrapper().run,
        description="useful for when you need to search for information you do not know. the input to this should be a single search term.",
        requires_context=False,
    ),
    CustomTool(
        name="speak",
        func=send_message,
        description="useful for when you need to speak to someone. the input to this should be a single message.",
        requires_context=True # this tool requires events_manager as context
    )
]

built_in_tools: List[BaseTool] = load_tools(
    tool_names=["wolfram-alpha", "human"], llm=OpenAI()
)

custom_built_in_tools = []
for tool in built_in_tools:
    custom_tool = CustomTool(
        name=tool.name,
        func=tool.run,
        description=tool.description,
        args_schema=tool.args_schema,
        requires_context=False
    )
    custom_built_in_tools.append(custom_tool)


all_tools = custom_tools + custom_built_in_tools
