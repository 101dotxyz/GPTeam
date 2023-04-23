import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel

from src.event.base import EventsManager
from ..agent.base import AgentsManager
from ..location.base import Location
from ..utils.database.database import supabase


class World(BaseModel):
    id: UUID
    name: str
    current_step: int
    _locations: list[Location]
    agents_manager: AgentsManager
    events_manager: EventsManager

    def __init__(self, name: str, current_step: int = 0, id: Optional[UUID] = None):
        if id is None:
            id = uuid4()

        super().__init__(
            id=id,
            name=name,
            current_step=current_step,
            agents_manager=AgentsManager(world_id=id),
            events_manager=EventsManager(current_step=current_step),
        )

    @property
    def locations(self) -> list[Location]:
        if self._locations:
            return self._locations

        # get all locations with this id as world_id
        data, count = (
            supabase.table("Locations").select("*").eq("world_id", self.id).execute()
        )
        self._locations = [Location(**location) for location in data[1]]

        return self._locations

    @classmethod
    def from_id(cls, id: UUID):
        data, count = supabase.table("Worlds").select("*").eq("id", str(id)).execute()
        return cls(**data[1][0])

    @classmethod
    def from_name(cls, name: str):
        data, count = supabase.table("Worlds").select("*").eq("name", name).execute()
        return cls(**data[1][0])

    def run_step(self):

        # Refresh events
        self.events_manager.refresh_events(self.current_step)

        # Run agents
        self.agents_manager.run_for_one_step(self.events_manager)

        # Increment step
        self.current_step += 1
        supabase.table("Worlds").update({"current_step": self.current_step}).eq(
            "id", str(self.id)
        ).execute()

    def run(self, steps: int = 1):
        for _ in range(steps):
            self.run_step()


def get_worlds():
    data, count = supabase.table("Worlds").select("*").execute()
    return [World(**world) for world in data[1]]
