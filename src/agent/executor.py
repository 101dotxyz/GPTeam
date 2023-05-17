import json
import os
import re
import time
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union
from uuid import UUID

from dotenv import load_dotenv
from langchain import LLMChain
from langchain.agents import AgentOutputParser, LLMSingleActionAgent
from langchain.llms import OpenAI
from langchain.output_parsers import OutputFixingParser
from langchain.prompts import BaseChatPromptTemplate
from langchain.schema import (
    AgentAction,
    AgentFinish,
    HumanMessage,
    OutputParserException,
    SystemMessage,
)
from langchain.tools import BaseTool
from pydantic import BaseModel
from typing_extensions import override

from src.utils.logging import agent_logger
from src.world.context import WorldContext

from ..memory.base import SingleMemory
from ..tools.base import CustomTool, get_tools
from ..tools.context import ToolContext
from ..tools.name import ToolName
from ..utils.colors import LogColor
from ..utils.formatting import print_to_console
from ..utils.models import ChatModel
from ..utils.parameters import DEFAULT_FAST_MODEL, DEFAULT_SMART_MODEL
from ..utils.prompt import PromptString
from .message import AgentMessage, get_conversation_history
from .plans import PlanStatus, SinglePlan

load_dotenv()


# Set up a prompt template
class CustomPromptTemplate(BaseChatPromptTemplate):
    # The template to use
    template: str
    # The list of tools available
    tools: List[BaseTool]

    @override
    def format_messages(self, **kwargs) -> str:
        # Get the intermediate steps (AgentAction, Observation tuples)
        # Format them in a particular way
        intermediate_steps = kwargs.pop("intermediate_steps")
        thoughts = ""
        for action, observation in intermediate_steps:
            thoughts += action.log
            thoughts += f"\nObservation: {observation}\nThought: "
        # Set the agent_scratchpad variable to that value
        kwargs["agent_scratchpad"] = thoughts

        # Create a tools variable from the list of tools provided
        kwargs["tools"] = "\n".join(
            [f"{tool.name}: {tool.description}" for tool in self.tools]
        )
        # Create a list of tool names for the tools provided
        kwargs["tool_names"] = ", ".join([tool.name for tool in self.tools])

        formatted = self.template.format(**kwargs)

        return [HumanMessage(content=formatted)]


# set up the output parser
class CustomOutputParser(AgentOutputParser):
    tools: List[BaseTool]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.tools = kwargs.pop("tools")

    def parse(self, llm_output: str) -> Union[AgentAction, AgentFinish]:
        # Check if agent should finish
        if "Final Response:" in llm_output:
            return AgentFinish(
                # Return values is generally always a dictionary with a single `output` key
                # It is not recommended to try anything else at the moment :)
                return_values={
                    "output": llm_output.split("Final Response:")[-1].strip()
                },
                log=llm_output,
            )
        # Parse out the action and action input
        regex = r"Action\s*\d*\s*:(.*?)\nAction\s*\d*\s*Input\s*\d*\s*:[\s]*(.*)"
        match = re.search(regex, llm_output, re.DOTALL)
        if not match:
            llm = ChatModel(DEFAULT_FAST_MODEL)

            formatting_correction = f"Could not parse the LLM output: `{llm_output}`\n\n Reformat the output to correspond to the following format: {self.get_format_instructions()} so that the result can be extracted using the regex: `{regex}`"

            retry = llm.get_chat_completion_sync(
                [SystemMessage(content=formatting_correction)]
            )

            match = re.search(regex, retry, re.DOTALL)

            if not match:
                raise OutputParserException(
                    f"Could not parse LLM output after retrying: \n`{retry}`. \nFirst attempt: \n`{retry}`"
                )

        action = match.group(1).strip()
        action_input = match.group(2)
        # try parsing action_input as json
        try:
            action_input = json.loads(action_input)
        except json.JSONDecodeError:
            action_input = action_input.strip(" ").strip('"')
        # Return the action and action input
        return AgentAction(tool=action, tool_input=action_input, log=llm_output)

    def get_format_instructions(self) -> str:
        tool_names = ", ".join([tool.name for tool in self.tools])
        return f"Your response should use the following format:\n\nTask: the task you must complete\nThought: your thoughts about what you should do\nAction: the action to take, which must be one of these words: [{tool_names}]\nAction Input: the input to the action\nObservation: the result of the action\n... (this Thought/Action/Action Input/Observation can repeated N times)\nThought: 'I have completed the task'\nFinal Response: the final response to the task\n\nIf you are not ready with a final response, then you must take an action.\n\nIf you determine that you are incapable of completing the task with the tools you have been given, return 'Final Response: Need Help', however, if you are in dialog with another character, responses such as 'I don't know' are valid responses. When in dialog, you should never, under any circumstance, break character, or admit that you are an AI.\nIf the task is complete and no specific response is needed, return 'Final Response: Done'"


