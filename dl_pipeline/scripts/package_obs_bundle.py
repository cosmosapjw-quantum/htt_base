#!/usr/bin/env python3
"""
package_obs_bundle.py
=====================

Final consolidation step. Take everything produced by the upstream
extraction stages and assemble it into the obs/ layout established by
the prior reorganization. Zipping is opt-in (`--zip`); the local-dev
workflow consumes the unpacked obs_bundle/ tree directly.

Output layout (mirror of the obs/ bundle):
    obs_bundle/
    ├── README.md, INDEX.json, obs_loader.py
    ├── cmb/{powerspectra,theory,lensing,maps,masks}/
    ├── lss/desi_y1/
    ├── pecvel/cf4/
    └── scalars/

The script is idempotent: if a target file is already present and
identical (by size + first-1KB hash), it is skipped.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import sys
import zipfile
from pathlib import Path

# These scripts are run as files and are also loaded by path from repo-root
# tests, so the sibling import needs this directory on sys.path either way.
_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from external_store import ensure_data_dir

# Mapping table: (source_relative_path_under_workdir, dest_relative_path_under_obs_bundle)
# `source` paths use placeholders that get expanded:
#   {htt}     → workdir/htt_extracted
#   {compact} → workdir/compact_products
#   {extra}   → workdir/obs_extra
#   {repo}    → repository root (passed in via --scalars-root, default: parent of workdir)
COPY_MAP = [
    # ── CMB power spectra ──
    ("{htt}/planck_tt_full_R3.01.npz",   "cmb/powerspectra/planck_pr3_tt_full.npz"),
    ("{htt}/planck_tt_binned_R3.01.npz", "cmb/powerspectra/planck_pr3_tt_binned.npz"),
    ("{htt}/planck_te_full_R3.01.npz",   "cmb/powerspectra/planck_pr3_te_full.npz"),
    ("{htt}/planck_ee_full_R3.01.npz",   "cmb/powerspectra/planck_pr3_ee_full.npz"),
    ("{htt}/planck_lowl_BB_R3.01.npz",   "cmb/powerspectra/planck_pr3_bb_lowl.npz"),
    ("{htt}/planck_lowl_EB_R3.01.npz",   "cmb/powerspectra/planck_pr3_eb_lowl.npz"),
    ("{htt}/act_dr6_tt_bandpowers.npz",  "cmb/powerspectra/act_dr6_tt.npz"),
    ("{htt}/act_dr6_te_bandpowers.npz",  "cmb/powerspectra/act_dr6_te.npz"),
    ("{htt}/act_dr6_ee_bandpowers.npz",  "cmb/powerspectra/act_dr6_ee.npz"),
    ("{compact}/act_dr4_compact.npz",    "cmb/powerspectra/act_dr4.npz"),
    ("{compact}/spt3g_y1_compact.npz",   "cmb/powerspectra/spt3g_y1.npz"),
    ("{extra}/bicep_keck_2018_BB.npz",   "cmb/powerspectra/bicep_keck_2018_bb.npz"),

    # ── CMB theory ──
    ("{htt}/planck_theory_R3.01.npz",                   "cmb/theory/planck_pr3_bestfit.npz"),
    ("{compact}/camb_planck2018_lensing_refs.npz",      "cmb/theory/camb_planck2018_lensing_refs.npz"),

    # ── CMB lensing ──
    ("{extra}/planck_2018_lensing.npz",                 "cmb/lensing/planck_pr3_lensing.npz"),

    # ── CMB maps & masks ──
    ("{htt}/planck_commander_map_nside{nside}.npz",     "cmb/maps/commander_nside{nside}.npz"),
    ("{htt}/planck_smica_map_nside{nside}.npz",         "cmb/maps/smica_nside{nside}.npz"),
    ("{htt}/planck_mask_temp_nside{nside}.npz",         "cmb/masks/temp_nside{nside}.npz"),
    ("{htt}/planck_mask_pol_nside{nside}.npz",          "cmb/masks/pol_nside{nside}.npz"),

    # ── DESI ──
    ("{compact}/desi/BGS_ANY_NGC_clustering_minimal.npz", "lss/desi_y1/bgs_ngc.npz"),
    ("{compact}/desi/BGS_ANY_SGC_clustering_minimal.npz", "lss/desi_y1/bgs_sgc.npz"),
    ("{compact}/desi/LRG_NGC_clustering_minimal.npz",     "lss/desi_y1/lrg_ngc.npz"),
    ("{compact}/desi/LRG_SGC_clustering_minimal.npz",     "lss/desi_y1/lrg_sgc.npz"),
    ("{compact}/desi/QSO_NGC_clustering_minimal.npz",     "lss/desi_y1/qso_ngc.npz"),
    ("{compact}/desi/QSO_SGC_clustering_minimal.npz",     "lss/desi_y1/qso_sgc.npz"),
    ("{compact}/desi/desi_compact_manifest_minimal.json", "lss/desi_y1/manifest.json"),

    # ── Peculiar velocity (CF4) ──
    ("{compact}/cf4/query_single.json",  "pecvel/cf4/query_single.json"),
    ("{compact}/cf4/query_batch.npz",    "pecvel/cf4/query_batch.npz"),

    # ── Scalars (consolidated dipole + per-variant SSOTs) ──
    ("{compact}/dipole_scalar_observations.json", "scalars/dipole_scalar_observations.json"),
    ("{repo}/obs_defaults.json",                  "scalars/obs_defaults.json"),
    ("{repo}/obs_defaults_watkins2023.json",      "scalars/obs_defaults_watkins2023.json"),
    ("{repo}/obs_defaults_CF4pp.json",            "scalars/obs_defaults_courtois2025.json"),
]


def fast_eq(a: Path, b: Path) -> bool:
    """Cheap-and-cheerful equality: same size + same first 1 KiB SHA-1."""
    if a.stat().st_size != b.stat().st_size:
        return False
    h_a = hashlib.sha1(a.read_bytes()[:1024]).hexdigest()
    h_b = hashlib.sha1(b.read_bytes()[:1024]).hexdigest()
    return h_a == h_b


def expand(template: str, *, htt: Path, compact: Path, extra: Path, repo: Path,
           nside: int) -> Path:
    return Path(template.format(htt=htt, compact=compact, extra=extra, repo=repo,
                                nside=nside))


def copy_with_skip(src: Path, dst: Path, log: list) -> str:
    if not src.exists():
        log.append(("MISSING", str(src), str(dst)))
        return "missing"
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() and fast_eq(src, dst):
        log.append(("SKIP",    str(src), str(dst)))
        return "skip"
    shutil.copy2(src, dst)
    log.append(("COPY",    str(src), str(dst)))
    return "copy"


def write_supplementary(out_root: Path, assets_dir: Path):
    """Copy README.md, INDEX.json, and obs_loader.py into the bundle.

    These are produced by the prior reorganization step; we expect them to live
    under assets_dir (i.e. `dl_pipeline/assets/obs_meta/`). If absent, we skip
    silently — the user can drop them in later.
    """
    for name in ("README.md", "INDEX.json", "obs_loader.py"):
        src = assets_dir / name
        if src.exists():
            shutil.copy2(src, out_root / name)
            print(f"  [meta] {name} → {out_root / name}")
        else:
            print(f"  [warn] {name} not found in {assets_dir} (bundle will lack metadata)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True,
                    help="workdir root containing htt_extracted/, compact_products/, obs_extra/")
    ap.add_argument("--out", required=True,
                    help="output bundle directory (will also be zipped to <out>.zip)")
    ap.add_argument("--scalars-root", default=None,
                    help="repository root containing obs_defaults*.json (default: parent of --root)")
    ap.add_argument("--meta-dir", default=None,
                    help="directory containing README.md, INDEX.json, obs_loader.py "
                         "(default: <pipeline>/assets/obs_meta)")
    ap.add_argument("--zip", dest="do_zip", action="store_true",
                    help="also write obs_bundle.zip (off by default; local-dev workflow "
                         "uses the unpacked obs_bundle/ tree directly)")
    ap.add_argument("--planck-nside-out", type=int, default=16,
                    help="NSIDE used for the Planck maps/masks extraction — must match "
                         "what extract_htt_data.py was invoked with (default 16).")
    args = ap.parse_args()

    root = Path(args.root).expanduser().resolve()
    out = Path(args.out).expanduser().resolve()
    htt = root / "htt_extracted"
    compact = root / "compact_products"
    extra = root / "obs_extra"
    repo = Path(args.scalars_root).expanduser().resolve() if args.scalars_root else root.parent
    meta_dir = Path(args.meta_dir).expanduser().resolve() if args.meta_dir else \
               Path(__file__).resolve().parent.parent / "assets" / "obs_meta"

    print(f"[package_obs_bundle]")
    print(f"  root         = {root}")
    print(f"  htt          = {htt}")
    print(f"  compact      = {compact}")
    print(f"  extra        = {extra}")
    print(f"  repo (scalars source) = {repo}")
    print(f"  meta_dir     = {meta_dir}")
    print(f"  out          = {out}")
    print()

    ensure_data_dir(out)
    log = []
    counts = {"copy": 0, "skip": 0, "missing": 0}

    nside = args.planck_nside_out
    for src_tpl, dst_rel in COPY_MAP:
        src = expand(src_tpl, htt=htt, compact=compact, extra=extra, repo=repo,
                     nside=nside)
        dst_str = dst_rel.format(nside=nside)
        dst = out / dst_str
        result = copy_with_skip(src, dst, log)
        counts[result] += 1

    write_supplementary(out, meta_dir)

    # Write a placement log
    log_path = out / "_packaging_log.json"
    log_path.write_text(json.dumps({
        "counts": counts,
        "entries": [{"action": a, "src": s, "dst": d} for (a, s, d) in log],
    }, indent=2))

    print()
    print(f"[summary] copy={counts['copy']}  skip={counts['skip']}  missing={counts['missing']}")
    print(f"          log: {log_path}")

    if counts["missing"] > 0:
        print(f"\n[warn] {counts['missing']} expected artifacts are missing — bundle is incomplete.")
        print( "       Run the upstream stages, then re-run this packager.")

    if args.do_zip:
        zip_path = out.with_suffix(".zip")
        print(f"\n[zip] writing {zip_path} (store-only, no deflate)")
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_STORED) as zf:
            for p in out.rglob("*"):
                if p.is_file():
                    zf.write(p, p.relative_to(out.parent))
        sz_mb = zip_path.stat().st_size / 1024 / 1024
        print(f"[zip] {zip_path.name}: {sz_mb:.1f} MB")

    return 0 if counts["missing"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
