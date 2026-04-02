try:
    import win32print
    PRINTER_AVAILABLE = True
except ImportError:
    PRINTER_AVAILABLE = False
    print("win32print not found. Running in MOCK PRINTER mode.")

import datetime

def print_receipt(printer_name="MP-POS80"):
    """
    Prints a sample pizza receipt to the specified printer using raw bytes.
    """
    date_str = datetime.datetime.now().strftime("%a, %b %d %Y %I:%M %p")
    
    receipt_text = f"""
********************************
        PIZZA SCRIPT TEST
********************************
Date: {date_str}

Order #12345
--------------------------------
1x  Pepperoni Pizza (14")  $15.00
1x  Custom Pizza (16")     $18.00
   + Sauce: Garlic
   + Cheese: Extra Mozzarella
   + Bacon
--------------------------------
TOTAL:                    $17.50
********************************
    Thank you for your order!
********************************
\n\n\n\n\n
"""

    if not PRINTER_AVAILABLE:
        print("--- MOCK PRINTER OUTPUT ---")
        print(receipt_text)
        print("--- MOCK PRINTER CUT ---")
        return

    try:
        # Open the printer
        hPrinter = win32print.OpenPrinter(printer_name)
        try:
            # Start a document
            hJob = win32print.StartDocPrinter(hPrinter, 1, ("Pizza Order", None, "RAW"))
            try:
                win32print.StartPagePrinter(hPrinter)
                
                # Send data to printer
                win32print.WritePrinter(hPrinter, receipt_text.encode('utf-8'))
                
                win32print.EndPagePrinter(hPrinter)
            finally:
                win32print.EndDocPrinter(hPrinter)
        finally:
            win32print.ClosePrinter(hPrinter)
            
        print(f"Successfully sent Job #{hJob} to printer '{printer_name}'")
        
    except Exception as e:
        print(f"Failed to print to '{printer_name}': {e}")
        try:
            print("Available printers:")
            for p in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS):
                print(f"- {p[2]}")
        except:
            pass

if __name__ == "__main__":
    # You might want to get this from input or args, but defaulting for the test
    target_printer = "MP-POS80" 
    print(f"Attempting to print to: {target_printer}")
    print_receipt(target_printer)
