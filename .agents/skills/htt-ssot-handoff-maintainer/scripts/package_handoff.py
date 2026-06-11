#!/usr/bin/env python3
from __future__ import annotations
import zipfile, json
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path.cwd(); stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
out=ROOT/f'htt_handoff_package_{stamp}.zip'
include_dirs=['docs/harness','docs/generated','docs/codex_handoff','.agents/skills','.codex/agents','.codex/rules','scripts/codex_harness']
include_files=['AGENTS.md','agent.md','README.md','pyproject.toml','pytest.ini']
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as zf:
    for d in include_dirs:
        p=ROOT/d
        if p.exists():
            for f in p.rglob('*'):
                if f.is_file() and '.git' not in f.parts: zf.write(f,f.relative_to(ROOT))
    for f in include_files:
        p=ROOT/f
        if p.exists(): zf.write(p,p.relative_to(ROOT))
print(out)
