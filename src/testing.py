from dotenv import load_dotenv

from .agent.base import Agent

load_dotenv()

agent = Agent.from_json_profile("TOM_THE_PIRATE")

def test_reflection():

    agent.add_observation_strings([
        "Tom picked up a kettle and poured water into it",
        "David killed his neighbour Freddie",
        "Michael went fishing",
        "Michael discovered a new music artist",
        "Tom ate a sandwich",
        "Michael ate a sandwich",
        "David found out that Michael is a good friend",
    ])

    agent.reflect()

    related_memories = agent.related_memories("David is going to the fish market")

    print("Relevant memories:")
    for item in related_memories:
        print(item)


def test_planning():

    agent.plan()

def main():
    # test_reflection()
    test_planning()