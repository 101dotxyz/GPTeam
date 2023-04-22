from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel

from ..location.base import Location

# from ..agent.base import Agent
from ..utils.database.database import supabase
from ..utils.parameters import DEFAULT_WORLD_ID

# class DiscordMessage(BaseModel):
#     content: str
#     location: Location
#     timestamp: datetime.datetime


class EventType(Enum):
    NON_MESSAGE = "non_message"
    MESSAGE = "message"


class Event(BaseModel):
    id: UUID
    timestamp: Optional[datetime] = None
    step: Optional[int] = None
    type: EventType
    description: str
    location_id: UUID
    witness_ids: list[UUID] = []

    def __init__(
        self,
        type: EventType,
        description: str,
        location_id: UUID,
        witness_ids: list[UUID] = [],
        timestamp: Optional[datetime] = None,
        step: Optional[int] = None,
        id: Optional[UUID] = None,
    ):
        if id is None:
            id = uuid4()

        if witness_ids is None:
            witness_ids = []

        if timestamp is None and step is None:
            raise ValueError("Either timestamp or step must be provided")

        if timestamp:
            # calculate step from timestamp
            pass

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


class EventManager(BaseModel):
    events: list[Event] = []
    current_step: int = 0

    def __init__(self, events: list[Event] = None, current_step: int = 0):
        if not events:
            (_, data), count = (
                supabase.table("Events")
                .select("*")
                .gte("step", current_step)
                .execute()
            )
            events = [Event(**event) for event in data]

        super().__init__(events=events, current_step=current_step)

    # get the next steps events
    def refresh_events(self, current_step: int = None):
        if current_step:
            self.current_step = current_step

        data, count = (
            supabase.table("Events")
            .select("*")
            .gte("step", self.current_step)
            .execute()
        )

        self.events = [Event(**event) for event in list(data[1])]
        return self.events

    def add_event(self, event: Event):
        # add event to database

        (_, witness_data), count = (
            supabase.table("Agents")
            .select("id")
            .eq("location_id", event.location_id)
            .execute()
        )

        event.witness_ids = [witness["id"] for witness in witness_data]

        supabase.table("Events").insert(event.db_dict()).execute()

        # add event to local events list
        self.events.append(event)
        return self.events

    def get_events(self):
        return self.events

    def get_current_step_events(self, location_id: UUID = None):
        step_events = [event for event in self.events if event.step == self.current_step]
        
        if location_id:
            step_events = [event for event in step_events if event.location_id == location_id]

        return step_events

    def get_events_by_location(self, location: Location):
        return [event for event in self.events if event.location_id == location.id]

    def get_events_by_location_id(self, location_id: UUID):
        return [event for event in self.events if event.location_id == location_id]

    def get_events_by_step(self, step: int):
        return [event for event in self.events if event.step == step]

    def remove_event(self, event_id: UUID):
        self.events = [event for event in self.events if event.id != event_id]
        return self.events
