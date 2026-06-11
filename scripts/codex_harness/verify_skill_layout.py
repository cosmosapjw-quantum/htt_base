#!/usr/bin/env python3
from __future__ import annotations
import re, sys
from pathlib import Path
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path.cwd()
skills=root/'.agents'/'skills'
if not skills.exists():
    print(f'Missing {skills}'); sys.exit(1)
names={}; issues=[]
for sk in sorted(skills.iterdir()):
    if not sk.is_dir(): continue
    f=sk/'SKILL.md'
    if not f.exists(): issues.append(f'{sk}: missing SKILL.md'); continue
    txt=f.read_text(errors='ignore')
    m=re.match(r'^---\s*\n(.*?)\n---',txt,re.S)
    if not m: issues.append(f'{f}: missing YAML frontmatter'); continue
    front=m.group(1)
    nm=re.search(r'^name:\s*(\S+)\s*$',front,re.M)
    desc=re.search(r'^description:\s*(.+)$',front,re.M)
    if not nm: issues.append(f'{f}: missing name'); continue
    if not desc: issues.append(f'{f}: missing description');
    name=nm.group(1)
    names.setdefault(name,[]).append(str(f))
for name,files in names.items():
    if len(files)>1: issues.append(f'duplicate skill name {name}: {files}')
if issues:
    print('Skill layout issues:')
    for i in issues: print('-',i)
    sys.exit(1)
print(f'{len(names)} skills OK')
for name in sorted(names): print('-',name)
