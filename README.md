# IFPiLM - 1st Task

This repository contains the main analysis work for the first IFPiLM task: data handling, fitting workflows, exploratory notebooks, and output artifacts.

The top-level README only gives general orientation. Each major folder should document its own details in a local README where appropriate.

## Repository structure

- `pha_lib/` - core library code used by the project. This package contains the main data models, IO helpers, fitting routines, pipeline logic, export helpers, and plotting utilities. It should stay stable and is expected to change rarely.
- `adaptive points/` - experiments and scripts for adaptive point selection.
- `data/` - source and test input data.
- `output/` - generated CSV, parquet, and plot outputs.
- `scripts/` - small runnable utilities and demos.
- `tests/` - automated checks for the library and analysis flow.
- `AI/` - context and background notes for AI-assisted work, including physics context.
- `archive/` - older prompts, notes, and superseded project materials kept for reference.
- `research/` - research outputs and exploratory work outside the stable library layer.
- `support-tools/` - external reference files and helper materials kept alongside the project.

## Notes

- Use folder-level READMEs for implementation details, conventions, and local usage notes.
- Treat `pha_lib/` as the primary reusable codebase.
- Keep exploratory work, temporary analysis, and dataset-specific notes outside `pha_lib/` when possible.


philosophy that i try using as much notebooks as possible cause they much more way flexible then python+images in some dirs