#!/usr/bin/env python3
"""
fetch.py ??Unified data download & extraction orchestrator
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

from download_inventory import (
    DEFAULT_DOWNLOAD_CAP_BYTES,
    DownloadSpec,
    build_download_inventory,
    resolve_download_url,
    safe_extract_tar,
    write_acquisition_manifest,
    write_inventory_outputs,
)
from dl_fits_utils import format_fits_size, inspect_fits_file


# ??????????????????????????????????????????????????????????????????????????
# Paths and constants
# ??????????????????????????????????????????????????????????????????????????

PIPELINE_DIR = Path(__file__).resolve().parent.parent  # scripts/.. = pipeline root
SOURCES_FILE = PIPELINE_DIR / "config" / "sources.json"
SCRIPTS_DIR  = PIPELINE_DIR / "scripts"
ASSETS_DIR   = PIPELINE_DIR / "assets"
CONFIG_DIR   = PIPELINE_DIR / "config"


# ??????????????????????????????????????????????????????????????????????????
# Logging
# ??????????????????????????????????????????????????????????????????????????

def _console_safe_text(text: str, encoding: str | None = None) -> str:
    """Return text that can be written to the active console encoding."""
    console_encoding = encoding or getattr(sys.stdout, "encoding", None) or "utf-8"
    try:
        text.encode(console_encoding)
        return text
    except (LookupError, UnicodeEncodeError):
        return text.encode(console_encoding, errors="replace").decode(
            console_encoding,
            errors="replace",
        )


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
        print(_console_safe_text(line), end=end, flush=True)
        if self._fh:
            self._fh.write(line + end)
            self._fh.flush()

    def close(self):
        if self._fh:
            self._fh.close()


# ??????????????????????????????????????????????????????????????????????????
# Idempotent downloader
# ??????????????????????????????????????????????????????????????????????????

def download(url: str, dst: Path, log: Logger, force: bool = False,
             optional: bool = False) -> bool:
    """Download url ??dst. Skip if dst exists and force is False.
    Returns True on success (or skip), False on optional failure."""
    if os.environ.get("DL_PIPELINE_NO_DOWNLOAD") == "1":
        raise RuntimeError("DL_PIPELINE_NO_DOWNLOAD=1 refuses network downloads")
    if dst.exists() and not force:
        sz = dst.stat().st_size
        log(f"  [skip] {dst.name} ({sz / 1024:.1f} KB already present)")
        return True

    dst.parent.mkdir(parents=True, exist_ok=True)
    log(f"  [download] {url}")
    log(f"             ??{dst}")

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


# ??????????????????????????????????????????????????????????????????????????
# Subprocess runner
# ??????????????????????????????????????????????????????????????????????????

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


# ??????????????????????????????????????????????????????????????????????????
# Stage implementations
# ??????????????????????????????????????????????????????????????????????????

def stage_env(root: Path, sources: dict, log: Logger, **opts):
    """Install Python dependencies into the active venv.

    Refuses to run outside a venv ??the pipeline is now local-dev only and must
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


def _configured_download_specs(stage: str, root: Path, sources: dict) -> list[DownloadSpec]:
    specs: list[DownloadSpec] = []
    for entry in sources.get(stage, {}).get("downloads", []):
        specs.append(
            DownloadSpec(
                stage=stage,
                item_id=str(entry.get("id") or Path(str(entry["out"])).name),
                url=entry.get("url"),
                source_page=entry.get("page"),
                filename=entry.get("filename"),
                dst=root / str(entry["out"]),
                optional=bool(entry.get("optional", False)),
                expected_size_bytes=entry.get("expected_size_bytes"),
                caveats=tuple(str(v) for v in entry.get("caveats", ())),
            )
        )
    return specs


