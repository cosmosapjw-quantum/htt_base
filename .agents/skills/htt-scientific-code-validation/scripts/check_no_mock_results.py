#!/usr/bin/env python3
from __future__ import annotations
import re, sys
from pathlib import Path
ROOT=Path.cwd()
EXCLUDE={'.git','.venv','venv','__pycache__','node_modules','dist','build','.mypy_cache','.pytest_cache','.agents'}
ALLOW={'DIAGNOSTIC_ONLY','SMOKE','mock calibration','null mock','mock_calibration','test_no_mock_results.py','check_no_mock_results.py'}
PATS=[r'fake[_ -]?validation',r'mock[_ -]?result',r'toy[_ -]?result',r'calibration[_ -]?factor',r'TODO.*validated',r'dummy.*benchmark',r'smoke.*publication']
SUFFIX={'.py','.rs','.md','.tex','.yaml','.yml','.toml','.json','.sh'}
regs=[re.compile(p,re.I) for p in PATS]
hits=[]
for p in ROOT.rglob('*'):
    if not p.is_file() or p.suffix.lower() not in SUFFIX: continue
    if any(part in EXCLUDE for part in p.parts): continue
    txt=p.read_text(errors='ignore')
    for i,line in enumerate(txt.splitlines(),1):
        if any(a in line for a in ALLOW): continue
        if any(r.search(line) for r in regs): hits.append((p,i,line.strip()))
if hits:
    print('Suspicious mock/fake validation markers:')
    for h in hits: print(f'{h[0]}:{h[1]}: {h[2]}')
    sys.exit(1)
print('No suspicious mock/fake validation markers found.')
