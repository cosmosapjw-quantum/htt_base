#!/usr/bin/env python3
"""
extract_cmb_like_products.py
============================

Pack ACT DR4 and/or SPT-3G Y1 likelihood archives into compact NPZ.

Patched from external_data_recovery_v2 to add --target {act,spt,both}
so the orchestrator can call this stage twice (once per instrument)
and skip the already-completed half.
"""
from __future__ import annotations
import argparse, io, json, tarfile, zipfile
from pathlib import Path
import sys
from typing import Dict, List, Optional
import numpy as np

# These scripts are run as files and are also loaded by path from repo-root
# tests, so the sibling import needs this directory on sys.path either way.
_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from external_store import ensure_data_dir


def ensure_dir(p: Path) -> None:
    if str(p).startswith('/path/to/'):
        raise SystemExit(f"Refusing placeholder outdir/workdir: {p}")
    ensure_data_dir(p)


def iter_archive_members(archive_path: Path):
    if archive_path.name.endswith(('.tar.gz', '.tgz')):
        with tarfile.open(archive_path, 'r:gz') as tf:
            for m in tf.getmembers():
                if m.isfile():
                    fh = tf.extractfile(m)
                    if fh is not None:
                        yield m.name, fh.read()
    elif archive_path.suffix.lower() == '.zip':
        with zipfile.ZipFile(archive_path, 'r') as zf:
            for n in zf.namelist():
                if not n.endswith('/'):
                    yield n, zf.read(n)


def lower_name(x: str) -> str:
    return x.replace('\\', '/').lower()


def try_load_numeric_text(blob: bytes) -> Optional[np.ndarray]:
    text = blob.decode('utf-8', errors='ignore')
    if not any(ch.isdigit() for ch in text):
        return None
    try:
        arr = np.genfromtxt(io.StringIO(text), comments='#')
        if isinstance(arr, np.ndarray) and arr.size > 0 and np.issubdtype(arr.dtype, np.number):
            return np.atleast_2d(arr)
    except Exception:
        return None
    return None


def collect_by_patterns(archive: Path, patterns: Dict[str, List[str]]):
    out = {k: [] for k in patterns}
    for name, blob in iter_archive_members(archive):
        lname = lower_name(name)
        for key, pats in patterns.items():
            if any(p in lname for p in pats):
                arr = try_load_numeric_text(blob)
                if arr is not None:
                    out[key].append((name, arr))
    return out


def _safe_key(category: str, fname: str, existing: set) -> str:
    stem = Path(fname).name
    for ch in "/\\.- ":
        stem = stem.replace(ch, "_")
    base = f"{category}__{stem}"
    key = base
    n = 1
    while key in existing:
        n += 1
        key = f"{base}__{n}"
    return key


def pack(label: str, archives: List[Path], patterns: Dict[str, List[str]],
         outnpz: Path, outmanifest: Path, keep_all: bool = True):
    manifest = {'label': label, 'archives': [], 'selected': {}, 'keep_all': keep_all}
    payload: dict = {}
    for p in archives:
        if not p.exists():
            continue
        manifest['archives'].append(str(p))
        found = collect_by_patterns(p, patterns)
        for key, vals in found.items():
            if not vals:
                continue
            if keep_all:
                for name, arr in vals:
                    unique = _safe_key(key, name, set(payload.keys()))
                    payload[unique] = arr
                    manifest['selected'].setdefault(key, []).append(
                        {'archive_member': name, 'payload_key': unique}
                    )
            else:
                if key not in payload:
                    name, arr = vals[0]
                    payload[key] = arr
                    manifest['selected'][key] = name
    if not payload:
        raise RuntimeError(f'No payload found for {label}')
    np.savez(outnpz, **payload)
    outmanifest.write_text(json.dumps(manifest, indent=2))
    return manifest


ACT_PATTERNS = {
    'binning': ['binning.dat', 'binning'],
    'clcmb':   ['cl_cmb', 'cmbonly', 'bandpower'],
    'cov':     ['covmat', 'covariance', 'cov'],
    'theory':  ['bestfit', 'theory', 'lcdm'],
}
SPT_PATTERNS = {
    'bandpowers': ['bandpower', 'bandpowers', 'spectra'],
    'cov':        ['covariance', 'covmat', 'cov'],
    'windows':    ['window', 'windows', 'bpwf'],
    'templates':  ['tsz', 'ksz', 'template'],
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--workdir', default='./workdir')
    ap.add_argument('--outdir', default=None)
    ap.add_argument('--target', choices=['act', 'spt', 'both'], default='both')
    ap.add_argument('--keep-all', dest='keep_all', action='store_true', default=True,
                    help="retain every archive member matching a pattern (default). "
                         "Multi-frequency covariances / all binning files land in the "
                         "NPZ keyed by <category>__<filename>.")
    ap.add_argument('--first-match-only', dest='keep_all', action='store_false',
                    help="legacy sandbox-era behavior: keep only the first matching "
                         "file per category.")
    args = ap.parse_args()

    workdir = Path(args.workdir).expanduser().resolve()
    outdir = Path(args.outdir).expanduser().resolve() if args.outdir else workdir / 'compact_products'
    ensure_dir(outdir)
    downloads = workdir / 'downloads'
    summary_path = outdir / 'cmb_like_extraction_summary.json'
    summary = json.loads(summary_path.read_text()) if summary_path.exists() else {}

    if args.target in ('act', 'both'):
        try:
            summary['act'] = pack(
                'ACT_DR4',
                [downloads / 'actpollite_python_dr4.01.tar.gz',
                 downloads / 'act_dr4.01_cmbonly_spectra.tar.gz',
                 downloads / 'pyactlike_master.zip'],
                ACT_PATTERNS,
                outdir / 'act_dr4_compact.npz',
                outdir / 'act_dr4_compact.manifest.json',
                keep_all=args.keep_all,
            )
            print(f"[ok] ACT DR4 → {outdir / 'act_dr4_compact.npz'}")
        except Exception as e:
            summary['act_error'] = str(e)
            print(f"[err] ACT DR4: {e}")

    if args.target in ('spt', 'both'):
        try:
            summary['spt'] = pack(
                'SPT3G_Y1',
                [downloads / 'SPT3G_2018_TTTEEE_public_likelihood.v1.1.tar.gz',
                 downloads / 'spt3g_y1_dist_main.zip'],
                SPT_PATTERNS,
                outdir / 'spt3g_y1_compact.npz',
                outdir / 'spt3g_y1_compact.manifest.json',
                keep_all=args.keep_all,
            )
            print(f"[ok] SPT-3G Y1 → {outdir / 'spt3g_y1_compact.npz'}")
        except Exception as e:
            summary['spt_error'] = str(e)
            print(f"[err] SPT-3G Y1: {e}")

    summary_path.write_text(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
