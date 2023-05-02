import asyncio
import hikari

rest = hikari.RESTApp()
client = None

async def _send_message(token, channel_id, message):
    global client
    if client is None:
        client = await rest.acquire(token, "BOT")
    message = await client.create_message(channel_id, message)
    return message

async def send_message(token, channel_id, message):
    task = asyncio.create_task(_send_message(token, channel_id, message))
    return await task