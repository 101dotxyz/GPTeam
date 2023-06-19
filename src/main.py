import asyncio
import os
import subprocess
import traceback
import webbrowser
from multiprocessing import Process
from time import sleep

import openai
from dotenv import load_dotenv

from src.utils.database.client import get_database
from src.utils.discord import discord_listener
from src.world.base import World

from .utils.colors import LogColor
from .utils.database.base import Tables
from .utils.formatting import print_to_console
from .utils.logging import init_logging
from .utils.parameters import DISCORD_ENABLED
from .web import get_server
from .utils.general import get_open_port

load_dotenv()

init_logging()


async def run_world_async():
    openai.api_key = os.getenv("OPENAI_API_KEY")
    try:
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


def run_world():
    run_in_new_loop(run_world_async())


def run_server():
    app = get_server()
    port = get_open_port()
    run_in_new_loop(app.run_task(port=port))


def run_in_new_loop(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(coro)
    finally:
        loop.close()


def run():
    port = get_open_port()

    process_discord = Process(target=discord_listener)
    process_world = Process(target=run_world)
    process_server = Process(target=run_server)

    process_discord.start()
    process_world.start()
    process_server.start()

    sleep(3)

    print(f"Opening browser on port {port}...")
    webbrowser.open(f"127.0.0.1:{port}")

    process_discord.join()
    process_world.join()
    process_server.join()


def main():
    run()
