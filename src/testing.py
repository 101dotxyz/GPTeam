from dotenv import load_dotenv

from .agent.base import Agent
from .world.base import World

load_dotenv()

discord_world_id = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13"
jane_smith_id = "b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12"
john_doe_id = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"

def main():

    # # Set up the world
    # world = World.from_id(discord_world_id)

    # print(world.locations)
    
    # for location in world.locations:
    #     print(location.allowed_agent_ids)
    

    # Set up the agents

    jane_observations = [
        "Jane Smith Built a new robot prototype",
        "Jane Smith ate some lunch",
        "Jane Smith Attended AI conference last month with John Doe",
        "John Doe is a dedicated researcher",
        "John Doe told Jane Smith about his upcoming presentation"
    ]

    john_observations = [
        "John Doe Attended AI conference last month with Jane Smith",
        "John Doe Read a new paper on reinforcement learning",
        "Jane Smith has an interest in AI",
    ]

    agent = Agent.from_id(jane_smith_id)
    agent.add_observation_strings(jane_observations)
    
    agent.act()

    # agent.reflect()


