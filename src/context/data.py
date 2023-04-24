from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from ..memory.base import SingleMemory


class WorldData(BaseModel):
    id: UUID
    name: str


class AgentData(BaseModel):
    id: UUID
    full_name: str
    private_bio: str
    public_bio: str
    directives: Optional[list[str]]
    world_id: UUID
    location_id: UUID
