from colorama import Fore

from . import AgentTool
from .llm_function import LLMFunctionTool


class MissingInformationTool(LLMFunctionTool):
    def __init__(self):
        super().__init__(
            name=AgentTool.MissingInformation.value,
            definition="def get_missing_information(task_specification: str) -> List[str]:",
            description= """Finds missing pieces of information that are required to complete the task and are missing from the provided tak specification."""
        )
