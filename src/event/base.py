from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel


# from ..agent.base import Agent
from ..utils.database import supabase
from ..utils.parameters import DEFAULT_WORLD_ID


# class DiscordMessage(BaseModel):
#     content: str
#     location: Location
#     timestamp: datetime.datetime


class EventType(Enum):
    NON_MESSAGE = "non_message"
    MESSAGE = "message"


class Event(BaseModel):
    id: UUID
    timestamp: Optional[datetime] = None
    step: int
    type: EventType
    description: str
    location_id: UUID
    witness_ids: list[UUID]

    def __init__(
        self,
        type: EventType,
        description: str,
        location_id: UUID,
        witness_ids: list[UUID],
        timestamp: Optional[datetime] = None,
        step: Optional[int] = None,
        id: Optional[UUID] = None,
    ):
        if id is None:
            id = uuid4()

        if timestamp is None and step is None:
            raise ValueError("Either timestamp or step must be provided")

        if timestamp:
            # calculate step from timestamp
            pass

        super().__init__(
            id=id,
            type=type,
            description=description,
            timestamp=timestamp,
            step=step,
            location_id=location_id,
            witness_ids=witness_ids,
        )

    def db_dict(self):
        return {
            "id": str(self.id),
            "timestamp": str(self.timestamp),
            "step": self.step,
            "type": self.type.value,
            "description": self.description,
            "location_id": str(self.location_id),
            "witness_ids": [str(witness_id) for witness_id in self.witness_ids],
        }

    # @staticmethod
    # def from_discord_message(message: DiscordMessage, witnesses: list[UUID]) -> "Event":
    #     # parse user provided message into an event
    #     # witnesses are all agents who were in the same location as the message
    #     pass

    # @staticmethod
    # def from_agent_action(action: AgentAction, witnesses: list[UUID]) -> "Event":
    #     # parse agent action into an event
    #     pass
