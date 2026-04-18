
import os
import ast
from pathlib import Path
from collections import defaultdict


def parse_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return ast.literal_eval(f.read())


def normalize_input_events(input_data):
    """Normalize inputmsglog: status=144 + velocity=0 means note-off -> convert to status=128."""
    result = []
    for event in input_data:
        idx, status, note, velocity, time = event
        if status == 144 and velocity == 0:
            status = 128
        result.append((status, note, velocity, time))
    return result


def align_to_score(score_events, input_events):
    """
    Align input performance events to score events using FIFO matching by (on_off, note).

    For each score event, find the earliest unmatched input event with the same
    (on_off, note) pair. This handles simultaneous note reordering while preserving
    the overall sequential structure of the performance.

    score_events : list of [idx, on_off, note, position]
    input_events : list of [idx, status, note, velocity, time]
    Returns      : list of [out_idx, on_off, note, position, time, velocity]
    """
    normalized = normalize_input_events(input_events)

    # Build FIFO queues keyed by (on_off, note)
    queues = defaultdict(list)
    for status, note, velocity, time in normalized:
        queues[(status, note)].append((velocity, time))

    result = []
    for out_idx, score_event in enumerate(score_events):
        _, s_status, s_note, s_pos = score_event
        key = (s_status, s_note)

        if queues[key]:
            velocity, time = queues[key].pop(0)
        else:
            # Performer missed this note
            velocity, time = None, None

        result.append([out_idx, s_status, s_note, s_pos, time, velocity])

    return result


def process_folder(folder_path):
    input_file = folder_path / 'inputmsglog.txt'
    score_file = folder_path / 'outputscore.txt'
    output_file = folder_path / 'inputinterpretation.txt'

    if not input_file.exists() or not score_file.exists():
        return False

    try:
        input_data = parse_file(input_file)
        score_data = parse_file(score_file)

        interpretation = align_to_score(score_data, input_data)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(str(interpretation))

        matched = sum(1 for e in interpretation if e[4] is not None)
        print(f"  {folder_path.name}: {matched}/{len(interpretation)} events matched")
        return True

    except Exception as e:
        print(f"  ERROR {folder_path.name}: {e}")
        return False


def main():
    logs_dir = Path(__file__).parent
    print(f"Processing logs in: {logs_dir}\n")

    success = 0
    total = 0

    for root, dirs, files in os.walk(logs_dir):
        # Skip the 'old' subdirectory
        if 'old' in dirs:
            dirs.remove('old')

        folder = Path(root)
        if folder == logs_dir:
            continue

        if 'inputmsglog.txt' in files and 'outputscore.txt' in files:
            total += 1
            if process_folder(folder):
                success += 1

    print(f"\nDone: {success}/{total} folders processed successfully")


if __name__ == '__main__':
    main()
