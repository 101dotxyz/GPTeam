import sqlite3
import unittest

import aiosqlite

from src.utils.database.sqlite import SqliteDatabase


class ShouldReflectTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.connection = await aiosqlite.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        await self.connection.execute(
            """
            CREATE TABLE Memories (
                id TEXT PRIMARY KEY,
                agent_id TEXT,
                type TEXT,
                created_at TEXT
            )
            """
        )
        await self.connection.executemany(
            "INSERT INTO Memories (id, agent_id, type, created_at) VALUES (?, ?, ?, ?)",
            [
                ("reflection-old", "agent-a", "reflection", "2026-01-01T00:00:00+00:00"),
                ("reflection-new", "agent-a", "reflection", "2026-02-01T00:00:00+00:00"),
                ("reflection-other", "agent-b", "reflection", "2026-03-01T00:00:00+00:00"),
            ],
        )
        await self.connection.commit()

        self.database = object.__new__(SqliteDatabase)
        self.database.client = self.connection

    async def asyncTearDown(self):
        await self.connection.close()

    async def test_gets_latest_reflection_for_requested_agent(self):
        reflections = await self.database.get_should_reflect("agent-a")

        self.assertEqual(len(reflections), 1)
        self.assertEqual(reflections[0]["id"], "reflection-new")
        self.assertEqual(reflections[0]["agent_id"], "agent-a")


if __name__ == "__main__":
    unittest.main()
