import math
from ast import parse
from datetime import datetime, timedelta
from typing import List

from attr import validate
from langchain.output_parsers import OutputFixingParser, PydanticOutputParser
from langchain.schema import SystemMessage
from pydantic import BaseModel, validator

from ..utils.chat import get_chat_completion
from ..utils.models import ChatModel, get_chat_model


class AgentState(BaseModel):
    action: str


class MemoryArgs(BaseModel):
    id: str
    description: str


class AgentMemoryArgs(BaseModel):
    seedMemories: List["Memory"]


class ImportanceRatingResponse(BaseModel):
    rating: int

    @validator("rating")
    def validate_cron_jobs(cls, rating):
        if rating < 1 or rating > 10:
            raise ValueError(f"rating must be between 1 and 10. Got: {rating}")

        return rating


class Memory(BaseModel):
    id: str
    description: str
    importance: int
    created: datetime
    lastAccessed: datetime

    def __init__(self, id: str, description: str):
        importance = calculate_memory_importance(description)
        super().__init__(
            id=id,
            description=description,
            importance=importance,
            created=datetime.now(),
            lastAccessed=datetime.now(),
        )

    def update_last_accessed(self):
        self.lastAccessed = datetime.now()

    @property
    def recency(self) -> float:
        last_retrieved_hours_ago = (datetime.now() - self.lastAccessed) / timedelta(
            hours=1
        )
        decay_factor = 0.99
        return math.pow(decay_factor, last_retrieved_hours_ago)


class AgentMemory(BaseModel):
    memories: List[Memory]

    def __init__(self, args: AgentMemoryArgs):
        super().__init__(memories=args.seedMemories)

    def retrieve_memories(self, state: AgentState):
        pass


def calculate_memory_importance(memory_description: str) -> int:
    llm = get_chat_model(ChatModel.TURBO)

    parser = OutputFixingParser.from_llm(
        parser=PydanticOutputParser(pydantic_object=ImportanceRatingResponse),
        llm=llm,
    )

    importance_scoring_prompt = SystemMessage(
        content=f"On the scale of 1 to 10, where 1 is purely mundane (e.g., brushing teeth, making bed) and 10 is extremely poignant (e.g., a break up, college acceptance), rate the likely poignancy of the following piece of memory.\nMemory: {memory_description}. {parser.get_format_instructions()}\n"
    )

    response = get_chat_completion([importance_scoring_prompt], ChatModel.GPT4)

    parsed_response = parser.parse(response)

    print("Parsed importance rating response: ", parsed_response)

    return parsed_response.rating
