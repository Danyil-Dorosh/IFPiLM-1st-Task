"""Centralized path configuration for all test data and output files.

NOTE: PROJECT_ROOT is hardcoded to avoid relying on file location.
"""
from pathlib import Path

# Project root (HARDCODED - won't change with script location)
PROJECT_ROOT = Path("D:/ℱ Sci/IFPiLM/1st task")

# File registry (data files your scripts work with)
DATA_FILES = {
    "united": PROJECT_ROOT / "data" / "test" / "modified" / "unitedc_62_239.txt",
    # Add more files as needed:
    # "other_file": PROJECT_ROOT / "data" / "other" / "filename.txt",
}

# Output directories
OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_DIR.mkdir(exist_ok=True)