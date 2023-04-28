import asyncio
from asyncio import events

from dotenv import load_dotenv

from .utils.logging import init_logging
from .world.base import World

load_dotenv()

init_logging()


def main():
    world = World.from_name("AI Discord Server")

    asyncio.run(world.run())
