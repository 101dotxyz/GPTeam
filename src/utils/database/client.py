import os

import dotenv

from src.utils.database.sqlite import SqliteDatabase

dotenv.load_dotenv()

database_provider = os.getenv("DATABASE_PROVIDER", "sqlite")


database_class = SqliteDatabase

if database_provider == "supabase":
    from src.utils.database.supabase import SupabaseDatabase

    database_class = SupabaseDatabase

database = None


async def get_database():
    global database
    if database is None:
        database = await database_class.create()
    return database
