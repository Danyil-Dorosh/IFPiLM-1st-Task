# Original .txt File Structure (Reference)

## test_<number of a frame>.txt - PHA system measurement during 1 frame

Text file consists of 9 columns and 2050 rows

### Column Descriptions:
- **Column 1 (Channel)**: Useless
- **Column 2 (E1[eV])**: The energy of photon, detected by 1st energy channel
- **Column 3 (Events1)**: Amount of photons of corresponding energy detected by 1st energy channel during 1 (current) frame
- **Column 4 (E2[eV])**: The energy of photon, detected by 2nd energy channel
- **Column 5 (Events2)**: Amount of photons of corresponding energy detected by 2nd energy channel during 1 (current) frame
- **Column 6 (E3[eV])**: The energy of photon, detected by 3rd energy channel (not used for calculations)
- **Column 7 (Events3)**: Amount of photons of corresponding energy detected by 3rd energy channel during 1 (current) frame (not used)
- **Column 8 (E4[eV])**: Useless
- **Column 9 (Events4)**: Useless

### File Structure:
- Series of test_<frame_number>.txt files (each representing 1 frame)
- 2050 rows per file (1 header + 2049 data rows including trash footer)
