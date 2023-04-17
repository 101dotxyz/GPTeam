import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel

from ..agent.base import Agent


class ActionType(Enum):
    MOVE = "move"
    MESSAGE = "message"


class AgentAction(BaseModel):
    type: ActionType
    agent: Agent
    step: int
    location: Optional["Location"] = None

    def __init__(self, agent: Agent, step: int, location: Optional["Location"] = None):
        super().__init__(agent=agent, step=step, location=location)


# Every location has a discord channel
class Location(BaseModel):
    id: str
    name: str
    channel_id: str

    def __init__(self, name: str):
        super().__init__(id=uuid4(), name=name)


class EventType(Enum):
    LOCATION = "location"
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
    witnesses: list[str]

    def __init__(
        self,
        name: str,
        witnesses: list[str],
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
    def from_discord_message(message: DiscordMessage, witnesses: list[str]) -> "Event":
        # parse user provided message into an event
        # witnesses are all agents who were in the same location as the message
        pass

    @staticmethod
    def from_agent_action(action: AgentAction, witnesses: list[str]) -> "Event":
        # parse agent action into an event
        pass


class WorldState(BaseModel):
    positions: dict[Agent, Location]


class World(BaseModel):
    locations: list[Location]
    events: list[Event]
    agents: list[Agent]
    history: list[WorldState]

    def __init__(
        self, locations: list[Location], agents: list[Agent], initial_state
    ) -> None:
        super().__init__(
            locations=locations, agents=agents, history=[initial_state], events=[]
        )

    @property
    def state(self) -> WorldState:
        return self.history[-1]

    @property
    def current_step(self) -> int:
        return len(self.history)

    def get_discord_messages(self) -> list[DiscordMessage]:
        # get all messages from discord
        pass

    def get_agent_actions(self) -> list[AgentAction]:
        # will need to parse some args
        return [agent.act() for agent in self.agents]

    def get_witnesses(self, location: Location) -> list[Agent]:
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
