from dotenv import load_dotenv

from .agent.base import Agent


load_dotenv()

def test_reflection(agent: Agent):

    agent.reflect()

    related_memories = agent.related_memories("David is going to the fish market")

    print("Relevant memories:")
    for item in related_memories:
        print(item)


def test_planning(agent: Agent):

    agent.plan()


def main():

    jane_observations = [
        "Jane Smith Built a new robot prototype",
        "Jane Smith Attended AI conference last month with John Doe",
        "John Doe is a dedicated researcher",
        "John Doe told Jane Smith about his upcoming presentation"
    ]

    john_observations = [
        "John Doe Attended AI conference last month with Jane Smith",
        "John Doe Read a new paper on reinforcement learning",
        "Jane Smith has an interest in AI",
    ]

    jane_smith_id = "b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12"
    john_doe_id = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"

    jane = Agent.from_db(jane_smith_id)
    jane.add_observation_strings(jane_observations)

    # test_reflection(jane)

    test_planning(jane)