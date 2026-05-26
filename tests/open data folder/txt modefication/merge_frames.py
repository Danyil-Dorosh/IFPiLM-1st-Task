import os
import re
from pathlib import Path

# Directory containing the test files
input_dir = Path(r"d:\ℱ Sci\IFPiLM\1st task\data\test\full")
output_file = input_dir / "merged_frames.txt"

# Find all test_full_*.txt files and sort by frame number
files = sorted(input_dir.glob("test_full_*.txt"), 
               key=lambda x: int(re.search(r'(\d+)', x.name).group(1)))

print(f"Found {len(files)} frame files")

# Merge into one file with frame markers
with open(output_file, 'w') as outf:
    for i, file in enumerate(files, 1):
        frame_num = re.search(r'(\d+)', file.name).group(1)
        
        # Write frame header
        outf.write(f"{frame_num}-\n")
        
        # Write file content
        with open(file, 'r') as inf:
            outf.write(inf.read())
        
        if i % 50 == 0:
            print(f"Processed {i} frames...")

print(f"Merged into: {output_file}")
print(f"Total frames: {len(files)}")
