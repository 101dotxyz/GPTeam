import os
import tempfile
import unittest
from datetime import datetime, timezone
from unittest.mock import patch
from uuid import uuid4

from src.agent.base import Agent
from src.event.base import EventsManager
from src.location.base import Location
from src.memory.base import MemoryType, SingleMemory
from src.tools.name import ToolName
from src.utils.database import client
from src.utils.database.base import Tables
from src.utils.database.sqlite import SqliteDatabase
from src.world.context import WorldContext, WorldData


class AgentLookupTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.directory = tempfile.TemporaryDirectory()
        previous_directory = os.getcwd()
        try:
            os.chdir(self.directory.name)
            self.database = await SqliteDatabase.create()
        finally:
            os.chdir(previous_directory)
        self.database_patch = patch.object(client, "database", self.database)
        self.database_patch.start()
        self.world_id = uuid4()
        self.agent_id = uuid4()
        self.location = Location(
            name="Office",
            description="A room",
            world_id=self.world_id,
            available_tools=[ToolName.SEARCH],
        )
        location_row = self.location._db_dict()
        location_row["available_tools"] = [
            tool.value for tool in self.location.available_tools
        ]
        await self.database.insert(Tables.Locations, location_row)
        self.context = WorldContext(
            agents=[],
            locations=[],
            events_manager=EventsManager(str(self.world_id), []),
            world=WorldData(id=str(self.world_id), name="Test world"),
        )

    async def asyncTearDown(self):
        self.database_patch.stop()
        await self.database.client.close()
        self.directory.cleanup()

    async def insert_agent(self, plan_ids):
        await self.database.insert(
            Tables.Agents,
            {
                "id": str(self.agent_id),
                "full_name": "Alex",
                "private_bio": "Private",
                "public_bio": "Public",
                "directives": ["Read notes"],
                "last_checked_events": datetime.now(timezone.utc).isoformat(),
                "authorized_tools": [ToolName.SEARCH.value],
                "ordered_plan_ids": [str(id) for id in plan_ids],
                "location_id": str(self.location.id),
                "world_id": str(self.world_id),
                "discord_bot_token": None,
            },
        )

    async def test_loads_related_state_and_tool_authorization(self):
        first, second = uuid4(), uuid4()
        for id in [second, first]:
            await self.database.insert(
                Tables.Plans,
                {
                    "id": str(id),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "agent_id": str(self.agent_id),
                    "description": "Read notes",
                    "location_id": str(self.location.id),
                    "max_duration_hrs": 1.0,
                    "stop_condition": "Read",
                    "scratchpad": [],
                    "status": "todo",
                    "related_event_id": None,
                    "completed_at": None,
                },
            )
        memory = SingleMemory(
            agent_id=self.agent_id,
            type=MemoryType.OBSERVATION,
            description="Notes exist",
            importance=1,
            embedding=[1.0, 0.0],
        )
        await self.database.insert(Tables.Memories, memory.db_dict())
        await self.insert_agent([first, second])
        loaded = await Agent.from_id(self.agent_id, self.context)
        self.assertEqual(loaded.id, self.agent_id)
        self.assertEqual(loaded.location, self.location)
        self.assertEqual([plan.id for plan in loaded.plans], [first, second])
        self.assertEqual([item.id for item in loaded.memories], [memory.id])
        self.assertEqual(loaded.authorized_tools, [ToolName.SEARCH])

    async def test_preserves_requested_subclass(self):
        class SpecializedAgent(Agent):
            pass

        await self.insert_agent([])
        loaded = await SpecializedAgent.from_id(self.agent_id, self.context)
        self.assertIsInstance(loaded, SpecializedAgent)

    async def test_missing_agent_has_clear_error(self):
        with self.assertRaisesRegex(ValueError, "No agent with that id"):
            await Agent.from_id(uuid4(), self.context)


if __name__ == "__main__":
    unittest.main()
