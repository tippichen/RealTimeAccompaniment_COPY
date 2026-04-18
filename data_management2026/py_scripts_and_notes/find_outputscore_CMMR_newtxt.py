import os
import shutil
import ast
import difflib
from collections import Counter


def parse_input_events(file_path):
    events = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = ast.literal_eval(f.read())
            for item in data:
                if len(item) >= 6:
                    on_off = item[1]
                    velocity = item[5]
                    if velocity > 0 and on_off in (144, 1):
                        events.append({
                            'pitch': item[2],
                            'time': item[4],
                            'velocity': velocity,
                        })
                elif len(item) >= 5:
                    on_off = item[1]
                    velocity = item[3]
                    if velocity > 0 and on_off in (144, 1):
                        events.append({
                            'pitch': item[2],
                            'time': item[4],
                            'velocity': velocity,
                        })
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    return events


def parse_output_events(file_path):
    events = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = ast.literal_eval(f.read())
            for item in data:
                if len(item) >= 4:
                    on_off = item[1]
                    if on_off in (144, 1):
                        events.append({
                            'pitch': item[2],
                            'time': item[3],
                        })
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    return events


def sequence_similarity(seq1, seq2):
    if not seq1 or not seq2:
        return 0.0
    matcher = difflib.SequenceMatcher(None, seq1, seq2)
    matches = sum(block.size for block in matcher.get_matching_blocks())
    return matches / min(len(seq1), len(seq2)) * 100


def multiset_overlap_ratio(seq1, seq2):
    if not seq1 or not seq2:
        return 0.0
    c1 = Counter(seq1)
    c2 = Counter(seq2)
    intersection = sum((c1 & c2).values())
    return intersection / min(len(seq1), len(seq2)) * 100


def normalized_deltas(events):
    if len(events) < 2:
        return []
    deltas = [curr['time'] - prev['time'] for prev, curr in zip(events, events[1:])]
    total = sum(deltas)
    if total <= 0:
        return deltas
    return [d / total for d in deltas]


def compare_time_profiles(events1, events2):
    dt1 = normalized_deltas(events1)
    dt2 = normalized_deltas(events2)
    if not dt1 or not dt2:
        return 0.0
    length = min(len(dt1), len(dt2))
    diff_sum = sum(abs(dt1[i] - dt2[i]) for i in range(length))
    return max(0.0, 100.0 * (1.0 - diff_sum / length))


def calculate_composite_similarity(input_events, output_events):
    input_pitches = [e['pitch'] for e in input_events]
    output_pitches = [e['pitch'] for e in output_events]

    if not input_pitches or not output_pitches:
        return 0.0

    pitch_ratio = sequence_similarity(input_pitches, output_pitches)
    interval_ratio = sequence_similarity(
        [j - i for i, j in zip(input_pitches, input_pitches[1:])],
        [j - i for i, j in zip(output_pitches, output_pitches[1:])],
    )
    overlap_ratio = multiset_overlap_ratio(input_pitches, output_pitches)
    time_ratio = compare_time_profiles(input_events, output_events)
    length_ratio = min(len(input_pitches), len(output_pitches)) / max(len(input_pitches), len(output_pitches)) * 100

    weights = {
        'pitch': 0.45,
        'interval': 0.30,
        'overlap': 0.20,
        'time': 0.03,
        'length': 0.02,
    }

    return (
        pitch_ratio * weights['pitch'] +
        interval_ratio * weights['interval'] +
        overlap_ratio * weights['overlap'] +
        time_ratio * weights['time'] +
        length_ratio * weights['length']
    )


def main():
    base_dir = "."
    logs_dir = os.path.join(base_dir, "logs")
    cmmr_dir = os.path.join(base_dir, "CMMR2023")

    song_folders = [f for f in os.listdir(logs_dir) if os.path.isdir(os.path.join(logs_dir, f))]

    input_files = sorted(
        f for f in os.listdir(cmmr_dir)
        if f.endswith('_new.txt') and os.path.isfile(os.path.join(cmmr_dir, f))
    )

    for input_filename in input_files:
        stem = input_filename[:-4]  # strip .txt
        input_path = os.path.join(cmmr_dir, input_filename)

        input_events = parse_input_events(input_path)
        if not input_events:
            print(f"No valid events in {input_filename}, skipping.")
            continue

        best_match = None
        best_similarity = -1.0
        best_song = None

        for song in song_folders:
            output_file = os.path.join(logs_dir, song, "outputscore.txt")
            if not os.path.exists(output_file):
                continue
            output_events = parse_output_events(output_file)
            if not output_events:
                continue
            similarity = calculate_composite_similarity(input_events, output_events)
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = output_file
                best_song = song

        if best_match:
            dest_score = os.path.join(cmmr_dir, f"{stem}_outputscore.txt")
            shutil.copy2(best_match, dest_score)
            dest_guessed = os.path.join(cmmr_dir, f"{stem}_guessedscore.txt")
            with open(dest_guessed, 'w', encoding='utf-8') as f:
                f.write(f"guessed score:{best_song}\n")
                f.write(f"similarity: {best_similarity:.2f}%\n")
                f.write(f"path: logs\\{best_song}\\outputscore.txt\n")
            print(f"{input_filename}: guessed {best_song} ({best_similarity:.2f}%)")
        else:
            print(f"No match found for {input_filename}")


if __name__ == "__main__":
    main()