class PlanExecutorResponse(BaseModel):
    status: PlanStatus
    output: str
    tool: Optional[CustomTool]
    tool_input: Optional[str]
    scratchpad: List[dict] = []


class CustomSingleActionAgent(LLMSingleActionAgent):
    @override
    def plan(self, *args, **kwargs) -> Union[AgentAction, AgentFinish]:
        try:
            result = super().plan(*args, **kwargs)

        # If there's an output parsing error, try again, with a reminder about the output format
        except OutputParserException as e:
            print("OutputParserException", e)

            if "input" in kwargs:
                kwargs["input"] = kwargs["input"] + PromptString.OUTPUT_FORMAT.value
            result = super().plan(*args, **kwargs)

        return result


class PlanExecutor(BaseModel):
    """Executes plans for an agent."""

    agent_id: UUID
    message_to_respond_to: Optional[AgentMessage] = None
    relevant_memories: list[SingleMemory]
    context: WorldContext
    plan: Optional[SinglePlan] = None

    def __init__(
        self,
        agent_id: UUID,
        world_context: WorldContext,
        relevant_memories: list[SingleMemory] = [],
        message_to_respond_to: AgentMessage = None,
    ) -> None:
        super().__init__(
            agent_id=agent_id,
            context=world_context,
            relevant_memories=relevant_memories,
            message_to_respond_to=message_to_respond_to,
        )

    def get_executor(self, tools: list[CustomTool]) -> CustomSingleActionAgent:
        prompt = CustomPromptTemplate(
            template=PromptString.EXECUTE_PLAN.value,
            tools=tools,
            # This omits the `agent_scratchpad`, `tools`, and `tool_names` variables because those are generated dynamically
            # This includes the `intermediate_steps` variable because that is needed
            input_variables=[
                "input",
                "intermediate_steps",
                "your_name",
                "your_private_bio",
                "location_context",
                "conversation_history",
                "relevant_memories",
            ],
        )

        # set up a simple completion llm
        llm = ChatModel(model_name=DEFAULT_SMART_MODEL, temperature=0).defaultModel

        # LLM chain consisting of the LLM and a prompt
        llm_chain = LLMChain(llm=llm, prompt=prompt)

        output_parser = CustomOutputParser(tools=tools)

        executor = CustomSingleActionAgent(
            llm_chain=llm_chain,
            output_parser=output_parser,
            stop=["\nObservation:"],
        )
        return executor

    def intermediate_steps_to_list(
        self, intermediate_steps: List[Tuple[AgentAction, str]]
    ) -> List[dict]:
        result = []
        for action, observation in intermediate_steps:
            action_dict = {
                "tool": action.tool,
                "tool_input": action.tool_input,
                "log": action.log,
            }
            result.append({"action": action_dict, "observation": observation})
        return result

    def list_to_intermediate_steps(
        self, intermediate_steps: List[dict]
    ) -> List[Tuple[AgentAction, str]]:
        result = []
        for step in intermediate_steps:
            action = AgentAction(**step["action"])
            observation = step["observation"]
            result.append((action, observation))
        return result

    def failed_action_response(self, output: str) -> PlanExecutorResponse:
        return PlanExecutorResponse(
            status=PlanStatus.IN_PROGRESS, output=output, scratchpad=[]
        )

    async def start_or_continue_plan(
        self, plan: SinglePlan, tools: list[CustomTool]
    ) -> PlanExecutorResponse:
        if not self.plan or self.plan.description != plan.description:
            self.plan = plan
        return await self.execute(tools)

    async def execute(self, tools: list[CustomTool]) -> str:
        if self.plan is None:
            raise ValueError("No plan set")

        executor = self.get_executor(tools=tools)

        # Get intermediate steps from the plan
        if self.plan.scratchpad is not None:
            intermediate_steps = self.list_to_intermediate_steps(self.plan.scratchpad)
        else:
            intermediate_steps = []

        # Make the conversation history
        conversation_history = await get_conversation_history(
            self.context.get_agent_location_id(self.agent_id), self.context
        )

        # Make the relevant memories string
        if self.relevant_memories:
            relevant_memories = "\n".join(
                f"{memory.description} [{memory.created_at}]"
                for memory in self.relevant_memories
            )
        else:
            relevant_memories = ""

        response = executor.plan(
            input=self.plan.make_plan_prompt(),
            intermediate_steps=intermediate_steps,
            your_name=self.context.get_agent_full_name(self.agent_id),
            your_private_bio=self.context.get_agent_private_bio(self.agent_id),
            location_context=self.context.location_context_string(self.agent_id),
            conversation_history=conversation_history,
            relevant_memories=relevant_memories,
        )

        agent_name = self.context.get_agent_full_name(self.agent_id)

        for log in response.log.split("\n"):
            prefix_text = log.split(":")[0] if ":" in log else "Thought"
            log_content = log.split(":", 1)[1].strip() if ":" in log else log.strip()

            log_color = self.context.get_agent_color(self.agent_id)

            agent_logger.info(
                f"[{agent_name}] [{log_color}] [{prefix_text}] {log_content}"
            )
            print_to_console(
                f"[{agent_name}] {prefix_text}: ",
                log_color,
                log_content,
            )

        # If the agent is finished, return the output
        if isinstance(response, AgentFinish):
            self.plan = None

            output = response.return_values.get("output")

            if output is None:
                raise ValueError(f"No output found in return values: {response}")

            if "Need Help" in output:
                return PlanExecutorResponse(status=PlanStatus.FAILED, output=output)
            else:
                return PlanExecutorResponse(status=PlanStatus.DONE, output=output)

        # Get the tool context
        tool_context = ToolContext(
            agent_id=self.agent_id,
            context=self.context,
            memories=self.relevant_memories,
        )

        # Clean the chosen tool name
        formatted_tool_name = response.tool.lower().strip().replace(" ", "-")

        # Try to get the tool object
        try:
            tool = get_tools(
                [ToolName(formatted_tool_name)],
                context=self.context,
                agent_id=self.agent_id,
            )[0]

        # If failed to get tool, return a failure message
        except Exception as e:
            if not isinstance(e, ValueError) and not isinstance(e, IndexError):
                raise e

            result = f"Tool: '{formatted_tool_name}' is not found in tool list"

            log_color = self.context.get_agent_color(self.agent_id)

            agent_logger.info(
                f"[{agent_name}] [{log_color}] [Action Response] {result}"
            )

            print_to_console(
                f"[{agent_name}] Action Response: ",
                log_color,
                result,
            )

            intermediate_steps.append((response, result))

            executor_response = PlanExecutorResponse(
                status=PlanStatus.IN_PROGRESS,
                output=result,
                tool=None,
                scratchpad=self.intermediate_steps_to_list(intermediate_steps),
                tool_input=str(response.tool_input),
            )

            return executor_response

        result = await tool.run(response.tool_input, tool_context)

        log_color = self.context.get_agent_color(self.agent_id)

        agent_logger.info(f"[{agent_name}] [{log_color}] [Action Response] {result}")

        print_to_console(
            f"[{agent_name}] Action Response: ",
            log_color,
            result[:280] + "..." if len(result) > 280 else str(result),
        )

        # Add the intermediate step to the list of intermediate steps
        # But if this is the second wait in a row, replace it
        if (
            intermediate_steps
            and intermediate_steps[-1][0].tool.strip() == ToolName.WAIT.value
            and response.tool.strip() == ToolName.WAIT.value
        ):
            intermediate_steps[-1] = (response, result)
        else:
            intermediate_steps.append((response, result))

        executor_response = PlanExecutorResponse(
            status=PlanStatus.IN_PROGRESS,
            output=result,
            tool=tool,
            scratchpad=self.intermediate_steps_to_list(intermediate_steps),
            tool_input=str(response.tool_input),
        )

        return executor_response
