from pathlib import Path

input_file = Path(r"d:\ℱ Sci\IFPiLM\1st task\data\test\full\unitedc.txt")
output_file = Path(r"d:\ℱ Sci\IFPiLM\1st task\data\test\full\unitedc_62_239.txt")

start_frame = 62
end_frame = 239

# Each frame has: 1 marker line + 2048 data rows = 2049 lines total
# Frame n starts at line: 1 + (n-1)*2049
# Frame n ends at line: n*2049

start_line = 1 + (start_frame - 1) * 2049  # Line where frame 62 marker is
end_line = end_frame * 2049                 # Line where frame 239 ends

print(f"Extracting frames {start_frame} to {end_frame}")
print(f"Lines {start_line} to {end_line}")

with open(input_file, 'r') as f_in:
    with open(output_file, 'w') as f_out:
        for line_num, line in enumerate(f_in, 1):
            if start_line <= line_num <= end_line:
                f_out.write(line)
            elif line_num > end_line:
                break

print(f"Output saved to: {output_file}")