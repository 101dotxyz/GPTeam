import asyncio
import os
import random

import openai

from src.utils.database.base import Tables
from src.utils.database.client import get_database
from ...tools.context import ToolContext
from ...tools.document import read_document, save_document, search_documents

from ..config import AgentConfig, load_config
from ..general import seed_uuid
from ..parameters import DISCORD_ENABLED

from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

config = load_config()


worlds = [
    {
        "id": config.world_id,
        "name": config.world_name,
    }
]

locations = [
    {
        "id": location.id,
        "world_id": config.world_id,
        "name": location.name,
        "description": location.description,
        "channel_id": os.environ.get(
            f"{location.name.upper().replace(' ','_')}_CHANNEL_ID", None
        )
        if DISCORD_ENABLED
        else None,
        "allowed_agent_ids": [],
        "available_tools": [],
    }
    for location in config.locations
]

agents = [
    {
        "id": agent.id,
        "full_name": agent.first_name,
        "private_bio": agent.private_bio,
        "public_bio": agent.public_bio,
        "directives": agent.directives,
        "authorized_tools": [],
        "ordered_plan_ids": [seed_uuid(f"agent-{agent.id}-initial-plan")],
        "world_id": config.world_id,
        "location_id": random.choice(locations)["id"],
        "discord_bot_token": os.environ.get(
            f"{agent.first_name.upper()}_DISCORD_TOKEN", None
        ),
    }
    for agent in config.agents
]

if DISCORD_ENABLED:
    for agent in agents:
        if agent["discord_bot_token"] is None:
            raise ValueError(
                f"Could not find discord bot token for agent {agent['full_name']}"
            )

# For now, allow all agents in all locations
for location in locations:
    location["allowed_agent_ids"] = [agent["id"] for agent in agents]


def get_agent_initial_plan(agent: AgentConfig):
    location_name = agent.initial_plan["location"]
    location = next(
        (location for location in config.locations if location.name == location_name),
        None,
    )

    if location is None:
        raise ValueError(
            f"Could not find location with name {location_name} for agent {agent.first_name}"
        )

    return {
        "id": seed_uuid(f"agent-{agent.id}-initial-plan"),
        "agent_id": agent.id,
        "description": agent.initial_plan["description"],
        "max_duration_hrs": 1,
        "stop_condition": agent.initial_plan["stop_condition"],
        "location_id": location.id,
    }


initial_plans = [get_agent_initial_plan(agent) for agent in config.agents]

documents = [
    {
        "id": seed_uuid(f"document-{document.title}"),
        "title": document.title,
        "content": document.content,
        "agent_id": agents[0]["id"],
    }
    for document in config.initial_documents
]


async def seed(small=False):
    print(f"seeding the db - {'small' if small else 'normal'}")

    saved_docs = await search_documents("life is good", None)

    print(f"{saved_docs}")

    database = await get_database()
    await database.insert(Tables.Worlds, worlds, upsert=True)
    await database.insert(Tables.Locations, locations, upsert=True)
    await database.insert(Tables.Agents, agents[:2] if small else agents, upsert=True)
    await database.insert(
        Tables.Plans, initial_plans[:2] if small else initial_plans, upsert=True
    )

    for document in documents:
        normalized_title = document["title"].lower().strip().replace(" ", "_")

        await (await get_database()).insert_document_with_embedding(
            {
                "id": seed_uuid(f"document-{document['title']}"),
                "title": document["title"],
                "normalized_title": normalized_title,
                "content": document["content"],
                "agent_id": agents[0]["id"],
            },
            f"""{document["title"]} ({normalized_title})
    {document}""",
        )

        print(f"inserted document {document['title']}")

    await database.close()


def main():
    asyncio.run(seed(small=False))


def main_small():
    asyncio.run(seed(small=True))
