from colorama import Fore

from . import AgentTool
from .llm_function import LLMFunctionTool


class EvaluateSpecTool(LLMFunctionTool):
    def __init__(self):
        super().__init__(
            name=AgentTool.EvaluateCode.value,
            definition="def analyze_code(code: str) -> List[str]:",
            description= """Analyzes the given code and returns a list of suggestions for improvements."""
        )
