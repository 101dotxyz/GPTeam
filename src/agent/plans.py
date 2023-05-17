from datetime import datetime
from enum import Enum
from typing import Generic, List, Literal, Optional, TypeVar
from uuid import UUID, uuid4

import pytz
from pydantic import BaseModel, Field, validator
from src.utils.database.base import Tables

from src.utils.database.client import get_database

from ..location.base import Location
from .message import AgentMessage


class PlanStatus(Enum):
    IN_PROGRESS = "in_progress"
    TODO = "todo"
    DONE = "done"
    FAILED = "failed"


class SinglePlan(BaseModel):
    id: UUID
    description: str
    location: Optional[Location]
    max_duration_hrs: float
    created_at: datetime
    agent_id: UUID
    related_message: Optional[AgentMessage] = None
    stop_condition: str
    status: PlanStatus
    scratchpad: list[dict] = []
    completed_at: Optional[datetime] = None

    def __init__(
        self,
        description: str,
        max_duration_hrs: float,
        stop_condition: str,
        agent_id: UUID,
        status: PlanStatus = PlanStatus.TODO,
        scratchpad: Optional[list[dict]] = [],
        location: Optional[Location] = None,
        created_at: datetime = None,
        completed_at: datetime = None,
        id: UUID = None,
        related_message: AgentMessage = None,
    ):
        if id is None:
            id = uuid4()

        if created_at is None:
            created_at = datetime.now(tz=pytz.utc)

        if scratchpad is None:
            scratchpad = []

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
    async def from_id(cls, id: UUID):
        data = await (await get_database()).get_by_id(Tables.Plan, id)

        if len(data) == 0:
            raise ValueError(f"Plan with id {id} does not exist")

        plan_data = data[0]
        if plan_data["location"] is not None:
            plan_data["location"] = await Location.from_id(plan_data["location_id"])
        else:
            plan_data["location"] = None
        del plan_data["location_id"]

        return cls(**plan_data)

    async def delete(self):
        return await (await get_database()).get_by_id(Tables.Plan, str(self.id))

    def _db_dict(self):
        row = {
            "id": str(self.id),
            "description": self.description,
            "location_id": str(self.location.id),
            "max_duration_hrs": self.max_duration_hrs,
            "created_at": self.created_at.isoformat(),
            "agent_id": str(self.id),
            "related_event_id": str(self.related_message.event_id)
            if self.related_message
            else None,
            "stop_condition": self.stop_condition,
            "status": self.status.value,
            "scratchpad": self.scratchpad,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
        }

        return row

    def make_plan_prompt(self):
        return f"\nDo this: {self.description}\nAt this location: {self.location.name}\nStop when this happens: {self.stop_condition}\nIf do not finish within {self.max_duration_hrs} hours, stop."


class LLMSinglePlan(BaseModel):
    index: int = Field(description="The plan number")
    description: str = Field(description="A description of the plan")
    start_time: datetime = Field(description="The starting time, in UTC, of the plan")
    stop_condition: str = Field(
        description="The condition that will cause this plan to be completed"
    )
    max_duration_hrs: float = Field(
        description="The maximum amount of time to spend on this activity before reassessing"
    )
    location_id: Optional[UUID] = Field(
        description="Optional. The id of the location if known. If included, it must be a valid UUID from the available locations."
    )


class LLMPlanResponse(BaseModel):
    plans: list[LLMSinglePlan] = Field(description="A numbered list of plans")
