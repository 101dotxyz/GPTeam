import math
from datetime import datetime, timedelta, tzinfo
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

import numpy as np
import pytz
from pydantic import BaseModel

from ..utils.embeddings import cosine_similarity, get_embedding
from ..utils.formatting import parse_array
from ..utils.parameters import (
    IMPORTANCE_WEIGHT,
    RECENCY_WEIGHT,
    SIMILARITY_WEIGHT,
    TIME_SPEED_MULTIPLIER,
)


class MemoryType(Enum):
    OBSERVATION = "observation"
    REFLECTION = "reflection"


class SingleMemory(BaseModel):
    id: UUID
    agent_id: UUID
    type: MemoryType
    description: str
    embedding: np.ndarray
    importance: int
    created_at: datetime
    last_accessed: datetime
    related_memory_ids: list[UUID]

    @property
    def recency(self) -> float:
        if self.last_accessed.tzinfo is None:
            self.last_accessed = pytz.utc.localize(self.last_accessed)

        last_retrieved_hours_ago = (
            datetime.now(pytz.utc) - self.last_accessed
        ) / timedelta(hours=1 / TIME_SPEED_MULTIPLIER)

        decay_factor = 0.99
        return math.pow(decay_factor, last_retrieved_hours_ago)

    @property
    def verbose_description(self) -> str:
        return f"{self.description} @ {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"

    class Config:
        arbitrary_types_allowed = True

    def __init__(
        self,
        agent_id: UUID,
        type: MemoryType,
        description: str,
        importance: int,
        embedding: np.ndarray,
        related_memory_ids: Optional[list[UUID]] = [],
        id: Optional[UUID] = None,
        created_at: Optional[datetime] = datetime.now(tz=pytz.utc),
        last_accessed: Optional[datetime] = None,
    ):
        if id is None:
            id = uuid4()

        if isinstance(embedding, str):
            embedding = parse_array(embedding)
        else:
            embedding = np.array(embedding)

        if not isinstance(embedding, np.ndarray):
            raise ValueError("Embedding must be a numpy array")

        super().__init__(
            id=id,
            agent_id=agent_id,
            type=type,
            description=description,
            embedding=embedding,
            importance=importance,
            created_at=created_at,
            last_accessed=last_accessed or created_at,
            related_memory_ids=related_memory_ids,
        )

    def db_dict(self):
        return {
            "id": str(self.id),
            "agent_id": str(self.agent_id),
            "type": self.type.value,
            "description": self.description,
            "embedding": str(self.embedding.tolist()),
            "importance": self.importance,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat()
            if self.last_accessed
            else None,
            "related_memory_ids": [
                str(related_memory_id) for related_memory_id in self.related_memory_ids
            ],
        }

    # Customize the printing behavior
    def __str__(self):
        return f"[{self.type.name}] - {self.description} ({round(self.importance, 1)})"

    def update_last_accessed(self):
        self.last_accessed = datetime.now(tz=pytz.utc)

    async def similarity(self, query: str) -> float:
        query_embedding = await get_embedding(query)
        return cosine_similarity(self.embedding, query_embedding)

    async def relevance(self, query: str) -> float:
        return (
            IMPORTANCE_WEIGHT * self.importance
            + SIMILARITY_WEIGHT * (await self.similarity(query))
            + RECENCY_WEIGHT * self.recency
        )


class RelatedMemory(BaseModel):
    memory: SingleMemory
    relevance: float

    def __str__(self) -> str:
        return f"SingleMemory: {self.memory.description}, Relevance: {self.relevance}"


async def get_relevant_memories(
    query: str, memories: list[SingleMemory], k: int = 5
) -> list[SingleMemory]:
    """Returns a list of the top k most relevant NON MESSAGE memories, based on the query string"""

    memories_with_relevance = [
        RelatedMemory(memory=memory, relevance=await memory.relevance(query))
        for memory in memories
    ]

    # Sort the list of dictionaries based on the 'relevance' key in descending order
    sorted_by_relevance = sorted(
        memories_with_relevance, key=lambda x: x.relevance, reverse=True
    )

    # get the top k memories, as a list of SingleMemory object
    top_memories = [memory.memory for memory in sorted_by_relevance[:k]]

    # now sort the list based on the created_at field, with the oldest memories first
    sorted_by_created_at = sorted(
        top_memories, key=lambda x: x.created_at, reverse=False
    )

    return sorted_by_created_at
