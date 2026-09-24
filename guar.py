#!/usr/bin/env python3
"""
guar.py - Trình khởi chạy đa nền tảng (Universal Cross-Platform Launcher)
Hỗ trợ chạy trực tiếp trên mọi hệ điều hành: Windows, macOS, Linux.
Ví dụ:
    python guar.py active
    python guar.py status
    python guar.py watch
"""
import sys
import runpy
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
jog_script = BASE_DIR / "bin" / "jog"

if __name__ == "__main__":
    runpy.run_path(str(jog_script), run_name="__main__")
