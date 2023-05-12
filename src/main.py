import asyncio
import os
import subprocess
import traceback
from multiprocessing import Process

import openai
from dotenv import load_dotenv

from src.utils.database.client import get_database
from src.utils.discord import discord_listener
from src.world.base import World

from .utils.colors import LogColor
from .utils.database.base import Tables
from .utils.formatting import print_to_console
from .utils.logging import init_logging

load_dotenv()

init_logging()


async def run_world():
    openai.api_key = os.getenv("OPENAI_API_KEY")
    try:
        process = Process(target=discord_listener)
        process.start()
        print("Started Discord listener")

        database = await get_database()

        worlds = await database.get_all(Tables.Worlds)

        if len(worlds) == 0:
            raise ValueError("No worlds found!")

        world = await World.from_id(worlds[-1]["id"])

        print_to_console(
            f"Welcome to {world.name}!",
            LogColor.ANNOUNCEMENT,
            "\n",
        )

        await world.run()
    except Exception:
        print(traceback.format_exc())
    finally:
        await (await get_database()).close()


def main():
    asyncio.run(run_world())
