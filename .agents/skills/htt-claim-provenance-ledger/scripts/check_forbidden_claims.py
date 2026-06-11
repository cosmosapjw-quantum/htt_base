#!/usr/bin/env python3
from __future__ import annotations
import re, sys
from pathlib import Path
ROOT=Path.cwd()
EXCLUDE={'.git','.venv','__pycache__','.agents'}
PATTERNS={
 'mio_truth_certificate': r'MIO.*(truth|certif(?:y|ies).*true|adjudicat.*posterior)',
 'teff_full_solver': r'Teff|TSC.*(full polar|full solver|BB control|family identification)',
 'scalar_family_id': r'(scalar|D_\ell|x,Q|F,G).*family identification',
 'native_transfer_overclaim': r'AniCLASS.*native|native.*AniCLASS',
 'geometry_detected': r'Bianchi geometry detected|global Bianchi anisotropy detected',
}
regs={k:re.compile(v,re.I) for k,v in PATTERNS.items()}
hits=[]
for p in ROOT.rglob('*'):
    if not p.is_file() or p.suffix.lower() not in {'.md','.tex','.py','.yaml','.yml','.json'}: continue
    if any(part in EXCLUDE for part in p.parts): continue
    for i,line in enumerate(p.read_text(errors='ignore').splitlines(),1):
        for name,reg in regs.items():
            if reg.search(line): hits.append((name,p,i,line.strip()))
if hits:
    print('Forbidden/unsafe claim patterns:')
    for name,p,i,l in hits: print(f'{name}: {p}:{i}: {l}')
    sys.exit(1)
print('No forbidden claim patterns detected.')
