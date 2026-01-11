
import asyncio
import os
import shutil
import logging
from app import organize_invoices, export_quarter_zip, INPUT_DIR

# Setup logging
logging.basicConfig(level=logging.INFO)

async def test_organize_and_export():
    print("Testing Organization...")
    # Clear previous run
    org_dir = os.path.join(INPUT_DIR, "organized")
    if os.path.exists(org_dir):
        shutil.rmtree(org_dir)
        
    # Run Organize
    res = await organize_invoices()
    print(f"Organize Result: {res}")
    
    # Verify Directory
    if os.path.exists(org_dir):
        print("SUCCESS: Organized directory created.")
        purchasers = os.listdir(org_dir)
        print(f"Purchasers found: {purchasers}")
        
        if purchasers:
             p = purchasers[0]
             q_dir = os.path.join(org_dir, p)
             if os.path.isdir(q_dir):
                 quarters = os.listdir(q_dir)
                 print(f"Quarters for {p}: {quarters}")
                 
                 if quarters:
                     q = quarters[0]
                     # Test Export
                     print(f"Testing Export for {p} / {q}...")
                     response = await export_quarter_zip(p, q)
                     print("Export Response headers:", response.headers)
                     print("SUCCESS: Export response received.")
    else:
        print("FAILURE: Organized directory NOT created.")

if __name__ == "__main__":
    asyncio.run(test_organize_and_export())
