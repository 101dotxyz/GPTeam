import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch


database_client_module = ModuleType("src.utils.database.client")


async def unused_get_database():
    raise AssertionError("The database is supplied directly by the test")


database_client_module.get_database = unused_get_database

with patch.dict(
    sys.modules,
    {"src.utils.database.client": database_client_module},
):
    from src.utils.database.base import Tables
    from src.utils.discord import _persist_human_message, hikari


class RecordingDatabase:
    def __init__(self):
        self.inserts = []
        self.looked_up_discord_id = None

    async def insert(self, table, data):
        self.inserts.append((table, data))

    async def get_messages_by_discord_id(self, discord_id):
        self.looked_up_discord_id = discord_id
        return [{"id": "event-1", "agent_id": "agent-1"}]


def make_message(message_type, **kwargs):
    message = {
        "id": "message-2",
        "type": message_type,
        "timestamp": "2026-01-01T00:00:00+00:00",
        "content": "A reply",
        "author": SimpleNamespace(username="reader", discriminator="1234", id="human-1"),
        "referenced_message": None,
    }
    message.update(kwargs)
    return SimpleNamespace(**message)


class DiscordMessageIngestionTests(unittest.IsolatedAsyncioTestCase):
    async def test_in_channel_message_is_stored_as_an_event(self):
        database = RecordingDatabase()
        message = make_message(None)
        location = {"id": "location-1"}

        await _persist_human_message(database, message, location)

        self.assertEqual(len(database.inserts), 1)
        table, data = database.inserts[0]
        self.assertIs(table, Tables.Events)
        self.assertEqual(data["subtype"], "human-in-channel")
        self.assertEqual(data["description"], "reader#1234 said: A reply")
        self.assertEqual(data["metadata"]["discord_id"], "message-2")

    async def test_reply_is_stored_as_an_event_with_its_reference(self):
        database = RecordingDatabase()
        message = make_message(
            hikari.MessageType.REPLY,
            referenced_message=SimpleNamespace(
                id="message-1", content="Agent: What do you need?"
            ),
        )
        location = {"id": "location-1"}

        await _persist_human_message(database, message, location)

        self.assertEqual(database.looked_up_discord_id, "message-1")
        self.assertEqual(len(database.inserts), 1)
        table, data = database.inserts[0]
        self.assertIs(table, Tables.Events)
        self.assertEqual(data["subtype"], "human-agent-reply")
        self.assertIn('replied to question "What do you need?"', data["description"])
        self.assertEqual(data["metadata"]["referenced_event_id"], "event-1")
        self.assertEqual(data["metadata"]["referenced_agent_id"], "agent-1")


if __name__ == "__main__":
    unittest.main()
