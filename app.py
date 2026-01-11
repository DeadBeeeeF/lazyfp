
import os
import shutil
import aiofiles
from fastapi import FastAPI, UploadFile, File, HTTPException
import io
import zipfile
from openpyxl import Workbook
from fastapi.responses import FileResponse, StreamingResponse
from fastapi import BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import List
import re
import logging

# Import refactored logic
from main import process_invoices, scan_directory, INPUT_DIR, OUTPUT_FILE

# Initialize App
app = FastAPI(title="LazyFP WebUI")

# CORS (Allow all for local dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure dirs exist
if not os.path.exists(INPUT_DIR):
    os.makedirs(INPUT_DIR)

if not os.path.exists("static"):
    os.makedirs("static")

# --- Routes ---

@app.get("/")
async def read_root():
    return FileResponse("static/index.html")

@app.get("/api/invoices")
async def get_invoices():
    """
    Returns the processed list of invoices.
    """
    try:
        df = process_invoices(INPUT_DIR)
        if df.empty:
            return []
        
        # Convert NaN to None for JSON compatibility
        records = df.where(pd.notnull(df), None).to_dict(orient="records")
        return records
    except Exception as e:
        logging.error(f"Error fetching invoices: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scan")
async def scan_invoices():
    """
    Triggers a fresh scan and returns the result.
    """
    return await get_invoices()

