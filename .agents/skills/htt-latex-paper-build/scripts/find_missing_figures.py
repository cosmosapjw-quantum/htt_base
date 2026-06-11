#!/usr/bin/env python3
from __future__ import annotations
import re, sys
from pathlib import Path
ROOT=Path.cwd(); tex_files=list(ROOT.rglob('*.tex'))
pat=re.compile(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}')
missing=[]
for tex in tex_files:
    if any(part.startswith('.') for part in tex.parts): continue
    txt=tex.read_text(errors='ignore')
    for m in pat.finditer(txt):
        raw=m.group(1)
        candidates=[raw]
        if not Path(raw).suffix:
            candidates += [raw+ext for ext in ['.pdf','.png','.jpg','.jpeg']]
        if not any((tex.parent/c).exists() or (ROOT/c).exists() for c in candidates): missing.append((tex,raw))
if missing:
    print('Missing figure references:')
    for tex,raw in missing: print(f'{tex}: {raw}')
    sys.exit(1)
print('No missing figure references detected by static scan.')
