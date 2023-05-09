import asyncio

import hikari

from src.utils.parameters import ANNOUNCER_DISCORD_TOKEN

rest = hikari.RESTApp()
event_loop = asyncio.get_event_loop()
rest_started = False


async def _send_message(token, channel_id, message, rest_client: hikari.RESTApp, retries=3, delay=5):
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
