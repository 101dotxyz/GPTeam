import os
from datetime import datetime
from uuid import UUID

import pytz
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from src.agent.message import AgentMessage
from src.tools.context import ToolContext

from ..event.base import Event, EventType
from ..utils.discord import send_message as send_discord_message
from ..utils.discord import send_message_async as send_discord_message_async
from ..utils.parameters import DISCORD_ENABLED

load_dotenv()


class SpeakToolInput(BaseModel):
    """Input for the document tool."""

    recipient: str = Field(..., description="recipient of message")
    message: str = Field(..., description="content of message")


async def send_message_async(recipient: str, message: str, tool_context: ToolContext):
    """Emits a message event to the Events table
    And triggers discord to send a message to the appropriate channel
    """

    # Make an AgentMessage object
    agent_message = None

    try:
        agent_message = AgentMessage.from_agent_input(
            f"{recipient}; {message}", tool_context.agent_id, tool_context.context
        )
    except Exception as e:
        if "Could not find agent" in str(e):
            return "Could not find agent with that name. Try checking the directory."
        else:
            raise e

    if DISCORD_ENABLED:
        discord_token = tool_context.context.get_discord_token(agent_message.sender_id)

        # now time to send the message in discord
        discord_message = await send_discord_message_async(
            discord_token,
            tool_context.context.get_channel_id(agent_message.location.id),
            message,
        )

        # # add the discord id to the agent message
        agent_message.discord_id = str(discord_message.id)

    # Covert the AgentMessage to an event
    event: Event = agent_message.to_event()

    # now add it to the events manager
    event = await tool_context.context.add_event(event)

    # Check that the recipient is in the room
    # TODO: for some reason this wasn't working as expected

    # if agent_message.recipient_id is not None:
    #     recipient_location_id = tool_context.context.get_agent_location_id(
    #         agent_message.recipient_id
    #     )
    #   if recipient_location_id != agent_message.location.id:
    #       return f"{event.description} but {agent_message.recipient_name} is not in the room to hear it."

    return event.description


def send_message_sync(recipient: str, message: str, tool_context: ToolContext):
    """Emits a message event to the Events table
    And triggers discord to send a message to the appropriate channel
    """

    # Make an AgentMessage object
    agent_message = AgentMessage.from_agent_input(
        f"{recipient}; {message}", tool_context.agent_id, tool_context.context
    )

    if DISCORD_ENABLED:
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
    tool_context.context.add_event(event)

    return event.description
