from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel


class EventType(Enum):
    NON_MESSAGE = "non_message"
    MESSAGE = "message"


class Event(BaseModel):
    id: UUID
    timestamp: datetime
    step: int
    type: EventType
    description: str
    location_id: UUID
    witness_ids: list[UUID] = []

    def __init__(
        self,
        type: EventType,
        description: str,
        location_id: UUID,
        timestamp: datetime,
        step: int,
        witness_ids: list[UUID] = [],
        id: Optional[UUID] = None,
    ):
        if id is None:
            id = uuid4()

        if witness_ids is None:
            witness_ids = []

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
