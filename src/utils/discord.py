import asyncio

import hikari

rest = hikari.RESTApp()
event_loop = asyncio.get_event_loop()
event_loop.run_until_complete(rest.start())


async def _send_message(token, channel_id, message):
    # We acquire a client with a given token. This allows one REST app instance
    # with one internal connection pool to be reused.
    async with rest.acquire(token, "BOT") as client:
        message = await client.create_message(channel_id, message)

    return message


def send_message(token, channel_id, message):
    return None
    return event_loop.run_until_complete(_send_message(token, channel_id, message))
