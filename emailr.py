#!/usr/bin/env python3
"""
Email-Based Hashcat Rule Extractor

This script processes a file containing email addresses, extracts trailing digit sequences
from the usernames (before the '@'), filters them by specified domains, and generates
Hashcat-compatible rule strings.

Each rule is based on a digit sequence + domain combination (e.g., '123@gmail.com'), 
transformed into a Hashcat rule using the format `$1$2$3...` for each character.

Functionality:
- Reads email addresses from an input file.
- Filters addresses by user-specified domain(s) (e.g., 'gmail.com', 'yahoo.com').
- Extracts trailing digits from the local-part (e.g., 'user123' -> '123').
- Groups and counts digit-domain combinations.
- Generates Hashcat rules from the most common combinations.
- Saves rules to an output file.
- Displays the top 5 most frequent patterns with example emails.

Usage:
    - Run the script and provide:
        1. Path to the input file containing emails (one per line).
        2. Comma-separated list of domains to filter.
        3. Path to save the output Hashcat rules.

Example:
    $ python3 emailr.py
    Enter path to input file containing emails: emails.txt
    Enter comma-separated domains to filter (e.g., gmail.com,yahoo.com): gmail.com,yahoo.com
    Enter path to save generated hashcat rules: rules.txt

Output:
    - A file containing one Hashcat rule per line.
    - Console output showing top 5 rules with example emails and frequency.
"""
import re
from collections import Counter, defaultdict

def extract_data_from_email(email):
    match = re.match(r'^([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})$', email.strip())
    if not match:
        return None
    user, domain = match.groups()
    digits_match = re.search(r'(\d+)$', user)
    if digits_match:
        digits = digits_match.group(1)
        return digits, domain.lower()
    return None

def string_to_hashcat_rule(s):
    return ''.join(f"${c}" for c in s)

def main():
    input_path = input("Enter path to input file containing emails: ").strip()
    domains_input = input("Enter comma-separated domains to filter (e.g., gmail.com,yahoo.com): ").strip()
    output_path = input("Enter path to save generated hashcat rules: ").strip()

    domains_to_include = set(domain.strip().lower() for domain in domains_input.split(',') if domain.strip())
    counter = Counter()
    examples = defaultdict(list)

    with open(input_path, 'r', encoding='utf-8') as f:
        for line in f:
            email = line.strip()
            extracted = extract_data_from_email(email)
            if extracted:
                digits, domain = extracted
                if domain in domains_to_include:
                    key = (digits, domain)
                    counter[key] += 1
                    if len(examples[key]) < 3:
                        examples[key].append(email)

    sorted_items = counter.most_common()

    with open(output_path, 'w', encoding='utf-8') as out:
        for (digits, domain), count in sorted_items:
            rule = string_to_hashcat_rule(digits + '@' + domain)
            out.write(f"{rule}\n")

    print(f"\nDone! {len(sorted_items)} rules written to {output_path}")
    print("Top 5 extracted rules with examples:")
    for (digits, domain), count in sorted_items[:5]:
        rule = string_to_hashcat_rule(digits + '@' + domain)
        print(f"  Rule: {rule} | Count: {count} | Examples: {examples[(digits, domain)]}")

if __name__ == '__main__':
    main()
