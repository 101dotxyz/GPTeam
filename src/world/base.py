import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel

from src.event.base import Event, EventManager

from ..agent.base import Agent
from ..location.base import Location
from ..utils.database.database import supabase


class World(BaseModel):
    id: UUID
    name: str
    current_step: int
    _locations: list[Location]
    agents: list[Agent] = []
    event_manager: EventManager

    def __init__(self, name: str, current_step: int = 0, id: Optional[UUID] = None):
        if id is None:
            id = uuid4()

        super().__init__(
            id=id,
            name=name,
            current_step=current_step,
            event_manager=EventManager(starting_step=current_step),
        )
        self.load_agents()

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

    def get_agents(self) -> list[Agent]:
        data, count = (
            supabase.table("Agents").select("*").eq("world_id", str(self.id)).execute()
        )
        agents = [Agent.from_id(agent["id"]) for agent in data[1]]
        return agents

    def load_agents(self):
        self.agents = self.get_agents()

    # def get_agent_actions(self) -> list[AgentAction]:
    #     # will need to parse some args
    #     return [agent.act() for agent in self.agents]

    def get_witnesses(self, location: Location) -> list[UUID]:
        return [agent for agent in self.agents if agent.location.id == location.id]

    def update(self) -> None:
        # very rough draft of how this might work

        discord_messages = self.get_discord_messages()

        for message in discord_messages:
            witnesses = self.get_witnesses(message.location)
            event = Event.from_discord_message(message, witnesses)
            self.events.append(event)

        agent_actions = self.get_agent_actions()

        for action in agent_actions:
            witnesses = self.get_witnesses(action.location)
            event = Event.from_agent_action(action, witnesses)
            self.events.append(event)

        new_state = self.state.copy()

        for action in agent_actions:
            new_state.positions[action.agent] = action.location

        self.history.append(new_state)

    def run_step(self):
        self.event_manager.refresh_events()
        for agent in self.agents:
            agent.run_for_one_step(self.event_manager)
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
