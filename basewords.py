#!/usr/bin/env python3

import re
import os
import multiprocessing as mp
from tqdm import tqdm
from collections import Counter

# MULTIPROCESSING CONSTANTS
# Use 75% of available CPU cores
NUM_PROCESSES = max(1, int(mp.cpu_count() * 0.75))
CHUNKSIZE = 10000  # Number of lines to pass to a single process

def clean_and_filter_word(word):
    """
    1. Removes all non-alphabetic characters (cleans 'word123!' to 'word').
    2. Converts to lowercase.
    3. Checks length (must be 5-30 characters long AFTER cleaning).
    4. Checks for unique characters.

    Returns the cleaned word or None if it fails any filter.
    """
    # Step 1: Remove non-alphabetic characters (removes digits, symbols, etc.)
    # Example: 'slowo123!' -> 'slowo'
    clean_word = re.sub(r'[^a-zA-Z]', '', word)
    
    # Convert to lowercase
    clean_word = clean_word.lower()

    # Step 2: Check length (5 to 30)
    if not (5 <= len(clean_word) <= 30):
        return None

    # Step 3: Check for unique characters (e.g., rejects 'apple' because of 'p')
    if len(set(clean_word)) == len(clean_word):
        return clean_word
    
    return None

def process_chunk(lines_chunk):
    """
    Processes a batch of lines and returns a Counter (dictionary) 
    with word counts for that chunk.
    """
    
    # Loose regex to capture initial tokens that contain 5-30 characters 
    # (letters, digits, or symbols) to ensure we don't miss complex strings like 'word123!'
    loose_words = re.compile(r'[a-zA-Z0-9!@#$%^&*()_\-+=]{5,30}')
    
    # Use Counter to store word counts for this process
    word_counts = Counter() 
    
    for line in lines_chunk:
        words = loose_words.findall(line)
        
        for word in words:
            # Cleaning and final verification
            result = clean_and_filter_word(word)
            
            # If the cleaned word passes the filters, count its occurrence
            if result:
                word_counts[result] += 1
                
    return word_counts # Return the Counter object (word:count dictionary)

# --- I/O Helper Functions ---

def read_file_chunked(filepath):
    """Reads the file and yields it in line chunks, handling encoding fallbacks."""
    
    chunk = []
    for encoding in ['utf-8', 'latin-1', 'windows-1252']:
        try:
            with open(filepath, 'r', encoding=encoding, errors='ignore') as f:
                for line in f:
                    chunk.append(line)
                    if len(chunk) >= CHUNKSIZE:
                        yield chunk
                        chunk = []
                if chunk: # Last, smaller chunk
                    yield chunk
            return
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("Failed to decode file using utf-8, latin-1 or windows-1252")

def count_lines(filepath):
    """Efficiently counts lines for the progress bar."""
    lines = 0
    try:
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(1024*1024), b''):
                lines += chunk.count(b'\n')
    except Exception as e:
        print(f"[Warning] Could not count lines precisely: {e}. Progress bar might be inaccurate.")
        return 0
    return lines

# --- Main Function ---

def main():
    input_file = input("Enter input file path: ").strip()
    output_file = input("Enter output file path: ").strip()

    if not os.path.isfile(input_file):
        print(f"[Error] File not found: {input_file}")
        return

    print(f"[Info] Using {NUM_PROCESSES} CPU cores for processing.")
    
    total_lines = count_lines(input_file)
    print(f"[Info] File has approximately {total_lines} lines. Chunk size: {CHUNKSIZE}.")

    # Initialize the main counter
    final_word_counts = Counter() 
    
    pool = mp.Pool(processes=NUM_PROCESSES)

    print("[Processing] Extracting and counting words using multiprocessing...")

    chunks_count = total_lines // CHUNKSIZE + 1
    
    results_iterator = pool.imap_unordered(process_chunk, read_file_chunked(input_file))

    try:
        for local_counts in tqdm(results_iterator, total=chunks_count, unit="chunks"):
            # KEY STEP: Aggregate (sum) the results from each process
            final_word_counts.update(local_counts)
    except Exception as e:
        print(f"\n[Error] Processing file chunk: {e}")
        pool.close()
        pool.join()
        return
    
    pool.close()
    pool.join()

    # KEY STEP: Sort by count (frequency) in descending order
    # item[1] is the count, reverse=True ensures descending order
    sorted_words_by_count = sorted(
        final_word_counts.items(), 
        key=lambda item: item[1], 
        reverse=True
    )

    print(f"\n[Info] Total unique words found: {len(sorted_words_by_count)}")

    print(f"[Info] Writing {len(sorted_words_by_count)} words to output file (sorted by frequency)...")

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            # Write ONLY the word, ignoring the count, but keeping the frequency sort
            for word, count in sorted_words_by_count:
                f.write(f"{word}\n")
        print(f"[Done] Saved {len(sorted_words_by_count)} words to '{output_file}'")
    except Exception as e:
        print(f"[Error] Writing output file: {e}")

if __name__ == "__main__":
    main()
