import os
import ast
import difflib

# Define candidate scores for each experiment date
FOLDER_CANDIDATES = {
    '20241218': ['faure5_1', 'faure5_2'],
    '20241220': ['debussy3_1', 'debussy3_2']
}

def extract_pitches(raw_data, is_score=False):
    """Extract pitch sequence from raw MIDI or Score data."""
    events = []
    for item in raw_data:
        # MIDI input format
        if not is_score and len(item) == 4 and item[0] in (144, 1) and item[2] > 0:
            events.append({'pitch': item[1], 'time': item[3]})
        # Score format
        elif is_score and len(item) >= 4 and item[1] in (144, 1):
            events.append({'pitch': item[2], 'time': item[3]})

    # Sort events by time to ensure correct sequence
    events.sort(key=lambda x: float(x['time']))
    return [e['pitch'] for e in events]

def calculate_similarity(input_pitches, score_pitches):
    """Calculate similarity ratio between two pitch sequences."""
    if not input_pitches or not score_pitches: 
        return 0.0
    matcher = difflib.SequenceMatcher(None, input_pitches, score_pitches)
    return matcher.ratio() * 100

def main():
    # 20241217 is excluded as requested
    search_dirs = [
        'data_management2026/202412 Experiments/20241218',
        'data_management2026/202412 Experiments/20241220',
    ]
    logs_dir = "logs"
    
    print("Starting Score Identification Mode \n")
    
    for d in search_dirs:
        if not os.path.exists(d): 
            continue
        
        folder_date = os.path.basename(os.path.normpath(d))
        candidates = FOLDER_CANDIDATES.get(folder_date)
        
        if not candidates:
            continue

        print(f"Processing Folder: {folder_date}")
        
        # Pre-load candidate scores for the current folder
        score_db = {}
        for song in candidates:
            score_path = os.path.join(logs_dir, song, "outputscore.txt")
            if os.path.exists(score_path):
                with open(score_path, 'r', encoding='utf-8') as f:
                    raw_score = list(ast.literal_eval(f.read().strip()))
                score_db[song] = {
                    'pitches': extract_pitches(raw_score, is_score=True) 
                }

        # Process input logs in the directory
        target_files = [f for f in os.listdir(d) if f.startswith('inputmslog') and f.endswith('.txt')]

        for fname in target_files:
            input_path = os.path.join(d, fname)
            try:
                with open(input_path, 'r', encoding='utf-8') as f:
                    raw_midi = list(ast.literal_eval(f.read().strip()))
            except Exception as e:
                print(f"  Error reading {fname}: {e}")
                continue
                
            input_pitches = extract_pitches(raw_midi, is_score=False)
            if not input_pitches: 
                print(f"  {fname}: No valid MIDI pitches found.")
                continue

            best_match = None
            max_sim = -1.0

            # Compare input against each candidate
            for song_name, score_data in score_db.items():
                sim = calculate_similarity(input_pitches, score_data['pitches'])
                if sim > max_sim:
                    max_sim = sim
                    best_match = song_name

            # Output only the identification result
            if best_match:
                print(f"  {fname} -> Identified as: {best_match} ({max_sim:.2f}%)")
        print()

if __name__ == '__main__':
    main()