from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

import pytz
from pydantic import BaseModel
from sqlalchemy import desc

from ..utils.colors import LogColor
from ..utils.database.database import supabase
from ..utils.formatting import print_to_console
from ..utils.parameters import DEFAULT_WORLD_ID

# class DiscordMessage(BaseModel):
#     content: str
#     location: Location
#     timestamp: datetime.datetime


class StepToUse(Enum):
    CURRENT = "current"
    NEXT = "next"


class EventType(Enum):
    NON_MESSAGE = "non_message"
    MESSAGE = "message"


class Event(BaseModel):
    id: UUID
    timestamp: datetime
    type: EventType
    agent_id: Optional[UUID] = None
    description: str
    location_id: UUID
    witness_ids: list[UUID] = []

    def __init__(
        self,
        type: EventType,
        description: str,
        location_id: UUID | str,
        timestamp: datetime = datetime.now(pytz.utc),
        witness_ids: list[UUID] = [],
        agent_id: Optional[UUID | str] = None,
        id: Optional[UUID] = None,
        **kwargs: Any,
    ):
        if id is None:
            id = uuid4()

        if isinstance(location_id, str):
            location_id = UUID(location_id)

        if isinstance(agent_id, str):
            agent_id = UUID(agent_id)

        if witness_ids is None:
            witness_ids = []

        super().__init__(
            id=id,
            type=type,
            description=description,
            timestamp=timestamp,
            agent_id=agent_id,
            location_id=location_id,
            witness_ids=witness_ids,
        )

    def db_dict(self):
        return {
            "id": str(self.id),
            "timestamp": str(self.timestamp),
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


RECENT_EVENTS_BUFFER = 500


class EventsManager(BaseModel):
    recent_events: list[Event] = []
    world_id: str

    def __init__(self, world_id: str, events: list[Event] = None):
        if not events:
            (_, data), _ = (
                supabase.table("Events")
                .select("*, location_id(*)")
                .eq("location_id.world_id", world_id)
                .order("timestamp", desc=True)
                .limit(RECENT_EVENTS_BUFFER)
                .execute()
            )
            recent_events = [
                Event(
                    type=event["type"],
                    description=event["description"],
                    location_id=event["location_id"]["id"],
                    timestamp=datetime.fromisoformat(event["timestamp"]),
                    witness_ids=event["witness_ids"],
                )
                for event in data
            ]

        super().__init__(
            recent_events=recent_events,
            world_id=world_id,
        )

    def refresh_events(self) -> list[Event]:
        (_, data), _ = (
            supabase.table("Events")
            .select("*, location_id(*)")
            .eq("location_id.world_id", self.world_id)
            .order("timestamp", desc=True)
            .limit(RECENT_EVENTS_BUFFER)
            .execute()
        )

        events = [
            Event(
                id=event["id"],
                type=event["type"],
                description=event["description"],
                location_id=event["location_id"]["id"],
                timestamp=datetime.fromisoformat(event["timestamp"]),
                witness_ids=event["witness_ids"],
            )
            for event in data
        ]

        self.recent_events = events

        return self.recent_events

    def add_event(self, event: Event) -> None:
        """Adds an event in the current step to the DB and local object"""

        # get the witnesses
        (_, witness_data), count = (
            supabase.table("Agents")
            .select("id")
            .eq("location_id", event.location_id)
            .execute()
        )

        event.witness_ids = [witness["id"] for witness in witness_data]

        supabase.table("Events").insert(event.db_dict()).execute()

        # add event to local events list
        self.recent_events.append(event)

    def get_events(
        self,
        location_id: Optional[UUID] = None,
        type: Optional[EventType] = None,
        description: Optional[str] = None,
        after: Optional[datetime] = None,
        witness_ids: Optional[list[UUID]] = None,
        refresh: Optional[bool] = False,
    ) -> list[Event]:
        if refresh:
            self.refresh_events()

        filtered_events = self.recent_events

        if after is not None:
            filtered_events = [
                event for event in filtered_events if event.timestamp > after
            ]

        if location_id is not None:
            filtered_events = [
                event
                for event in filtered_events
                if str(event.location_id) == str(location_id)
            ]

        if type is not None:
            filtered_events = [event for event in filtered_events if event.type == type]

        if description is not None:
            filtered_events = [
                event for event in filtered_events if event.description == description
            ]

        if witness_ids is not None:
            filtered_events = [
                event
                for event in filtered_events
                if set(list(map(str, witness_ids))).issubset(
                    set(list(map(str, event.witness_ids)))
                )
            ]

        return filtered_events

    def remove_event(self, event_id: UUID):
        self.recent_events = [
            event for event in self.recent_events if event.id != event_id
        ]
        return self.recent_events
