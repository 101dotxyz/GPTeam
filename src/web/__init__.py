import asyncio
import json
import os
import re

from dotenv import load_dotenv
from quart import Quart, abort, make_response, send_file, websocket, request, jsonify
from elevenlabs import generate, set_api_key
import base64

from src.utils.database.base import Tables
from src.utils.database.client import get_database

load_dotenv()
set_api_key(os.getenv("ELEVEN_LABS_KEY"))


def get_server():
    app = Quart(__name__)

    app.config["ENV"] = "development"
    app.config["DEBUG"] = True

    @app.route("/")
    async def index():
        file_path = os.path.join(os.path.dirname(__file__), "templates/logs.html")
        return await send_file(file_path)

    @app.websocket("/logs")
    async def logs_websocket():
        file_path = os.path.join(os.path.dirname(__file__), "logs/agent.txt")
        position = 0
        while True:
            await asyncio.sleep(0.25)
            with open(file_path, "r") as log_file:
                log_file.seek(position)
                line = log_file.readline()
                if line:
                    position = log_file.tell()
                    matches = re.match(r"\[(.*?)\] \[(.*?)\] \[(.*?)\] (.*)$", line)
                    if matches:
                        agentName = matches.group(1).strip()
                        color = matches.group(2).strip().split(".")[1]
                        title = matches.group(3).strip()
                        description = matches.group(4).strip()

                        data = {
                            "agentName": agentName,
                            "color": color,
                            "title": title,
                            "description": description,
                        }
                        await websocket.send_json(data)

    @app.websocket("/world")
    async def world_websocket():
        while True:
            await asyncio.sleep(0.25)
            database = await get_database()
            worlds = await database.get_all(Tables.Worlds)

            if not worlds:
                abort(404, "No worlds found")

            id = worlds[0]["id"]

            # get all locations
            locations = await database.get_by_field(
                Tables.Locations, "world_id", str(id)
            )

            # get all agents
            agents = await database.get_by_field(Tables.Agents, "world_id", str(id))

            location_mapping = {
                location["id"]: location["name"] for location in locations
            }

            agents_state = [
                {
                    "full_name": agent["full_name"],
                    "location": location_mapping.get(
                        agent["location_id"], "Unknown Location"
                    ),
                }
                for agent in agents
            ]

            sorted_agents = sorted(agents_state, key=lambda k: k["full_name"])

            await websocket.send_json(
                {"agents": sorted_agents, "name": worlds[0]["name"]}
            )

    @app.route('/tts', methods=['POST'])
    async def text_to_speech():
        data = await request.get_json()
        text = data['text']
        voice = data['voice']
        model = "eleven_monolingual_v1"

        audio = generate(text=text, voice=voice, model=model)
        audio_base64 = base64.b64encode(audio).decode('utf-8')
        return jsonify({"audio": audio_base64})

    return app
