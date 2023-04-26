from uuid import UUID

from pydantic import BaseModel

from ..event.base import EventsManager
from ..world.context import WorldContext


class ToolContext(BaseModel):
    agent_id: UUID
    context: WorldContext
