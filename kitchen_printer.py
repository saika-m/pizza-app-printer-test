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

# ESC/POS Constants
ESC = b'\x1b'
GS = b'\x1d'
LF = b'\x0a'

# Commands
INIT_PRINTER = ESC + b'@'
CUT_PAPER = GS + b'V\x42\x00'

# Text Format
TXT_NORMAL = ESC + b'!\x00'
TXT_2HEIGHT = ESC + b'!\x10'
TXT_2WIDTH = ESC + b'!\x20'
TXT_4SIZE = ESC + b'!\x30' # Double Width & Height (Big)

BOLD_ON = ESC + b'E\x01'
BOLD_OFF = ESC + b'E\x00'

ALIGN_LEFT = ESC + b'a\x00'
ALIGN_CENTER = ESC + b'a\x01'
ALIGN_RIGHT = ESC + b'a\x02'

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

def format_receipt_text(order):
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

def format_receipt_bytes(order):
    """
    Formats the order data into a printable byte string with ESC/POS commands.
    """
    cmds = []
    
    # Safe helper
    def add_text(text, align=ALIGN_LEFT, style=TXT_NORMAL, bold=False):
        cmds.append(align)
        cmds.append(style)
        if bold: cmds.append(BOLD_ON)
        else: cmds.append(BOLD_OFF)
        cmds.append(text.encode('cp437', errors='ignore'))
        cmds.append(LF)
    
    # Initialize
    cmds.append(INIT_PRINTER)
    
    # ---------------- HEADER ----------------
    add_text("PIZZA KITCHEN", align=ALIGN_CENTER, style=TXT_2HEIGHT, bold=True)
    add_text("--------------------------------", align=ALIGN_CENTER)
    
    # Date & Order ID
    date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    order_id = order.get('id', 'UNKNOWN')[-8:]
    add_text(f"Date: {date_str}")
    add_text(f"Order ID: #{order_id}", bold=True)
    add_text("--------------------------------")

    # ---------------- CUSTOMER ----------------
    customer_name = order.get('customer_name', 'Guest')
    customer_phone = order.get('customer_phone', '')
    dorm = order.get('dorm', '')
    
    add_text(f"Customer: {customer_name}")
    if customer_phone:
        add_text(f"Phone:    {customer_phone}")
        
    # --- BIG DORM LOCATION ---
    if dorm:
        cmds.append(LF)
        add_text(f"DELIVERY TO:", align=ALIGN_LEFT, style=TXT_NORMAL, bold=True)
        # MAKE IT BIG!
        add_text(f"{dorm}", align=ALIGN_CENTER, style=TXT_4SIZE, bold=True)
        cmds.append(LF)
        
    # --- PAYMENT METHOD ---
    payment_method = order.get('payment_method', 'Unknown')
    add_text(f"Payment: {payment_method}", style=TXT_2HEIGHT, bold=True)

    add_text("--------------------------------")
    
    # ---------------- ITEMS ----------------
    add_text("ITEMS:", bold=True)
    
    items = order.get('items', [])
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
            
            # Print Item Line
            item_line = f"{qty}x {name}"
            # Align price to right if possible, but for now simple format
            add_text(item_line, bold=True)
            
            # Customizations
            customizations = item.get('customizations', {})
            if customizations:
                if customizations.get('sauce'):
                    add_text(f"   + Sauce: {customizations['sauce']}")
                if customizations.get('cheese'):
                    add_text(f"   + Cheese: {customizations['cheese']}")
                if customizations.get('toppings'):
                    for topping in customizations['toppings']:
                        add_text(f"   + Add: {topping}")
            
            cmds.append(LF) # Extra space between items

    # ---------------- TOTAL ----------------
    total = order.get('total_amount', 0.0)
    add_text("--------------------------------")
    add_text(f"TOTAL: ${total:.2f}", style=TXT_2HEIGHT, bold=True)
    
    # ---------------- NOTES ----------------
    notes = order.get('notes', '')
    if notes:
        add_text("--------------------------------")
        add_text("NOTES:", bold=True)
        add_text(notes, style=TXT_2HEIGHT) # Bigger notes for visibility
        
    # Footer
    cmds.append(LF)
    cmds.append(LF)
    cmds.append(LF)
    cmds.append(CUT_PAPER)
    
    return b''.join(cmds)

def print_raw(data):
    """
    Sends raw bytes or text to the printer.
    If 'data' is str, converts to bytes + Cut.
    If 'data' is bytes, sends as-is.
    """
    
    final_payload = b''
    
    if isinstance(data, str):
        # Legacy behavior for string input
        encoded_text = data.encode('cp437', errors='ignore')
        final_payload = encoded_text + b'\n\n\n' + CUT_PAPER
    elif isinstance(data, bytes):
        final_payload = data
    else:
        logging.error("print_raw received unknown type")
        return
    
    if PRINTER_AVAILABLE:
        try:
            hPrinter = win32print.OpenPrinter(PRINTER_NAME)
            try:
                hJob = win32print.StartDocPrinter(hPrinter, 1, ("Kitchen Receipt", None, "RAW"))
                try:
                    win32print.StartPagePrinter(hPrinter)
                    win32print.WritePrinter(hPrinter, final_payload)
                    win32print.EndPagePrinter(hPrinter)
                finally:
                    win32print.EndDocPrinter(hPrinter)
            finally:
                win32print.ClosePrinter(hPrinter)
            logging.info(f"Successfully printed receipt.")
        except Exception as e:
            logging.error(f"Failed to print to {PRINTER_NAME}: {e}")
            logging.info("Dumping hex payload for debug:")
            # logging.info(final_payload.hex()) 
    else:
        logging.info("--- MOCK PRINTER OUTPUT START ---")
        if isinstance(data, str):
            print(data)
        else:
            try:
                # Try to decode for display
                print(final_payload.decode('cp437', errors='replace'))
            except:
                print(f"[Binary Data: {len(final_payload)} bytes]")
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
            # Generate LOG version
            log_text = format_receipt_text(new_order)
            logging.info("Receipt Content:\n" + log_text)
            
            # Generate PRINT version (bytes)
            print_payload = format_receipt_bytes(new_order)
            print_raw(print_payload)
            
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
