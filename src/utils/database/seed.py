import asyncio
import os
import random
import traceback

from src.utils.database.base import Tables
from src.utils.database.client import get_database

from ..config import load_config
from ..general import seed_uuid
from ..parameters import DISCORD_ENABLED, DiscordChannelId

config = load_config()

DEFAULT_WORLD = {
    "id": config.default_world_id,
    "name": config.world_name,
}


def get_channel_id(location_name: str):
    location_name = location_name.upper().replace(" ", "_")
    try:
        return DiscordChannelId[location_name].value
    except KeyError:
        return None


worlds = [DEFAULT_WORLD]

locations = [
    {
        "id": seed_uuid(f"location-{location.name}"),
        "world_id": config.default_world_id,
        "name": location.name,
        "description": location.description,
        "channel_id": get_channel_id(location.name) if DISCORD_ENABLED else None,
        "allowed_agent_ids": [],
        "available_tools": [],
    }
    for location in config.locations
]


agents = [
    {
        "id": seed_uuid(f"agent-{agent.first_name}"),
        "full_name": agent.first_name,
        "private_bio": agent.private_bio,
        "public_bio": agent.public_bio,
        "directives": agent.directives,
        "authorized_tools": [],
        "ordered_plan_ids": [],
        "world_id": config.default_world_id,
        "location_id": random.choice(locations)["id"],
        "discord_bot_token": os.environ.get(
            f"{agent.first_name.upper()}_DISCORD_TOKEN", None
        ),
    }
    for agent in config.agents
]

# For now, allow all agents in all locations
for location in locations:
    location["allowed_agent_ids"] = [agent["id"] for agent in agents]

# plans = [
#     {
#         "id": "06d08245-81a4-4236-ad98-e128ed01167b",
#         "agent_id": "16b8e29c-ce8e-4d7e-96a4-8ba4b6550460",  # Marty
#         "description": "Meet with Rebecca in the conference room and ask her how she is doing",
#         "max_duration_hrs": 1,
#         "stop_condition": "The meeting is over",
#         "location_id": locations[2]["id"],  # Conference Room
#     },
#     {
#         "id": "2bedb32a-e1e8-46b3-a0c9-e98dfaabc391",
#         "agent_id": "1cb5bc4f-4ea9-42b6-9fb7-af2626cf8bb0",  # Rebecca
#         "description": "Join the team meeting in the conference room",
#         "max_duration_hrs": 1,
#         "stop_condition": "The meeting is over",
#         "location_id": locations[2]["id"],  # Conference Room
#     },
#     {
#         "id": "3a44ec12-8211-4a21-8d73-e0bc2a0c73c9",
#         "agent_id": "b956fdf7-4ca8-4b25-9b84-a359b497017a",  # Sam
#         "description": "Conduct a code review session with the engineering team in the Work Zone",
#         "max_duration_hrs": 2,
#         "stop_condition": "The code review session is complete",
#         "location_id": locations[6]["id"],  # Work Zone
#     },
#     {
#         "id": "c38a73a2-2e59-4dc6-aa87-d05df1e3c8d3",
#         "agent_id": "7988ca44-d43a-4052-87ec-ded3fb48bd77",  # Nina
#         "description": "Present a new marketing campaign proposal to the team in the Conference Room",
#         "max_duration_hrs": 1,
#         "stop_condition": "The presentation is over",
#         "location_id": locations[2]["id"],  # Conference Room
#     },
#     {
#         "id": "6fdd5f5f-e67a-4a1a-b6e9-6a34b6a977d6",
#         "agent_id": "f1f5a0d9-42fd-442c-b687-f9f1348998e6",  # Oliver
#         "description": "Analyze the latest financial reports and prepare a budget update in the Break Room",
#         "max_duration_hrs": 2,
#         "stop_condition": "The budget update is prepared",
#         "location_id": locations[3]["id"],  # Break Room
#     },
# ]


async def seed(small=False):
    print(f"🌱 seeding the db - {'small' if small else 'normal'}")

    database = await get_database()
    await database.insert(Tables.Worlds, worlds, upsert=True)
    await database.insert(Tables.Locations, locations, upsert=True)
    await database.insert(Tables.Agents, agents[:2] if small else agents, upsert=True)

    await database.close()

    # await database.insert(Tables.Plans, plans[:2] if small else plans, upsert=True)


def main():
    asyncio.run(seed(small=False))


def main_small():
    asyncio.run(seed(small=True))
