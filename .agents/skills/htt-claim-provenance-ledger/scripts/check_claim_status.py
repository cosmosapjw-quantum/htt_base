#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path.cwd()
EXCLUDE = {'.git', '.venv', 'venv', '__pycache__', 'node_modules', 'dist', 'build', '.agents'}
SUFFIX = {'.md', '.tex', '.rst'}
STRONG = [
    r'\bwe prove\b',
    r'\bwe demonstrate\b',
    r'\bvalidated\b',
    r'\bproduction[- ]ready\b',
    r'\bexact (proof|solution|solver|validation|match|bound|evidence)\b',
    r'\bguarantee\b',
    r'\bfully implemented\b',
    r'\bsubmission[- ]ready\b',
    r'\bfamily identification\b',
    r'\bBianchi geometry detected\b',
]
STATUS = [
    'IMPLEMENTED',
    'SMOKE_TESTED',
    'VALIDATED',
    'DERIVED',
    'SPECIFIED',
    'CONDITIONAL',
    'DIAGNOSTIC_ONLY',
    'PROPOSED',
    'SPECULATIVE',
    'DEPRECATED',
    'FORBIDDEN',
    'C0',
    'C1',
    'C2',
    'C3',
    'C4',
    'C5',
    'C6',
]


def _iter_files(paths: list[Path], *, explicit: bool):
    for path in paths:
        if path.is_file():
            candidates = [path]
        elif path.is_dir():
            candidates = path.rglob('*')
        else:
            continue
        for p in candidates:
            if not p.is_file() or p.suffix.lower() not in SUFFIX:
                continue
            if not explicit and any(part in EXCLUDE for part in p.parts):
                continue
            yield p


def _is_negative_guardrail(line: str) -> bool:
    return re.search(r'\b(cannot|must not|do not|does not|not|blocked until|forbidden)\b', line, re.I) is not None


def main(argv: list[str]) -> int:
    explicit = bool(argv)
    roots = [Path(arg) for arg in argv] if explicit else [ROOT]
    regs = [re.compile(pattern, re.I) for pattern in STRONG]
    hits = []
    for p in _iter_files(roots, explicit=explicit):
        lines = p.read_text(errors='ignore').splitlines()
        in_frontmatter = bool(lines and lines[0].strip() == '---')
        for i, line in enumerate(lines):
            if i == 0 and in_frontmatter:
                continue
            if in_frontmatter:
                if line.strip() == '---':
                    in_frontmatter = False
                continue
            if line.lstrip().startswith('#'):
                continue
            if _is_negative_guardrail(line):
                continue
            if any(reg.search(line) for reg in regs):
                window = '\n'.join(lines[max(0, i - 3):min(len(lines), i + 4)])
                if not any(status in window for status in STATUS):
                    hits.append((p, i + 1, line.strip()))
    if hits:
        print('Strong claims without nearby status markers:')
        for p, i, line in hits:
            print(f'{p}:{i}: {line}')
        return 1
    print('No unmarked strong claims detected.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
