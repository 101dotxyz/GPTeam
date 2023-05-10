import asyncio
import os
import subprocess
from asyncio import events

from dotenv import load_dotenv

from .seed import seed

load_dotenv()


async def reset():
    DATABASE_PROVIDER = os.getenv("DATABASE_PROVIDER", "sqlite")

    if DATABASE_PROVIDER == "supabase":
        subprocess.run(["supabase", "db", "reset"])
    else:
        subprocess.run(["rm", "-f", "database.db"])
        subprocess.run(["rm", "-f", "vectors.pickle.gz"])

    print("database reset")

    await seed()


def main():
    asyncio.run(reset())
