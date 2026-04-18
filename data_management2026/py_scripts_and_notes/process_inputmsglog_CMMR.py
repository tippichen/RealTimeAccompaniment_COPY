#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import glob
import re
from pathlib import Path

def replace_strings_with_indices(file_path):
    """
    Read a file containing nested arrays and replace all string values with indices.
    Example: [['Keyboard1', 144, 72, 80, 5.11], ...] 
             becomes [[0, 144, 72, 80, 5.11], [1, 144, 72, 80, 5.11], ...]
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse the content as a Python literal
        # The file contains a list of lists
        data = eval(content)
        
        # Process each inner list
        index_counter = 0
        new_data = []
        
        for item in data:
            if isinstance(item, list):
                new_item = []
                for element in item:
                    # Replace strings with indices
                    if isinstance(element, str):
                        new_item.append(index_counter)
                        index_counter += 1
                    else:
                        new_item.append(element)
                new_data.append(new_item)
        
        # Write the modified data back to the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(str(new_data))
        
        print(f"✓ Processed: {file_path}")
        return True
    
    except Exception as e:
        print(f"✗ Error processing {file_path}: {str(e)}")
        return False


def main():
    """
    Main function to process all inputmsglog.txt files in logs directory.
    Skips the 'old' subdirectory.
    """
    logs_dir = Path(__file__).parent
    print(f"Processing directory: {logs_dir}\n")
    
    # Find all inputmsglog.txt files, excluding those in 'old' directory
    input_files = []
    for root, dirs, files in os.walk(logs_dir):
        # Skip the 'old' directory
        if 'old' in dirs:
            dirs.remove('old')
        
        if 'inputmsglog.txt' in files:
            file_path = os.path.join(root, 'inputmsglog.txt')
            input_files.append(file_path)
    
    if not input_files:
        print("No inputmsglog.txt files found.")
        return
    
    print(f"Found {len(input_files)} inputmsglog.txt file(s)\n")
    
    # Process each file
    success_count = 0
    for file_path in input_files:
        if replace_strings_with_indices(file_path):
            success_count += 1
    
    print(f"\n{'='*60}")
    print(f"Processing complete: {success_count}/{len(input_files)} files processed successfully")


if __name__ == '__main__':
    main()
