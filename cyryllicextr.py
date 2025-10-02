#!/usr/bin/env python3

"""
Cyrillic Word Extractor with Mojibake Fix

This script processes one or more text files to extract words containing Cyrillic characters,
while addressing common mojibake issues caused by incorrect text encoding (e.g., UTF-8 bytes
misinterpreted as Windows-1252). It is designed to handle large files efficiently with low RAM usage.

Key Features:
- Reads multiple .txt files specified by the user.
- Attempts to fix mojibake in lines by re-encoding text from Windows-1252 to UTF-8.
- Extracts words containing at least one Cyrillic character (including words with digits and special chars).
- Collects extracted words from all input files, removes duplicates, sorts them alphabetically.
- Saves the unique sorted list of words to a user-specified output file.

Usage:
    - Run the script.
    - Input one or more valid .txt file paths (one per line).
    - Provide the output file path to save results.

Example:
    $ python3 cyrillicextr.py
    File path: input1.txt
    File path: input2.txt
    File path: 
    Enter path for output file (e.g., result.txt): output.txt

Output:
    - A file containing unique Cyrillic words extracted from the input files, one per line.

Note:
    The script handles mojibake commonly arising from UTF-8 encoded text being incorrectly decoded as Windows-1252,
    improving extraction accuracy for Cyrillic text.
"""
import os
import re
import tempfile
from pathlib import Path

def fix_mojibake(text):
    """
    Attempts to fix mojibake caused by decoding UTF-8 bytes as Windows-1252.
    If decoding fails, returns the original text.
    """
    try:
        return text.encode('windows-1252').decode('utf-8')
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text

def extract_cyrillic_words(line):
    """
    Extract words containing at least one Cyrillic character.
    Allows digits and special characters in the word.
    """
    return re.findall(r'\b[\w@#%&*+!.\-]*[Ð°-ÑÐ-Ð¯Ñ‘Ð]+[\w@#%&*+!.\-]*\b', line)

def process_files(file_paths, output_file):
    temp_file = tempfile.NamedTemporaryFile(delete=False, mode='w+', encoding='utf-8')
    total_written = 0

    for file_path in file_paths:
        print(f"ðŸ“„ Processing: {file_path}")
        try:
            # Read as binary to fix mojibake reliably
            with open(file_path, 'rb') as f:
                for raw_line in f:
                    # Try decode UTF-8 first
                    try:
                        line = raw_line.decode('utf-8')
                    except UnicodeDecodeError:
                        # fallback: decode as Windows-1252 and fix mojibake
                        try:
                            line = fix_mojibake(raw_line.decode('windows-1252', errors='replace'))
                        except Exception:
                            # if all fails, skip line
                            continue

                    words = extract_cyrillic_words(line)
                    for w in words:
                        temp_file.write(w + '\n')
                        total_written += 1

        except Exception as e:
            print(f"âŒ Error reading {file_path}: {e}")

    temp_file.flush()
    temp_file.seek(0)

    print(f"\nðŸ§  Extracted approx. {total_written:,} words. Removing duplicates and sorting...")

    unique_words = sorted(set(temp_file.read().splitlines()))

    print(f"ðŸ’¾ Writing {len(unique_words):,} unique words to: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as out_f:
        for word in unique_words:
            out_f.write(word + '\n')

    temp_file.close()
    os.remove(temp_file.name)
    print("âœ… Done!")

def main():
    print("ðŸ”  Cyrillic Word Extractor with Mojibake Fix (Multi-file, Low RAM)")
    
    print("\nðŸ“‚ Enter paths to .txt files to process (one per line).")
    print("ðŸ›‘ Leave an empty line to finish.\n")

    file_paths = []
    while True:
        path = input("File path: ").strip()
        if not path:
            break
        if not os.path.isfile(path):
            print("âŒ Not a valid file path.")
        elif not path.lower().endswith('.txt'):
            print("âš ï¸ Only .txt files are allowed.")
        else:
            file_paths.append(path)

    if not file_paths:
        print("âŒ No valid files provided. Exiting.")
        return

    output_file = input("\nðŸ’¾ Enter path for output file (e.g., result.txt): ").strip()
    if not output_file:
        print("âŒ Output file path is required.")
        return

    process_files(file_paths, output_file)

if __name__ == '__main__':
    main()
