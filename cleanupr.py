#!/usr/bin/env python3

import subprocess
import os

def run_and_rename_cleanup(input_file, temp_output_file="file2", command_binary="./cleanup-rules.bin", command_arg="2"):
    """
    Runs an external command, adds a rule to the start of the output file,
    counts the lines, and renames the file.

    Args:
        input_file (str): The name of the input file (passed via '<'). **(No default value)**
        temp_output_file (str): The name of the temporary output file (passed via '>').
        command_binary (str): The path to the command's binary file.
        command_arg (str): The command argument.

    Returns:
        bool: True if the operation succeeded, False otherwise.
    """
    # Defined rule to add to the start
    RULE_TO_ADD = ":\n"
    
    # 1. Command construction and execution
    print(f"Running command: {command_binary} {command_arg} with input from {input_file} and output to {temp_output_file}...")

    try:
        # Open the input file for reading
        with open(input_file, 'r') as infile:
            # Open the output file for writing
            with open(temp_output_file, 'w') as outfile:
                # Execute the command.
                result = subprocess.run(
                    [command_binary, command_arg],
                    stdin=infile,
                    stdout=outfile,
                    check=True  # Checks the return code (raises an error if non-zero)
                )
        print("Command finished successfully.")

    except FileNotFoundError:
        print(f"ERROR: Binary file not found: {command_binary} or input file: {input_file}")
        return False
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Command returned a non-zero exit code: {e.returncode}")
        print(f"Error details: {e}")
        return False
    except Exception as e:
        print(f"An unknown error occurred during command execution: {e}")
        return False
    
    # --- ADDING THE RULE TO THE START OF THE OUTPUT FILE ---
    try:
        print(f"Adding rule to the start of file: {temp_output_file}...")

        # Read the entire content of the temporary file
        with open(temp_output_file, 'r') as f:
            content = f.read()

        # Write the file again, adding the rule to the start
        with open(temp_output_file, 'w') as f:
            f.write(RULE_TO_ADD)
            f.write(content)

        print("Rule added successfully.")

    except FileNotFoundError:
        print(f"ERROR: File {temp_output_file} not found after command execution. Did the command create it?")
        return False
    except Exception as e:
        print(f"An error occurred while modifying the file: {e}")
        return False
    # ---------------------------------------------------

    # 2. Count lines in the output file (file2) (now with the rule)
    line_count = 0
    try:
        print(f"Counting lines in file: {temp_output_file}...")
        with open(temp_output_file, 'r') as f:
            for _ in f:
                line_count += 1
        print(f"Found {line_count} lines.")

    except FileNotFoundError:
        print(f"ERROR: File {temp_output_file} not found.")
        return False

    # 3. Rename the file
    # Filename format: concentrator_<command_arg>_<line_count>.rule
    new_filename = f"concentrator_{command_arg}_{line_count}.rule"

    try:
        os.rename(temp_output_file, new_filename)
        print(f"Successfully renamed file '{temp_output_file}' to '{new_filename}'.")
        return True
    except OSError as e:
        print(f"ERROR: Failed to rename file: {e}")
        return False


if __name__ == "__main__":
    
    # --- Get input file path from user ---
    # Using 'file1' as a suggested default if no input is provided
    input_path = input("Enter the path to the input file (e.g., file1): ").strip() or "file1"

    # Creating a dummy input file for testing if the user accepts the default 'file1' 
    # and it doesn't already exist.
    if input_path == "file1" and not os.path.exists(input_path):
        print("Creating dummy file 'file1' for testing.")
        with open("file1", "w") as f:
            # Create three lines of content
            f.write("test\nline\ninput\n")
    # ------------------------------------

    # Run the main function
    success = run_and_rename_cleanup(input_path)

    # Cleanup logic remains, but now references 'input_path'
    
    # We leave the resulting file `concentrator_2_*.rule`
    if success and os.path.exists(input_path) and input(f"Delete the test file '{input_path}'? (y/n): ").lower() == 'y':
          os.remove(input_path)
          print(f"Deleted '{input_path}'.")
    # In case of an error, check if the temporary file 'file2' is not the final file
    # and delete it only if the operation failed (renaming didn't occur)
    elif not success and os.path.exists("file2"): 
          os.remove("file2")
          print("Deleted temporary 'file2'.")
