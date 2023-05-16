import asyncio
import os

from dotenv import load_dotenv
from quart import Quart, make_response, send_file

load_dotenv()


def get_server():
    app = Quart(__name__)

    app.config["ENV"] = "development"
    app.config["DEBUG"] = True

    @app.route("/")
    async def index():
        print(os.path.dirname(__file__))
        file_path = os.path.join(os.path.dirname(__file__), "templates/logs.html")
        return await send_file(file_path)

    @app.get("/logs")
    async def display_logs():
        async def event_stream():
            file_path = os.path.join(os.path.dirname(__file__), "logs/agent.txt")
            position = 0
            while True:
                await asyncio.sleep(0.25)
                with open(file_path, "r") as log_file:
                    log_file.seek(position)
                    line = log_file.readline()
                    if line:
                        position = log_file.tell()
                        yield f"data: {line}\n\n"

        response = await make_response(
            event_stream(),
            {
                "Content-Type": "text/event-stream",
                "Cache-Control": "no-cache",
                "Transfer-Encoding": "chunked",
            },
        )
        response.timeout = None
        return response

    return app
