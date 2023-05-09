from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from ..event.base import EventsManager
from ..world.context import WorldContext
from ..memory.base import SingleMemory


class ToolContext(BaseModel):
    agent_id: UUID
    context: WorldContext
    memories: Optional[list[SingleMemory]]
