from dotenv import load_dotenv

from src.utils.database.database import supabase

from .context.base import ContextManager
from .utils.parameters import WORLD_ID
from .world.base import World

load_dotenv()


def main():
    context = ContextManager()

    world = World.from_id(WORLD_ID, context=context)

    world.run(steps=10)
