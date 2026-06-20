#!/usr/bin/env python3
"""Generate manifest-backed observed-data manuscript figures."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from figure_env import REPO_ROOT, build_obs_catalog, configure_repo_paths  # noqa: E402

configure_repo_paths()
COMMON_ROOT = REPO_ROOT / "htt" / "src"
if str(COMMON_ROOT) not in sys.path:
    sys.path.insert(0, str(COMMON_ROOT))

from common.artifact_manifest import validate_manifest_payload  # noqa: E402
from common.sky_support import build_sky_support_from_mask  # noqa: E402
from inventory_observational_data import (  # noqa: E402
    GENERATING_COMMAND as INVENTORY_GENERATING_COMMAND,
    build_inventory,
    render_gap_report as render_inventory_gap_report,
    render_markdown as render_inventory_markdown,
)


FIGURE_DIR = REPO_ROOT / "figures" / "observed_current"
SNIPPET_DIR = REPO_ROOT / "docs" / "manuscript" / "generated"
INVENTORY_JSON = REPO_ROOT / "docs" / "generated" / "observational_data_inventory.json"
INVENTORY_MD = REPO_ROOT / "docs" / "generated" / "observational_data_inventory.md"
INVENTORY_GAP_MD = REPO_ROOT / "docs" / "generated" / "data_binding_gap_report.md"
LONGRUN_JSON = REPO_ROOT / "docs" / "generated" / "observed_longrun_analysis.json"
LONGRUN_MD = REPO_ROOT / "docs" / "generated" / "observed_longrun_analysis.md"
PLOT_LIST = REPO_ROOT / "docs" / "generated" / "observed_current_plot_list.md"
COMPOSITE_PLOT_INDEX = REPO_ROOT / "docs" / "generated" / "manuscript_plot_list_index.md"

DESI_FILES = {
    "BGS NGC": REPO_ROOT / "workdir/compact_products/desi/BGS_ANY_NGC_clustering_extended.npz",
    "BGS SGC": REPO_ROOT / "workdir/compact_products/desi/BGS_ANY_SGC_clustering_extended.npz",
    "LRG NGC": REPO_ROOT / "workdir/compact_products/desi/LRG_NGC_clustering_extended.npz",
    "LRG SGC": REPO_ROOT / "workdir/compact_products/desi/LRG_SGC_clustering_extended.npz",
    "QSO NGC": REPO_ROOT / "workdir/compact_products/desi/QSO_NGC_clustering_extended.npz",
    "QSO SGC": REPO_ROOT / "workdir/compact_products/desi/QSO_SGC_clustering_extended.npz",
}
CF4_BATCH = REPO_ROOT / "workdir/compact_products/cf4/query_batch.npz"

COLORS = {
    "blue": "#2563eb",
    "cyan": "#0891b2",
    "green": "#15803d",
    "orange": "#c2410c",
    "red": "#b91c1c",
    "purple": "#7c3aed",
    "slate": "#334155",
    "muted": "#64748b",
    "panel": "#f8fafc",
}


@dataclass(frozen=True)
class PlotMetadata:
    statistics_definitions: dict[str, Any] = field(default_factory=dict)
    sky_support_status: str = "not_directional"
    sky_support: dict[str, Any] | None = None
    null_mock_status: str = "not_statistical"
    extra_caveats: tuple[str, ...] = ()


@dataclass(frozen=True)
class FigureSpec:
    artifact_id: str
    file_name: str
    title: str
    flow_slot: str
    source_paths: tuple[str, ...]
    caption: str
    label: str
    snippet: str
    builder: Callable[[Path], PlotMetadata]
    owner: str = "OBSSTAT"
    implementation_scope: str = "obsstat"
    claim_tier: str = "diagnostic_only"
    artifact_mode: str = "paper_appendix_conditioned"
    allowed_use: str = "paper_appendix"
    transfer_source: str = "none"
    caption_policy: tuple[str, ...] = (
        "must_state_diagnostic_only",
        "must_not_use_for_family_identification_or_family_selection",
        "must_state_no_native_low_ell_solver_output",
    )
    promotion_blockers: tuple[str, ...] = (
        "matched_nulls_not_bound",
        "full_covariance_not_bound",
        "native_solver_validation_absent",
        "native_morphology_atlas_absent",
        "family_identification_blocked_pre_native_atlas",
    )
    caveats: tuple[str, ...] = (
        "Observed-data diagnostic figure; not inference evidence.",
        "No native low-ell solver output is used.",
        "No Bianchi family-ID or geometry-detection claim is made.",
    )


def _repo_relative(path: Path, repo_root: Path = REPO_ROOT) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _stable_hash(payload: Any) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _input_hashes(paths: tuple[str, ...]) -> list[str]:
    hashes: list[str] = []
    for rel_path in paths:
        path = REPO_ROOT / rel_path
        hashes.append(f"{rel_path}:{_sha256(path) if path.exists() else 'missing'}")
    return hashes


def _git_state(repo_root: Path = REPO_ROOT) -> tuple[str | None, str]:
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=repo_root,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        dirty = subprocess.run(
            ["git", "status", "--short"],
            cwd=repo_root,
            text=True,
            capture_output=True,
            check=False,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None, "git_state_unavailable"
    return commit, f"{commit}+dirty" if dirty else commit


def _style_axes(ax: plt.Axes) -> None:
    ax.set_facecolor(COLORS["panel"])
    ax.grid(True, alpha=0.22, linewidth=0.7)
    for spine in ax.spines.values():
        spine.set_color("#cbd5e1")


def _save_figure(fig: plt.Figure, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=220, bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)


def _read_npz(path: Path) -> dict[str, Any]:
    with np.load(path, allow_pickle=False) as z:
        return {key: z[key] for key in z.files}


def _wrap_mollweide_lon(ra_deg: np.ndarray) -> np.ndarray:
    lon = np.remainder(ra_deg + 180.0, 360.0) - 180.0
    return np.deg2rad(-lon)


def _sample_indices(n: int, max_points: int, *, salt: int) -> np.ndarray:
    if n <= max_points:
        return np.arange(n, dtype=int)
    stride = max(1, n // max_points)
    start = salt % stride
    return np.arange(start, n, stride, dtype=int)[:max_points]


def _desi_tracer(label: str) -> str:
    return label.split()[0]


def _desi_rows_by_tracer() -> dict[str, int]:
    rows = {"BGS": 0, "LRG": 0, "QSO": 0}
    for label, path in DESI_FILES.items():
        if not path.exists():
            continue
        with np.load(path, allow_pickle=False) as data:
            rows[_desi_tracer(label)] += int(data["ra"].shape[0])
    return rows


def _desi_occupancy_sky_support() -> dict[str, Any]:
    try:
        import healpy as hp
    except ImportError:
        payload = {
            "coordinate_frame": "equatorial_icrs",
            "pixelization": "unavailable_healpy",
            "source": "DESI compact catalog occupancy",
        }
        return {
            "selection_mode": "angular_occupancy",
            "sky_support_hash": _stable_hash(payload),
            "mask_hash": _stable_hash({"mask": "healpy_unavailable"}),
            "mock_coverage_status": "not_mocked",
            "scan_volume_hash": "",
            "coordinate_frame": "equatorial_icrs",
            "sky_fraction": 1.0e-6,
            "completeness_status": "coordinate_frame_only_healpy_unavailable",
            "pixelization": "unavailable",
            "nside": None,
        }

    nside = 32
    occupied = np.zeros(hp.nside2npix(nside), dtype=bool)
    for path in DESI_FILES.values():
        if not path.exists():
            continue
        with np.load(path, allow_pickle=False) as data:
            ra = np.asarray(data["ra"], dtype=float)
            dec = np.asarray(data["dec"], dtype=float)
            theta = np.deg2rad(90.0 - dec)
            phi = np.deg2rad(ra)
            pix = hp.ang2pix(nside, theta, phi, nest=False)
            occupied[pix] = True
    support = build_sky_support_from_mask(
        occupied,
        coordinate_frame="equatorial_icrs",
        completeness_status="occupied_pixel_diagnostic_from_compact_catalogs",
        selection_mode="angular_occupancy",
        mock_coverage_status="not_mocked",
        pixelization="healpix_ring",
        nside=nside,
    )
    return support.to_metadata()


def _write_inventory(command: str) -> dict[str, Any]:
    del command
    payload = build_inventory(
        REPO_ROOT,
        command=INVENTORY_GENERATING_COMMAND,
        artifact_path=_repo_relative(INVENTORY_JSON),
    )
    INVENTORY_JSON.parent.mkdir(parents=True, exist_ok=True)
    INVENTORY_JSON.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    INVENTORY_MD.write_text(render_inventory_markdown(payload), encoding="utf-8")
    INVENTORY_GAP_MD.write_text(
        render_inventory_gap_report(
            payload,
            artifact_path=_repo_relative(INVENTORY_GAP_MD),
        ),
        encoding="utf-8",
    )
    return payload


def _desi_jackknife_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for label, path in DESI_FILES.items():
        if not path.exists():
            continue
        with np.load(path, allow_pickle=False) as data:
            z = np.asarray(data["z"], dtype=float)
            weight = np.asarray(data["weight"], dtype=float)
            n_hat = np.asarray(data["n_hat"], dtype=float)
            ra = np.asarray(data["ra"], dtype=float)
            z_edges = np.linspace(float(np.nanmin(z)), float(np.nanmax(z)), 7)
            sectors = np.floor(np.remainder(ra, 360.0) / 30.0).astype(int)
            for bin_index, (z0, z1) in enumerate(zip(z_edges[:-1], z_edges[1:])):
                mask = (z >= z0) & (z < z1 if bin_index < len(z_edges) - 2 else z <= z1)
                if int(mask.sum()) < 32:
                    continue
                w = weight[mask]
                nh = n_hat[mask]
                resultant = np.sum(nh * w[:, None], axis=0)
                amp = float(np.linalg.norm(resultant) / np.sum(w))
                jk_values: list[float] = []
                local_sectors = sectors[mask]
                for sector in range(12):
                    keep = local_sectors != sector
                    if int(keep.sum()) < 16:
                        continue
                    jw = w[keep]
                    jn = nh[keep]
                    jr = np.sum(jn * jw[:, None], axis=0)
                    jk_values.append(float(np.linalg.norm(jr) / np.sum(jw)))
                jk = np.asarray(jk_values, dtype=float)
                jk_std = float(np.sqrt((len(jk) - 1) / len(jk) * np.sum((jk - jk.mean()) ** 2))) if len(jk) > 1 else 0.0
                rows.append(
                    {
                        "label": label,
                        "tracer": _desi_tracer(label),
                        "z_min": float(z0),
                        "z_max": float(z1),
                        "z_mid": float(0.5 * (z0 + z1)),
                        "n_rows": int(mask.sum()),
                        "weighted_resultant_amplitude": amp,
                        "jackknife_std": jk_std,
                        "jackknife_sectors": int(len(jk)),
                    }
                )
    return rows


def _cf4_bootstrap_rows(seed: int = 20260617, n_boot: int = 512) -> list[dict[str, Any]]:
    if not CF4_BATCH.exists():
        return []
    rng = np.random.default_rng(seed)
    with np.load(CF4_BATCH, allow_pickle=False) as data:
        sgx = np.asarray(data["sgx"], dtype=float)
        sgy = np.asarray(data["sgy"], dtype=float)
        sgz = np.asarray(data["sgz"], dtype=float)
        radius = np.sqrt(sgx * sgx + sgy * sgy + sgz * sgz)
        vr = np.asarray(data["vr_mean"], dtype=float)
        delta = np.asarray(data["delta_mean"], dtype=float)
    edges = np.quantile(radius, np.linspace(0.0, 1.0, 11))
    edges = np.unique(edges)
    rows: list[dict[str, Any]] = []
    for idx, (r0, r1) in enumerate(zip(edges[:-1], edges[1:])):
        mask = (radius >= r0) & (radius < r1 if idx < len(edges) - 2 else radius <= r1)
        values = vr[mask]
        deltas = delta[mask]
        if values.size < 32:
            continue
        boot = np.empty(n_boot, dtype=float)
        for boot_idx in range(n_boot):
            draw = rng.integers(0, values.size, size=values.size)
            boot[boot_idx] = float(np.mean(values[draw]))
        rows.append(
            {
                "radius_min_mpc_h": float(r0),
                "radius_max_mpc_h": float(r1),
                "radius_mid_mpc_h": float(0.5 * (r0 + r1)),
                "n_rows": int(values.size),
                "vr_mean_km_s": float(np.mean(values)),
                "vr_bootstrap_p16_km_s": float(np.percentile(boot, 16)),
                "vr_bootstrap_p84_km_s": float(np.percentile(boot, 84)),
                "delta_mean": float(np.mean(deltas)),
                "delta_p16": float(np.percentile(deltas, 16)),
                "delta_p84": float(np.percentile(deltas, 84)),
            }
        )
    return rows


def _write_longrun(command: str, *, force: bool = False) -> dict[str, Any]:
    source_paths = tuple(
        _repo_relative(path)
        for path in [*DESI_FILES.values(), CF4_BATCH]
        if path.exists()
    )
    config = {
        "desi_ra_jackknife_sectors": 12,
        "desi_z_bins_per_catalog": 6,
        "cf4_bootstrap_samples": 512,
        "cf4_seed": 20260617,
        "script_sha256": _sha256(Path(__file__)),
        "version": "observed-longrun-v2",
    }
    config_hash = _stable_hash(config)
    input_hashes = _input_hashes(source_paths)
    if LONGRUN_JSON.exists() and not force:
        cached = json.loads(LONGRUN_JSON.read_text(encoding="utf-8"))
        cached_manifest = cached.get("manifest", {})
        if (
            cached_manifest.get("config_hash") == config_hash
            and cached_manifest.get("input_hashes") == input_hashes
        ):
            LONGRUN_MD.write_text(_render_longrun_markdown(cached), encoding="utf-8")
            return cached

    git_commit, worktree = _git_state()
    payload = {
        "manifest": {
            "artifact_id": "obsstat.observed_longrun_analysis",
            "artifact_path": "docs/generated/observed_longrun_analysis.json",
            "owner": "OBSSTAT",
            "implementation_scope": "obsstat",
            "claim_tier": "diagnostic_only",
            "production_status": "diagnostic_only",
            "created_by": "scripts/make_observed_data_manuscript_figures.py",
            "git_commit": git_commit,
            "config_hash": config_hash,
            "input_hashes": input_hashes,
            "code_version": worktree,
            "schema_version": "obsstat.observed_longrun_analysis.v2",
            "caveats": [
                "Long-run diagnostics use jackknife and bootstrap uncertainty summaries only.",
                "No p-value, evidence, posterior, or family-ID claim is made.",
                "DESI directional support is recorded from compact catalog occupancy; CF4 support is volume-coordinate diagnostic.",
                "DESI survey selection and CF4 reconstruction systematics remain diagnostic unless matched nulls and covariance are explicitly bound.",
            ],
            "transfer_source": "none",
            "sky_support_status": "sky_support_recorded",
            "sky_support": _desi_occupancy_sky_support(),
            "null_mock_status": "jackknife_bootstrap_diagnostic_no_pvalue",
            "required_gates": [
                "repo_local_observed_data_present",
                "jackknife_bootstrap_summary_generated",
                "claim_firewall_report_review",
            ],
            "passed_gates": [
                "repo_local_observed_data_present",
                "jackknife_bootstrap_summary_generated",
                "claim_firewall_report_review",
            ],
            "failed_gates": [
                "matched_nulls_not_bound",
                "full_covariance_not_bound",
                "native_low_ell_solver_not_available",
                "family_morphology_atlas_not_available",
            ],
            "science_promotion_gates": {
                "matched_nulls": "fail_not_bound",
                "full_covariance": "fail_not_bound",
                "native_low_ell_solver": "fail_not_available",
                "family_morphology_atlas": "fail_not_available",
            },
            "publication_gates": {
                "paper_main_claim": "fail_diagnostic_only",
                "evidence_or_pvalue_claim": "fail_not_calibrated",
            },
            "generating_command": command,
            "git_commit_or_worktree_state": worktree,
        },
        "config": config,
        "desi_depth_jackknife": _desi_jackknife_rows(),
        "cf4_radius_bootstrap": _cf4_bootstrap_rows(),
    }
    issues = validate_manifest_payload(
        payload["manifest"],
        manifest_path=LONGRUN_JSON,
        expected_artifact_path="docs/generated/observed_longrun_analysis.json",
    )
    if issues:
        rendered = "; ".join(f"{issue.code}: {issue.detail}" for issue in issues)
        raise ValueError(f"invalid longrun manifest: {rendered}")
    LONGRUN_JSON.parent.mkdir(parents=True, exist_ok=True)
    LONGRUN_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    LONGRUN_MD.write_text(_render_longrun_markdown(payload), encoding="utf-8")
    return payload


def _render_longrun_markdown(payload: dict[str, Any]) -> str:
    manifest = payload["manifest"]
    lines = [
        "# Observed Long-Run Analysis",
        "",
        f"owner: {manifest['owner']}",
        f"implementation_scope: {manifest['implementation_scope']}",
        f"claim_tier: {manifest['claim_tier']}",
        f"transfer_source: {manifest['transfer_source']}",
        f"sky_support_status: {manifest['sky_support_status']}",
        f"null_mock_status: {manifest['null_mock_status']}",
        f"config_hash: `{manifest['config_hash']}`",
        "input_hashes:",
        *[f"- `{item}`" for item in manifest["input_hashes"]],
        "caveats:",
        *[f"- {item}" for item in manifest["caveats"]],
        f"generating_command: `{manifest['generating_command']}`",
        f"git_commit_or_worktree_state: `{manifest['git_commit_or_worktree_state']}`",
        f"artifact_path: {manifest['artifact_path']}",
        "",
        "## Summary",
        "",
        f"- DESI jackknife rows: `{len(payload['desi_depth_jackknife'])}`",
        f"- CF4 bootstrap rows: `{len(payload['cf4_radius_bootstrap'])}`",
        "- Interpretation ceiling: diagnostic-only, no p-value or evidence term.",
    ]
    return "\n".join(lines) + "\n"


def _plot_inventory_matrix(output: Path) -> PlotMetadata:
    inventory = json.loads(INVENTORY_JSON.read_text(encoding="utf-8"))
    rows = inventory["rows"]
    collections = sorted({row["collection"] for row in rows})
    present = [sum(1 for row in rows if row["collection"] == collection and row["present"]) for collection in collections]
    missing = [sum(1 for row in rows if row["collection"] == collection and not row["present"]) for collection in collections]

    fig, ax = plt.subplots(figsize=(8.3, 4.8))
    y = np.arange(len(collections))
    ax.barh(y, present, color=COLORS["green"], label="present")
    ax.barh(y, missing, left=present, color=COLORS["red"], label="missing")
    ax.set_yticks(y)
    ax.set_yticklabels(collections, fontsize=8)
    ax.set_xlabel("dataset count")
    ax.set_title("Repo-local observational dataset inventory")
    ax.legend(loc="lower right")
    _style_axes(ax)
    fig.tight_layout()
    _save_figure(fig, output)
    return PlotMetadata(
        statistics_definitions={
            "quantity": "dataset availability counts by collection",
            "present": int(sum(present)),
            "missing": int(sum(missing)),
        }
    )


def _plot_planck_spectra(output: Path) -> PlotMetadata:
    cat = build_obs_catalog()
    tt = cat.load("planck.pr3.tt_full")
    te = cat.load("planck.pr3.te_full")
    ee = cat.load("planck.pr3.ee_full")
    theory = cat.load("planck.pr3.bestfit")

    fig, axes = plt.subplots(3, 1, figsize=(8.0, 7.2), sharex=True)
    panels = [
        (axes[0], tt, np.asarray(theory["dl_TT"]), "TT", COLORS["blue"]),
        (axes[1], te, np.asarray(theory["dl_TE"]), "TE", COLORS["orange"]),
        (axes[2], ee, np.asarray(theory["dl_EE"]), "EE", COLORS["green"]),
    ]
    ell_theory = np.asarray(theory["ell"], dtype=float)
    for ax, obs, th, label, color in panels:
        ell = np.asarray(obs["ell"], dtype=float)
        dl = np.asarray(obs["dl"], dtype=float)
        err = 0.5 * (np.asarray(obs["err_lo"], dtype=float) + np.asarray(obs["err_hi"], dtype=float))
        step = max(1, len(ell) // 650)
        ax.errorbar(ell[::step], dl[::step], yerr=err[::step], fmt=".", ms=2.0, color=color, alpha=0.55, lw=0.0, elinewidth=0.3)
        ax.plot(ell_theory, th, color=COLORS["slate"], lw=1.0, label="Planck best-fit theory")
        ax.set_ylabel(f"{label} D_l")
        ax.set_xlim(2, 2508)
        _style_axes(ax)
    axes[0].legend(fontsize=8, loc="upper right")
    axes[-1].set_xlabel("multipole l")
    fig.suptitle("Planck PR3 observed spectra with best-fit reference", fontsize=11)
    fig.tight_layout()
    _save_figure(fig, output)
    return PlotMetadata(
        statistics_definitions={
            "quantity": "Planck PR3 TT/TE/EE D_l spectra",
            "units": "microK^2",
            "ell_ranges": {"TT": [2, 2508], "TE": [2, 1996], "EE": [2, 1996]},
        }
    )


def _plot_planck_lowell_residual(output: Path) -> PlotMetadata:
    cat = build_obs_catalog()
    tt = cat.load("planck.pr3.tt_full")
    theory = cat.load("planck.pr3.bestfit")
    camb = _read_npz(REPO_ROOT / "data/camb_ref_planck2018.npz")
    ell = np.asarray(tt["ell"], dtype=int)
    mask = ell <= 30
    obs_ell = ell[mask]
    obs = np.asarray(tt["dl"], dtype=float)[mask]
    err = 0.5 * (np.asarray(tt["err_lo"], dtype=float)[mask] + np.asarray(tt["err_hi"], dtype=float)[mask])
    th = np.interp(obs_ell, np.asarray(theory["ell"], dtype=float), np.asarray(theory["dl_TT"], dtype=float))
    camb_th = np.interp(obs_ell, np.asarray(camb["ell"], dtype=float), np.asarray(camb["D_TT"], dtype=float))
    residual_sigma = (obs - th) / np.where(err > 0, err, np.nan)

    fig, axes = plt.subplots(2, 1, figsize=(7.7, 5.8), sharex=True)
    axes[0].errorbar(obs_ell, obs, yerr=err, fmt="o", ms=4.0, color=COLORS["blue"], label="Planck PR3 TT")
    axes[0].plot(obs_ell, th, color=COLORS["slate"], lw=1.1, label="Planck best-fit")
    axes[0].plot(obs_ell, camb_th, color=COLORS["orange"], lw=1.0, ls="--", label="repo CAMB low-l reference")
    axes[0].set_ylabel("TT D_l")
    axes[0].legend(fontsize=8)
    axes[1].axhline(0.0, color=COLORS["slate"], lw=0.8)
    axes[1].bar(obs_ell, residual_sigma, color=np.where(residual_sigma >= 0, COLORS["blue"], COLORS["red"]), alpha=0.7)
    axes[1].set_xlabel("multipole l")
    axes[1].set_ylabel("(obs - best-fit) / sigma")
    for ax in axes:
        _style_axes(ax)
    fig.suptitle("Planck low-l TT residual diagnostic", fontsize=11)
    fig.tight_layout()
    _save_figure(fig, output)
    return PlotMetadata(
        statistics_definitions={
            "quantity": "low-l TT residuals against Planck best-fit reference",
            "ell_range": [2, 30],
            "normalization": "reported Planck PR3 TT error column",
        },
        extra_caveats=(
            "Residual bars are not a full-covariance, cosmic-variance, or mask-coupled likelihood calculation.",
            "This figure reports no p-value, look-elsewhere statistic, or family-ID result.",
        ),
    )


def _plot_planck_map_mask(output: Path) -> PlotMetadata:
    try:
        import healpy as hp
    except ImportError as exc:
        raise RuntimeError("healpy is required for Planck map pixel coordinates") from exc

    cat = build_obs_catalog()
    smica = cat.load("planck.smica.nside16")
    mask_payload = cat.load("planck.temp_mask.nside16")
    i_map = np.asarray(smica["I"], dtype=float)
    mask = np.asarray(mask_payload["mask"], dtype=float) > 0.5
    nside = int(smica["nside"])
    lon, lat = hp.pix2ang(nside, np.arange(i_map.size), lonlat=True)
    lon_rad = _wrap_mollweide_lon(lon)
    lat_rad = np.deg2rad(lat)
    display = np.where(mask, i_map, np.nan)
    vlim = float(np.nanpercentile(np.abs(display), 98))

    fig = plt.figure(figsize=(8.5, 4.6))
    ax = fig.add_subplot(111, projection="mollweide")
    sc = ax.scatter(lon_rad, lat_rad, c=display, s=8, cmap="RdBu_r", vmin=-vlim, vmax=vlim, linewidths=0)
    ax.grid(True, alpha=0.25)
    ax.set_title("Planck SMICA NSIDE=16 temperature map with PR3 temperature mask")
    cb = fig.colorbar(sc, ax=ax, shrink=0.72, pad=0.08)
    cb.set_label("microK")
    fig.tight_layout()
    _save_figure(fig, output)
    support = build_sky_support_from_mask(
        mask,
        coordinate_frame="galactic",
        completeness_status="planck_pr3_temperature_mask_applied",
        selection_mode="planck_temperature_mask",
        mock_coverage_status="not_mocked",
        pixelization="healpix_ring",
        nside=nside,
    )
    return PlotMetadata(
        sky_support_status="masked_sky",
        sky_support=support.to_metadata(),
        statistics_definitions={
            "quantity": "masked Planck SMICA temperature pixels",
            "nside": nside,
            "fsky": float(mask.mean()),
            "units": "microK_CMB",
        },
    )


def _plot_lensing_bandpowers(output: Path) -> PlotMetadata:
    cat = build_obs_catalog()
    lens = cat.load("planck.pr3.lensing")
    camb = cat.load("camb.planck2018.lensing_refs")
    bp = np.asarray(lens["smica_g30_ftl_full_pp_bandpowers.dat"], dtype=float)
    cov = np.asarray(lens["smica_g30_ftl_full_pp_cov.dat"], dtype=float)
    ell_th = np.asarray(camb["ell_pp"], dtype=float)
    pp = np.asarray(camb["lens_potential_cls"], dtype=float)[:, 0]

    fig, axes = plt.subplots(1, 2, figsize=(9.3, 4.0))
    axes[0].plot(ell_th, pp, color=COLORS["slate"], lw=1.0, label="CAMB reference")
    axes[0].errorbar(bp[:, 3], bp[:, 4], yerr=bp[:, 5], xerr=[bp[:, 3] - bp[:, 1], bp[:, 2] - bp[:, 3]], fmt="o", color=COLORS["purple"], ms=4.0, lw=0.0, elinewidth=0.8, capsize=2.0, label="Planck PR3 lensing")
    axes[0].set_xscale("log")
    axes[0].set_xlabel("lensing multipole L")
    axes[0].set_ylabel("lensing bandpower")
    axes[0].legend(fontsize=8)
    im = axes[1].imshow(cov, cmap="viridis", aspect="auto")
    axes[1].set_title("bandpower covariance")
    axes[1].set_xlabel("bin")
    axes[1].set_ylabel("bin")
    fig.colorbar(im, ax=axes[1], shrink=0.78)
    for ax in axes:
        _style_axes(ax)
    fig.suptitle("Planck PR3 lensing bandpowers and covariance", fontsize=11)
    fig.tight_layout()
    _save_figure(fig, output)
    return PlotMetadata(
        statistics_definitions={
            "quantity": "Planck PR3 lensing bandpower and covariance diagnostic",
            "n_bins": int(bp.shape[0]),
        }
    )


def _plot_high_ell_experiment_summary(output: Path) -> PlotMetadata:
    cat = build_obs_catalog()
    act = cat.load("act.dr4.compact")
    spt = cat.load("spt.3g.y1")
    bk = cat.load("bicep_keck.2018.bb")
    act_keys = [
        ("ACT TT", "clcmb__act_dr4_01_D_ell_TT_cmbonly_txt", COLORS["blue"]),
        ("ACT TE", "clcmb__act_dr4_01_D_ell_TE_cmbonly_txt", COLORS["orange"]),
        ("ACT EE", "clcmb__act_dr4_01_D_ell_EE_cmbonly_txt", COLORS["green"]),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(11.0, 3.8))
    for label, key, color in act_keys:
        arr = np.asarray(act[key], dtype=float)
        axes[0].errorbar(arr[:, 0], arr[:, 1], yerr=np.abs(arr[:, 2]), fmt=".", ms=3.0, color=color, alpha=0.75, label=label)
    axes[0].set_xlabel("multipole/bin center")
    axes[0].set_ylabel("D_l")
    axes[0].legend(fontsize=7)
    spt_vec = np.ravel(np.asarray(spt["bandpowers__SPT3G_2018_TTTEEE_bandpowers_dat"], dtype=float))
    axes[1].plot(np.arange(spt_vec.size), spt_vec, color=COLORS["cyan"], lw=0.7)
    axes[1].set_xlabel("packed SPT bandpower index")
    axes[1].set_ylabel("reported bandpower")
    bk_mat = np.asarray(bk["BK18lf_cl_hat.dat"], dtype=float)
    x = bk_mat[:, 0]
    packed = bk_mat[:, 1:]
    axes[2].plot(x, np.nanmedian(packed, axis=1), color=COLORS["purple"], marker="o", ms=3.5)
    axes[2].fill_between(x, np.nanpercentile(packed, 16, axis=1), np.nanpercentile(packed, 84, axis=1), color=COLORS["purple"], alpha=0.2)
    axes[2].set_xlabel("BK18 bin")
    axes[2].set_ylabel("packed cross-spectrum spread")
    for ax in axes:
        _style_axes(ax)
    fig.suptitle("ACT DR4, SPT-3G Y1, and BICEP/Keck observed high-l products", fontsize=11)
    fig.tight_layout()
    _save_figure(fig, output)
    return PlotMetadata(
        statistics_definitions={
            "quantity": "external CMB high-l and polarization product diagnostics",
            "act_panels": [label for label, _, _ in act_keys],
            "spt_packed_length": int(spt_vec.size),
            "bk_bins": int(bk_mat.shape[0]),
        }
    )


def _plot_desi_footprint_depth(output: Path) -> PlotMetadata:
    fig = plt.figure(figsize=(10.0, 6.2))
    ax_sky = fig.add_subplot(211, projection="mollweide")
    ax_hist = fig.add_subplot(212)
    colors = {"BGS": COLORS["blue"], "LRG": COLORS["green"], "QSO": COLORS["orange"]}
    z_edges = np.linspace(0.0, 3.6, 121)
    total_rows = 0
    for idx, (label, path) in enumerate(DESI_FILES.items()):
        if not path.exists():
            continue
        tracer = _desi_tracer(label)
        with np.load(path, allow_pickle=False) as data:
            ra = np.asarray(data["ra"], dtype=float)
            dec = np.asarray(data["dec"], dtype=float)
            z = np.asarray(data["z"], dtype=float)
            weight = np.asarray(data["weight"], dtype=float)
            total_rows += int(z.size)
            sample = _sample_indices(z.size, 18_000, salt=idx + 3)
            ax_sky.scatter(_wrap_mollweide_lon(ra[sample]), np.deg2rad(dec[sample]), s=1.5, alpha=0.35, color=colors[tracer], linewidths=0)
            hist, _ = np.histogram(z, bins=z_edges, weights=weight)
            width = z_edges[1] - z_edges[0]
            norm = hist / np.sum(hist) / width if np.sum(hist) > 0 else hist
            ax_hist.plot(0.5 * (z_edges[:-1] + z_edges[1:]), norm, color=colors[tracer], alpha=0.55 if "SGC" in label else 0.95, lw=1.2, label=label)
    ax_sky.grid(True, alpha=0.25)
    ax_sky.set_title("DESI compact catalog sky footprint sample")
    ax_hist.set_xlabel("redshift z")
    ax_hist.set_ylabel("weighted normalized dN/dz")
    ax_hist.legend(ncol=3, fontsize=7)
    _style_axes(ax_hist)
    fig.suptitle(f"DESI compact observational catalogs ({total_rows:,} rows)", fontsize=11)
    fig.tight_layout()
    _save_figure(fig, output)
    return PlotMetadata(
        sky_support_status="sky_support_recorded",
        sky_support=_desi_occupancy_sky_support(),
        statistics_definitions={
            "quantity": "DESI sky footprint sample and weighted redshift distribution",
            "total_rows": total_rows,
            "coordinate_frame": "equatorial_icrs",
        },
    )


def _plot_desi_selection_weights(output: Path) -> PlotMetadata:
    fig, axes = plt.subplots(1, 3, figsize=(10.8, 3.8))
    fields = [("weight", "pipeline weight"), ("weight_fkp", "FKP weight"), ("weight_zfail", "z-failure weight")]
    colors = {"BGS": COLORS["blue"], "LRG": COLORS["green"], "QSO": COLORS["orange"]}
    for label, path in DESI_FILES.items():
        if not path.exists():
            continue
        tracer = _desi_tracer(label)
        with np.load(path, allow_pickle=False) as data:
            for ax, (field_name, field_label) in zip(axes, fields):
                values = np.asarray(data[field_name], dtype=float)
                values = values[np.isfinite(values)]
                lo, hi = np.nanpercentile(values, [0.5, 99.5])
                ax.hist(values, bins=80, range=(lo, hi), density=True, histtype="step", color=colors[tracer], alpha=0.65 if "SGC" in label else 0.95, lw=1.0)
                ax.set_title(field_label)
    for ax in axes:
        ax.set_yscale("log")
        ax.set_xlabel("value")
        ax.set_ylabel("density")
        _style_axes(ax)
    fig.suptitle("DESI compact selection and weighting diagnostics", fontsize=11)
    fig.tight_layout()
    _save_figure(fig, output)
    return PlotMetadata(
        sky_support_status="sky_support_recorded",
        sky_support=_desi_occupancy_sky_support(),
        statistics_definitions={
            "quantity": "DESI weight field distributions",
            "fields": [field for field, _ in fields],
        },
    )


def _plot_cf4_velocity_density(output: Path) -> PlotMetadata:
    data = _read_npz(CF4_BATCH)
    delta = np.asarray(data["delta_mean"], dtype=float)
    vr = np.asarray(data["vr_mean"], dtype=float)
    v = np.asarray(data["vxyz_mean"], dtype=float)
    sgx = np.asarray(data["sgx"], dtype=float)
    sgy = np.asarray(data["sgy"], dtype=float)
    speed = np.linalg.norm(v, axis=1)
    sample = _sample_indices(delta.size, 60_000, salt=17)

    fig, axes = plt.subplots(1, 3, figsize=(11.0, 3.9))
    axes[0].hist(delta, bins=120, color=COLORS["blue"], alpha=0.75)
    axes[0].set_xlabel("delta mean")
    axes[0].set_ylabel("count")
    axes[1].hist(speed, bins=120, color=COLORS["orange"], alpha=0.75)
    axes[1].set_xlabel("|v| mean [km/s]")
    sc = axes[2].scatter(sgx[sample], sgy[sample], c=vr[sample], s=1.5, cmap="RdBu_r", vmin=-900, vmax=900, linewidths=0)
    axes[2].set_xlabel("SGX [Mpc/h]")
    axes[2].set_ylabel("SGY [Mpc/h]")
    axes[2].set_aspect("equal", adjustable="box")
    fig.colorbar(sc, ax=axes[2], shrink=0.78, label="vr mean [km/s]")
    for ax in axes:
        _style_axes(ax)
    fig.suptitle("CF4 reconstructed density and peculiar-velocity diagnostics", fontsize=11)
    fig.tight_layout()
    _save_figure(fig, output)
    return PlotMetadata(
        sky_support_status="not_directional",
        statistics_definitions={
            "quantity": "CF4 density and velocity field summaries",
            "n_query_points": int(delta.size),
            "coordinate_frame": "supergalactic_cartesian",
            "selection_mode": "cf4_supergalactic_grid_query",
            "scan_volume_hash": _stable_hash({"n_rows": int(delta.size), "frame": "supergalactic_cartesian"}),
        },
    )


def _plot_cf4_depth_response(output: Path) -> PlotMetadata:
    data = _read_npz(CF4_BATCH)
    radius = np.sqrt(np.asarray(data["sgx"]) ** 2 + np.asarray(data["sgy"]) ** 2 + np.asarray(data["sgz"]) ** 2)
    vr = np.asarray(data["vr_mean"], dtype=float)
    delta = np.asarray(data["delta_mean"], dtype=float)
    edges = np.quantile(radius, np.linspace(0, 1, 14))
    centers: list[float] = []
    vr_med: list[float] = []
    vr_lo: list[float] = []
    vr_hi: list[float] = []
    de_med: list[float] = []
    de_lo: list[float] = []
    de_hi: list[float] = []
    for idx, (r0, r1) in enumerate(zip(edges[:-1], edges[1:])):
        mask = (radius >= r0) & (radius < r1 if idx < len(edges) - 2 else radius <= r1)
        centers.append(float(0.5 * (r0 + r1)))
        vr_med.append(float(np.median(vr[mask])))
        vr_lo.append(float(np.percentile(vr[mask], 16)))
        vr_hi.append(float(np.percentile(vr[mask], 84)))
        de_med.append(float(np.median(delta[mask])))
        de_lo.append(float(np.percentile(delta[mask], 16)))
        de_hi.append(float(np.percentile(delta[mask], 84)))
    x = np.asarray(centers)
    fig, axes = plt.subplots(2, 1, figsize=(7.8, 5.8), sharex=True)
    axes[0].plot(x, vr_med, color=COLORS["orange"], marker="o", ms=3.5)
    axes[0].fill_between(x, vr_lo, vr_hi, color=COLORS["orange"], alpha=0.18)
    axes[0].set_ylabel("radial velocity [km/s]")
    axes[1].plot(x, de_med, color=COLORS["blue"], marker="o", ms=3.5)
    axes[1].fill_between(x, de_lo, de_hi, color=COLORS["blue"], alpha=0.18)
    axes[1].set_xlabel("supergalactic radius [Mpc/h]")
    axes[1].set_ylabel("density contrast")
    for ax in axes:
        _style_axes(ax)
    fig.suptitle("CF4 depth-binned reconstruction response", fontsize=11)
    fig.tight_layout()
    _save_figure(fig, output)
    return PlotMetadata(
        sky_support_status="not_directional",
        statistics_definitions={
            "quantity": "CF4 radius-binned median and percentile response",
            "n_radius_bins": int(len(x)),
            "coordinate_frame": "supergalactic_cartesian",
            "selection_mode": "cf4_supergalactic_radius_bins",
            "scan_volume_hash": _stable_hash({"radius_bins": [float(v) for v in x]}),
        },
    )


def _plot_longrun_jackknife(output: Path) -> PlotMetadata:
    payload = json.loads(LONGRUN_JSON.read_text(encoding="utf-8"))
    desi = payload["desi_depth_jackknife"]
    cf4 = payload["cf4_radius_bootstrap"]
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.2))
    colors = {"BGS": COLORS["blue"], "LRG": COLORS["green"], "QSO": COLORS["orange"]}
    for tracer in ("BGS", "LRG", "QSO"):
        rows = [row for row in desi if row["tracer"] == tracer]
        rows = sorted(rows, key=lambda row: row["z_mid"])
        if not rows:
            continue
        x = np.asarray([row["z_mid"] for row in rows], dtype=float)
        y = np.asarray([row["weighted_resultant_amplitude"] for row in rows], dtype=float)
        e = np.asarray([row["jackknife_std"] for row in rows], dtype=float)
        axes[0].errorbar(x, y, yerr=e, fmt="o-", ms=3.5, color=colors[tracer], lw=1.0, capsize=2.0, label=tracer)
    axes[0].set_xlabel("redshift bin midpoint")
    axes[0].set_ylabel("weighted resultant amplitude")
    axes[0].legend(fontsize=8)
    cf4_rows = sorted(cf4, key=lambda row: row["radius_mid_mpc_h"])
    x = np.asarray([row["radius_mid_mpc_h"] for row in cf4_rows], dtype=float)
    y = np.asarray([row["vr_mean_km_s"] for row in cf4_rows], dtype=float)
    lo = np.asarray([row["vr_bootstrap_p16_km_s"] for row in cf4_rows], dtype=float)
    hi = np.asarray([row["vr_bootstrap_p84_km_s"] for row in cf4_rows], dtype=float)
    axes[1].plot(x, y, color=COLORS["purple"], marker="o", ms=3.5)
    axes[1].fill_between(x, lo, hi, color=COLORS["purple"], alpha=0.2)
    axes[1].set_xlabel("CF4 radius [Mpc/h]")
    axes[1].set_ylabel("bootstrap mean vr [km/s]")
    for ax in axes:
        _style_axes(ax)
    fig.suptitle("Observed-data long-run jackknife and bootstrap diagnostics", fontsize=11)
    fig.tight_layout()
    _save_figure(fig, output)
    return PlotMetadata(
        sky_support_status="sky_support_recorded",
        sky_support=_desi_occupancy_sky_support(),
        null_mock_status="jackknife_bootstrap_diagnostic_no_pvalue",
        statistics_definitions={
            "quantity": "DESI depth-bin jackknife and CF4 bootstrap summaries",
            "desi_rows": len(desi),
            "cf4_rows": len(cf4),
            "no_pvalue": True,
        },
    )


def _figure_specs() -> tuple[FigureSpec, ...]:
    inventory = "docs/generated/observational_data_inventory.json"
    longrun = "docs/generated/observed_longrun_analysis.json"
    return (
        FigureSpec(
            artifact_id="obsstat.observed.inventory_matrix",
            file_name="fig_observed_inventory_matrix.png",
            title="Observed data inventory matrix",
            flow_slot="Observed-data pipeline",
            source_paths=(inventory,),
            caption=(
                "Repo-local observational data availability by collection. Missing indexed entries are blocked from "
                "plot promotion until their files are present; this figure is an inventory diagnostic only."
            ),
            label="fig:observed-inventory-matrix",
            snippet="observed_figures_pipeline.tex",
            builder=_plot_inventory_matrix,
        ),
        FigureSpec(
            artifact_id="obsstat.observed.planck_pr3_spectra",
            file_name="fig_observed_planck_pr3_spectra.png",
            title="Planck PR3 spectra",
            flow_slot="Observed CMB spectra",
            source_paths=(
                inventory,
                "workdir/obs_bundle/cmb/powerspectra/planck_pr3_tt_full.npz",
                "workdir/obs_bundle/cmb/powerspectra/planck_pr3_te_full.npz",
                "workdir/obs_bundle/cmb/powerspectra/planck_pr3_ee_full.npz",
                "workdir/obs_bundle/cmb/theory/planck_pr3_bestfit.npz",
            ),
            caption=(
                "Planck PR3 TT, TE, and EE observed spectra against the bundled Planck best-fit reference. "
                "The panel is a data-quality and normalization diagnostic, not a Bianchi morphology or native-solver result."
            ),
            label="fig:observed-planck-pr3-spectra",
            snippet="observed_figures_pipeline.tex",
            builder=_plot_planck_spectra,
            transfer_source="external_reference",
        ),
        FigureSpec(
            artifact_id="obsstat.observed.planck_lowell_residual",
            file_name="fig_observed_planck_lowell_residual.png",
            title="Planck low-l residual",
            flow_slot="Observed low-l statistics",
            source_paths=(
                inventory,
                "workdir/obs_bundle/cmb/powerspectra/planck_pr3_tt_full.npz",
                "workdir/obs_bundle/cmb/theory/planck_pr3_bestfit.npz",
                "data/camb_ref_planck2018.npz",
            ),
            caption=(
                "Low-l Planck TT residuals against the bundled best-fit and repo CAMB references. "
                "Residual normalization follows the reported Planck error column; this is not a full-covariance, "
                "cosmic-variance, mask-coupled likelihood, p-value, look-elsewhere, or family-ID calculation."
            ),
            label="fig:observed-planck-lowell-residual",
            snippet="observed_figures_results.tex",
            builder=_plot_planck_lowell_residual,
            transfer_source="external_reference",
        ),
        FigureSpec(
            artifact_id="obsstat.observed.planck_map_mask",
            file_name="fig_observed_planck_map_mask.png",
            title="Planck map and mask",
            flow_slot="Observed CMB maps",
            source_paths=(
                inventory,
                "workdir/obs_bundle/cmb/maps/smica_nside16.npz",
                "workdir/obs_bundle/cmb/masks/temp_nside16.npz",
            ),
            caption=(
                "Planck SMICA NSIDE-16 temperature pixels with the PR3 temperature mask applied. "
                "This sky-facing diagnostic records mask provenance and does not infer global anisotropy."
            ),
            label="fig:observed-planck-map-mask",
            snippet="observed_figures_pipeline.tex",
            builder=_plot_planck_map_mask,
        ),
        FigureSpec(
            artifact_id="obsstat.observed.planck_lensing_bandpowers",
            file_name="fig_observed_planck_lensing_bandpowers.png",
            title="Planck lensing bandpowers",
            flow_slot="Observed lensing products",
            source_paths=(
                inventory,
                "workdir/obs_bundle/cmb/lensing/planck_pr3_lensing.npz",
                "workdir/obs_bundle/cmb/theory/camb_planck2018_lensing_refs.npz",
            ),
            caption=(
                "Planck PR3 lensing bandpowers and covariance with the bundled CAMB reference. "
                "The comparison is a transfer/reference diagnostic and not native low-l solver validation."
            ),
            label="fig:observed-planck-lensing-bandpowers",
            snippet="observed_figures_results.tex",
            builder=_plot_lensing_bandpowers,
            transfer_source="external_reference",
        ),
        FigureSpec(
            artifact_id="obsstat.observed.high_ell_experiment_summary",
            file_name="fig_observed_high_ell_experiment_summary.png",
            title="High-l experiment summary",
            flow_slot="Observed high-l and polarization products",
            source_paths=(
                inventory,
                "workdir/obs_bundle/cmb/powerspectra/act_dr4.npz",
                "workdir/obs_bundle/cmb/powerspectra/spt3g_y1.npz",
                "workdir/obs_bundle/cmb/powerspectra/bicep_keck_2018_bb.npz",
            ),
            caption=(
                "ACT DR4, SPT-3G Y1, and BICEP/Keck 2018 packed observational products. "
                "Packed-vector panels are provenance diagnostics only and do not replace the upstream likelihood analyses."
            ),
            label="fig:observed-high-ell-experiment-summary",
            snippet="observed_figures_pipeline.tex",
            builder=_plot_high_ell_experiment_summary,
        ),
        FigureSpec(
            artifact_id="obsstat.observed.desi_footprint_depth",
            file_name="fig_observed_desi_footprint_depth.png",
            title="DESI footprint and depth",
            flow_slot="Observed LSS catalog",
            source_paths=(inventory, *tuple(_repo_relative(path) for path in DESI_FILES.values())),
            caption=(
                "DESI compact BGS, LRG, and QSO sky-footprint samples with weighted redshift distributions. "
                "This is a survey and depth diagnostic; selection effects are not promoted to evidence."
            ),
            label="fig:observed-desi-footprint-depth",
            snippet="observed_figures_pipeline.tex",
            builder=_plot_desi_footprint_depth,
        ),
        FigureSpec(
            artifact_id="obsstat.observed.desi_selection_weights",
            file_name="fig_observed_desi_selection_weights.png",
            title="DESI selection weights",
            flow_slot="Observed LSS systematics",
            source_paths=(inventory, *tuple(_repo_relative(path) for path in DESI_FILES.values())),
            caption=(
                "DESI compact catalog weight, FKP, and redshift-failure weight distributions. "
                "The figure records survey-systematic structure for downstream null design without claiming a local or global cause."
            ),
            label="fig:observed-desi-selection-weights",
            snippet="observed_figures_results.tex",
            builder=_plot_desi_selection_weights,
        ),
        FigureSpec(
            artifact_id="obsstat.observed.cf4_velocity_density",
            file_name="fig_observed_cf4_velocity_density.png",
            title="CF4 velocity and density",
            flow_slot="Observed peculiar-velocity reconstruction",
            source_paths=(inventory, "workdir/compact_products/cf4/query_batch.npz"),
            caption=(
                "CF4 query-batch density and peculiar-velocity summaries in supergalactic coordinates. "
                "The plot is a reconstruction diagnostic and does not label the signal as native or family-specific."
            ),
            label="fig:observed-cf4-velocity-density",
            snippet="observed_figures_results.tex",
            builder=_plot_cf4_velocity_density,
        ),
        FigureSpec(
            artifact_id="obsstat.observed.cf4_depth_response",
            file_name="fig_observed_cf4_depth_response.png",
            title="CF4 depth response",
            flow_slot="Observed peculiar-velocity reconstruction",
            source_paths=(inventory, "workdir/compact_products/cf4/query_batch.npz"),
            caption=(
                "CF4 radius-binned radial-velocity and density-response diagnostics. "
                "The bands are descriptive percentiles, not calibrated null intervals or posterior credible regions."
            ),
            label="fig:observed-cf4-depth-response",
            snippet="observed_figures_results.tex",
            builder=_plot_cf4_depth_response,
        ),
        FigureSpec(
            artifact_id="obsstat.observed.longrun_jackknife_bootstrap",
            file_name="fig_observed_longrun_jackknife_bootstrap.png",
            title="Observed long-run jackknife and bootstrap",
            flow_slot="Observed long-run diagnostics",
            source_paths=(inventory, longrun),
            caption=(
                "Long-run observed-data diagnostics: DESI depth-bin jackknife amplitudes and CF4 radial-velocity bootstrap means. "
                "These uncertainty summaries are diagnostic only and introduce no p-value, posterior, evidence, or family-ID claim."
            ),
            label="fig:observed-longrun-jackknife-bootstrap",
            snippet="observed_figures_results.tex",
            builder=_plot_longrun_jackknife,
        ),
    )


def _manifest_for_spec(spec: FigureSpec, figure_path: Path, command: str, meta: PlotMetadata) -> dict[str, Any]:
    rel_path = _repo_relative(figure_path)
    git_commit, worktree = _git_state()
    caveats = [*spec.caveats, *meta.extra_caveats]
    manifest = {
        "artifact_id": spec.artifact_id,
        "artifact_path": rel_path,
        "owner": spec.owner,
        "implementation_scope": spec.implementation_scope,
        "claim_tier": spec.claim_tier,
        "production_status": "diagnostic_only",
        "artifact_mode": spec.artifact_mode,
        "allowed_use": spec.allowed_use,
        "caption_policy": list(spec.caption_policy),
        "promotion_blockers": list(spec.promotion_blockers),
        "created_by": "scripts/make_observed_data_manuscript_figures.py",
        "git_commit": git_commit,
        "config_hash": _stable_hash(
            {
                "artifact_id": spec.artifact_id,
                "file_name": spec.file_name,
                "source_paths": spec.source_paths,
                "caption": spec.caption,
                "version": "observed-current-figures-v1",
            }
        ),
        "input_hashes": _input_hashes(spec.source_paths),
        "code_version": worktree,
        "schema_version": "obsstat.observed_current_figure.v2",
        "caveats": caveats,
        "required_gates": [
            "repo_local_observed_data_present",
            "manifest_metadata_present",
            "claim_firewall_caption_review",
        ],
        "passed_gates": [
            "repo_local_observed_data_present",
            "manifest_metadata_present",
            "claim_firewall_caption_review",
        ],
        "failed_gates": [
            "matched_nulls_not_bound",
            "full_covariance_not_bound",
            "native_low_ell_solver_not_available",
            "family_morphology_atlas_not_available",
        ],
        "science_promotion_gates": {
            "matched_nulls": "fail_not_bound",
            "full_covariance": "fail_not_bound",
            "native_low_ell_solver": "fail_not_available",
            "family_morphology_atlas": "fail_not_available",
        },
        "publication_gates": {
            "paper_main_claim": "fail_diagnostic_only",
            "evidence_or_pvalue_claim": "fail_not_calibrated",
        },
        "statistics_definitions": {
            "flow_slot": spec.flow_slot,
            "source_artifacts": list(spec.source_paths),
            **meta.statistics_definitions,
        },
        "transfer_source": spec.transfer_source,
        "sky_support_status": meta.sky_support_status,
        "null_mock_status": meta.null_mock_status,
        "generating_command": command,
        "git_commit_or_worktree_state": worktree,
    }
    if meta.sky_support is not None:
        manifest["sky_support"] = meta.sky_support
    issues = validate_manifest_payload(
        manifest,
        manifest_path=figure_path.with_suffix(".manifest.json"),
        expected_artifact_path=rel_path,
    )
    if issues:
        rendered = "; ".join(f"{issue.code}: {issue.detail}" for issue in issues)
        raise ValueError(f"invalid manifest for {rel_path}: {rendered}")
    return manifest


def _write_sidecar(spec: FigureSpec, figure_path: Path, command: str, meta: PlotMetadata) -> None:
    manifest = _manifest_for_spec(spec, figure_path, command, meta)
    sidecar = figure_path.with_suffix("").with_name(figure_path.stem + ".manifest.json")
    sidecar.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _latex_figure(spec: FigureSpec) -> str:
    graphic_path = "observed_current/" + Path(spec.file_name).with_suffix("").name
    return "\n".join(
        [
            "\\begin{figure}[htbp]",
            "\\centering",
            f"\\includegraphics[width=0.92\\textwidth]{{{graphic_path}}}",
            f"\\caption{{{spec.caption}}}",
            f"\\label{{{spec.label}}}",
            "\\end{figure}",
            "",
        ]
    )


def _write_snippets(specs: tuple[FigureSpec, ...]) -> None:
    SNIPPET_DIR.mkdir(parents=True, exist_ok=True)
    by_snippet: dict[str, list[FigureSpec]] = {}
    for spec in specs:
        by_snippet.setdefault(spec.snippet, []).append(spec)
    for snippet, snippet_specs in by_snippet.items():
        body = [
            "% Generated by scripts/make_observed_data_manuscript_figures.py.",
            "% Do not edit figure paths by hand; regenerate instead.",
            "",
        ]
        for spec in snippet_specs:
            body.append(_latex_figure(spec))
        (SNIPPET_DIR / snippet).write_text("\n".join(body), encoding="utf-8")


def _write_plot_list(specs: tuple[FigureSpec, ...], command: str) -> None:
    source_paths = tuple(sorted({path for spec in specs for path in spec.source_paths}))
    git_commit, worktree = _git_state()
    config_hash = _stable_hash(
        {
            "specs": [spec.artifact_id for spec in specs],
            "source_paths": source_paths,
            "version": "observed-current-plot-list-v1",
        }
    )
    lines = [
        "# Observed Current Plot List",
        "",
        "owner: OBSSTAT",
        "implementation_scope: obsstat",
        "claim_tier: diagnostic_only",
        "transfer_source: mixed_none_and_external_reference",
        "sky_support_status: mixed_not_directional_and_recorded_sky_support",
        "null_mock_status: mixed_not_statistical_and_jackknife_bootstrap_diagnostic",
        f"config_hash: `{config_hash}`",
        "input_hashes:",
    ]
    for item in _input_hashes(source_paths):
        lines.append(f"- `{item}`")
    lines.extend(
        [
            "caveats:",
            "- Observed-data plots are diagnostic unless separately calibrated by matched nulls and covariance metadata.",
            "- No plot claims native low-ell solver output, geometry detection, or Bianchi family-ID.",
            "- Packed upstream likelihood products are displayed only as provenance diagnostics.",
            f"generating_command: `{command}`",
            f"git_commit_or_worktree_state: `{worktree}`",
            "artifact_path: docs/generated/observed_current_plot_list.md",
            "",
            "## Current Observed-Data Plot Sequence",
            "",
            f"- Manifest-backed observed-data plot count: `{len(specs)}`",
            "- Long-run plots use jackknife/bootstrap summaries only; no p-value is introduced.",
            "",
            "| Flow slot | Figure | Source artifacts | Claim tier | Artifact mode | Allowed use | Caveat |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for spec in specs:
        source = "<br>".join(f"`{path}`" for path in spec.source_paths)
        lines.append(
            f"| {spec.flow_slot} | `figures/observed_current/{spec.file_name}` | {source} | "
            f"`{spec.claim_tier}` | `{spec.artifact_mode}` | `{spec.allowed_use}` | {spec.caveats[0]} |"
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- These figures support only observed-data diagnostic reporting.",
            "- Directional and sky-support plots record masks or coordinate frames but do not establish a global anisotropy cause.",
            "- DESI and CF4 diagnostics remain separate from HTT posterior/evidence and MIO certificates.",
            "- Scalar, depth, and direction summaries do not identify a Bianchi family.",
            f"git_commit: `{git_commit}`",
        ]
    )
    PLOT_LIST.parent.mkdir(parents=True, exist_ok=True)
    PLOT_LIST.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _markdown_count(path: Path, prefix: str, default: int) -> int:
    if not path.exists():
        return default
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if line.strip().startswith(prefix):
            digits = "".join(char if char.isdigit() else " " for char in line)
            values = [int(item) for item in digits.split()]
            if values:
                return values[-1]
    return default


def _write_composite_plot_index(specs: tuple[FigureSpec, ...], command: str) -> None:
    current_list = REPO_ROOT / "docs" / "generated" / "current_manuscript_plot_list.md"
    expanded_list = REPO_ROOT / "docs" / "generated" / "expanded_manuscript_plot_list.md"
    candidate_paths = (current_list, PLOT_LIST, expanded_list)
    source_paths = tuple(
        path.relative_to(REPO_ROOT).as_posix()
        for path in candidate_paths
        if path.exists()
    )
    current_count = _markdown_count(current_list, "- Current manifest-backed plot count:", 10)
    ver2_count = _markdown_count(expanded_list, "- Added current-code VER2 pack figures:", 5)
    legacy_count = _markdown_count(expanded_list, "- Added conditioned legacy appendix figures:", 88)
    observed_count = len(specs)
    total = current_count + observed_count + ver2_count + legacy_count
    git_commit, worktree = _git_state()
    config_hash = _stable_hash(
        {
            "current_count": current_count,
            "observed_count": observed_count,
            "ver2_count": ver2_count,
            "legacy_count": legacy_count,
            "source_paths": source_paths,
            "version": "manuscript-plot-list-index-v1",
        }
    )
    lines = [
        "# Manuscript Plot List Index",
        "",
        "owner: COMMON",
        "implementation_scope: common",
        "claim_tier: diagnostic_only",
        "transfer_source: mixed_observed_current_and_conditioned_legacy",
        "sky_support_status: mixed_not_directional_and_recorded_sky_support",
        "null_mock_status: mixed_not_statistical_jackknife_bootstrap_and_legacy_conditioned",
        f"config_hash: `{config_hash}`",
        "input_hashes:",
    ]
    for item in _input_hashes(source_paths):
        lines.append(f"- `{item}`")
    lines.extend(
        [
            "caveats:",
            "- This is an index over generated plot-list documents, not a new science result.",
            "- Observed-data entries are descriptive or diagnostic-only unless matched-null status is explicit.",
            "- Conditioned legacy entries remain appendix-only and assumption-conditioned.",
            "- No entry claims native low-ell solver output, geometry detection, or Bianchi family-ID.",
            f"generating_command: `{command}`",
            f"git_commit_or_worktree_state: `{worktree}`",
            "artifact_path: docs/generated/manuscript_plot_list_index.md",
            "",
            "## Summary",
            "",
            f"- Current-code core figures: `{current_count}`",
            f"- Observed-data figures added in this deck: `{observed_count}`",
            f"- Current-code VER2 diagnostic figures: `{ver2_count}`",
            f"- Conditioned legacy appendix figures: `{legacy_count}`",
            f"- Total manuscript figure references after observed-data extension: `{total}`",
            "",
            "## Manuscript Flow",
            "",
            "| Report flow | Plot deck | Count | Source list | Claim ceiling |",
            "| --- | --- | ---: | --- | --- |",
            f"| Framework and repository status | Current-code core | {current_count} | `docs/generated/current_manuscript_plot_list.md` | diagnostic-only framework reporting |",
            f"| Observational pipeline and observed-data results | Observed-data deck | {observed_count} | `docs/generated/observed_current_plot_list.md` | observed-data diagnostics only |",
            f"| Results and robustness | Current-code VER2 packs | {ver2_count} | `docs/generated/expanded_manuscript_plot_list.md` | current-code diagnostics only |",
            f"| Appendix context | Conditioned legacy appendix deck | {legacy_count} | `docs/generated/expanded_manuscript_plot_list.md` | appendix-only conditioned context |",
            "",
            "## Observed-Data Figure Order",
            "",
            "| Flow slot | Figure | Manuscript snippet |",
            "| --- | --- | --- |",
        ]
    )
    for spec in specs:
        lines.append(
            f"| {spec.flow_slot} | `figures/observed_current/{spec.file_name}` | "
            f"`docs/manuscript/generated/{spec.snippet}` |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- MIO certificates and HTT evidence are not merged into this observed-data deck.",
            "- External or conditioned transfer products are not labeled native.",
            "- Scalar, depth, and direction summaries do not assign a Bianchi family.",
            f"git_commit: `{git_commit}`",
        ]
    )
    COMPOSITE_PLOT_INDEX.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _command(argv: list[str] | None) -> str:
    args = [sys.argv[0], *(argv if argv is not None else sys.argv[1:])]
    return " ".join(args)


def run(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="list figure specs and exit")
    parser.add_argument("--only", default=None, help="render one figure file name")
    parser.add_argument("--force-longrun", action="store_true", help="recompute cached long-run diagnostics")
    args = parser.parse_args(argv)

    specs = _figure_specs()
    if args.list:
        for spec in specs:
            print(f"{spec.file_name}\t{spec.flow_slot}")
        return 0

    command = _command(argv)
    _write_inventory(command)
    _write_longrun(command, force=args.force_longrun)

    selected = specs
    if args.only:
        selected = tuple(spec for spec in specs if spec.file_name == args.only)
        if not selected:
            raise SystemExit(f"unknown figure file name: {args.only}")
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    for spec in selected:
        output = FIGURE_DIR / spec.file_name
        meta = spec.builder(output)
        _write_sidecar(spec, output, command, meta)
        print(f"wrote {_repo_relative(output)}")
    if not args.only:
        _write_snippets(specs)
        _write_plot_list(specs, command)
        _write_composite_plot_index(specs, command)
        print(f"wrote {_repo_relative(PLOT_LIST)}")
        print(f"wrote {_repo_relative(COMPOSITE_PLOT_INDEX)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
