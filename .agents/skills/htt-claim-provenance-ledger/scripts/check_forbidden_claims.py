#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path.cwd()
EXCLUDE = {'.git', '.venv', 'venv', '__pycache__', 'node_modules', 'dist', 'build', '.agents'}
SUFFIX = {'.md', '.tex', '.py', '.yaml', '.yml', '.json'}
PATTERNS = {
    'mio_truth_certificate': r'MIO.*(truth|certif(?:y|ies).*true|adjudicat.*posterior)',
    'teff_full_solver': r'(Teff|TSC).*(full polar|full solver|BB control|family identification)',
    'scalar_family_id': r'(scalar|D_\\ell|D_l|x\s*[,/]\s*Q|F\s*[,/]\s*G).*family identification',
    'native_transfer_overclaim': (
        r'AniCLASS.{0,80}(native (solver )?(result|evidence|validation|validated)|'
        r'validated as native)'
        r'|native.{0,80}AniCLASS.{0,80}(result|evidence|validation|validated)'
    ),
    'geometry_detected': r'Bianchi geometry detected|global Bianchi anisotropy detected',
}


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
    return re.search(r'\b(cannot|must not|do not|does not|not|forbidden)\b', line, re.I) is not None


def main(argv: list[str]) -> int:
    explicit = bool(argv)
    roots = [Path(arg) for arg in argv] if explicit else [ROOT]
    regs = {k: re.compile(v, re.I) for k, v in PATTERNS.items()}
    hits = []
    for p in _iter_files(roots, explicit=explicit):
        for i, line in enumerate(p.read_text(errors='ignore').splitlines(), 1):
            for name, reg in regs.items():
                if _is_negative_guardrail(line):
                    continue
                if reg.search(line):
                    hits.append((name, p, i, line.strip()))
    if hits:
        print('Forbidden/unsafe claim patterns:')
        for name, p, i, line in hits:
            print(f'{name}: {p}:{i}: {line}')
        return 1
    print('No forbidden claim patterns detected.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
