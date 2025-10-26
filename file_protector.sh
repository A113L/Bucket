#!/bin/bash
# -----------------------------------------------------------------------------
# Interactive File Protector Script (Encryption/Decryption)
# Dependencies: Requires the 'openssl' command-line tool.
# Usage: Run in terminal: bash file_protector.sh
# -----------------------------------------------------------------------------

# Configuration
ENCRYPT_EXT=".enc"
CIPHER_METHOD="aes-256-cbc"

# --- Utility Functions ---

# Function to display error messages
error_message() {
    echo -e "\n\033[31m[ERROR]\033[0m $1"
}

# Function to get secure password input
get_password() {
    read -rsp "Enter password (will not be visible): " PASSWORD
    echo "" # Add a newline after secure input
}

# --- Core Logic ---

# 1. Encrypts a file
encrypt_file() {
    echo -e "\n--- File Encryption ---"
    read -rp "Enter the filename to encrypt (e.g., secret.txt): " INPUT_FILE

    if [ ! -f "$INPUT_FILE" ]; then
        error_message "File '$INPUT_FILE' not found."
        return 1
    fi

    OUTPUT_FILE="${INPUT_FILE}${ENCRYPT_EXT}"
    get_password

    echo -e "\nEncrypting '$INPUT_FILE' to '$OUTPUT_FILE'..."

    # Use openssl with PBKDF2 for robust key derivation
    if openssl enc -"$CIPHER_METHOD" -salt -pbkdf2 -in "$INPUT_FILE" -out "$OUTPUT_FILE" -k "$PASSWORD"; then
        echo -e "\033[32m[SUCCESS]\033[0m File encrypted successfully!"
        read -rp "Do you want to securely delete the original file '$INPUT_FILE'? (y/N): " DELETE_CONFIRM
        if [[ "$DELETE_CONFIRM" =~ ^[Yy]$ ]]; then
            # Check for 'shred' utility to perform secure, multi-pass file deletion.
            if command -v shred >/dev/null 2>&1; then
                # -u ensures file is overwritten, renamed, and deleted
                shred -u "$INPUT_FILE"
                echo -e "\033[33m[WARNING]\033[0m Original file securely deleted using shred (multi-pass overwrite)."
            else
                # Fallback to standard removal if shred is not found (less secure)
                rm -f "$INPUT_FILE"
                echo -e "\033[33m[WARNING]\033[0m Original file deleted using standard 'rm' (less secure)."
            fi
        fi
    else
        error_message "Encryption failed. Check your file path or permissions."
    fi
}

# 2. Decrypts a file
decrypt_file() {
    echo -e "\n--- File Decryption ---"
    read -rp "Enter the encrypted filename (e.g., secret.txt.enc): " INPUT_FILE

    if [ ! -f "$INPUT_FILE" ]; then
        error_message "File '$INPUT_FILE' not found."
        return 1
    fi

    # Determine output filename by stripping the encryption extension
    OUTPUT_FILE="${INPUT_FILE%$ENCRYPT_EXT}"
    if [ "$OUTPUT_FILE" == "$INPUT_FILE" ]; then
        error_message "Input file does not end with '$ENCRYPT_EXT'. Specify the output filename manually."
        read -rp "Enter the desired output filename: " OUTPUT_FILE
        if [ -z "$OUTPUT_FILE" ]; then
            error_message "No output filename provided. Aborting decryption."
            return 1
        fi
    fi

    if [ -f "$OUTPUT_FILE" ]; then
        error_message "Output file '$OUTPUT_FILE' already exists. Aborting to prevent overwrite."
        return 1
    fi

    get_password

    echo -e "\nDecrypting '$INPUT_FILE' to '$OUTPUT_FILE'..."

    # Use openssl to decrypt, including -pbkdf2 to match the encryption method
    if openssl enc -d -"$CIPHER_METHOD" -pbkdf2 -in "$INPUT_FILE" -out "$OUTPUT_FILE" -k "$PASSWORD"; then
        echo -e "\033[32m[SUCCESS]\033[0m File decrypted successfully!"
    else
        error_message "Decryption failed. Check your password or file integrity."
    fi
}

# --- Main Menu ---

main_menu() {
    echo "========================================="
    echo "        File Protection Utility (Bash)     "
    echo "========================================="
    echo "1. Encrypt a File"
    echo "2. Decrypt a File"
    echo "3. Exit"
    echo "========================================="

    read -rp "Enter your choice (1-3): " CHOICE

    case "$CHOICE" in
        1)
            encrypt_file
            main_menu
            ;;
        2)
            decrypt_file
            main_menu
            ;;
        3)
            echo -e "\nGoodbye! Data security is important."
            exit 0
            ;;
        *)
            error_message "Invalid choice. Please enter 1, 2, or 3."
            main_menu
            ;;
    esac
}

# Start the main script process
main_menu
