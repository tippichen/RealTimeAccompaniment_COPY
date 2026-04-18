import os
import ast
import pandas as pd
import difflib
import re
import shutil

# ==========================================
# 1. Dynamic Relative Path Setup
# ==========================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)

OLD_SMC_DIR = os.path.join(ROOT_DIR, 'SMC2024')
NEW_SMC_DIR = os.path.join(ROOT_DIR, 'data_management2026', 'SMC2024', 'data')
ENTRY_DIR = os.path.join(ROOT_DIR, 'data_management2026', 'entry')

FINAL_EXCEL_PATH = os.path.join(OLD_SMC_DIR, 'SMC2024_auto_filled_FINAL.xlsx')
MIDI_EXCEL_PATH = os.path.join(OLD_SMC_DIR, 'separate_midi.xlsx')
OUTPUT_EXCEL_PATH = os.path.join(ROOT_DIR, 'data_management2026', 'sample_database_SMC2024_filled.xlsx')

os.makedirs(ENTRY_DIR, exist_ok=True)

print("=== System Path Initialization ===")
print(f"Project Root: {ROOT_DIR}")
print(f"Old SMC Dir:  {OLD_SMC_DIR}")
print(f"New SMC Dir:  {NEW_SMC_DIR}")
print(f"Entry Target: {ENTRY_DIR}")

# ==========================================
# 2. Define GT Score Mapping
# ==========================================
GT_INFO = {
    r"SMC2024\gt\SMC_gounod_16_1\outputscore.txt": "SMC_gounod_16_1",
    r"SMC2024\gt\SMC_gounod_16_1\outputscore_concat.txt": "SMC_gounod_16_1_Concatenation",
    r"SMC2024\gt\SMC_gounod_16_2\outputscore.txt": "SMC_gounod_16_2",
    r"SMC2024\gt\SMC_gounod_melody_1\outputscore.txt": "SMC_gounod_melody_1",
    r"SMC2024\gt\SMC_gounod_melody_1\outputscore_concat.txt": "SMC_gounod_melody_1_Concatenation",
    r"SMC2024\gt\SMC_gounod_melody_2\outputscore.txt": "SMC_gounod_melody_2",
    r"SMC2024\gt\SMC_little_star_LH4\outputscore.txt": "SMC_little_star_LH4",
    r"SMC2024\gt\SMC_little_star_LH16\outputscore.txt": "SMC_little_star_LH16",
    r"SMC2024\gt\SMC_little_star_RH\outputscore.txt": "SMC_little_star_RH"
}

