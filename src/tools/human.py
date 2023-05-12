from src.agent.message import AgentMessage
from src.event.base import MessageEventSubtype
from src.tools.context import ToolContext
from src.utils.parameters import DISCORD_ENABLED

from ..utils.discord import send_message as send_discord_message
from ..utils.discord import send_message_async as send_discord_message_async


def _print_func(text: str) -> None:
    print("\n")
    print(text)


async def ask_human_async(agent_input: str, tool_context: ToolContext):
    if DISCORD_ENABLED:
        # Make an AgentMessage object
        agent_message = AgentMessage.from_agent_input(
            agent_input,
            tool_context.agent_id,
            tool_context.context,
            type=MessageEventSubtype.AGENT_TO_HUMAN,
        )

        # get the appropriate discord token
        discord_token = tool_context.context.get_discord_token(
            agent_message.sender_id
        )

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
        tool_context.context.add_event(event)

        return event.description
    _print_func(agent_input)
    return input()


def ask_human(agent_input: str, tool_context: ToolContext):
    if DISCORD_ENABLED:
        # Make an AgentMessage object
        agent_message = AgentMessage.from_agent_input(
            agent_input,
            tool_context.agent_id,
            tool_context.context,
            type=MessageEventSubtype.AGENT_TO_HUMAN,
        )

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
    _print_func(agent_input)
    return input()
