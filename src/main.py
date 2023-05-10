import asyncio
import traceback

from dotenv import load_dotenv

from src.utils.database.client import get_database
from src.world.base import World

from .utils.logging import init_logging

load_dotenv()

init_logging()


async def run_world():
    try:
        world = await World.from_name("AI Discord Server")
        await world.run()
    except Exception:
        print(traceback.format_exc())
    finally:
        await (await get_database()).close()


def main():
    asyncio.run(run_world())
