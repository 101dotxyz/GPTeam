from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from ..tools.context import ToolContext


def consult_directory(
    tool_context: ToolContext,
    agent_input: str = None,
):
    """Shows a list of all agents and their current locations"""

    # first, craft the event object
    agents = tool_context.context.agents

    directory = ""

    for index, agent in enumerate(agents):
        if agent["id"] == tool_context.agent_id:
            continue

        directory += (
            f"{agent['full_name']}\n"
            f"---------------------\n"
            f"Bio: {agent['public_bio']}\n"
            f"---------------------\n\n"
        )

    return directory
