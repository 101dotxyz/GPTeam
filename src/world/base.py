import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel

from src.event.base import EventManager
from ..agent.base import AgentManager
from ..location.base import Location
from ..utils.database.database import supabase


class World(BaseModel):
    id: UUID
    name: str
    current_step: int
    _locations: list[Location]
    agent_manager: AgentManager
    event_manager: EventManager

    def __init__(self, name: str, current_step: int = 0, id: Optional[UUID] = None):
        if id is None:
            id = uuid4()

        super().__init__(
            id=id,
            name=name,
            current_step=current_step,
            agent_manager=AgentManager(world_id=id),
            event_manager=EventManager(starting_step=current_step),
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
        self.event_manager.refresh_events(self.current_step)

        # Run agents
        self.agent_manager.run_for_one_step(self.event_manager)

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
