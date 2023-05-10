import json
from os import name
from typing import Optional

from pydantic import BaseModel

from .general import seed_uuid


class LocationConfig(BaseModel):
    id: str
    name: str
    description: str


class AgentConfig(BaseModel):
    id: str
    first_name: str
    private_bio: str
    public_bio: str
    directives: list[str]
    initial_plan: dict[str, str]


class WorldConfig(BaseModel):
    world_id: str
    world_name: str
    default_location_id: str
    locations: list[LocationConfig]
    agents: list[AgentConfig]


def load_config():
    with open("./config.json", "r") as f:
        config = json.load(f)

    if len(config["locations"]) == 0:
        raise ValueError("You must specify at least one location.")

    if len(config["agents"]) == 0:
        raise ValueError("You must specify at least one agent.")

    default_location_id = seed_uuid(f"location-{config['locations'][0]['name']}")
    locations = [
        LocationConfig(
            id=seed_uuid(f"location-{location['name']}"),
            **location,
        )
        for location in config["locations"]
    ]

    agents = [
        AgentConfig(id=seed_uuid(f"agent-{agent['first_name']}"), **agent)
        for agent in config["agents"]
    ]

    return WorldConfig(
        world_id=seed_uuid(f"world-{config['world_name']}"),
        world_name=config["world_name"],
        default_location_id=default_location_id,
        locations=locations,
        agents=agents,
    )
