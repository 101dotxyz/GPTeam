import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel

from ..location.base import Event, Location

from ..agent.base import Agent

# from ..agent.base import Agent
from ..world.base import Event
from ..utils.database import supabase


class World(BaseModel):
    id: UUID
    name: str
    current_step: int
    agents: list[Agent] = []

    def __init__(self, name: str, current_step: int = 0, id: Optional[UUID] = None):
        if id is None:
            id = uuid4()

        super().__init__(id=id, name=name, current_step=current_step)
        self.load_agents()

    @property
    def locations(self) -> list[Location]:
        # get all locations with this id as world_id
        data, count = (
            supabase.table("Locations").select("*").eq("world_id", self.id).execute()
        )
        return [Location(**location) for location in data[1]]

    @classmethod
    def from_id(cls, id: UUID):
        data, count = supabase.table("Worlds").select("*").eq("id", str(id)).execute()
        return cls(**data[1][0])

    @classmethod
    def from_name(cls, name: str):
        data, count = supabase.table("Worlds").select("*").eq("name", name).execute()
        return cls(**data[1][0])

    def get_agents(self):
        data, count = supabase.table("Agents").select("*").eq("world_id", str(self.id)).execute()
        agents = [Agent(**agent) for agent in data[1]]
        return agents

    def load_agents(self):
        self.agents = self.get_agents()

    # def get_agent_actions(self) -> list[AgentAction]:
    #     # will need to parse some args
    #     return [agent.act() for agent in self.agents]

    def get_witnesses(self, location: Location) -> list[UUID]:
        return [
            agent for agent in self.agents if self.state.positions[agent] == location
        ]

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
        for agent in self.agents:
            agent.run()
        self.current_step += 1
        supabase.table("Worlds").update({"current_step": self.current_step}).eq("id", str(self.id)).execute()

    def run(self, steps: int = 1):
        for _ in range(steps):
            self.run_step()


def get_worlds():
    data, count = supabase.table("Worlds").select("*").execute()
    return [World(**world) for world in data[1]]
