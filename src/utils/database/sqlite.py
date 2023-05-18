import datetime
import json
import uuid
from sqlite3 import Cursor
from typing import Any, Coroutine

import aiosqlite
from genericpath import isfile
from hyperdb import HyperDB
from numpy import ndarray

from src.utils.database.base import DatabaseProviderSingleton, Tables


class NumpyArrayEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)


def dict_factory(cursor: Cursor, row: Any) -> dict[str, Any]:
    fields = [column[0] for column in cursor.description]
    row = [
        json.loads(value)
        if isinstance(value, str) and (value.startswith("[") or value.startswith("{"))
        else value
        for value in row
    ]
    return {key: value for key, value in zip(fields, row)}


class SqliteDatabase(DatabaseProviderSingleton):
    client: aiosqlite.Connection = None
    documents = []
    vector_db: HyperDB = None

    async def get_by_id(self, table: Tables, id: str) -> list[dict[str, Any]]:
        async with self.client.execute(
            f"SELECT * FROM {table.value} WHERE id = ?", (id,)
        ) as cursor:
            return await cursor.fetchall()

    async def get_by_ids(self, table: Tables, ids: list[str]) -> list[dict[str, Any]]:
        async with self.client.execute(
            f"SELECT * FROM {table.value} WHERE id IN ({','.join('?' * len(ids))})", ids
        ) as cursor:
            return await cursor.fetchall()

    async def get_all(self, table: Tables) -> list[dict[str, Any]]:
        async with self.client.execute(f"SELECT * FROM {table.value}") as cursor:
            return await cursor.fetchall()

    async def get_by_field(
        self, table: Tables, field: str, value: Any, limit: int = None
    ) -> list[dict[str, Any]]:
        if isinstance(value, list) or isinstance(value, dict):
            value = json.dumps(value)
        if limit is None:
            async with self.client.execute(
                f"SELECT * FROM {table.value} WHERE {field} = ?", (value,)
            ) as cursor:
                return await cursor.fetchall()
        async with self.client.execute(
            f"SELECT * FROM {table.value} WHERE {field} = ? LIMIT ?", (value, limit)
        ) as cursor:
            return await cursor.fetchall()

    # needs testing
    async def get_by_field_contains(
        self, table: Tables, field: str, value: Any, limit: int = None
    ) -> list[dict[str, Any]]:
        if isinstance(value, list) or isinstance(value, dict):
            value = json.dumps(value)
        if limit is None:
            async with self.client.execute(
                f"SELECT * FROM {table.value} WHERE {field} LIKE ?", (f"%{value}%",)
            ) as cursor:
                return await cursor.fetchall()
        async with self.client.execute(
            f"SELECT * FROM {table.value} WHERE {field} LIKE ? LIMIT ?",
            (f"%{value}%", limit),
        ) as cursor:
            return await cursor.fetchall()

    # needs testing
    async def get_memories_since(
        self, timestamp: datetime, agent_id: str
    ) -> list[dict[str, Any]]:
        async with self.client.execute(
            f"SELECT * FROM Memories WHERE agent_id = ? AND created_at > ?",
            (agent_id, timestamp),
        ) as cursor:
            return await cursor.fetchall()

    async def get_should_reflect(self, agent_id: str) -> list[dict[str, Any]]:
        async with self.client.execute(
            f"SELECT * FROM Memories WHERE id = ? AND type = 'reflection' ORDER BY created_at DESC LIMIT 1",
            (agent_id,),
        ) as cursor:
            return await cursor.fetchall()

    # needs testing
    async def get_recent_events(
        self, world_id: str, limit: int
    ) -> list[dict[str, Any]]:
        async with self.client.execute(
            f"SELECT Events.*, Locations.world_id FROM Events INNER JOIN locations ON Events.location_id = locations.id WHERE Locations.world_id = ? ORDER BY Events.timestamp DESC LIMIT ?",
            (world_id, limit),
        ) as cursor:
            return await cursor.fetchall()

    async def get_messages_by_discord_id(self, discord_id: str) -> list[dict[str, Any]]:
        async with self.client.execute(
            f"select * from events where metadata is not null and metadata->>'$.discord_id' = ?",
            (discord_id,),
        ) as cursor:
            return await cursor.fetchall()

    async def insert(
        self, table: Tables, data: dict | list[dict], upsert=False
    ) -> None:
        if isinstance(data, dict):
            data = [data]
        for item in data:
            if "id" not in item:
                item["id"] = uuid.uuid4().hex
            for key, value in item.items():
                if isinstance(value, list) or isinstance(value, dict):
                    item[key] = json.dumps(value)
            if upsert:
                await self.client.execute(
                    f"INSERT OR REPLACE INTO {table.value} ({','.join(item.keys())}) VALUES ({','.join(['?'] * len(item))})",
                    tuple(item.values()),
                )
            else:
                await self.client.execute(
                    f"INSERT INTO {table.value} ({','.join(item.keys())}) VALUES ({','.join(['?'] * len(item))})",
                    tuple(item.values()),
                )
            await self.client.commit()

    async def update(self, table: Tables, id: str, data: dict) -> None:
        for key, value in data.items():
            if isinstance(value, list) or isinstance(value, dict):
                data[key] = json.dumps(value)
        await self.client.execute(
            f"UPDATE {table.value} SET {','.join([f'{key} = ?' for key in data.keys()])} WHERE id = ?",
            tuple(data.values()) + (id,),
        )
        await self.client.commit()

    async def delete(self, table: Tables, id: str) -> None:
        await self.client.execute(f"DELETE FROM {table.value} WHERE id = ?", (id,))
        await self.client.commit()
        if table == Tables.Documents:
            indexes = [
                i for i, x in enumerate(self.vector_db.documents) if x["id"] == id
            ]
            if len(indexes) > 0:
                self.vector_db.remove_document(indexes[0])

    async def insert_document_with_embedding(self, data: dict, embedding_text) -> None:
        if "id" not in data:
            data["id"] = uuid.uuid4().hex
        else:
            if len(await self.get_by_id(Tables.Documents, data["id"])) > 0:
                await self.delete(Tables.Documents, data["id"])
        await self.insert(Tables.Documents, data)
        data["embedding_text"] = embedding_text
        self.vector_db.add_document(data)

    async def search_document_embeddings(
        self, embedding_text: str, limit: int = 10
    ) -> None:
        if len(self.vector_db.documents) == 0:
            return []
        docs = self.vector_db.query(
            embedding_text, top_k=limit, return_similarities=False
        )
        return docs

    async def close(self) -> None:
        await self.client.close()
        self.vector_db.save("vectors.pickle.gz")

    @classmethod
    async def create(cls):
        cls.client = await aiosqlite.connect("database.db")
        cls.documents = []
        cls.vector_db = HyperDB(cls.documents, key="embedding_text")
        try:
            if isfile("vectors.pickle.gz"):
                cls.vector_db.load("vectors.pickle.gz")
        except:
            cls.documents = []
            cls.vector_db = HyperDB(cls.documents, key="embedding_text")
            pass

        await cls.client.execute(
            """
        CREATE TABLE IF NOT EXISTS worlds (
            id TEXT PRIMARY KEY,
            name TEXT
        )
        """
        )
        await cls.client.execute(
            """
        CREATE TABLE IF NOT EXISTS locations (
            id TEXT PRIMARY KEY,
            name TEXT,
            world_id TEXT,
            available_tools TEXT,
            description TEXT,
            channel_id TEXT,
            allowed_agent_ids TEXT,
            FOREIGN KEY (world_id) REFERENCES worlds (id)
        )
        """
        )
        await cls.client.execute(
            """
        CREATE TABLE IF NOT EXISTS agents (
            id TEXT PRIMARY KEY,
            full_name TEXT,
            private_bio TEXT,
            public_bio TEXT,
            authorized_tools TEXT,
            directives TEXT,
            last_checked_events TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ordered_plan_ids TEXT,
            location_id TEXT,
            discord_bot_token TEXT,
            world_id TEXT,
            FOREIGN KEY (world_id) REFERENCES worlds (id),
            FOREIGN KEY (location_id) REFERENCES locations (id)
        )
        """
        )
        await cls.client.execute(
            """
        CREATE TABLE IF NOT EXISTS plans (
            id TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            agent_id TEXT,
            description TEXT,
            location_id TEXT,
            max_duration_hrs REAL,
            stop_condition TEXT,
            completed_at TIMESTAMP,
            scratchpad TEXT,
            status TEXT DEFAULT 'todo' CHECK(status IN ('failed', 'in_progress', 'todo', 'done')),
            related_event_id TEXT,
            FOREIGN KEY (agent_id) REFERENCES agents (id)
        )
        """
        )
        await cls.client.execute(
            """
        CREATE TABLE IF NOT EXISTS events (
            id TEXT PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            type TEXT CHECK (type IN ('non_message', 'message')),
            subtype TEXT,
            description TEXT,
            agent_id TEXT,
            location_id TEXT,
            witness_ids TEXT,
            metadata TEXT,
            FOREIGN KEY (agent_id) REFERENCES agents (id)
        )
        """
        )
        await cls.client.execute(
            """
        CREATE TABLE IF NOT EXISTS memories (
            id TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            agent_id TEXT,
            type TEXT CHECK (type IN ('reflection', 'observation')),
            description TEXT,
            related_memory_ids TEXT,
            embedding TEXT,
            importance INTEGER,
            last_accessed TIMESTAMP,
            FOREIGN KEY (agent_id) REFERENCES agents (id)
        )
        """
        )
        await cls.client.execute(
            """
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            agent_id TEXT,
            title TEXT,
            normalized_title TEXT,
            content TEXT,
            embedding TEXT,
            FOREIGN KEY (agent_id) REFERENCES agents (id)
        )
        """
        )
        await cls.client.commit()
        cls.client.row_factory = dict_factory
        return cls()
