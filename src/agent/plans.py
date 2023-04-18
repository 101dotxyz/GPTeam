import datetime
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from ..utils.database import supabase


class SinglePlan(BaseModel):
    id: UUID
    description: str
    location_id: UUID
    max_duration_hrs: float
    created_at: datetime.datetime
    agent_id: UUID
    stop_condition: str
    completed_at: Optional[datetime.datetime] = None

    def __init__(
        self,
        description: str,
        location_id: UUID,
        max_duration_hrs: float,
        stop_condition: str,
        agent_id: UUID,
        created_at: Optional[datetime.datetime] = None,
        completed_at: Optional[datetime.datetime] = None,
        id: Optional[UUID] = None,
    ):
        if id is None:
            id = uuid4()

        if created_at is None:
            created_at = datetime.datetime.now()

        super().__init__(
            id=id,
            description=description,
            location_id=location_id,
            max_duration_hrs=max_duration_hrs,
            created_at=created_at,
            agent_id=agent_id,
            stop_condition=stop_condition,
            completed_at=completed_at,
        )

    @classmethod
    def from_id(cls, id: UUID):
        data, count = supabase.table("Plans").select("*").eq("id", str(id)).execute()
        return cls(**data[1][0])

    def delete(self):
        data, count = supabase.table("Plans").delete().eq("id", str(self.id)).execute()
        return data


class LLMSinglePlan(BaseModel):
    index: int = Field(description="The plan number")
    description: str = Field(description="A description of the plan")
    location_name: str = Field(description="The name of the location")
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
