import unittest
import os
import tempfile
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

from src.agent.plans import SinglePlan
from src.location.base import Location
from src.utils.database.base import Tables
from src.utils.database import client
from src.utils.database.sqlite import SqliteDatabase


class SinglePlanPersistenceTests(unittest.IsolatedAsyncioTestCase):
    async def test_from_id_loads_plan_and_location(self):
        plan_id = uuid4()
        agent_id = uuid4()
        location_id = uuid4()
        location = Location(id=location_id, name="Office", description="A room")
        row = {
            "id": str(plan_id),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "agent_id": str(agent_id),
            "description": "Review the notes",
            "location_id": str(location_id),
            "max_duration_hrs": 1.0,
            "stop_condition": "Notes are reviewed",
            "completed_at": None,
            "scratchpad": [],
            "status": "todo",
            "related_event_id": None,
        }
        database = Mock()
        database.get_by_id = AsyncMock(return_value=[row])

        with patch(
            "src.agent.plans.get_database", new=AsyncMock(return_value=database)
        ):
            with patch(
                "src.agent.plans.Location.from_id",
                new=AsyncMock(return_value=location),
            ) as load_location:
                plan = await SinglePlan.from_id(plan_id)

        database.get_by_id.assert_awaited_once_with(Tables.Plans, str(plan_id))
        load_location.assert_awaited_once_with(str(location_id))
        self.assertEqual(plan.id, plan_id)
        self.assertEqual(plan.location, location)

    async def test_delete_removes_the_plan_row(self):
        plan_id = uuid4()
        plan = SinglePlan(
            id=plan_id,
            description="Review the notes",
            max_duration_hrs=1.0,
            stop_condition="Notes are reviewed",
            agent_id=uuid4(),
            location=None,
        )
        database = Mock()
        database.delete = AsyncMock(return_value=None)

        with patch(
            "src.agent.plans.get_database", new=AsyncMock(return_value=database)
        ):
            await plan.delete()

        database.delete.assert_awaited_once_with(Tables.Plans, str(plan_id))


class SqlitePlanPersistenceTests(unittest.IsolatedAsyncioTestCase):
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

    async def asyncTearDown(self):
        self.database_patch.stop()
        await self.database.client.close()
        self.directory.cleanup()

    async def insert_plan(self, location=None):
        plan = SinglePlan(
            description="Review notes",
            max_duration_hrs=1.0,
            stop_condition="Notes reviewed",
            agent_id=uuid4(),
            location=location,
        )
        await self.database.insert(
            Tables.Plans,
            {
                "id": str(plan.id),
                "created_at": plan.created_at.isoformat(),
                "agent_id": str(plan.agent_id),
                "description": plan.description,
                "location_id": str(location.id) if location else None,
                "max_duration_hrs": plan.max_duration_hrs,
                "stop_condition": plan.stop_condition,
                "completed_at": None,
                "scratchpad": [],
                "status": "todo",
                "related_event_id": None,
            },
        )
        return plan

    async def test_loads_real_sqlite_plan_and_location(self):
        location = Location(name="Office", description="A room")
        await self.database.insert(Tables.Locations, location._db_dict())
        original = await self.insert_plan(location)
        loaded = await SinglePlan.from_id(original.id)
        self.assertEqual(loaded.id, original.id)
        self.assertEqual(loaded.agent_id, original.agent_id)
        self.assertEqual(loaded.location, location)

    async def test_loads_real_sqlite_plan_without_location(self):
        original = await self.insert_plan()
        loaded = await SinglePlan.from_id(original.id)
        self.assertEqual(loaded.id, original.id)
        self.assertIsNone(loaded.location)

    async def test_deletes_only_requested_sqlite_plan(self):
        removed = await self.insert_plan()
        retained = await self.insert_plan()
        await removed.delete()
        self.assertEqual(
            await self.database.get_by_id(Tables.Plans, str(removed.id)), []
        )
        self.assertEqual(
            len(await self.database.get_by_id(Tables.Plans, str(retained.id))), 1
        )


if __name__ == "__main__":
    unittest.main()
