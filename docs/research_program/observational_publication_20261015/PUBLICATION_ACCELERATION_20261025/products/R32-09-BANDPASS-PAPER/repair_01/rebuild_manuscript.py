"""Rebuild only the repaired manuscript using unchanged included numerical assets."""
from pathlib import Path
import subprocess
root=Path(__file__).resolve().parent
subprocess.run(['latexmk','-pdf','-interaction=nonstopmode','-halt-on-error','-cd','report/main.tex'],cwd=root,check=True)
