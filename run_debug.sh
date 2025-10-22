#!/bin/bash

# --- Constant Hashcat Settings ---
HASHCAT_BIN="./hashcat.bin"
# Hashcat options that are constant
HASHCAT_OPTIONS="-a0 -m0 -w4 --bitmap-max=28 --potfile-disable -O --debug-mode=1"

# --- Function for Interactive Input ---
get_input() {
    local prompt="$1"
    local default_value="$2"
    local result_var="$3"
    
    # Check if a default value is provided and non-empty
    if [ -n "$default_value" ]; then
        read -r -p "$prompt [$default_value]: " input
        if [ -z "$input" ]; then
            eval "$result_var='$default_value'"
        else
            eval "$result_var='$input'"
        fi
    else
        # If no default value, input is mandatory (loop until non-empty)
        while true; do
            read -r -p "$prompt: " input
            if [ -n "$input" ]; then
                eval "$result_var='$input'"
                break
            fi
            echo "Input cannot be empty. Please provide a value."
        done
    fi
}

echo "--- Hashcat Benchmark Automation Script (Interactive) ---"

# --- 1. Get Hash File Part (Mandatory) ---
if [ -z "$1" ]; then
    echo ""
    echo ">> Step 1: Hashlist File << "
    echo "Please provide the FULL PATH (or relative path) to ONE part of the hashlist file."
    echo "Example: hashes/benchmarks/MD5_debug_hashes.txt_aa"
    get_input "Hashlist file part path" "" INPUT_FILE
else
    INPUT_FILE="$1"
fi

# --- 2. Get Wordlist File ---
if [ -z "$2" ]; then
    echo ""
    echo ">> Step 2: Wordlist File << "
    echo "Provide the path to the wordlist file."
    echo "Example: /mnt/wlists/hc_wordlist.txt.gz"
    get_input "Wordlist file path" "" WORDLIST
else
    WORDLIST="$2"
fi

# --- 3. Get Rule File ---
if [ -z "$3" ]; then
    echo ""
    echo ">> Step 3: Rule File << "
    echo "Provide the path to the rule file."
    echo "Example: rules.bak/MT/stats-gen_TOP_500000.rule"
    get_input "Rule file path" "" RULE_FILE
else
    RULE_FILE="$3"
fi

# --- 4. Get Debug Output File ---
if [ -z "$4" ]; then
    echo ""
    echo ">> Step 4: Debug Output File << "
    echo "Provide the desired name for the debug statistics file."
    echo "Example: debugged.txt"
    get_input "Debug output file name" "debugged.txt" DEBUG_FILE
else
    DEBUG_FILE="$4"
fi

# --- Validation and Prefix Extraction ---

# Check if the provided hash file part exists
if [ ! -f "$INPUT_FILE" ]; then
    echo "ERROR: Hash file part '$INPUT_FILE' does not exist."
    exit 1
fi

# Check if the wordlist exists
if [ ! -f "$WORDLIST" ]; then
    echo "ERROR: Wordlist file '$WORDLIST' does not exist."
    exit 1
fi

# Check if the rule file exists
if [ ! -f "$RULE_FILE" ]; then
    echo "ERROR: Rule file '$RULE_FILE' does not exist."
    exit 1
fi

# Extract Directory and Base Name
DIR_NAME=$(dirname "$INPUT_FILE")
BASE_NAME=$(basename "$INPUT_FILE")

# Check if the filename is long enough to remove the two-character suffix
if [ ${#BASE_NAME} -lt 3 ]; then
    echo "ERROR: Hash file name is too short. Expected format is e.g., name_xx."
    exit 1
fi

# Remove the two-character suffix (e.g., _aa) to get the prefix
PREFIX_BASE="${BASE_NAME%??}"
# Combine directory and base prefix (e.g., hashes/benchmarks/MD5_debug_hashes.txt_)
FILE_PREFIX="${DIR_NAME}/${PREFIX_BASE}"
SEARCH_PATTERN="${FILE_PREFIX}*"

echo ""
echo "--- Benchmark Settings Summary ---"
echo "Hash Base (Prefix): ${FILE_PREFIX}*"
echo "Wordlist: ${WORDLIST}"
echo "Rule File: ${RULE_FILE}"
echo "Debug Output: ${DEBUG_FILE}"
echo "----------------------------------"

# --- Main Processing Loop ---

echo "Starting processing of files matching the pattern: ${SEARCH_PATTERN}"
echo ""

# Find and process all files matching the prefix
for HASH_FILE in $(ls -v $SEARCH_PATTERN 2>/dev/null); do
    
    if [ ! -f "$HASH_FILE" ]; then
        echo "WARNING: Skipping ${HASH_FILE}, file does not exist or 'ls' returned an error."
        continue
    fi

    echo ">>> STARTING: ${HASH_FILE} <<<"

    # Full hashcat command
    $HASHCAT_BIN $HASHCAT_OPTIONS \
        "$HASH_FILE" \
        "$WORDLIST" \
        -r "$RULE_FILE" \
        --debug-file="$DEBUG_FILE"
    
    EXIT_CODE=$?

    if [ $EXIT_CODE -eq 0 ]; then
        echo "SUCCESSFULLY FINISHED: ${HASH_FILE} (Code: 0)"
    else
        echo "EXECUTION ERROR: ${HASH_FILE} (Code: $EXIT_CODE)"
        # If you want to stop the script on the first error, uncomment:
        # exit $EXIT_CODE
    fi

    echo "---"

done

echo "Finished processing all hash parts."
