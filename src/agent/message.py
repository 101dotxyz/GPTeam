from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from ..event.base import Event, EventType
from ..location.base import Location
from ..world.context import WorldContext


class AgentMessage(BaseModel):
    content: str
    sender: str
    recipient: Optional[str] = None
    location: Location
    timestamp: datetime

    @classmethod
    def from_event(cls, event: Event, context: WorldContext):
        if event.type != EventType.MESSAGE:
            raise ValueError("Event must be of type message")

        if ":" in event.description:
            recipient, content = event.description.split(":", 1)
        else:
            recipient = None
            content = event.description

        if recipient is not None:
            recipient = context.get_agent_id_from_full_name(recipient)

        location = [
            Location(loc) for loc in context.locations if loc.id == event.location_id
        ][0]

        return cls(
            content=content,
            sender=str(event.agent_id),
            location=location,
            recipient=recipient,
            timestamp=event.timestamp,
        )

    def get_chat_history(self) -> list["AgentMessage"]:
        if self.recipient is None:
            recent_message_events_at_location = self.context.events_manager.get_events(
                type=EventType.MESSAGE,
                location_id=self.location.id,
            )

            recent_messages_at_location = [
                AgentMessage.from_event(event, self.context)
                for event in recent_message_events_at_location
            ]

            return recent_messages_at_location

    def __str__(self):
        return f"{self.sender}: {self.content}"
