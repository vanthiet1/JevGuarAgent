#!/usr/bin/env python3
import sys
import runpy
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
jog_script = BASE_DIR / "bin" / "jog"

if __name__ == "__main__":
    runpy.run_path(str(jog_script), run_name="__main__")
