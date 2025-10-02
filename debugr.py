#!/usr/bin/env python3
'''
The script is to use to process debugged hashcat rules in mode = 1
'''
import sys
import os
from collections import Counter
from typing import List, Tuple, Dict

def sort_and_count_occurrences(input_filepath: str):
    """
    Reads data from a file, counts occurrences, sorts them in descending order
    by count, and saves the unique, sorted entries to a new file.
    Allows limiting the number of lines saved.
    """
    if not os.path.exists(input_filepath):
        print(f"Error: Input file '{input_filepath}' does not exist.")
        return
    print("\n" + "="*50)
    print(f"Processing file: {input_filepath}")
    print("="*50)

    # 1. Reading the data
    try:
        with open(input_filepath, 'r', encoding='utf-8') as f:
            # Read lines, removing trailing whitespace (e.g., '\n')
            data = [line.strip() for line in f if line.strip()]
    except IOError as e:
        print(f"File read error: {e}")
        return

    if not data:
        print("The file is empty or only contains blank lines.")
        return

    # 2. Counting and Sorting
    occurrence_counts: Counter = Counter(data)
    # Get sorted data: list of (element, count) tuples, sorted by count (descending)
    sorted_data: List[Tuple[str, int]] = occurrence_counts.most_common()

    # 3. User Input for Limit
    unique_count = len(sorted_data)
    limit: int = 0  # Default 0, meaning no limit (save all)

    print(f"\nThe file contains {unique_count} unique entries.")

    while True:
        # Prompt changed to clarify which file is being processed
        limit_input = input(f"[{os.path.basename(input_filepath)}] Enter the maximum number of unique entries to save (1 to {unique_count}, 0 or Enter = save all): ").strip()

        if not limit_input or limit_input == '0':
            limit = unique_count
            print("[+] Selected to save ALL unique entries.")
            break

        try:
            limit = int(limit_input)
            if 1 <= limit <= unique_count:
                print(f"[+] Selected to save the top {limit} most frequent entries.")
                break
            else:
                print(f"[-] The number must be between 1 and {unique_count}, or 0/Enter.")
        except ValueError:
            print("[-] Invalid format. Please enter an integer.")

    # 4. Applying the limit
    # If the limit is less than the total number of unique entries,
    # we take only the most frequent ones (from the start of the most_common() list)
    if limit < unique_count:
        final_data_to_write = sorted_data[:limit]
        final_write_count = limit
    else:
        final_data_to_write = sorted_data
        final_write_count = unique_count

    # 5. Generating the output file name
    basename, ext = os.path.splitext(input_filepath)

    # New file name: basename_MT_numberOfWritten.rule
    output_filepath = f"{basename}_MT_{final_write_count}.rule"

    # 6. Saving the data to the new file (ONLY the entries, no counts)
    try:
        with open(output_filepath, 'w', encoding='utf-8') as f:
            print(f"\nSaving unique sorted data to: {output_filepath}")

            # Save only the item, ignoring the count
            for item, count in final_data_to_write:
                f.write(f"{item}\n")

            print(f"Successfully saved {final_write_count} unique entries to file: {output_filepath}")
    except IOError as e:
        print(f"File write error: {e}")

if __name__ == "__main__":
    # sys.argv[0] is the script name itself, so we check if there are at least 2 arguments
    if len(sys.argv) < 2:
        print("Usage: python3 debugr.py <input_file_path_1> [input_file_path_2 ...]")
        # Exit with a non-zero status code to indicate an error
        sys.exit(1)
    else:
        # sys.argv[1:] contains all command-line arguments EXCEPT the script name
        input_files = sys.argv[1:]
        print(f"Found {len(input_files)} file(s) to process.")
        
        # Iterate over all provided file paths
        for input_file in input_files:
            sort_and_count_occurrences(input_file)
        
        print("\nAll files processed.")
