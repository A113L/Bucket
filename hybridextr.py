#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This script analyzes cracked passwords to extract and count common Hashcat masks, 
including length-limited edge masks (?x?x...WORD) and full password masks (?u?l?l?d?s...).
"""

import string
import os
import argparse 
from collections import Counter

# --- Constants for all Hashcat Charsets ---
LOWER_CHARS = string.ascii_lowercase
UPPER_CHARS = string.ascii_uppercase
DIGIT_CHARS = string.digits
SPECIAL_CHARS = string.punctuation
# COMBINED_CHARS is useful for filtering non-standard characters
COMBINED_CHARS = LOWER_CHARS + UPPER_CHARS + DIGIT_CHARS + SPECIAL_CHARS

def get_char_type(char):
    """Maps a character to its corresponding Hashcat mask character."""
    if char in DIGIT_CHARS:
        return "?d"
    elif char in SPECIAL_CHARS:
        return "?s"
    elif char in LOWER_CHARS:
        return "?l"
    elif char in UPPER_CHARS:
        return "?u"
    else:
        # Returns None for non-standard characters (e.g., spaces, control chars)
        return None

def read_file_safe(path):
    """Reads a file with encoding error handling."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.readlines()
    except UnicodeDecodeError:
        # Fallback with invalid byte replacement for problematic files
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.readlines()

# --- NEW FEATURE: Full Mask Extraction ---
def extract_full_mask(password):
    """
    Extracts the full Hashcat mask for the entire password.
    Returns the mask string, or None if the password contains non-standard characters.
    Example: "Pass123!" -> "?u?l?l?l?d?d?d?s"
    """
    full_mask = ""
    for ch in password:
        char_type = get_char_type(ch)
        if char_type:
            full_mask += char_type
        else:
            # If any character is non-standard, we discard the whole mask
            return None
    
    return full_mask

# --- Existing Edge Mask Extraction (Enhanced) ---
def extract_edge_masks(password, max_length):
    """
    Extracts masks using all four Hashcat charsets (?l, ?u, ?d, ?s) 
    from the beginning and end of the password.
    Returns a list of unique masks.
    """
    masks = []
    
    # 1. Prefix Extraction
    prefix_mask = ""
    for ch in password:
        # Stop if the mask length limit is reached (2 characters per ?x)
        if len(prefix_mask) // 2 >= max_length: 
            break
        
        char_type = get_char_type(ch)
        if char_type:
            prefix_mask += char_type
        else:
            # The first encountered non-standard character ends the prefix
            break
            
    if prefix_mask:
        masks.append(prefix_mask)
        
    # 2. Suffix Extraction
    suffix_mask = ""
    for ch in reversed(password):
        # Stop if the mask length limit is reached
        if len(suffix_mask) // 2 >= max_length:
            break
                
        char_type = get_char_type(ch)
        if char_type:
            # Prepend the character type for the suffix
            suffix_mask = char_type + suffix_mask
        else:
            # The first encountered non-standard character ends the suffix
            break
            
    # Ensure the suffix is unique
    if suffix_mask and suffix_mask not in masks:
        masks.append(suffix_mask)
        
    return masks

def main():
    # --- Argument Parsing Setup ---
    parser = argparse.ArgumentParser(
        description="Extracts charset edge masks and/or full masks from cracked password files."
    )
    
    parser.add_argument(
        'input_path', 
        type=str, 
        help="Path to the file with cracked passwords (hash:password format)."
    )
    
    # Arguments for EDGE MASKS
    parser.add_argument(
        '-m', '--max-length', 
        type=int, 
        default=8, 
        help="Maximum length of the extracted edge mask (in terms of ?x pairs). Default is 8."
    )
    
    parser.add_argument(
        '-n', '--min-length',
        type=int,
        default=2,
        help="Minimum length of the extracted edge mask (in terms of ?x pairs). Default is 2."
    )
    
    # Argument for FULL MASKS
    parser.add_argument(
        '-f', '--extract-full',
        action='store_true',
        help="Activate extraction of full-password masks (e.g., ?u?l?l?d?s)."
    )

    args = parser.parse_args()
    
    input_path = args.input_path
    max_mask_length = args.max_length
    min_mask_length = args.min_length
    extract_full = args.extract_full
    
    # --- Main Logic ---
    
    base_name = os.path.basename(input_path)
    
    # Adjust output name based on extraction mode
    mode = "full_and_edge" if extract_full else "edge_only"
    output_path = f"{mode}_from_{base_name}_min{min_mask_length}_max{max_mask_length}.hcmask" 
        
    try:
        lines = read_file_safe(input_path)
    except Exception as e:
        print(f"ERROR: Error reading file: {e}")
        return
        
    all_masks = []
    
    mode_info = "full and edge" if extract_full else "edge"
    print(f"Analyzing {len(lines)} lines to extract {mode_info} patterns (min {min_mask_length}, max {max_mask_length} for edges)...") 
        
    for line in lines:
        line = line.strip()
        if not line:
            continue
                    
        # Handle the hash:password format
        password = line.split(":")[-1] if ":" in line else line
                    
        if len(password) < 5:
            continue
            
        # 1. Edge Mask Extraction
        edge_masks = extract_edge_masks(password, max_mask_length)
        
        # Apply minimum length filter
        filtered_edge_masks = [mask for mask in edge_masks if len(mask) // 2 >= min_mask_length]
        all_masks.extend(filtered_edge_masks)
        
        # 2. Full Mask Extraction (If enabled)
        if extract_full:
            full_mask = extract_full_mask(password)
            if full_mask:
                # Full masks are not length-limited, but must be unique
                if full_mask not in all_masks:
                    all_masks.append(full_mask)

            
    # Counting and sorting masks
    counts = Counter(all_masks)
        
    # Sorting: first by count (descending), then alphabetically (ascending)
    sorted_masks = sorted(counts.items(), key=lambda x: (-x[1], x[0]))
        
    # Writing to file
    try:
        with open(output_path, "w", encoding="utf-8") as f_out:
            for mask, count in sorted_masks:
                f_out.write(f"# Count: {count}\n") 
                f_out.write(mask + "\n")
                        
        print(f"\n--- Analysis Complete ---")
        print(f"Found {len(sorted_masks)} unique masks.") 
        print(f"Successfully saved sorted masks to '{output_path}'.")
        print(f"Top 5 most frequent masks:")
        for mask, count in sorted_masks[:5]:
            print(f"  - {mask} ({count} occurrences)")
                
    except Exception as e:
        print(f"ERROR: Error writing output file: {e}")

if __name__ == "__main__":
    main()
