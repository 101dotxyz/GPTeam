import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel

from ..tools.name import ToolName

# from ..agent.base import Agent
from ..utils.database.database import supabase
from ..utils.parameters import DEFAULT_WORLD_ID


class ActionType(Enum):
    MOVE = "move"
    MESSAGE = "message"


class Location(BaseModel):
    id: UUID
    name: str
    description: str
    available_tools: list[ToolName]
    channel_id: str
    allowed_agent_ids: list[UUID] = []
    world_id: UUID = None

    def __init__(
        self,
        name: str,
        description: str,
        channel_id: int,
        available_tools: list[ToolName] = [],
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
            available_tools=available_tools,
            allowed_agent_ids=allowed_agent_ids,
        )

    def __str__(self):
        return f"{self.name}"

    def db_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "channel_id": self.channel_id,
            "available_tools": [tool.name for tool in self.available_tools],
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

        available_tools = list(
            map(lambda name: ToolName(name), data[0].get("authorized_tools"))
        )

        return cls(**data[0], available_tools=available_tools)

    def context_string(self):
        return f"- {self.name}: {self.description}\n"
