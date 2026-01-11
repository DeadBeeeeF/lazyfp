# LazyFP (Lazy Fa Piao) / 懒人发票

LazyFP is a web-based tool designed to simplify the management, organization, and export of electronic invoices (PDFs). It scans, parses, groups, and renames invoices automatically, saving you time during reimbursement processes.

## Features

- **Web UI**: specialized interface to manage local invoice files.
- **Auto-Parsing**: Automatically extracts key information (Invoice No, Date, Amount, Seller, Purchaser) from PDF invoices.
- **Deduplication**: Identifies and moves duplicate invoices to a `dump/` folder.
- **Organization**: Sorts invoices into folders by `Purchaser/Quarter` and standardizes filenames (`Suffix-Seller-Amount.pdf`).
- **Export**: Generates a ZIP file for a specific quarter containing all organized invoices and a summary Excel sheet.

## Installation

1. **Clone the repository**:

    ```bash
    git clone https://github.com/YourUsername/lazyfp.git
    cd lazyfp
    ```

2. **Install dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

## Usage

1. **Start the server**:

    ```bash
    python app.py
    # OR
    uvicorn app:app --host 0.0.0.0 --port 8000
    ```

2. **Open the Web UI**:
    Go to `http://localhost:8000` in your browser.

3. **Workflow**:
    - **Upload**: Drag and drop PDF invoices or place them in the `fp/` directory.
    - **Scan**: The system parses the files.
    - **Deduplicate**: Click to remove duplicates.
    - **Organize**: Click to sort files into folders and rename them.
    - **Export**: Select a Purchaser and Quarter to download a ZIP package.

## Project Structure

- `app.py`: FastAPI backend and API routes.
- `main.py`: Core invoice processing logic (parsing, regex).
- `static/`: Frontend HTML/JS.
- `fp/`: Default directory for invoice input and organization.
- `fp/organized/`: Destination for organized invoices.
- `fp/dump/`: Destination for duplicate invoices.
- `requirements.txt`: Python dependencies.

## License

MIT
