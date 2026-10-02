#!/usr/bin/python3
"""Frozen entrypoint for the independent SymPy component checks."""
from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).with_name('check.py')), run_name='__main__')
