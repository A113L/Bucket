import os
import sys
from PIL import Image
from PIL.ExifTags import TAGS

# --- SAFETY NOTICE ---
# This script is designed to operate ONLY on the files in the CURRENT directory
# to prevent accidental, recursive bulk modification of your entire file system.
# It will create a new file named 'original_filename_CLEANED.ext' for each file processed.
# The original file is not modified or deleted.

IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp', '.tiff', '.tif')
CLEAN_SUFFIX = "_CLEANED"

def view_exif_data(input_path):
    """
    Extracts and prints EXIF data from a single image, translating tags 
    into human-readable names.
    """
    print("-" * 35)
    print(f"EXIF Data for: {input_path}")
    print("-" * 35)
    
    try:
        img = Image.open(input_path)
        # Use _getexif() to retrieve the metadata dictionary
        exif_data = img._getexif()

        if exif_data is None:
            print("No EXIF data found in this image.")
            return

        found_exif = False
        for tag_id, value in exif_data.items():
            # Get the tag name from the TAGS dictionary, defaulting to the ID if not found
            tag_name = TAGS.get(tag_id, tag_id)
            print(f"  {tag_name}: {value}")
            found_exif = True
            
        if not found_exif:
             print("No EXIF data found in this image.")
            
    except Exception as e:
        print(f"❌ Error reading EXIF data: {e}")
    finally:
        print("-" * 35)

def remove_exif_data(input_path):
    """
    Removes EXIF data from a single image and saves the result as a new file.
    The original file is preserved.
    """
    output_path = input_path.rsplit('.', 1)
    if len(output_path) > 1:
        # Create output path: filename_CLEANED.extension
        output_path = f"{output_path[0]}{CLEAN_SUFFIX}.{output_path[1]}"
    else:
        # Handle files without extensions, append CLEANED
        output_path = f"{input_path}{CLEAN_SUFFIX}"

    try:
        # 1. Open the image
        img = Image.open(input_path)
        
        # 2. Extract image data without EXIF (discarding the 'info' dictionary)
        data = list(img.getdata())
        
        # 3. Create a new image from the raw data
        new_img = Image.new(img.mode, img.size)
        new_img.putdata(data)
        
        # 4. Determine save arguments (copying format but excluding EXIF)
        save_kwargs = {}
        if img.format:
            save_kwargs['format'] = img.format

        # 5. Save the new image without metadata
        new_img.save(output_path, **save_kwargs)
        
        print(f"✅ CLEANED and saved to: {output_path}")
        
    except FileNotFoundError:
        print(f"❌ Error: The file '{input_path}' was not found. Skipping.")
    except Exception as e:
        print(f"❌ An unexpected error occurred while cleaning '{input_path}': {e}")

def main():
    """Main function to perform interactive, non-recursive EXIF cleaning."""
    print("--- Safe Interactive EXIF Cleaner ---")
    print("WARNING: This script processes files ONLY in the current directory.")
    print("It requires the 'Pillow' library: pip install Pillow")
    print("-" * 35)

    try:
        # List all files in the current directory
        files = os.listdir('.')
    except Exception as e:
        print(f"Error accessing current directory: {e}")
        return

    image_files = [f for f in files if f.lower().endswith(IMAGE_EXTENSIONS) and CLEAN_SUFFIX not in f]
    
    if not image_files:
        print("No eligible image files found in the current directory.")
        print("Supported formats: JPG, JPEG, PNG, WEBP, TIFF.")
        return

    print(f"Found {len(image_files)} image file(s) to process.")
    
    for filename in image_files:
        print(f"\nProcessing: {filename}")
        
        while True:
            # Interactive confirmation prompt updated to include 'v'
            user_input = input("Action (y: clean, n: skip, v: view EXIF, q: quit): ").lower().strip()
            
            if user_input == 'y':
                remove_exif_data(filename)
                break # Move to the next file
            elif user_input == 'v':
                view_exif_data(filename)
                # Loop continues, re-prompting for action on the same file
            elif user_input == 'n':
                print(f"⏩ Skipping {filename}.")
                break # Move to the next file
            elif user_input == 'q':
                print("Quitting script. No further files processed.")
                return # Exit main function entirely
            else:
                print("Invalid input. Please use 'y', 'n', 'v', or 'q'.")

if __name__ == "__main__":
    main()
