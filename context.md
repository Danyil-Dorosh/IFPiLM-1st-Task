# Context for pha_lib

This file collects the domain background for the library: the physical meaning of the data, the vocabulary used in the task, and the assumptions that matter when analyzing the current test input.

## Domain dictionary

- Discharge: one experimental run, i.e. one session that contains a series of injections.
- Injection: a cleaning/injection event in the stellarator. The signal from impurity radiation rises, then decays.
- Frame: one time window of measurement, about 50 ms in the current data.
- PHA / PHE: pulse-height analysis / pulse-height events. The detector measures photon counts as a function of energy.
- Channel: one energy-detection path of the PHA system. In the current test data there are 2 usable channels.
- Line energy: the target photon energy range being analyzed. For the current task this is 6660 eV.

## Physical meaning

The experiment studies impurity injection and subsequent self-cleaning of the plasma in W7-X. During an injection, impurities are injected into the stellarator, emit X-ray photons, and then decay as the plasma cleans itself. The goal of the analysis is to estimate how quickly that emission falls off after each injection.

The expected per-injection shape is an exponential decay:

$$
y(t) = A \cdot \exp\left(-(t - t_0)/\tau\right) + C
$$

where:

- $y(t)$ is the number of detected photons in a frame or time window,
- $A$ is the amplitude of the injection signal,
- $t_0$ is the start time / start frame of the decay,
- $\tau$ is the decay time,
- $C$ is the background level.

The line at 6660 eV is treated as the working spectral window for the current development stage. The real signal can shift slightly left/right and can be broadened by Doppler effects, so a small energy window around 6660 eV is used instead of a single bin.

## Current input format

The test artifact is the united text file `unitedc_62_239.txt`.

- It contains frames 62 to 239 from one test discharge.
- Each frame is separated by a line like `62-`, `63-`, etc.
- The file is already preprocessed for development convenience.
- Columns for unused channels and some structural columns have already been removed.

This is a temporary training/testing format, not the final production format. The long-term target is either:

- individual `test_<frame_number>.txt` files, or
- a binary `.pha` file containing all frames of one discharge.

## Testing dataset (training artifact)

The project includes a temporary, pre-processed training file used for development and smoke tests. Details:

- Filename: `unitedc_62_239.txt`
- Frames included: 62..239 (178 frames total)
- Frame marker: each frame begins with a line like `62-`, `63-`, etc.
- Rows per frame (after trimming): ~2048 data rows (header/footer removed for convenience)
- Columns (training format): `E1[eV], Events1, E2[eV], Events2` (four columns — two channels)
- This file is a safety artifact for fast iteration. Production inputs will be either individual `test_<frame_number>.txt` files or binary `.pha` files with full original column layouts.

Use this file only for local development and tests; keep production parsers compatible with the original file structure described in `txt_structure_original.md`.

## Analysis assumptions for the current task

1. Analyze only the 6660 eV window during testing.
2. Detect the start and finish frames of each injection in a discharge.
3. Fit the photon-count decay for each injection with the exponential model above.
4. Keep the code modular so the same library can later support `.pha`, other energies, and more channels.

## Output meaning

The requested output is two dataframes, one per energy channel, saved in Parquet.

Each row corresponds to one injection and should contain:

- injection number,
- discharge energy,
- start frame,
- finish frame,
- fit coefficients in frame units,
- fit coefficients converted to physical units.

The library is expected to remain extensible, so these results should be produced by small independent modules rather than a single monolithic script.
