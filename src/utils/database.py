from dotenv import load_dotenv

load_dotenv()
import os

from supabase import Client, create_client

url: str = os.environ.get("SUPABASE_DEV_URL")
key: str = os.environ.get("SUPABASE_DEV_KEY")
supabase: Client = create_client(url, key)
