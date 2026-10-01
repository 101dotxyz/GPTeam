import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

from src.agent.plans import SinglePlan
from src.location.base import Location
from src.utils.database.base import Tables


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


if __name__ == "__main__":
    unittest.main()
