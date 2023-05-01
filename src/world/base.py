import asyncio
import os
from collections import deque
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel

from src.event.base import EventsManager

from ..agent.base import Agent
from ..location.base import Location
from ..utils.database.database import supabase
from .context import WorldContext, WorldData


class World(BaseModel):
    id: UUID
    name: str
    locations: list[Location]
    agents: list[Agent]
    context: WorldContext
    agent_queue: asyncio.Queue[Agent]

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, name: str, id: Optional[UUID] = None):
        if id is None:
            id = uuid4()

        # get all locations
        (_, locations), count = (
            supabase.table("Locations").select("*").eq("world_id", id).execute()
        )

        # get all agents
        (_, agents), count = (
            supabase.table("Agents").select("*").eq("world_id", id).execute()
        )

        context = WorldContext(
            world=WorldData(id=id, name=name),
            agents=agents,
            locations=locations,
        )

        locations = [Location(**location) for location in locations]
        agents = [
            Agent.from_db_dict(agent_dict, locations, context=context)
            for agent_dict in agents
        ]

        queue = asyncio.Queue()

        # Add all agents to the queue
        for agent in agents:
            queue.put_nowait(agent)

        super().__init__(
            id=id,
            name=name,
            locations=locations,
            agents=agents,
            context=context,
            agent_queue=queue,
        )

    @classmethod
    def from_id(cls, id: UUID):
        data, count = supabase.table("Worlds").select("*").eq("id", str(id)).execute()
        return cls(**data[1][0])

    @classmethod
    def from_name(cls, name: str):
        (_, worlds), count = (
            supabase.table("Worlds").select("*").eq("name", name).execute()
        )

        if not worlds:
            raise ValueError(f"World with name {name} not found")

        return cls(**worlds[0])

    async def run_step(self):
        # Run agents asynchronously
        tasks = [agent.run_for_one_step() for agent in self.agents]
        await asyncio.gather(*tasks)

    async def run_next_agent(self):
        agent = await self.agent_queue.get()
        await agent.run_for_one_step()
        self.agent_queue.put_nowait(agent)

    async def run_agent_loop(self):
        while True:
            await self.run_next_agent()

    async def run(self):
        concurrency = min(os.cpu_count(), len(self.agents))
        tasks = [self.run_agent_loop() for _ in range(concurrency)]
        await asyncio.gather(*tasks)


def get_worlds():
    data, count = supabase.table("Worlds").select("*").execute()
    return [World(**world) for world in data[1]]
