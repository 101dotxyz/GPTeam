import json
import os
import random
import requests


async def discord_request(endpoint, options):
    # append endpoint to root API URL
    url = 'https://discord.com/api/v10/' + endpoint
    # Stringify payloads
    if 'body' in options:
        options['body'] = json.dumps(options['body'])
    # Use requests library to make requests
    headers = {
        'Authorization': f'Bot {os.environ["DISCORD_TOKEN"]}',
        'Content-Type': 'application/json; charset=UTF-8',
        'User-Agent': 'DiscordBot (https://github.com/discord/discord-example-app, 1.0.0)',
    }
    response = requests.request(options.get(
        'method', 'GET'), url, headers=headers, **options)
    # throw API errors
    if not response.ok:
        data = response.json()
        print(response.status_code)
        raise Exception(json.dumps(data))
    # return original response
    return response


async def install_global_commands(app_id, commands):
    # API endpoint to overwrite global commands
    endpoint = f'applications/{app_id}/commands'

    try:
        # This is calling the bulk overwrite endpoint: https://discord.com/developers/docs/interactions/application-commands#bulk-overwrite-global-application-commands
        await discord_request(endpoint, {'method': 'PUT', 'body': commands})
    except Exception as err:
        print(err)


def get_random_emoji():
    emoji_list = ['😭', '😄', '😌', '🤓', '😎', '😤',
                  '🤖', '😶‍🌫️', '🌏', '📸', '💿', '👋', '🌊', '✨']
    return random.choice(emoji_list)


def capitalize(string):
    return string.capitalize()
