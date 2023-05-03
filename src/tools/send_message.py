import os
from datetime import datetime
from uuid import UUID

import pytz
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from src.tools.context import ToolContext
from src.agent.message import AgentMessage
from ..event.base import Event, EventType
from ..utils.discord import send_message as send_discord_message

load_dotenv()


def send_message(agent_input: str, tool_context: ToolContext):
    """ Emits a message event to the Events table
        And triggers discord to send a message to the appropriate channel
    """

    print("Sending message... AGENT INPUT: ", agent_input) #TIMC

    # TIMC
    input("Press any key to continue...")

    # Make an AgentMessage object
    agent_message = AgentMessage.from_agent_input(agent_input, tool_context.agent_id, tool_context.context)

    # Covert the AgentMessage to an event
    event = agent_message.to_event()

    # now add it to the events manager
    tool_context.context.events_manager.add_event(event)

    # now time to send the message in discord
    send_discord_message(
        os.environ.get("DISCORD_TOKEN"),
        tool_context.context.get_channel_id(agent_message.location.id),
        event.description,
    )

    return event.description
