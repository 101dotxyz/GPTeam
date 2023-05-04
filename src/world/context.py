from uuid import UUID

from pydantic import BaseModel

from ..event.base import EventsManager


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
        world: WorldData,
    ):
        events_manager = EventsManager(world_id=world.id)
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

    def get_agent_dict_from_id(self, agent_id: UUID | str) -> dict:
        # get agent
        try:
            agent = [
                agent for agent in self.agents if str(agent["id"]) == str(agent_id)
            ][0]
        except IndexError:
            raise Exception(f"Could not find agent with id {agent_id}")

        return agent

    def get_agents_at_location(self, location_id: str):
        return [a for a in self.agents if str(a["location_id"]) == str(location_id)]

    def get_location_from_agent_id(self, agent_id: UUID | str) -> dict:
        agent = self.get_agent_dict_from_id(agent_id)
        try:
            location = [location for location in self.locations if str(location["id"]) == str(agent["location_id"])][0]
        except IndexError:
            raise Exception(f"Could not find location with id {agent['location_id']}")
        
        return location
    
    def get_location_from_location_id(self, location_id: UUID | str) -> dict:
        try:
            location = [location for location in self.locations if str(location["id"]) == str(location_id)][0]
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
