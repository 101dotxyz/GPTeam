from uuid import UUID, uuid4

from .agent.base import Agent
from .location.base import Location
from .utils.database.client import supabase


def create_world(name: str):
    ## add to db
    data, count = supabase.table("Worlds").insert({"name": name}).execute()

    return data


def create_location(
    name: str, description: str, channel_id: str, allowed_agent_ids: list[UUID] = []
):
    location = Location(
        name=name,
        description=description,
        channel_id=channel_id,
        allowed_agent_ids=allowed_agent_ids,
    )

    ## add to db
    data, count = supabase.table("Locations").insert(location._db_dict()).execute()

    return location


def create_agent(
    full_name: str, private_bio: str, public_bio: str, directives: list[str]
):
    # agent = Agent(full_name=full_name, private_bio=private_bio, directives=directives)

    # ## add to db
    # data, count = supabase.table("Agents").insert(agent.db_dict()).execute()

    return
