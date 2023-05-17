import asyncio
import os
import sys

import hikari
from aiohttp import ServerDisconnectedError
from openai import ChatCompletion

from src.utils.database.base import Tables
from src.utils.database.client import get_database
from src.utils.parameters import ANNOUNCER_DISCORD_TOKEN

rest = hikari.RESTApp()
event_loop = asyncio.get_event_loop()
rest_started = False


async def _send_message(
    token, channel_id, message, rest_client: hikari.RESTApp, retries=3, delay=5
):
    for attempt in range(retries):
        try:
            async with rest_client.acquire(token, "BOT") as client:
                message = await client.create_message(channel_id, message)
            return message
        except asyncio.TimeoutError:
            if attempt < retries - 1:  # If it's not the last attempt
                await asyncio.sleep(delay)  # Wait for a while before trying again
            else:
                raise  # Raise the TimeoutError if all retries have failed
        except ServerDisconnectedError:
            if attempt < retries - 1:
                await asyncio.sleep(delay)
            else:
                raise


async def send_message_async(token, channel_id, message):
    global rest_started
    if not rest_started:
        await rest.start()
        rest_started = True

    return await _send_message(token, channel_id, message, rest)


def send_message(token, channel_id, message):
    return event_loop.run_until_complete(
        _send_message(token, channel_id, message, rest)
    )


async def announce_bot_move(bot_name: str, left_channel_id: str, enter_channel_id):
    return (
        await send_message_async(
            ANNOUNCER_DISCORD_TOKEN, left_channel_id, f"{bot_name} left the room."
        ),
        await send_message_async(
            ANNOUNCER_DISCORD_TOKEN, enter_channel_id, f"{bot_name} entered the room."
        ),
    )


async def close_rest_app():
    global rest_started
    if rest_started:
        await rest.close()
        rest_started = False


def discord_listener():
    print("Starting Discord listener")
    if not ANNOUNCER_DISCORD_TOKEN:
        return
    sys.stdout = open("discord_server.out", "a", buffering=1)
    sys.stderr = open("discord_server_errors.out", "a", buffering=1)
    print("Starting Discord listener")
    bot = hikari.GatewayBot(
        token=ANNOUNCER_DISCORD_TOKEN,
        intents=(hikari.Intents.ALL_UNPRIVILEGED | hikari.Intents.MESSAGE_CONTENT),
    )

    @bot.listen()
    async def inbound_message(event: hikari.GuildMessageCreateEvent) -> None:
        """If a non-bot user mentions your bot, respond with 'Pong!'."""

        # Do not respond to bots nor webhooks pinging us, only user accounts
        if not event.is_human:
            return

        me = bot.get_me()

        if me.id in event.message.user_mentions_ids:
            message = (
                ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an AI that impersonates characters from fiction",
                        },
                        {
                            "role": "user",
                            "content": "Can you send me something ominous that Big Brother from 1984 might say? It doesn't have to be literally from the book, just more in the spirit of the character. Reply with only the message content, no quotes, or other commentary.",
                        },
                    ],
                    temperature=0.9,
                )
                .choices[0]
                .message.content
            )

            await event.message.respond(message, reply=True)
            return

        database = await get_database()
        locations = await database.get_by_field(
            Tables.Locations, "channel_id", str(event.message.channel_id)
        )
        if len(locations) == 0:
            return
        location = locations[0]

        if event.message.type == hikari.MessageType.REPLY:
            referenced_message = event.message.referenced_message
            if referenced_message is None:
                return
            referenced_event = await database.get_messages_by_discord_id(
                str(referenced_message.id)
            )
            if len(referenced_event) == 0:
                return
            referenced_event = referenced_event[0]
            question = referenced_message.content.split(":")[1].strip()
            await database.insert(
                Tables.Messages,
                {
                    "timestamp": event.message.timestamp,
                    "type": "message",
                    "subtype": "human-agent-reply",
                    "description": f'{event.message.author.username}#{event.message.author.discriminator} (human) replied to question "{question}": {event.message.content}',
                    "location_id": str(location.id),
                    "metadata": {
                        "discord_id": str(event.message.id),
                        "referenced_event_id": str(referenced_event.id),
                        "referenced_agent_id": str(referenced_event.agent_id),
                        "human_id": str(event.message.author.id),
                    },
                },
            )
            return
        await database.insert(
            Tables.Messages,
            {
                "timestamp": event.message.timestamp,
                "type": "message",
                "subtype": "human-in-channel",
                "description": f"{event.message.author.username}#{event.message.author.discriminator} said: {event.message.content}",
                "location_id": str(location.id),
                "metadata": {
                    "discord_id": str(event.message.id),
                },
            },
        )

    bot.run()
