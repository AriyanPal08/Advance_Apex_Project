import pandas as pd
import sys
import os
from datetime import datetime

# =============================================================================
# BITS Pilani Apex Project
# Problem P5 - BFSI Compliance Automation Pipeline
# =============================================================================

INPUT_FILE = "complaints.csv"
OUTPUT_FILE = "cfpb_raw_2022_2024.csv"
CHUNK_SIZE = 100000
START_YEAR = 2022
END_YEAR = 2024
TARGET_ROWS = 350000

REQUIRED_COLUMNS = [
    "Date received",
    "Product",
    "Sub-product",
    "Issue",
    "Sub-issue",
    "Consumer complaint narrative",
    "Company public response",
    "Company",
    "State",
    "ZIP code",
    "Tags",
    "Submitted via",
    "Date sent to company",
    "Company response to consumer",
    "Timely response?",
    "Complaint ID"
]

def print_header():
    print("=" * 80)
    print("BFSI Compliance Automation Pipeline - Data Filter")
    print("=" * 80)

def validate_columns(columns):
    missing = [col for col in REQUIRED_COLUMNS if col not in columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

def process_dataset():
    total_rows = 0
    filtered_rows = 0
    filtered_chunks = []
    chunk_number = 0

    print("Reading and filtering dataset in chunks...")
    
    for chunk in pd.read_csv(INPUT_FILE, chunksize=CHUNK_SIZE, low_memory=False):
        chunk_number += 1
        
        if chunk_number == 1:
            validate_columns(chunk.columns)
            
        rows_in_chunk = len(chunk)
        total_rows += rows_in_chunk
        
        # Handle timezones and convert to datetime
        chunk["Date received"] = pd.to_datetime(chunk["Date received"], errors="coerce", utc=True).dt.tz_localize(None)
        chunk["Date sent to company"] = pd.to_datetime(chunk["Date sent to company"], errors="coerce", utc=True).dt.tz_localize(None)
        
        filtered_chunk = chunk[chunk["Date received"].dt.year.between(START_YEAR, END_YEAR)].copy()
        
        filtered_rows += len(filtered_chunk)
        filtered_chunks.append(filtered_chunk)
        
    print("\nFinished reading all chunks.")
    
    if not filtered_chunks:
        print("\nNo records found.")
        sys.exit(1)
        
    print("\nCombining filtered chunks...")
    df_filtered = pd.concat(filtered_chunks, ignore_index=True)
    
    if len(df_filtered) > TARGET_ROWS:
        print("\nCreating representative sample...")
        df_filtered = df_filtered.sample(n=TARGET_ROWS, random_state=42).sort_values("Date received").reset_index(drop=True)
        print(f"Sample size : {len(df_filtered):,}")
    else:
        print("\nDataset already within target size.")
        df_filtered = df_filtered.sort_values("Date received").reset_index(drop=True)
        
    # Remove only completely empty rows
    rows_before = len(df_filtered)
    df_filtered.dropna(how="all", inplace=True)
    rows_after = len(df_filtered)
    removed_empty = rows_before - rows_after

    print("\n" + "=" * 80)
    print("DATASET SUMMARY")
    print("=" * 80)
    print(f"Original rows processed : {total_rows:,}")
    print(f"Rows after filtering    : {filtered_rows:,}")
    print(f"Completely empty rows   : {removed_empty:,}")
    
    print("\nDataset Shape")
    print("-" * 80)
    print(f"Rows    : {df_filtered.shape[0]:,}")
    print(f"Columns : {df_filtered.shape[1]}")
    
    print("\nDate Range")
    print("-" * 80)
    min_date = df_filtered["Date received"].min()
    max_date = df_filtered["Date received"].max()
    print(f"From : {min_date.date()}")
    print(f"To   : {max_date.date()}")
    
    memory_mb = df_filtered.memory_usage(deep=True).sum() / 1024 / 1024
    print("\nMemory Usage")
    print("-" * 80)
    print(f"{memory_mb:.2f} MB")
    
    print("\nSaving filtered dataset...")
    df_filtered.to_csv(OUTPUT_FILE, index=False)
    print("Done.")

def main():
    start_time = datetime.now()
    print_header()
    print(f"Started : {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    try:
        process_dataset()
        end_time = datetime.now()
        duration = end_time - start_time
        print("\n" + "=" * 80)
        print("PROCESS COMPLETED SUCCESSFULLY")
        print("=" * 80)
        print(f"Finished : {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Execution Time : {duration}")
    except Exception as error:
        print("\n" + "=" * 80)
        print("UNEXPECTED ERROR")
        print("=" * 80)
        print(error)
        sys.exit(1)

if __name__ == "__main__":
    main()