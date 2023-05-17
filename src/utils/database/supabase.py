import datetime
import os
from typing import Any, Coroutine, Dict, List

from colorama import Fore
from numpy import ndarray

from src.utils.colors import LogColor
from src.utils.database.base import DatabaseProviderSingleton, Tables
from src.utils.database.clients.supabase_client import Client, create_client
from src.utils.embeddings import get_embedding
from src.utils.formatting import print_to_console


class SupabaseDatabase(DatabaseProviderSingleton):
    client: Client

    def __init__(self, client):
        # instantiate like this
        self.client = client

    async def get_by_id(self, table: Tables, id: str) -> List[Dict[str, Any]]:
        return (
            await self.client.table(table.value).select("*").eq("id", id).execute()
        ).data

    async def get_by_ids(self, table: Tables, ids: list[str]) -> List[Dict[str, Any]]:
        return (
            await self.client.table(table.value).select("*").in_("id", ids).execute()
        ).data

    async def get_all(self, table: Tables) -> List[Dict[str, Any]]:
        return (await self.client.table(table.value).select("*").execute()).data

    async def get_by_field(
        self, table: Tables, field: str, value: Any, limit: int = None
    ) -> List[Dict[str, Any]]:
        if limit is not None:
            return (
                await self.client.table(table.value)
                .select("*")
                .eq(field, value)
                .limit(limit)
                .execute()
            ).data
        return (
            await self.client.table(table.value).select("*").eq(field, value).execute()
        ).data

    async def get_by_field_contains(
        self, table: Tables, field: str, value: Any, limit: int = None
    ) -> List[Dict[str, Any]]:
        if limit is not None:
            return (
                await self.client.table(table.value)
                .select("*")
                .contains(field, [value])
                .limit(limit)
                .execute()
            ).data
        return (
            await self.client.table(table.value)
            .select("*")
            .contains(field, [value])
            .execute()
        ).data

    async def get_memories_since(
        self, timestamp: datetime, agent_id: str
    ) -> List[Dict[str, Any]]:
        return (
            await self.client.table(Tables.Memories.value)
            .select("*")
            .gte("created_at", timestamp)
            .eq("agent_id", agent_id)
            .execute()
        ).data

    async def get_should_reflect(self, agent_id: str) -> List[Dict[str, Any]]:
        return (
            await self.client.table(Tables.Memories.value)
            .select("type", "created_at", "agent_id")
            .eq("agent_id", agent_id)
            .eq("type", "reflection")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        ).data

    async def get_recent_events(
        self, world_id: str, limit: int
    ) -> List[Dict[str, Any]]:
        return (
            await self.client.table("Events")
            .select("*, location_id(*)")
            .eq("location_id.world_id", world_id)
            .order("timestamp", desc=True)
            .limit(limit)
            .execute()
        ).data

    async def get_messages_by_discord_id(self, discord_id: str) -> list[dict[str, Any]]:
        return (
            await self.client.table("Events")
            .select()
            .eq("metadata->>discord_id", discord_id)
            .single()
        ).data

    async def insert(
        self, table: Tables, data: dict | list[dict], upsert=False
    ) -> None:
        return (
            await self.client.table(table.value).insert(data, upsert=upsert).execute()
        )

    async def update(self, table: Tables, id: str, data: dict) -> None:
        return await self.client.table(table.value).update(data).eq("id", id).execute()

    async def delete(self, table: Tables, id: str) -> None:
        return await self.client.table(table.value).delete().eq("id", id).execute()

    async def insert_document_with_embedding(
        self, data: dict, embedding_text: str
    ) -> None:
        data["embedding"] = await get_embedding(embedding_text)
        await self.insert(Tables.Documents, data)

    async def search_document_embeddings(self, embedding_text: str, limit: int = 10):
        embedding = await get_embedding(embedding_text)
        return (
            await (
                await self.client.rpc(
                    "match_documents",
                    {
                        "query_embedding": list(embedding),
                        "match_threshold": 0.78,
                        "match_count": limit,
                    },
                )
            ).execute()
        ).data

    async def close(self) -> Coroutine[Any, Any, None]:
        return await super().close()

    @classmethod
    async def create(cls):
        url: str = os.getenv("SUPABASE_URL")
        key: str = os.getenv("SUPABASE_KEY")
        client = create_client(url, key)

        try:
            for table in [e.value for e in Tables]:
                await client.table(table).select("*").limit(1).execute()

        except Exception as e:
            print_to_console(
                f"Supabase Error",
                LogColor.ERROR,
                "Either there was an issue with your database connection or the tables do not exist. Please check your database connection and try again.",
            )
            print(e)
            exit(1)

        return cls(client)
