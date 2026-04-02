import os
import asyncio
from dotenv import load_dotenv
from supabase import create_async_client
from kitchen_printer import format_receipt_text, format_receipt_bytes, print_raw

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

async def main():
    if not SUPABASE_URL:
        # Try parent .env
        parent_env = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
        if os.path.exists(parent_env):
            load_dotenv(parent_env)
            
    url = os.getenv("VITE_SUPABASE_URL") or SUPABASE_URL
    key = os.getenv("VITE_SUPABASE_ANON_KEY") or SUPABASE_KEY
    
    if not url or not key:
        print("Missing credentials")
        return

    supabase = await create_async_client(url, key)
    
    order_id = "413d26d1-5785-4baf-bc31-40f441bdbe8e"
    print(f"Fetching order {order_id}...")
    try:
        response = await supabase.table("orders").select("*").eq("id", order_id).execute()
        
        if hasattr(response, 'data') and response.data:
            order_data = response.data[0]
            print("\n----- MOCK RECEIPT PREVIEW (TEXT FORMAT) -----")
            print(format_receipt_text(order_data))
            
            print("\n----- MOCK RECEIPT PREVIEW (RAW MOCK OUTPUT) -----")
            print_payload = format_receipt_bytes(order_data)
            print_raw(print_payload)
        else:
             print(f"Order {order_id} not found: {response}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
