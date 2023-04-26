from uuid import UUID
from pydantic import BaseModel, Field
from datetime import datetime
from ..tools.context import ToolContext

def consult_directory(agent_input, tool_context: ToolContext):
    """Shows a list of all agents and their current locations"""

    # TIMC - For testing purposes
    if input("Agent wants to consult the directory. Continue? (y/n) ") != "y":
        return

    # first, craft the event object
    agents = tool_context.world_context.agents

    directory = ""

    print("People in the directory:")
    for index, agent in enumerate(agents):
        if agent["id"] == tool_context.agent_id:
            continue

        location_name = tool_context.world_context.get_location_name(agent["id"])
        directory += (
            f"{index}. {agent['full_name']}\n"
            f"   Bio: {agent['public_bio']}\n"
            f"   Location: {location_name}\n"
        )

    return directory

