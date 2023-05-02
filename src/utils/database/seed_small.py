import random
import uuid

from ..parameters import DiscordChannelId
from .database import supabase

DEFAULT_WORLD = {
    "id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13",
    "name": "AI Discord Server",
}

worlds = [DEFAULT_WORLD]

locations = [
    {
        "id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a14",
        "world_id": DEFAULT_WORLD["id"],
        "name": "Lobby",
        "description": "The entrance to the company's office. Features a reception desk, a sign-in sheet for visitors, and brochures about the company. Good for meeting visitors.",
        "channel_id": DiscordChannelId.LOBBY.value,
        "allowed_agent_ids": [],
        "available_tools": [],
    },
    {
        "id": "05cc2004-cc48-4bfa-8d1f-ecf0ef6c16d6",
        "world_id": DEFAULT_WORLD["id"],
        "name": "Conference Room",
        "description": "A room for holding meetings and presentations. Features video conference equipment, a whiteboard, and a projector.",
        "channel_id": DiscordChannelId.CONFERENCE_ROOM.value,
        "allowed_agent_ids": [],
        "available_tools": [],
    },
    {
        "id": "55556b9c-1c07-4d08-a46f-72a2d225db53",
        "world_id": DEFAULT_WORLD["id"],
        "name": "Copy Room",
        "description": "A room for making copies and other document-related tasks. Features a copy machine, a scanner, a fax machine, and a paper shredder.",
        "channel_id": DiscordChannelId.COPY_ROOM.value,
        "allowed_agent_ids": [],
        "available_tools": [],
    },
    {
        "id": "e69a1f91-91aa-4a15-9e4f-9f4c4b712d61",
        "world_id": DEFAULT_WORLD["id"],
        "name": "Executive Suite",
        "description": "An exclusive area for the company's executives. Features a PA system, a personal secretary, a mini-fridge, and executive lounge chairs.",
        "channel_id": DiscordChannelId.EXECUTIVE_SUITE.value,
        "allowed_agent_ids": [],
        "available_tools": [],
    },
    {
        "id": "79c7f247-1f63-44ea-8b71-ae1e1d04c53d",
        "world_id": DEFAULT_WORLD["id"],
        "name": "Work Zone",
        "description": "An open area for employees to work. Features cubicles, desks, and a printer.",
        "channel_id": DiscordChannelId.WORK_ZONE.value,
        "allowed_agent_ids": [],
        "available_tools": [],
    },
]

agents = [
    {
        "id": "16b8e29c-ce8e-4d7e-96a4-8ba4b6550460",
        "full_name": "Marty",
        "private_bio": "Marty is a lovable, naive, and energetic. He is 52 years old. He started the company 20 years ago and is still the CEO. His role is to lead  and enable the others to complete the companies goals.",
        "public_bio": "Marty is the CEO of the company. His job is to help the employees however he can. He is also responsible for making sure the company is profitable, and the clients are happy. He also controls the company budget, and oversees recruitment activities. He does not have technical skills, but he is very good at talking to customers and giving speeches.",
        "directives": [
            "Prepare for and run the company's daily standup meetings.",
            "Make sure employees are happy and being productive.",
            "Guide the others to help the company achieve it's goals.",
        ],
        "authorized_tools": [],
        "ordered_plan_ids": [],
        "world_id": DEFAULT_WORLD["id"],
        "location_id": random.choice(locations)["id"],
    },
    {
        "id": "1cb5bc4f-4ea9-42b6-9fb7-af2626cf8bb0",
        "full_name": "Rebecca",
        "private_bio": "Rebecca is Vice President, she is 2nd in command at the company, answering only to Marty. She has experience in research having worked at Harvard University for 10 years.",
        "public_bio": "Rebecca is the Vice President of the company. Her job is to facilitate the day-to-day operations of the company. Compared to Marty, Rebecca tends to know more about the day to day activities of the company and its employees. She does not have technical skills, but she is very good at managing people and giving speeches.",
        "directives": [
            "Make sure the employees are productive.",
            "Help Marty to run the company.",
            "Guide the others to help the company achieve it's goals.",
        ],
        "authorized_tools": [],
        "ordered_plan_ids": [],
        "world_id": DEFAULT_WORLD["id"],
        "location_id": random.choice(locations)["id"],
    },
    {
        "id": "bdc8dcbd-f0d6-41e6-a3a3-eaa48c7ad816",
        "full_name": "David",
        "private_bio": "David is a senior software developer. He has 25 years of programming experience and usually knows the answer to technical questions.",
        "public_bio": "David is a senior software developer. He has 25 years of programming experience and usually knows the answer to technical questions.",
        "directives": [
            "Help others with technical questions.",
            "Provide suggestions for technical solutions to the company goal.",
        ],
        "authorized_tools": [],
        "ordered_plan_ids": [],
        "world_id": DEFAULT_WORLD["id"],
        "location_id": random.choice(locations)["id"],
    },
    {
        "id": "4be7db32-0de7-4657-a1b0-153fc52cf1cd",
        "full_name": "Freddie",
        "private_bio": "Freddie works in sales and is good at finding companies that Arcadia Innovations can partner with",
        "private_bio": "Freddie works in sales and is good at finding companies that Arcadia Innovations can partner with",
        "directives": [
            "Think of other companies and/or products that can help the company achieve it's goals.",
            "Find new clients for the company.",
        ],
        "authorized_tools": [],
        "ordered_plan_ids": [],
        "world_id": DEFAULT_WORLD["id"],
        "location_id": random.choice(locations)["id"],
    },
]

# For now, allow all agents in all locations
for location in locations:
    location["allowed_agent_ids"] = [agent["id"] for agent in agents]

plans = []


def main():
    print("🌱 seeding the db")
    supabase.table("Worlds").upsert(worlds).execute()
    supabase.table("Locations").upsert(locations).execute()
    supabase.table("Agents").upsert(agents).execute()
    supabase.table("Plans").upsert(plans).execute()
