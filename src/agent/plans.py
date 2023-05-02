from datetime import datetime
from enum import Enum
from typing import Generic, List, Literal, Optional, TypeVar
from uuid import UUID, uuid4

import pytz
from pydantic import BaseModel, Field, validator

from ..location.base import Location
from .message import AgentMessage
from ..utils.database.database import supabase


class PlanStatus(Enum):
    IN_PROGRESS = "in_progress"
    TODO = "todo"
    DONE = "done"
    FAILED = "failed"

class PlanType(Enum):
    DEFAULT = "default"
    RESPONSE = "response"

class SinglePlan(BaseModel):
    id: UUID
    description: str
    type: PlanType = PlanType.DEFAULT
    location: Location
    max_duration_hrs: float
    created_at: datetime
    agent_id: UUID
    related_message: Optional[AgentMessage] = None
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
        type: PlanType = PlanType.DEFAULT,
        related_message: Optional[AgentMessage] = None,
    ):
        if id is None:
            id = uuid4()

        if created_at is None:
            created_at = datetime.now(tz=pytz.utc)

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
            type=type,
            related_message=related_message,
        )

    def __str__(self):
        return f"[PLAN] - {self.description} at {self.location.name}"

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

    def _db_dict(self):

        row = {
            "id": str(self.id),
            "description": self.description,
            "type": self.type.value,
            "location_id": str(self.location.id),
            "max_duration_hrs": self.max_duration_hrs,
            "created_at": self.created_at.isoformat(),
            "agent_id": str(self.id),
            "related_event_id": str(self.related_message.event_id) if self.related_message else None,
            "stop_condition": self.stop_condition,
            "status": self.status.value,
            "scratchpad": self.scratchpad,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

        return row
    
    
    def make_plan_prompt(self):
        if self.type == PlanType.RESPONSE:
            return f"Do this: {self.description}\nAt this location: {self.location.name}\nStop when this happens: {self.stop_condition}\nIf do not finish within {self.max_duration_hrs} hours, stop.\n\n{self.scratchpad}"
        else:
            # "Respond to what {full_name} said to you."
            return f"{self.description}"

class LLMSinglePlan(BaseModel):
    index: int = Field(description="The plan number")
    description: str = Field(description="A description of the plan")
    location_id: UUID = Field(
        description="The id of the location. Must be a valid UUID from the available locations."
    )
    start_time: datetime = Field(description="The starting time, in UTC, of the plan")
    stop_condition: str = Field(
        description="The condition that will cause this plan to be completed"
    )
    max_duration_hrs: float = Field(
        description="The maximum amount of time to spend on this activity before reassessing"
    )


class LLMPlanResponse(BaseModel):
    plans: list[LLMSinglePlan] = Field(description="A numbered list of plans")
