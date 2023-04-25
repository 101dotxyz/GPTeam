import json

from src.utils.parameters import DEFAULT_WORLD_ID

from ..utils.database.database import supabase


def look_up_company_directory(agent_input):
    data, count = (
        supabase.table("Agents")
        .select("full_name, public_bio")
        .eq("world_id", DEFAULT_WORLD_ID)
        .execute()
    )
    return json.dumps(data[1])
