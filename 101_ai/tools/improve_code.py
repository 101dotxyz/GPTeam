import json

from colorama import Fore

from . import AgentTool
from .llm_function import LLMFunctionTool


class ImproveCodeTool(LLMFunctionTool):
    def __init__(self):

        super().__init__(
            name=AgentTool.ImproveCode.value,
            definition="def generate_improved_code(suggestions: List[str], code: str) -> str:",
            description= """Improves the provided code based on the suggestions provided, making no other changes."""
        )
