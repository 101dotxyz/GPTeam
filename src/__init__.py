from quart import Quart, Response, render_template, send_file

app = Quart(__name__)


def run() -> None:
    app.run()


@app.route("/")
async def view_logs():
    return await render_template("logs.html")


@app.route("/logs")
async def display_logs():
    print("event_stream requested")

    async def event_stream():
        with open("src/logs/agent.txt", "r") as log_file:
            while True:
                line = log_file.readline()
                if line:
                    yield f"data: {line}\n\n"

    return Response(event_stream(), mimetype="text/event-stream")
