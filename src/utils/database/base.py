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
    async def get_by_id(self, table: Tables, id: str):
        """get a row by id"""
        pass

    @abc.abstractmethod
    async def get_by_ids(self, table: Tables, ids: list[str]):
        """get rows by ids"""
        pass

    @abc.abstractmethod
    async def get_all(self, table: Tables):
        """get all rows"""
        pass

    @abc.abstractmethod
    async def get_by_field(self, table: Tables, field: str, value: Any, limit: int = None):
        """get all rows by field"""
        pass

    @abc.abstractmethod
    async def get_by_field_contains(self, table: Tables, field: str, value: Any, limit: int = None):
        """get all rows by field contains"""
        pass

    @abc.abstractmethod
    async def get_memories_since(self, timestamp: datetime, agent_id: str):
        """get all memories since timestamp"""
        pass

    @abc.abstractmethod
    async def get_should_reflect(self, agent_id: str):
        """get the val for if we should reflect"""
        pass

    @abc.abstractmethod
    async def get_recent_events(self, world_id: str, limit: int):
        """get the most recent events"""
        pass

    @abc.abstractmethod
    async def insert(self, table: Tables, data: dict, upsert=False):
        """insert a row"""
        pass

    @abc.abstractmethod
    async def update(self, table: Tables, id: str, data: dict):
        """update a row"""
        pass

    @abc.abstractmethod
    async def delete(self, table: Tables, id: str):
        """delete a row"""
        pass

    @abc.abstractmethod
    async def insert_document_with_embedding(self, data: dict, embedding: ndarray):
        """insert a row with an embedding"""
        pass

    @abc.abstractmethod
    async def search_document_embeddings(self, embedding: ndarray, limit: int = 10):
        """search for rows with embeddings"""
        pass
