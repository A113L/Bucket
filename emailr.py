#!/usr/bin/env python3
"""
Email-Based Hashcat Rule Extractor

This script processes a file containing email addresses. It supports two input formats:
1. Plain email address (e.g., 'user123@gmail.com')
2. Hash:Email format (e.g., '1a2b3c4d5e6f:user123@gmail.com')

It extracts trailing digit sequences from the usernames, filters them by user-specified
domains, and generates Hashcat-compatible rule strings.

Functionality:
- Reads input file supporting both plain email and 'hash:mail' formats.
- Prompts the user for the maximum number of top domains to display.
- Analyzes and displays the top domains based on the user's limit.
- Filters addresses by user-specified domain(s).
- Extracts trailing digits from the local-part.
- Groups and counts digit-domain combinations.
- Generates Hashcat rules from the most common combinations.
- Saves rules to an output file.
- **Removed: Display of the top 5 most frequent patterns.**

Usage:
    - Run the script and provide:
        1. Path to the input file containing emails/hashes (one per line).
        2. Limit for the number of domains to display.
        3. Comma-separated list of domains to filter.
        4. Path to save the output Hashcat rules.
"""
import sys
import re
from collections import Counter, defaultdict

def get_file_path(prompt):
    """Handles continuous prompting until a non-empty path is entered."""
    while True:
        path = input(prompt).strip()
        if path:
            return path
        print("Path cannot be empty. Please try again.")

def get_integer_input(prompt, default_value=20):
    """Handles continuous prompting until a valid integer is entered, or returns default."""
    while True:
        value = input(f"{prompt} (Default: {default_value}): ").strip()
        if not value:
            return default_value
        try:
            num = int(value)
            if num > 0:
                return num
            print("The number must be positive. Please try again.")
        except ValueError:
            print("Invalid number. Please try again.")

def extract_data_from_email(email):
    """
    Extracts the local part and domain from an email.
    Returns (digits, domain) if the local part ends in digits, otherwise None.
    """
    # Regex to validate email structure and separate user/domain
    match = re.match(r'^([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})$', email.strip())
    if not match:
        return None
    
    user, domain = match.groups()
    domain = domain.lower() # Normalize domain to lowercase
    
    # Check for trailing digits in the local part (username)
    digits_match = re.search(r'(\d+)$', user)
    
    if digits_match:
        digits = digits_match.group(1)
        return digits, domain
        
    return None

def string_to_hashcat_rule(s):
    """Converts a string (e.g., '123@gmail.com') to a Hashcat rule (e.g., '$1$2$3$@$g$m$a$i$l$.$c$o$m')."""
    return ''.join(f"${c}" for c in s)

def print_top_domains(file_path, limit):
    """Reads the file, counts all domains, and prints the top 'limit' domains.
       Now handles 'hash:mail' lines by ignoring the hash part."""
    domain_counts = Counter()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                # Handle 'hash:mail' format by splitting and taking the second part
                if ':' in line and '@' in line.split(':', 1)[-1]:
                    email = line.split(':', 1)[-1]
                elif '@' in line:
                    email = line
                else:
                    continue

                # Extract domain from the email part
                if '@' in email:
                    _, domain = email.rsplit('@', 1) 
                    if domain:
                        domain_counts[domain.lower()] += 1
    except FileNotFoundError:
        print(f"\nError: File not found at '{file_path}'", file=sys.stderr)
        return False
    except Exception as e:
        print(f"\nAn error occurred while reading the file: {e}", file=sys.stderr)
        return False

    top_domains_list = domain_counts.most_common(limit)
    
    print("\n" + "="*50)
    print(f"🥇 Top {len(top_domains_list)} Domains Found in the Input File:")
    print("="*50)
    # Print the top domains comma-separated for easy copy-paste
    print(','.join(domain for domain, count in top_domains_list))
    print("="*50 + "\n")
    
    return True

def main():
    """Main function to handle user input, file processing, and rule generation."""
    print("--- Hashcat Rule Extractor for Email Patterns ---")
    
    # 1. Get Input Path
    input_path = get_file_path("Enter path to input file containing emails (or hash:mail): ")

    # 2. Get Domain Display Limit
    domain_limit = get_integer_input("Enter the maximum number of top domains to display")
    
    # 3. Display Top Domains
    if not print_top_domains(input_path, limit=domain_limit):
        # Exit if file reading failed
        sys.exit(1)
        
    # 4. Get Domains to Filter
    domains_input = input("Enter comma-separated domains to filter (e.g., gmail.com,yahoo.com): ").strip()
    
    # 5. Get Output Path
    output_path = get_file_path("Enter path to save generated hashcat rules: ")

    domains_to_include = set(domain.strip().lower() for domain in domains_input.split(',') if domain.strip())
    
    if not domains_to_include:
        print("\nWarning: No domains were specified for filtering. Exiting.", file=sys.stderr)
        sys.exit(0)
        
    counter = Counter()
    # Examples list is still needed to provide context in case the user wants to debug or verify later, 
    # but we won't print them in the final summary.
    examples = defaultdict(list) 

    print("\nProcessing file...")
    
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                # --- LOGIC FOR HANDLING 'hash:mail' ---
                if ':' in line and '@' in line.split(':', 1)[-1]:
                    # Assumes format is always 'hash:email', take the part after the first colon
                    email = line.split(':', 1)[-1]
                else:
                    # Treat the whole line as a plain email
                    email = line
                # --- END LOGIC ---

                extracted = extract_data_from_email(email)
                
                if extracted:
                    digits, domain = extracted
                    if domain in domains_to_include:
                        key = (digits, domain)
                        counter[key] += 1
                        # Store a few examples for display later
                        if len(examples[key]) < 3:
                            # Store the original input line (hash:mail or plain email) as the example
                            examples[key].append(line)
    except Exception as e:
        print(f"An error occurred during file processing: {e}", file=sys.stderr)
        sys.exit(1)


    sorted_items = counter.most_common()

    # 6. Write Rules to Output File
    try:
        with open(output_path, 'w', encoding='utf-8') as out:
            for (digits, domain), count in sorted_items:
                # Rule format: '$d$i$g$i$t$s$@$d$o$m$a$i$n$.$c$o$m'
                rule = string_to_hashcat_rule(digits + '@' + domain)
                out.write(f"{rule}\n")
    except Exception as e:
        print(f"Error writing to output file '{output_path}': {e}", file=sys.stderr)
        sys.exit(1)


    # 7. Display Summary
    print(f"\nDone! {len(sorted_items)} rules written to {output_path}")

    if not sorted_items:
        print("  No patterns found matching the specified domains and having trailing digits.")
        return

if __name__ == '__main__':
    main()
