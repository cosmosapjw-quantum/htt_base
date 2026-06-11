#!/usr/bin/env python3
from __future__ import annotations
import re, sys
from pathlib import Path
ROOT=Path.cwd()
EXCLUDE={'.git','.venv','venv','__pycache__','node_modules','dist','build','.agents'}
SUFFIX={'.md','.tex','.rst'}
STRONG=[r'\bwe prove\b',r'\bwe demonstrate\b',r'\bvalidated\b',r'\bproduction[- ]ready\b',r'\bexact\b',r'\bguarantee\b',r'\bfully implemented\b',r'\bsubmission[- ]ready\b',r'\bfamily identification\b',r'\bBianchi geometry detected\b']
STATUS=['IMPLEMENTED','SMOKE_TESTED','VALIDATED','DERIVED','SPECIFIED','CONDITIONAL','DIAGNOSTIC_ONLY','PROPOSED','SPECULATIVE','DEPRECATED','FORBIDDEN','C0','C1','C2','C3','C4','C5','C6']
regs=[re.compile(p,re.I) for p in STRONG]
hits=[]
for p in ROOT.rglob('*'):
    if not p.is_file() or p.suffix.lower() not in SUFFIX: continue
    if any(part in EXCLUDE for part in p.parts): continue
    lines=p.read_text(errors='ignore').splitlines()
    for i,line in enumerate(lines):
        if any(r.search(line) for r in regs):
            win='\n'.join(lines[max(0,i-3):min(len(lines),i+4)])
            if not any(s in win for s in STATUS): hits.append((p,i+1,line.strip()))
if hits:
    print('Strong claims without nearby status markers:')
    for p,i,l in hits: print(f'{p}:{i}: {l}')
    sys.exit(1)
print('No unmarked strong claims detected.')
