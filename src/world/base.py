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
from ..utils.database.client import supabase
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

    def __init__(
        self,
        name: str,
        context: WorldContext,
        locations=list[Location],
        agents=list[Agent],
        id: Optional[UUID] = None,
    ):
        if id is None:
            id = uuid4()

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
    async def from_id(cls, id: UUID):
        data = (
            await supabase.table("Worlds").select("*").eq("id", str(id)).execute()
        ).data

        # get all locations
        (_, locations), count = (
            await supabase.table("Locations").select("*").eq("world_id", id).execute()
        )

        # get all agents
        (_, agents), count = (
            await supabase.table("Agents").select("*").eq("world_id", id).execute()
        )

        context = await WorldContext.from_data(
            agents=agents, locations=locations, world=WorldData(**data[0])
        )

        locations = [Location(**location) for location in locations]
        agents = [
            await Agent.from_db_dict(agent_dict, locations, context=context)
            for agent_dict in agents
        ]

        return cls(locations=locations, agents=agents, context=context, **data[0])

    @classmethod
    async def from_name(cls, name: str):
        (_, worlds), count = (
            await supabase.table("Worlds").select("*").eq("name", name).execute()
        )

        if not worlds:
            raise ValueError(f"World with name {name} not found")

        return await World.from_id(worlds[0]["id"])

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
