from datetime import datetime
from enum import Enum
from typing import Generic, List, Literal, Optional, TypeVar
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator

from ..location.base import Location
from ..utils.database import supabase


class PlanStatus(Enum):
    IN_PROGRESS = "in_progress"
    TODO = "todo"
    DONE = "done"


class SinglePlan(BaseModel):
    id: UUID
    description: str
    location: Location
    max_duration_hrs: float
    created_at: datetime
    agent_id: UUID
    stop_condition: str
    status: PlanStatus
    scratchpad: Optional[str]
    completed_at: Optional[datetime] = None

    def __init__(
        self,
        description: str,
        location: Location,
        max_duration_hrs: float,
        stop_condition: str,
        agent_id: UUID,
        status: PlanStatus = PlanStatus.TODO,
        scratchpad: Optional[str] = "",
        created_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        id: Optional[UUID] = None,
    ):
        if id is None:
            id = uuid4()

        if created_at is None:
            created_at = datetime.now()

        super().__init__(
            id=id,
            description=description,
            location=location,
            max_duration_hrs=max_duration_hrs,
            created_at=created_at,
            agent_id=agent_id,
            stop_condition=stop_condition,
            completed_at=completed_at,
            status=status,
            scratchpad=scratchpad,
        )

    @classmethod
    def from_id(cls, id: UUID):
        (_, data), (_, count) = (
            supabase.table("Plans").select("*").eq("id", str(id)).execute()
        )

        if not count:
            raise ValueError(f"Plan with id {id} does not exist")

        plan_data = data[0]
        plan_data["location"] = Location.from_id(plan_data["location_id"])
        del plan_data["location_id"]

        return cls(**plan_data)

    def delete(self):
        data, count = supabase.table("Plans").delete().eq("id", str(self.id)).execute()
        return data


class LLMSinglePlan(BaseModel):
    index: int = Field(description="The plan number")
    description: str = Field(description="A description of the plan")
    location_name: str = Field(description="The name of the location")
    start_time: datetime = Field(
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
