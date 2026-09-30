import sys
from types import ModuleType
import unittest
from unittest.mock import patch
from uuid import uuid4


agent_message_module = ModuleType("src.agent.message")
agent_message_module.AgentMessage = object
database_client_module = ModuleType("src.utils.database.client")


async def unused_get_database():
    raise AssertionError("The database is not used by this test")


database_client_module.get_database = unused_get_database

with patch.dict(
    sys.modules,
    {
        "src.agent.message": agent_message_module,
        "src.utils.database.client": database_client_module,
    },
):
    from src.agent.plans import SinglePlan
    from src.location.base import Location


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


if __name__ == "__main__":
    unittest.main()
