import json
from os import name
from typing import Optional

from pydantic import BaseModel

from .general import seed_uuid


class LocationConfig(BaseModel):
    name: str
    description: str
    channel_id: Optional[str] = None


class WorldConfig(BaseModel):
    world_name: str
    default_location_id: str
    default_world_id: str
    locations: list[LocationConfig]


def load_config():
    with open("../../config.json", "r") as f:
        data = json.load(f)

    if len(data["locations"]) == 0:
        raise ValueError("You must specify at least one location.")

    if len(data["agents"]) == 0:
        raise ValueError("You must specify at least one agent.")

    default_location_id = seed_uuid(f"location-{data['locations'][0]['name']}")
    default_world_id = seed_uuid(f"world-{data['world_name']}")
    locations = [
        LocationConfig(
            **location,
        )
        for location in data["locations"]
    ]

    return WorldConfig(
        default_location_id=default_location_id,
        default_world_id=default_world_id,
        locations=locations,
    )
