import datetime
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class SinglePlan(BaseModel):
    id: UUID
    description: str
    max_duration_hrs: float
    created_at: datetime.datetime
    agent_id: UUID
    stop_condition: str
    completed_at: Optional[datetime.datetime] = None

    def __init__(
        self,
        description: str,
        max_duration_hrs: float,
        stop_condition: str,
        agent_id: UUID,
    ):
        super().__init__(
            id=uuid4(),
            description=description,
            max_duration_hrs=max_duration_hrs,
            created_at=datetime.datetime.now(),
            agent_id=agent_id,
            stop_condition=stop_condition,
            completed_at=None,
        )


class LLMSinglePlan(BaseModel):
    index: int = Field(description="The plan number")
    description: str = Field(description="A description of the plan")
    start_time: datetime.datetime = Field(
        description="The starting time, using this strftime format string: '%H:%M - %m/%d/%y'"
    )
    stop_condition: str = Field(
        description="The condition that will cause this plan to be completed"
    )
    max_duration_hrs: float = Field(
        description="The maximum amount of time to spend on this activity before reassessing"
    )


class LLMPlanResponse(BaseModel):
    plans: list[LLMSinglePlan] = Field(description="A numbered list of plans")
