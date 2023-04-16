from dotenv import load_dotenv

from .agent.base import Agent


load_dotenv()



def test_reflection(agent: Agent):

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


def test_planning(agent):

    agent.plan()


def main():

    jane_smith_id = "b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12"
    john_doe_id = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"

    agent = Agent.from_db(jane_smith_id)

    test_reflection(agent)

    # test_reflection()
    # test_planning()