#!/usr/bin/env python3
import os
import re
from tqdm import tqdm
from typing import List, Set, Optional, Dict

# ==============================================================================
# REGULAR EXPRESSIONS FOR COMMON PASSWORD HASHES
# ==============================================================================
# Definitions for fixed-length hexadecimal hashes (Mode 1)
HEX_HASH_PATTERNS = {
    "MD5_32": r'\b[a-fA-F0-9]{32}\b',       # 32 (MD5, MD4, NTLM)
    "SHA-1_40": r'\b[a-fA-F0-9]{40}\b',     # 40
    "SHA-256_64": r'\b[a-fA-F0-9]{64}\b',   # 64
    "SHA-384_96": r'\b[a-fA-F0-9]{96}\b',   # 96
    "SHA-512_128": r'\b[a-fA-F0-9]{128}\b',  # 128
}

# Definitions for structural hashes (identified by format/prefix) (Mode 2)
STRUCTURAL_HASH_PATTERNS = {
    # vBulletin Patterns
    # vBulletin < 3.8.5 (MD5 + 3-char salt, typically $hash:$salt format)
    # This captures the 32-char hex hash, separator, and 3-char salt
    "vBulletin_less_3.8.5_salt_3": r'[a-fA-F0-9]{32}[:\$][a-zA-Z0-9\.\/]{3}',
    # vBulletin >= 3.8.5 (MD5 + 30-char salt, typically $hash:$salt format)
    "vBulletin_greater_eq_3.8.5_salt_30": r'[a-fA-F0-9]{32}[:\$][a-zA-Z0-9\.\/]{30}',
    
    # Other structural hashes
    "Wordpress_PHPass": r'\$[P|H]\$\w{31}',
    "Bcrypt": r'\$[2][abxy]\$[0-9]{2}\$[a-zA-Z0-9.\/]{53}',
    "SHA-512_Crypt": r'\$6\$[a-zA-Z0-9./]{1,16}\$[a-zA-Z0-9./]{43,86}',
    "SHA-256_Crypt": r'\$5\$[a-zA-Z0-9./]{1,16}\$[a-zA-Z0-9./]{43,86}',
    "MD5_Crypt": r'\$1\$[a-zA-Z0-9./]{1,16}\$[a-zA-Z0-9./]{22}',
    "NTLM_32": r'\b[a-fA-F0-9]{32}\b', 
}
# ==============================================================================
# CORE FUNCTIONS
# ==============================================================================
def get_file_list(root_dir: str, extensions: List[str]) -> List[str]:
    """
    Recursively finds all files under root_dir matching the given extensions.
    """
    matched_files = []
    extensions_lower = [ext.lower() for ext in extensions]
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if any(filename.lower().endswith(f".{ext}") for ext in extensions_lower):
                matched_files.append(os.path.join(dirpath, filename))
    return matched_files

def extract_hashes_from_file_by_pattern(filepath: str, pattern: re.Pattern) -> Set[str]:
    """
    Extracts strings matching a compiled regex pattern from the file.
    """
    hashes = set()
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                # Use findall on the entire line to capture multi-part hashes like $hash:$salt
                found = pattern.findall(line)
                for h in found:
                    hashes.add(h)
    except Exception as e:
        print(f"\n[!] Warning: Could not read file {filepath}: {e}")
    return hashes

