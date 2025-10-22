#!/usr/bin/env python3

import base64
import os
import sys

def base64_decode_safe(line):
    """
    Attempts to decode Base64, automatically handling standard and URL-safe variants.
    """
    cleaned_line = line.strip()

    # 1. Try standard Base64
    try:
        return base64.b64decode(cleaned_line, validate=True)
    except Exception:
        pass

    # 2. Try Base64 URL-safe (handles '-' and '_')
    try:
        # base64.urlsafe_b64decode requires padding ('=')
        padding_needed = 4 - (len(cleaned_line) % 4)
        if padding_needed != 4:
            cleaned_line += '=' * padding_needed
        return base64.urlsafe_b64decode(cleaned_line)
    except Exception:
        pass

    return None

def format_output(decoded_bytes, format_choice, split_length=0):
    """
    Formats the decoded bytes according to the user's choice.
    """
    length = len(decoded_bytes)

    if format_choice == '1': # Raw / Text
        # Try to return as text, otherwise return Hex
        try:
            return decoded_bytes.decode('utf-8', errors='ignore')
        except Exception:
            return decoded_bytes.hex()
    
    elif format_choice == '2': # Hexadecimal
        return decoded_bytes.hex()
    
    elif format_choice == '3': # Hex with Custom Split
        hex_str = decoded_bytes.hex()
        
        # Default split logic for common hash lengths if user enters 0
        if split_length == 0:
            if length == 32: # 32 bytes = 64 hex chars (e.g., SHA-256)
                split_length = 32
            elif length % 16 == 0 and length > 0: # Split every 16 bytes (32 hex chars)
                split_length = 32
            else:
                return hex_str # If custom length, do not split
        
        # Split length in Hex characters
        split_hex_len = split_length * 2
        
        parts = []
        for i in range(0, len(hex_str), split_hex_len):
            parts.append(hex_str[i:i + split_hex_len])
        
        return ':'.join(parts)

    return f"Raw Bytes ({length}B): {decoded_bytes.hex()}"


def process_lines(lines, format_choice, split_length):
    """
    Processes a list of lines and returns a list of formatted results.
    """
    results = []
    
    for idx, line in enumerate(lines, 1):
        if not line.strip():
            continue
            
        decoded_bytes = base64_decode_safe(line)
        
        if decoded_bytes is not None:
            # Skip if 0 bytes decoded
            if len(decoded_bytes) == 0:
                 print(f"[{idx}] Warning: Empty line or 0 bytes decoded.")
                 continue

            formatted_result = format_output(decoded_bytes, format_choice, split_length)
            print(f"[{idx}] Success: {len(decoded_bytes)}B -> {formatted_result}")
            results.append(formatted_result)
        else:
            print(f"[{idx}] Error: Failed to decode Base64.")
            
    return results

def main():
    """
    Main program function handling user interface.
    """
    print("--- Universal Base64 Decoder ---")
    
    # Short description of the script
    print("This Python script is a **Universal Base64 Decoder**. It can process data from either a text file or direct console input. It automatically handles both standard and URL-safe Base64 variants and allows the user to specify the output format, including raw text/bytes, a continuous hexadecimal string, or a hexadecimal string split by byte length (e.g., for hash/salt analysis).")
    
    # --- Input Mode Selection ---
    mode = input("\nSelect input mode (1: File, 2: Text Input): ").strip()
    
    if mode == '1':
        file_path = input("Enter path to Base64 file (one entry per line): ").strip()
        if not os.path.isfile(file_path):
            print("Error: File does not exist. Exiting.")
            return
        
        with open(file_path, 'r') as f:
            lines = f.read().splitlines()
        print(f"Read {len(lines)} lines from file.")
        
    elif mode == '2':
        print("\nEnter Base64 data. End with an empty line and press Enter twice.")
        lines = []
        while True:
            line = sys.stdin.readline().strip()
            if not line:
                break
            lines.append(line)
        print(f"Read {len(lines)} entries.")
        
    else:
        print("Error: Invalid mode selection. Exiting.")
        return
        
    if not lines:
        print("Warning: No data to process.")
        return

    # --- Output Format Selection ---
    print("\n--- Output Format Selection ---")
    print("1: Raw Data (Text attempt)")
    print("2: Hexadecimal String (No split)")
    print("3: Hex with Custom Split (e.g., 32:32 for SHA-256)")
    format_choice = input("Select format (1/2/3): ").strip()
    
    split_length = 0
    if format_choice == '3':
        try:
            split_length_input = input("Enter segment length in bytes (e.g., 16, 32). Enter 0 for default split: ").strip()
            split_length = int(split_length_input)
        except ValueError:
            print("Warning: Invalid value, using default split.")
            split_length = 0
            
    print("\n--- Decoding Results ---")
    results = process_lines(lines, format_choice, split_length)

    # --- Save to File ---
    if not results:
        print("\nWarning: No valid data decoded.")
        return

    save = input("\nSave results to file? (y/n): ").strip().lower()
    if save == 'y':
        output_path = input("Enter output file path: ").strip()
        try:
            with open(output_path, 'w') as out:
                out.write('\n'.join(results) + '\n')
            print(f"Success: Output saved to {output_path}")
        except Exception as e:
            print(f"Error saving file: {e}")
    else:
        print("\nFinished.")

if __name__ == "__main__":
    main()
