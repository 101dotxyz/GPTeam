import asyncio
from multiprocessing import Process
import os
import traceback
import openai

from dotenv import load_dotenv

from src.utils.database.client import get_database
from src.utils.discord import discord_listener
from src.world.base import World

from .utils.logging import init_logging

load_dotenv()

init_logging()


async def run_world():
    openai.api_key = os.getenv("OPENAI_API_KEY")
    try:
        process = Process(target=discord_listener)
        process.start()
        print("Started Discord listener")

        world = await World.from_name("AI Discord Server")
        await world.run()
    except Exception:
        print(traceback.format_exc())
    finally:
        await (await get_database()).close()


def main():
    asyncio.run(run_world())
