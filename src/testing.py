from dotenv import load_dotenv
from langchain.schema import SystemMessage

from src.event.base import EventManager
from src.utils.database import supabase
from src.utils.models import ChatModel
from src.utils.prompt import Prompter

from .agent.base import Agent
from .world.base import World

load_dotenv()


def main():
    world = World.from_name("AI Discord Server")

    world.run_step()
