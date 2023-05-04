import asyncio
from asyncio import events

from dotenv import load_dotenv

from .utils.logging import init_logging
from .world.base import World

load_dotenv()

init_logging()


async def run_world():
    world = await World.from_name("AI Discord Server")

    await world.run()


def main():
    asyncio.run(run_world())
