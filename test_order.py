import os
import asyncio
from dotenv import load_dotenv
from supabase import create_async_client

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

async def main():
    if not SUPABASE_URL:
        # Try parent .env
        parent_env = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
        if os.path.exists(parent_env):
            print(f"Loading credentials from {parent_env}")
            load_dotenv(parent_env)
            
    url = os.getenv("VITE_SUPABASE_URL") or SUPABASE_URL
    key = os.getenv("VITE_SUPABASE_ANON_KEY") or SUPABASE_KEY
    
    if not url or not key:
        print("Missing credentials")
        return

    supabase = await create_async_client(url, key)
    
    print("Inserting test order...")
    # Using correct syntax: await supabase.table("orders").insert({...}).execute()
    # And correct response access: response.data[0]
    try:
        response = await supabase.table("orders").insert({
            "customer_name": "Debug Test",
            "customer_email": "debug@example.com",
            "customer_phone": "555-DEBUG",
            "items": '[{"name": "Debug Pizza", "quantity": 1, "price": 0}]',
            "total_amount": 0.0,
            "status": "pending",
            "notes": "Debug order for payload inspection"
        }).execute()
        
        if hasattr(response, 'data') and response.data:
             print(f"Order inserted: {response.data[0].get('id')}")
        else:
             print(f"Result: {response}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
