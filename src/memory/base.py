from enum import Enum
from pydantic import BaseModel
from datetime import datetime, timedelta
import numpy as np
import math
from typing import Optional
from uuid import uuid4, UUID

from ..utils.embeddings import cosine_similarity, get_embedding
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
    related_agent_ids: list[UUID]

    @property
    def recency(self) -> float:
        last_retrieved_hours_ago = (datetime.now() - self.last_accessed) / timedelta(
            hours=1 / TIME_SPEED_MULTIPLIER
        )

        decay_factor = 0.99
        return math.pow(decay_factor, last_retrieved_hours_ago)

    class Config:
        arbitrary_types_allowed = True

    def __init__(
        self,
        agent_id: UUID,
        type: MemoryType,
        description: str,
        importance: int,
        related_memory_ids: list[UUID] = [],
        related_agent_ids: list[UUID] = [],
    ):
        embedding = get_embedding(description)
        super().__init__(
            id=uuid4(),
            agent_id=agent_id,
            type=type,
            description=description,
            embedding=embedding,
            importance=importance,
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            related_memory_ids=related_memory_ids,
            related_agent_ids=related_agent_ids
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
            "last_accessed": self.last_accessed.isoformat(),
            "related_memory_ids": [str(related_memory_id) for related_memory_id in self.related_memory_ids],
            "related_agent_ids": [str(related_agent_id) for related_agent_id in self.related_agent_ids]
        }

    # Customize the printing behavior
    def __str__(self):
        return f"[{self.type.name}] - {self.description} ({round(self.importance, 1)})"

    def update_last_accessed(self):
        self.last_accessed = datetime.now()

    def similarity(self, query: str) -> float:
        query_embedding = get_embedding(query)
        return cosine_similarity(self.embedding, query_embedding)

    def relevance(self, query: str) -> float:
        return (
            IMPORTANCE_WEIGHT * self.importance
            + SIMILARITY_WEIGHT * self.similarity(query)
            + RECENCY_WEIGHT * self.recency
        )

    

        

