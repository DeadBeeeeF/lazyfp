import pandas as pd
import sys

# Set display options to see full content
pd.set_option('display.max_columns', None)
pd.set_option('display.max_colwidth', None)
pd.set_option('display.width', 1000)

try:
    df = pd.read_excel("invoice_summary.xlsx")
    print(f"Total Rows: {len(df)}")
    print(f"Columns: {df.columns.tolist()}")
    
    print("\n--- Sample Rows (First 5) ---")
    print(df.head(5))
    
    print("\n--- Rows with multiple files (Duplicates) ---")
    dupes = df[df['count'] > 1]
    if not dupes.empty:
        print(dupes.head(5))
    else:
        print("No duplicates found.")

    print("\n--- Rows with Missing Data ---")
    missing = df[df.isnull().any(axis=1)]
    if not missing.empty:
        print(missing)
    else:
        print("No missing data detected (NaN).")

    print("\n--- Data Types ---")
    print(df.dtypes)

except Exception as e:
    print(f"Error: {e}")
