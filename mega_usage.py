#!/usr/bin/env python3

import sys
from mega import Mega
from mega.errors import RequestError

# Define the User-Agent string for a modern Windows Chrome browser
# (User-Agent strings are subject to change over time)
WINDOWS_CHROME_USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/129.0.0.0 Safari/537.36'
)


# Function to format bytes into a readable format (MB, GB, TB)
def format_bytes(bytes_size):
    """Converts bytes to the most appropriate unit (MB, GB, TB)."""
    if bytes_size is None:
        return "N/A"
    
    # Conversion factors
    TB = 1024**4
    GB = 1024**3
    MB = 1024**2

    if bytes_size >= TB:
        return f"{bytes_size / TB:.2f} TB"
    elif bytes_size >= GB:
        return f"{bytes_size / GB:.2f} GB"
    elif bytes_size >= MB:
        return f"{bytes_size / MB:.2f} MB"
    else:
        return f"{bytes_size} Bytes"

def check_mega_usage(accounts_file="accounts.txt"):
    """
    Reads accounts from a file, logs in, and displays storage usage.
    """
    print("--- ☁️ MEGA.nz Account Usage Checker ☁️ ---")
    
    # 1. Load accounts
    try:
        with open(accounts_file, 'r', encoding='utf-8') as f:
            account_lines = [line.strip() for line in f if line.strip() and ':' in line]
    except FileNotFoundError:
        print(f"\n❌ Error: File '{accounts_file}' not found.", file=sys.stderr)
        print("Make sure the file exists and is named correctly.")
        return

    if not account_lines:
        print("\n⚠️ No accounts to process in the file. Check the format: email:password")
        return

    print(f"\nFound {len(account_lines)} accounts. Starting check...")
    print(f"Using User-Agent: {WINDOWS_CHROME_USER_AGENT.split(') ')[-1].split(' ')[0]}...")
    print("-" * 50)
    
    # 2. Process accounts
    for line in account_lines:
        try:
            email, password = line.split(':', 1)
        except ValueError:
            print(f"Format error for line: {line}. Expected 'email:password'. Skipping.")
            continue
            
        print(f"[{email}] Logging in...")
        
        # --- MODIFICATION HERE: Pass the User-Agent ---
        # The Mega constructor accepts a dictionary of options, including 'User-Agent'
        mega_options = {'User-Agent': WINDOWS_CHROME_USER_AGENT}
        mega = Mega(options=mega_options)
        # ---------------------------------------------
        
        m = None # Mega client object

        try:
            # Attempt to log in
            m = mega.login(email, password)
            
            # Retrieve storage data
            space_data = m.get_storage_space()
            
            used = space_data['used']
            total = space_data['total']
            free = total - used
            
            # Format data
            used_fmt = format_bytes(used)
            total_fmt = format_bytes(total)
            free_fmt = format_bytes(free)

            # Calculate percentage usage
            if total > 0:
                percentage = (used / total) * 100
            else:
                percentage = 0

            print(f"  ✅ Successfully logged in.")
            print(f"  ➡️ Used: **{used_fmt}** / {total_fmt} ({percentage:.2f}%)")
            print(f"  ➡️ Free: {free_fmt}")
        
        except RequestError as e:
            # Handle API errors (e.g., invalid password, network error)
            error_message = str(e).strip()
            if "EACCESS" in error_message or "Invalid email or password" in error_message:
                print(f"  ❌ LOGIN ERROR: Invalid email/password or access denied.")
            else:
                print(f"  ❌ API ERROR: {error_message}")
        
        except Exception as e:
            # General handling for other errors
            print(f"  ❌ Unexpected error: {e}")
        
        finally:
            # Ensure a separating line after each operation
            print("-" * 50)


if __name__ == "__main__":
    check_mega_usage()