def _download_configured_specs(
    stage: str,
    root: Path,
    sources: dict,
    log: Logger,
    *,
    force: bool = False,
) -> tuple[list[Path], list[dict]]:
    downloaded: list[Path] = []
    source_items: list[dict] = []
    for spec in _configured_download_specs(stage, root, sources):
        url = resolve_download_url(spec, fetch_pages=True)
        if url is None:
            if spec.optional:
                log(f"  [warn] optional source unresolved: {spec.item_id}")
                continue
            raise RuntimeError(f"download URL could not be resolved for {spec.item_id}")
        download(url, spec.dst, log, force=force, optional=spec.optional)
        if spec.dst.exists():
            downloaded.append(spec.dst)
        source_items.append(
            {
                "id": spec.item_id,
                "url": url,
                "source_page": spec.source_page,
                "filename": spec.filename,
                "destination": str(spec.dst),
                "expected_size_bytes": spec.expected_size_bytes,
                "optional": spec.optional,
            }
        )
    return downloaded, source_items


def _find_file_named(root: Path, filename: str) -> Path | None:
    if not root.exists():
        return None
    for path in root.rglob(filename):
        if path.is_file():
            return path
    return None


def _act_dr6_sacc_path(act_dir: Path) -> Path | None:
    for rel in (
        Path("ACTDR6MFLike") / "v1.0" / "dr6_data.fits",
        Path("v1.0") / "dr6_data.fits",
        Path("dr6_data.fits"),
    ):
        path = act_dir / rel
        if path.exists():
            return path
    return _find_file_named(act_dir, "dr6_data.fits")


def _is_tar_archive(path: Path) -> bool:
    suffixes = path.suffixes
    return suffixes[-2:] == [".tar", ".gz"] or path.suffix == ".tgz"


def _extract_act_dr6_only(root: Path, log: Logger, **opts) -> None:
    run_python(
        SCRIPTS_DIR / "extract_htt_data.py",
        [
            "--act-dir", str(root / "raw" / "act_data"),
            "--out", str(root / "htt_extracted"),
            "--only-act",
        ],
        log,
        check=False,
    )


def stage_act_dr6(root: Path, sources: dict, log: Logger, **opts):
    """ACT DR6.02 SACC acquisition + ACT-only extraction."""
    act_dir = root / "raw" / "act_data"
    act_dir.mkdir(parents=True, exist_ok=True)
    target = act_dir / "dr6_data.fits"
    found = _act_dr6_sacc_path(act_dir)
    if found is not None:
        log(f"  [ok] ACT DR6 SACC present: {found} ({found.stat().st_size / 1024 / 1024:.1f} MB)")
        _extract_act_dr6_only(root, log, **opts)
        return

    url = os.environ.get("ACT_DR6_SACC_URL")
    if url:
        download(url, target, log, force=opts.get("force", False))
        write_acquisition_manifest(
            root / "raw" / "act_data" / "act_dr6_02_acquisition_manifest.json",
            stage="act_dr6",
            source_items=[{"id": "ACT_DR6_SACC_URL", "url": url, "destination": str(target)}],
            local_files=[target],
            generating_command="fetch.py --stages act_dr6",
        )
        _extract_act_dr6_only(root, log, **opts)
        return

    if not opts.get("approve_downloads", False):
        log(f"  [approval-required] ACT DR6.02 SACC missing at: {target}")
        log("           Run --download-inventory first, then rerun with --approve-downloads to fetch Batch A.")
        return

    archives, source_items = _download_configured_specs(
        "act_dr6",
        root,
        sources,
        log,
        force=opts.get("force", False),
    )
    extracted_files: list[Path] = []
    extract_root = act_dir / "act_dr6_02_archives"
    for archive in archives:
        if _is_tar_archive(archive):
            item_dir = extract_root / archive.stem.replace(".tar", "")
            extracted_files.extend(safe_extract_tar(archive, item_dir))

    found = _act_dr6_sacc_path(act_dir) or _find_file_named(extract_root, "dr6_data.fits")
    if found is not None and not target.exists():
        shutil.copy2(found, target)
        log(f"  [ok] copied primary ACT DR6 SACC to {target}")
    write_acquisition_manifest(
        root / "raw" / "act_data" / "act_dr6_02_acquisition_manifest.json",
        stage="act_dr6",
        source_items=source_items,
        local_files=[*archives, *extracted_files, target],
        generating_command="fetch.py --stages act_dr6 --approve-downloads",
    )
    if _act_dr6_sacc_path(act_dir) is None:
        log("  [warn] ACT DR6.02 archives downloaded, but dr6_data.fits was not found after extraction.")
        return
    _extract_act_dr6_only(root, log, **opts)


