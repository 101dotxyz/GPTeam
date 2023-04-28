import os
from datetime import datetime
from uuid import UUID

import pytz
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from src.tools.context import ToolContext

from ..event.base import Event, EventType
from ..utils.discord import send_message as send_discord_message

load_dotenv()


def send_message(agent_input, tool_context: ToolContext):
    """Emits a message event to the Events table"""

    # get the agent name
    agent_name = tool_context.context.get_agent_full_name(tool_context.agent_id)
    agent_location_id = tool_context.context.get_agent_location_id(
        tool_context.agent_id
    )

    # Tim Connors said: "Hello, world!"
    event_message = f"{agent_name} said: '{agent_input}'"

    # first, craft the event object
    event = Event(
        agent_id=tool_context.agent_id,
        type=EventType.MESSAGE,
        description=event_message,
        location_id=agent_location_id,
    )

    # now add it to the events manager
    tool_context.context.events_manager.add_event(event)

    # now time to send the message in discord
    send_discord_message(
        os.environ.get("DISCORD_TOKEN"),
        tool_context.context.get_channel_id(agent_location_id),
        event_message,
    )

    return event_message
