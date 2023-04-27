from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from ..tools.context import ToolContext


def consult_directory(agent_input, tool_context: ToolContext):
    """Shows a list of all agents and their current locations"""

    # first, craft the event object
    agents = tool_context.context.agents

    directory = ""

    for index, agent in enumerate(agents):
        if agent["id"] == tool_context.agent_id:
            continue

        location_id = tool_context.context.get_agent_location_id(agent["id"])

        location_name = tool_context.context.get_location_name(location_id)
        directory += (
            f"{index}. {agent['full_name']}\n"
            f"   Bio: {agent['public_bio']}\n"
            f"   Location: {location_name}\n"
        )

    return directory
