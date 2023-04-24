import hikari
import asyncio

rest = hikari.RESTApp()


async def _send_message(token, channel_id, message):
    await rest.start()

    # We acquire a client with a given token. This allows one REST app instance
    # with one internal connection pool to be reused.
    async with rest.acquire(token, "BOT") as client:
        message = await client.create_message(channel_id, message)

    await rest.close()
    return message


def send_message(token, channel_id, message):
    return asyncio.run(_send_message(token, channel_id, message))
