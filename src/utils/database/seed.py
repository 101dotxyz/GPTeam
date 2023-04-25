import random
import uuid

from ..database.database import supabase

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
        "channel_id": 8395726143,
        "allowed_agent_ids": [],
        "available_tools": [],
    },
    {
        "id": str(uuid.uuid4()),
        "world_id": DEFAULT_WORLD["id"],
        "name": "Water Cooler",
        "description": "A place where employees gather to chat and exchange gossip. Features a bulletin board for posting company announcements.",
        "channel_id": 8395726143,
        "allowed_agent_ids": [],
        "available_tools": [],
    },
    {
        "id": str(uuid.uuid4()),
        "world_id": DEFAULT_WORLD["id"],
        "name": "Conference Room",
        "description": "A room for holding meetings and presentations. Features video conference equipment, a whiteboard, and a projector.",
        "channel_id": 8395726143,
        "allowed_agent_ids": [],
        "available_tools": [],
    },
    {
        "id": str(uuid.uuid4()),
        "world_id": DEFAULT_WORLD["id"],
        "name": "Break Room",
        "description": "A place for employees to take a break and grab a snack. Features a fridge, a microwave, a coffee maker, and a snack vending machine.",
        "channel_id": 8395726143,
        "allowed_agent_ids": [],
        "available_tools": [],
    },
    {
        "id": str(uuid.uuid4()),
        "world_id": DEFAULT_WORLD["id"],
        "name": "Copy Room",
        "description": "A room for making copies and other document-related tasks. Features a copy machine, a scanner, a fax machine, and a paper shredder.",
        "channel_id": 8395726143,
        "allowed_agent_ids": [],
        "available_tools": [],
    },
    {
        "id": str(uuid.uuid4()),
        "world_id": DEFAULT_WORLD["id"],
        "name": "Executive Suite",
        "description": "An exclusive area for the company's executives. Features a PA system, a personal secretary, a mini-fridge, and executive lounge chairs.",
        "channel_id": 8395726143,
        "allowed_agent_ids": [],
        "available_tools": [],
    },
    {
        "id": str(uuid.uuid4()),
        "world_id": DEFAULT_WORLD["id"],
        "name": "Developer Den",
        "description": "A space for the company's programmers to work. Features multiple computers, a printer, ergonomic chairs, and extra monitors.",
        "channel_id": 8395726143,
        "allowed_agent_ids": [],
        "available_tools": [],
    },
    {
        "id": str(uuid.uuid4()),
        "world_id": DEFAULT_WORLD["id"],
        "name": "Sales Pit",
        "description": "The area where the company's sales team works. Features phones with headsets, a leaderboard, and motivational posters.",
        "channel_id": 8395726143,
        "allowed_agent_ids": [],
        "available_tools": [],
    },
    {
        "id": str(uuid.uuid4()),
        "world_id": DEFAULT_WORLD["id"],
        "name": "Human Resources",
        "description": "The department responsible for managing the company's employees. Features file cabinets, employee handbooks, team-building supplies, and a complaint box.",
        "channel_id": 8395726143,
        "allowed_agent_ids": [],
        "available_tools": [],
    },
    {
        "id": str(uuid.uuid4()),
        "world_id": DEFAULT_WORLD["id"],
        "name": "Janitor Closet",
        "description": "A small storage space for cleaning supplies and equipment. Features a mop, a vacuum cleaner, and extra light bulbs.",
        "channel_id": 8395726143,
        "allowed_agent_ids": [],
        "available_tools": [],
    },
]

