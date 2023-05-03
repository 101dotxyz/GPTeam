import re
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from ..event.base import Event, EventType
from ..location.base import Location
from ..utils.general import deduplicate_list
from ..world.context import WorldContext


class AgentMessage(BaseModel):
    content: str
    sender_id: UUID
    sender_name: str
    recipient_id: Optional[UUID] = None
    recipient_name: Optional[str] = None
    location: Location
    timestamp: datetime
    context: WorldContext
    event_id: UUID = None

    @classmethod
    def from_agent_input(cls, agent_input: str, agent_id: UUID, context: WorldContext):
        # get the agent name and location id
        agent_name = context.get_agent_full_name(agent_id)
        agent_location_id = context.get_agent_location_id(agent_id)

        # make the location object
        location = [
            Location(**loc)
            for loc in context.locations
            if str(loc["id"]) == str(agent_location_id)
        ][0]

        # grab the recipient and content
        recipient_name, content = agent_input.split(";")

        # remove the leading and trailing quotation marks if they exist
        content = content.strip().strip("'").strip('"')

        if "everyone" in recipient_name:
            recipient_name = None
            recipient_id = None
        else:
            recipient_id = context.get_agent_id_from_name(recipient_name)

        return cls(
            content=content,
            sender_id=agent_id,
            recipient_id=recipient_id,
            recipient_name=recipient_name,
            location=location,
            context=context,
            timestamp=datetime.now(),
            sender_name=agent_name,
        )

    @classmethod
    def from_event(cls, event: Event, context: WorldContext):
        if event.type != EventType.MESSAGE:
            raise ValueError("Event must be of type message")

        pattern = (
            r"(?P<sender>[\w\s]+) said to (?P<recipient>[\w\s]+): '(?P<message>[^']*)'"
        )
        sender_name, recipient, content = re.findall(pattern, event.description)[0]

        if "everyone" in recipient:
            recipient_name = None
            recipient_id = None
        else:
            recipient_name = recipient.strip()
            recipient_id = context.get_agent_id_from_name(recipient_name)

        location = [
            Location(**loc)
            for loc in context.locations
            if str(loc["id"]) == str(event.location_id)
        ][0]

        return cls(
            content=content,
            sender_id=str(event.agent_id),
            sender_name=sender_name,
            location=location,
            recipient_id=recipient_id,
            recipient_name=recipient_name,
            context=context,
            timestamp=event.timestamp,
            event_id=event.id,
        )

    def to_event(self) -> Event:
        # get the agent_name and location_name

        if self.recipient_id is None:
            event_message = f"{self.sender_name} said to everyone in the {self.location.name}: '{self.content}'"
        else:
            event_message = (
                f"{self.sender_name} said to {self.recipient_name}: '{self.content}'"
            )

        event = Event(
            agent_id=self.sender_id,
            type=EventType.MESSAGE,
            description=event_message,
            location_id=self.location.id,
        )

        self.event_id = event.id

        return event

    # Given a message, get the relevant chat history
    def get_chat_history(self) -> str:
        if self.recipient_id is None:
            (
                recent_message_events_at_location,
                _,
            ) = self.context.events_manager.get_events(
                type=EventType.MESSAGE,
                location_id=self.location.id,
            )

        # get all the messages sent at the location
        (recent_message_events_at_location, _) = self.context.events_manager.get_events(
            type=EventType.MESSAGE,
            location_id=self.location.id,
        )

        messages = [
            AgentMessage.from_event(event, self.context)
            for event in recent_message_events_at_location
        ]

        formatted_messages = [
            f"{m.sender_name}: {m.content} @ {m.timestamp}" for m in messages
        ]

        return "\n".join(formatted_messages)

    def __str__(self):
        if self.recipient_name is None:
            return f"[{self.location.name}] {self.sender_name}: {self.content}"
        else:
            return f"[{self.location.name}] {self.sender_name} to {self.recipient_name}: {self.content}"


class LLMMessageResponse(BaseModel):
    to: str = Field(description="The recipient of the message")
    content: str = Field(description="The content of the message")


def get_latest_messages(messages: list[AgentMessage]) -> list[AgentMessage]:
    messages.sort(key=lambda x: x.timestamp, reverse=True)

    return deduplicate_list(messages, key=lambda x: str(x.sender_id))
