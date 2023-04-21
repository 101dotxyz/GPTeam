import os
import re
import time
from enum import Enum
from typing import Any, Dict, List, Tuple, Union

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

from ..tools.base import all_tools
from ..utils.model_name import ChatModelName
from ..utils.models import ChatModel
from ..utils.parameters import DEFAULT_SMART_MODEL
from ..utils.prompt import PromptString

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


class ExecutorStatus(Enum):
    COMPLETED = "completed"
    TIMED_OUT = "timed_out"
    NEEDS_HELP = "needs_help"


class ExecutorResponse(BaseModel):
    status: ExecutorStatus
    output: str


def run_executor(
    input: str,
    timeout: int = int(os.getenv("STEP_DURATION")),
    intermediate_steps_old: List[Tuple[AgentAction, str]] = [],
) -> ExecutorResponse:
    """Runs the executor for a max of 1 step"""

    print("Runing agent executor")

    class PreemptableExecutor(AgentExecutor):
        @override
        def _call(self, inputs: Dict[str, str]) -> Dict[str, Any]:
            """Run text through and get agent response."""
            # Construct a mapping of tool name to tool for easy lookup
            name_to_tool_map = {tool.name: tool for tool in self.tools}
            # We construct a mapping from each tool to a color, used for logging.
            color_mapping = get_color_mapping(
                [tool.name for tool in self.tools], excluded_colors=["green"]
            )
            intermediate_steps: List[Tuple[AgentAction, str]] = intermediate_steps_old
            # Let's start tracking the number of iterations and time elapsed
            iterations = 0
            time_elapsed = 0.0
            start_time = time.time()
            # We now enter the agent loop (until it returns something).
            while self._should_continue(iterations, time_elapsed):
                next_step_output = self._take_next_step(
                    name_to_tool_map, color_mapping, inputs, intermediate_steps
                )
                if isinstance(next_step_output, AgentFinish):
                    return self._return(next_step_output, intermediate_steps)

                intermediate_steps.extend(next_step_output)
                if len(next_step_output) == 1:
                    next_step_action = next_step_output[0]
                    # See if tool should return directly
                    tool_return = self._get_tool_return(next_step_action)
                    if tool_return is not None:
                        return self._return(tool_return, intermediate_steps)
                iterations += 1
                time_elapsed = time.time() - start_time
            output = self.agent.return_stopped_response(
                self.early_stopping_method, intermediate_steps, **inputs
            )
            return self._return(output, intermediate_steps)

        @override
        def run(self, *args: Any, **kwargs: Any) -> str:
            """Run the chain as text in, text out or multiple variables, text out."""
            if len(self.output_keys) != 1:
                raise ValueError(
                    f"`run` not supported when there is not exactly "
                    f"one output key. Got {self.output_keys}."
                )

            if args and not kwargs:
                if len(args) != 1:
                    raise ValueError("`run` supports only one positional argument.")
                result = self(args[0])
                print(result)
                return result[self.output_keys[0]]

            if kwargs and not args:
                result = self(kwargs)
                print(result)
                return result[self.output_keys[0]]

            raise ValueError(
                f"`run` supported with either positional arguments or keyword arguments"
                f" but not both. Got args: {args} and kwargs: {kwargs}."
            )

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
    agent = LLMSingleActionAgent(
        llm_chain=llm_chain,
        output_parser=output_parser,
        stop=["\nObservation:"],
        allowed_tools=tool_names,
    )

    agent_executor = PreemptableExecutor.from_agent_and_tools(
        agent=agent,
        tools=all_tools,
        verbose=True,
        max_execution_time=timeout,
    )

    output = agent_executor.run(input)
    print("output")
    print(output)
    if "Agent stopped" in output:
        return ExecutorResponse(status=ExecutorStatus.TIMED_OUT, output=output)

    elif "Need Help" in output:
        return ExecutorResponse(status=ExecutorStatus.NEEDS_HELP, output=output)

    else:
        return ExecutorResponse(status=ExecutorStatus.COMPLETED, output=output)
