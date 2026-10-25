"""Recreate paper assets from included sufficient statistics; no upstream solve."""
import json
from pathlib import Path
import subprocess
import sys

root=Path(__file__).resolve().parent
bindings=json.loads((root/'SOURCE_BINDINGS.json').read_text())
commands=[
 [sys.executable,'consumer.py','--qualified-dir','data',
  '--expected-result-sha256',bindings['bounded_RESULT.json']['sha256'],
  '--expected-r31-sha256',bindings['R31_RESULT.json']['sha256'],
  '--output-dir','report/generated'],
 [sys.executable,'-m','pytest','-q','-o','addopts=','test_consumer.py','test_publication.py'],
 [sys.executable,'publication.py'],
 ['latexmk','-pdf','-interaction=nonstopmode','-halt-on-error','-cd','report/main.tex'],
]
for command in commands:
    print(command,flush=True)
    subprocess.run(command,cwd=root,check=True)
