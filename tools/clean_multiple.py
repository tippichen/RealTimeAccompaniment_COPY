#!/usr/bin/env python3
"""Clean multiple files in-place by converting list-of-dicts to list-of-lists.
Usage: python tools\clean_multiple.py <file1> <file2> ...
Each file is parsed as a Python literal (list of dicts). Output overwrites the input file.
Fields order: [index, on_off, note#, score_pos, time, vel]
Non-numeric on_off or None time/vel -> 0
"""
import ast
import sys
from pathlib import Path

def to_number(x):
    try:
        if x is None:
            return 0
        if isinstance(x, (int, float)):
            return x
        # numeric string?
        sx = str(x)
        if sx.isdigit():
            return int(sx)
        try:
            return float(sx)
        except:
            return 0
    except:
        return 0

if len(sys.argv) < 2:
    print("Usage: python tools\\clean_multiple.py <file1> <file2> ...")
    sys.exit(1)

for p in sys.argv[1:]:
    path = Path(p)
    if not path.exists():
        print(f"Skipping missing: {path}")
        continue
    s = path.read_text(encoding='utf-8')
    try:
        data = ast.literal_eval(s)
    except Exception as e:
        print(f"Failed to parse {path}: {e}")
        continue
    clean = []
    for d in data:
        idx = to_number(d.get('index'))
        onoff = to_number(d.get('on_off'))
        note = to_number(d.get('note#'))
        pos = to_number(d.get('score_pos'))
        time = to_number(d.get('time'))
        vel = to_number(d.get('vel'))
        clean.append([idx, onoff, note, pos, time, vel])
    path.write_text(repr(clean), encoding='utf-8')
    print('WROTE', path)
