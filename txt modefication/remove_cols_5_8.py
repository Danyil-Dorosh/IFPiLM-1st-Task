import re
from pathlib import Path

input_file = Path(r"d:\ℱ Sci\IFPiLM\1st task\data\test\full\united.txt")
output_file = Path(r"d:\ℱ Sci\IFPiLM\1st task\data\test\full\unitedc.txt")

with open(input_file, 'r') as f:
    lines = f.readlines()

output_lines = []

for line in lines:
    # Check if this is a frame marker line (e.g., "1-")
    if re.match(r'^\d+-\n?$', line.strip() + '\n'):
        output_lines.append(line)
        continue
    
    # Check if line is empty or just whitespace
    if not line.strip():
        output_lines.append(line)
        continue
    
    # For data rows: split by whitespace, keep first 4 columns, rejoin
    parts = line.split()
    
    # Keep only first 4 columns (E1, Events1, E2, Events2)
    if len(parts) >= 4:
        kept_parts = parts[:4]
        modified_line = ' '.join(kept_parts) + '\n'
        output_lines.append(modified_line)
    else:
        # If line has fewer than 4 parts, keep as is
        output_lines.append(line)

with open(output_file, 'w') as f:
    f.writelines(output_lines)

print(f"Processed {len(lines)} lines")
print(f"Removed columns 5-8 (E3[eV], Events3, E4[eV], Events4)")
print(f"Output saved to: {output_file}")
