#!/usr/bin/env python3
"""Generate report-candidate figures from bound observational data.

This lane is intentionally data-facing. It avoids code-history, governance,
readiness, claim-gate, and self-audit figures. The outputs remain
diagnostic-only observed-data analyses: no p-values, posterior odds, Bianchi
family identification, geometry detection, or native low-ell solver output.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shlex
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402


REPO_ROOT = Path(__file__).resolve().parents[1]
COMMON_ROOT = REPO_ROOT / "htt" / "src"
if str(COMMON_ROOT) not in sys.path:
    sys.path.insert(0, str(COMMON_ROOT))

from common.artifact_manifest import validate_manifest_payload  # noqa: E402
from common.sky_support import build_sky_support_from_mask  # noqa: E402


GEN = REPO_ROOT / "docs" / "generated"
FIGURE_DIR = REPO_ROOT / "figures" / "data_analysis_current"
PACK_JSON = GEN / "report_data_analysis_figure_pack.json"
PACK_MD = GEN / "report_data_analysis_figure_pack.md"

OBSERVED_LONGRUN = "docs/generated/observed_longrun_analysis.json"
PLANCK_TT = "workdir/obs_bundle/cmb/powerspectra/planck_pr3_tt_binned.npz"
PLANCK_SMICA = "workdir/obs_bundle/cmb/maps/smica_nside16.npz"
PLANCK_COMMANDER = "workdir/obs_bundle/cmb/maps/commander_nside16.npz"
PLANCK_TEMP_MASK = "workdir/obs_bundle/cmb/masks/temp_nside16.npz"
CF4_GROUPS = "workdir/obs_bundle/pecvel/cf4_full/cf4_groups.npz"
DESI_CF4_TARGETS = "workdir/compact_products/cf4/targets_cf4_from_desi_bgs_auto.csv"
DESI_BGS_NGC = "workdir/compact_products/desi/BGS_ANY_NGC_clustering_extended.npz"
DESI_BGS_SGC = "workdir/compact_products/desi/BGS_ANY_SGC_clustering_extended.npz"
DESI_LRG_NGC = "workdir/compact_products/desi/LRG_NGC_clustering_extended.npz"
DESI_LRG_SGC = "workdir/compact_products/desi/LRG_SGC_clustering_extended.npz"
DESI_QSO_NGC = "workdir/compact_products/desi/QSO_NGC_clustering_extended.npz"
DESI_QSO_SGC = "workdir/compact_products/desi/QSO_SGC_clustering_extended.npz"
K5_CF4_RELEASE_COVERAGE = "docs/generated/k5_cf4_release_coverage.json"
K6_CF4_CURL_POSTERIOR = "docs/generated/k6_cf4_curl_posterior.json"
CF4_APEX_DEPTH = "docs/generated/cf4_bulkflow_apex_depth_report.json"
CF4_BULKFLOW_LIKELIHOOD = "docs/generated/cf4_bulkflow_likelihood_report.json"
CF4_AFFINE_FLOW = "docs/generated/cf4_affine_flow_report.json"
CF4_P0_BLOCK = "docs/generated/cf4_p0_quarantine_block.json"
CF4_WF_GRID = "workdir/raw/cf4/CF4pp_mean_std_grids.npz"
LOWELL_MORPHOLOGY = "docs/generated/lowell_morphology_real_map_report.json"
K1_GLOBAL_MAXSCAN = "docs/generated/k1_global_maxscan.json"
K1_BIPOSH_SMICA = "docs/generated/k1_biposh_smica.json"
PR08_JOINT_ARTIFACT = "docs/generated/pr08_006_joint_artifact.json"
SCRIPT_PATH = "scripts/make_report_data_analysis_figures.py"
PLANCK_LENSING = "workdir/obs_bundle/cmb/lensing/planck_pr3_lensing.npz"
CAMB_LENSING_REFS = "workdir/obs_bundle/cmb/theory/camb_planck2018_lensing_refs.npz"
ACT_DR4_COMPACT = "workdir/obs_bundle/cmb/powerspectra/act_dr4.npz"
SPT3G_Y1_COMPACT = "workdir/obs_bundle/cmb/powerspectra/spt3g_y1.npz"
BICEP_KECK_2018_BB = "workdir/obs_bundle/cmb/powerspectra/bicep_keck_2018_bb.npz"
ACT_DR6_TT = "workdir/htt_extracted/act_dr6_tt_bandpowers.npz"
ACT_DR6_TE = "workdir/htt_extracted/act_dr6_te_bandpowers.npz"
ACT_DR6_EE = "workdir/htt_extracted/act_dr6_ee_bandpowers.npz"
APPROVAL_COMPACT_INVENTORY = "docs/generated/v6_approval_compact_download_inventory.json"
ACT_DR6_LENSING_MANIFEST = "workdir/raw/act_dr6_lensing/act_dr6_lensing_acquisition_manifest.json"
ACT_DR6_LENSING_LIKE_README = "workdir/raw/act_dr6_lensing/ACT_dr6_likelihood_v1.2/v1.2/README"
ACT_DR6_LENSING_MAP_README = "workdir/raw/act_dr6_lensing/dr6_lensing_release/README"
ACT_DR6_LENSING_BANDPOWERS = (
    "workdir/raw/act_dr6_lensing/ACT_dr6_likelihood_v1.2/v1.2/clkk_bandpowers_act.txt",
    "workdir/raw/act_dr6_lensing/ACT_dr6_likelihood_v1.2/v1.2/clkk_bandpowers_act_cibdeproj.txt",
    "workdir/raw/act_dr6_lensing/ACT_dr6_likelihood_v1.2/v1.2/clkk_bandpowers_act_cinpaint.txt",
    "workdir/raw/act_dr6_lensing/ACT_dr6_likelihood_v1.2/v1.2/clkk_bandpowers_act_polonly.txt",
    "workdir/raw/act_dr6_lensing/ACT_dr6_likelihood_v1.2/v1.2/clkk_bandpowers_planck.txt",
)
ACT_DR6_LENSING_NOISE_CURVES = (
    "workdir/raw/act_dr6_lensing/dr6_lensing_release/maps/baseline/N_L_kk_act_dr6_lensing_v1_baseline.txt",
    "workdir/raw/act_dr6_lensing/dr6_lensing_release/maps/tonly/N_L_kk_act_dr6_lensing_v1_tonly.txt",
    "workdir/raw/act_dr6_lensing/dr6_lensing_release/maps/polonly/N_L_kk_act_dr6_lensing_v1_polonly.txt",
    "workdir/raw/act_dr6_lensing/dr6_lensing_release/maps/curl/N_L_kk_act_dr6_lensing_v1_curl.txt",
    "workdir/raw/act_dr6_lensing/dr6_lensing_release/maps/diff_f150_f090/N_L_kk_act_dr6_lensing_v1_diff_f150_f090.txt",
)
ACT_DR6_LENSING_BASELINE_FILTER = (
    "workdir/raw/act_dr6_lensing/dr6_lensing_release/maps/baseline/kappa_filter_act_dr6_lensing_v1_baseline.txt"
)

OBSERVED_LONGRUN_SOURCES = (
    OBSERVED_LONGRUN,
    DESI_BGS_NGC,
    DESI_BGS_SGC,
    DESI_LRG_NGC,
    DESI_LRG_SGC,
    DESI_QSO_NGC,
    DESI_QSO_SGC,
    "workdir/compact_products/cf4/query_batch.npz",
    SCRIPT_PATH,
)

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

SKIPPED_CURRENT_DATA_CANDIDATES = (
    {
        "candidate": "K5 CF4 bulk-flow/global-tilt and forward-coverage figure set",
        "reason": "PR-120 quarantine: K5 coverage, K5-versus-affine, forward-coverage residual, observed-sector response, and K1-K5 joint figures consume the OPEN CF4 P0 chain; historical copies are legacy_reproduction_only",
    },
    {
        "candidate": "MIO directional pairwise separation heatmap",
        "reason": "probe set is hardcoded/literature-level in the current checkout; source-bound report manifest is not present",
    },
    {
        "candidate": "redshift-bin directional drift line",
        "reason": "requires an explicitly bound probe tuple and matched null metadata before report-lane use",
    },
    {
        "candidate": "CF4/JWST catalogue-linkage diagnostic",
        "reason": "PR-120 quarantine: no CF4-conditioned precision or global-tilt forecast is authorized while N-DATA-CF4-DOWNSTREAM remains OPEN",
    },
    {
        "candidate": "Planck low-ell residual map with CF4 apex-track overlay",
        "reason": "low-ell residual map overlay is not yet represented as a bound current-data source artifact",
    },
    {
        "candidate": "DESI data-random dipole by tracer, cap, and redshift",
        "reason": "implemented estimator needs certified data-random binding and selection correction",
    },
    {
        "candidate": "CF4 forward-likelihood residual anatomy",
        "reason": "implemented likelihood surface needs a real-catalog driver and basis binding",
    },
)

CF4_P0_QUARANTINED_FIGURE_NAMES = frozenset(
    {
        "fig_data_k5_cf4_bulk_flow_coverage.png",
        "fig_data_k5_cf4_vs_affine_consistency.png",
        "fig_data_cf4_forward_coverage_residual.png",
        "fig_data_observed_sector_response_vector.png",
        "fig_data_k1_k5_joint_diagnostic_axes.png",
    }
)

CF4_RECONSTRUCTION_FUNCTIONAL_FIGURE_NAMES = frozenset(
    {
        "fig_data_cf4_depth_apex_phase_portrait.png",
        "fig_data_cf4_shell_apex_separation_matrix.png",
        "fig_data_cf4_affine_gradient_spectrum.png",
    }
)


class CF4P0FigureQuarantined(RuntimeError):
    """Raised when a removed CF4 P0 report builder is called directly."""


def _reject_cf4_p0_figure_builder(file_name: str) -> None:
    if file_name not in CF4_P0_QUARANTINED_FIGURE_NAMES:
        raise ValueError(f"unknown quarantined CF4 P0 figure: {file_name}")
    raise CF4P0FigureQuarantined(
        f"{file_name} is legacy_reproduction_only while the CF4 P0 findings "
        "remain OPEN; no active figure may be generated"
    )


@dataclass(frozen=True)
class PlotMeta:
    statistics_definitions: dict[str, Any]
    sky_support_status: str = "not_directional"
    sky_support: dict[str, Any] | None = None
    null_mock_status: str = "not_statistical"
    transfer_source: str = "none"


@dataclass(frozen=True)
class FigureSpec:
    artifact_id: str
    file_name: str
    title: str
    source_paths: tuple[str, ...]
    builder: Callable[[Path], PlotMeta]
    caption: str


def _repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _input_hashes(paths: tuple[str, ...]) -> list[str]:
    rows: list[str] = []
    for relative in paths:
        path = REPO_ROOT / relative
        rows.append(f"{relative}:{_sha256(path) if path.exists() else 'missing'}")
    return rows


def _config_hash(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode(
        "utf-8"
    )
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _command(argv: list[str] | None) -> str:
    args = sys.argv[1:] if argv is None else argv
    return shlex.join(["python", SCRIPT_PATH, *args])


def _save(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def _style(ax: plt.Axes) -> None:
    ax.set_facecolor(COLORS["panel"])
    ax.grid(True, alpha=0.25, linewidth=0.7)
    for spine in ax.spines.values():
        spine.set_color("#cbd5e1")


def _wrap_mollweide_lon(ra_deg: np.ndarray) -> np.ndarray:
    lon = np.remainder(ra_deg + 180.0, 360.0) - 180.0
    return np.deg2rad(-lon)


def _unit_from_lb(l_deg: float, b_deg: float) -> np.ndarray:
    lon = np.deg2rad(float(l_deg))
    lat = np.deg2rad(float(b_deg))
    return np.asarray(
        [np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)],
        dtype=float,
    )


def _angular_sep_deg(
    l1_deg: float,
    b1_deg: float,
    l2_deg: float,
    b2_deg: float,
    *,
    antipodal: bool = False,
) -> float:
    dot = float(np.dot(_unit_from_lb(l1_deg, b1_deg), _unit_from_lb(l2_deg, b2_deg)))
    dot = abs(dot) if antipodal else dot
    return float(np.rad2deg(np.arccos(np.clip(dot, -1.0, 1.0))))


def _plot_galactic_marker(
    ax: plt.Axes,
    l_deg: float,
    b_deg: float,
    *,
    label: str,
    color: str,
    marker: str,
    size: float = 58.0,
    edgecolor: str = "white",
) -> None:
    ax.scatter(
        _wrap_mollweide_lon(np.asarray([float(l_deg)])),
        np.deg2rad([float(b_deg)]),
        s=size,
        color=color,
        marker=marker,
        edgecolor=edgecolor,
        linewidth=0.7,
        label=label,
        zorder=5,
    )


def _desi_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = payload["desi_depth_jackknife"]
    if not isinstance(rows, list):
        raise TypeError("desi_depth_jackknife must be a list")
    return rows


def _cf4_radius_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = payload["cf4_radius_bootstrap"]
    if not isinstance(rows, list):
        raise TypeError("cf4_radius_bootstrap must be a list")
    return rows


def _label_cap(label: str) -> str:
    parts = str(label).split()
    return parts[-1] if parts else "unknown"


def _sample_indices(n: int, max_points: int, *, salt: int) -> np.ndarray:
    if n <= max_points:
        return np.arange(n, dtype=int)
    stride = max(1, n // max_points)
    start = salt % stride
    return np.arange(start, n, stride, dtype=int)[:max_points]


def _sky_support_from_radec(
    ra_deg: np.ndarray,
    dec_deg: np.ndarray,
    *,
    completeness_status: str,
    selection_mode: str,
) -> dict[str, Any]:
    import healpy as hp

    nside = 32
    theta = np.deg2rad(90.0 - np.asarray(dec_deg, dtype=float))
    phi = np.deg2rad(np.asarray(ra_deg, dtype=float))
    good = np.isfinite(theta) & np.isfinite(phi)
    occupied = np.zeros(hp.nside2npix(nside), dtype=bool)
    occupied[hp.ang2pix(nside, theta[good], phi[good], nest=False)] = True
    support = build_sky_support_from_mask(
        occupied,
        coordinate_frame="equatorial_icrs",
        completeness_status=completeness_status,
        selection_mode=selection_mode,
        mock_coverage_status="not_mocked",
        pixelization="healpix_ring",
        nside=nside,
    )
    return support.to_metadata()


def _plot_planck_tt_binned_residual(output: Path) -> PlotMeta:
    with np.load(REPO_ROOT / PLANCK_TT, allow_pickle=False) as data:
        ell = np.asarray(data["ell"], dtype=float)
        dl = np.asarray(data["dl"], dtype=float)
        bestfit = np.asarray(data["bestfit"], dtype=float)
        err = 0.5 * (
            np.asarray(data["err_lo"], dtype=float)
            + np.asarray(data["err_hi"], dtype=float)
        )
    residual = (dl - bestfit) / np.where(err > 0, err, np.nan)
    fig, axes = plt.subplots(2, 1, figsize=(8.2, 5.8), sharex=True)
    axes[0].errorbar(
        ell,
        dl,
        yerr=err,
        fmt="o",
        ms=3.3,
        color=COLORS["blue"],
        ecolor="#93c5fd",
        elinewidth=0.8,
        capsize=1.5,
        label="Planck PR3 TT binned",
    )
    axes[0].plot(ell, bestfit, color=COLORS["slate"], lw=1.1, label="best-fit reference")
    axes[0].set_ylabel("TT D_l [microK^2]")
    axes[0].legend(frameon=False, fontsize=8)
    axes[1].axhline(0.0, color=COLORS["slate"], lw=0.8)
    axes[1].bar(
        ell,
        residual,
        width=np.maximum(4.0, np.gradient(ell)),
        color=np.where(residual >= 0.0, COLORS["blue"], COLORS["red"]),
        alpha=0.72,
    )
    axes[1].set_xlabel("multipole l")
    axes[1].set_ylabel("residual / sigma")
    for ax in axes:
        _style(ax)
    fig.suptitle("Planck PR3 binned TT spectrum and residuals", fontsize=12)
    fig.tight_layout()
    _save(fig, output)
    return PlotMeta(
        statistics_definitions={
            "figure_lane": "report_data_analysis_current",
            "quantity": "Planck PR3 TT binned spectrum and residuals",
            "ell_count": int(ell.size),
            "residual_sigma_rms": float(np.sqrt(np.nanmean(residual**2))),
        },
        transfer_source="external_reference",
    )


def _plot_planck_smica_masked_temperature(output: Path) -> PlotMeta:
    import healpy as hp

    with np.load(REPO_ROOT / PLANCK_SMICA, allow_pickle=False) as data:
        temp = np.asarray(data["I"], dtype=float)
        nside = int(data["nside"])
    with np.load(REPO_ROOT / PLANCK_TEMP_MASK, allow_pickle=False) as data:
        mask = np.asarray(data["mask"], dtype=float) > 0.5
    lon, lat = hp.pix2ang(nside, np.arange(temp.size), lonlat=True)
    display = np.where(mask, temp, np.nan)
    vlim = float(np.nanpercentile(np.abs(display), 98.0))
    fig = plt.figure(figsize=(8.8, 4.7))
    ax = fig.add_subplot(111, projection="mollweide")
    sc = ax.scatter(
        _wrap_mollweide_lon(lon),
        np.deg2rad(lat),
        c=display,
        s=11,
        cmap="RdBu_r",
        vmin=-vlim,
        vmax=vlim,
        linewidths=0,
    )
    ax.grid(True, alpha=0.25)
    ax.set_title("Planck SMICA temperature map with PR3 mask")
    cb = fig.colorbar(sc, ax=ax, shrink=0.72, pad=0.08)
    cb.set_label("microK")
    fig.tight_layout()
    _save(fig, output)
    support = build_sky_support_from_mask(
        mask,
        coordinate_frame="galactic",
        completeness_status="planck_pr3_temperature_mask_applied",
        selection_mode="planck_temperature_mask",
        mock_coverage_status="not_mocked",
        pixelization="healpix_ring",
        nside=nside,
    )
    return PlotMeta(
        sky_support_status="masked_sky",
        sky_support=support.to_metadata(),
        statistics_definitions={
            "figure_lane": "report_data_analysis_current",
            "quantity": "masked Planck SMICA temperature pixels",
            "nside": nside,
            "fsky": float(mask.mean()),
            "temperature_median_microK": float(np.nanmedian(display)),
        },
    )


def _plot_cf4_catalog_sky_velocity(output: Path) -> PlotMeta:
    with np.load(REPO_ROOT / CF4_GROUPS, allow_pickle=False) as data:
        ra = np.asarray(data["RAdeg"], dtype=float)
        dec = np.asarray(data["DEdeg"], dtype=float)
        vpec = np.asarray(data["Vpec"], dtype=float)
        dist = np.asarray(data["Dist"], dtype=float)
    good = np.isfinite(ra) & np.isfinite(dec) & np.isfinite(vpec) & np.isfinite(dist)
    sample = _sample_indices(int(good.sum()), 38_000, salt=11)
    ra_g = ra[good][sample]
    dec_g = dec[good][sample]
    v_g = vpec[good][sample]
    fig = plt.figure(figsize=(9.2, 5.9))
    ax0 = fig.add_subplot(211, projection="mollweide")
    sc = ax0.scatter(
        _wrap_mollweide_lon(ra_g),
        np.deg2rad(dec_g),
        c=v_g,
        s=4.5,
        cmap="RdBu_r",
        vmin=-1200,
        vmax=1200,
        alpha=0.72,
        linewidths=0,
    )
    ax0.grid(True, alpha=0.25)
    ax0.set_title("CF4 group catalog sky positions colored by peculiar velocity")
    cb = fig.colorbar(sc, ax=ax0, shrink=0.74, pad=0.08)
    cb.set_label("Vpec [km/s]")
    ax1 = fig.add_subplot(212)
    ax1.hist(vpec[good], bins=120, range=(-2500, 2500), color=COLORS["purple"], alpha=0.76)
    ax1.set_xlabel("Vpec [km/s]")
    ax1.set_ylabel("groups")
    _style(ax1)
    fig.tight_layout()
    _save(fig, output)
    return PlotMeta(
        sky_support_status="not_directional",
        sky_support=_sky_support_from_radec(
            ra[good],
            dec[good],
            completeness_status="cf4_group_catalog_coordinate_support",
            selection_mode="cf4_group_release_positions",
        ),
        statistics_definitions={
            "figure_lane": "report_data_analysis_current",
            "quantity": "CF4 group sky positions and Vpec distribution",
            "n_groups": int(good.sum()),
            "vpec_median_km_s": float(np.nanmedian(vpec[good])),
        },
    )


def _plot_cf4_depth_velocity_profile(output: Path) -> PlotMeta:
    with np.load(REPO_ROOT / CF4_GROUPS, allow_pickle=False) as data:
        dist = np.asarray(data["Dist"], dtype=float)
        vpec = np.asarray(data["Vpec"], dtype=float)
        err_dm = np.asarray(data["e_DMzp"], dtype=float)
    good = np.isfinite(dist) & np.isfinite(vpec) & np.isfinite(err_dm) & (dist > 0.0)
    edges = np.quantile(dist[good], np.linspace(0.0, 1.0, 15))
    centers: list[float] = []
    med: list[float] = []
    lo: list[float] = []
    hi: list[float] = []
    counts: list[int] = []
    err_med: list[float] = []
    for idx, (left, right) in enumerate(zip(edges[:-1], edges[1:])):
        mask = good & (dist >= left) & (dist < right if idx < len(edges) - 2 else dist <= right)
        values = vpec[mask]
        centers.append(float(0.5 * (left + right)))
        med.append(float(np.nanmedian(values)))
        lo.append(float(np.nanpercentile(values, 16)))
        hi.append(float(np.nanpercentile(values, 84)))
        counts.append(int(mask.sum()))
        err_med.append(float(np.nanmedian(err_dm[mask])))
    fig, axes = plt.subplots(2, 1, figsize=(8.1, 5.9), sharex=True)
    x = np.asarray(centers)
    axes[0].plot(x, med, marker="o", ms=3.5, color=COLORS["orange"], lw=1.4)
    axes[0].fill_between(x, lo, hi, color=COLORS["orange"], alpha=0.2)
    axes[0].axhline(0.0, color=COLORS["slate"], lw=0.8)
    axes[0].set_ylabel("Vpec percentile band [km/s]")
    axes[1].bar(x, counts, width=np.maximum(0.3, np.gradient(x)), color=COLORS["blue"], alpha=0.6, label="groups")
    ax_err = axes[1].twinx()
    ax_err.plot(x, err_med, color=COLORS["red"], marker="s", ms=3.0, lw=1.0, label="median e_DMzp")
    axes[1].set_xlabel("CF4 distance [Mpc]")
    axes[1].set_ylabel("groups per quantile bin")
    ax_err.set_ylabel("median distance-modulus error")
    for ax in axes:
        _style(ax)
    fig.suptitle("CF4 depth-binned peculiar-velocity profile", fontsize=12)
    fig.tight_layout()
    _save(fig, output)
    return PlotMeta(
        statistics_definitions={
            "figure_lane": "report_data_analysis_current",
            "quantity": "CF4 distance-binned Vpec percentiles and counts",
            "n_bins": int(len(x)),
            "n_groups": int(good.sum()),
        }
    )


def _load_desi_targets() -> dict[str, np.ndarray]:
    rows: dict[str, list[float]] = {key: [] for key in ("ra", "dec", "z", "selected_weight", "sgx", "sgy", "sgz")}
    with (REPO_ROOT / DESI_CF4_TARGETS).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            for key in rows:
                rows[key].append(float(row[key]))
    return {key: np.asarray(values, dtype=float) for key, values in rows.items()}


def _load_json(relative: str) -> dict[str, Any]:
    payload = json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"{relative} must contain a JSON object")
    return payload


def _plot_desi_redshift_jackknife_ridge(output: Path) -> PlotMeta:
    payload = _load_json(OBSERVED_LONGRUN)
    rows = _desi_rows(payload)
    colors = {"BGS": COLORS["blue"], "LRG": COLORS["green"], "QSO": COLORS["purple"]}
    linestyles = {"NGC": "-", "SGC": "--"}

    fig, ax = plt.subplots(figsize=(8.4, 5.0))
    _style(ax)
    for label in sorted({str(row["label"]) for row in rows}):
        subset = sorted((row for row in rows if row["label"] == label), key=lambda row: row["z_mid"])
        tracer = str(subset[0]["tracer"])
        cap = _label_cap(label)
        x = np.asarray([row["z_mid"] for row in subset], dtype=float)
        y = np.asarray([row["weighted_resultant_amplitude"] for row in subset], dtype=float)
        err = np.asarray([row["jackknife_std"] for row in subset], dtype=float)
        ax.errorbar(
            x,
            y,
            yerr=err,
            marker="o",
            ms=3.6,
            lw=1.3,
            capsize=2.0,
            color=colors.get(tracer, COLORS["slate"]),
            linestyle=linestyles.get(cap, "-"),
            alpha=0.9,
            label=label,
        )
    ax.set_xlabel("redshift bin midpoint")
    ax.set_ylabel("weighted resultant amplitude")
    ax.set_title("DESI redshift-jackknife resultant ridge")
    ax.legend(frameon=False, fontsize=7.4, ncol=2)
    fig.tight_layout()
    _save(fig, output)
    return PlotMeta(
        statistics_definitions={
            "figure_lane": "report_data_analysis_current",
            "quantity": "DESI tracer/cap weighted-resultant amplitude by redshift",
            "n_rows": int(len(rows)),
            "tracers": sorted({str(row["tracer"]) for row in rows}),
            "caps": sorted({_label_cap(str(row["label"])) for row in rows}),
            "jackknife_sectors": sorted({int(row["jackknife_sectors"]) for row in rows}),
        },
        sky_support_status=str(payload["manifest"]["sky_support_status"]),
        sky_support=payload["manifest"].get("sky_support"),
        null_mock_status=str(payload["manifest"]["null_mock_status"]),
    )


def _plot_desi_ngc_sgc_asymmetry_surface(output: Path) -> PlotMeta:
    payload = _load_json(OBSERVED_LONGRUN)
    rows = _desi_rows(payload)
    colors = {"BGS": COLORS["blue"], "LRG": COLORS["green"], "QSO": COLORS["purple"]}
    fig, ax = plt.subplots(figsize=(8.4, 4.9))
    _style(ax)
    delta_rows: list[dict[str, float | str]] = []
    for tracer in sorted({str(row["tracer"]) for row in rows}):
        ngc = sorted(
            (
                row
                for row in rows
                if row["tracer"] == tracer and _label_cap(str(row["label"])) == "NGC"
            ),
            key=lambda row: row["z_mid"],
        )
        sgc = sorted(
            (
                row
                for row in rows
                if row["tracer"] == tracer and _label_cap(str(row["label"])) == "SGC"
            ),
            key=lambda row: row["z_mid"],
        )
        x: list[float] = []
        y: list[float] = []
        err: list[float] = []
        for left, right in zip(ngc, sgc):
            z_mid = 0.5 * (float(left["z_mid"]) + float(right["z_mid"]))
            delta = float(left["weighted_resultant_amplitude"]) - float(
                right["weighted_resultant_amplitude"]
            )
            sigma = float(
                np.hypot(float(left["jackknife_std"]), float(right["jackknife_std"]))
            )
            x.append(z_mid)
            y.append(delta)
            err.append(sigma)
            delta_rows.append({"tracer": tracer, "z_mid": z_mid, "delta": delta, "sigma": sigma})
        ax.errorbar(
            x,
            y,
            yerr=err,
            marker="o",
            ms=3.8,
            lw=1.3,
            capsize=2.0,
            color=colors.get(tracer, COLORS["slate"]),
            label=tracer,
        )
    ax.axhline(0.0, color=COLORS["slate"], lw=0.9)
    ax.set_xlabel("redshift bin midpoint")
    ax.set_ylabel("NGC - SGC resultant amplitude")
    ax.set_title("DESI north-south resultant asymmetry by tracer")
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    _save(fig, output)
    return PlotMeta(
        statistics_definitions={
            "figure_lane": "report_data_analysis_current",
            "quantity": "DESI NGC-minus-SGC resultant-amplitude differences",
            "n_delta_rows": int(len(delta_rows)),
            "max_abs_delta": float(max(abs(float(row["delta"])) for row in delta_rows)),
        },
        sky_support_status=str(payload["manifest"]["sky_support_status"]),
        sky_support=payload["manifest"].get("sky_support"),
        null_mock_status=str(payload["manifest"]["null_mock_status"]),
    )


def _plot_desi_tracer_handoff_continuity(output: Path) -> PlotMeta:
    payload = _load_json(OBSERVED_LONGRUN)
    rows = _desi_rows(payload)
    colors = {"BGS": COLORS["blue"], "LRG": COLORS["green"], "QSO": COLORS["purple"]}
    markers = {"NGC": "o", "SGC": "s"}
    n_rows = np.asarray([float(row["n_rows"]) for row in rows], dtype=float)
    sizes = 24.0 + 120.0 * np.sqrt(n_rows / np.nanmax(n_rows))

    fig, ax = plt.subplots(figsize=(8.8, 4.9))
    _style(ax)
    for idx, row in enumerate(rows):
        tracer = str(row["tracer"])
        cap = _label_cap(str(row["label"]))
        ax.errorbar(
            float(row["z_mid"]),
            float(row["weighted_resultant_amplitude"]),
            yerr=float(row["jackknife_std"]),
            marker=markers.get(cap, "o"),
            ms=float(np.sqrt(sizes[idx])),
            color=colors.get(tracer, COLORS["slate"]),
            ecolor="#94a3b8",
            elinewidth=0.8,
            capsize=1.7,
            alpha=0.72,
        )
    for tracer in sorted({str(row["tracer"]) for row in rows}):
        subset = sorted((row for row in rows if row["tracer"] == tracer), key=lambda row: row["z_mid"])
        ax.plot(
            [row["z_mid"] for row in subset],
            [row["weighted_resultant_amplitude"] for row in subset],
            color=colors.get(tracer, COLORS["slate"]),
            alpha=0.28,
            lw=1.2,
            label=tracer,
        )
    ax.set_xlabel("redshift bin midpoint")
    ax.set_ylabel("weighted resultant amplitude")
    ax.set_title("DESI tracer hand-off continuity")
    ax.legend(frameon=False, fontsize=8, title="tracer")
    fig.tight_layout()
    _save(fig, output)
    return PlotMeta(
        statistics_definitions={
            "figure_lane": "report_data_analysis_current",
            "quantity": "DESI tracer hand-off continuity with occupancy-scaled markers",
            "n_catalog_rows": int(len(rows)),
            "n_objects_total": int(sum(int(row["n_rows"]) for row in rows)),
        },
        sky_support_status=str(payload["manifest"]["sky_support_status"]),
        sky_support=payload["manifest"].get("sky_support"),
        null_mock_status=str(payload["manifest"]["null_mock_status"]),
    )


def _plot_cf4_radial_velocity_sign_transition(output: Path) -> PlotMeta:
    payload = _load_json(OBSERVED_LONGRUN)
    rows = _cf4_radius_rows(payload)
    radius = np.asarray([row["radius_mid_mpc_h"] for row in rows], dtype=float)
    mean = np.asarray([row["vr_mean_km_s"] for row in rows], dtype=float)
    lo = np.asarray([row["vr_bootstrap_p16_km_s"] for row in rows], dtype=float)
    hi = np.asarray([row["vr_bootstrap_p84_km_s"] for row in rows], dtype=float)
    counts = np.asarray([row["n_rows"] for row in rows], dtype=float)

    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    _style(ax)
    ax.fill_between(radius, lo, hi, color=COLORS["cyan"], alpha=0.22, label="bootstrap p16-p84")
    ax.plot(radius, mean, marker="o", color=COLORS["blue"], lw=1.5, label="mean radial velocity")
    ax.axhline(0.0, color=COLORS["slate"], lw=0.9)
    ax.set_xlabel("radius midpoint [Mpc/h]")
    ax.set_ylabel("radial velocity mean [km/s]")
    ax.set_title("CF4 radial velocity sign-transition diagnostic")
    ax2 = ax.twinx()
    ax2.fill_between(radius, 0.0, counts, color=COLORS["muted"], alpha=0.12, step="mid")
    ax2.set_ylabel("rows per radial bin")
    ax2.grid(False)
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    fig.tight_layout()
    _save(fig, output)
    return PlotMeta(
        statistics_definitions={
            "figure_lane": "report_data_analysis_current",
            "quantity": "CF4 radial-shell mean velocity with bootstrap band",
            "n_radius_bins": int(len(rows)),
            "min_vr_mean_km_s": float(np.nanmin(mean)),
            "max_vr_mean_km_s": float(np.nanmax(mean)),
        },
        null_mock_status=str(payload["manifest"]["null_mock_status"]),
    )


def _plot_cf4_radial_delta_stability(output: Path) -> PlotMeta:
    payload = _load_json(OBSERVED_LONGRUN)
    rows = _cf4_radius_rows(payload)
    radius = np.asarray([row["radius_mid_mpc_h"] for row in rows], dtype=float)
    mean = np.asarray([row["delta_mean"] for row in rows], dtype=float)
    lo = np.asarray([row["delta_p16"] for row in rows], dtype=float)
    hi = np.asarray([row["delta_p84"] for row in rows], dtype=float)
    counts = np.asarray([row["n_rows"] for row in rows], dtype=float)

    fig, axes = plt.subplots(2, 1, figsize=(8.2, 5.6), sharex=True)
    axes[0].fill_between(radius, lo, hi, color=COLORS["orange"], alpha=0.22, label="bootstrap p16-p84")
    axes[0].plot(radius, mean, marker="o", color=COLORS["orange"], lw=1.4, label="delta mean")
    axes[0].axhline(0.0, color=COLORS["slate"], lw=0.9)
    axes[0].set_ylabel("delta summary")
    axes[0].legend(frameon=False, fontsize=8)
    axes[1].bar(radius, counts, width=np.maximum(5.0, np.gradient(radius)), color=COLORS["blue"], alpha=0.55)
    axes[1].set_xlabel("radius midpoint [Mpc/h]")
    axes[1].set_ylabel("rows")
    for ax in axes:
        _style(ax)
    fig.suptitle("CF4 radial delta-stability diagnostic", fontsize=12)
    fig.tight_layout()
    _save(fig, output)
    return PlotMeta(
        statistics_definitions={
            "figure_lane": "report_data_analysis_current",
            "quantity": "CF4 radial-shell delta mean and bootstrap band",
            "n_radius_bins": int(len(rows)),
            "delta_mean_range": [float(np.nanmin(mean)), float(np.nanmax(mean))],
        },
        null_mock_status=str(payload["manifest"]["null_mock_status"]),
    )


def _plot_cf4_forward_coverage_residual(output: Path) -> PlotMeta:
    _reject_cf4_p0_figure_builder("fig_data_cf4_forward_coverage_residual.png")
    payload = _load_json(CF4_BULKFLOW_LIKELIHOOD)
    rows = payload["depth_windows"]
    depth = np.asarray([row["depth_mpc"] for row in rows], dtype=float)
    bulk = np.asarray([row["bulk_amplitude_kms"] for row in rows], dtype=float)
    recovered = np.asarray([row["forward_mock_recovered_kms"] for row in rows], dtype=float)
    coverage = np.asarray([row["forward_mock_coverage_1sigma"] for row in rows], dtype=float)
    residual = recovered - bulk

    fig, axes = plt.subplots(2, 1, figsize=(8.0, 5.5), sharex=True)
    axes[0].axhline(0.0, color=COLORS["slate"], lw=0.9)
    axes[0].plot(depth, residual, marker="o", color=COLORS["red"], lw=1.5)
    axes[0].set_ylabel("mock recovered - data |B| [km/s]")
    axes[1].plot(depth, coverage, marker="s", color=COLORS["green"], lw=1.5)
    axes[1].axhline(0.68, color=COLORS["slate"], lw=0.9, ls="--")
    axes[1].set_xlabel("depth window [Mpc]")
    axes[1].set_ylabel("1-sigma coverage")
    for ax in axes:
        _style(ax)
    fig.suptitle("CF4 forward-coverage residual by depth", fontsize=12)
    fig.tight_layout()
    _save(fig, output)
    return PlotMeta(
        statistics_definitions={
            "figure_lane": "report_data_analysis_current",
            "quantity": "CF4 depth-window forward-mock residual and coverage",
            "n_depth_windows": int(len(rows)),
            "residual_km_s_range": [float(np.nanmin(residual)), float(np.nanmax(residual))],
        },
        null_mock_status=str(payload["null_mock_status"]),
    )


def _plot_cf4_depth_apex_phase_portrait(output: Path) -> PlotMeta:
    apex = _load_json(CF4_APEX_DEPTH)
    lowell = _load_json(LOWELL_MORPHOLOGY)
    shells = sorted(apex["shells"], key=lambda row: row["r_mean_mpch"])
    radius = np.asarray([row["r_mean_mpch"] for row in shells], dtype=float)
    l_deg = np.asarray([row["apex_galactic_l_deg"] for row in shells], dtype=float)
    b_deg = np.asarray([row["apex_galactic_b_deg"] for row in shells], dtype=float)
    angle_cmb = np.asarray([row["apex_angle_to_cmb_dipole_deg"] for row in shells], dtype=float)
    drift_full = np.asarray([row["apex_drift_from_full_sample_deg"] for row in shells], dtype=float)
    amplitude = np.asarray([row["bulk_magnitude_kms"] for row in shells], dtype=float)
    cmb_l, cmb_b = apex["cmb_dipole_apex_galactic_lb_deg"]
    full_l, full_b = apex["full_sample_apex_galactic_lb_deg"]
    low_l, low_b = lowell["low_ell_preferred_axis_galactic_lb_deg"]
    angle_lowell = np.asarray(
        [
            _angular_sep_deg(float(lon), float(lat), float(low_l), float(low_b), antipodal=True)
            for lon, lat in zip(l_deg, b_deg)
        ],
        dtype=float,
    )

    fig = plt.figure(figsize=(9.2, 7.0))
    ax0 = fig.add_subplot(211, projection="mollweide")
    sc = ax0.scatter(
        _wrap_mollweide_lon(l_deg),
        np.deg2rad(b_deg),
        c=radius,
        s=44,
        cmap="viridis",
        edgecolor="white",
        linewidth=0.6,
        zorder=4,
    )
    ax0.plot(_wrap_mollweide_lon(l_deg), np.deg2rad(b_deg), color=COLORS["slate"], lw=1.0, alpha=0.55)
    _plot_galactic_marker(ax0, float(cmb_l), float(cmb_b), label="CMB dipole", color=COLORS["red"], marker="*")
    _plot_galactic_marker(ax0, float(full_l), float(full_b), label="CF4 full sample", color=COLORS["blue"], marker="D")
    _plot_galactic_marker(ax0, float(low_l), float(low_b), label="low-ell axis", color=COLORS["purple"], marker="X")
    ax0.grid(True, alpha=0.25)
    ax0.set_title("CF4 depth-apex phase portrait")
    ax0.legend(frameon=False, fontsize=7.4, loc="lower left")
    cb = fig.colorbar(sc, ax=ax0, shrink=0.72, pad=0.08)
    cb.set_label("shell radius [Mpc/h]")

    ax1 = fig.add_subplot(212)
    _style(ax1)
    ax1.plot(radius, angle_cmb, marker="o", color=COLORS["red"], lw=1.3, label="angle to CMB dipole")
    ax1.plot(radius, angle_lowell, marker="s", color=COLORS["purple"], lw=1.3, label="axis angle to low-ell")
    ax1.plot(radius, drift_full, marker="^", color=COLORS["blue"], lw=1.3, label="drift from full sample")
    ax1.set_xlabel("shell radius [Mpc/h]")
    ax1.set_ylabel("angle [deg]")
    ax2 = ax1.twinx()
    ax2.plot(radius, amplitude, color=COLORS["slate"], lw=1.0, alpha=0.45, label="|B|")
    ax2.set_ylabel("|B| [km/s]")
    ax2.grid(False)
    ax1.legend(frameon=False, fontsize=8, loc="upper left")
    fig.tight_layout()
    _save(fig, output)
    return PlotMeta(
        statistics_definitions={
            "figure_lane": "report_data_analysis_current",
            "quantity": "CF4 shell apex track and angular separations",
            "n_shells": int(len(shells)),
            "radius_range_mpc_h": [float(radius.min()), float(radius.max())],
            "full_sample_bulk_magnitude_kms": float(apex["full_sample_bulk_magnitude_kms"]),
        },
        sky_support_status="not_directional",
        null_mock_status=str(apex["null_mock_status"]),
        transfer_source="external_proxy_cf4_wf_reconstruction",
    )


def _plot_cf4_shell_apex_separation_matrix(output: Path) -> PlotMeta:
    apex = _load_json(CF4_APEX_DEPTH)
    shells = sorted(apex["shells"], key=lambda row: row["r_mean_mpch"])
    labels = [f"{int(row['r_lo_mpch'])}-{int(row['r_hi_mpch'])}" for row in shells]
    coords = [(float(row["apex_galactic_l_deg"]), float(row["apex_galactic_b_deg"])) for row in shells]
    labels.extend(["full", "CMB"])
    coords.append(tuple(float(value) for value in apex["full_sample_apex_galactic_lb_deg"]))
    coords.append(tuple(float(value) for value in apex["cmb_dipole_apex_galactic_lb_deg"]))
    matrix = np.zeros((len(coords), len(coords)), dtype=float)
    for i, (l1, b1) in enumerate(coords):
        for j, (l2, b2) in enumerate(coords):
            matrix[i, j] = _angular_sep_deg(l1, b1, l2, b2)

    fig, ax = plt.subplots(figsize=(7.4, 6.2))
    image = ax.imshow(matrix, cmap="magma_r", vmin=0.0, vmax=180.0)
    ax.set_xticks(np.arange(len(labels)), labels, rotation=45, ha="right", fontsize=8)
    ax.set_yticks(np.arange(len(labels)), labels, fontsize=8)
    for i in range(len(labels)):
        for j in range(len(labels)):
            ax.text(j, i, f"{matrix[i, j]:.0f}", ha="center", va="center", fontsize=6.8, color="#111827")
    ax.set_title("CF4 shell-to-shell apex separation matrix")
    cb = fig.colorbar(image, ax=ax, shrink=0.78)
    cb.set_label("angular separation [deg]")
    fig.tight_layout()
    _save(fig, output)
    return PlotMeta(
        statistics_definitions={
            "figure_lane": "report_data_analysis_current",
            "quantity": "CF4 shell/full/CMB apex pairwise angular separations",
            "n_directions": int(len(labels)),
            "max_shell_shell_separation_deg": float(np.nanmax(matrix[: len(shells), : len(shells)])),
        },
        sky_support_status="not_directional",
        null_mock_status=str(apex["null_mock_status"]),
        transfer_source="external_proxy_cf4_wf_reconstruction",
    )


def _plot_k5_cf4_vs_affine_consistency(output: Path) -> PlotMeta:
    _reject_cf4_p0_figure_builder("fig_data_k5_cf4_vs_affine_consistency.png")
    k5 = _load_json(K5_CF4_RELEASE_COVERAGE)
    affine = _load_json(CF4_AFFINE_FLOW)
    measured = k5["measured_bulk"]
    coverage = k5["coverage"]
    shells = k5["depth_shells"]
    affine_rows = affine["radius_sweep"]
    shell_mid = np.asarray(
        [0.5 * (row["cz_lo_kms"] + row["cz_hi_kms"]) for row in shells],
        dtype=float,
    )
    shell_amp = np.asarray([row["bulk_amplitude_kms"] for row in shells], dtype=float)
    shell_err = np.asarray([row["bulk_amplitude_error_kms"] for row in shells], dtype=float)
    radius = np.asarray([row["radius_mpc"] for row in affine_rows], dtype=float)
    affine_amp = np.asarray([row["bulk_amplitude_kms"] for row in affine_rows], dtype=float)

    fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.4))
    for ax in axes:
        _style(ax)
    axes[0].errorbar(
        shell_mid,
        shell_amp,
        yerr=shell_err,
        marker="o",
        color=COLORS["blue"],
        ecolor="#93c5fd",
        capsize=2.0,
        lw=1.1,
    )
    axes[0].axhline(float(measured["amplitude_kms"]), color=COLORS["slate"], lw=1.0)
    axes[0].fill_between(
        [float(shell_mid.min()), float(shell_mid.max())],
        float(measured["amplitude_kms"]) - float(coverage["total_amplitude_error_kms"]),
        float(measured["amplitude_kms"]) + float(coverage["total_amplitude_error_kms"]),
        color=COLORS["blue"],
        alpha=0.12,
    )
    axes[0].set_xlabel("K5 shell cz midpoint [km/s]")
    axes[0].set_ylabel("bulk amplitude [km/s]")
    axes[0].set_title("Group-catalog GLS depth shells")

    axes[1].plot(radius, affine_amp, marker="s", color=COLORS["green"], lw=1.4)
    axes[1].axhline(float(measured["amplitude_kms"]), color=COLORS["slate"], lw=1.0, label="K5 full |B|")
    axes[1].fill_between(
        [float(radius.min()), float(radius.max())],
        float(measured["amplitude_kms"]) - float(coverage["total_amplitude_error_kms"]),
        float(measured["amplitude_kms"]) + float(coverage["total_amplitude_error_kms"]),
        color=COLORS["blue"],
        alpha=0.12,
        label="K5 total error band",
    )
    axes[1].set_xlabel("CF4++ WF affine radius [Mpc]")
    axes[1].set_ylabel("bulk amplitude [km/s]")
    axes[1].set_title("WF affine bulk scale")
    axes[1].legend(frameon=False, fontsize=8)
    fig.suptitle("K5 group-GLS and CF4++ WF affine bulk consistency", fontsize=12)
    fig.tight_layout()
    _save(fig, output)
    return PlotMeta(
        statistics_definitions={
            "figure_lane": "report_data_analysis_current",
            "quantity": "K5 group-GLS bulk amplitude compared with CF4++ WF affine bulk scale",
            "k5_full_bulk_km_s": float(measured["amplitude_kms"]),
            "affine_bulk_range_km_s": [float(affine_amp.min()), float(affine_amp.max())],
        },
        null_mock_status="conditional_release_matched_gaussian_bulk_flow_mocks",
        transfer_source="mixed_none_and_external_proxy_cf4_wf_reconstruction",
    )


def _plot_cf4_affine_gradient_spectrum(output: Path) -> PlotMeta:
    affine = _load_json(CF4_AFFINE_FLOW)
    rows = affine["radius_sweep"]
    radius = np.asarray([row["radius_mpc"] for row in rows], dtype=float)
    bulk = np.asarray([row["bulk_amplitude_kms"] for row in rows], dtype=float)
    expansion = np.asarray([row["expansion_kms_per_mpc"] for row in rows], dtype=float)
    shear = np.asarray([row["shear_amplitude_kms_per_mpc"] for row in rows], dtype=float)
    vort = np.asarray([row["vorticity_amplitude_kms_per_mpc"] for row in rows], dtype=float)
    ratio = np.divide(vort, shear, out=np.zeros_like(vort), where=shear > 0.0)

    fig, axes = plt.subplots(1, 3, figsize=(12.0, 4.1))
    for ax in axes:
        _style(ax)
    axes[0].plot(radius, bulk, marker="o", color=COLORS["blue"], lw=1.4)
    axes[0].set_xlabel("radius [Mpc]")
    axes[0].set_ylabel("|B| [km/s]")
    axes[0].set_title("bulk")
    axes[1].axhline(0.0, color=COLORS["slate"], lw=0.8)
    axes[1].plot(radius, expansion, marker="o", color=COLORS["orange"], lw=1.4, label="expansion")
    axes[1].plot(radius, shear, marker="s", color=COLORS["green"], lw=1.4, label="shear")
    axes[1].set_xlabel("radius [Mpc]")
    axes[1].set_ylabel("gradient [km/s/Mpc]")
    axes[1].set_title("symmetric gradient sectors")
    axes[1].legend(frameon=False, fontsize=8)
    axes[2].plot(radius, vort, marker="o", color=COLORS["red"], lw=1.4, label="vorticity")
    axes[2].plot(radius, ratio, marker="s", color=COLORS["purple"], lw=1.4, label="vorticity/shear")
    axes[2].set_yscale("log")
    axes[2].set_xlabel("radius [Mpc]")
    axes[2].set_title("curl-suppressed sector")
    axes[2].legend(frameon=False, fontsize=8)
    fig.suptitle("CF4 affine gradient spectrum", fontsize=12)
    fig.tight_layout()
    _save(fig, output)
    return PlotMeta(
        statistics_definitions={
            "figure_lane": "report_data_analysis_current",
            "quantity": "CF4 affine bulk, expansion, shear, and vorticity sectors",
            "n_radii": int(len(rows)),
            "vorticity_over_shear_max": float(np.nanmax(ratio)),
        },
        null_mock_status=str(affine["null_mock_status"]),
        transfer_source=str(affine["transfer_source"]),
    )


def _plot_k1_lowell_tensor_conditioning(output: Path) -> PlotMeta:
    lowell = _load_json(LOWELL_MORPHOLOGY)
    morph = lowell["morphology_feature_payload"]
    eigenvalues = np.asarray(morph["eigenvalues"], dtype=float)
    gaps = np.asarray(morph["eigenvalue_gaps"], dtype=float)
    metrics = {
        "effective\nrank": float(morph["effective_rank"]),
        "condition\nnumber": float(morph["condition_number"]),
        "tensor\nrank": float(morph["tensor_rank"]),
    }
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 4.4))
    for ax in axes:
        _style(ax)
    axes[0].bar(["lambda1", "lambda2", "lambda3"], eigenvalues, color=COLORS["blue"], alpha=0.72)
    axes[0].set_ylabel("morphology tensor eigenvalue")
    axes[0].set_title("tensor spectrum")
    axes[1].bar(["gap12", "gap23"], gaps, color=COLORS["green"], alpha=0.68, label="gaps")
    ax2 = axes[1].twinx()
    ax2.plot(list(metrics.keys()), list(metrics.values()), marker="o", color=COLORS["red"], lw=1.1)
    ax2.set_ylabel("rank/condition metrics")
    ax2.grid(False)
    axes[1].set_title("axis conditioning")
    fig.suptitle("K1 low-ell tensor conditioning panel", fontsize=12)
    fig.tight_layout()
    _save(fig, output)
    return PlotMeta(
        statistics_definitions={
            "figure_lane": "report_data_analysis_current",
            "quantity": "K1 low-ell morphology tensor eigenvalues and conditioning",
            "effective_rank": float(morph["effective_rank"]),
            "condition_number": float(morph["condition_number"]),
            "axis_identifiability_status": str(morph["axis_identifiability_status"]),
        },
        sky_support_status="not_directional",
        null_mock_status=str(lowell["null_mock_status"]),
    )


def _plot_k1_maxscan_waterfall(output: Path) -> PlotMeta:
    k1 = _load_json(K1_GLOBAL_MAXSCAN)
    stats = list(k1["statistics"])
    maps = {"SMICA": k1["smica"], "Commander": k1["commander"]}
    x = np.arange(len(stats), dtype=float)
    width = 0.36
    fig, ax = plt.subplots(figsize=(9.6, 4.8))
    _style(ax)
    for idx, (name, payload) in enumerate(maps.items()):
        scores = np.asarray([-np.log10(float(payload["local_p"][stat])) for stat in stats], dtype=float)
        ax.bar(x + (idx - 0.5) * width, scores, width=width, label=name)
    ax.set_xticks(x, [stat.replace("_", "\n") for stat in stats], fontsize=8)
    ax.set_ylabel("-log10 local tail probability")
    ax.set_title("K1 max-scan contribution waterfall")
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    _save(fig, output)
    return PlotMeta(
        statistics_definitions={
            "figure_lane": "report_data_analysis_current",
            "quantity": "K1 local statistics contributing to global max-scan",
            "smica_global_p": float(k1["smica"]["global_p"]),
            "commander_global_p": float(k1["commander"]["global_p"]),
            "statistics": stats,
        },
        null_mock_status="isotropic_lcdm_grf_global_max_scan",
    )


def _plot_k1_scalar_biposh_map_stability(output: Path) -> PlotMeta:
    k1 = _load_json(K1_GLOBAL_MAXSCAN)
    biposh = _load_json(K1_BIPOSH_SMICA)
    maps = ["smica", "commander"]
    scalar_p = np.asarray([float(k1[name]["global_p"]) for name in maps], dtype=float)
    biposh_p = np.asarray([float(biposh["results"][name]["global_p"]) for name in maps], dtype=float)
    matrix = -np.log10(np.vstack([scalar_p, biposh_p]).T)
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.2))
    _style(axes[0])
    axes[0].scatter(-np.log10(scalar_p), -np.log10(biposh_p), s=80, color=COLORS["purple"], edgecolor="white")
    for name, xval, yval in zip(maps, -np.log10(scalar_p), -np.log10(biposh_p)):
        axes[0].annotate(
            name.upper(),
            (xval, yval),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=8,
            clip_on=True,
        )
    axes[0].margins(x=0.18, y=0.28)
    axes[0].set_xlabel("scalar max-scan -log10 global tail")
    axes[0].set_ylabel("BiPoSH -log10 global tail")
    axes[0].set_title("map stability scatter")
    im = axes[1].imshow(matrix, cmap="viridis", aspect="auto")
    axes[1].set_yticks(np.arange(len(maps)), [name.upper() for name in maps])
    axes[1].set_xticks([0, 1], ["scalar", "BiPoSH"])
    axes[1].set_title("two-channel tail matrix")
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            axes[1].text(j, i, f"{matrix[i, j]:.2f}", ha="center", va="center", color="white", fontsize=8)
    fig.colorbar(im, ax=axes[1], shrink=0.74, label="-log10 global tail")
    fig.suptitle("K1 scalar/BiPoSH map-stability matrix", fontsize=12)
    fig.tight_layout()
    _save(fig, output)
    return PlotMeta(
        statistics_definitions={
            "figure_lane": "report_data_analysis_current",
            "quantity": "K1 scalar and BiPoSH global-tail comparison across maps",
            "smica_scalar_global_p": float(scalar_p[0]),
            "commander_scalar_global_p": float(scalar_p[1]),
            "smica_biposh_global_p": float(biposh_p[0]),
            "commander_biposh_global_p": float(biposh_p[1]),
        },
        null_mock_status="scalar_grf_and_biposh_matched_power_isotropic_nulls",
    )


def _plot_observed_sector_response_vector(output: Path) -> PlotMeta:
    _reject_cf4_p0_figure_builder("fig_data_observed_sector_response_vector.png")
    joint = _load_json(PR08_JOINT_ARTIFACT)
    sectors = joint["sectors"]
    fig, axes = plt.subplots(1, 3, figsize=(11.2, 4.1))
    for ax in axes:
        _style(ax)
    sigma = sectors["Sigma2"]
    axes[0].bar(
        ["SMICA", "Commander"],
        [-np.log10(float(sigma["global_p_smica"])), -np.log10(float(sigma["global_p_commander"]))],
        color=[COLORS["blue"], COLORS["cyan"]],
        alpha=0.75,
    )
    axes[0].set_ylabel("-log10 global tail")
    axes[0].set_title("Sigma2 data coordinate")
    omega = sectors["Omega_tilt"]
    axes[1].bar(["CF4 |B|"], [float(omega["value_kms"])], color=COLORS["green"], alpha=0.75)
    axes[1].errorbar(
        [0],
        [float(omega["value_kms"])],
        yerr=[float(omega["error_kms"])],
        color=COLORS["slate"],
        capsize=3.0,
        fmt="none",
    )
    axes[1].set_ylabel("km/s")
    axes[1].set_title("Omega_tilt data coordinate")
    w2 = sectors["W2"]
    axes[2].bar(["max W/shear"], [float(w2["vorticity_over_shear_max"])], color=COLORS["red"], alpha=0.75)
    axes[2].set_ylabel("ratio")
    axes[2].set_title("W2 reconstruction coordinate")
    fig.suptitle("Observed-sector response vector from available data coordinates", fontsize=12)
    fig.tight_layout()
    _save(fig, output)
    return PlotMeta(
        statistics_definitions={
            "figure_lane": "report_data_analysis_current",
            "quantity": "Available observed-sector coordinates without sector promotion",
            "sigma2_global_p_smica": float(sigma["global_p_smica"]),
            "sigma2_global_p_commander": float(sigma["global_p_commander"]),
            "omega_tilt_value_km_s": float(omega["value_kms"]),
            "omega_tilt_error_km_s": float(omega["error_kms"]),
            "w2_vorticity_over_shear_max": float(w2["vorticity_over_shear_max"]),
        },
        null_mock_status="mixed_by_sector",
        transfer_source="mixed_none_and_external_proxy_cf4_wf_reconstruction",
    )


def _plot_k1_k5_joint_diagnostic_axes(output: Path) -> PlotMeta:
    _reject_cf4_p0_figure_builder("fig_data_k1_k5_joint_diagnostic_axes.png")
    k1 = _load_json(K1_GLOBAL_MAXSCAN)
    k5 = _load_json(K5_CF4_RELEASE_COVERAGE)
    x = np.asarray(
        [-np.log10(float(k1["smica"]["global_p"])), -np.log10(float(k1["commander"]["global_p"]))],
        dtype=float,
    )
    y = np.asarray(
        [
            float(k5["coverage"]["measurement_noise_only"]["amplitude_coverage"]),
            float(k5["coverage"]["cosmic_variance_inclusive"]["amplitude_coverage"]),
        ],
        dtype=float,
    )
    fig, ax = plt.subplots(figsize=(6.4, 5.2))
    _style(ax)
    points = [
        ("SMICA x meas-only", x[0], y[0], COLORS["red"]),
        ("SMICA x CV-inclusive", x[0], y[1], COLORS["green"]),
        ("Commander x meas-only", x[1], y[0], COLORS["orange"]),
        ("Commander x CV-inclusive", x[1], y[1], COLORS["blue"]),
    ]
    for label, xpos, ypos, color in points:
        ax.scatter(xpos, ypos, s=72, color=color, edgecolor="white", linewidth=0.7, label=label)
    ax.axhline(0.68, color=COLORS["slate"], ls="--", lw=0.9, label="0.68 reference")
    ax.set_xlabel("K1 -log10 global tail")
    ax.set_ylabel("K5 amplitude coverage")
    ax.set_title("K1-K5 joint diagnostic axes")
    ax.legend(frameon=False, fontsize=7.2)
    fig.tight_layout()
    _save(fig, output)
    return PlotMeta(
        statistics_definitions={
            "figure_lane": "report_data_analysis_current",
            "quantity": "K1 global-tail coordinate crossed with K5 coverage coordinate",
            "joint_null_status": "not_bound_no_joint_probability_reported",
            "smica_global_p": float(k1["smica"]["global_p"]),
            "commander_global_p": float(k1["commander"]["global_p"]),
            "k5_measurement_only_coverage": float(y[0]),
            "k5_cosmic_variance_inclusive_coverage": float(y[1]),
        },
        null_mock_status="separate_k1_and_k5_nulls_no_joint_null",
    )


def _plot_k5_cf4_bulk_flow_coverage(output: Path) -> PlotMeta:
    _reject_cf4_p0_figure_builder("fig_data_k5_cf4_bulk_flow_coverage.png")
    k5 = _load_json(K5_CF4_RELEASE_COVERAGE)
    measured = k5["measured_bulk"]
    coverage = k5["coverage"]
    shells = k5["depth_shells"]

    shell_mid = np.asarray(
        [0.5 * (row["cz_lo_kms"] + row["cz_hi_kms"]) for row in shells],
        dtype=float,
    )
    shell_width = np.asarray(
        [row["cz_hi_kms"] - row["cz_lo_kms"] for row in shells],
        dtype=float,
    )
    shell_amp = np.asarray([row["bulk_amplitude_kms"] for row in shells], dtype=float)
    shell_err = np.asarray([row["bulk_amplitude_error_kms"] for row in shells], dtype=float)
    shell_counts = np.asarray([row["n_groups"] for row in shells], dtype=float)

    fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.4))
    ax0, ax1 = axes
    _style(ax0)
    _style(ax1)

    ax0.errorbar(
        shell_mid,
        shell_amp,
        yerr=shell_err,
        fmt="o",
        ms=4.5,
        color=COLORS["blue"],
        ecolor="#93c5fd",
        elinewidth=1.0,
        capsize=2.0,
        label="depth shells",
    )
    ax0.axhline(
        float(measured["amplitude_kms"]),
        color=COLORS["slate"],
        lw=1.1,
        label="full CF4 |B|",
    )
    ax0.fill_between(
        [float(shell_mid.min() - 0.5 * shell_width[0]), float(shell_mid.max() + 0.5 * shell_width[-1])],
        float(measured["amplitude_kms"]) - float(coverage["total_amplitude_error_kms"]),
        float(measured["amplitude_kms"]) + float(coverage["total_amplitude_error_kms"]),
        color=COLORS["blue"],
        alpha=0.12,
        label="total amplitude error",
    )
    ax0.set_xlabel("CMB-frame shell cz [km/s]")
    ax0.set_ylabel("bulk-flow amplitude [km/s]")
    ax0.set_title("CF4 bulk flow by depth")
    ax0.legend(frameon=False, fontsize=8)

    ax_counts = ax0.twinx()
    ax_counts.bar(
        shell_mid,
        shell_counts,
        width=0.72 * shell_width,
        color=COLORS["muted"],
        alpha=0.16,
        zorder=0,
    )
    ax_counts.set_ylabel("groups per shell")
    ax_counts.grid(False)
    ax_counts.spines["right"].set_color("#cbd5e1")

    cov_labels = ["measurement\nonly", "cosmic-variance\ninclusive"]
    cov_values = [
        float(coverage["measurement_noise_only"]["amplitude_coverage"]),
        float(coverage["cosmic_variance_inclusive"]["amplitude_coverage"]),
    ]
    ax1.bar(cov_labels, cov_values, color=[COLORS["red"], COLORS["green"]], alpha=0.78)
    ax1.axhline(0.68, color=COLORS["slate"], ls="--", lw=1.0, label="nominal 0.68")
    ax1.set_ylim(0.0, 1.0)
    ax1.set_ylabel("amplitude coverage")
    ax1.set_title(
        f"CF4 |B| = {float(measured['amplitude_kms']):.0f} +/- "
        f"{float(coverage['total_amplitude_error_kms']):.0f} km/s"
    )
    ax1.legend(frameon=False, fontsize=8)

    fig.tight_layout()
    _save(fig, output)
    return PlotMeta(
        statistics_definitions={
            "figure_lane": "report_data_analysis_current",
            "quantity": "K5 CF4 bulk-flow coverage and depth-shell amplitudes",
            "measured_bulk_amplitude_kms": float(measured["amplitude_kms"]),
            "measurement_amplitude_error_kms": float(coverage["measurement_amplitude_error_kms"]),
            "total_amplitude_error_kms": float(coverage["total_amplitude_error_kms"]),
            "measurement_only_coverage": cov_values[0],
            "cosmic_variance_inclusive_coverage": cov_values[1],
            "n_groups": int(measured["n_groups"]),
            "n_mock": int(k5["config"]["n_mock"]),
        },
        null_mock_status="conditional_release_matched_gaussian_bulk_flow_mocks",
        transfer_source="none",
    )


def _plot_k6_cf4_wf_curl_shear_diagnostic(output: Path) -> PlotMeta:
    k6 = _load_json(K6_CF4_CURL_POSTERIOR)
    keys = sorted(k6["per_radius"], key=lambda key: int(key[1:]))
    radii = np.asarray([float(key[1:]) for key in keys], dtype=float)
    wf_shear = np.asarray(
        [k6["per_radius"][key]["wf_mean_shear_amplitude"] for key in keys],
        dtype=float,
    )
    wf_vort = np.asarray(
        [k6["per_radius"][key]["wf_mean_vorticity_amplitude"] for key in keys],
        dtype=float,
    )
    cr_vort = np.asarray(
        [k6["per_radius"][key]["cr_vorticity_amplitude_median"] for key in keys],
        dtype=float,
    )
    cr_lo = np.asarray(
        [k6["per_radius"][key]["cr_vorticity_amplitude_p16"] for key in keys],
        dtype=float,
    )
    cr_hi = np.asarray(
        [k6["per_radius"][key]["cr_vorticity_amplitude_p84"] for key in keys],
        dtype=float,
    )
    ratio = np.divide(wf_vort, wf_shear, out=np.zeros_like(wf_vort), where=wf_shear > 0.0)

    fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.4))
    ax0, ax1 = axes
    _style(ax0)
    _style(ax1)

    ax0.plot(radii, wf_shear, marker="o", color=COLORS["blue"], label="WF shear")
    ax0.plot(radii, wf_vort, marker="s", color=COLORS["red"], label="WF vorticity")
    ax0.fill_between(radii, cr_lo, cr_hi, color=COLORS["orange"], alpha=0.18, label="CR proxy p16-p84")
    ax0.plot(radii, cr_vort, marker="^", color=COLORS["orange"], label="CR proxy median")
    ax0.set_yscale("log")
    ax0.set_xlabel("analysis radius [Mpc]")
    ax0.set_ylabel("amplitude [km/s/Mpc]")
    ax0.set_title("CF4 WF curl/shear amplitudes")
    ax0.legend(frameon=False, fontsize=8)

    ax1.bar(radii.astype(str), ratio, color=COLORS["purple"], alpha=0.72)
    ax1.axhline(0.01, color=COLORS["slate"], ls="--", lw=1.0, label="1% reference")
    ax1.set_ylabel("WF vorticity / shear")
    ax1.set_xlabel("analysis radius [Mpc]")
    ax1.set_title("Curl channel is reconstruction-suppressed")
    ax1.legend(frameon=False, fontsize=8)

    fig.tight_layout()
    _save(fig, output)
    return PlotMeta(
        statistics_definitions={
            "figure_lane": "report_data_analysis_current",
            "quantity": "K6 CF4 WF curl/shear reconstruction diagnostic",
            "structural_no_go": bool(k6["structural_no_go"]),
            "physical_vorticity_identifiable": False,
            "curl_injection_validated": bool(k6["curl_injection_validated"]),
            "vorticity_over_shear_ratio_max": float(k6["vorticity_over_shear_ratio_max"]),
            "radii_mpc": [float(value) for value in radii],
        },
        null_mock_status="wf_reconstruction_conditioned_cr_proxy_lower_bound",
        transfer_source="external_proxy_cf4_wf_reconstruction",
    )


def _plot_desi_bgs_cf4_targets(output: Path) -> PlotMeta:
    data = _load_desi_targets()
    z = data["z"]
    ra = data["ra"]
    dec = data["dec"]
    weight = data["selected_weight"]
    sample = _sample_indices(z.size, 60_000, salt=29)
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.5), subplot_kw={})
    axes[0].remove()
    ax0 = fig.add_subplot(121, projection="mollweide")
    sc = ax0.scatter(
        _wrap_mollweide_lon(ra[sample]),
        np.deg2rad(dec[sample]),
        c=z[sample],
        s=2.0,
        cmap="viridis",
        alpha=0.68,
        linewidths=0,
    )
    ax0.grid(True, alpha=0.25)
    ax0.set_title("DESI BGS targets selected for CF4 queries")
    cb = fig.colorbar(sc, ax=ax0, shrink=0.72, pad=0.08)
    cb.set_label("redshift z")
    ax1 = axes[1]
    ax1.hist(z, bins=90, weights=weight, color=COLORS["green"], alpha=0.72)
    ax1.set_xlabel("redshift z")
    ax1.set_ylabel("weighted target count")
    _style(ax1)
    fig.tight_layout()
    _save(fig, output)
    return PlotMeta(
        sky_support_status="sky_support_recorded",
        sky_support=_sky_support_from_radec(
            ra,
            dec,
            completeness_status="desi_bgs_cf4_target_coordinate_support",
            selection_mode="desi_bgs_cf4_target_selection",
        ),
        statistics_definitions={
            "figure_lane": "report_data_analysis_current",
            "quantity": "DESI BGS CF4 target sky positions and redshift distribution",
            "n_targets": int(z.size),
            "z_median": float(np.nanmedian(z)),
        },
    )


def _optional_act_dr6_series(relative: str) -> tuple[np.ndarray, np.ndarray, np.ndarray] | None:
    path = REPO_ROOT / relative
    if not path.exists():
        return None
    with np.load(path, allow_pickle=False) as data:
        if not {"ell", "dl", "dl_err"} <= set(data.files):
            return None
        return (
            np.asarray(data["ell"], dtype=float),
            np.asarray(data["dl"], dtype=float),
            np.asarray(data["dl_err"], dtype=float),
        )


def _plot_compact_cmb_high_ell_products(output: Path) -> PlotMeta:
    with np.load(REPO_ROOT / PLANCK_TT, allow_pickle=False) as planck:
        planck_ell = np.asarray(planck["ell"], dtype=float)
        planck_dl = np.asarray(planck["dl"], dtype=float)
        planck_err = 0.5 * (
            np.asarray(planck["err_lo"], dtype=float)
            + np.asarray(planck["err_hi"], dtype=float)
        )
    with np.load(REPO_ROOT / ACT_DR4_COMPACT, allow_pickle=False) as act:
        act_tt = np.asarray(act["clcmb__act_dr4_01_D_ell_TT_cmbonly_txt"], dtype=float)
        act_te = np.asarray(act["clcmb__act_dr4_01_D_ell_TE_cmbonly_txt"], dtype=float)
        act_ee = np.asarray(act["clcmb__act_dr4_01_D_ell_EE_cmbonly_txt"], dtype=float)
    with np.load(REPO_ROOT / SPT3G_Y1_COMPACT, allow_pickle=False) as spt:
        spt_vec = np.ravel(
            np.asarray(spt["bandpowers__SPT3G_2018_TTTEEE_bandpowers_dat"], dtype=float)
        )
        spt_cov = np.asarray(spt["cov__SPT3G_2018_TTTEEE_covariance_dat"], dtype=float)
    with np.load(REPO_ROOT / BICEP_KECK_2018_BB, allow_pickle=False) as bk:
        bk_mat = np.asarray(bk["BK18lf_cl_hat.dat"], dtype=float)

    act_dr6 = {
        "TT": _optional_act_dr6_series(ACT_DR6_TT),
        "TE": _optional_act_dr6_series(ACT_DR6_TE),
        "EE": _optional_act_dr6_series(ACT_DR6_EE),
    }

    fig, axes = plt.subplots(1, 3, figsize=(12.0, 4.4))
    ax0, ax1, ax2 = axes
    ax0.errorbar(
        planck_ell,
        planck_dl,
        yerr=planck_err,
        fmt=".",
        ms=3.0,
        color=COLORS["slate"],
        alpha=0.55,
        label="Planck TT",
    )
    ax0.errorbar(
        act_tt[:, 0],
        act_tt[:, 1],
        yerr=np.abs(act_tt[:, 2]),
        fmt="o",
        ms=3.0,
        color=COLORS["blue"],
        alpha=0.72,
        label="ACT DR4 TT",
    )
    if act_dr6["TT"] is not None:
        ell, dl, err = act_dr6["TT"]
        ax0.errorbar(
            ell,
            dl,
            yerr=np.abs(err),
            fmt="s",
            ms=2.8,
            color=COLORS["red"],
            alpha=0.68,
            label="ACT DR6 TT",
        )
    ax0.set_xlabel("multipole ell")
    ax0.set_ylabel("D_ell")
    ax0.set_title("TT compact bandpowers")
    ax0.legend(fontsize=7, frameon=False)

    for label, arr, color in (
        ("ACT DR4 TE", act_te, COLORS["orange"]),
        ("ACT DR4 EE", act_ee, COLORS["green"]),
    ):
        ax1.errorbar(
            arr[:, 0],
            arr[:, 1],
            yerr=np.abs(arr[:, 2]),
            fmt=".",
            ms=3.0,
            color=color,
            alpha=0.72,
            label=label,
        )
    for label, color in (("TE", COLORS["red"]), ("EE", COLORS["purple"])):
        series = act_dr6[label]
        if series is None:
            continue
        ell, dl, err = series
        ax1.errorbar(
            ell,
            dl,
            yerr=np.abs(err),
            fmt="s",
            ms=2.6,
            color=color,
            alpha=0.62,
            label=f"ACT DR6 {label}",
        )
    ax1.set_xlabel("multipole ell")
    ax1.set_ylabel("D_ell")
    ax1.set_title("polarization compact bandpowers")
    ax1.legend(fontsize=7, frameon=False)

    spt_x = np.linspace(0.0, 1.0, spt_vec.size)
    bk_x = np.linspace(0.0, 1.0, bk_mat.shape[0])
    bk_packed = bk_mat[:, 1:]
    ax2.plot(spt_x, spt_vec, color=COLORS["cyan"], lw=0.55, alpha=0.70, label="SPT-3G packed")
    ax2.plot(
        bk_x,
        np.nanmedian(bk_packed, axis=1),
        color=COLORS["purple"],
        marker="o",
        ms=3.6,
        lw=1.2,
        label="BK18 BB median",
    )
    ax2.fill_between(
        bk_x,
        np.nanpercentile(bk_packed, 16, axis=1),
        np.nanpercentile(bk_packed, 84, axis=1),
        color=COLORS["purple"],
        alpha=0.18,
        linewidth=0,
    )
    ax2.set_xlabel("packed product coordinate")
    ax2.set_ylabel("reported bandpower")
    ax2.set_title("packed SPT/BK products")
    ax2.legend(fontsize=7, frameon=False)
    for ax in axes:
        _style(ax)
    fig.suptitle("Compact CMB high-ell and polarization products", fontsize=12)
    fig.tight_layout()
    _save(fig, output)
    return PlotMeta(
        transfer_source="external_public_cmb_products",
        statistics_definitions={
            "figure_lane": "report_data_analysis_current",
            "quantity": "compact CMB high-ell and polarization product diagnostic",
            "planck_tt_bins": int(planck_ell.size),
            "act_dr4_tt_bins": int(act_tt.shape[0]),
            "act_dr4_te_bins": int(act_te.shape[0]),
            "act_dr4_ee_bins": int(act_ee.shape[0]),
            "act_dr6_present": {key: value is not None for key, value in act_dr6.items()},
            "spt3g_packed_length": int(spt_vec.size),
            "spt3g_covariance_shape": [int(v) for v in spt_cov.shape],
            "bk18_bins": int(bk_mat.shape[0]),
            "bk18_packed_spectra": int(bk_packed.shape[1]),
        },
    )


def _plot_compact_lensing_bandpower_covariance(output: Path) -> PlotMeta:
    with np.load(REPO_ROOT / PLANCK_LENSING, allow_pickle=False) as lens:
        bandpowers = np.asarray(lens["smica_g30_ftl_full_pp_bandpowers.dat"], dtype=float)
        cov = np.asarray(lens["smica_g30_ftl_full_pp_cov.dat"], dtype=float)
    with np.load(REPO_ROOT / CAMB_LENSING_REFS, allow_pickle=False) as camb:
        ell_pp = np.asarray(camb["ell_pp"], dtype=float)
        pp = np.asarray(camb["lens_potential_cls"], dtype=float)[:, 0]

    diag = np.diag(cov)
    scale = np.sqrt(np.maximum(diag, 0.0))
    denom = np.outer(scale, scale)
    corr = np.divide(cov, denom, out=np.zeros_like(cov), where=denom > 0)

    fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.4))
    ax0, ax1 = axes
    ax0.plot(ell_pp[1:], pp[1:], color=COLORS["slate"], lw=1.0, label="CAMB reference")
    ax0.errorbar(
        bandpowers[:, 3],
        bandpowers[:, 4],
        yerr=bandpowers[:, 5],
        xerr=[bandpowers[:, 3] - bandpowers[:, 1], bandpowers[:, 2] - bandpowers[:, 3]],
        fmt="o",
        ms=4.0,
        color=COLORS["purple"],
        ecolor=COLORS["purple"],
        elinewidth=0.8,
        capsize=2.0,
        label="Planck PR3 lensing",
    )
    ax0.set_xscale("log")
    ax0.set_xlabel("lensing multipole L")
    ax0.set_ylabel("bandpower")
    ax0.set_title("Planck lensing bandpowers")
    ax0.legend(fontsize=8, frameon=False)
    _style(ax0)

    im = ax1.imshow(corr, cmap="coolwarm", vmin=-1.0, vmax=1.0, aspect="auto")
    ax1.set_title("bandpower covariance correlation")
    ax1.set_xlabel("bin")
    ax1.set_ylabel("bin")
    fig.colorbar(im, ax=ax1, shrink=0.78, label="correlation")
    fig.suptitle("Compact CMB lensing product diagnostic", fontsize=12)
    fig.tight_layout()
    _save(fig, output)
    finite_corr = corr[np.isfinite(corr)]
    return PlotMeta(
        transfer_source="external_reference",
        statistics_definitions={
            "figure_lane": "report_data_analysis_current",
            "quantity": "Planck PR3 lensing bandpowers and covariance correlation",
            "lensing_bins": int(bandpowers.shape[0]),
            "covariance_shape": [int(v) for v in cov.shape],
            "max_abs_offdiag_correlation": float(
                np.nanmax(np.abs(finite_corr - np.eye(corr.shape[0])[np.isfinite(corr)]))
            )
            if finite_corr.size
            else None,
        },
    )


def _variant_label(relative: str, *, prefix: str, suffix: str) -> str:
    name = Path(relative).name
    if not name.startswith(prefix) or not name.endswith(suffix):
        return name
    return name[len(prefix) : -len(suffix)]


def _load_vector_text(relative: str) -> np.ndarray:
    data = np.loadtxt(REPO_ROOT / relative, comments="#", dtype=float)
    return np.atleast_1d(np.asarray(data, dtype=float))


def _load_two_column_text(relative: str) -> tuple[np.ndarray, np.ndarray]:
    data = np.loadtxt(REPO_ROOT / relative, comments="#", dtype=float)
    data = np.atleast_2d(np.asarray(data, dtype=float))
    return data[:, 0], data[:, 1]


def _plot_act_dr6_lensing_noise_systematics(output: Path) -> PlotMeta:
    bandpower_rows: dict[str, np.ndarray] = {}
    for relative in ACT_DR6_LENSING_BANDPOWERS:
        label = _variant_label(
            relative,
            prefix="clkk_bandpowers_",
            suffix=".txt",
        )
        bandpower_rows[label] = _load_vector_text(relative)

    noise_rows: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for relative in ACT_DR6_LENSING_NOISE_CURVES:
        label = _variant_label(
            relative,
            prefix="N_L_kk_act_dr6_lensing_v1_",
            suffix=".txt",
        )
        ell, noise = _load_two_column_text(relative)
        good = np.isfinite(ell) & np.isfinite(noise) & (ell >= 2.0) & (ell <= 3000.0)
        noise_rows[label] = (ell[good], noise[good])

    filt_ell, filt_value = _load_two_column_text(ACT_DR6_LENSING_BASELINE_FILTER)
    active = filt_value > 0.5
    active_range = [
        int(np.nanmin(filt_ell[active])) if np.any(active) else None,
        int(np.nanmax(filt_ell[active])) if np.any(active) else None,
    ]

    fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.6))
    ax0, ax1 = axes
    _style(ax0)
    _style(ax1)
    color_cycle = [COLORS["blue"], COLORS["green"], COLORS["purple"], COLORS["orange"], COLORS["slate"]]
    for idx, (label, values) in enumerate(bandpower_rows.items()):
        x = np.arange(1, values.size + 1, dtype=float)
        ax0.plot(
            x,
            values,
            marker="o",
            ms=3.3,
            lw=1.2,
            color=color_cycle[idx % len(color_cycle)],
            label=label,
        )
    ax0.set_yscale("log")
    ax0.set_xlabel("bandpower index")
    ax0.set_ylabel("C_L^kk")
    ax0.set_title("ACT DR6 lensing bandpower variants")
    ax0.legend(frameon=False, fontsize=7.2)

    for idx, (label, (ell, noise)) in enumerate(noise_rows.items()):
        stride = max(1, int(np.ceil(ell.size / 900)))
        ax1.plot(
            ell[::stride],
            noise[::stride],
            lw=1.1,
            color=color_cycle[idx % len(color_cycle)],
            alpha=0.9,
            label=label,
        )
    if active_range[0] is not None and active_range[1] is not None:
        ax1.axvspan(active_range[0], active_range[1], color=COLORS["muted"], alpha=0.10, label="baseline filter active")
    ax1.set_yscale("log")
    ax1.set_xlim(2, 3000)
    ax1.set_xlabel("lensing multipole L")
    ax1.set_ylabel("N_L^kk")
    ax1.set_title("ACT DR6 lensing noise curves")
    ax1.legend(frameon=False, fontsize=7.0)
    fig.suptitle("ACT DR6 lensing release diagnostic", fontsize=12)
    fig.tight_layout()
    _save(fig, output)

    baseline_ell, baseline_noise = noise_rows["baseline"]
    curl_ell, curl_noise = noise_rows["curl"]
    common = np.intersect1d(baseline_ell.astype(int), curl_ell.astype(int))
    baseline_interp = np.interp(common, baseline_ell, baseline_noise)
    curl_interp = np.interp(common, curl_ell, curl_noise)
    ratio = np.divide(curl_interp, baseline_interp, out=np.full_like(curl_interp, np.nan), where=baseline_interp > 0)
    return PlotMeta(
        transfer_source="external_public_lensing_products",
        sky_support_status="not_directional",
        null_mock_status="data_product_null_variants_no_mock_calibration",
        statistics_definitions={
            "figure_lane": "report_data_analysis_current",
            "quantity": "ACT DR6 lensing bandpower variants and N_L noise curves",
            "sky_support_note": "release masks are available in Equatorial HEALPix files, but this figure plots bandpower/noise text products rather than sky pixels",
            "bandpower_variants": sorted(bandpower_rows),
            "noise_variants": sorted(noise_rows),
            "bandpower_count_range": [
                int(min(values.size for values in bandpower_rows.values())),
                int(max(values.size for values in bandpower_rows.values())),
            ],
            "baseline_filter_active_L_range": active_range,
            "baseline_noise_points": int(baseline_ell.size),
            "curl_over_baseline_noise_median": float(np.nanmedian(ratio)),
            "source_artifacts": [
                ACT_DR6_LENSING_MANIFEST,
                *ACT_DR6_LENSING_BANDPOWERS,
                *ACT_DR6_LENSING_NOISE_CURVES,
            ],
        },
    )


def _figure_specs() -> tuple[FigureSpec, ...]:
    specs = (
        FigureSpec(
            artifact_id="obsstat.report_data.planck_tt_binned_residual",
            file_name="fig_data_planck_tt_binned_residual.png",
            title="Planck TT binned residual",
            source_paths=(PLANCK_TT, SCRIPT_PATH),
            builder=_plot_planck_tt_binned_residual,
            caption="Planck PR3 binned TT spectrum with bundled best-fit reference and residuals.",
        ),
        FigureSpec(
            artifact_id="obsstat.report_data.planck_smica_masked_temperature",
            file_name="fig_data_planck_smica_masked_temperature.png",
            title="Planck SMICA masked temperature",
            source_paths=(PLANCK_SMICA, PLANCK_TEMP_MASK, SCRIPT_PATH),
            builder=_plot_planck_smica_masked_temperature,
            caption="Planck SMICA nside16 temperature pixels displayed under the PR3 temperature mask.",
        ),
        FigureSpec(
            artifact_id="obsstat.report_data.cf4_catalog_sky_velocity",
            file_name="fig_data_cf4_catalog_sky_velocity.png",
            title="CF4 sky velocity",
            source_paths=(CF4_GROUPS, SCRIPT_PATH),
            builder=_plot_cf4_catalog_sky_velocity,
            caption="Cosmicflows-4 group sky positions colored by catalog peculiar velocity, with the velocity distribution below.",
        ),
        FigureSpec(
            artifact_id="obsstat.report_data.cf4_depth_velocity_profile",
            file_name="fig_data_cf4_depth_velocity_profile.png",
            title="CF4 depth velocity profile",
            source_paths=(CF4_GROUPS, SCRIPT_PATH),
            builder=_plot_cf4_depth_velocity_profile,
            caption="Cosmicflows-4 distance-binned peculiar-velocity percentile profile and group counts.",
        ),
        FigureSpec(
            artifact_id="obsstat.report_data.k5_cf4_bulk_flow_coverage",
            file_name="fig_data_k5_cf4_bulk_flow_coverage.png",
            title="K5 CF4 bulk-flow coverage",
            source_paths=(K5_CF4_RELEASE_COVERAGE, CF4_GROUPS, SCRIPT_PATH),
            builder=_plot_k5_cf4_bulk_flow_coverage,
            caption="Cosmicflows-4 bulk-flow amplitude, shell amplitudes, and conditional coverage from the K5 result.",
        ),
        FigureSpec(
            artifact_id="obsstat.report_data.k6_cf4_wf_curl_shear_diagnostic",
            file_name="fig_data_k6_cf4_wf_curl_shear_diagnostic.png",
            title="K6 CF4 WF curl/shear diagnostic",
            source_paths=(K6_CF4_CURL_POSTERIOR, CF4_WF_GRID, SCRIPT_PATH),
            builder=_plot_k6_cf4_wf_curl_shear_diagnostic,
            caption="CF4 Wiener-filter velocity-field curl/shear diagnostic showing reconstruction-conditioned curl suppression.",
        ),
        FigureSpec(
            artifact_id="obsstat.report_data.compact_cmb_high_ell_products",
            file_name="fig_data_compact_cmb_high_ell_products.png",
            title="Compact CMB high-ell products",
            source_paths=(
                PLANCK_TT,
                ACT_DR4_COMPACT,
                SPT3G_Y1_COMPACT,
                BICEP_KECK_2018_BB,
                ACT_DR6_TT,
                ACT_DR6_TE,
                ACT_DR6_EE,
                APPROVAL_COMPACT_INVENTORY,
                SCRIPT_PATH,
            ),
            builder=_plot_compact_cmb_high_ell_products,
            caption="Compact Planck, ACT, SPT-3G, and BICEP/Keck CMB bandpower products, with ACT DR6 included when locally extracted.",
        ),
        FigureSpec(
            artifact_id="obsstat.report_data.compact_lensing_bandpower_covariance",
            file_name="fig_data_compact_lensing_bandpower_covariance.png",
            title="Compact CMB lensing covariance",
            source_paths=(PLANCK_LENSING, CAMB_LENSING_REFS, APPROVAL_COMPACT_INVENTORY, SCRIPT_PATH),
            builder=_plot_compact_lensing_bandpower_covariance,
            caption="Planck PR3 lensing bandpowers and covariance correlation against the bundled CAMB reference.",
        ),
        FigureSpec(
            artifact_id="obsstat.report_data.act_dr6_lensing_noise_systematics",
            file_name="fig_data_act_dr6_lensing_noise_systematics.png",
            title="ACT DR6 lensing noise/systematics",
            source_paths=(
                ACT_DR6_LENSING_MANIFEST,
                ACT_DR6_LENSING_LIKE_README,
                ACT_DR6_LENSING_MAP_README,
                *ACT_DR6_LENSING_BANDPOWERS,
                *ACT_DR6_LENSING_NOISE_CURVES,
                ACT_DR6_LENSING_BASELINE_FILTER,
                SCRIPT_PATH,
            ),
            builder=_plot_act_dr6_lensing_noise_systematics,
            caption="ACT DR6 lensing bandpower variants and release-provided noise curves; no ACT lensing likelihood or mock-calibrated inference is run.",
        ),
        FigureSpec(
            artifact_id="obsstat.report_data.desi_bgs_cf4_targets",
            file_name="fig_data_desi_bgs_cf4_targets.png",
            title="DESI BGS CF4 targets",
            source_paths=(DESI_CF4_TARGETS, SCRIPT_PATH),
            builder=_plot_desi_bgs_cf4_targets,
            caption="DESI BGS targets selected for CF4 queries, shown by sky position and redshift.",
        ),
        FigureSpec(
            artifact_id="obsstat.report_data.desi_redshift_jackknife_ridge",
            file_name="fig_data_desi_redshift_jackknife_ridge.png",
            title="DESI redshift-jackknife ridge",
            source_paths=OBSERVED_LONGRUN_SOURCES,
            builder=_plot_desi_redshift_jackknife_ridge,
            caption="DESI BGS/LRG/QSO resultant amplitudes by cap and redshift bin with jackknife uncertainty.",
        ),
        FigureSpec(
            artifact_id="obsstat.report_data.desi_ngc_sgc_asymmetry_surface",
            file_name="fig_data_desi_ngc_sgc_asymmetry_surface.png",
            title="DESI NGC-SGC asymmetry surface",
            source_paths=OBSERVED_LONGRUN_SOURCES,
            builder=_plot_desi_ngc_sgc_asymmetry_surface,
            caption="DESI NGC-minus-SGC resultant-amplitude differences as a function of tracer and redshift.",
        ),
        FigureSpec(
            artifact_id="obsstat.report_data.desi_tracer_handoff_continuity",
            file_name="fig_data_desi_tracer_handoff_continuity.png",
            title="DESI tracer hand-off continuity",
            source_paths=OBSERVED_LONGRUN_SOURCES,
            builder=_plot_desi_tracer_handoff_continuity,
            caption="DESI tracer redshift hand-off shown with occupancy-scaled markers and jackknife uncertainty.",
        ),
        FigureSpec(
            artifact_id="obsstat.report_data.cf4_radial_velocity_sign_transition",
            file_name="fig_data_cf4_radial_velocity_sign_transition.png",
            title="CF4 radial velocity sign transition",
            source_paths=(OBSERVED_LONGRUN, "workdir/compact_products/cf4/query_batch.npz", SCRIPT_PATH),
            builder=_plot_cf4_radial_velocity_sign_transition,
            caption="CF4 radial-shell mean velocity with bootstrap p16-p84 band and bin occupancy.",
        ),
        FigureSpec(
            artifact_id="obsstat.report_data.cf4_radial_delta_stability",
            file_name="fig_data_cf4_radial_delta_stability.png",
            title="CF4 radial delta stability",
            source_paths=(OBSERVED_LONGRUN, "workdir/compact_products/cf4/query_batch.npz", SCRIPT_PATH),
            builder=_plot_cf4_radial_delta_stability,
            caption="CF4 radial-shell delta summary with bootstrap band and row counts.",
        ),
        FigureSpec(
            artifact_id="obsstat.report_data.cf4_forward_coverage_residual",
            file_name="fig_data_cf4_forward_coverage_residual.png",
            title="CF4 forward-coverage residual",
            source_paths=(CF4_BULKFLOW_LIKELIHOOD, CF4_GROUPS, SCRIPT_PATH),
            builder=_plot_cf4_forward_coverage_residual,
            caption="CF4 depth-window forward-mock recovered amplitude residuals and coverage curve.",
        ),
        FigureSpec(
            artifact_id="obsstat.report_data.cf4_depth_apex_phase_portrait",
            file_name="fig_data_cf4_depth_apex_phase_portrait.png",
            title="CF4 depth-apex phase portrait",
            source_paths=(CF4_APEX_DEPTH, CF4_P0_BLOCK, LOWELL_MORPHOLOGY, CF4_WF_GRID, PLANCK_SMICA, SCRIPT_PATH),
            builder=_plot_cf4_depth_apex_phase_portrait,
            caption="CF4++ reconstruction-functional shell-apex track with reference axes; method/systematics only while C1-K5-MV-F1 remains OPEN.",
        ),
        FigureSpec(
            artifact_id="obsstat.report_data.cf4_shell_apex_separation_matrix",
            file_name="fig_data_cf4_shell_apex_separation_matrix.png",
            title="CF4 shell apex separation matrix",
            source_paths=(CF4_APEX_DEPTH, CF4_P0_BLOCK, CF4_WF_GRID, SCRIPT_PATH),
            builder=_plot_cf4_shell_apex_separation_matrix,
            caption="Pairwise angular separations among CF4++ reconstruction-functional shell apexes; no observed amplitude or global-tilt claim.",
        ),
        FigureSpec(
            artifact_id="obsstat.report_data.k5_cf4_vs_affine_consistency",
            file_name="fig_data_k5_cf4_vs_affine_consistency.png",
            title="K5 CF4 versus affine consistency",
            source_paths=(K5_CF4_RELEASE_COVERAGE, CF4_AFFINE_FLOW, CF4_GROUPS, CF4_WF_GRID, SCRIPT_PATH),
            builder=_plot_k5_cf4_vs_affine_consistency,
            caption="K5 group-GLS bulk amplitudes compared with CF4++ WF affine bulk scale.",
        ),
        FigureSpec(
            artifact_id="obsstat.report_data.cf4_affine_gradient_spectrum",
            file_name="fig_data_cf4_affine_gradient_spectrum.png",
            title="CF4 affine gradient spectrum",
            source_paths=(CF4_AFFINE_FLOW, CF4_P0_BLOCK, CF4_WF_GRID, SCRIPT_PATH),
            builder=_plot_cf4_affine_gradient_spectrum,
            caption="CF4++ affine reconstruction functionals versus radius; estimator/systematics only while C1-K5-MV-F1 remains OPEN.",
        ),
        FigureSpec(
            artifact_id="obsstat.report_data.k1_lowell_tensor_conditioning",
            file_name="fig_data_k1_lowell_tensor_conditioning.png",
            title="K1 low-ell tensor conditioning",
            source_paths=(LOWELL_MORPHOLOGY, PLANCK_SMICA, PLANCK_COMMANDER, SCRIPT_PATH),
            builder=_plot_k1_lowell_tensor_conditioning,
            caption="K1 low-ell morphology tensor eigenvalues, eigenvalue gaps, and conditioning metrics.",
        ),
        FigureSpec(
            artifact_id="obsstat.report_data.k1_maxscan_waterfall",
            file_name="fig_data_k1_maxscan_waterfall.png",
            title="K1 max-scan waterfall",
            source_paths=(K1_GLOBAL_MAXSCAN, PLANCK_SMICA, PLANCK_COMMANDER, SCRIPT_PATH),
            builder=_plot_k1_maxscan_waterfall,
            caption="K1 local statistic contributions to the global max-scan for SMICA and Commander.",
        ),
        FigureSpec(
            artifact_id="obsstat.report_data.k1_scalar_biposh_map_stability",
            file_name="fig_data_k1_scalar_biposh_map_stability.png",
            title="K1 scalar/BiPoSH map stability",
            source_paths=(K1_GLOBAL_MAXSCAN, K1_BIPOSH_SMICA, PLANCK_SMICA, PLANCK_COMMANDER, SCRIPT_PATH),
            builder=_plot_k1_scalar_biposh_map_stability,
            caption="K1 scalar and BiPoSH two-channel global-tail comparison across map products.",
        ),
        FigureSpec(
            artifact_id="obsstat.report_data.observed_sector_response_vector",
            file_name="fig_data_observed_sector_response_vector.png",
            title="Observed-sector response vector",
            source_paths=(
                PR08_JOINT_ARTIFACT,
                K1_GLOBAL_MAXSCAN,
                K5_CF4_RELEASE_COVERAGE,
                K6_CF4_CURL_POSTERIOR,
                PLANCK_SMICA,
                PLANCK_COMMANDER,
                CF4_GROUPS,
                CF4_WF_GRID,
                SCRIPT_PATH,
            ),
            builder=_plot_observed_sector_response_vector,
            caption="Available observed-sector numeric coordinates without promoting absent sectors.",
        ),
        FigureSpec(
            artifact_id="obsstat.report_data.k1_k5_joint_diagnostic_axes",
            file_name="fig_data_k1_k5_joint_diagnostic_axes.png",
            title="K1-K5 joint diagnostic axes",
            source_paths=(K1_GLOBAL_MAXSCAN, K5_CF4_RELEASE_COVERAGE, PLANCK_SMICA, PLANCK_COMMANDER, CF4_GROUPS, SCRIPT_PATH),
            builder=_plot_k1_k5_joint_diagnostic_axes,
            caption="K1 global-tail coordinates crossed with K5 coverage coordinates; no joint null probability is reported.",
        ),
    )
    return tuple(
        spec
        for spec in specs
        if spec.file_name not in CF4_P0_QUARANTINED_FIGURE_NAMES
    )


def _manifest_for_spec(
    spec: FigureSpec,
    figure_path: Path,
    command: str,
    meta: PlotMeta,
) -> dict[str, Any]:
    rel_path = _repo_relative(figure_path)
    reconstruction_functional = (
        spec.file_name in CF4_RECONSTRUCTION_FUNCTIONAL_FIGURE_NAMES
    )
    reconstruction_caveats = (
        [
            "Numerical rows are functionals of one CF4++ Wiener-filter reconstruction, not observed bulk-flow amplitude measurements.",
            "C1-K5-MV-F1 remains OPEN; no global-tilt coordinate or cosmological inference is permitted.",
        ]
        if reconstruction_functional
        else []
    )
    manifest = {
        "artifact_id": spec.artifact_id,
        "artifact_path": rel_path,
        "owner": "OBSSTAT",
        "implementation_scope": "obsstat",
        "claim_tier": "diagnostic_only",
        "production_status": "diagnostic_only",
        "artifact_mode": "paper_appendix_conditioned",
        "allowed_use": "paper_appendix",
        "analysis_mode": (
            "reconstruction_conditioned_method_systematics"
            if reconstruction_functional
            else "observed_or_prepared_data_diagnostic"
        ),
        "caption_policy": [
            "must_state_observed_data_diagnostic",
            "must_not_state_family_identification",
            "must_not_state_native_low_ell_solver_output",
            "must_not_state_p_value_without_null_ensemble",
        ],
        "promotion_blockers": [
            "matched_nulls_not_bound_for_inference",
            "full_covariance_not_bound_for_likelihood",
            "native_morphology_atlas_absent",
            *(["C1-K5-MV-F1_OPEN"] if reconstruction_functional else []),
        ],
        "created_by": SCRIPT_PATH,
        "git_commit": "content-addressed",
        "config_hash": _config_hash(
            {
                "artifact_id": spec.artifact_id,
                "file_name": spec.file_name,
                "caption": spec.caption,
                "source_hashes": _input_hashes(spec.source_paths),
                "version": "report-data-analysis-figures-v2",
            }
        ),
        "input_hashes": _input_hashes(spec.source_paths),
        "code_version": "content-addressed",
        "schema_version": "obsstat.report_data_analysis_figure.v1",
        "caveats": [
            "Observed/prepared data analysis figure.",
            "Diagnostic-only: no posterior odds, p-value, geometry detection, or family identification.",
            "No native low-ell solver output is used.",
            *reconstruction_caveats,
        ],
        "required_gates": [
            "repo_local_data_input_present",
            "manifest_metadata_present",
            "report_lane_is_data_analysis_not_meta",
        ],
        "passed_gates": [
            "repo_local_data_input_present",
            "manifest_metadata_present",
            "report_lane_is_data_analysis_not_meta",
        ],
        "failed_gates": [
            "matched_nulls_not_bound_for_inference",
            "full_covariance_not_bound_for_likelihood",
        ],
        "statistics_definitions": {
            "source_artifacts": list(spec.source_paths),
            **(
                {
                    "finding_state": {
                        "finding_id": "C1-K5-MV-F1",
                        "scientific_status": "OPEN",
                        "canonical_source": "docs/generated/cf4_p0_quarantine_block.json",
                    },
                    "observational_amplitude_claim_allowed": False,
                    "global_tilt_claim_allowed": False,
                    "cosmological_inference_allowed": False,
                }
                if reconstruction_functional
                else {}
            ),
            **meta.statistics_definitions,
        },
        "transfer_source": meta.transfer_source,
        "sky_support_status": meta.sky_support_status,
        "null_mock_status": meta.null_mock_status,
        "generating_command": command,
        "git_commit_or_worktree_state": "content-addressed",
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


def _sidecar_path(figure_path: Path) -> Path:
    return figure_path.with_suffix("").with_name(figure_path.stem + ".manifest.json")


def build_pack(command: str, specs: tuple[FigureSpec, ...]) -> dict[str, Any]:
    figures = [
        {
            "artifact_id": spec.artifact_id,
            "file_name": spec.file_name,
            "artifact_path": _repo_relative(FIGURE_DIR / spec.file_name),
            "manifest_path": _repo_relative(_sidecar_path(FIGURE_DIR / spec.file_name)),
            "caption": spec.caption,
            "source_paths": list(spec.source_paths),
        }
        for spec in specs
    ]
    source_paths = tuple(sorted({path for spec in specs for path in spec.source_paths}))
    return {
        "artifact_id": "obsstat.report_data_analysis_figure_pack",
        "artifact_path": _repo_relative(PACK_JSON),
        "owner": "OBSSTAT",
        "implementation_scope": "obsstat",
        "claim_tier": "diagnostic_only",
        "transfer_source": "mixed_none_and_external_reference",
        "sky_support_status": "mixed_recorded_and_not_directional",
        "null_mock_status": "not_statistical",
        "config_hash": _config_hash(
            {
                "figures": figures,
                "source_hashes": _input_hashes(source_paths),
                "skipped_current_data_candidates": SKIPPED_CURRENT_DATA_CANDIDATES,
                "version": "report-data-analysis-figure-pack-v2",
            }
        ),
        "input_hashes": _input_hashes(source_paths),
        "caveats": [
            "Report-candidate observed-data analysis lane only.",
            "No internal process, governance, or self-audit figures are included.",
            "Diagnostic-only; no posterior odds, p-values, or family-identification claim.",
        ],
        "generating_command": command,
        "git_commit_or_worktree_state": "content-addressed",
        "figure_lane": "report_data_analysis_current",
        "figures": figures,
        "skipped_current_data_candidates": list(SKIPPED_CURRENT_DATA_CANDIDATES),
    }


def render_pack_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Report Data Analysis Figure Pack",
        "",
        "owner: OBSSTAT",
        "implementation_scope: obsstat",
        "claim_tier: diagnostic_only",
        f"transfer_source: {payload['transfer_source']}",
        f"config_hash: `{payload['config_hash']}`",
        "caveats:",
        "- Report-candidate observed-data analysis lane only.",
        "- No code-internal process or governance figures are included.",
        "- Diagnostic-only; no posterior odds, p-values, or family-identification result.",
        f"generating_command: {payload['generating_command']}",
        "git_commit_or_worktree_state: content-addressed",
        "",
        "## Figures",
        "",
        "| Figure | Data inputs | Caption |",
        "| --- | --- | --- |",
    ]
    for row in payload["figures"]:
        inputs = ", ".join(
            f"`{path}`" for path in row["source_paths"] if not path.startswith("scripts/")
        )
        lines.append(f"| `{row['artifact_path']}` | {inputs} | {row['caption']} |")
    lines.extend(
        [
            "",
            "## Not generated in this current-data pass",
            "",
            "| Candidate | Reason |",
            "| --- | --- |",
        ]
    )
    for row in payload["skipped_current_data_candidates"]:
        lines.append(f"| {row['candidate']} | {row['reason']} |")
    lines.append("")
    return "\n".join(lines)


def _expected_texts(pack: dict[str, Any]) -> dict[Path, str]:
    return {
        PACK_JSON: json.dumps(pack, indent=2, sort_keys=True) + "\n",
        PACK_MD: render_pack_markdown(pack),
    }


def write_outputs(argv: list[str] | None) -> None:
    command = _command([] if argv is None else [arg for arg in argv if arg != "--check"])
    specs = _figure_specs()
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    GEN.mkdir(parents=True, exist_ok=True)
    for spec in specs:
        figure_path = FIGURE_DIR / spec.file_name
        meta = spec.builder(figure_path)
        manifest = _manifest_for_spec(spec, figure_path, command, meta)
        _sidecar_path(figure_path).write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(f"wrote {_repo_relative(figure_path)}")
    pack = build_pack(command, specs)
    for path, text in _expected_texts(pack).items():
        path.write_text(text, encoding="utf-8")
        print(f"wrote {_repo_relative(path)}")


def check_outputs(argv: list[str] | None) -> int:
    command = _command([] if argv is None else [arg for arg in argv if arg != "--check"])
    specs = _figure_specs()
    pack = build_pack(command, specs)
    stale: list[str] = []
    for path, expected in _expected_texts(pack).items():
        if not path.exists() or path.read_text(encoding="utf-8") != expected:
            stale.append(_repo_relative(path))
    for spec in specs:
        figure_path = FIGURE_DIR / spec.file_name
        sidecar = _sidecar_path(figure_path)
        if not figure_path.exists() or figure_path.stat().st_size == 0:
            stale.append(_repo_relative(figure_path))
        if not sidecar.exists():
            stale.append(_repo_relative(sidecar))
    for file_name in sorted(CF4_P0_QUARANTINED_FIGURE_NAMES):
        figure_path = FIGURE_DIR / file_name
        sidecar = _sidecar_path(figure_path)
        if figure_path.exists():
            stale.append(f"{_repo_relative(figure_path)} (must be quarantined)")
        if sidecar.exists():
            stale.append(f"{_repo_relative(sidecar)} (must be quarantined)")
    if stale:
        print("report data-analysis figures are stale:", file=sys.stderr)
        for path in stale:
            print(f"- {path}", file=sys.stderr)
        return 1
    print("report data-analysis figures are current")
    return 0


def run(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if args.check:
        return check_outputs(argv)
    write_outputs(argv)
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