def _download_act_sims(root: Path, sources: dict, log: Logger, **opts):
    """Download the ACT DR6 lensing baseline reconstruction sims (~59.6 GB)
    for the EXT-ACT low-ell kappa mean field. Off-Dropbox by default; each
    file skips if already present (resumable across restarts)."""
    spec = sources.get("act_dr6_lensing", {}).get("simulations")
    if not spec:
        log("  [err] act_dr6_lensing.simulations missing from sources.json")
        return
    target = opts.get("act_sims_dir")
    if not target:
        nvme = Path("/mnt/sn850x2t/htt_base_e2e/act_dr6_lensing_sims")
        target = nvme if nvme.parent.exists() else root / "downloads" / "act_dr6_lensing_sims"
    target = Path(target)
    target.mkdir(parents=True, exist_ok=True)
    variant = spec.get("variant", "baseline")
    first = int(spec.get("first_index", 1))
    count = int(spec.get("count", 400))
    base = spec["base"]
    pattern = spec["pattern"]
    urls = [f"{base}/{pattern.format(variant=variant, i=i)}"
            for i in range(first, first + count)]
    log(f"  [act-sims] {count} sims -> {target} (~{spec.get('size_estimate_GB')} GB)")

    # Prefer aria2c (parallel + resumable) over the sequential curl fallback:
    # the NERSC portal is slow per stream (~0.2 MB/s), so parallel files win.
    if shutil.which("aria2c"):
        listing = target / "_act_sims_urls.txt"
        listing.write_text("\n".join(urls) + "\n")
        cmd = ["aria2c", "--input-file", str(listing), "--dir", str(target),
               "--continue=true", "--max-concurrent-downloads=8",
               "--max-connection-per-server=2", "--split=2",
               "--min-split-size=32M", "--auto-file-renaming=false",
               "--allow-overwrite=false", "--max-tries=20", "--retry-wait=15",
               "--connect-timeout=60", "--timeout=600", "--summary-interval=30",
               "--console-log-level=notice"]
        log(f"  [act-sims] aria2c {len(urls)} urls (8x2 parallel)")
        run_shell(cmd, log, check=False)
    else:
        for i, url in enumerate(urls, first):
            dst = target / Path(url).name
            download(url, dst, log, force=opts.get("force", False), optional=True)
    done = len(list(target.glob("kappa_alm_sim_*.fits")))
    log(f"  [act-sims] present: {done}/{count} in {target}")


def stage_act_dr6_lensing(root: Path, sources: dict, log: Logger, **opts):
    """ACT DR6 lensing release acquisition; no inference is run here."""
    out_dir = root / "raw" / "act_dr6_lensing"
    out_dir.mkdir(parents=True, exist_ok=True)
    if opts.get("act_sims"):
        _download_act_sims(root, sources, log, **opts)
        return
    if not opts.get("approve_downloads", False):
        log("  [approval-required] ACT DR6 lensing downloads require --approve-downloads.")
        return
    archives, source_items = _download_configured_specs(
        "act_dr6_lensing",
        root,
        sources,
        log,
        force=opts.get("force", False),
    )
    extracted_files: list[Path] = []
    for archive in archives:
        if _is_tar_archive(archive):
            item_dir = out_dir / archive.stem.replace(".tar", "")
            extracted_files.extend(safe_extract_tar(archive, item_dir))
    write_acquisition_manifest(
        out_dir / "act_dr6_lensing_acquisition_manifest.json",
        stage="act_dr6_lensing",
        source_items=source_items,
        local_files=[*archives, *extracted_files],
        generating_command="fetch.py --stages act_dr6_lensing --approve-downloads",
    )
    log("  [done] ACT DR6 lensing acquisition manifest written; no scientific inference was run.")


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
    if opts.get("desi_randoms"):
        for fname in s.get("randoms", []):
            download(f"{s['base']}/{fname}", raw / fname, log,
                     force=opts.get("force", False))
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
        log("  [info] CAMB not installed ??running pip install camb==1.6.6")
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


