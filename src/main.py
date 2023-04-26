from asyncio import events

from dotenv import load_dotenv

from .world.base import World

load_dotenv()


def main():
    world = World.from_name("AI Discord Server")

    world.run(steps=10)
