import unittest
from uuid import uuid4
import aiosqlite

from src.agent.plans import SinglePlan
from src.location.base import Location
from src.utils.database.base import Tables
from src.utils.database.sqlite import SqliteDatabase, dict_factory


class PlanDatabaseDictionaryTests(unittest.TestCase):
    def test_plan_row_keeps_owning_agent_id(self):
        agent_id = uuid4()
        plan = SinglePlan(
            description="Review the map",
            max_duration_hrs=1,
            stop_condition="The map is reviewed",
            agent_id=agent_id,
            location=Location(
                name="Library",
                description="A quiet room",
                available_tools=[],
            ),
        )

        row = plan._db_dict()

        self.assertEqual(row["agent_id"], str(agent_id))
        self.assertNotEqual(row["agent_id"], row["id"])


class SqlitePlanOwnershipTests(unittest.IsolatedAsyncioTestCase):
    async def test_saved_plans_are_retrievable_by_their_owner(self):
        database = SqliteDatabase()
        database.client = await aiosqlite.connect(":memory:")
        database.client.row_factory = dict_factory
        try:
            await database.client.execute(
                """
                CREATE TABLE plans (
                    id TEXT PRIMARY KEY, description TEXT, location_id TEXT,
                    max_duration_hrs REAL, created_at TEXT, agent_id TEXT,
                    related_event_id TEXT, stop_condition TEXT, status TEXT,
                    scratchpad TEXT, completed_at TEXT
                )
            """
            )
            owner, other_owner = uuid4(), uuid4()
            plans = []
            for agent_id in [owner, other_owner, owner]:
                plan = SinglePlan(
                    description="Review map",
                    max_duration_hrs=1,
                    stop_condition="Reviewed",
                    agent_id=agent_id,
                    location=Location(name="Library", description="A room"),
                )
                plans.append(plan)
                await database.insert(Tables.Plans, plan._db_dict())
            rows = await database.get_by_field(Tables.Plans, "agent_id", str(owner))
            self.assertEqual(
                {row["id"] for row in rows}, {str(plans[0].id), str(plans[2].id)}
            )
            other_rows = await database.get_by_field(
                Tables.Plans, "agent_id", str(other_owner)
            )
            self.assertEqual([row["id"] for row in other_rows], [str(plans[1].id)])
        finally:
            await database.client.close()


if __name__ == "__main__":
    unittest.main()
