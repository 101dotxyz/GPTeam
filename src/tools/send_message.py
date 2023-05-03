import os
from datetime import datetime
from uuid import UUID

import pytz
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from src.tools.context import ToolContext
from src.agent.message import AgentMessage
from ..event.base import Event, EventType
from ..utils.discord import send_message_async as send_discord_message

load_dotenv()


async def send_message_async(agent_input: str, tool_context: ToolContext):
    """ Emits a message event to the Events table
        And triggers discord to send a message to the appropriate channel
    """

    # TIMC
    input("Press any key to continue...")

    # Make an AgentMessage object
    agent_message = AgentMessage.from_agent_input(agent_input, tool_context.agent_id, tool_context.context)

    # Covert the AgentMessage to an event
    event = agent_message.to_event()

    # now add it to the events manager
    tool_context.context.events_manager.add_event(event)

    # get the appropriate discord token
    discord_token = tool_context.context.get_discord_token(agent_message.sender_id)

    # now time to send the message in discord
    await send_discord_message(
        discord_token,
        tool_context.context.get_channel_id(agent_message.location.id),
        agent_message.content
    )

    return event.description


def send_message_sync(agent_input: str, tool_context: ToolContext):
    """ Emits a message event to the Events table
        And triggers discord to send a message to the appropriate channel
    """

    # TIMC
    input("Press any key to continue...")

    # Make an AgentMessage object
    agent_message = AgentMessage.from_agent_input(agent_input, tool_context.agent_id, tool_context.context)

    # Covert the AgentMessage to an event
    event = agent_message.to_event()

    # now add it to the events manager
    tool_context.context.events_manager.add_event(event)

    # get the appropriate discord token
    discord_token = tool_context.context.get_discord_token(agent_message.sender_id)

    # now time to send the message in discord
    send_discord_message(
        discord_token,
        tool_context.context.get_channel_id(agent_message.location.id),
        event.description,
    )

    return event.description
