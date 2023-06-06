import asyncio
import json
import os
import re

from dotenv import load_dotenv
from quart import Quart, abort, make_response, send_file, websocket

from src.utils.database.base import Tables
from src.utils.database.client import get_database

from src.utils.windowai_model import WindowAIRouter

load_dotenv()

window_router = WindowAIRouter()


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

    @app.websocket("/window")
    async def window_websocket():
        while True:
            await asyncio.sleep(0.25)

            data = await websocket.receive()

            # client should ping server periodically to see if new requests to process

            print("window_websocket data", data)
            
            await websocket.send(data)

    @app.websocket("/windowmodel")
    async def window_model_websocket():
        while True:
            await asyncio.sleep(0.25)

            data = await websocket.receive()

            print("window_websocket data", data)

            await websocket.send(data)

            """
            requests = window_router.get_window_requests()

            print("window_websocket requests", requests)

            # loop through requests
            for request in requests:
                request_id = request["request_id"]
                messages = request["messages"]

                # get response
                response = window_router.get_window_response(request_id)
                
                if not response:
                    print("window_websocket request", request)

                    # send request
                    await websocket.send_json(request)

                    response = await websocket.receive_json()

                    print("window_websocket response", response)

                    window_router.add_window_response(response)
            """



    return app
