from uuid import UUID

from pydantic import BaseModel

from src.utils.database.base import Tables
from src.utils.database.client import get_database

from ..event.base import Event, EventsManager
from ..utils.colors import NUM_AGENT_COLORS, LogColor


class WorldData(BaseModel):
    id: str
    name: str


class WorldContext(BaseModel):
    world: WorldData
    agents: list[dict]
    locations: list[dict]
    events_manager: EventsManager

    def __init__(
        self,
        agents: dict,
        locations: dict,
        events_manager: EventsManager,
        world: WorldData,
    ):
        # convert all UUIDs to strings
        for agent in agents:
            agent["id"] = str(agent["id"])
            agent["location_id"] = str(agent["location_id"])

        return super().__init__(
            agents=agents,
            locations=locations,
            world=world,
            events_manager=events_manager,
        )

    async def from_data(
        agents: dict,
        locations: dict,
        world: WorldData,
    ):
        events_manager = await EventsManager.from_world_id(world.id)

        return WorldContext(
            agents=agents,
            locations=locations,
            world=world,
            events_manager=events_manager,
        )

    async def add_event(self, event: Event) -> None:
        """Adds an event in the current step to the DB and local object"""

        # get agents at this location
        agents_at_location = self.get_agents_at_location(event.location_id)

        # add the witnesses
        event.witness_ids = [UUID(witness["id"]) for witness in agents_at_location]

        # This code is helpful when an agent is changing location
        if event.agent_id not in event.witness_ids:
            event.witness_ids.append(event.agent_id)

        # Add event to the db
        database = await get_database()
        await database.insert(Tables.Events, event.db_dict())

        # add event to local events list
        self.events_manager.recent_events.append(event)

        return event

    def get_agent_dict_from_id(self, agent_id: UUID | str) -> dict:
        # get agent
        try:
            agent = [
                agent for agent in self.agents if str(agent["id"]) == str(agent_id)
            ][0]
        except IndexError:
            raise Exception(f"Could not find agent with id {agent_id}")

        return agent

    def get_agents_at_location(self, location_id: str) -> list[dict]:
        return [a for a in self.agents if str(a["location_id"]) == str(location_id)]

    def get_location_from_agent_id(self, agent_id: UUID | str) -> dict:
        agent = self.get_agent_dict_from_id(agent_id)
        try:
            location = [
                location
                for location in self.locations
                if str(location["id"]) == str(agent["location_id"])
            ][0]
        except IndexError:
            raise Exception(f"Could not find location with id {agent['location_id']}")

        return location

    def get_location_from_location_id(self, location_id: UUID | str) -> dict:
        try:
            location = [
                location
                for location in self.locations
                if str(location["id"]) == str(location_id)
            ][0]
        except IndexError:
            raise Exception(f"Could not find location with id {location_id}")

        return location

    def location_context_string(self, agent_id: UUID | str) -> str:
        if isinstance(agent_id, UUID):
            agent_id = str(agent_id)

        # get agent
        agent = [agent for agent in self.agents if agent["id"] == agent_id][0]

        agents_at_location = self.get_agents_at_location(agent["location_id"])

        # get other agents in this location
        other_agents = [a for a in agents_at_location if a["id"] != agent_id]
        location = self.get_location_from_agent_id(agent_id)

        return (
            "Your current location: \n"
            + f"{location['name']}: {location['description']}\n"
            + "Nearby people: \n- "
            + "- ".join(
                [
                    f"{agent['full_name']}: {agent['public_bio']}\n"
                    for agent in other_agents
                ]
            )
        )

    def get_agent_color(self, agent_id: UUID | str) -> LogColor:
        agent_ids = sorted([str(agent["id"]) for agent in self.agents], key=str)

        color = f"AGENT_{agent_ids.index(str(agent_id)) % NUM_AGENT_COLORS}"
        return LogColor[color]

    def get_location_name(self, location_id: UUID | str):
        return self.get_location_from_location_id(location_id)["name"]

    def get_channel_id(self, location_id: UUID | str):
        # get location
        try:
            location = [
                location
                for location in self.locations
                if str(location["id"]) == str(location_id)
            ][0]
        except IndexError:
            raise Exception(f"Could not find location with id {location_id}")

        return location["channel_id"]

    def get_agent_location_id(self, agent_id: UUID | str):
        return self.get_agent_dict_from_id(agent_id)["location_id"]

    def get_agent_id_from_name(self, full_name: str) -> UUID:
        try:
            agent = [
                agent
                for agent in self.agents
                if agent["full_name"].lower() in full_name.strip().lower()
            ][0]
        except IndexError:
            raise Exception(f"Could not find agent with name {full_name}")
        return UUID(agent["id"])

    def get_agent_full_name(self, agent_id: UUID | str) -> str:
        return self.get_agent_dict_from_id(agent_id)["full_name"]

    def get_agent_public_bio(self, agent_id: UUID | str) -> str:
        return self.get_agent_dict_from_id(agent_id)["public_bio"]

    def get_agent_private_bio(self, agent_id: UUID | str) -> str:
        return self.get_agent_dict_from_id(agent_id)["private_bio"]

    def get_discord_token(self, agent_id: UUID | str) -> str:
        return self.get_agent_dict_from_id(agent_id)["discord_bot_token"]

    def update_agent(self, agent: dict):
        new_agents = [a for a in self.agents if str(a["id"]) != str(agent["id"])]
        agent["location_id"] = str(agent["location_id"])
        new_agents.append(agent)
        self.agents = new_agents
