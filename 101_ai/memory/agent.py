import math
from ast import parse
from datetime import datetime, timedelta
from enum import Enum
from typing import List
from uuid import UUID, uuid4

import numpy as np
from attr import validate
from colorama import Fore
from langchain.output_parsers import OutputFixingParser, PydanticOutputParser
from langchain.schema import SystemMessage
from numpy import number
from pydantic import BaseModel, Field, validator

from ..utils.chat import get_chat_completion
from ..utils.formatting import print_to_console
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


class ReflectionQuestionsResponse(BaseModel):
    questions: tuple[str, str, str]


class ReflectionInsight(BaseModel):
    insight: str = Field(description="The insight")
    statements: list[int] = Field(
        description="A list of statements that support the insight"
    )


class ReflectionResponse(BaseModel):
    insights: list[ReflectionInsight] = Field(
        description="A list of insights and the statements that support them"
    )


RECENCY_WEIGHT = 1
RELEVANCE_WEIGHT = 1
IMPORTANCE_WEIGHT = 1
REFLECTION_MEMORY_COUNT = 100


class MemoryType(Enum):
    OBSERVATION = "observation"
    ACTION = "action"
    REFLECTION = "reflection"


class Memory(BaseModel):
    id: str
    type: MemoryType
    description: str
    insights: list[str]
    embedding: np.ndarray
    importance: int
    created: datetime
    lastAccessed: datetime

    class Config:
        arbitrary_types_allowed = True

    def __init__(
        self,
        description: str,
        type: MemoryType = MemoryType.OBSERVATION,
        insights: list[str] = [],
    ):
        importance = calculate_memory_importance(description)
        embedding = get_embedding(description)
        super().__init__(
            id=str(uuid4()),
            description=description,
            type=type,
            importance=importance,
            insights=insights,
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
    name: str
    memories: List[Memory]

    def __init__(self, name: str, seed_memories: list[Memory]):
        super().__init__(name=name, memories=seed_memories)

    def retrieve_memories(self, state: AgentState, k: int = 5):
        query_memory = Memory(description=state.description)

        sorted_memories = sorted(
            self.memories, key=lambda memory: memory.score(query_memory), reverse=True
        )

        return sorted_memories[:k]

    def add_memory(self, memory: Memory):
        self.memories.append(memory)

    def reflect(self):
        recent_memories = sorted(
            self.memories, key=lambda memory: memory.lastAccessed, reverse=True
        )[:REFLECTION_MEMORY_COUNT]

        llm = get_chat_model(ChatModel.GPT4)

        question_parser = OutputFixingParser.from_llm(
            parser=PydanticOutputParser(pydantic_object=ReflectionQuestionsResponse),
            llm=llm,
        )

        reflection_questions_prompt = SystemMessage(
            content=f"Here are a list of statements:\n{[memory.description for memory in recent_memories]}\n\nGiven only the information above, what are 3 most salient high-level questions we can answer about the subjects in the statements? {question_parser.get_format_instructions()}"
        )

        response = get_chat_completion(
            [reflection_questions_prompt],
            ChatModel.GPT4,
            "🤔 Thinking about what to reflect on...",
        )

        parsed_questions_response: ReflectionQuestionsResponse = question_parser.parse(
            response
        )

        for question in parsed_questions_response.questions:
            relevant_memories = self.retrieve_memories(
                AgentState(description=question), 20
            )

            formatted_memories = [
                f"{index}. {memory.description}"
                for index, memory in enumerate(relevant_memories, start=1)
            ]

            reflection_parser = OutputFixingParser.from_llm(
                parser=PydanticOutputParser(pydantic_object=ReflectionResponse),
                llm=llm,
            )

            reflection_prompt = SystemMessage(
                content=f"Statements about {self.name}\n{formatted_memories}\nWhat 5 high-level insights can you infer from the above statements? {reflection_parser.get_format_instructions()}"
            )

            response = get_chat_completion(
                [reflection_prompt],
                ChatModel.GPT4,
                f"🤔 Reflecting on the following question: {question}",
            )

            parsed_insights_response: ReflectionResponse = reflection_parser.parse(
                response
            )

            print_to_console("Committing reflections to memory", Fore.CYAN, "")

            for reflection_insight in parsed_insights_response.insights:
                related_memory_ids = [
                    relevant_memories[index - 1].id
                    for index in reflection_insight.statements
                ]

                new_reflection_memory = Memory(
                    type=MemoryType.REFLECTION,
                    description=reflection_insight.insight,
                    insights=related_memory_ids,
                )

                print(f"Added reflection memory: {new_reflection_memory.description}")

                self.add_memory(new_reflection_memory)

            print("Done!")


def calculate_memory_importance(memory_description: str) -> int:
    llm = get_chat_model(ChatModel.GPT4)

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
