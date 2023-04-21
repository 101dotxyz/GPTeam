import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel

# from ..agent.base import Agent
from ..utils.database.database import supabase
from ..utils.parameters import DEFAULT_WORLD_ID


class ActionType(Enum):
    MOVE = "move"
    MESSAGE = "message"


# class AgentAction(BaseModel):
#     type: ActionType
#     agent: Agent
#     step: int
#     location: Optional["Location"] = None

#     def __init__(self, agent: Agent, step: int, location: Optional["Location"] = None):
#         super().__init__(agent=agent, step=step, location=location)


class Location(BaseModel):
    id: UUID
    name: str
    description: str
    channel_id: str
    allowed_agent_ids: list[UUID] = []
    world_id: UUID = None

    def __init__(
        self,
        name: str,
        description: str,
        channel_id: int,
        allowed_agent_ids: list[UUID] = None,
        id: Optional[UUID] = None,
        world_id: UUID = None,
    ):
        if id is None:
            id = uuid4()

        if world_id is None:
            world_id = DEFAULT_WORLD_ID

        if allowed_agent_ids is None:
            allowed_agent_ids = []

        super().__init__(
            id=id,
            world_id=world_id,
            name=name,
            description=description,
            channel_id=channel_id,
            allowed_agent_ids=allowed_agent_ids,
        )

    def db_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "channel_id": self.channel_id,
            "allowed_agent_ids": [str(agent_id) for agent_id in self.allowed_agent_ids],
            "world_id": str(self.world_id),
        }

    @classmethod
    def from_id(cls, id: UUID):
        (_, data), _ = (
            supabase.table("Locations").select("*").eq("id", str(id)).execute()
        )

        if len(data) == 0:
            raise ValueError(f"Location with id {id} not found")

        return cls(**data[0])

    @classmethod
    def from_name(cls, name: str):
        data, count = supabase.table("Locations").select("*").eq("name", name).execute()
        if count == 0:
            raise ValueError(f"Location with name {name} not found")
        return cls(**data[1][0])
