from dotenv import load_dotenv

from .agents.base import Agent
from .memory.agent import AgentState, Memory

load_dotenv()


def main():
    seed_memories = [
        Memory(description="Klaus picked up a kettle and poured water into it"),
        Memory(description="David killed his neighbour Freddie"),
        Memory(description="Michael went fishing"),
        Memory(description="Michael discovered a new music artist"),
        Memory(description="Klaus ate a sandwich"),
        Memory(description="David found out that Michael is a good friend"),
    ]

    agent = Agent(name="Klaus", seed_memories=seed_memories)

    agent.memory.reflect()

    state = AgentState(description="Klaus would like to go to the fish market")

    query_memory = Memory(description=state.description)

    relevant_memories = agent.memory.retrieve_memories(state=state)

    print("Relevant memories:")
    for memory in relevant_memories:
        print(f"Memory: {memory.description}, Score: {memory.score(query_memory)}")
