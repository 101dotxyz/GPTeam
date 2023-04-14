import math
from ast import parse
from datetime import datetime, timedelta
from typing import List

import numpy as np
from attr import validate
from langchain.output_parsers import OutputFixingParser, PydanticOutputParser
from langchain.schema import SystemMessage
from numpy import number
from pydantic import BaseModel, validator

from ..utils.chat import get_chat_completion
from ..utils.models import ChatModel, get_chat_model
from .embeddings import cosine_similarity, get_embedding


class AgentState(BaseModel):
    description: str


class MemoryArgs(BaseModel):
    id: str
    description: str


class ImportanceRatingResponse(BaseModel):
    rating: int

    @validator("rating")
    def validate_cron_jobs(cls, rating):
        if rating < 1 or rating > 10:
            raise ValueError(f"rating must be between 1 and 10. Got: {rating}")

        return rating


RECENCY_WEIGHT = 1
RELEVANCE_WEIGHT = 1
IMPORTANCE_WEIGHT = 1


class Memory(BaseModel):
    id: str
    description: str
    embedding: np.ndarray
    importance: int
    created: datetime
    lastAccessed: datetime

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, id: str, description: str):
        importance = calculate_memory_importance(description)
        embedding = get_embedding(description)
        super().__init__(
            id=id,
            description=description,
            importance=importance,
            embedding=embedding,
            created=datetime.now(),
            lastAccessed=datetime.now(),
        )

    def update_last_accessed(self):
        self.lastAccessed = datetime.now()

    def relevance(self, query_memory: "Memory") -> float:
        return cosine_similarity(self.embedding, query_memory.embedding)

    def score(self, query_memory: "Memory") -> float:
        return (
            IMPORTANCE_WEIGHT * self.importance
            + RELEVANCE_WEIGHT * self.relevance(query_memory)
            + RECENCY_WEIGHT * self.recency
        )

    @property
    def recency(self) -> float:
        last_retrieved_hours_ago = (datetime.now() - self.lastAccessed) / timedelta(
            hours=1
        )
        decay_factor = 0.99
        return math.pow(decay_factor, last_retrieved_hours_ago)


class AgentMemory(BaseModel):
    memories: List[Memory]

    def __init__(self, seed_memories: list[Memory]):
        super().__init__(memories=seed_memories)

    def retrieve_memories(self, state: AgentState, k: int = 5):
        query_memory = Memory(id="query", description=state.description)

        sorted_memories = sorted(
            self.memories, key=lambda memory: memory.score(query_memory)
        )

        return sorted_memories[:k]


def calculate_memory_importance(memory_description: str) -> int:
    llm = get_chat_model(ChatModel.TURBO)

    parser = OutputFixingParser.from_llm(
        parser=PydanticOutputParser(pydantic_object=ImportanceRatingResponse),
        llm=llm,
    )

    importance_scoring_prompt = SystemMessage(
        content=f"On the scale of 1 to 10, where 1 is purely mundane (e.g., brushing teeth, making bed) and 10 is extremely poignant (e.g., a break up, college acceptance), rate the likely poignancy of the following piece of memory.\nMemory: {memory_description}. {parser.get_format_instructions()}\n"
    )

    response = get_chat_completion(
        [importance_scoring_prompt],
        ChatModel.GPT4,
        "🤔 Calculating memory importance...",
    )

    parsed_response = parser.parse(response)

    rating = parsed_response.rating

    normalized_rating = (rating - 1) / 9

    return normalized_rating
