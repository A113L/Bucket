#!/bin/bash

# --- Script Description and Configuration ---
# This script parses a log file (from a tool like hashcat) to extract line numbers 
# of invalid rules and then deletes those lines from the rule file.
# hashcat -a 0 -m 0 hash.txt wordlist.txt -r rules/invalid.rule | tee -a log.txt


# The log file containing the invalid rule line numbers
LOG_FILE="./log.txt"

# --- Interactive Input for Rule File Path ---
echo "--- Rule File Cleaner (Optimized) ---"
# Prompts the user to input the path to the rule file (e.g., rules/invalid.rule)
read -p "Please enter the path to the rule file you want to clean: " INPUT_FILE

# Check if the input file path is empty
if [ -z "$INPUT_FILE" ]; then
    echo "Error: Rule file path cannot be empty. Exiting."
    exit 1
fi

# Temporary file used during the cleaning process
OUTPUT_FILE="${INPUT_FILE}.temp"

# --- Extraction and Preparation of Line Numbers ---

echo "Parsing ${LOG_FILE} to find invalid line numbers..."

# 1. Use grep with PCRE to extract all line numbers.
# 2. Use sort -u (or sort | uniq) to handle sorting and duplicate removal in one command.
# 3. Store the list of line numbers in a file for awk to read.
# We skip the complex sed formatting entirely.
DELETE_LINES_FILE=$(mktemp)

grep -oP 'on line \K\d+' "${LOG_FILE}" 2>/dev/null | sort -u > "${DELETE_LINES_FILE}"

# Count the number of unique lines to be deleted
DELETE_COUNT=$(wc -l < "${DELETE_LINES_FILE}")

# Check if any commands were successfully generated
if [ "$DELETE_COUNT" -eq 0 ]; then
    echo "No invalid lines found in ${LOG_FILE} to delete. Exiting."
    rm -f "${DELETE_LINES_FILE}"
    exit 0
fi

# --- Execution using AWK for Single-Pass Deletion ---

echo "Found ${DELETE_COUNT} unique line numbers to delete. Starting removal from ${INPUT_FILE} using AWK..."

# 1. Check if the input file exists
if [ ! -f "${INPUT_FILE}" ]; then
    echo "Error: Input rule file ${INPUT_FILE} not found. Exiting."
    echo "Please ensure the path is correct."
    rm -f "${DELETE_LINES_FILE}"
    exit 1
fi

# 2. Use awk to read the rule file, load the lines-to-delete into an array, and perform the deletion in a single pass.
# This avoids the "Argument list too long" error and is much faster than sed with many commands.
if awk '
    # BEGIN block: Runs once before processing the rule file.
    BEGIN {
        # ARGV[1] is the name of the lines file. Read it and populate the DEL array.
        while (getline < ARGV[1]) { 
            DEL[$1] = 1 
        }
        close(ARGV[1])
        # Skip the lines file so awk only processes the rule file next.
        ARGV[1] = ""
    }
    # Main block: Runs for every line in the rule file (now ARGV[2]).
    ! (FNR in DEL) { 
        # FNR is the current record number (line number).
        # If FNR is NOT in the DEL array, print the line.
        print $0 
    }
' "${DELETE_LINES_FILE}" "${INPUT_FILE}" > "${OUTPUT_FILE}"; then
    
    # 3. Overwrite the original file with the cleaned temporary file
    mv "${OUTPUT_FILE}" "${INPUT_FILE}"
    echo "Successfully removed ${DELETE_COUNT} invalid lines. The file ${INPUT_FILE} has been updated."
else
    echo "Error: The AWK command failed. The original file was not modified."
    # 4. Clean up the temporary file on error
    rm -f "${OUTPUT_FILE}"
fi

# 5. Always clean up the temporary line numbers file
rm -f "${DELETE_LINES_FILE}"
