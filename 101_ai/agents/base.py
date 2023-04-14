from pydantic import BaseModel

from ..memory.agent import AgentMemory, Memory


class Agent(BaseModel):
    name: str
    memory: AgentMemory

    def __init__(self, name: str, seed_memories: list[Memory] = []):
        super().__init__(
            name=name, memory=AgentMemory(name=name, seed_memories=seed_memories)
        )
