import os
import re
import time
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

from dotenv import load_dotenv
from langchain import LLMChain
from langchain.agents import AgentExecutor, AgentOutputParser, LLMSingleActionAgent
from langchain.input import get_color_mapping
from langchain.output_parsers import OutputFixingParser
from langchain.prompts import BaseChatPromptTemplate
from langchain.schema import AgentAction, AgentFinish, HumanMessage
from langchain.tools import BaseTool
from pydantic import BaseModel
from typing_extensions import override

from ..memory.base import MemoryType
from ..tools.base import all_tools
from ..utils.model_name import ChatModelName
from ..utils.models import ChatModel
from ..utils.parameters import DEFAULT_SMART_MODEL
from ..utils.prompt import PromptString
from .plans import PlanStatus, SinglePlan

load_dotenv()


# Set up a prompt template
class CustomPromptTemplate(BaseChatPromptTemplate):
    # The template to use
    template: str
    # The list of tools available
    tools: List[BaseTool]

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
            raise ValueError(f"Could not parse LLM output: `{llm_output}`")
        action = match.group(1).strip()
        action_input = match.group(2)
        # Return the action and action input
        return AgentAction(
            tool=action, tool_input=action_input.strip(" ").strip('"'), log=llm_output
        )


class PlanExecutorResponse(BaseModel):
    status: PlanStatus
    output: str
    tool_name: Optional[str]
    tool_input: Optional[str]


class PlanExecutor(BaseModel):
    """Executes plans for an agent."""

    executor: LLMSingleActionAgent
    plan: Optional[SinglePlan] = None
    intermediate_steps: List[Tuple[AgentAction, str]] = []

    def __init__(self) -> None:
        prompt = CustomPromptTemplate(
            template=PromptString.EXECUTE_PLAN.value,
            tools=all_tools,
            # This omits the `agent_scratchpad`, `tools`, and `tool_names` variables because those are generated dynamically
            # This includes the `intermediate_steps` variable because that is needed
            input_variables=["input", "intermediate_steps"],
        )

        # set up a simple completion llm
        llm = ChatModel(model_name=DEFAULT_SMART_MODEL, temperature=0).defaultModel

        # LLM chain consisting of the LLM and a prompt
        llm_chain = LLMChain(llm=llm, prompt=prompt)

        output_parser = CustomOutputParser()

        tool_names = [tool.name for tool in all_tools]

        executor = LLMSingleActionAgent(
            llm_chain=llm_chain,
            output_parser=output_parser,
            stop=["\nObservation:"],
            allowed_tools=tool_names,
        )

        super().__init__(executor=executor)

    def set_plan(self, plan: SinglePlan) -> None:
        self.plan = plan
        self.intermediate_steps = []

    def start_or_continue_plan(self, plan: SinglePlan) -> PlanExecutorResponse:
        if not self.plan or self.plan.description != plan.description:
            self.set_plan(plan)
            return self.execute()
        else:
            return self.execute()

    def execute(self) -> str:
        if self.plan is None:
            raise ValueError("No plan set")

        response = self.executor.plan(
            input=self.plan.description, intermediate_steps=self.intermediate_steps
        )

        if isinstance(response, AgentFinish):
            self.plan = None
            self.intermediate_steps = []

            output = response.return_values.get("output")

            if output is None:
                raise ValueError(f"No output found in return values: {response}")

            if "Need Help" in output:
                return PlanExecutorResponse(status=PlanStatus.FAILED, output=output)
            else:
                return PlanExecutorResponse(status=PlanStatus.DONE, output=output)

        tool = next(
            (tool for tool in all_tools if tool.name.lower() == response.tool.lower()),
            None,
        )

        if tool is None:
            raise ValueError(f"Tool {response.tool} not found in tool list")

        result = tool.run(response.tool_input)

        self.intermediate_steps.append((response, result))

        return PlanExecutorResponse(
            status=PlanStatus.IN_PROGRESS,
            output=result,
            tool_name=tool.name,
            tool_input=response.tool_input,
        )
