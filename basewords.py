import re
from collections import Counter
import os
import sys
from multiprocessing import Pool, Manager

# --- Configuration ---
# Number of CPU cores to use for parallel processing.
NUM_PROCESSES = os.cpu_count() or 4 
# Minimum acceptable length for a base word. Set to 2 to exclude single letters.
MIN_WORD_LENGTH = 2 

def process_chunk_for_words(chunk):
    """
    Processes a list of lines (a chunk) and returns a Counter 
    of the base words found in that chunk. Includes a minimum word length filter.
    """
    local_counter = Counter()
    word_pattern = re.compile(r'[^\W\d_]+')
    
    for line in chunk:
        line = line.lower()
        base_words = word_pattern.findall(line)
        
        # Filtering Step: Only include words that meet the minimum length requirement
        filtered_words = [word for word in base_words if len(word) >= MIN_WORD_LENGTH]
        
        local_counter.update(filtered_words)
        
    return local_counter

def file_to_chunks(file_path):
    """
    Reads a file line by line and divides its content into chunks 
    for parallel processing. Handles large files by streaming.
    """
    try:
        total_size = os.path.getsize(file_path)
    except OSError:
        print(f"Error: Could not determine size of file '{file_path}'.", file=sys.stderr)
        return []
        
    chunk_size_bytes = max(10 * 1024 * 1024, total_size // NUM_PROCESSES)
    
    chunks = []
    current_chunk = []
    current_chunk_size = 0

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                current_chunk.append(line)
                current_chunk_size += len(line.encode('utf-8'))
                
                if current_chunk_size >= chunk_size_bytes and len(current_chunk) > 0:
                    chunks.append(current_chunk)
                    current_chunk = []
                    current_chunk_size = 0
            
            if current_chunk:
                chunks.append(current_chunk)
                
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred during file reading: {e}", file=sys.stderr)
        sys.exit(1)
        
    return chunks

def process_file_and_sort(file_path):
    """
    Coordinates the parallel processing of the file, merges results, and sorts them.
    """
    chunks = file_to_chunks(file_path)
    
    if not chunks:
        return []
        
    print(f"Using {NUM_PROCESSES} CPU cores to process {len(chunks)} chunks...")
    
    all_counters = []
    
    with Pool(NUM_PROCESSES) as pool:
        all_counters = pool.map(process_chunk_for_words, chunks)

    final_counter = Counter()
    for counter in all_counters:
        final_counter.update(counter)
        
    if not final_counter:
        return []

    # Sorting: By count (descending), then by word (ascending)
    sorted_words_with_count = sorted(
        final_counter.items(), 
        key=lambda item: (item[1], item[0]), 
        reverse=True
    )

    # Remove the count and return the final list of words
    result_words = [word for word, _ in sorted_words_with_count]
    
    return result_words

def save_results_to_file(data_list, output_path):
    """
    Saves the list of words to a specified file path, one word per line.
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            for word in data_list:
                f.write(word + '\n')
        print(f"\nSuccessfully saved {len(data_list)} unique words to: {output_path}")
    except Exception as e:
        print(f"\nError: Could not save results to file '{output_path}'. Reason: {e}", file=sys.stderr)

def interactive_mode():
    """
    Main function to run the script in interactive mode.
    """
    print("--- Base Word Extractor (Multiprocessing & Save Option) ---")
    print(f"Note: Using {NUM_PROCESSES} CPU cores for fast processing.")
    print(f"Filter: Excluding words shorter than {MIN_WORD_LENGTH} characters.")
    
    while True:
        input_file_path = input("\nEnter the full path to the INPUT text file (or 'q' to quit): ").strip()
        
        if input_file_path.lower() == 'q':
            print("Exiting program.")
            break
            
        if not os.path.exists(input_file_path):
            print(f"The path '{input_file_path}' is invalid. Please try again.")
            continue
            
        output_file_path = input("Enter the full path for the OUTPUT file (e.g., 'output.txt', or leave blank to skip saving): ").strip()
        
        print(f"\nStarting processing of file: {input_file_path}...")
        
        # Execute the main logic
        result = process_file_and_sort(input_file_path)
        
        if not result:
            print("The file contains no base words to process.")
            continue

        print("\n" + "-"*50)
        
        # Display results
        print("\nTop 20 Base Words (by frequency):")
        for i, word in enumerate(result[:20]): 
            print(f"{i+1}. {word}")
        
        if len(result) > 20:
            print(f"... and {len(result) - 20} more unique words.")

        # Save results if output path was provided
        if output_file_path:
            save_results_to_file(result, output_file_path)
            
        print("\n" + "-"*50)

if __name__ == "__main__":
    if sys.platform.startswith('win') or sys.platform == 'darwin':
        try:
            from multiprocessing import freeze_support
            freeze_support()
        except ImportError:
            pass
            
    interactive_mode()
