from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel

from ..location.base import Location
from ..utils.colors import LogColor
from ..utils.database.database import supabase
from ..utils.formatting import print_to_console
from ..utils.parameters import DEFAULT_WORLD_ID, WORLD_ID
from .base import Event, EventType


class ContextManager(BaseModel):
    """Manages context within a world"""

    world_id: str
    current_step_events: list[Event] = []
    last_step_events: list[Event] = []
    current_step: int = 0

    def __init__(
        self,
        world_id: str = WORLD_ID,
        events: list[Event] = None,
        current_step: int = 0,
    ):
        if not events:
            # TODO: Query should only get events for this world
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

    def get_events_by_location(self, location: Location):
        return [
            event
            for event in self.current_step_events
            if event.location_id == location.id
        ]

    def get_events_by_location_id(self, location_id: UUID):
        return [
            event
            for event in self.current_step_events
            if event.location_id == location_id
        ]

    def get_world_state(self):
        return [
            event
            for event in self.current_step_events
            if event.location_id == DEFAULT_WORLD_ID
        ]

    def get_events_by_step(self, step: int):
        return [event for event in self.current_step_events if event.step == step]

    def remove_event(self, event_id: UUID):
        self.current_step_events = [
            event for event in self.current_step_events if event.id != event_id
        ]
        return self.current_step_events
