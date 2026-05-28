# Context (uploaded) data:
- [1], [2], [3] - articles about the stellator and PHA system
- unitedc_62_239.txt - united frames (from 62 to 239) of 1 test shot (frames are separated by "<frame's number>-") (although it is cut - it represents the usual data well)
- test_101.txt - Example of .txt file of PHE measurement of test shot during 101-st frame


# Slang:
- Shot - series of discharges
- Discharge - action of injecting & cleaning inpurities in stellator
- frame - window of time for measurements (~50 ms)


# Structure


# Physical context:
During the experiment the stellarator is injected with impurities and then
cleans itself. The goal is to measure the effectiveness of the cleaning.
The PHA system (3 energy channels) performs spectroscopy. The detected
photon counts during a cleaning event should follow the model
y(t) = A*exp(-(t-t_0)/tau) + C, where

y(t) = detected photon counts (events)
A, C, t_0 = parameters to estimate (in frames or seconds)


# Input data (FOR TRAINING/TESTING):
**Current input:** `unitedc_62_239.txt` - United and pre-processed data file
- Contains frames 62 to 239 (178 frames total)
- Unified format with frame markers: each frame begins with a line like "62-", "63-", etc.
- Each frame has 2048 data rows (header row removed, trash footer rows removed)
- 4 columns per row: E1[eV], Events1, E2[eV], Events2
- Already processed: Channel column removed, E3/E4 columns removed


**Note on modifications:**
- See `txt_structure_original.md` for reference of the original unmodified .txt file structure


# Input comment:
## Final input format vs. training setup


**Final production input** (not yet implemented):
- Will be binary `.pha` file (includes all frames of 1 shot)
- OR series of individual `test_<frame_number>.txt` files (as originally described)
- Each file: 9 columns, ~2050 rows per frame


**Current training/testing input** (safety wheels):
For safety and faster iteration during development, the input has been pre-processed:
1. **Rows removed:** Trash footer rows (timestamp + empty row) removed from each frame
2. **Frames cut:** Only frames 62-239 included (178 frames instead of 532)
3. **Columns removed:** Channel column (useless), E3[eV], Events3, E4[eV], Events4 (not used)
4. **Unified format:** All frames merged into single `unitedc_62_239.txt` file for convenience


**Important:** This united text file is a **temporary training artifact**, not the final operational format.
Once validated, the actual program will operate on:
- Individual `.txt` or `.pha` files
- Full frame sets
- Original column structure



# Task (and physical nuances)
1. (testing stage) only the 6660 eV window is analyzed.
	The line may shift slightly and be broadened by Doppler effects, so
	we use a small energy window around 6660 eV.
2. Determine start and finish frames of injections in a shot (there may be zero or multiple).
	a) Typically the first 3 frames of an injection are sufficient for fitting.
		- This is a practical minimum; beyond ~3 frames background usually
		  dominates.
	b) An injection starts when the 6660 eV trace experiences a large jump.
	c) The second frame after the start is usually a good choice for t_0
		(the first frame may not capture the peak due to discrete sampling).
		Depending on the case, 1..4 points may be appropriate — this is
		configurable and visible in plots.
3. Fit amount of events (a one frame) to y(t) = A*exp(-(t-t_0)/tau) + C - where
y(t) - amount of detected photons (Events№)
C, A, t_0 (both in frames or time-scale) - coefficients which are to detect
4. We are writting LIBRARY. Although the main usage will be getting the coeficients, in future it will be, probably, developed in othe rdirections - so be sure to write it modular-ly, as it would be the library (with 1 more-developed direction, though)


# Output data:
2 dataframes (for energy channel 1 & 2):
Column 0 (discharge_№):
Column 1 (discharge_E):
Column 2 (start_frame):
Column 3 (finish_frame):
Column 4 (A_f):
Column 5 (t_0_f):
Column 6 (tau_f):
Column 7 (C):
Column 8 (A):
Column 9 (t_0):
Column 10 (tau):
Column 11 (C):


Save it in Parquet