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
    agent_queue: deque[tuple[Agent, asyncio.Lock]]
    queue_lock: asyncio.Lock

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

        agent_queue = deque([(agent, asyncio.Lock()) for agent in agents])
        queue_lock = asyncio.Lock()

        super().__init__(
            id=id,
            name=name,
            locations=locations,
            agents=agents,
            context=context,
            agent_queue=agent_queue,
            queue_lock=queue_lock,
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

    async def run_agent_cycle(self):
        while True:
            async with self.queue_lock:
                if not self.agent_queue:
                    continue
                agent, agent_lock = self.agent_queue.popleft()

            # Attempt to acquire the agent's lock; if not acquired, move on to the next agent
            if agent_lock.locked():
                async with self.queue_lock:
                    self.agent_queue.append((agent, agent_lock))
                continue

            await self.run_step_for_agent(agent, agent_lock)

            async with self.queue_lock:
                self.agent_queue.append((agent, agent_lock))

    async def run(self):
        tasks = [self.run_agent_cycle() for _ in range(os.cpu_count())]
        await asyncio.gather(*tasks)


def get_worlds():
    data, count = supabase.table("Worlds").select("*").execute()
    return [World(**world) for world in data[1]]
