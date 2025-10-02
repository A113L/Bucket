#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import string
import os
import argparse  # Import the argparse library
from collections import Counter

# --- Constants ---
SPECIAL_CHARS = string.punctuation
NUM_SPEC_CHARS = string.digits + SPECIAL_CHARS
# MAX_MASK_LENGTH will now be set by CLI argument in main()

def read_file_safe(path):
    """Reads a file with encoding error handling."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.readlines()
    except UnicodeDecodeError:
        # Fallback with invalid byte replacement
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.readlines()

# The function now accepts max_length as an argument
def extract_edge_masks(password, max_length):
    """
    Extracts masks for strings composed of ?d (digits) and ?s (special chars)
    from the beginning and end of the password.
    Returns a list of unique masks, e.g.: ['?d?d?d', '?s?s']
    Limit: Extraction stops after a mask reaches max_length characters in length.
    """
    masks = []
        
    # 1. Prefix Extraction
    prefix_mask = ""
    for ch in password:
        # Check against the new max_length argument
        if len(prefix_mask) >= max_length: 
            break
                
        if ch in string.digits:
            prefix_mask += "?d"
        elif ch in SPECIAL_CHARS:
            prefix_mask += "?s"
        else:
            # The first encountered non-numeric/non-special character ends the prefix
            break
                
    if prefix_mask:
        masks.append(prefix_mask)
            
    # 2. Suffix Extraction
    suffix_mask = ""
    for ch in reversed(password):
        # Check against the new max_length argument
        if len(suffix_mask) >= max_length:
            break
                    
        if ch in string.digits:
            suffix_mask = "?d" + suffix_mask
        elif ch in SPECIAL_CHARS:
            suffix_mask = "?s" + suffix_mask
        else:
            # The first encountered non-numeric/non-special character ends the suffix
            break
                    
    # Ensure the suffix is different from the prefix
    # e.g., password "123" has both prefix and suffix "?d?d?d", only add it once
    if suffix_mask and suffix_mask not in masks:
        masks.append(suffix_mask)
            
    return masks

def main():
    # --- Argument Parsing Setup ---
    parser = argparse.ArgumentParser(
        description="Extracts num-spec edge masks from cracked password files."
    )
    
    # Optional flag for max mask length with a default value of 16
    parser.add_argument(
        '-m', '--max-length', 
        type=int, 
        default=16, 
        help="Maximum length of the extracted edge mask (in terms of ?d/?s pairs). Default is 16."
    )
    
    # Positional argument for the input file path
    parser.add_argument(
        'input_path', 
        type=str, 
        help="Path to the file with cracked passwords (hash:password format)."
    )

    args = parser.parse_args()
    
    input_path = args.input_path
    max_mask_length = args.max_length # Get max length from the argument
    
    # --- Rest of the main logic ---
    
    # Automatic generation of the output path
    base_name = os.path.basename(input_path)
    output_path = f"num_spec_edges_from_{base_name}_max{max_mask_length}.hcmask" 
        
    try:
        lines = read_file_safe(input_path)
    except Exception as e:
        print(f"ERROR: Error reading file: {e}")
        return
        
    all_edge_masks = []
    print(f"Analyzing {len(lines)} lines to extract numerical/special edge patterns (max length {max_mask_length})...") 
        
    for line in lines:
        line = line.strip()
        if not line:
            continue
                    
        # Handle the hash:password format (assume the password is after the last colon)
        if ":" in line:
            password = line.split(":")[-1]
        else:
            password = line # Use the whole line if there is no colon
                    
        # Discard passwords that are too short or consist only of num-spec chars
        if len(password) < 5 or all(ch in NUM_SPEC_CHARS for ch in password):
            continue
                    
        # Extraction of num-spec prefixes and suffixes, passing the max length
        masks = extract_edge_masks(password, max_mask_length)
        all_edge_masks.extend(masks)
            
    # Counting and sorting masks
    counts = Counter(all_edge_masks)
        
    # Sorting: first by count (descending), then alphabetically (ascending)
    sorted_masks = sorted(counts.items(), key=lambda x: (-x[1], x[0]))
        
    # Writing to file
    try:
        with open(output_path, "w", encoding="utf-8") as f_out:
            for mask, count in sorted_masks:
                # Optional: a comment with the count can be added
                # f_out.write(f"#{count}\n") 
                f_out.write(mask + "\n")
                        
        print(f"\n--- Analysis Complete ---")
        print(f"Found {len(sorted_masks)} unique Num-Spec edge masks (max length {max_mask_length}).") 
        print(f"Successfully saved sorted masks to '{output_path}'.")
        print(f"Top 5 most frequent masks:")
        for mask, count in sorted_masks[:5]:
            print(f"  - {mask} ({count} occurrences)")
                
    except Exception as e:
        print(f"ERROR: Error writing output file: {e}")

if __name__ == "__main__":
    main()
