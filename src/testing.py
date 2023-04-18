from dotenv import load_dotenv

from .agent.base import Agent
from .world.base import World

load_dotenv()


def main():
    jane_smith = Agent.from_id("b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12")

    jane_smith.plan()
