import os
import ast
import pandas as pd
import difflib
import re

# 1. Define paths
# Since this script is placed in the 'smc2024' root directory, BASE_DIR is set to current '.'
BASE_DIR = '.'
DATA_DIR = os.path.join(BASE_DIR, 'data')
OUTPUT_EXCEL_PATH = os.path.join(BASE_DIR, 'separate.xlsx')

# Define Excel headers
COLUMNS = [
    'Folder', 
    'MIDI Recording 1', 
    'Corresponding Interpretation 1', 
    'MIDI Recording 2', 
    'Corresponding Interpretation 2'
]

def get_interpretation_pitches(file_path):
    """Read interpretation and filter ghost notes (time == 0)"""
    if not os.path.exists(file_path):
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = ast.literal_eval(f.read().strip())
        pitches = []
        for row in data:
            if len(row) >= 6:
                status, note, time_val = row[1], row[2], row[4]
                # Filter notes that were never actually played or aligned (time is 0)
                if status == 144 and (time_val == 0 or time_val == 0.0 or time_val is None):
                    continue
                if status == 144:
                    pitches.append(note)
        return pitches
    except Exception:
        return None

def parse_msglog(file_path):
    """Read msglog and extract full events and pitches classified by device"""
    if not os.path.exists(file_path):
        return {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = ast.literal_eval(f.read().strip())
        devices = {}
        for row in data:
            if len(row) >= 1:
                dev = row[0]
                if dev not in devices:
                    devices[dev] = {'events': [], 'pitches': []}
                # Record full event for file saving
                devices[dev]['events'].append(row)
                # Record pitch for matching
                if len(row) >= 3 and row[1] == 144:
                    devices[dev]['pitches'].append(row[2])
        return devices
    except Exception:
        return {}

def main():
    print("=== Start scanning 'data' folder ===")
    if not os.path.exists(DATA_DIR):
        print(f"[Error] Directory '{DATA_DIR}' not found. Please ensure the script is in the 'smc2024' root.")
        return

    # Scan and sort folders in X_Y format (e.g., 1_1, 1_2)
    folders = [f for f in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, f)) and re.match(r'^\d+_\d+$', f)]
    folders.sort(key=lambda x: [int(p) for p in x.split('_')])

    processed_count = 0
    all_rows = []

    for folder in folders:
        folder_path = os.path.join(DATA_DIR, folder)
        msglog_path = os.path.join(folder_path, 'inputmsglog.txt')

        # Skip if msglog does not exist
        if not os.path.exists(msglog_path):
            continue

        # Parse devices from msglog
        devices = parse_msglog(msglog_path)
        dev_names = list(devices.keys())

        # Condition 1: Skip if there is only 1 device
        if len(dev_names) < 2:
            continue
        
        # Condition 2: Error and skip if there are more than 2 devices
        if len(dev_names) > 2:
            print(f"[Warning] Folder {folder} contains {len(dev_names)} devices ({', '.join(dev_names)}). Skipping.")
            continue

        # --- Process folders with exactly 2 devices ---
        dev1, dev2 = dev_names[0], dev_names[1]
        file1_name = f"{dev1}_original_recording.txt"
        file2_name = f"{dev2}_original_recording.txt"

        # 1. Generate and write split txt files
        with open(os.path.join(folder_path, file1_name), 'w', encoding='utf-8') as f:
            f.write(str(devices[dev1]['events']))
        with open(os.path.join(folder_path, file2_name), 'w', encoding='utf-8') as f:
            f.write(str(devices[dev2]['events']))

        # 2. Prepare for Interpretation matching
        in_interp_path = os.path.join(folder_path, 'inputinterpretation.txt')
        out_interp_path = os.path.join(folder_path, 'outputinterpretation.txt')

        in_pitches = get_interpretation_pitches(in_interp_path)
        out_pitches = get_interpretation_pitches(out_interp_path)

        # Helper function to calculate similarity ratio
        def calc_similarity(seq_a, seq_b):
            if seq_a is None or seq_b is None: return -1
            if len(seq_a) == 0 or len(seq_b) == 0: return 0
            return difflib.SequenceMatcher(None, seq_a, seq_b).ratio()

        acc_1_in = calc_similarity(devices[dev1]['pitches'], in_pitches)
        acc_1_out = calc_similarity(devices[dev1]['pitches'], out_pitches)
        acc_2_in = calc_similarity(devices[dev2]['pitches'], in_pitches)
        acc_2_out = calc_similarity(devices[dev2]['pitches'], out_pitches)

        # Determine best combination: compare (dev1-In + dev2-Out) vs (dev1-Out + dev2-In)
        score_A = acc_1_in + acc_2_out
        score_B = acc_1_out + acc_2_in

        interp1_label = "Missing"
        interp2_label = "Missing"

        # If both interpretations are missing, keep labels as "Missing"
        if in_pitches is None and out_pitches is None:
            pass
        else:
            if score_A >= score_B:
                # Combination A is better: dev1 matches Input, dev2 matches Output
                interp1_label = "inputinterpretation.txt" if in_pitches is not None else "Missing"
                interp2_label = "outputinterpretation.txt" if out_pitches is not None else "Missing"
            else:
                # Combination B is better: dev1 matches Output, dev2 matches Input
                interp1_label = "outputinterpretation.txt" if out_pitches is not None else "Missing"
                interp2_label = "inputinterpretation.txt" if in_pitches is not None else "Missing"

        # 3. Record the row for Excel
        all_rows.append([
            folder,
            file1_name,
            interp1_label,
            file2_name,
            interp2_label
        ])

        print(f"[Success] Folder {folder} | Split: {file1_name} -> {interp1_label}, {file2_name} -> {interp2_label}")
        processed_count += 1

    # 4. Export Excel report
    if all_rows:
        df = pd.DataFrame(all_rows, columns=COLUMNS)
        df.to_excel(OUTPUT_EXCEL_PATH, index=False)
        print(f"\n=== Task Completed ===")
        print(f"Total folders processed with dual devices: {processed_count}")
        print(f"Excel report saved to: {OUTPUT_EXCEL_PATH}")
    else:
        print("\n=== Task Ended ===")
        print("No folders with dual devices found. Excel file was not generated.")

if __name__ == "__main__":
    main()