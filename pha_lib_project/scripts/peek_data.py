"""Quick exploratory look at unitedc_62_239.txt.

Goal: dla każdej ramki policz sumę Events1 i Events2 w oknie 6660 eV +/- 50 eV
i zobacz, kiedy są skoki — to nam pokaże, ile jest discharges w tym shocie.
"""
from pathlib import Path
import numpy as np

INPUT = Path("/home/user/workspace/unitedc_62_239.txt")

# Energy window of interest
E_CENTER = 6660.0
E_HALF = 50.0  # +- 50 eV around 6660 eV

frames = {}  # frame_no -> (E1, Ev1, E2, Ev2) arrays
current_frame = None
current_rows = []

with INPUT.open() as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        # frame marker like "62-"
        if line.endswith("-") and line[:-1].isdigit():
            if current_frame is not None:
                frames[current_frame] = np.array(current_rows, dtype=float)
            current_frame = int(line[:-1])
            current_rows = []
            continue
        # header line
        if line.startswith("E1"):
            continue
        parts = line.split()
        if len(parts) != 4:
            continue
        try:
            current_rows.append([float(p) for p in parts])
        except ValueError:
            continue

# flush last frame
if current_frame is not None:
    frames[current_frame] = np.array(current_rows, dtype=float)

print(f"Parsed {len(frames)} frames")
sample_no = sorted(frames.keys())[0]
sample = frames[sample_no]
print(f"Sample frame {sample_no}: shape {sample.shape}")
print(f"E1 range: {sample[:,0].min()} - {sample[:,0].max()} eV (step ~{sample[1,0]-sample[0,0]} eV)")

# For each frame, count events in 6660 +- 50 eV window for both channels
records = []
for fn in sorted(frames.keys()):
    a = frames[fn]
    E1, Ev1, E2, Ev2 = a[:,0], a[:,1], a[:,2], a[:,3]
    m1 = (E1 >= E_CENTER - E_HALF) & (E1 <= E_CENTER + E_HALF)
    m2 = (E2 >= E_CENTER - E_HALF) & (E2 <= E_CENTER + E_HALF)
    records.append((fn, int(Ev1[m1].sum()), int(Ev2[m2].sum())))

import csv
with open("/home/user/workspace/pha_lib_project/output/window_6660_per_frame.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["frame", "events1_window", "events2_window"])
    w.writerows(records)

# Show top 30 frames by events1+events2 (so we can see jumps)
arr = np.array(records, dtype=int)
print("\nTop 30 frames by Ev1+Ev2 in 6660 +/- 50 eV window:")
order = np.argsort(-(arr[:,1] + arr[:,2]))
for idx in order[:30]:
    print(f"  frame {arr[idx,0]:4d}  Ev1={arr[idx,1]:5d}  Ev2={arr[idx,2]:5d}  total={arr[idx,1]+arr[idx,2]:5d}")

print("\nFirst 20 frames:")
for r in records[:20]:
    print(f"  frame {r[0]:4d}  Ev1={r[1]:5d}  Ev2={r[2]:5d}")

print("\nFull histogram (compressed) — frames where total >= 50:")
for r in records:
    if r[1] + r[2] >= 50:
        print(f"  frame {r[0]:4d}  Ev1={r[1]:5d}  Ev2={r[2]:5d}")
