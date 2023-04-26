import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel

from src.event.base import EventsManager
from ..agent.base import Agent
from ..location.base import Location
from ..utils.database.database import supabase
from .context import WorldContext


class World(BaseModel):
    id: UUID
    name: str
    current_step: int
    locations: list[Location]
    agents: list[Agent]
    events_manager: EventsManager
    context: WorldContext

    @property
    def context(self):
        return WorldContext(
            agents = [agent._db_dict() for agent in self.agents],
            locations = [location._db_dict() for location in self.locations]
        )

    def __init__(self, name: str, current_step: int = 0, id: Optional[UUID] = None):
        if id is None:
            id = uuid4()

        events_manager = EventsManager(current_step=current_step)

        # get all locations
        (_, locations), count = (
            supabase.table("Locations")
            .select("*")
            .eq("world_id", id)
            .execute()
        )
        locations = [Location(**location) for location in locations]

        # get all agents
        (_, agents), count = (
            supabase.table("Agents")
            .select("*")
            .eq("world_id", id)
            .execute()
        )
        agents = [Agent.from_db_dict(agent_dict, locations) for agent_dict in agents]

        context = WorldContext(
            agents = [agent._db_dict() for agent in agents],
            locations = [location._db_dict() for location in locations]
        )

        super().__init__(
            id=id,
            name=name,
            current_step=current_step,
            locations=locations,
            agents=agents,
            events_manager=events_manager,
            context = context
        )

    @classmethod
    def from_id(cls, id: UUID):
        data, count = supabase.table("Worlds").select("*").eq("id", str(id)).execute()
        return cls(**data[1][0])

    @classmethod
    def from_name(cls, name: str):
        (_, worlds), count = supabase.table("Worlds").select("*").eq("name", name).execute()

        if not worlds:
            raise ValueError(f"World with name {name} not found")

        return cls(**worlds[0])

    def run_step(self):

        # Refresh events for this step
        self.events_manager.refresh_events(self.current_step)

        # Run agents
        for agent in self.agents:
        
            agent.run_for_one_step(
                self.events_manager, self.context
            )

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
