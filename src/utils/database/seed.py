from ..database.database import supabase

worlds = [
    {
        "id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13",
        "name": "AI Discord Server",
        "current_step": 0,
    }
]

locations = [
    {
        "id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a14",
        "world_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13",
        "name": "water-cooler",
        "description": "A place to chit chat",
        "channel_id": 8395726143,
        "allowed_agent_ids": [
            "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
            "b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12",
        ],
    },
    {
        "id": "b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a15",
        "world_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13",
        "name": "quiet-area",
        "description": "A place to do focused work",
        "channel_id": 8395726144,
        "allowed_agent_ids": [
            "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
            "b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12",
        ],
    },
    {
        "id": "c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a16",
        "world_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13",
        "name": "outside",
        "description": "A place to get some fresh air",
        "channel_id": 8395726145,
        "allowed_agent_ids": [
            "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
            "b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12",
        ],
    },
]

agents = [
    {
        "id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
        "full_name": "John Doe",
        "bio": "John is an AI researcher and developer",
        "directives": ["Improve AI models"],
        "ordered_plan_ids": ["a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13"],
        "world_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13",
        "location_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a14",
    },
    {
        "id": "b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12",
        "full_name": "Jane Smith",
        "bio": "Jane is a Robotics engineer. She is currently getting her PHD at the University of California, Los Angeles. She loves riding her bike on the weekends, and has a secret passion for horseback riding.",
        "directives": ["Develop new robotic applications"],
        "ordered_plan_ids": ["b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a14"],
        "world_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13",
        "location_id": "b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a15",
    },
]

plans = [
    {
        "id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13",
        "agent_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
        "description": "Research new semantic embedding algorithms",
        "max_duration_hrs": 2,
        "stop_condition": "Research is complete",
        "location_id": "b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a15",
    },
    {
        "id": "b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a14",
        "agent_id": "b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12",
        "description": "Write a paper on advanced robotics",
        "max_duration_hrs": 2,
        "stop_condition": "Paper is written",
        "location_id": "b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a15",
    },
]


def main():
    print("🌱 seeding the db")
    supabase.table("Worlds").insert(worlds).execute()
    supabase.table("Locations").insert(locations).execute()
    supabase.table("Agents").insert(agents).execute()
    supabase.table("Plans").insert(plans).execute()