# ==========================================
# 3. Helper Functions
# ==========================================
def get_gt_pitch(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = ast.literal_eval(f.read().strip())
            return [row[2] for row in data if len(row) >= 3 and row[1] == 144]
    except: return []

def get_interpretation_pitch(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = ast.literal_eval(f.read().strip())
            pitches = []
            for row in data:
                if len(row) >= 6:
                    status, note, time_val = row[1], row[2], row[4]
                    if status == 144 and (time_val == 0 or time_val == 0.0 or time_val is None):
                        continue
                    if status == 144: pitches.append(note)
            return pitches
    except: return []

# Pre-load GT Sequences
print("\n=== Loading Ground Truth Sequences ===")
gt_sequences = {}
for score_path, music_piece in GT_INFO.items():
    relative_path = score_path.replace("SMC2024\\", "", 1) 
    sys_path = os.path.join(OLD_SMC_DIR, relative_path.replace('\\', os.sep))
    seq = get_gt_pitch(sys_path)
    gt_sequences[score_path] = {"music_piece": music_piece, "seq": seq}
    
    if seq:
        print(f"[Success] Loaded GT: {music_piece} (Length: {len(seq)})")
    else:
        print(f"[Warning] Failed to load or empty GT file at: {sys_path}")

# ==========================================
# 4. Read Excel Dictionaries
# ==========================================
print("\n=== Loading Excel Reference Databases ===")
player_dict = {}
try:
    if os.path.exists(FINAL_EXCEL_PATH):
        final_df = pd.read_excel(FINAL_EXCEL_PATH)
        for _, row in final_df.iterrows():
            path_val = str(row['file name and path']).strip(' "').replace('\\', '/')
            player_dict[path_val] = str(row['player ']).strip()
        print(f"[Success] Loaded {len(player_dict)} valid paths from FINAL Excel.")
    else:
        print(f"[Error] FINAL Excel NOT FOUND at: {FINAL_EXCEL_PATH}")
except Exception as e:
    print(f"[Error] Exception while reading FINAL Excel: {e}")

midi_dict = {}
try:
    if os.path.exists(MIDI_EXCEL_PATH):
        midi_df = pd.read_excel(MIDI_EXCEL_PATH)
        for _, row in midi_df.iterrows():
            folder = str(row['Folder']).strip()
            midi_dict[folder] = {
                str(row['Corresponding Interpretation 1']).strip(): str(row['MIDI Recording 1']).strip(),
                str(row['Corresponding Interpretation 2']).strip(): str(row['MIDI Recording 2']).strip()
            }
        print(f"[Success] Loaded {len(midi_dict)} folder rules from separate_midi Excel.")
    else:
        print(f"[Warning] separate_midi Excel NOT FOUND at: {MIDI_EXCEL_PATH}. Will fallback to 'None'.")
except Exception as e:
    print(f"[Error] Exception while reading separate_midi Excel: {e}")

# ==========================================
# 5. Main Scanning and Processing
# ==========================================
print("\n=== Starting File Scan and Copy Process ===")
columns = [
    'entry', 'original file path', 'raw recording source', 'music piece', 
    'score path', 'player ', 'recorded time', 'MIDI recording', 
    'which code align it', 'Concurrent recordings (entry #)'
]

all_rows_data = []
current_entry = 1

if os.path.exists(NEW_SMC_DIR):
    all_items = os.listdir(NEW_SMC_DIR)
    folders = [f for f in all_items if os.path.isdir(os.path.join(NEW_SMC_DIR, f)) and re.match(r'^\d+_\d+$', f)]
    folders.sort(key=lambda x: [int(p) for p in x.split('_')])
else:
    folders = []
    print(f"[Error] New SMC Directory DOES NOT EXIST: {NEW_SMC_DIR}")

for folder_id in folders:
    folder_path = os.path.join(NEW_SMC_DIR, folder_id)
    all_files_in_folder = os.listdir(folder_path)
    
    files = [f for f in all_files_in_folder if f in ['inputinterpretation.txt', 'outputinterpretation.txt']]
    
    if not files:
        continue
    
    for fname in files:
        sys_file_path = os.path.join(folder_path, fname)
        is_output = 'output' in fname.lower()
        
        # 1. Copy file to entry directory
        dest_file_path = os.path.join(ENTRY_DIR, f"{current_entry}.txt")
        shutil.copy2(sys_file_path, dest_file_path)

        # 2. Define original file paths (Tweak 1)
        lookup_path = f"data/{folder_id}/{fname}" 
        orig_file_path = f"data_management2026\\SMC2024\\data\\{folder_id}\\{fname}"
        
        # 3. Handle Player Name Translations
        raw_player = player_dict.get(lookup_path, "?")
        is_ai = False
        
        if raw_player == "AI":
            final_player = "3-oscillator Kuramoto"
            is_ai = True
        elif raw_player in ["?", "kit?", "??", "unknown human"]:
            final_player = "unknown human"
        else:
            final_player = raw_player
        
        # 4. Define raw recording source (Tweak 2)
        if is_output and is_ai:
            raw_source = "None"
        else:
            raw_source = f"SMC2024\\data\\{folder_id}\\inputmsglog.txt"
            
        # 5. Determine Music Piece & Score Path (Tweak 5: Remarks removed, but still matching internally)
        test_seq = get_interpretation_pitch(sys_file_path)
        music_piece_val, score_path_val = "?", "?"
        
        if test_seq:
            max_acc, best_match = -1, None
            for spath, gt_data in gt_sequences.items():
                if not gt_data['seq']: continue
                matcher = difflib.SequenceMatcher(None, test_seq, gt_data['seq'])
                acc = sum(n for i,j,n in matcher.get_matching_blocks()) / len(gt_data['seq'])
                if acc > max_acc:
                    max_acc = acc
                    best_match = spath
            if best_match:
                music_piece_val = gt_sequences[best_match]['music_piece']
                score_path_val = best_match

        # 6. Resolve MIDI recording device
        midi_recording_val = "None"
        if not (is_output and is_ai):
            if folder_id in midi_dict and fname in midi_dict[folder_id]:
                midi_file = midi_dict[folder_id][fname]
                if midi_file != "Missing":
                    midi_recording_val = f"SMC2024\\data\\{folder_id}\\{midi_file}"

        # 7. Code alignment flag (Tweak 4)
        align_code_val = "None" if (is_output and is_ai) else "SMC2024\\extract_interpretation.py"
        
        # Construct the row dictionary (Tweak 3 & 5 applied)
        row_dict = {
            "entry": current_entry,
            "folder_id": folder_id,
            "file_type": "output" if is_output else "input",
            "original file path": orig_file_path,
            "raw recording source": raw_source,
            "music piece": music_piece_val,
            "score path": score_path_val,
            "player ": final_player,
            "recorded time": "unknown",
            "MIDI recording": midi_recording_val,
            "which code align it": align_code_val,
            "Concurrent recordings (entry #)": ""
        }
        
        all_rows_data.append(row_dict)
        print(f"  -> [Success] Entry {current_entry} | '{fname}' processed (Player: {final_player})")
        current_entry += 1

# ==========================================
# 6. Calculate Concurrent Recordings
# ==========================================
print("\n=== Calculating Concurrent Relationships ===")
for i, row in enumerate(all_rows_data):
    current_folder = row['folder_id']
    target_type = "input" if row['file_type'] == "output" else "output"
    
    for j, other_row in enumerate(all_rows_data):
        if i != j and other_row['folder_id'] == current_folder and other_row['file_type'] == target_type:
            row["Concurrent recordings (entry #)"] = float(other_row["entry"])
            break

# ==========================================
# 7. Convert to DataFrame and Save
# ==========================================
final_list = []
for row in all_rows_data:
    final_row = [row.get(col, "") for col in columns]
    final_list.append(final_row)

df_out = pd.DataFrame(final_list, columns=columns)
if not df_out.empty:
    df_out['entry'] = df_out['entry'].astype(float) 

df_out.to_excel(OUTPUT_EXCEL_PATH, index=False)

print(f"\n======================================")
print(f"PROCESS COMPLETED!")
print(f"Total entries generated: {len(df_out)}")
print(f"Text file copies saved to: {ENTRY_DIR}")
print(f"Database Excel saved to: {OUTPUT_EXCEL_PATH}")
print(f"======================================")