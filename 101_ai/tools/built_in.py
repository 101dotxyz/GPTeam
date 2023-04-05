from langchain.utilities import BashProcess


def get_built_in_tools(tools: list[str]):
    bash = BashProcess()

    load_tools(["human"])
    return [bash]
