import os
from datetime import datetime
from uuid import UUID

import pytz
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from src.agent.message import AgentMessage
from src.tools.context import ToolContext

from ..event.base import Event, EventType
from ..utils.discord import send_message_async as send_discord_message_async, send_message as send_discord_message

load_dotenv()


async def send_message_async(agent_input: str, tool_context: ToolContext):
    """ Emits a message event to the Events table
        And triggers discord to send a message to the appropriate channel
    """

    # TIMC
    input("Press any key to continue...")

    # Make an AgentMessage object
    agent_message = AgentMessage.from_agent_input(
        agent_input, tool_context.agent_id, tool_context.context
    )

    # get the appropriate discord token
    discord_token = tool_context.context.get_discord_token(agent_message.sender_id)

    # now time to send the message in discord
    discord_message = await send_discord_message_async(
        discord_token,
        tool_context.context.get_channel_id(agent_message.location.id),
        agent_message.get_event_message(),
    )

    # add the discord id to the agent message
    agent_message.discord_id = str(discord_message.id)

    # Covert the AgentMessage to an event
    event = agent_message.to_event()

    # now add it to the events manager
    tool_context.context.events_manager.add_event(event)

    return event.description


def send_message_sync(agent_input: str, tool_context: ToolContext):
    """ Emits a message event to the Events table
        And triggers discord to send a message to the appropriate channel
    """

    # TIMC
    input("Press any key to continue...")

    # Make an AgentMessage object
    agent_message = AgentMessage.from_agent_input(agent_input, tool_context.agent_id, tool_context.context)

    # get the appropriate discord token
    discord_token = tool_context.context.get_discord_token(agent_message.sender_id)

    # now time to send the message in discord
    discord_message = send_discord_message(
        discord_token,
        tool_context.context.get_channel_id(agent_message.location.id),
        agent_message.get_event_message(),
    )

    # add the discord id to the agent message
    agent_message.discord_id = str(discord_message.id)

    # Covert the AgentMessage to an event
    event = agent_message.to_event()

    # now add it to the events manager
    tool_context.context.events_manager.add_event(event)

    return event.description
