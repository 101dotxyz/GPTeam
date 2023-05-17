import asyncio
import os
from collections import deque
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel

from src.event.base import EventsManager
from src.utils.database.base import Tables
from src.utils.database.client import get_database

from ..agent.base import Agent
from ..location.base import Location
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
        database = await get_database()
        data = await database.get_by_id(Tables.Worlds, str(id))

        # get all locations
        locations = await database.get_by_field(Tables.Locations, "world_id", str(id))

        # get all agents
        agents = await database.get_by_field(Tables.Agents, "world_id", str(id))

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
        worlds = await (await get_database()).get_by_field(Tables.Worlds, "name", name)

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
        # Delete previous agents
        agents_folder = os.path.join(os.getcwd(), "agents")
        if not os.path.exists(agents_folder):
            os.mkdir(agents_folder)
        for agent in os.listdir(agents_folder):
            os.remove(os.path.join(agents_folder, agent))

        concurrency = min(os.cpu_count(), len(self.agents))
        tasks = [self.run_agent_loop() for _ in range(concurrency)]
        await asyncio.gather(*tasks)
