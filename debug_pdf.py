import pdfplumber
import sys

filename = "fp/25312000000327776462_838c.pdf"

if len(sys.argv) > 1:
    filename = sys.argv[1]

print(f"Inspecting {filename}...")

try:
    with pdfplumber.open(filename) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            print(f"--- Page {i+1} ---")
            print(text)
            print("--- End Page ---")
except Exception as e:
    print(f"Error: {e}")
