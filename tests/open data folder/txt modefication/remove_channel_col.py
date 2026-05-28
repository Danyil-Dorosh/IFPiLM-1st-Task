import re
from pathlib import Path

input_file = Path(r"d:\ℱ Sci\IFPiLM\1st task\data\test\full\full.txt")
output_file = Path(r"d:\ℱ Sci\IFPiLM\1st task\data\test\full\full_no_channel.txt")

with open(input_file, 'r') as f:
    lines = f.readlines()

output_lines = []
frame_header_count = 0

for i, line in enumerate(lines, 1):
    # Check if this is a frame marker line (e.g., "1-")
    if re.match(r'^\d+-\n?$', line.strip() + '\n'):
        output_lines.append(line)
        frame_header_count += 1
        continue
    
    # Check if this is a data row (not frame marker)
    # Remove leading channel number (1-4 digits + space)
    modified_line = re.sub(r'^[\s]*\d{1,4}\s+', '', line)
    
    # Also remove "Channel " text if present
    modified_line = modified_line.replace("Channel ", "")
    
    output_lines.append(modified_line)

with open(output_file, 'w') as f:
    f.writelines(output_lines)

print(f"Processed {len(lines)} lines")
print(f"Output saved to: {output_file}")
