from enum import Enum

from pydantic import BaseModel, Field


class Reaction(Enum):
    REPLAN = "replan"
    MAINTAIN_PLANS = "maintain_plans"


class LLMReactionResponse(BaseModel):
    reaction: Reaction = Field(
        description="The reaction to the message. Must be either 'replan' or 'maintain_plans'. Do not provide anything else."
    )
    thought_process: str = Field(
        description="A summary of what has happened recently, why the reaction was chosen, and, if applicable, how the plans should be changed. Phrased in this format: 'I should change my plans / I should not change my plans because ...'"
    )
