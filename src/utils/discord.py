import hikari

rest = hikari.RESTApp()


async def send_message(token, channel_id, message):
    # Disable in dev
    return None
    if not rest._client_session:
        await rest.start()
    # We acquire a client with a given token. This allows one REST app instance
    # with one internal connection pool to be reused.
    async with rest.acquire(token, "BOT") as client:
        message = await client.create_message(channel_id, message)

    return message
