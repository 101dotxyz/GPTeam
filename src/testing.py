from dotenv import load_dotenv

from .agent.base import Agent

load_dotenv()


def main():

    jane_smith = Agent.from_id("549d5dfb-e259-4cb9-a81d-41d4c49e9c33")

    jane_smith.plan()
