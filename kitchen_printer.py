import os
import time
import json
import datetime
import asyncio
import logging
import socket
from dotenv import load_dotenv
from supabase import create_async_client, AClient

# Configure logging
LOG_FILE = "kitchen_printer.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

# Attempt to import win32print, use mock if unavailable (for testing on Mac/Linux)
try:
    import win32print
    PRINTER_AVAILABLE = True
except ImportError:
    PRINTER_AVAILABLE = False
    logging.warning("win32print not found. Running in MOCK PRINTER mode.")

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
PRINTER_NAME = "MP-POS80"  # Adjust if your printer name is different

if not SUPABASE_URL or not SUPABASE_KEY:
    # Try parent .env for dev/testing
    parent_env = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    if os.path.exists(parent_env):
        logging.info(f"Loading credentials from {parent_env}")
        load_dotenv(parent_env)
        SUPABASE_URL = os.getenv("VITE_SUPABASE_URL")
        SUPABASE_KEY = os.getenv("VITE_SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    logging.error("SUPABASE_URL and SUPABASE_KEY must be set in .env file")
    print("\nCRITICAL ERROR: Missing Supabase credentials. Please check your .env file.\n")
    # Don't exit immediately, let the user see the error
    time.sleep(10)
    exit(1)

def check_internet_connection(host="8.8.8.8", port=53, timeout=3):
    """
    Check if there is an internet connection by trying to connect to Google's public DNS.
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error as ex:
        logging.error(f"No internet connection detected: {ex}")
        return False

def check_printer_available(printer_name):
    """
    Checks if the printer is available (Windows only).
    Returns True if available, False otherwise.
    """
    if not PRINTER_AVAILABLE:
        return True # Mock always available

    try:
        # Open the printer to check if it exists and is accessible
        hPrinter = win32print.OpenPrinter(printer_name)
        win32print.ClosePrinter(hPrinter)
        return True
    except Exception as e:
        logging.error(f"Printer '{printer_name}' not found or not accessible: {e}")
        return False

def format_receipt(order):
    """
    Formats the order data into a printable receipt string.
    """
    date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    order_id = order.get('id', 'UNKNOWN')[-8:] # Shorten ID for display
    customer_name = order.get('customer_name', 'Guest')
    customer_phone = order.get('customer_phone', '')
    dorm = order.get('dorm', '')
    items = order.get('items', [])
    total = order.get('total_amount', 0.0)
    notes = order.get('notes', '')

    receipt_lines = [
        "********************************",
        "    PIZZA APP KITCHEN RECEIPT",
        "********************************",
        f"Date: {date_str}",
        f"Order ID: #{order_id}",
        "--------------------------------",
        f"Customer: {customer_name}",
    ]
    
    if customer_phone:
        receipt_lines.append(f"Phone:    {customer_phone}")
    if dorm:
        receipt_lines.append(f"Location: {dorm}")
        
    payment_method = order.get('payment_method', 'Unknown')
    receipt_lines.append(f"Payment:  {payment_method}")
        
    receipt_lines.append("--------------------------------")
    receipt_lines.append("ITEMS:")
    
    # Check if items is a string (JSON) or list
    if isinstance(items, str):
        try:
            items = json.loads(items)
        except:
            items = []

    if isinstance(items, list):
        for item in items:
            qty = item.get('quantity', 1)
            name = item.get('name', 'Unknown Item')
            price = item.get('price', 0)
            
            receipt_lines.append(f"{qty}x {name:<20} ${price * qty:.2f}")
            
            # Handle customizations
            customizations = item.get('customizations', {})
            if customizations:
                if customizations.get('sauce'):
                    receipt_lines.append(f"   + Sauce: {customizations['sauce']}")
                if customizations.get('cheese'):
                    receipt_lines.append(f"   + Cheese: {customizations['cheese']}")
                if customizations.get('toppings'):
                    for topping in customizations['toppings']:
                        receipt_lines.append(f"   + Add: {topping}")
    
    receipt_lines.append("--------------------------------")
    receipt_lines.append(f"TOTAL:                    ${total:.2f}")
    
    if notes:
        receipt_lines.append("--------------------------------")
        receipt_lines.append("NOTES:")
        receipt_lines.append(notes)
        
    receipt_lines.append("********************************")
    receipt_lines.append("\n\n\n\n\n") # Feed lines for cutter
    
    return "\n".join(receipt_lines)

def print_raw(text):
    """
    Sends raw text to the printer, followed by a cut command.
    """
    # ESC/POS Commands
    # LF = b'\x0a'
    # GS V m = Cut Paper. m=66 is "Feed paper to cutting position and cut"
    CUT_COMMAND = b'\x1d\x56\x42\x00' 
    
    if PRINTER_AVAILABLE:
        try:
            hPrinter = win32print.OpenPrinter(PRINTER_NAME)
            try:
                hJob = win32print.StartDocPrinter(hPrinter, 1, ("Kitchen Receipt", None, "RAW"))
                try:
                    win32print.StartPagePrinter(hPrinter)
                    
                    # Encode text
                    encoded_text = text.encode('cp437', errors='ignore')
                    
                    # Send text + extra whitespace + cut command
                    # We add a few newlines (b'\n') to ensure text is past the cutter if the command handles it poorly
                    # But GS V 66 usually feeds automatically. We'll send both to be safe.
                    final_payload = encoded_text + b'\n\n\n' + CUT_COMMAND
                    
                    win32print.WritePrinter(hPrinter, final_payload)
                    win32print.EndPagePrinter(hPrinter)
                finally:
                    win32print.EndDocPrinter(hPrinter)
            finally:
                win32print.ClosePrinter(hPrinter)
            logging.info(f"Successfully printed receipt.")
        except Exception as e:
            logging.error(f"Failed to print to {PRINTER_NAME}: {e}")
            logging.info("Dumping receipt to console:")
            print(text)
    else:
        logging.info("--- MOCK PRINTER OUTPUT START ---")
        print(text)
        logging.info("--- CUT COMMAND WOULD BE SENT HERE ---")
        logging.info("--- MOCK PRINTER OUTPUT END ---")

def handle_new_order(payload):
    """
    Callback for new order events.
    """
    logging.info("New order received!")
    # logging.debug(f"Payload raw: {payload}")
    
    try:
        # Debugging shown payload: {'data': {'record': {...}}} or similar
        # Check standard Realtime structures
        if hasattr(payload, 'new'):
            new_order = payload.new
        elif isinstance(payload, dict):
            # 1. Standard dict payload
            if 'new' in payload:
                new_order = payload['new']
            # 2. Nested data.record (as seen in user logs)
            elif 'data' in payload and isinstance(payload['data'], dict) and 'record' in payload['data']:
                new_order = payload['data']['record']
            # 3. Direct record key
            elif 'record' in payload:
                new_order = payload['record']
            else:
                new_order = None
        else:
            # Fallback for object with data attr
            if hasattr(payload, 'data') and isinstance(payload.data, dict) and 'record' in payload.data:
                 new_order = payload.data['record']
            else:
                new_order = None
    except Exception as e:
        logging.error(f"Extraction error: {e}")
        new_order = None 

    if new_order:
        try:
            receipt_text = format_receipt(new_order)
            print_raw(receipt_text)
        except Exception as e:
            logging.error(f"Error formatting or printing receipt: {e}")
    else:
        logging.error("Could not extract order data from payload")

async def main():
    print(f"\n{'='*40}")
    print(f"   PIZZA APP KITCHEN PRINTER SERVICE")
    print(f"{'='*40}\n")
    
    logging.info(f"Starting Service...")
    
    # 1. Check Internet
    print("Checking Internet Connection...", end=" ", flush=True)
    while not check_internet_connection():
        print("FAILED!")
        logging.error("No Internet connection. Retrying in 5 seconds...")
        print("   >> ERROR: No Internet detected! Please check your WiFi.")
        print("   >> Retrying in 5 seconds...", end=" ", flush=True)
        await asyncio.sleep(5)
        print("Retrying...", end=" ", flush=True)
    print("OK!")
    
    # 2. Check Printer
    print(f"Checking Printer ({PRINTER_NAME})...", end=" ", flush=True)
    if check_printer_available(PRINTER_NAME):
        print("OK!")
    else:
        print("FAILED!")
        logging.error(f"Printer {PRINTER_NAME} not found.")
        print(f"   >> ERROR: Printer '{PRINTER_NAME}' not found or offline!")
        print("   >> Please check USB connection and power.")
        print("   >> The script will continue, but printing will fail.")
        
    print(f"Connecting to Supabase...", end=" ", flush=True)
    
    try:
        # Initialize Async Supabase client
        supabase: AClient = await create_async_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Subscribe to the orders table
        channel = supabase.channel('schema-db-changes')
        
        await channel.on_postgres_changes(
            event='INSERT',
            schema='public',
            table='orders',
            callback=handle_new_order
        ).subscribe()

        print("OK!")
        print(f"\n{'-'*40}")
        print("   SERVICE RUNNING - WAITING FOR ORDERS")
        print(f"{'-'*40}\n")
        logging.info("Subscribed to 'orders' INSERT events. Ready.")

        # Keep the script running
        while True:
            # Optional: Periodic connection check could go here
            await asyncio.sleep(1)
            
    except Exception as e:
        logging.critical(f"Fatal error in main loop: {e}")
        print(f"\nCRITICAL ERROR: {e}\n")
        
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Stopping service (KeyboardInterrupt)...")
        print("\nStopping service...")
    except Exception as e:
        logging.critical(f"Unhandled exception: {e}")
        print(f"\nCRITICAL ERROR: {e}")
        time.sleep(5)