def stage_cf4_reconstructions(root: Path, sources: dict, log: Logger, **opts):
    """External velocity-field reconstructions for the CF4 reconstruction-method
    cross-check (REV-R196/R197). Carrick 2015 2M++ is a public direct download
    (an INDEPENDENT tracer + linear method). REV-R197 substitutes the blocked
    private Nusser 2026 2MRS reconstruction with TWO public 2MRS reconstructions
    from the Lilow group -- the LVN 2024 neural-network reconstruction and the
    CORAS 2021 Wiener-filter/constrained-realization reconstruction -- both
    shipped as public Dropbox folder zips. Nusser 2026 stays private (superseded,
    provenance note kept). Off-Dropbox targets if available."""
    s = sources.get("cf4_reconstructions", {})
    base = Path("/mnt/sn850x2t/htt_base_e2e") if Path(
        "/mnt/sn850x2t/htt_base_e2e").exists() else (root / "raw")

    # Carrick 2M++ (per-file public downloads)
    dest = Path(opts.get("cf4_recon_dir") or base / "carrick_2mpp")
    for name, url in s.get("carrick_2mpp", {}).get("files", {}).items():
        download(url, dest / name, log, optional=True)
    log(f"  [note] Carrick 2M++ velocity field -> {dest} (257^3, 400 Mpc/h).")

    # LVN 2024 NN + CORAS 2021 (public 2MRS reconstruction folder zips)
    for key, label, grid in (
        ("lilow_nn_2mrs", "Lilow-Veena-Nusser 2024 NN 2MRS", "128^3, 400 h^-1 Mpc, Galactic Cartesian, CMB frame"),
        ("coras_2mrs", "CORAS (Lilow-Nusser 2021) 2MRS", "201^3, +/-200 Mpc/h, comoving Galactic, zCMB/zLG"),
    ):
        cfg = s.get(key, {})
        url = os.environ.get(cfg.get("env_url_var", "")) or cfg.get("folder_zip")
        if url:
            zdest = base / key / cfg.get("zip_name", f"{key}.zip")
            ok = download(url, zdest, log, optional=True)
            if ok:
                log(f"  [note] {label} reconstruction -> {zdest} ({grid}). "
                    f"Unzip in place; grid parsed at analysis time.")
            else:
                log(f"  [blocked] {label}: {cfg.get('blocker', 'BLOCKED_MISSING_RECONSTRUCTION')} "
                    f"(folder zip fetch failed; set {cfg.get('env_url_var')}).")
        else:
            log(f"  [blocked] {label}: {cfg.get('blocker', 'BLOCKED_MISSING_RECONSTRUCTION')} "
                f"(no URL; set {cfg.get('env_url_var')}).")

    # Nusser 2026: private, superseded by the two public reconstructions above
    nurl = os.environ.get(s.get("nusser_2mrs", {}).get("env_url_var", "NUSSER_2MRS_URL"))
    if nurl:
        download(nurl, (base / "nusser_2mrs" / Path(nurl).name), log, optional=True)
    else:
        log("  [note] Nusser 2026 2MRS: SUPERSEDED_BY_LILOW_2024_PUBLIC "
            "(no public release; the LVN 2024 NN + CORAS 2021 reconstructions substitute).")


def stage_planck_npipe(root: Path, sources: dict, log: Logger, **opts):
    """Planck PR4/NPIPE maps for LR-06E (observer-boost / BipoSH).

    Fail-closed: auto-fetches only if a direct map URL is provided via the
    PLANCK_NPIPE_URL env var (the PLA serves maps through an interactive portal,
    not a plain file URL). The end-to-end NPIPE simulation ensemble required to
    CALIBRATE boost injection recovery is not downloaded here; LR-06E calibration
    stays BLOCKED_MISSING_E2E_SIMULATIONS until those sims are bound.
    """
    s = sources["planck_npipe"]
    url = os.environ.get(s.get("env_url_var", "PLANCK_NPIPE_URL"))
    out_dir = root / "raw" / "planck_npipe"
    if url:
        out_dir.mkdir(parents=True, exist_ok=True)
        download(url, out_dir / Path(url).name, log, optional=True)
        log("  [note] NPIPE map fetched; LR-06E boost calibration still needs the E2E sim ensemble.")
    else:
        log("  [manual] PR4/NPIPE maps require the PLA portal; set PLANCK_NPIPE_URL for a direct map.")
        log(f"           Portal: {s['project_page']}")
        log("  [blocked] LR-06E calibration: BLOCKED_MISSING_E2E_SIMULATIONS (sim ensemble not bound).")


