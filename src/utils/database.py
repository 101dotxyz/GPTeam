from dotenv import load_dotenv

load_dotenv()
import os

from supabase import Client, create_client

url: str = (
    os.environ.get("SUPABASE_DEV_URL")
    if os.environ.get("ENV") == "dev"
    else os.environ.get("SUPABASE_PROD_URL")
)
key: str = (
    os.environ.get("SUPABASE_DEV_KEY")
    if os.environ.get("ENV") == "dev"
    else os.environ.get("SUPABASE_PROD_KEY")
)
supabase: Client = create_client(url, key)
