import json
import threading
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

import pytz
from pydantic import BaseModel, Field
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


class MessageEventSubtype(Enum):
    AGENT_TO_AGENT = "agent-to-agent"
    AGENT_TO_HUMAN = "agent-to-human"
    HUMAN_AGENT_REPLY = "human-agent-reply"
    HUMAN_IN_CHANNEL = "human-in-channel"


Subtype = MessageEventSubtype


class Event(BaseModel):
    id: UUID
    timestamp: datetime
    type: EventType
    subtype: Optional[Subtype] = None
    agent_id: Optional[UUID] = None
    description: str
    location_id: UUID
    witness_ids: list[UUID] = []
    metadata: Optional[Any]

    def __init__(
        self,
        type: EventType,
        description: str,
        location_id: UUID | str,
        timestamp: datetime = None,
        witness_ids: list[UUID] = [],
        agent_id: Optional[UUID | str] = None,
        id: Optional[UUID] = None,
        subtype: Optional[Subtype] = None,
        metadata: Optional[Any] = None,
        **kwargs: Any,
    ):
        if id is None:
            id = uuid4()

        if timestamp is None:
            timestamp = datetime.now(pytz.utc)

        if isinstance(location_id, str):
            location_id = UUID(location_id)

        if isinstance(agent_id, str):
            agent_id = UUID(agent_id)

        if witness_ids is None:
            witness_ids = []

        subtype = Subtype(subtype) if subtype is not None else None
        if type == EventType.MESSAGE and subtype != MessageEventSubtype.HUMAN_AGENT_REPLY and agent_id is None:
            raise ValueError("agent_id must be provided for message events")

        super().__init__(
            id=id,
            type=type,
            subtype=subtype,
            description=description,
            timestamp=timestamp,
            agent_id=agent_id,
            location_id=location_id,
            witness_ids=witness_ids,
            metadata=metadata
        )

    def db_dict(self):
        return {
            "id": str(self.id),
            "timestamp": str(self.timestamp),
            "type": self.type.value,
            "subtype": self.subtype.value if self.subtype is not None else None,
            "agent_id": str(self.agent_id),
            "description": self.description,
            "location_id": str(self.location_id),
            "witness_ids": [str(witness_id) for witness_id in self.witness_ids],
            "metadata": self.metadata
        }

    @classmethod
    def from_id(cls, event_id: UUID) -> "Event":
        (_, data), _ = (
            supabase.table("Events")
            .select("*, location_id(*)")
            .eq("id", str(event_id))
            .limit(1)
            .execute()
        )

        event = data[0]

        return cls(
            id=event["id"],
            type=event["type"],
            subtype=event["subtype"],
            description=event["description"],
            location_id=event["location_id"]["id"],
            agent_id=event["agent_id"],
            timestamp=datetime.fromisoformat(event["timestamp"]),
            witness_ids=event["witness_ids"],
            metadata=event["metadata"]
        )

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

REFRESH_INTERVAL_SECONDS = 5


class EventsManager(BaseModel):
    recent_events: list[Event] = []
    world_id: str
    last_refresh: datetime
    refresh_lock: Any

    def __init__(self, world_id: str):
        last_refresh = datetime.now(pytz.utc)
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
                type=EventType(event["type"]),
                subtype=event["subtype"],
                description=event["description"],
                location_id=event["location_id"]["id"],
                timestamp=datetime.fromisoformat(event["timestamp"]),
                witness_ids=event["witness_ids"],
                metadata=event["metadata"],
                agent_id=event["agent_id"],
            )
            for event in data
        ]

        super().__init__(
            recent_events=recent_events,
            world_id=world_id,
            last_refresh=last_refresh,
            refresh_lock=threading.Lock(),
        )

    def refresh_events(self) -> None:
        started_checking_events = datetime.now(pytz.utc)

        with self.refresh_lock:
            print("Refreshing events...")
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
                    type=EventType(event["type"]),
                    subtype=event["subtype"],
                    description=event["description"],
                    location_id=event["location_id"]["id"],
                    agent_id=event["agent_id"],
                    timestamp=datetime.fromisoformat(event["timestamp"]),
                    witness_ids=event["witness_ids"],
                    metadata=event["metadata"],
                )
                for event in data
            ]

            self.recent_events = events
            self.last_refresh = (
                max(
                    datetime.fromisoformat(data[0]["timestamp"]),
                    started_checking_events,
                )
                if len(data) > 0
                else started_checking_events
            )

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
        agent_id: Optional[UUID] = None,
        location_id: Optional[UUID] = None,
        type: Optional[EventType] = None,
        description: Optional[str] = None,
        after: Optional[datetime] = None,
        witness_ids: Optional[list[UUID]] = None,
        force_refresh: Optional[bool] = False,
    ) -> tuple[list[Event], datetime]:
        if (
            (datetime.now(pytz.utc) - self.last_refresh).seconds
            > REFRESH_INTERVAL_SECONDS
        ) or force_refresh:
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

        if agent_id is not None:
            filtered_events = [
                event
                for event in filtered_events
                if str(event.agent_id) == str(agent_id)
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

        return (filtered_events, self.last_refresh)

    def remove_event(self, event_id: UUID):
        self.recent_events = [
            event for event in self.recent_events if event.id != event_id
        ]
        return self.recent_events
