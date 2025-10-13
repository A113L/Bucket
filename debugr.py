#!/usr/bin/env python3
'''
The script is used to process debugged hashcat rules in mode = 1.
It reads one or more input files, combines the rules, counts and sorts unique entries
across all files, displays redundancy statistics, prompts the user for a limit, 
and saves the top 'N' most frequent entries to a single new consolidated file.
'''
import sys
import os
from collections import Counter
from typing import List, Tuple, Dict

def read_file_data(input_filepath: str) -> List[str]:
    """
    Reads data from a single file, handles errors, and returns a list of stripped lines.
    Uses 'latin-1' encoding to avoid UnicodeDecodeError.
    """
    if not os.path.exists(input_filepath):
        print(f"Error: Input file '{input_filepath}' does not exist.")
        return []
    
    print(f"[+] Reading file: {input_filepath}")
    
    try:
        # Using 'latin-1' to handle non-UTF-8 bytes
        with open(input_filepath, 'r', encoding='latin-1') as f:
            # Read lines, removing trailing whitespace (e.g., '\n')
            data = [line.strip() for line in f if line.strip()]
            return data
    except IOError as e:
        print(f"[-] File read error for {input_filepath}: {e}")
        return []

def process_multiple_files(input_files: List[str]):
    """
    Reads and combines data from all input files, counts occurrences, sorts them,
    calculates and displays redundancy statistics, and handles user input 
    for the final limit before writing the output.
    """
    all_data: List[str] = []
    
    # 1. Reading and Combining Data from all files
    print("\n" + "="*60)
    print("STARTING MULTI-FILE PROCESSING")
    print("="*60)
    
    for input_file in input_files:
        file_data = read_file_data(input_file)
        if file_data:
            all_data.extend(file_data)

    if not all_data:
        print("\nNo valid data found across all files. Exiting.")
        return

    # Store total lines before processing
    total_lines = len(all_data)
    print(f"\n[+] Total lines read across all files: {total_lines:,}")

    # 2. Counting and Sorting (Consolidated)
    occurrence_counts: Counter = Counter(all_data)
    # Get sorted data: list of (element, count) tuples, sorted by count (descending)
    sorted_data: List[Tuple[str, int]] = occurrence_counts.most_common()

    # 3. Calculate and Display Redundancy Statistics
    unique_count = len(sorted_data)
    
    # Calculate the percentage
    if total_lines > 0:
        # Percentage of unique lines out of the total lines
        unique_percentage = (unique_count / total_lines) * 100
    else:
        unique_percentage = 0.0

    print(f"The consolidated dataset contains {unique_count:,} unique entries.")
    print(f"[STAT] Unique entries are {unique_percentage:.2f}% of the total lines read.")
    # Calculate the redundant lines and the percentage
    redundant_lines = total_lines - unique_count
    if total_lines > 0:
        redundant_percentage = (redundant_lines / total_lines) * 100
    else:
        redundant_percentage = 0.0
    print(f"[STAT] Redundant lines (duplicates) removed: {redundant_lines:,} ({redundant_percentage:.2f}%)")
    
    # 4. User Input for Limit
    limit: int = 0  # Default 0, meaning no limit (save all)

    while True:
        limit_input = input(f"[CONSOLIDATED] Enter the maximum number of unique entries to save (1 to {unique_count}, 0 or Enter = save all): ").strip()

        if not limit_input or limit_input == '0':
            limit = unique_count
            print("[+] Selected to save ALL unique entries.")
            break

        try:
            limit = int(limit_input)
            if 1 <= limit <= unique_count:
                print(f"[+] Selected to save the top {limit:,} most frequent entries.")
                break
            else:
                print(f"[-] The number must be between 1 and {unique_count}, or 0/Enter.")
        except ValueError:
            print("[-] Invalid format. Please enter an integer.")

    # 5. Applying the limit
    if limit < unique_count:
        final_data_to_write = sorted_data[:limit]
        final_write_count = limit
    else:
        final_data_to_write = sorted_data
        final_write_count = unique_count
    
    # 6. Generating the output file name
    # We use the first input file's directory and create a generic name.
    first_basename = os.path.basename(os.path.splitext(input_files[0])[0])
    output_filepath = f"{first_basename}_CONSOLIDATED_MT_{final_write_count}.rule"
    
    # Attempt to put the output file in the same directory as the first input file
    input_dir = os.path.dirname(input_files[0])
    if input_dir:
        output_filepath = os.path.join(input_dir, output_filepath)

    # 7. Saving the data to the new file (ONLY the entries, no counts)
    try:
        with open(output_filepath, 'w', encoding='utf-8') as f:
            print(f"\nSaving unique consolidated sorted data to: {output_filepath}")

            # Save only the item, ignoring the count
            for item, count in final_data_to_write:
                f.write(f"{item}\n")

            print(f"Successfully saved {final_write_count:,} unique consolidated entries.")
            print("\n" + "="*60)
            print("PROCESSING COMPLETE")
            print("="*60)
            
    except IOError as e:
        print(f"File write error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 debugr.py <input_file_path_1> [input_file_path_2 ...]")
        sys.exit(1)
    else:
        input_files = sys.argv[1:]
        print(f"Found {len(input_files)} file(s) to process.")
        
        process_multiple_files(input_files)
