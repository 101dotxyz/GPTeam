import os

from src.utils.database.sqlite import SqliteDatabase

config_value = os.getenv("DATABASE_PROVIDER", "sqlite")

database_class = SqliteDatabase

if config_value == "supabase":
    from src.utils.database.supabase import SupabaseDatabase

    database_class = SupabaseDatabase

database = None


async def get_database():
    global database
    if database is None:
        database = await database_class.create()
    return database
