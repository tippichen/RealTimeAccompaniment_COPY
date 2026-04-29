import os
import re

def split_single_msglog(file_path):
    """Read a single msglog file and split it by device using Regex to bypass corruption."""
    
    # 1. Check if the file exists
    if not os.path.exists(file_path):
        print(f"[Error] File not found: {file_path}")
        return

    print(f"=== Started processing: {file_path} ===")
    
    # 2. Extract data using Regular Expressions (Immune to Python syntax errors like ww4243)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            
        devices = {}
        
        # Regex pattern explanation:
        # \[ \s* '([^']+)' \s* , [^\]]+ \]
        # Looks for: ['DeviceName', anything_here_until_closing_bracket]
        pattern = re.compile(r"\[\s*'([^']+)'\s*,[^\]]+\]")
        
        for match in pattern.finditer(content):
            full_row_str = match.group(0) # e.g., "['Keyboard1', ww4243]"
            dev_name = match.group(1)     # e.g., "Keyboard1"
            
            if dev_name not in devices:
                devices[dev_name] = []
            # Store the raw string representation of the event
            devices[dev_name].append(full_row_str)
            
        if not devices:
            print("[Error] No valid device events found. Check file format.")
            return

    except Exception as e:
        print(f"[Error] File reading failed: {e}")
        return

    # 3. Get the original folder path and output the split files
    folder_dir = os.path.dirname(file_path)
    print(f"Found {len(devices)} device(s): {', '.join(devices.keys())}")
    
    for dev_name, event_strings in devices.items():
        # Construct the new filename and path
        out_filename = f"{dev_name}_original_recording.txt"
        out_path = os.path.join(folder_dir, out_filename)
        
        # Manually join the text blocks to form a valid list string: "[ [...], [...] ]"
        final_content = "[" + ", ".join(event_strings) + "]"
        
        # Write to file
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(final_content)
            
        print(f"  -> [Success] Generated: {out_path} ({len(event_strings)} events in total)")
        
    print("=== Processing Complete ===")

# ==========================================
# Execution block: Target file path
# ==========================================
target_file = os.path.join("data", "12_5", "inputmsglog.txt")

# Call the function
split_single_msglog(target_file)