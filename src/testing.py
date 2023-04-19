from dotenv import load_dotenv
from langchain.schema import SystemMessage

from src.event.base import EventManager
from src.utils.database import supabase
from src.utils.models import ChatModel
from src.utils.prompt import Prompter

from .agent.base import Agent

load_dotenv()


def main():
    jane_smith_id = (
        supabase.table("Agents").select("id").eq("full_name", "Jane Smith").execute()
    ).data[0]["id"]

    jane_smith = Agent.from_id(jane_smith_id)

    events_manager = EventManager(events=[], starting_step=0)
    jane_smith.run_for_one_step(events_manager=events_manager)
