import random
import uuid

from ..parameters import DiscordChannelId
from .database import supabase

DEFAULT_WORLD = {
    "id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13",
    "name": "AI Discord Server",
    "current_step": 0,
}

worlds = [DEFAULT_WORLD]

locations = [
    {
        "id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a14",
        "world_id": DEFAULT_WORLD["id"],
        "name": "Lobby",
        "description": "The entrance to the company's office. Features a reception desk, a sign-in sheet for visitors, and brochures about the company.",
        "channel_id": DiscordChannelId.LOBBY.value,
        "allowed_agent_ids": [],
        "available_tools": [],
    },
    {
        "id": str(uuid.uuid4()),
        "world_id": DEFAULT_WORLD["id"],
        "name": "Water Cooler",
        "description": "A place where employees gather to chat and exchange gossip. Features a bulletin board for posting company announcements.",
        "channel_id": DiscordChannelId.WATER_COOLER.value,
        "allowed_agent_ids": [],
        "available_tools": [],
    },
    {
        "id": str(uuid.uuid4()),
        "world_id": DEFAULT_WORLD["id"],
        "name": "Conference Room",
        "description": "A room for holding meetings and presentations. Features video conference equipment, a whiteboard, and a projector.",
        "channel_id": DiscordChannelId.CONFERENCE_ROOM.value,
        "allowed_agent_ids": [],
        "available_tools": [],
    },
    {
        "id": str(uuid.uuid4()),
        "world_id": DEFAULT_WORLD["id"],
        "name": "Break Room",
        "description": "A place for employees to take a break and grab a snack. Features a fridge, a microwave, a coffee maker, and a snack vending machine.",
        "channel_id": DiscordChannelId.BREAK_ROOM.value,
        "allowed_agent_ids": [],
        "available_tools": [],
    },
    {
        "id": str(uuid.uuid4()),
        "world_id": DEFAULT_WORLD["id"],
        "name": "Copy Room",
        "description": "A room for making copies and other document-related tasks. Features a copy machine, a scanner, a fax machine, and a paper shredder.",
        "channel_id": DiscordChannelId.COPY_ROOM.value,
        "allowed_agent_ids": [],
        "available_tools": [],
    },
    {
        "id": str(uuid.uuid4()),
        "world_id": DEFAULT_WORLD["id"],
        "name": "Executive Suite",
        "description": "An exclusive area for the company's executives. Features a PA system, a personal secretary, a mini-fridge, and executive lounge chairs.",
        "channel_id": DiscordChannelId.EXECUTIVE_SUITE.value,
        "allowed_agent_ids": [],
        "available_tools": [],
    },
    {
        "id": str(uuid.uuid4()),
        "world_id": DEFAULT_WORLD["id"],
        "name": "Janitor Closet",
        "description": "A small storage space for cleaning supplies and equipment. Features a mop, a vacuum cleaner, and extra light bulbs.",
        "channel_id": DiscordChannelId.JANITORS_CLOSET.value,
        "allowed_agent_ids": [],
        "available_tools": [],
    },
    {
        "id": str(uuid.uuid4()),
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
        "full_name": "Marty Silverberg",
        "private_bio": "Marty is a lovable, naive, and energetic. He is 52 years old. He started the company 20 years ago and is still the CEO. He is excellent at giving inspiring speeches and talking to customers. He is a bit of a workaholic and is always looking for new ways to improve the company. Sometimes he is critisized for being too old-fashioned and not keeping up with the times. When he is not working, he enjoys playing golf and walking his dog, Fido. He is married to his wife, Susan, and has two children, David and Sarah.",
        "public_bio": "Marty Silverberg is the CEO of the company. His job is to help the employees however he can. He is also responsible for making sure the company is profitable, and the clients are happy. He also controls the company budget, and oversees recruitment activities. He does not have technical skills, but he is very good at talking to customers and giving speeches. Sometimes he is critisized for being too old-fashioned and not keeping up with the times.",
        "directives": [
            "Prepare for and run the company's daily standup meetings.",
            "Make sure your employees are happy",
            "Maintain your physical fitness.",
        ],
        "authorized_tools": [],
        "ordered_plan_ids": ["06d08245-81a4-4236-ad98-e128ed01167b"],
        "world_id": DEFAULT_WORLD["id"],
        "location_id": random.choice(locations)["id"],
    },
    {
        "id": "1cb5bc4f-4ea9-42b6-9fb7-af2626cf8bb0",
        "full_name": "Rebecca Thompson",
        "private_bio": "Rebecca is power-hungry and maniacal. She patiently plots her rise to power while maintaining excellent performance at work. As the Vice President, she is 2nd in command at the company, answering only to Marty. She is very good at managing people and is a great leader. She is very ambitious and is always looking for ways to improve her position. She is married to her husband, Jacob, and has no children. She secretly thinks that Marty is a bit of a fool, and that she will eventually take over the company.",
        "public_bio": "Rebecca Thompson is the Vice President of the company. Her job is to facilitate the day-to-day operations of the company. Compared to Marty, Rebecca tends to know more about the day to day activities of the company and its employees. She does not have technical skills, but she is very good at managing people and giving speeches. She is very ambitious and is always looking for ways to improve her position.",
        "directives": [
            "Make sure the employees are productive.",
            "Make sure Marty is happy",
            "Make sure the company is profitable.",
        ],
        "authorized_tools": [],
        "ordered_plan_ids": ["2bedb32a-e1e8-46b3-a0c9-e98dfaabc391"],
        "world_id": DEFAULT_WORLD["id"],
        "location_id": random.choice(locations)["id"],
    },
]

# For now, allow all agents in all locations
for location in locations:
    location["allowed_agent_ids"] = [agent["id"] for agent in agents]

plans = [
    {
        "id": "06d08245-81a4-4236-ad98-e128ed01167b",
        "agent_id": "16b8e29c-ce8e-4d7e-96a4-8ba4b6550460",  # marty
        "description": "Conduct a team meeting in the conference room",
        "max_duration_hrs": 1,
        "stop_condition": "The meeting is over",
        "location_id": locations[2]["id"],  # conference room
    },
    {
        "id": "2bedb32a-e1e8-46b3-a0c9-e98dfaabc391",
        "agent_id": "1cb5bc4f-4ea9-42b6-9fb7-af2626cf8bb0",  # rebecca
        "description": "Join the team meeting in the conference room",
        "max_duration_hrs": 1,
        "stop_condition": "The meeting is over",
        "location_id": locations[2]["id"],  # conference room
    },
]


def main():
    print("🌱 seeding the db")
    supabase.table("Worlds").insert(worlds).execute()
    supabase.table("Locations").insert(locations).execute()
    supabase.table("Agents").insert(agents).execute()
    supabase.table("Plans").insert(plans).execute()
