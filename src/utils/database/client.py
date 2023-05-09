
import os

from src.utils.database.supabase import SubabaseDatabase


config_value = os.getenv("DATABASE_PROVIDER", "supabase")
database_class = SubabaseDatabase if config_value == "supabase" else None
database = None


async def get_database():
    global database
    if database is None:
        database = await database_class.create()
    return database