# ==============================================================================
# MAIN EXECUTION LOGIC
# ==============================================================================
def main():
    print("=== Advanced Hash Extractor (SHA, Bcrypt, Wordpress, UNIX Crypt) ===")
    
    # --- Input: Folder Path ---
    root_dir = input("Enter folder path to scan: ").strip()
    if not os.path.isdir(root_dir):
        print("[-] Invalid folder path.")
        return

    # --- Input: File Extensions ---
    exts_input = input("Enter file extensions to include (comma-separated, e.g. txt,csv,log): ").strip()
    if not exts_input:
        print("[-] No extensions provided.")
        return
    extensions = [e.strip().lower() for e in exts_input.split(",")]

    # --- Input: Hash Selection Mode ---
    print("\n--- Hash Extraction Mode ---")
    print("1: Extract **Fixed-Length** hex hashes (e.g., MD5, SHA-512) by predefined length.")
    print("2: Extract **Structural** hashes (Wordpress, Bcrypt, UNIX Crypt, vBulletin) by format.")
    
    mode: Optional[int] = None
    while mode not in (1, 2):
        try:
            mode = int(input("Select mode (1 or 2): ").strip())
        except ValueError:
            pass
        if mode not in (1, 2):
            print("[-] Please enter 1 or 2.")
            
    # Dictionary to store results: { 'Pattern_Name': {compiled_pattern, hashes} }
    selected_patterns: Dict[str, Dict] = {}
    if mode == 1:
        # --- Mode 1: Fixed-Length Hex Extraction ---
        print("\nAvailable Fixed-Length Hex Hash Types:")
        pattern_keys = sorted(HEX_HASH_PATTERNS.keys())
        for i, key in enumerate(pattern_keys):
            # Extract length from regex string for display
            # The regex is of the form r'\b[a-fA-F0-9]{LENGTH}\b'
            length = HEX_HASH_PATTERNS[key].split('{')[1].split('}')[0]
            print(f"[{i+1}]: {key} (Length: {length})")
            
        while True:
            selection_input = input("Enter numbers of hashes to extract (comma-separated, e.g. 1,3,5 for 32, 64, 128): ").strip()
            if not selection_input:
                print("[-] No selection made.")
                continue
            
            try:
                selections = [int(s.strip()) for s in selection_input.split(',')]
                selected_names = []
                for index in selections:
                    if 1 <= index <= len(pattern_keys):
                        name = pattern_keys[index - 1]
                        
                        selected_patterns[name] = {
                            'pattern': re.compile(HEX_HASH_PATTERNS[name]),
                            'hashes': set()
                        }
                        selected_names.append(name)
                        
                if not selected_patterns:
                    print("[-] Invalid selection. Please choose numbers from the list.")
                    continue
                
                print(f"[+] Mode 1: Will scan for the following hex formats: {', '.join(selected_names)}")
                break
            except ValueError:
                print("[-] Invalid input. Please use comma-separated numbers.")

    elif mode == 2:
        # --- Mode 2: Structural Hash Extraction ---
        print("\nAvailable Structural Hash Types:")
        pattern_keys = sorted(STRUCTURAL_HASH_PATTERNS.keys())
        for i, key in enumerate(pattern_keys):
            print(f"[{i+1}]: {key}")

        while True:
            selection_input = input("Enter numbers of hashes to extract (comma-separated, e.g. 1,2,3): ").strip()
            if not selection_input:
                print("[-] No selection made.")
                continue
            
            try:
                selections = [int(s.strip()) for s in selection_input.split(',')]
                selected_names = []
                for index in selections:
                    if 1 <= index <= len(pattern_keys):
                        name = pattern_keys[index - 1]
                        
                        selected_patterns[name] = {
                            'pattern': re.compile(STRUCTURAL_HASH_PATTERNS[name]),
                            'hashes': set()
                        }
                        selected_names.append(name)
                        
                if not selected_patterns:
                    print("[-] Invalid selection. Please choose numbers from the list.")
                    continue
                
                print(f"[+] Mode 2: Will scan for the following formats: {', '.join(selected_names)}")
                break
            except ValueError:
                print("[-] Invalid input. Please use comma-separated numbers.")

    print(f"\n[+] Scanning '{root_dir}' recursively for files with extensions: {extensions}")
    files = get_file_list(root_dir, extensions)
    total_files = len(files)
    print(f"[+] Found {total_files} matching files.")
    total_unique_hashes = 0
    
    # Use tqdm progress bar
    with tqdm(total=total_files, unit="file") as pbar:
        for filepath in files:
            for pattern_name, data in selected_patterns.items():
                compiled_pattern = data['pattern']
                file_hashes = extract_hashes_from_file_by_pattern(filepath, compiled_pattern)
                data['hashes'].update(file_hashes)
            
            # Sum the unique hashes for the progress bar
            total_unique_hashes = sum(len(data['hashes']) for data in selected_patterns.values())
            pbar.set_postfix({"Total unique hashes": total_unique_hashes})
            pbar.update(1)

    print("\n[+] Scan complete.")
    print(f"[+] Found a total of {total_unique_hashes} unique hashes across all selected patterns.")

    # ==========================================================================
    # SAVE SECTION - AUTOSAVE TO MULTIPLE FILES
    # ==========================================================================
    
    if total_unique_hashes == 0:
        return
        
    print("\n[+] Starting automatic save process...")
    save_count = 0
    for pattern_name, data in selected_patterns.items():
        hashes = data['hashes']
        if hashes:
            # File name: AlgorithmName_hashes.txt
            output_file = f"{pattern_name}_hashes.txt"
            
            try:
                # Open file in write mode ('w')
                with open(output_file, 'w') as f:
                    # Write the sorted list of unique hashes
                    for h in sorted(hashes):
                        f.write(h + '\n')
                print(f"   - [+] Saved {len(hashes)} unique {pattern_name} hashes to {output_file}")
                save_count += 1
            except Exception as e:
                print(f"   - [-] Failed to save file {output_file}: {e}")
                
    if save_count > 0:
        print(f"\n[+] Successfully saved hashes to {save_count} file(s) in the current directory.")
    else:
        print("\n[!] No hashes were saved (zero found or file error).")

if __name__ == "__main__":
    main()
