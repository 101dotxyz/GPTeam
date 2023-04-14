import asyncio

from dotenv import load_dotenv

from .memory.agent import AgentMemory, AgentState, Memory

load_dotenv()


def main():
    seed_memories = [
        Memory(id="1", description="picked up a kettle and poured water into it"),
        Memory(id="2", description="killed my neighbour"),
        Memory(id="3", description="went fishing"),
        Memory(id="4", description="discovered a new music artist"),
        Memory(id="5", description="ate a sandwich"),
        Memory(id="6", description="found out that Mike is a good friend"),
    ]

    agent_memory = AgentMemory(seed_memories)

    state = AgentState(description="I'd like to go to the fish market")

    relevant_memories = agent_memory.retrieve_memories(state=state)

    print("Relevant memories:")
    for memory in relevant_memories:
        print(
            f"Memory: {memory.description}, Score: {memory.score(Memory(id='query', description=state.description))}"
        )
