import os
import ast
from pathlib import Path
from collections import defaultdict


def parse_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return ast.literal_eval(f.read())


def normalize_input_events(input_data):
    """
    Handle both formats:
    - 5-element [idx, status, note, velocity, time]: sec*-style, 144+vel=0 = note-off
    - 6-element [idx, on_off, note, position, time, velocity]: *_new.txt style, already normalized
    """
    result = []
    for event in input_data:
        if len(event) >= 6:
            _, status, note, _, time, velocity = event
        else:
            _, status, note, velocity, time = event
            if status == 144 and velocity == 0:
                status = 128
        result.append((status, note, velocity, time))
    return result


def align_to_score(score_events, input_events):
    """
    score_events : list of [idx, on_off, note, position]
    input_events : list of performance events (5- or 6-element)
    Returns      : list of [out_idx, on_off, note, position, time, velocity]
    """
    normalized = normalize_input_events(input_events)

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
            velocity, time = None, None

        result.append([out_idx, s_status, s_note, s_pos, time, velocity])

    return result


def main():
    cmmr_dir = Path(__file__).parent / 'CMMR2023'

    input_files = sorted(
        f for f in os.listdir(cmmr_dir)
        if f.endswith('_new.txt')
        and not any(f.endswith(s) for s in ('_outputscore.txt', '_guessedscore.txt', '_inputinterpretation.txt'))
        and os.path.isfile(cmmr_dir / f)
    )

    success = 0
    total = 0

    for input_filename in input_files:
        stem = input_filename[:-4]  # strip .txt
        input_path = cmmr_dir / input_filename
        score_path = cmmr_dir / f"{stem}_outputscore.txt"
        output_path = cmmr_dir / f"{stem}_inputinterpretation.txt"

        if not score_path.exists():
            print(f"  SKIP {input_filename}: {score_path.name} not found")
            continue

        total += 1
        try:
            input_data = parse_file(input_path)
            score_data = parse_file(score_path)

            interpretation = align_to_score(score_data, input_data)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(str(interpretation))

            matched = sum(1 for e in interpretation if e[4] is not None)
            print(f"  {input_filename}: {matched}/{len(interpretation)} events matched")
            success += 1

        except Exception as e:
            print(f"  ERROR {input_filename}: {e}")

    print(f"\nDone: {success}/{total} files processed successfully")


if __name__ == '__main__':
    main()
