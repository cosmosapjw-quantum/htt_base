#!/usr/bin/env python3
"""
fetch.py — Unified data download & extraction orchestrator
==========================================================

Single entry point for every external download required by the BASS
observational data bundle. Reads `config/sources.json` as the single
source of truth and runs each stage in dependency order.

Idempotent: every download checks file existence + size; every extraction
checks output mtime > input mtime. Re-running is cheap.

Usage
-----
    python3 fetch.py --root ./workdir --all
    python3 fetch.py --root ./workdir --stages planck_pr3,desi_y1
    python3 fetch.py --root ./workdir --list
    python3 fetch.py --root ./workdir --dry-run --all

Stage IDs (run in this order with --all):
    env, planck_pr3, bicep_keck, planck_lensing, act_dr4, act_dr6,
    spt3g_y1, desi_y1, cf4, camb_refs, scalars, package
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Optional

from dl_fits_utils import format_fits_size, inspect_fits_file


# ──────────────────────────────────────────────────────────────────────────
# Paths and constants
# ──────────────────────────────────────────────────────────────────────────

PIPELINE_DIR = Path(__file__).resolve().parent.parent  # scripts/.. = pipeline root
SOURCES_FILE = PIPELINE_DIR / "config" / "sources.json"
SCRIPTS_DIR  = PIPELINE_DIR / "scripts"
ASSETS_DIR   = PIPELINE_DIR / "assets"
CONFIG_DIR   = PIPELINE_DIR / "config"


# ──────────────────────────────────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────────────────────────────────

class Logger:
    def __init__(self, log_path: Optional[Path] = None):
        self.log_path = log_path
        if log_path:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            self._fh = open(log_path, "a", encoding="utf-8")
        else:
            self._fh = None

    def __call__(self, msg: str, end: str = "\n"):
        ts = time.strftime("%H:%M:%S")
        line = f"[{ts}] {msg}"
        print(line, end=end, flush=True)
        if self._fh:
            self._fh.write(line + end)
            self._fh.flush()

    def close(self):
        if self._fh:
            self._fh.close()


# ──────────────────────────────────────────────────────────────────────────
# Idempotent downloader
# ──────────────────────────────────────────────────────────────────────────

def download(url: str, dst: Path, log: Logger, force: bool = False,
             optional: bool = False) -> bool:
    """Download url → dst. Skip if dst exists and force is False.
    Returns True on success (or skip), False on optional failure."""
    if dst.exists() and not force:
        sz = dst.stat().st_size
        log(f"  [skip] {dst.name} ({sz / 1024:.1f} KB already present)")
        return True

    dst.parent.mkdir(parents=True, exist_ok=True)
    log(f"  [download] {url}")
    log(f"             → {dst}")

    # Prefer curl if available (better progress, retries)
    if shutil.which("curl"):
        cmd = ["curl", "-L", "--fail", "--retry", "4", "--retry-delay", "5",
               "--connect-timeout", "30", "-o", str(dst), url]
        try:
            subprocess.run(cmd, check=True)
            return True
        except subprocess.CalledProcessError as e:
            if optional:
                log(f"  [warn] optional download failed (rc={e.returncode}): {url}")
                return False
            raise

    # Fallback: urllib
    try:
        with urllib.request.urlopen(url, timeout=120) as r, open(dst, "wb") as f:
            shutil.copyfileobj(r, f)
        return True
    except Exception as e:
        if optional:
            log(f"  [warn] optional download failed: {e}")
            return False
        raise


# ──────────────────────────────────────────────────────────────────────────
# Subprocess runner
# ──────────────────────────────────────────────────────────────────────────

def run_python(script: Path, args: list[str], log: Logger,
               check: bool = True) -> int:
    """Run a Python script as a subprocess, capturing both streams to log."""
    cmd = [sys.executable, str(script), *args]
    log(f"  [exec] {' '.join(cmd)}")
    try:
        proc = subprocess.run(cmd, check=check, capture_output=False)
        return proc.returncode
    except subprocess.CalledProcessError as e:
        log(f"  [err] script failed (rc={e.returncode})")
        if check:
            raise
        return e.returncode


def run_shell(cmd: list[str], log: Logger, check: bool = True) -> int:
    log(f"  [exec] {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=check)
        return 0
    except subprocess.CalledProcessError as e:
        log(f"  [err] command failed (rc={e.returncode})")
        if check:
            raise
        return e.returncode


# ──────────────────────────────────────────────────────────────────────────
# Stage implementations
# ──────────────────────────────────────────────────────────────────────────

def stage_env(root: Path, sources: dict, log: Logger, **opts):
    """Install Python dependencies into the active venv.

    Refuses to run outside a venv — the pipeline is now local-dev only and must
    never pollute the system site-packages. Invoke via run_all.sh (which picks
    the repo-local venv) or activate the venv manually before running fetch.py.
    """
    in_venv = sys.prefix != getattr(sys, 'base_prefix', sys.prefix)
    if not in_venv:
        log(f"  [err] not running inside a venv (sys.executable={sys.executable}).")
        log( "        Activate the venv or invoke via run_all.sh, which uses ../venv/bin/python.")
        return
    deps = ["numpy>=1.24", "scipy>=1.10", "requests>=2.31",
            "beautifulsoup4>=4.12", "astropy>=6.0", "healpy>=1.16",
            "sacc>=0.4", "cobaya>=3.5", "camb==1.6.6"]
    if opts.get("skip_heavy"):
        deps = [d for d in deps if not d.startswith(("camb", "healpy", "sacc", "cobaya"))]
        log("  (--skip-heavy: omitting camb/healpy/sacc/cobaya)")
    log(f"  Installing deps into venv: {sys.prefix}")
    cmd = [sys.executable, "-m", "pip", "install", "--upgrade", *deps]
    run_shell(cmd, log, check=False)


def stage_planck_pr3(root: Path, sources: dict, log: Logger, **opts):
    """Download Planck PR3 spectra/maps/masks, then run extract_htt_data.py."""
    s = sources["planck_pr3"]
    raw_dir = root / "raw" / "planck_data"
    raw_dir.mkdir(parents=True, exist_ok=True)

    skip_maps = opts.get("skip_large_maps", False)

    def maybe_force_redownload(path: Path) -> bool:
        if not path.exists() or path.suffix.lower() != ".fits":
            return False
        report = inspect_fits_file(path)
        if report.status == "truncated":
            log(
                f"  [warn] {path.name} is truncated "
                f"(actual={format_fits_size(report.actual_size)}, "
                f"expected={format_fits_size(report.expected_size)}); re-downloading"
            )
            return True
        if report.status == "unreadable":
            log(f"  [warn] {path.name} is unreadable ({report.detail}); re-downloading")
            return True
        if report.status == "unavailable":
            log(f"  [warn] astropy unavailable; cannot validate existing FITS {path.name}")
        return False

    # Download spectra + theory
    for fname in s["files"]["spectra"] + s["files"]["theory"]:
        download(f"{s['base_cosmoparams']}/{fname}", raw_dir / fname, log)
    # Download masks
    for fname in s["files"]["masks"]:
        dst = raw_dir / fname
        download(
            f"{s['base_masks']}/{fname}",
            dst,
            log,
            force=opts.get("force", False) or maybe_force_redownload(dst),
        )
    # Maps (optional, large ~1.6 GB each)
    if not skip_maps:
        for fname in s["files"]["maps_optional_large"]:
            dst = raw_dir / fname
            download(
                f"{s['base_maps']}/{fname}",
                dst,
                log,
                force=opts.get("force", False) or maybe_force_redownload(dst),
                optional=True,
            )
    else:
        log("  [skip] large maps (--skip-large-maps)")

    # Extract
    out_dir = root / "htt_extracted"
    act_dir = root / "raw" / "act_data"
    act_dir.mkdir(parents=True, exist_ok=True)
    extract_args = ["--planck-dir", str(raw_dir),
                    "--act-dir", str(act_dir),
                    "--out", str(out_dir),
                    "--planck-nside-out", str(opts.get("planck_nside_out", 16))]
    if opts.get("full_res_maps"):
        extract_args.append("--full-res-maps")
    run_python(SCRIPTS_DIR / "extract_htt_data.py", extract_args, log, check=False)


def stage_act_dr6(root: Path, sources: dict, log: Logger, **opts):
    """ACT DR6: hint that the user must place dr6_data.fits manually."""
    act_dir = root / "raw" / "act_data"
    act_dir.mkdir(parents=True, exist_ok=True)
    target = act_dir / "dr6_data.fits"
    if target.exists():
        log(f"  [ok] {target} already present ({target.stat().st_size / 1024 / 1024:.1f} MB)")
        log("  ACT DR6 extraction is performed inside stage planck_pr3 (extract_htt_data.py).")
        return

    url = os.environ.get("ACT_DR6_SACC_URL")
    if url:
        download(url, target, log)
        return

    log(f"  [manual] ACT DR6 sacc file required at: {target}")
    log("           Either set ACT_DR6_SACC_URL=... and rerun this stage,")
    log("           or copy the file there yourself and rerun stage planck_pr3.")


def stage_bicep_keck(root: Path, sources: dict, log: Logger, **opts):
    pkg = root / "cobaya_packages"
    pkg.mkdir(parents=True, exist_ok=True)
    out = root / "obs_extra" / "bicep_keck_2018_BB.npz"
    if out.exists() and not opts.get("force"):
        log(f"  [skip] {out.name} already present")
        return
    log("  cobaya-install bicep_keck_2018 ...")
    cmd = ["cobaya-install", "bicep_keck_2018", "-p", str(pkg),
           "--no-set-global", "--no-progress-bars"]
    if not shutil.which("cobaya-install"):
        log("  [err] cobaya-install not on PATH. Install with: pip install cobaya")
        return
    run_shell(cmd, log, check=False)
    run_python(SCRIPTS_DIR / "pack_cobaya_install.py",
               ["--module", "bicep_keck_2018",
                "--packages-path", str(pkg),
                "--out", str(out)], log, check=False)


def stage_planck_lensing(root: Path, sources: dict, log: Logger, **opts):
    pkg = root / "cobaya_packages"
    pkg.mkdir(parents=True, exist_ok=True)
    out = root / "obs_extra" / "planck_2018_lensing.npz"
    if out.exists() and not opts.get("force"):
        log(f"  [skip] {out.name} already present")
        return
    if not shutil.which("cobaya-install"):
        log("  [err] cobaya-install not on PATH. Install with: pip install cobaya")
        return
    log("  cobaya-install planck_2018_lensing.native ...")
    cmd = ["cobaya-install", "planck_2018_lensing.native", "-p", str(pkg),
           "--no-set-global", "--no-progress-bars"]
    run_shell(cmd, log, check=False)
    run_python(SCRIPTS_DIR / "pack_cobaya_install.py",
               ["--module", "planck_2018_lensing.native",
                "--packages-path", str(pkg),
                "--out", str(out)], log, check=False)


def stage_act_dr4(root: Path, sources: dict, log: Logger, **opts):
    s = sources["act_dr4"]
    for d in s["downloads"]:
        download(d["url"], root / d["out"], log,
                 optional=d.get("optional", False))
    run_python(SCRIPTS_DIR / "extract_cmb_like_products.py",
               ["--workdir", str(root),
                "--outdir", str(root / "compact_products"),
                "--target", "act"], log, check=False)


def stage_spt3g_y1(root: Path, sources: dict, log: Logger, **opts):
    s = sources["spt3g_y1"]
    for d in s["downloads"]:
        download(d["url"], root / d["out"], log,
                 optional=d.get("optional", False))
    run_python(SCRIPTS_DIR / "extract_cmb_like_products.py",
               ["--workdir", str(root),
                "--outdir", str(root / "compact_products"),
                "--target", "spt"], log, check=False)


def stage_desi_y1(root: Path, sources: dict, log: Logger, **opts):
    s = sources["desi_y1"]
    raw = root / "raw" / "desi"
    raw.mkdir(parents=True, exist_ok=True)
    for fname in s["files"]:
        download(f"{s['base']}/{fname}", raw / fname, log)
    out = root / "compact_products" / "desi"
    desi_mode = opts.get("desi_mode") or "extended"
    run_python(SCRIPTS_DIR / "extract_desi_compact.py",
               ["--input-dir", str(raw),
                "--outdir", str(out),
                "--mode", desi_mode], log, check=False)


def stage_cf4(root: Path, sources: dict, log: Logger, **opts):
    s = sources["cf4"]
    cf4_dir = root / "raw" / "cf4"
    cf4_dir.mkdir(parents=True, exist_ok=True)
    grid_file = cf4_dir / s["expected_filename"]

    # Try to fetch the grid from the canonical URL unless the env var overrides it.
    url = os.environ.get("CF4_GRID_URL") or s.get("download_url")
    if url and not grid_file.exists():
        download(url, grid_file, log, optional=True)

    if not grid_file.exists():
        log(f"  [manual] CF4 grid required at: {grid_file}")
        log(f"           Project page: {s['project_page']}")
        if s.get("download_url"):
            log(f"           Automatic download URL: {s['download_url']}")
        log( "           If auto-download fails, rerun with CF4_GRID_URL=... or copy the file in place.")
        return

    out_dir = root / "compact_products" / "cf4"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Single-point query
    args_single = [a.replace("{out}", str(root)) for a in s["queries"][0]["args"]]
    args_single = ["--grid", str(grid_file)] + args_single
    run_python(SCRIPTS_DIR / "cf4_grid_adapter.py", args_single, log, check=False)

    # Batch query targets: prefer a DESI-derived hardware-adaptive CSV.
    csv_in = ASSETS_DIR / "targets_cf4_from_desi_bgs.csv"
    desi_dir = root / "compact_products" / "desi"
    auto_csv = out_dir / "targets_cf4_from_desi_bgs_auto.csv"
    auto_report = out_dir / "targets_cf4_from_desi_bgs_auto.report.json"
    if desi_dir.exists():
        rc = run_python(
            SCRIPTS_DIR / "generate_cf4_targets_from_desi.py",
            ["--desi-dir", str(desi_dir),
             "--grid", str(grid_file),
             "--out", str(auto_csv),
             "--report-out", str(auto_report)],
            log,
            check=False,
        )
        if rc == 0 and auto_csv.exists():
            csv_in = auto_csv
            log(f"  [ok] using hardware-adaptive CF4 target CSV: {csv_in}")
        else:
            log(f"  [warn] auto-generation failed; falling back to bundled CSV: {csv_in}")
    else:
        log(f"  [warn] DESI compact products missing at {desi_dir}; using bundled CF4 target CSV")

    args_batch = ["--grid", str(grid_file),
                  "--input-csv", str(csv_in),
                  "--coord-type", "equatorial",
                  "--unit-type", "degrees",
                  "--distance-type", "redshift",
                  "--out", str(out_dir / "query_batch.npz")]
    run_python(SCRIPTS_DIR / "cf4_grid_adapter.py", args_batch, log, check=False)


def stage_camb_refs(root: Path, sources: dict, log: Logger, **opts):
    out = root / "compact_products" / "camb_planck2018_lensing_refs.npz"
    if out.exists() and not opts.get("force"):
        log(f"  [skip] {out.name} already present")
        return
    try:
        import camb  # noqa: F401
    except ImportError:
        log("  [info] CAMB not installed — running pip install camb==1.6.6")
        run_shell([sys.executable, "-m", "pip", "install", "camb==1.6.6"],
                  log, check=False)
    run_python(SCRIPTS_DIR / "generate_camb_lensing_refs.py",
               ["--params-json", str(CONFIG_DIR / "planck2018_camb_params.json"),
                "--outdir", str(root / "compact_products")],
               log, check=False)


def stage_scalars(root: Path, sources: dict, log: Logger, **opts):
    out = root / "compact_products" / "dipole_scalar_observations.json"
    repo_root = opts.get("scalars_root") or root.parent
    run_python(SCRIPTS_DIR / "package_dipole_observations.py",
               ["--repo-root", str(repo_root), "--out", str(out)],
               log, check=False)


def stage_package(root: Path, sources: dict, log: Logger, **opts):
    out = root / "obs_bundle"
    repo_root = opts.get("scalars_root") or root.parent
    args = ["--root", str(root), "--out", str(out),
            "--scalars-root", str(repo_root),
            "--meta-dir", str(ASSETS_DIR / "obs_meta"),
            "--planck-nside-out", str(opts.get("planck_nside_out", 16))]
    if opts.get("bundle_zip"):
        args.append("--zip")
    run_python(SCRIPTS_DIR / "package_obs_bundle.py", args, log, check=False)


def stage_cf4_full(root: Path, sources: dict, log: Logger, **opts):
    """Cosmicflows-4 FULL release group catalog (VizieR J/ApJ/944/94) -> npz.

    Downloads table2/3/4 + ReadMe and parses table4 (group distances + peculiar
    velocities) into a release-hashed npz for LR-06D. Acquisition + schema only.
    """
    s = sources["cf4_full"]
    out_npz = root / "obs_bundle" / "pecvel" / "cf4_full" / "cf4_groups.npz"
    args = [a.replace("{raw}", str(root / "raw")).replace("{out}", str(root / "obs_bundle"))
            for a in s["extraction"]["args"]]
    rc = run_python(SCRIPTS_DIR / "extract_cf4_full.py", args, log, check=False)
    if rc != 0 or not out_npz.exists():
        log("  [manual] CF4 full release unavailable (BLOCKED_MISSING_FULL_RELEASE_BINDING).")
        log(f"           VizieR: {s['project_page']}")


# Stage registry
STAGES = {
    "env":            stage_env,
    "cf4_full":       stage_cf4_full,
    "planck_pr3":     stage_planck_pr3,
    "bicep_keck":     stage_bicep_keck,
    "planck_lensing": stage_planck_lensing,
    "act_dr4":        stage_act_dr4,
    "act_dr6":        stage_act_dr6,
    "spt3g_y1":       stage_spt3g_y1,
    "desi_y1":        stage_desi_y1,
    "cf4":            stage_cf4,
    "camb_refs":      stage_camb_refs,
    "scalars":        stage_scalars,
    "package":        stage_package,
}


# ──────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────

def list_stages(sources: dict):
    print("Available stages (run in this order with --all):\n")
    for sid in sources["_schema"]["stage_order"]:
        meta = sources.get(sid, {})
        doc = meta.get("_doc", "(env / orchestration stage)")
        sz = meta.get("size_estimate_GB")
        sz_str = f" [~{sz} GB raw]" if sz else ""
        print(f"  {sid:18s}{sz_str}")
        print(f"      {doc[:120]}")
        print()


def main():
    ap = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                 description=__doc__)
    ap.add_argument("--root", required=True,
                    help="Working directory (downloads, raw, extracted, compact_products)")
    ap.add_argument("--all", action="store_true", help="run every stage in order")
    ap.add_argument("--stages", default=None,
                    help="comma-separated subset of stage IDs to run")
    ap.add_argument("--list", action="store_true", help="list stages and exit")
    ap.add_argument("--dry-run", action="store_true",
                    help="print plan without executing")
    ap.add_argument("--force", action="store_true",
                    help="re-download / re-extract even if outputs exist")
    ap.add_argument("--skip-heavy", action="store_true",
                    help="skip heavy pip installs (camb, healpy, sacc, cobaya) in env stage")
    ap.add_argument("--skip-large-maps", action="store_true",
                    help="skip the ~3 GB Planck Commander/SMICA map downloads")
    ap.add_argument("--scalars-root", default=None,
                    help="repo dir holding obs_defaults*.json (default: parent of --root)")
    ap.add_argument("--bundle-zip", action="store_true",
                    help="also emit obs_bundle.zip (off by default; local-dev uses "
                         "the unpacked obs_bundle/ tree directly)")
    ap.add_argument("--planck-nside-out", type=int, default=16,
                    help="Target NSIDE for Planck map/mask downgrade (default 16, "
                         "the canonical low-ℓ pixel-likelihood resolution).")
    ap.add_argument("--full-res-maps", action="store_true",
                    help="Also dump full-resolution (NSIDE=2048) Planck map/mask "
                         "NPZs alongside the downgraded ones (~200 MB per map).")
    ap.add_argument("--desi-mode", choices=["minimal", "extended"], default="extended",
                    help="DESI column set — extended (default) keeps all weights + "
                         "targetid/ntile/photsys; minimal strips to ra/dec/z/weight/n_hat.")
    args = ap.parse_args()

    if not SOURCES_FILE.exists():
        sys.exit(f"sources.json not found at {SOURCES_FILE}")
    sources = json.loads(SOURCES_FILE.read_text())

    if args.list:
        list_stages(sources)
        return

    if not args.all and not args.stages:
        ap.error("must specify either --all or --stages")

    if args.all:
        plan = sources["_schema"]["stage_order"]
    else:
        plan = [s.strip() for s in args.stages.split(",") if s.strip()]
        for s in plan:
            if s not in STAGES:
                sys.exit(f"unknown stage: {s!r}. See --list.")

    root = Path(args.root).expanduser().resolve()
    if str(root).startswith("/path/to/"):
        sys.exit(f"refusing placeholder workdir: {root}")
    root.mkdir(parents=True, exist_ok=True)

    log_path = root / "logs" / f"fetch_{time.strftime('%Y%m%d_%H%M%S')}.log"
    log = Logger(log_path)
    log("=" * 70)
    log(f"BASS data pipeline — root={root}")
    log(f"plan: {' → '.join(plan)}")
    log(f"options: force={args.force}  skip_heavy={args.skip_heavy}  "
        f"skip_large_maps={args.skip_large_maps}  dry_run={args.dry_run}")
    log("=" * 70)

    if args.dry_run:
        for sid in plan:
            log(f"[plan] {sid}: {sources.get(sid, {}).get('_doc', '')[:80]}")
        log.close()
        return

    opts = dict(force=args.force, skip_heavy=args.skip_heavy,
                skip_large_maps=args.skip_large_maps,
                scalars_root=args.scalars_root,
                bundle_zip=args.bundle_zip,
                planck_nside_out=args.planck_nside_out,
                full_res_maps=args.full_res_maps,
                desi_mode=args.desi_mode)

    failed = []
    for sid in plan:
        log("")
        log(f"━━━ stage: {sid} ━━━")
        try:
            STAGES[sid](root, sources, log, **opts)
            log(f"  [done] {sid}")
        except Exception as e:
            log(f"  [FAIL] {sid}: {e}")
            failed.append(sid)

    log("")
    log("=" * 70)
    log(f"completed: {len(plan) - len(failed)}/{len(plan)}  failed: {failed or 'none'}")
    log(f"log saved: {log_path}")
    log("=" * 70)
    log.close()
    sys.exit(0 if not failed else 1)


if __name__ == "__main__":
    main()
