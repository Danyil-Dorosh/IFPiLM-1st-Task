# global_stats

global_stats is an analysis layer for fast statistics over the full dataset, not just one discharge or one notebook run.

The goal is to answer high-level questions quickly:
- What is typical behavior across all discharges?
- How often do rare patterns happen?
- How does distribution change by channel, threshold, or filter?

This package is designed for scale:
- Works on many files and many discharges in one pass
- Reuses existing domain objects and detection outputs
- Produces compact summary tables that are easy to plot or export