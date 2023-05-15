import asyncio
import subprocess
import webbrowser

from dotenv import load_dotenv
from quart import Quart, Response, make_response, render_template, send_file

load_dotenv()

app = Quart(__name__)


def run() -> None:
    app.run()


@app.route("/")
async def view_logs():
    return await render_template("logs.html")


@app.get("/logs")
async def display_logs():

    async def event_stream():
        with open("./src/logs/agent.txt", "r") as log_file:
            while True:
                await asyncio.sleep(0.25)
                line = log_file.readline()
                if line:
                    yield f"data: {line}\n\n"

    response = await make_response(
        event_stream(),
        {
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'Transfer-Encoding': 'chunked',
        },
    )
    response.timeout = None
    return response

webbrowser.open("http://127.0.0.1:8000/")
