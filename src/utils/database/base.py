"""Base class for database providers."""
import abc
import datetime
from enum import Enum
from typing import Any

from numpy import ndarray

from src.utils.singleton import AbstractSingleton


class Tables(Enum):
    Agents = "Agents"
    Memories = "Memories"
    Events = "Events"
    Documents = "Documents"
    Locations = "Locations"
    Plans = "Plans"
    Worlds = "Worlds"


class DatabaseProviderSingleton(AbstractSingleton):
    @abc.abstractmethod
    async def get_by_id(self, table: Tables, id: str) -> list[dict[str, Any]]:
        """get a row by id"""
        pass

    @abc.abstractmethod
    async def get_by_ids(self, table: Tables, ids: list[str]) -> list[dict[str, Any]]:
        """get rows by ids"""
        pass

    @abc.abstractmethod
    async def get_all(self, table: Tables) -> list[dict[str, Any]]:
        """get all rows"""
        pass

    @abc.abstractmethod
    async def get_by_field(self, table: Tables, field: str, value: Any, limit: int = None) -> list[dict[str, Any]]:
        """get all rows by field"""
        pass

    @abc.abstractmethod
    async def get_by_field_contains(self, table: Tables, field: str, value: Any, limit: int = None) -> list[dict[str, Any]]:
        """get all rows by field contains"""
        pass

    @abc.abstractmethod
    async def get_memories_since(self, timestamp: datetime, agent_id: str) -> list[dict[str, Any]]:
        """get all memories since timestamp"""
        pass

    @abc.abstractmethod
    async def get_should_reflect(self, agent_id: str) -> list[dict[str, Any]]:
        """get the val for if we should reflect"""
        pass

    @abc.abstractmethod
    async def get_recent_events(self, world_id: str, limit: int) -> list[dict[str, Any]]:
        """get the most recent events"""
        pass

    @abc.abstractmethod
    async def get_messages_by_discord_id(self, discord_id: str) -> list[dict[str, Any]]:
        """get messages by discord id"""
        pass

    @abc.abstractmethod
    async def insert(self, table: Tables, data: dict, upsert=False) -> None:
        """insert a row"""
        pass

    @abc.abstractmethod
    async def update(self, table: Tables, id: str, data: dict) -> None:
        """update a row"""
        pass

    @abc.abstractmethod
    async def delete(self, table: Tables, id: str) -> None:
        """delete a row"""
        pass

    @abc.abstractmethod
    async def insert_document_with_embedding(self, data: dict, embedding_text: str) -> None:
        """insert a row with an embedding"""
        pass

    @abc.abstractmethod
    async def search_document_embeddings(self, embedding_text: str, limit: int = 10) -> None:
        """search for rows with embeddings"""
        pass

    @abc.abstractmethod
    async def close(self) -> None:
        """close the database"""
        pass

    @abc.abstractclassmethod
    async def create(cls) -> "DatabaseProviderSingleton":
        """create the database"""
        pass
