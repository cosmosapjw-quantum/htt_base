#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
from typing import Any, Dict, List, Optional

def load_json(p: Path) -> Dict[str, Any]:
    return json.loads(p.read_text())

def find_first(names: List[str], roots: List[Path]) -> Optional[Path]:
    for r in roots:
        if not r.exists():
            continue
        for name in names:
            cand = r / name
            if cand.exists():
                return cand
        for name in names:
            hits = list(r.rglob(name))
            if hits:
                return hits[0]
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--obs-defaults', default=None)
    ap.add_argument('--obs-defaults-alt', action='append', default=[])
    ap.add_argument('--repo-root', default='.')
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    search_roots = [Path.cwd(), repo_root, repo_root.parent]
    canonical_path = Path(args.obs_defaults).expanduser().resolve() if args.obs_defaults else find_first(['obs_defaults.json'], search_roots)
    if canonical_path is None:
        raise SystemExit('Could not locate obs_defaults.json; pass --obs-defaults or --repo-root')
    alt_paths = []
    for p in args.obs_defaults_alt:
        alt_paths.append(Path(p).expanduser().resolve())
    for default_name in ['obs_defaults_watkins2023.json','obs_defaults_CF4pp.json']:
        hit = find_first([default_name], search_roots)
        if hit and hit not in alt_paths:
            alt_paths.append(hit)
    canonical = load_json(canonical_path)
    alts = [load_json(p) for p in alt_paths if p.exists()]
    out = {
        'canonical_source': str(canonical_path),
        'alternate_sources': [str(p) for p in alt_paths if p.exists()],
        'planck2018': canonical.get('planck2018', {}),
        'dipole_observations': canonical.get('dipole_observations', {}),
        'vorticity_bound': canonical.get('vorticity_bound', {}),
        'scenarios': canonical.get('scenarios', {}),
        'alternates': []
    }
    for a, p in zip(alts, alt_paths):
        out['alternates'].append({'source': str(p), '_meta': a.get('_meta', {}), 'dipole_observations': a.get('dipole_observations', {}), 'vorticity_bound': a.get('vorticity_bound', {}), 'scenarios': a.get('scenarios', {})})
    out_path = Path(args.out).expanduser().resolve(); out_path.parent.mkdir(parents=True, exist_ok=True); out_path.write_text(json.dumps(out, indent=2))
    print(f'[ok] wrote {out_path}')

if __name__ == '__main__':
    main()
