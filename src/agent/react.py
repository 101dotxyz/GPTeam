from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field
from .plans import LLMSinglePlan


class Reaction(Enum):
    CONTINUE = "continue"
    POSTPONE = "postpone"
    CANCEL = "cancel"

class LLMReactionResponse(BaseModel):
    reaction: Reaction = Field(
        description="The reaction to the message. Must be one of 'continue', 'postpone', or 'cancel'. Do not provide anything else."
    )
    thought_process: str = Field(
        description="A summary of what has happened recently, why the reaction was chosen, and, if applicable, what should be done instead of the current plan. Phrased in this format: 'I should continue/postpone/cancel my plan because ...'"
    )
    new_plan: Optional[LLMSinglePlan] = Field(
        None,
        description="If the reaction is 'postpone', this field should be included to specify what the new plan should be."
    )

