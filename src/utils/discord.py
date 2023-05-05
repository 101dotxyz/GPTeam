import asyncio

import hikari

from src.utils.parameters import ANNOUNCER_DISCORD_TOKEN

rest = hikari.RESTApp()
event_loop = asyncio.get_event_loop()
rest_started = False


async def _send_message(token, channel_id, message, rest_client: hikari.RESTApp):
    # We acquire a client with a given token. This allows one REST app instance
    # with one internal connection pool to be reused.
    async with rest_client.acquire(token, "BOT") as client:
        message = await client.create_message(channel_id, message)

        # pass  # TIMC toggles discord messages

    return message


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
    return (await send_message_async(ANNOUNCER_DISCORD_TOKEN, left_channel_id, f"{bot_name} left the room."), await send_message_async(ANNOUNCER_DISCORD_TOKEN, enter_channel_id, f"{bot_name} entered the room."))


async def close_rest_app():
    global rest_started
    if rest_started:
        await rest.close()
        rest_started = False
