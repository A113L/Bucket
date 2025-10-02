#!/usr/bin/env python3

import sys
import os

# QWERTY to Russian Dvorak keymap (simplified example)
qwerty_to_dvorak_russian = {
    'q': 'Ð¹', 'w': 'Ñ†', 'e': 'Ñƒ', 'r': 'Ðº', 't': 'Ðµ', 'y': 'Ð½', 'u': 'Ð³', 'i': 'Ñˆ', 'o': 'Ñ‰', 'p': 'Ð·',
    'a': 'Ñ„', 's': 'Ñ‹', 'd': 'Ð²', 'f': 'Ð°', 'g': 'Ð¿', 'h': 'Ñ€', 'j': 'Ð¾', 'k': 'Ð»', 'l': 'Ð´',
    'z': 'Ñ', 'x': 'Ñ‡', 'c': 'Ñ', 'v': 'Ð¼', 'b': 'Ð¸', 'n': 'Ñ‚', 'm': 'ÑŒ',
    'Q': 'Ð™', 'W': 'Ð¦', 'E': 'Ð£', 'R': 'Ðš', 'T': 'Ð•', 'Y': 'Ð', 'U': 'Ð“', 'I': 'Ð¨', 'O': 'Ð©', 'P': 'Ð—',
    'A': 'Ð¤', 'S': 'Ð«', 'D': 'Ð’', 'F': 'Ð', 'G': 'ÐŸ', 'H': 'Ð ', 'J': 'Ðž', 'K': 'Ð›', 'L': 'Ð”',
    'Z': 'Ð¯', 'X': 'Ð§', 'C': 'Ð¡', 'V': 'Ðœ', 'B': 'Ð˜', 'N': 'Ð¢', 'M': 'Ð¬'
}

def translate_to_dvorak(line):
    return ''.join(qwerty_to_dvorak_russian.get(char, char) for char in line)

def convert_file(input_path, output_path, encoding='utf-8', errors='ignore'):
    # Use buffered reading for large file support
    total_bytes = os.path.getsize(input_path)
    bytes_read = 0
    buffer_size = 1024 * 1024  # 1MB chunks

    with open(input_path, 'rb') as infile, open(output_path, 'w', encoding='utf-8') as outfile:
        while chunk := infile.read(buffer_size):
            try:
                decoded = chunk.decode(encoding, errors=errors)
            except Exception as e:
                print(f"Decoding error: {e}")
                continue

            # Translate and write
            lines = decoded.splitlines(keepends=True)
            for line in lines:
                translated = translate_to_dvorak(line)
                outfile.write(translated)

            bytes_read += len(chunk)
            percent = bytes_read / total_bytes * 100
            print(f"Progress: {percent:.2f}%", end='\r', flush=True)

    print("\nConversion complete.")

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 qwerty2dvorak.py <input_file> <output_file>")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    if not os.path.exists(input_path):
        print(f"Error: File '{input_path}' does not exist.")
        sys.exit(1)

    print(f"Converting '{input_path}' to Dvorak layout...")
    convert_file(input_path, output_path)

if __name__ == "__main__":
    main()
