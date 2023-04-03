from quart import Quart

app = Quart(__name__)

def run() -> None:
    app.run()
