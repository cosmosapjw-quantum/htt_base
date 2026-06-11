#!/usr/bin/env python3
from __future__ import annotations
import re, json, sys
from pathlib import Path
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path.cwd(); skills=root/'.agents'/'skills'
rows=[]
for sk in sorted(skills.iterdir() if skills.exists() else []):
    f=sk/'SKILL.md'
    if not f.exists(): continue
    txt=f.read_text(errors='ignore')
    m=re.match(r'^---\s*\n(.*?)\n---',txt,re.S)
    front=m.group(1) if m else ''
    name=re.search(r'^name:\s*(\S+)\s*$',front,re.M)
    desc=re.search(r'^description:\s*(.+)$',front,re.M)
    rows.append({'folder':sk.name,'name':name.group(1) if name else sk.name,'description':desc.group(1).strip() if desc else ''})
print(json.dumps(rows,indent=2,ensure_ascii=False))
