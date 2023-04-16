from enum import Enum
from pydantic import BaseModel
from datetime import datetime, timedelta
import numpy as np
import math
from uuid import uuid4

from ..utils.embeddings import cosine_similarity, get_embedding
from ..utils.parameters import (
    IMPORTANCE_WEIGHT,
    RECENCY_WEIGHT,
    SIMILARITY_WEIGHT,
    TIME_SPEED_MULTIPLIER,
)

class MemoryType(Enum):
    OBSERVATION = "observation"
    ACTION = "action"
    REFLECTION = "reflection"
    PLAN = "plan"

class SingleMemory(BaseModel):

    id: str
    type: MemoryType
    description: str
    embedding: np.ndarray
    importance: int
    created: datetime
    lastAccessed: datetime
    related_memory_ids: list[str]
    related_agent_ids: list[str]

    @property
    def recency(self) -> float:
        last_retrieved_hours_ago = (datetime.now() - self.lastAccessed) / timedelta(
            hours=1 / TIME_SPEED_MULTIPLIER
        )

        decay_factor = 0.99
        return math.pow(decay_factor, last_retrieved_hours_ago)


    class Config:
        arbitrary_types_allowed = True

    def __init__(
        self,
        description: str,
        type: MemoryType,
        importance: int,
        related_memory_ids: list[str] = [],
    ):
        embedding = get_embedding(description)
        super().__init__(
            id=str(uuid4()),
            description=description,
            type=type,
            importance=importance,
            related_memory_ids=related_memory_ids,
            embedding=embedding,
            created=datetime.now(),
            lastAccessed=datetime.now(),
        )
    
    # Customize the printing behavior
    def __str__(self):
        return f"[{self.type.name}] - {self.description} ({round(self.importance, 1)})"

    def update_last_accessed(self):
        self.lastAccessed = datetime.now()

    def similarity(self, query: str) -> float:
        query_embedding = get_embedding(query)
        return cosine_similarity(self.embedding, query_embedding)

    def relevance(self, query: str) -> float:
        return (
            IMPORTANCE_WEIGHT * self.importance
            + SIMILARITY_WEIGHT * self.similarity(query)
            + RECENCY_WEIGHT * self.recency
        )

    

        

