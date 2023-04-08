from enum import Enum


class AgentTool(Enum):
    Search = "SEARCH"
    AskUserQuestion = "ASK_USER_QUESTION"
    EvaluateCode = "EVALUATE_CODE"
    ImproveCode = "IMPROVE_CODE"
    