# Stage registry
STAGES = {
    "env":            stage_env,
    "cf4_full":       stage_cf4_full,
    "cf4_reconstructions": stage_cf4_reconstructions,
    "planck_npipe":   stage_planck_npipe,
    "planck_pr3":     stage_planck_pr3,
    "bicep_keck":     stage_bicep_keck,
    "planck_lensing": stage_planck_lensing,
    "act_dr4":        stage_act_dr4,
    "act_dr6":        stage_act_dr6,
    "act_dr6_lensing": stage_act_dr6_lensing,
    "spt3g_y1":       stage_spt3g_y1,
    "desi_y1":        stage_desi_y1,
    "cf4":            stage_cf4,
    "camb_refs":      stage_camb_refs,
    "scalars":        stage_scalars,
    "package":        stage_package,
}


# ??????????????????????????????????????????????????????????????????????????
# CLI
# ??????????????????????????????????????????????????????????????????????????

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
                         "the canonical low-??pixel-likelihood resolution).")
    ap.add_argument("--full-res-maps", action="store_true",
                    help="Also dump full-resolution (NSIDE=2048) Planck map/mask "
                         "NPZs alongside the downgraded ones (~200 MB per map).")
    ap.add_argument("--desi-randoms", action="store_true",
                    help="also download the DESI DR1 BGS random catalogues "
                         "(desi_y1.randoms) for EXT-DESI window deconvolution")
    ap.add_argument("--act-sims", action="store_true",
                    help="download the ACT DR6 lensing baseline reconstruction "
                         "sims (~59.6 GB) for the EXT-ACT low-ell kappa mean "
                         "field; goes off-Dropbox by default")
    ap.add_argument("--act-sims-dir", default=None,
                    help="target dir for --act-sims (default: "
                         "/mnt/sn850x2t/htt_base_e2e/act_dr6_lensing_sims if "
                         "the NVMe is present, else "
                         "<root>/downloads/act_dr6_lensing_sims)")
    ap.add_argument("--desi-mode", choices=["minimal", "extended"], default="extended",
                    help="DESI column set ??extended (default) keeps all weights + "
                         "targetid/ntile/photsys; minimal strips to ra/dec/z/weight/n_hat.")
    ap.add_argument("--approve-downloads", action="store_true",
                    help="allow newly added approval-gated external download stages")
    ap.add_argument("--download-inventory", default=None,
                    help="write a JSON/Markdown download inventory for the selected plan and exit")
    ap.add_argument("--probe-network", action="store_true",
                    help="resolve source pages and probe remote Content-Length for --download-inventory")
    ap.add_argument("--max-download-gb", type=float, default=50.0,
                    help="download inventory budget ceiling in GB (default 50)")
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
    log(f"BASS data pipeline ??root={root}")
    log(f"plan: {' ??'.join(plan)}")
    log(f"options: force={args.force}  skip_heavy={args.skip_heavy}  "
        f"skip_large_maps={args.skip_large_maps}  dry_run={args.dry_run}")
    log("=" * 70)

    cap_bytes = int(args.max_download_gb * 1024**3)
    if args.download_inventory:
        inventory = build_download_inventory(
            sources,
            root,
            plan,
            max_download_bytes=cap_bytes,
            probe_network=args.probe_network,
        )
        json_path, md_path = write_inventory_outputs(inventory, Path(args.download_inventory))
        log(f"  [inventory] wrote {json_path}")
        log(f"  [inventory] wrote {md_path}")
        log(f"  [inventory] known additional GB: {inventory['known_additional_gb']:.3f}")
        if not inventory["within_cap_for_known_sizes"]:
            log("  [FAIL] planned known downloads exceed configured cap")
            log.close()
            sys.exit(2)
        log.close()
        return

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
                desi_mode=args.desi_mode,
                desi_randoms=args.desi_randoms,
                act_sims=args.act_sims,
                act_sims_dir=args.act_sims_dir,
                approve_downloads=args.approve_downloads,
                max_download_bytes=cap_bytes)

    failed = []
    for sid in plan:
        log("")
        log(f"--- stage: {sid} ---")
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

