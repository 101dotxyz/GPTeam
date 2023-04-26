from datetime import datetime
from enum import Enum
from typing import Optional
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
    step: int
    type: EventType
    description: str
    location_id: UUID
    witness_ids: list[UUID] = []

    def __init__(
        self,
        type: EventType,
        description: str,
        location_id: UUID | str,
        step: int,
        timestamp: datetime = datetime.now(pytz.utc),
        witness_ids: list[UUID] = [],
        id: Optional[UUID] = None,
    ):
        if id is None:
            id = uuid4()

        if isinstance(location_id, str):
            location_id = UUID(location_id)

        if witness_ids is None:
            witness_ids = []

        super().__init__(
            id=id,
            type=type,
            description=description,
            timestamp=timestamp,
            step=step,
            location_id=location_id,
            witness_ids=witness_ids,
        )

    def db_dict(self):
        return {
            "id": str(self.id),
            "timestamp": str(self.timestamp),
            "step": self.step,
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


RECENT_EVENTS_STEPS = 250


class EventsManager(BaseModel):
    """Saves events from the current step and the last step"""

    recent_events: list[Event] = []
    current_step: int = 0
    world_id: str

    def __init__(
        self, world_id: str, events: list[Event] = None, current_step: int = 0
    ):
        if not events:
            (_, data), count = (
                supabase.table("Events")
                .select("*")
                .gte("step", current_step - RECENT_EVENTS_STEPS)
                .execute()
            )
            recent_events = [Event(**event) for event in data]

        super().__init__(
            recent_events=recent_events,
            current_step=current_step,
            world_id=world_id,
        )

    def refresh_events(self, current_step: int = None):
        print_to_console(
            "Refreshing events...", LogColor.GENERAL, f"new step = {current_step}"
        )

        if current_step:
            self.current_step = current_step

        (_, data), _ = (
            supabase.table("Events")
            .select("*, location_id(*)")
            .eq("location_id.world_id", self.world_id)
            .gte("step", self.current_step - RECENT_EVENTS_STEPS)
            .execute()
        )

        events = [
            Event(
                id=event["id"],
                type=event["type"],
                description=event["description"],
                location_id=event["location_id"]["id"],
                step=event["step"],
                timestamp=event["timestamp"],
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
        step: Optional[int] = None,
        event_type: Optional[EventType] = None,
        description: Optional[str] = None,
        witness_ids: Optional[list[UUID]] = None,
        refresh: Optional[bool] = False,
    ) -> list["Event"]:
        if refresh:
            self.refresh_events()

        filtered_events = self.recent_events

        if location_id is not None:
            filtered_events = [
                event
                for event in filtered_events
                if str(event.location_id) == str(location_id)
            ]

        if step is not None:
            filtered_events = [event for event in filtered_events if event.step == step]

        if event_type is not None:
            filtered_events = [
                event for event in filtered_events if event.type == event_type
            ]

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
