import asyncio
from asyncio import events

from dotenv import load_dotenv

from .utils.logging import set_up_logging
from .world.base import World

load_dotenv()


def main():
    set_up_logging()
    world = World.from_name("AI Discord Server")

    asyncio.run(world.run(steps=10))
