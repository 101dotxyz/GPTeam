
import os

from src.utils.database.supabase import SubabaseDatabase
from src.utils.database.sqlite import SqliteDatabase


config_value = os.getenv("DATABASE_PROVIDER", "supabase")
database_class = SubabaseDatabase if config_value == "supabase" else SqliteDatabase
database = None


async def get_database():
    global database
    if database is None:
        database = await database_class.create()
    return database
