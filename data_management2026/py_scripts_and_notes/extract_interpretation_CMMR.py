import os
import ast
from pathlib import Path


def parse_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return ast.literal_eval(f.read())


def build_time_map(input_interp):
    """Collect (position, time) pairs from matched note-on events, sorted by position."""
    pairs = []
    for event in input_interp:
        on_off, position, time = event[1], event[3], event[4]
        if on_off == 144 and time is not None:
            pairs.append((position, time))
    pairs.sort()
    return pairs


def interpolate_time(position, time_map):
    """Piecewise-linear interpolation/extrapolation of time at a given score position."""
    if not time_map:
        return None
    if len(time_map) == 1:
        return time_map[0][1]

    positions = [p for p, _ in time_map]

    if position <= positions[0]:
        (p0, t0), (p1, t1) = time_map[0], time_map[1]
        slope = (t1 - t0) / (p1 - p0) if p1 != p0 else 0.0
        return t0 + slope * (position - p0)

    if position >= positions[-1]:
        (p0, t0), (p1, t1) = time_map[-2], time_map[-1]
        slope = (t1 - t0) / (p1 - p0) if p1 != p0 else 0.0
        return t1 + slope * (position - p1)

    for i in range(len(time_map) - 1):
        p0, t0 = time_map[i]
        p1, t1 = time_map[i + 1]
        if p0 <= position <= p1:
            if p1 == p0:
                return (t0 + t1) / 2
            return t0 + (t1 - t0) * (position - p0) / (p1 - p0)

    return None


def estimate_velocity(position, input_interp, window=2.0):
    """Average velocity of nearby matched note-on events within window beats."""
    vels = [e[5] for e in input_interp
            if e[1] == 144 and e[5] is not None and abs(e[3] - position) <= window]
    if vels:
        return int(round(sum(vels) / len(vels)))
    all_vels = [e[5] for e in input_interp if e[1] == 144 and e[5] is not None]
    return int(round(sum(all_vels) / len(all_vels))) if all_vels else 64


def generate_output_interpretation(input_interp, output_score):
    time_map = build_time_map(input_interp)
    result = []
    for event in output_score:
        idx, on_off, note, position = event
        time = interpolate_time(position, time_map)
        velocity = estimate_velocity(position, input_interp) if on_off == 144 else 0
        result.append([idx, on_off, note, position, time, velocity])
    return result


def process_folder(folder_path):
    input_file = folder_path / 'inputinterpretation.txt'
    score_file = folder_path / 'outputscore.txt'
    output_file = folder_path / 'outputinterpretation.txt'

    if not input_file.exists() or not score_file.exists():
        return False

    try:
        input_interp = parse_file(input_file)
        output_score = parse_file(score_file)

        output_interp = generate_output_interpretation(input_interp, output_score)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(str(output_interp))

        timed = sum(1 for e in output_interp if e[4] is not None)
        print(f"  {folder_path.name}: {timed}/{len(output_interp)} events timed")
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
        if 'old' in dirs:
            dirs.remove('old')

        folder = Path(root)
        if folder == logs_dir:
            continue

        if 'inputinterpretation.txt' in files and 'outputscore.txt' in files:
            total += 1
            if process_folder(folder):
                success += 1

    print(f"\nDone: {success}/{total} folders processed successfully")


if __name__ == '__main__':
    main()
