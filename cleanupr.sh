#!/bin/bash

# --- Script Description and Configuration ---
# This script parses a log file (from a tool like hashcat) to extract line numbers 
# of invalid rules and then deletes those lines from the rule file.
# hashcat -a 0 -m 0 hash.txt wordlist.txt -r rules/invalid.rule | tee -a log.txt


# The log file containing the invalid rule line numbers
LOG_FILE="./log.txt"

# EDIT THIS PATH if your file is different (e.g., rules/invalid.rule)
INPUT_FILE="./rules/invalid.rule" 

# Temporary file used during the cleaning process
OUTPUT_FILE="${INPUT_FILE}.temp"

# --- Extraction and Formatting of Line Numbers ---

echo "Parsing ${LOG_FILE} to find invalid line numbers..."

# 1. Use grep with PCRE to pull the line numbers (e.g., 1850, 2402) after 'on line '
# 2. Sort the numbers numerically and remove duplicates (uniq).
# 3. Use sed to format them into a single 'sed delete command' string (e.g., "1850d;2402d;...").
DELETE_COMMANDS=$( \
    grep -oP 'on line \K\d+' "${LOG_FILE}" 2>/dev/null | \
    sort -n | \
    uniq | \
    sed 's/$/d;/' | \
    tr -d '\n' | \
    sed 's/;$//' \
)

# Check if any commands were successfully generated
if [ -z "$DELETE_COMMANDS" ]; then
    echo "No invalid lines found in ${LOG_FILE} to delete. Exiting."
    exit 0
fi

# Count the number of unique lines to be deleted
DELETE_COUNT=$(echo "$DELETE_COMMANDS" | grep -o 'd' | wc -l)

# --- Execution ---

echo "Found ${DELETE_COUNT} unique line numbers to delete. Starting removal from ${INPUT_FILE}..."

# 1. Check if the input file exists
if [ ! -f "${INPUT_FILE}" ]; then
    echo "Error: Input rule file ${INPUT_FILE} not found. Exiting."
    echo "Please ensure the path is correct or adjust the INPUT_FILE variable in the script."
    exit 1
fi

# 2. Ensure the directory for the temporary file exists
TEMP_FILE_DIR=$(dirname "${INPUT_FILE}")
mkdir -p "${TEMP_FILE_DIR}"

# 3. Use sed to apply all deletion commands and write to the temporary file
# The sed command will look like: sed '1850d;2402d;3374d;...' "rules/invalid.rule" > "rules/invalid.rule.temp"
if sed "${DELETE_COMMANDS}" "${INPUT_FILE}" > "${OUTPUT_FILE}"; then
    
    # 4. Overwrite the original file with the cleaned temporary file
    mv "${OUTPUT_FILE}" "${INPUT_FILE}"
    echo "Successfully removed ${DELETE_COUNT} invalid lines. The file ${INPUT_FILE} has been updated."
else
    echo "Error: The sed command failed. The original file was not modified."
    # 5. Clean up the temporary file on error
    rm -f "${OUTPUT_FILE}"
fi