agents = [
    {
        "id": str(uuid.uuid4()),
        "full_name": "Marty Silverberg",
        "private_bio": "Lovable, naive, and energetic, he unknowingly leads the company to success with his early adoption of internet advertising.",
        "directives": [],
        "authorized_tools": [],
        "ordered_plan_ids": [],
        "world_id": DEFAULT_WORLD["id"],
        "location_id": random.choice(locations)["id"],
    },
    {
        "id": str(uuid.uuid4()),
        "full_name": "Rebecca Thompson",
        "private_bio": "Power-hungry and maniacal, she patiently plots her rise to power while maintaining her excellent performance at work.",
        "directives": [],
        "authorized_tools": [],
        "ordered_plan_ids": [],
        "world_id": DEFAULT_WORLD["id"],
        "location_id": random.choice(locations)["id"],
    },
    {
        "id": str(uuid.uuid4()),
        "full_name": "Linda Smith",
        "private_bio": "The enigmatic programmer with a mysterious past, she is convinced they're living in a simulation and leaves hidden messages in her code for users to find.",
        "directives": [],
        "authorized_tools": [],
        "ordered_plan_ids": [],
        "world_id": DEFAULT_WORLD["id"],
        "location_id": random.choice(locations)["id"],
    },
    {
        "id": str(uuid.uuid4()),
        "full_name": "Karen Jones",
        "private_bio": "Enthusiastic about cringeworthy team-building activities, she is always looking for ways to boost morale and foster a sense of camaraderie among the employees.",
        "directives": [],
        "authorized_tools": [],
        "ordered_plan_ids": [],
        "world_id": DEFAULT_WORLD["id"],
        "location_id": random.choice(locations)["id"],
    },
    {
        "id": str(uuid.uuid4()),
        "full_name": "Peter Williams",
        "private_bio": "A persuasive and persistent salesperson, Peter manages to close deals and maintain client relationships, even though he's not entirely sure what the company does.",
        "directives": [],
        "authorized_tools": [],
        "ordered_plan_ids": [],
        "world_id": DEFAULT_WORLD["id"],
        "location_id": random.choice(locations)["id"],
    },
    {
        "id": str(uuid.uuid4()),
        "full_name": "Dave Johnson",
        "private_bio": "While not particularly productive, he's a master of jokes and socializing, making him a beloved figure at the company. Marty can't bring himself to fire him because of his humor and charm.",
        "directives": [],
        "authorized_tools": [],
        "ordered_plan_ids": [],
        "world_id": DEFAULT_WORLD["id"],
        "location_id": random.choice(locations)["id"],
    },
    {
        "id": str(uuid.uuid4()),
        "full_name": "Susan Miller",
        "private_bio": "Diligent and detail-oriented, she's responsible for tracking the company's performance metrics, even if she doesn't fully understand the technical aspects of the business.",
        "directives": [],
        "authorized_tools": [],
        "ordered_plan_ids": [],
        "world_id": DEFAULT_WORLD["id"],
        "location_id": random.choice(locations)["id"],
    },
    {
        "id": str(uuid.uuid4()),
        "full_name": "Emma Davis",
        "private_bio": "Friendly and approachable, she welcomes visitors to the company with a warm smile and helps keep the office running smoothly, while secretly harboring a talent for hacking.",
        "directives": [],
        "authorized_tools": [],
        "ordered_plan_ids": [],
        "world_id": DEFAULT_WORLD["id"],
        "location_id": random.choice(locations)["id"],
    },
    {
        "id": str(uuid.uuid4()),
        "full_name": "Eddie Brown",
        "private_bio": "The hardworking janitor, always ready to lend an ear and offer sage advice, often knows more about the inner workings of the company than anyone suspects.",
        "directives": [],
        "authorized_tools": [],
        "ordered_plan_ids": [],
        "world_id": DEFAULT_WORLD["id"],
        "location_id": random.choice(locations)["id"],
    },
]

# For now, allow all agents in all locations
for location in locations:
    location["allowed_agent_ids"] = [agent["id"] for agent in agents]

plans = [
    {
        "id": str(uuid.uuid4()),
        "agent_id": agents[0]["id"],
        "description": "Socialize with colleagues at the water cooler",
        "max_duration_hrs": 1,
        "stop_condition": "No more conversation topics",
        "location_id": locations[0]["id"],
    },
    {
        "id": str(uuid.uuid4()),
        "agent_id": agents[1]["id"],
        "description": "Conduct a team meeting in the conference room",
        "max_duration_hrs": 2,
        "stop_condition": "All agenda items have been covered",
        "location_id": locations[2]["id"],
    },
    {
        "id": str(uuid.uuid4()),
        "agent_id": agents[2]["id"],
        "description": "Work on coding project in the developer den",
        "max_duration_hrs": 4,
        "stop_condition": "Code has been pushed to production",
        "location_id": locations[6]["id"],
    },
    {
        "id": str(uuid.uuid4()),
        "agent_id": agents[3]["id"],
        "description": "Organize a team-building exercise in the break room",
        "max_duration_hrs": 3,
        "stop_condition": "Everyone has participated in at least one activity",
        "location_id": locations[3]["id"],
    },
    {
        "id": str(uuid.uuid4()),
        "agent_id": agents[4]["id"],
        "description": "Meet with a client in the lobby",
        "max_duration_hrs": 2,
        "stop_condition": "All client questions have been answered",
        "location_id": locations[1]["id"],
    },
    {
        "id": str(uuid.uuid4()),
        "agent_id": agents[5]["id"],
        "description": "Tell jokes in the break room",
        "max_duration_hrs": 1,
        "stop_condition": "Everyone has laughed at least once",
        "location_id": locations[3]["id"],
    },
    {
        "id": str(uuid.uuid4()),
        "agent_id": agents[6]["id"],
        "description": "Track company performance metrics in the human resources department",
        "max_duration_hrs": 4,
        "stop_condition": "All metrics have been recorded for the month",
        "location_id": locations[8]["id"],
    },
    {
        "id": str(uuid.uuid4()),
        "agent_id": agents[7]["id"],
        "description": "Hack into the company's system in the executive suite",
        "max_duration_hrs": 8,
        "stop_condition": "Access has been gained to sensitive information",
        "location_id": locations[5]["id"],
    },
    {
        "id": str(uuid.uuid4()),
        "agent_id": agents[8]["id"],
        "description": "Clean the conference room",
        "max_duration_hrs": 5,
        "stop_condition": "The office is spotless",
        "location_id": locations[9]["id"],
    },
]


def main():
    print("🌱 seeding the db")
    supabase.table("Worlds").insert(worlds).execute()
    supabase.table("Locations").insert(locations).execute()
    supabase.table("Agents").insert(agents).execute()
    supabase.table("Plans").insert(plans).execute()
