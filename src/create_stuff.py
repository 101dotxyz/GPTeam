from uuid import uuid4, UUID

from .agent.base import Agent
from .location.base import Location
from .utils.database import supabase


def create_world(name: str):

    ## add to db
    data, count = supabase.table("Worlds").insert({"name": name}).execute()

    print("New World Created: ", name)

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
    data, count = supabase.table("Locations").insert(location.db_dict()).execute()

    print("New Location Created: ", location.name)

    return location


def create_agent(full_name: str, bio: str, directives: list[str]):
    agent = Agent(full_name=full_name, bio=bio, directives=directives)

    ## add to db
    data, count = supabase.table("Agents").insert(agent.db_dict()).execute()

    print("New Agent Created: ", agent.full_name)

    return agent
