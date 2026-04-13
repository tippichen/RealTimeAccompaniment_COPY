#!/usr/bin/env python3
"""
Clean in.txt by converting list-of-dicts to list-of-lists with numeric fields only.
Output: in_clean.txt (same directory as in.txt)
Fields order: [index, on_off, note#, score_pos, time, vel]
None values are converted to 0.
"""
import ast
from pathlib import Path

in_path = Path(r"C:\Users\tippi\SynologyDrive\Tsing_Hua\third_grade\project\RealTimeAccompaniment_COPY.worktrees\copilot-worktree-2026-04-13T17-02-15\202412 Experiments\20241217\in.txt")
out_path = in_path.with_name("in_clean.txt")

s = in_path.read_text(encoding="utf-8")
try:
    data = ast.literal_eval(s)
except Exception as e:
    raise SystemExit(f"Failed to parse input file as Python literal: {e}")

clean = []
for d in data:
    idx = d.get('index')
    onoff = d.get('on_off')
    note = d.get('note#')
    pos = d.get('score_pos')
    time = d.get('time') if d.get('time') is not None else 0
    vel = d.get('vel') if d.get('vel') is not None else 0
    clean.append([idx, onoff, note, pos, time, vel])

out_path.write_text(repr(clean), encoding="utf-8")
print("WROTE", out_path)
