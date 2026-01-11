
import sys
import os

try:
    from main import process_invoices, INPUT_DIR
    from app import app, deduplicate_invoices
    print("Imports successful")
    
    # Test logic
    df = process_invoices(INPUT_DIR)
    print(f"Processed {len(df)} records")
    
    # Check deduplicate function existence
    if deduplicate_invoices:
         print("Deduplication endpoint found")
    
except Exception as e:
    print(f"Verification failed: {e}")
    sys.exit(1)
