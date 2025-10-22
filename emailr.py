#!/usr/bin/env python3
"""
Email-Based Hashcat Rule Extractor

This script processes a file containing email addresses, extracts trailing digit sequences
from the usernames (before the '@'), filters them by specified domains, and generates
Hashcat-compatible rule strings.

It first displays the top 20 most frequent domains in the input file to help the user 
decide which domains to target for rule extraction.

Functionality:
- Reads email addresses from an input file.
- **Analyzes and displays the top 20 overall domains (NEW).**
- Filters addresses by user-specified domain(s) (e.g., 'gmail.com', 'yahoo.com').
- Extracts trailing digits from the local-part (e.g., 'user123' -> '123').
- Groups and counts digit-domain combinations.
- Generates Hashcat rules from the most common combinations.
- Saves rules to an output file.
- Displays the top 5 most frequent patterns with example emails.

Usage:
    - Run the script and provide:
        1. Path to the input file containing emails (one per line).
        2. Comma-separated list of domains to filter (after seeing the top domains).
        3. Path to save the output Hashcat rules.
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

def print_top_domains(file_path, limit=20): # edit limit if required
    """Reads the file, counts all domains, and prints the top 'limit' domains."""
    domain_counts = Counter()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                email = line.strip()
                if '@' in email:
                    # rsplit ensures we only split once from the right
                    _, domain = email.rsplit('@', 1)
                    if domain:
                        domain_counts[domain.lower()] += 1
    except FileNotFoundError:
        print(f"\nError: File not found at '{file_path}'", file=sys.stderr)
        return False
    except Exception as e:
        print(f"\nAn error occurred while reading the file: {e}", file=sys.stderr)
        return False

    top_domains = [f"{domain} ({count})" for domain, count in domain_counts.most_common(limit)]
    
    print("\n" + "="*50)
    print(f"🥇 Top {limit} Domains Found in the Input File:")
    print("="*50)
    # Print the top domains comma-separated, without spaces, just like the original request's output
    print(','.join(domain for domain, count in domain_counts.most_common(limit)))
    print("="*50 + "\n")
    
    return True

def main():
    """Main function to handle user input, file processing, and rule generation."""
    print("--- Hashcat Rule Extractor for Email Patterns ---")
    
    # 1. Get Input Path and Print Top Domains
    input_path = get_file_path("Enter path to input file containing emails: ")
    
    # Display the top domains before proceeding
    if not print_top_domains(input_path, limit=20):
        # Exit if file reading failed in print_top_domains
        sys.exit(1)
        
    # 2. Get Domains to Filter
    domains_input = input("Enter comma-separated domains to filter (e.g., gmail.com,yahoo.com): ").strip()
    
    # 3. Get Output Path
    output_path = get_file_path("Enter path to save generated hashcat rules: ")

    domains_to_include = set(domain.strip().lower() for domain in domains_input.split(',') if domain.strip())
    
    if not domains_to_include:
        print("\nWarning: No domains were specified for filtering. Exiting.", file=sys.stderr)
        sys.exit(0)
        
    counter = Counter()
    examples = defaultdict(list)

    print("\nProcessing file...")
    
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            for line in f:
                email = line.strip()
                extracted = extract_data_from_email(email)
                
                if extracted:
                    digits, domain = extracted
                    if domain in domains_to_include:
                        key = (digits, domain)
                        counter[key] += 1
                        # Store a few examples for display later
                        if len(examples[key]) < 3:
                            examples[key].append(email)
    except Exception as e:
        print(f"An error occurred during file processing: {e}", file=sys.stderr)
        sys.exit(1)


    sorted_items = counter.most_common()

    # 4. Write Rules to Output File
    try:
        with open(output_path, 'w', encoding='utf-8') as out:
            for (digits, domain), count in sorted_items:
                rule = string_to_hashcat_rule(digits + '@' + domain)
                out.write(f"{rule}\n")
    except Exception as e:
        print(f"Error writing to output file '{output_path}': {e}", file=sys.stderr)
        sys.exit(1)


    # 5. Display Summary
    print(f"\nDone! {len(sorted_items)} rules written to {output_path}")
    print("\nTop 5 extracted rules with examples:")
    
    if not sorted_items:
        print("  No patterns found matching the specified domains and having trailing digits.")
        return

    for (digits, domain), count in sorted_items[:5]:
        rule = string_to_hashcat_rule(digits + '@' + domain)
        print(f"  Rule: {rule} | Count: {count} | Examples: {', '.join(examples[(digits, domain)])}")

if __name__ == '__main__':
    main()
