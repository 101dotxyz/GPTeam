from uuid import UUID
from pydantic import BaseModel, Field
from datetime import datetime
import pytz
import os

from dotenv import load_dotenv
from ..utils.discord import send_message as send_discord_message
from ..event.base import Event, EventType
from src.tools.context import ToolContext

load_dotenv()


def send_message(agent_input, tool_context: ToolContext):
    """Emits a message event to the Events table"""

    # get the agent name
    agent_name = tool_context.world_context.get_agent_full_name(tool_context.agent_id)
    agent_location_id = tool_context.world_context.get_agent_location_id(tool_context.agent_id)

    # Tim Connors said: "Hello, world!"
    event_message = f"{agent_name} said: '{agent_input}'"

    # TIMC - For testing purposes
    if input("Agent wants to send a message. Continue? (y/n) ") != "y":
        return

    # first, craft the event object
    event = Event(
        step=tool_context.events_manager.current_step,
        timestamp=datetime.now(pytz.utc),
        type=EventType.MESSAGE,
        description=event_message,
        location_id=agent_location_id,
    )

    # now add it to the events manager
    tool_context.events_manager.add_event(event)

    # now time to send the message in discord
    send_discord_message(
        os.environ.get("DISCORD_TOKEN"),
        tool_context.world_context.get_channel_id(agent_location_id),
        event_message
    )

    print(
        "Message added to event manager at step "
        + str(tool_context.events_manager.current_step)
        + "."
    )

    return "Message sent!"
