
import os
import pdfplumber
import logging
from main import extract_invoice_data

# Setup logging to console
logging.basicConfig(level=logging.INFO, format='%(message)s')

TARGET_FILE = "fp/2101474183-31111990035-202509.pdf"

def analyze_pdf(path):
    print(f"Analyzing {path}...")
    if not os.path.exists(path):
        print("File not found.")
        return

    with pdfplumber.open(path) as pdf:
        # Full text extraction
        full_text = ""
        for page in pdf.pages:
            full_text += page.extract_text() or ""
            
    print("-" * 40)
    print("RAW TEXT CONTENT:")
    print("-" * 40)
    print(full_text)
    print("-" * 40)
    
    # Flattened text (as used in main.py)
    text_flat = full_text.replace("\n", "").replace(" ", "")
    print("FLATTENED TEXT:")
    print("-" * 40)
    print(text_flat)
    print("-" * 40)

    # Attempt extraction
    print("Attempting Extraction...")
    data = extract_invoice_data(path)
    print("Extracted Data:", data)
    
    if data and data['invoice_no']:
        print(f"SUCCESS: Found Invoice No: {data['invoice_no']}")
    else:
        print("FAILURE: Invoice No not found.")

if __name__ == "__main__":
    analyze_pdf(TARGET_FILE)
