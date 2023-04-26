from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel

from ..location.base import Location
from ..utils.formatting import print_to_console
from ..utils.colors import LogColor
from ..utils.database.database import supabase
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
        location_id: UUID,
        timestamp: datetime,
        step: int,
        witness_ids: list[UUID] = [],
        id: Optional[UUID] = None,
    ):
        if id is None:
            id = uuid4()

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


class EventsManager(BaseModel):
    """Saves events from the current step and the last step"""

    current_step_events: list[Event] = []
    last_step_events: list[Event] = []
    current_step: int = 0

    def __init__(self, events: list[Event] = None, current_step: int = 0):
        if not events:
            (_, data), count = (
                supabase.table("Events").select("*").gte("step", current_step).execute()
            )
            current_step_events = [Event(**event) for event in data]

        super().__init__(
            current_step_events=current_step_events, current_step=current_step
        )

    # get the next steps events, save last step
    def refresh_events(self, current_step: int = None):
        print_to_console(
            "Refreshing events...", LogColor.GENERAL, f"new step = {current_step}"
        )

        if current_step:
            self.current_step = current_step

        self.last_step_events = self.current_step_events

        data, count = (
            supabase.table("Events")
            .select("*")
            .gte("step", self.current_step)
            .execute()
        )

        self.current_step_events = [Event(**event) for event in list(data[1])]
        return self.current_step_events

    def add_event(self, event: Event):
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
        self.current_step_events.append(event)

        return self.current_step_events

    def get_events(self):
        return self.current_step_events

    def get_events_by_location(self, location: Location, step: StepToUse):
        if step == 'last':
            return [event for event in self.last_step_events if event.location_id == location.id]
        else:
            return [event for event in self.current_step_events if event.location_id == location.id]

    def get_events_by_location_id(self, location_id: UUID):
        return [
            event
            for event in self.current_step_events
            if event.location_id == location_id
        ]

    def get_events_by_step(self, step: int):
        return [event for event in self.current_step_events if event.step == step]

    def remove_event(self, event_id: UUID):
        self.current_step_events = [
            event for event in self.current_step_events if event.id != event_id
        ]
        return self.current_step_events
