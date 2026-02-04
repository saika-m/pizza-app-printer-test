import win32print
import datetime

def print_receipt(printer_name="MP-POS80"):
    """
    Prints a sample pizza receipt to the specified printer using raw bytes.
    """
    try:
        # Open the printer
        hPrinter = win32print.OpenPrinter(printer_name)
        try:
            # Start a document
            hJob = win32print.StartDocPrinter(hPrinter, 1, ("Pizza Order", None, "RAW"))
            try:
                win32print.StartPagePrinter(hPrinter)
                
                # Receipt content
                # ESC/POS commands can be added here if needed (e.g., formatting)
                # For now, just plain text with some layout
                # \n is line feed.
                
                date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                receipt_text = f"""
********************************
        PIZZA SCRIPT TEST
********************************
Date: {date_str}

Order #12345
--------------------------------
1x  Pepperoni Pizza       $15.00
1x  Coca Cola              $2.50
--------------------------------
TOTAL:                    $17.50
********************************
    Thank you for your order!
********************************
\n\n\n\n\n
"""
                # Send data to printer
                # Encode to bytes (defaulting to utf-8 or cp437 for printers)
                # Many receipts use code pages, but simple text often works.
                win32print.WritePrinter(hPrinter, receipt_text.encode('utf-8'))
                
                win32print.EndPagePrinter(hPrinter)
            finally:
                win32print.EndDocPrinter(hPrinter)
        finally:
            win32print.ClosePrinter(hPrinter)
            
        print(f"Successfully sent Job #{hJob} to printer '{printer_name}'")
        
    except Exception as e:
        print(f"Failed to print to '{printer_name}': {e}")
        print("Available printers:")
        for p in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS):
            print(f"- {p[2]}")

if __name__ == "__main__":
    # You might want to get this from input or args, but defaulting for the test
    target_printer = "MP-POS80" 
    print(f"Attempting to print to: {target_printer}")
    print_receipt(target_printer)
