from pydantic import BaseModel
from uuid import UUID

from ..world.context import WorldContext
from ..event.base import EventsManager

class ToolContext(BaseModel):
    agent_id: UUID
    world_context: WorldContext
    events_manager: EventsManager