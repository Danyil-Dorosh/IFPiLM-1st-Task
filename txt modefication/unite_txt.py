import os
import re
from pathlib import Path

# Directory containing the test files
input_dir = Path(r"d:\ℱ Sci\IFPiLM\1st task\data\test\full")
output_file = input_dir / "united.txt"

# Find all test_full_*.txt files and sort by frame number
files = sorted(input_dir.glob("test_full_*.txt"), 
               key=lambda x: int(re.search(r'(\d+)', x.name).group(1)))

print(f"Found {len(files)} frame files")

# Merge into one file with frame markers
with open(output_file, 'w') as outf:
    for i, file in enumerate(files, 1):
        frame_num = re.search(r'(\d+)', file.name).group(1)
        
        # Read the file
        with open(file, 'r') as inf:
            lines = inf.readlines()
        
        # Remove last 2 rows (trash timestamp and empty row)
        if len(lines) >= 2:
            lines = lines[:-2]
        
        # Write frame marker
        outf.write(f"{frame_num}-\n")
        
        # Write cleaned data (remove first column)
        for line in lines:
            # Remove leading channel number (1-4 digits + space)
            modified_line = re.sub(r'^[\s]*\d{1,4}\s+', '', line)
            
            # Also remove "Channel " text if present
            modified_line = modified_line.replace("Channel ", "")
            
            outf.write(modified_line)
        
        if i % 50 == 0:
            print(f"Processed {i} frames...")

print(f"Merged into: {output_file}")
print(f"Total frames: {len(files)}")
