import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel

from src.utils.database.base import Tables
from src.utils.database.client import get_database

from ..tools.name import ToolName

# from ..agent.base import Agent
from ..utils.parameters import DEFAULT_WORLD_ID


class ActionType(Enum):
    MOVE = "move"
    MESSAGE = "message"


class Location(BaseModel):
    id: UUID
    name: str
    description: str
    available_tools: list[ToolName]
    channel_id: Optional[int] = None
    allowed_agent_ids: list[UUID] = []
    world_id: UUID = None

    def __init__(
        self,
        name: str,
        description: str,
        channel_id: Optional[int] = None,
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

        if channel_id is not None and len(str(channel_id)) == 0:
            channel_id = None

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

    def _db_dict(self):
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
    async def from_id(cls, id: UUID):
        data = await (await get_database()).get_by_id(Tables.Locations, str(id))

        if len(data) == 0:
            raise ValueError(f"Location with id {id} not found")

        location = data[0]

        available_tools = list(
            map(lambda name: ToolName(name), location.get("available_tools"))
        )

        return cls(
            id=location["id"],
            name=location["name"],
            description=location["description"],
            available_tools=available_tools,
            channel_id=location["channel_id"],
            allowed_agent_ids=list(
                map(lambda id: UUID(id), location.get("allowed_agent_ids"))
            ),
            world_id=location["world_id"],
        )

    def context_string(self):
        return f"- {self.name}: {self.description}\n"
