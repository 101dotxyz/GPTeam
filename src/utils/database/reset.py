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
        if os.path.exists("database.db"):
            os.remove("database.db")

        if os.path.exists("vectors.pickle.gz"):
            os.remove("vectors.pickle.gz")

    print("database reset")

    await seed()


def main():
    asyncio.run(reset())
