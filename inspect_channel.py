import asyncio
import os
from dotenv import load_dotenv
from supabase import create_async_client

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

async def main():
    if not SUPABASE_URL:
        # Try parent .env for dev/testing
        parent_env = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
        if os.path.exists(parent_env):
            print(f"Loading credentials from {parent_env}")
            load_dotenv(parent_env)
    
    url = os.getenv("VITE_SUPABASE_URL") or SUPABASE_URL
    key = os.getenv("VITE_SUPABASE_ANON_KEY") or SUPABASE_KEY

    supabase = await create_async_client(url, key)
    channel = supabase.channel('test')
    print("Channel details:")
    print(dir(channel))
    print("Type:", type(channel))

if __name__ == "__main__":
    asyncio.run(main())
