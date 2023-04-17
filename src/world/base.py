import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4, UUID

from pydantic import BaseModel

# from ..agent.base import Agent
from ..utils.database import supabase


class ActionType(Enum):
    MOVE = "move"
    MESSAGE = "message"


# class AgentAction(BaseModel):
#     type: ActionType
#     agent: Agent
#     step: int
#     location: Optional["Location"] = None

#     def __init__(self, agent: Agent, step: int, location: Optional["Location"] = None):
#         super().__init__(agent=agent, step=step, location=location)

class Location(BaseModel):
    id: UUID
    world_id: UUID
    name: str
    description: str
    channel_id: str
    allowed_agent_ids: list[UUID]

    def __init__(
            self, 
            id: UUID,
            world_id: UUID,
            name: str,
            description: str,
            channel_id: int,
            allowed_agent_ids: list[UUID]
        ):
        super().__init__(
            id=id, 
            world_id=world_id,
            name=name,
            description=description,
            channel_id=channel_id,
            allowed_agent_ids=allowed_agent_ids
        )

    @classmethod
    def from_id(cls, id: UUID):
        data, count = supabase.table("Locations").select("*").eq("id", id).execute()
        return cls(**data[1][0])
    
    @classmethod
    def from_name(cls, name: str):
        data, count = supabase.table("Locations").select("*").eq("name", name).execute()
        return cls(**data[1][0])
    
    @property
    def local_agent_ids(self) -> list[UUID]:
        """Get IDs of agents who are currently in this location."""
        data, count = supabase.table("Agents").select("id").eq("location_id", self.id).execute()
        print(data)
        return [agent["id"] for agent in data[1]]


class EventType(Enum):
    LOCATION = "non_message"
    MESSAGE = "message"


class DiscordMessage(BaseModel):
    content: str
    location: Location
    timestamp: datetime.datetime


class Event(BaseModel):
    id: str
    type: EventType
    timestamp: Optional[datetime.datetime] = None
    step: int
    witnesses: list[UUID]

    def __init__(
        self,
        name: str,
        witnesses: list[UUID],
        timestamp: Optional[datetime.datetime] = None,
        step: Optional[int] = None,
    ):
        if timestamp is None and step is None:
            raise ValueError("Either timestamp or step must be provided")

        if timestamp:
            # calculate step from timestamp
            pass

        super().__init__(
            id=uuid4(), name=name, timestamp=timestamp, _step=step, witnesses=witnesses
        )

    @staticmethod
    def from_discord_message(message: DiscordMessage, witnesses: list[UUID]) -> "Event":
        # parse user provided message into an event
        # witnesses are all agents who were in the same location as the message
        pass

    # @staticmethod
    # def from_agent_action(action: AgentAction, witnesses: list[UUID]) -> "Event":
    #     # parse agent action into an event
    #     pass


class WorldState(BaseModel):
    agent_positions: dict[UUID, Location]


class World(BaseModel):
    id: UUID
    name: str
    history: list[WorldState]

    def __init__(
        self, 
        id: UUID, 
        name: str,
        history: list[WorldState] = [],
    ) -> None:
        super().__init__(
            id=id,
            name=name,
            history=history,
        )

    @property
    def state(self) -> WorldState:
        return self.history[-1]

    @property
    def current_step(self) -> int:
        return len(self.history)
    
    @property
    def locations(self) -> list[Location]:
        # get all locations with this id as world_id
        data, count = supabase.table("Locations").select("*").eq("world_id", self.id).execute()
        return [Location(**location) for location in data[1]]

    @classmethod
    def from_id(cls, id: UUID):
        data, count = supabase.table("Worlds").select("*").eq("id", id).execute()
        return cls(**data[1][0])

    def get_discord_messages(self) -> list[DiscordMessage]:
        # get all messages from discord
        pass

    # def get_agent_actions(self) -> list[AgentAction]:
    #     # will need to parse some args
    #     return [agent.act() for agent in self.agents]

    def get_witnesses(self, location: Location) -> list[UUID]:
        return [
            agent for agent in self.agents if self.state.positions[agent] == location
        ]

    def update(self) -> None:
        # very rough draft of how this might work

        discord_messages = self.get_discord_messages()

        for message in discord_messages:
            witnesses = self.get_witnesses(message.location)
            event = Event.from_discord_message(message, witnesses)
            self.events.append(event)

        agent_actions = self.get_agent_actions()

        for action in agent_actions:
            witnesses = self.get_witnesses(action.location)
            event = Event.from_agent_action(action, witnesses)
            self.events.append(event)

        new_state = self.state.copy()

        for action in agent_actions:
            new_state.positions[action.agent] = action.location

        self.history.append(new_state)
