#!/bin/bash

# --- Script Description and Configuration ---
# This script parses a log file (from a tool like hashcat) to extract line numbers 
# of invalid rules and then deletes those lines from the rule file.
# run first hashcat -a 0 -m 0 hash.txt wordlist.txt -r rules/invalid.rule | tee -a log.txt


# The log file containing the invalid rule line numbers
LOG_FILE="./log.txt"
# Temporary file to hold the actual sed delete commands (e.g., 1d, 2d, 3d, ...)
SED_SCRIPT_FILE="/tmp/sed_commands_$$" 

# --- Interactive Input for Rule File Path ---
echo "--- Rule File Cleaner ---"
# Prompts the user to input the path to the rule file (e.g., rules/invalid.rule)
read -p "Please enter the path to the rule file you want to clean: " INPUT_FILE

# Check if the input file path is empty
if [ -z "$INPUT_FILE" ]; then
    echo "❌ Error: Rule file path cannot be empty. Exiting."
    exit 1
fi

# Temporary file used during the cleaning process
OUTPUT_FILE="${INPUT_FILE}.temp"

# --- Extraction and Formatting of Line Numbers ---

echo "Parsing ${LOG_FILE} to find invalid line numbers..."

# 1. Use grep with PCRE to pull the line numbers (e.g., 1850, 2402) after 'on line '
# 2. Sort the numbers numerically and remove duplicates (uniq).
# 3. Format them into one command per line (e.g., 1d, 2d, 3d, ...) and pipe to the temporary script file.
DELETE_COMMANDS=$( \
    grep -oP 'on line \K\d+' "${LOG_FILE}" 2>/dev/null | \
    sort -n | \
    uniq | \
    sed 's/$/d/' > "${SED_SCRIPT_FILE}" \
)

# Count the number of unique lines to be deleted
DELETE_COUNT=$(wc -l < "${SED_SCRIPT_FILE}")

# Check if any commands were successfully generated (i.e., if the file is empty)
if [ "$DELETE_COUNT" -eq 0 ]; then
    echo "✅ No invalid lines found in ${LOG_FILE} to delete. Exiting."
    rm -f "${SED_SCRIPT_FILE}"
    exit 0
fi

# --- Execution ---

echo "Found ${DELETE_COUNT} unique line numbers to delete. Starting removal from ${INPUT_FILE}..."

# 1. Check if the input file exists
if [ ! -f "${INPUT_FILE}" ]; then
    echo "❌ Error: Input rule file ${INPUT_FILE} not found. Exiting."
    echo "Please ensure the path is correct."
    rm -f "${SED_SCRIPT_FILE}"
    exit 1
fi

# 2. Ensure the directory for the temporary file exists
TEMP_FILE_DIR=$(dirname "${INPUT_FILE}")
mkdir -p "${TEMP_FILE_DIR}"

# 3. Use sed to apply all deletion commands from the temporary script file (-f flag)
# The command will look like: sed -f "/tmp/sed_commands_12345" "rules/invalid.rule" > "rules/invalid.rule.temp"
if sed -f "${SED_SCRIPT_FILE}" "${INPUT_FILE}" > "${OUTPUT_FILE}"; then
    
    # 4. Overwrite the original file with the cleaned temporary file
    mv "${OUTPUT_FILE}" "${INPUT_FILE}"
    echo "✅ Successfully removed ${DELETE_COUNT} invalid lines. The file ${INPUT_FILE} has been updated."
else
    echo "❌ Error: The sed command failed. The original file was not modified."
    # 5. Clean up the temporary file on error
    rm -f "${OUTPUT_FILE}"
fi

# 6. Always clean up the temporary sed script file
rm -f "${SED_SCRIPT_FILE}"