@app.post("/api/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """
    Uploads PDF files to the input directory.
    """
    uploaded_counts = 0
    for file in files:
        if not file.filename.lower().endswith(".pdf"):
            continue
            
        file_path = os.path.join(INPUT_DIR, file.filename)
        try:
            async with aiofiles.open(file_path, 'wb') as out_file:
                content = await file.read()
                await out_file.write(content)
            uploaded_counts += 1
        except Exception as e:
            logging.error(f"Failed to upload {file.filename}: {e}")
            
    return {"message": f"Successfully uploaded {uploaded_counts} files"}

@app.delete("/api/invoices/{filename}")
async def delete_invoice(filename: str):
    """
    Deletes a specific PDF file.
    Note: The filename provided might be a comma-separated list if grouped, 
    but for deletion we usually expect a single file or a specific target.
    Logic: If it's a single file, delete it.
    """
    # Security check: simple sanitize
    safe_name = os.path.basename(filename)
    path = os.path.join(INPUT_DIR, safe_name)
    
    if os.path.exists(path):
        try:
            os.remove(path)
            return {"message": f"Deleted {safe_name}"}
        except Exception as e:
             raise HTTPException(status_code=500, detail=str(e))
    else:
        raise HTTPException(status_code=404, detail="File not found")

@app.post("/api/deduplicate")
async def deduplicate_invoices():
    """
    Moves duplicate invoices to the 'dump' folder, keeping one copy.
    """
    import shutil
    
    df = process_invoices(INPUT_DIR)
    if df.empty:
        return {"message": "No invoices to process.", "moved_count": 0}
        
    dump_dir = os.path.join(INPUT_DIR, "dump")
    if not os.path.exists(dump_dir):
        os.makedirs(dump_dir)
        
    moved_count = 0
    
    # Iterate over grouped data
    # The process_invoices already groups by invoice_no.
    # We need to find groups where 'count' > 1.
    # However, process_invoices returns aggregated string for filename "a.pdf, b.pdf".
    
    duplicates = df[df["count"] > 1]
    
    for _, row in duplicates.iterrows():
        filenames = row["filename"].split(", ")
        # Keep the first one, move the rest
        to_move = filenames[1:]
        
        for fname in to_move:
            src = os.path.join(INPUT_DIR, fname)
            dst = os.path.join(dump_dir, fname)
            
            if os.path.exists(src):
                try:
                    # Handle name collision in dump
                    if os.path.exists(dst):
                        base, ext = os.path.splitext(fname)
                        dst = os.path.join(dump_dir, f"{base}_{int(datetime.now().timestamp())}{ext}")
                        
                    shutil.move(src, dst)
                    moved_count += 1
                except Exception as e:
                    logging.error(f"Failed to move {fname}: {e}")
                    
    return {"message": f"Deduplication complete. Moved {moved_count} files to 'dump/'.", "moved_count": moved_count}

@app.post("/api/organize")
async def organize_invoices():
    """
    Organizes processed invoices into folders by Purchaser -> Quarter.
    Renames files to: {Last6Digits}-{Seller}-{Amount}.pdf
    """
    import shutil
    
    # Get RAW data for all files
    data_list = scan_directory(INPUT_DIR)
    
    organized_base = os.path.join(INPUT_DIR, "organized")
    if not os.path.exists(organized_base):
        os.makedirs(organized_base)
        
    count = 0
    errors = 0
    
    for item in data_list:
        try:
            filename = item.get("filename")
            src_path = os.path.join(INPUT_DIR, filename)
            
            if not os.path.exists(src_path):
                continue
                
            # Get metadata
            purchaser = item.get("purchaser") or "Unknown Purchaser"
            # Recalculate quarter effectively or rely on what's in item if we put it there?
            # scan_directory doesn't add 'quarter' column, process_invoices does.
            # We need to compute it.
            from main import get_quarter
            date_str = item.get("date")
            quarter = get_quarter(str(date_str))
            
            seller = item.get("seller") or "Unknown Seller"
            invoice_no = item.get("invoice_no") or "000000"
            amount = item.get("total_amount")
            if amount is not None:
                amount = f"{float(amount):.2f}"
            else:
                amount = "0.00"
                
            # Create Target Dir
            # Clean purchaser name slightly for path safety
            safe_purchaser = re.sub(r'[\\/*?:"<>|]', "", purchaser).strip()
            target_dir = os.path.join(organized_base, safe_purchaser, quarter)
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
                
            # Format New Filename: Last 6 digits - Seller - Amount
            # If invoice_no is short, pad with 0? Or just take what we have.
            # Req: "发票号后6位" (Last 6 digits)
            # If invalid, "0补足" (pad with 0)
            
            # Clean invoice no (digits in item are already extracted string)
            inv_str = str(invoice_no)
            if len(inv_str) >= 6:
                inv_suffix = inv_str[-6:]
            else:
                inv_suffix = inv_str.zfill(6)
            
            # Safe seller name
            safe_seller = re.sub(r'[\\/*?:"<>|]', "", seller).strip()
            
            new_name = f"{inv_suffix}-{safe_seller}-{amount}.pdf"
            dst_path = os.path.join(target_dir, new_name)
            
            # Copy (preserve original)
            shutil.copy2(src_path, dst_path)
            count += 1
        except Exception as e:
            logging.error(f"Error organizing {item}: {e}")
            errors += 1
            
    return {"message": f"Organized {count} files.", "errors": errors}

@app.get("/api/export/{purchaser}/{quarter}")
async def export_quarter_zip(purchaser: str, quarter: str):
    """
    Exports a ZIP of the organized folder for a specific Purchaser and Quarter.
    Includes a summary Excel file.
    """
    import re
    
    # Path safety
    # We must allow decode because URL params are decoded by FastAPI? Yes.
    # But clean path traversal just in case
    safe_purchaser = re.sub(r'[\\/*?:"<>|]', "", purchaser).strip()
    safe_quarter = re.sub(r'[\\/*?:"<>|]', "", quarter).strip()
    
    target_dir = os.path.join(INPUT_DIR, "organized", safe_purchaser, safe_quarter)
    
    if not os.path.exists(target_dir):
        # Maybe user hasn't organized yet, or name mismatch
        # Fix: Provide clear error
        raise HTTPException(status_code=400, detail="Folder not found. Please click 'Organize' first.")
        
    # Create ZIP in memory
    mem_zip = io.BytesIO()
    
    files_to_zip = [f for f in os.listdir(target_dir) if f.lower().endswith(".pdf")]
    
    # Prepare Summary Data
    summary_data = []
    total_amount = 0.0
    
    with zipfile.ZipFile(mem_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for fname in files_to_zip:
            fpath = os.path.join(target_dir, fname)
            zf.write(fpath, arcname=fname)
            
            # Parse filename back to summary? 
            # Or better: Extract info from our cache for these files?
            # Issue: The organized filenames {Suffix}-{Seller}-{Amount} don't have full info (Date, Full ID).
            # The user asked for "Quarter Summary".
            # We can try to re-match the original files or just parse what we can.
            # Or we can iterate current `process_invoices` data and filter by P/Q matching this export.
            # Iterating `scan_directory` again is safer to get full metadata.
            
            # Parse filename for basic info if needed, but scanning directory allows finding the *original* metadata 
            # if we can link them? No, inside zip we just have the renamed file.
            
            # Better approach: Recalculate summary from `scan_directory(INPUT_DIR)` 
            # filtering by Purchaser and Quarter.
            pass

    # Generate Summary Excel
    # Filter raw data
    raw_data = scan_directory(INPUT_DIR)
    from main import get_quarter
    
    sheet_rows = []
    
    for item in raw_data:
        p = item.get("purchaser") or "Unknown"
        d = item.get("date")
        q = get_quarter(str(d))
        
        # Match current export target
        # Do fuzzy match? Or exact? The file structure was created using exact strings from extraction.
        # So we should match exact.
        if p == purchaser and q == quarter:
             amt = float(item.get("total_amount") or 0)
             total_amount += amt
             sheet_rows.append({
                 "Date": d,
                 "Invoice No": item.get("invoice_no"),
                 "Seller": item.get("seller"),
                 "Amount": amt,
                 "Filename": item.get("filename") # Original filename
             })
             
    # Create Excel
    wb = Workbook()
    ws = wb.active
    ws.title = "Summary"
    ws.append(["Date", "Invoice No", "Seller", "Amount", "Original Filename"])
    
    for row in sheet_rows:
        ws.append([row["Date"], row["Invoice No"], row["Seller"], row["Amount"], row["Filename"]])
        
    # Add Total
    ws.append(["", "", "Total", total_amount, ""])
    
    # Save Excel to Zip
    excel_io = io.BytesIO()
    wb.save(excel_io)
    excel_io.seek(0)
    
    with zipfile.ZipFile(mem_zip, mode="a", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"{safe_quarter}_Summary.xlsx", excel_io.getvalue())
        
    mem_zip.seek(0)
    
    zip_filename = f"{safe_purchaser}-{safe_quarter}-{total_amount:.2f}.zip"
    
    # Return (headers for download)
    from urllib.parse import quote
    encoded_name = quote(zip_filename)
    
    return StreamingResponse(
        mem_zip, 
        media_type="application/zip", 
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_name}"}
    )

# Global import for datetime
from datetime import datetime

# Global import for pandas (needed inside routes)
import pandas as pd

# Mount static files (ensure this is last to avoid overriding API routes)
app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
