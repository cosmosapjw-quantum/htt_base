#!/usr/bin/env python3
"""K1: null-calibrated low-ell morphology of the real Planck low-ell map.

REV-R102. Feeds the real Planck PR3 SMICA (and Commander cross-check)
NSIDE=16 temperature map into the existing, tested OBSSTAT low-ell estimators
(`summarize_lowell_scalars`, `summarize_morphology_axes`) and calibrates the
classic low-ell anomaly statistics against an isotropic LambdaCDM null ensemble:

  - S_{1/2} (large-angle correlation suppression),
  - parity even/odd power ratio and asymmetry,
  - planarity (m^2 power fraction),
  - quadrupole-octupole (ell=2 vs ell=3) preferred-axis alignment,
  - low-ell preferred-axis alignment to the CMB kinematic dipole apex.

All outputs are OBSSTAT diagnostic features (model-independent). No Bianchi
family identification, geometry detection, native solver output, or HTT/MIO
evidence is produced. The low-ell power is also expressed as a fraction of the
MES anisotropy budget ceiling for framing only.

Usage:
    venv/bin/python scripts/make_lowell_morphology_real_map.py [--null-count N]
    venv/bin/python scripts/make_lowell_morphology_real_map.py --check
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import healpy as hp  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
HTT_ROOT = REPO_ROOT / "htt"
COMMON_ROOT = HTT_ROOT / "src"
for root in (HTT_ROOT, COMMON_ROOT):
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

from common.sky_geometry import lb_to_unitvec, unitvec_to_lb  # noqa: E402
from obsstat.lowell_map_features import (  # noqa: E402
    densify_alm,
    empirical_pvalue,
    power_inertia_tensor,
)
from obsstat.morphology import (  # noqa: E402
    MorphologyNullCalibration,
    summarize_morphology_axes,
)
from obsstat.scalar_lowell import (  # noqa: E402
    LowEllNullCalibration,
    summarize_lowell_scalars,
)

NSIDE = 16
LMAX = 8
ELL_MIN = 2
DEFAULT_NULL_COUNT = 10000
SEED = 12345

SMICA_MAP = REPO_ROOT / "workdir/obs_bundle/cmb/maps/smica_nside16.npz"
COMMANDER_MAP = REPO_ROOT / "workdir/obs_bundle/cmb/maps/commander_nside16.npz"
TEMP_MASK = REPO_ROOT / "workdir/obs_bundle/cmb/masks/temp_nside16.npz"
CAMB_REF = REPO_ROOT / "data/camb_ref_planck2018.npz"
OBS_DEFAULTS = REPO_ROOT / "htt/workspace/data/obs_defaults.json"

OUT_JSON = REPO_ROOT / "docs/generated/lowell_morphology_real_map_report.json"
OUT_MD = REPO_ROOT / "docs/generated/lowell_morphology_real_map_report.md"
FIG_DIR = REPO_ROOT / "figures/observed_current"
FIG_MAP = FIG_DIR / "fig_observed_lowell_morphology_axis.png"
FIG_SIG = FIG_DIR / "fig_observed_lowell_null_significance.png"

# Statistic tail conventions: the named low-ell "anomaly" direction.
# Pre-specified anomaly directions (the registered low-ell anomaly tails).
TAILS = {
    "s_one_half": "lower",  # anomalously low large-angle correlation
    "parity_even_over_odd_ratio": "lower",  # odd-power excess -> ratio < 1
    "parity_asymmetry": "lower",  # odd-power excess -> asymmetry < 0
    "planarity_mean": "upper",  # anomalously planar (m ~ +/- ell)
    "qo_axis_alignment_deg": "lower",  # anomalously aligned ell=2 vs ell=3
    "axis_to_cmb_dipole_deg": "lower",  # anomalously aligned to CMB apex
}
TAIL_TEXT = {
    "s_one_half": "P(null S_1/2 <= observed)",
    "parity_even_over_odd_ratio": "P(null even/odd ratio <= observed)",
    "parity_asymmetry": "P(null asymmetry <= observed)",
    "planarity_mean": "P(null planarity >= observed)",
    "qo_axis_alignment_deg": "P(null ell2-ell3 angle <= observed)",
    "axis_to_cmb_dipole_deg": "P(null axis-to-apex angle <= observed)",
}


def _sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _git_state() -> tuple[str, str]:
    try:
        short = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT, text=True
        ).strip()
        dirty = subprocess.run(
            ["git", "status", "--short"], cwd=REPO_ROOT, text=True, capture_output=True
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return "unknown", "unknown"
    return short, (f"{short}+dirty" if dirty else short)


def _load_real_map(path: Path) -> np.ndarray:
    data = np.load(path)
    temp = np.asarray(data["I"], dtype=float)
    unit = str(data["unit"])
    # Commander NSIDE=16 is stored in K despite a "uK (assumed)" label; rescale.
    if "uK" not in unit or float(np.std(temp)) < 1.0e-2:
        temp = temp * 1.0e6
    return temp


def _fiducial_cl(lmax: int) -> np.ndarray:
    ref = np.load(CAMB_REF)
    ell = np.asarray(ref["ell"], dtype=int)
    c_tt = np.asarray(ref["C_TT"], dtype=float)
    table = dict(zip(ell.tolist(), c_tt.tolist()))
    cl = np.zeros(lmax + 1, dtype=float)
    for ell_value in range(2, lmax + 1):
        cl[ell_value] = float(table.get(ell_value, 0.0))
    return cl


def _principal_axis(tensor: np.ndarray) -> np.ndarray:
    evals, evecs = np.linalg.eigh(tensor)
    axis = evecs[:, int(np.argmax(evals))]
    # antipodal: fix sign so the z-component (or first non-zero) is non-negative.
    for component in axis:
        if abs(component) > 1.0e-12:
            if component < 0:
                axis = -axis
            break
    return axis / np.linalg.norm(axis)


def _filtered_map(alm_packed: np.ndarray, keep_ells: set[int]) -> np.ndarray:
    filtered = np.zeros_like(alm_packed)
    for ell in keep_ells:
        for m in range(0, ell + 1):
            idx = hp.Alm.getidx(LMAX, ell, m)
            filtered[idx] = alm_packed[idx]
    return hp.alm2map(filtered, nside=NSIDE, lmax=LMAX)


def _angle_deg(u: np.ndarray, v: np.ndarray) -> float:
    # antipodal-invariant angle in [0, 90]
    c = abs(float(np.dot(u, v))) / (np.linalg.norm(u) * np.linalg.norm(v))
    return float(np.degrees(np.arccos(np.clip(c, 0.0, 1.0))))


def compute_map_statistics(
    temp_map: np.ndarray, pix_vectors: np.ndarray, cmb_apex: np.ndarray
) -> dict[str, object]:
    """Return the low-ell anomaly statistics + the low-ell preferred axis."""

    alm_packed = hp.map2alm(temp_map, lmax=LMAX, iter=3)
    dense = densify_alm(alm_packed, LMAX)
    summary = summarize_lowell_scalars(
        alm_by_lm=dense, ell_min=ELL_MIN, ell_max=LMAX, channel="TT"
    )
    map2 = _filtered_map(alm_packed, {2})
    map3 = _filtered_map(alm_packed, {3})
    map23 = _filtered_map(alm_packed, {2, 3})
    axis2 = _principal_axis(power_inertia_tensor(map2, pix_vectors))
    axis3 = _principal_axis(power_inertia_tensor(map3, pix_vectors))
    tensor23 = power_inertia_tensor(map23, pix_vectors)
    axis23 = _principal_axis(tensor23)
    parity = summary.parity
    return {
        "s_one_half": float(summary.s_one_half),
        "parity_even_over_odd_ratio": float(parity["even_over_odd_ratio"]),
        "parity_asymmetry": float(parity["asymmetry"]),
        "planarity_mean": float(summary.planarity["mean"]),
        "qo_axis_alignment_deg": _angle_deg(axis2, axis3),
        "axis_to_cmb_dipole_deg": _angle_deg(axis23, cmb_apex),
        "_axis23": axis23,
        "_tensor23": tensor23,
        "_map23": map23,
        "_dense": dense,
    }


def _build_null_distribution(
    cl: np.ndarray, pix_vectors: np.ndarray, cmb_apex: np.ndarray, n_null: int
) -> dict[str, np.ndarray]:
    np.random.seed(SEED)
    keys = list(TAILS)
    collected: dict[str, list[float]] = {key: [] for key in keys}
    for _ in range(n_null):
        null_map = hp.synfast(cl, nside=NSIDE, lmax=LMAX, pixwin=False)
        stats = compute_map_statistics(null_map, pix_vectors, cmb_apex)
        for key in keys:
            collected[key].append(float(stats[key]))
    return {key: np.asarray(values, dtype=float) for key, values in collected.items()}


def build_report(*, n_null: int, generating_command: str, worktree_state: str) -> dict:
    pix_vectors = np.asarray(hp.pix2vec(NSIDE, np.arange(hp.nside2npix(NSIDE)))).T
    obs_defaults = json.loads(OBS_DEFAULTS.read_text())
    cmb = obs_defaults["dipole_observations"]["cmb_planck_2018"]
    cmb_apex = lb_to_unitvec(np.array(cmb["l_deg"]), np.array(cmb["b_deg"]))
    cmb_apex = np.asarray(cmb_apex, dtype=float).reshape(3)

    cl = _fiducial_cl(LMAX)
    real_map = _load_real_map(SMICA_MAP)
    real = compute_map_statistics(real_map, pix_vectors, cmb_apex)
    nulls = _build_null_distribution(cl, pix_vectors, cmb_apex, n_null)

    p_values = {
        key: empirical_pvalue(float(real[key]), nulls[key], tail=TAILS[key])
        for key in TAILS
    }
    # MES anisotropy-budget framing only (dimensionless ratio of low-ell power
    # to the S2a MES shear ceiling); not an evidence statement.
    low_ell_power = float(sum(real["_dense"][(ell, m)].real ** 2 + real["_dense"][(ell, m)].imag ** 2
                             for ell in range(ELL_MIN, LMAX + 1) for m in range(-ell, ell + 1)))
    mes_ceiling_x_max = 9.25e-6  # S2a x_max (dimensionless), manuscript Table
    axis_l, axis_b = unitvec_to_lb(real["_axis23"])

    scan_volume = {
        "statistics_tested": list(TAILS),
        "n_statistics": len(TAILS),
        "ell_range": [ELL_MIN, LMAX],
        "nside": NSIDE,
    }
    lowell_null = LowEllNullCalibration(
        null_ensemble_ref="isotropic_lcdm_synfast_camb_ref_planck2018",
        look_elsewhere_status="look_elsewhere_tracked",
        p_values={
            "s_one_half": p_values["s_one_half"],
            "parity_even_over_odd_ratio": p_values["parity_even_over_odd_ratio"],
            "parity_asymmetry": p_values["parity_asymmetry"],
            "planarity_mean": p_values["planarity_mean"],
        },
        mock_count=n_null,
        tail_definitions={
            "s_one_half": TAIL_TEXT["s_one_half"],
            "parity_even_over_odd_ratio": TAIL_TEXT["parity_even_over_odd_ratio"],
            "parity_asymmetry": TAIL_TEXT["parity_asymmetry"],
            "planarity_mean": TAIL_TEXT["planarity_mean"],
        },
        covariance_status="diagonal_fiducial_cl_only",
        mask_status="full_sky_cleaned_map_fsky_0p79_no_deconvolution",
        scan_volume=scan_volume,
    )
    morph_scan_volume = {
        "targets": ["cmb_dipole_apex", "ell2_vs_ell3_axis"],
        "statistic_keys": ["principal_axis_alignment", "alignment_to_reference"],
        "look_elsewhere_trials": len(TAILS),
        "global_local_status": "local_unadjusted_with_trials",
        "n_statistics": len(TAILS),
    }
    morph_null = MorphologyNullCalibration(
        null_ensemble_ref="isotropic_lcdm_synfast_camb_ref_planck2018",
        look_elsewhere_status="look_elsewhere_tracked",
        p_values={
            "principal_axis_alignment": p_values["qo_axis_alignment_deg"],
            "alignment_to_reference": p_values["axis_to_cmb_dipole_deg"],
        },
        mock_count=n_null,
        covariance_status="diagonal_fiducial_cl_only",
        mask_status="full_sky_cleaned_map_fsky_0p79_no_deconvolution",
        scan_volume=morph_scan_volume,
        look_elsewhere_trials=len(TAILS),
        tail_definitions={
            "principal_axis_alignment": TAIL_TEXT["qo_axis_alignment_deg"],
            "alignment_to_reference": TAIL_TEXT["axis_to_cmb_dipole_deg"],
        },
    )

    config = {"nside": NSIDE, "lmax": LMAX, "ell_min": ELL_MIN, "n_null": n_null, "seed": SEED}
    config_hash = "sha256:" + hashlib.sha256(
        json.dumps(config, sort_keys=True).encode()
    ).hexdigest()
    lowell_summary = summarize_lowell_scalars(
        alm_by_lm=real["_dense"],
        ell_min=ELL_MIN,
        ell_max=LMAX,
        channel="TT",
        null_calibration=lowell_null,
        mask_status="full_sky_cleaned_map_fsky_0p79_no_deconvolution",
    )
    morph_summary = summarize_morphology_axes(
        morphology_tensor=real["_tensor23"].tolist(),
        tensor_label="lowell_ell2_ell3_power_inertia",
        reference_axes={"cmb_dipole_apex": cmb_apex.tolist()},
        null_calibration=morph_null,
        config_hash=config_hash,
        input_hashes=[_sha256_file(SMICA_MAP), _sha256_file(CAMB_REF)],
    )

    return {
        "owner": "OBSSTAT",
        "implementation_scope": "obsstat",
        "claim_tier": "diagnostic_only",
        "schema_version": "obsstat.lowell_morphology_real_map.v1",
        "transfer_source": "none",
        "sky_support_status": "full_sky_cleaned_map",
        "null_mock_status": "null_calibrated_isotropic_lcdm_ensemble",
        "config_hash": config_hash,
        "config": config,
        "input_hashes": [_sha256_file(SMICA_MAP), _sha256_file(CAMB_REF), _sha256_file(TEMP_MASK)],
        "generating_command": generating_command,
        "git_commit_or_worktree_state": worktree_state,
        "map": "planck_pr3_smica_nside16",
        "observed": {key: float(real[key]) for key in TAILS},
        "p_values": {key: float(value) for key, value in p_values.items()},
        "p_value_tails": {key: TAIL_TEXT[key] for key in TAILS},
        "low_ell_preferred_axis_galactic_lb_deg": [float(axis_l), float(axis_b)],
        "mes_budget_framing": {
            "low_ell_alm_power_uK2": low_ell_power,
            "mes_s2a_x_max_dimensionless": mes_ceiling_x_max,
            "note": "framing only; low-ell power and MES shear ceiling are different "
            "quantities and this ratio is not an evidence statement",
        },
        "lowell_feature_payload": lowell_summary.to_feature_payload(),
        "morphology_feature_payload": morph_summary.to_feature_payload(),
        "caveats": [
            "model-independent low-ell feature p-values; not evidence for any "
            "Bianchi model and not a source-identification claim",
            "ell2-ell3 axis alignment is a power-inertia-axis diagnostic, not the "
            "multipole-vector axis-of-evil statistic",
            "no native low-ell solver output or morphology atlas is used",
            "no Bianchi family identification or geometry detection is claimed",
            "full-sky cleaned map; no mask deconvolution or full pixel-pixel covariance",
            "look-elsewhere across the tested statistics is tracked, not globally corrected",
            f"null ensemble is isotropic LambdaCDM synfast (n={n_null}, seed={SEED}); "
            "cross-healpy-version reproducibility may vary at the synfast RNG level",
        ],
        "_real": real,
        "_nulls": nulls,
    }


def render_markdown(report: dict) -> str:
    lines = [
        "# Low-ell Morphology of the Real Planck Map (REV-R102)",
        "",
        f"owner: {report['owner']}",
        f"implementation_scope: {report['implementation_scope']}",
        f"claim_tier: {report['claim_tier']}",
        "transfer_source: none",
        "sky_support_status: full_sky_cleaned_map",
        f"null_mock_status: {report['null_mock_status']}",
        f"config_hash: `{report['config_hash']}`",
        "input_hashes:",
        *[f"- {item}" for item in report["input_hashes"]],
        f"generating_command: `{report['generating_command']}`",
        f"git_commit_or_worktree_state: `{report['git_commit_or_worktree_state']}`",
        "",
        "## Null-calibrated low-ell statistics (Planck PR3 SMICA NSIDE=16)",
        "",
        "| Statistic | Observed | p-value | Tail |",
        "| --- | --- | --- | --- |",
        *[
            f"| {key} | {report['observed'][key]:.5g} | {report['p_values'][key]:.4f} | {report['p_value_tails'][key]} |"
            for key in report["observed"]
        ],
        "",
        f"Low-ell (ell=2,3) preferred axis (Galactic l,b): "
        f"{report['low_ell_preferred_axis_galactic_lb_deg'][0]:.1f}, "
        f"{report['low_ell_preferred_axis_galactic_lb_deg'][1]:.1f} deg.",
        "",
        "## Caveats",
        "",
        *[f"- {item}" for item in report["caveats"]],
        "",
    ]
    return "\n".join(lines)


def _figure_manifest(fig_path: Path, report: dict, *, title: str, extra_caveats: list[str]) -> dict:
    short, worktree = _git_state()
    return {
        "artifact_id": f"obsstat.observed.{fig_path.stem}",
        "artifact_path": fig_path.relative_to(REPO_ROOT).as_posix(),
        "owner": "OBSSTAT",
        "implementation_scope": "obsstat",
        "claim_tier": "diagnostic_only",
        "production_status": "diagnostic_only",
        "artifact_mode": "paper_appendix_conditioned",
        "allowed_use": "paper_appendix",
        "transfer_source": "none",
        "sky_support_status": "full_sky_cleaned_map",
        "null_mock_status": "null_calibrated_isotropic_lcdm_ensemble",
        "config_hash": report["config_hash"],
        "input_hashes": report["input_hashes"],
        "created_by": "scripts/make_lowell_morphology_real_map.py",
        "git_commit": short,
        "git_commit_or_worktree_state": worktree,
        "code_version": worktree,
        "schema_version": "obsstat.lowell_morphology_figure.v1",
        "caption_policy": [
            "must_state_diagnostic_only",
            "must_not_use_for_family_identification_or_family_selection",
            "must_state_no_native_low_ell_solver_output",
        ],
        "caveats": [
            "Model-independent low-ell feature; not Bianchi evidence.",
            "No native low-ell solver output or morphology atlas is used.",
            "No Bianchi family-ID or geometry-detection claim is made.",
            *extra_caveats,
        ],
        "failed_gates": [
            "native_low_ell_solver_not_available",
            "family_morphology_atlas_not_available",
            "full_pixel_covariance_not_bound",
        ],
        "passed_gates": [
            "repo_local_observed_data_present",
            "null_calibration_present",
            "manifest_metadata_present",
            "claim_firewall_caption_review",
        ],
        "promotion_blockers": [
            "native_solver_validation_absent",
            "native_morphology_atlas_absent",
            "family_identification_blocked_pre_native_atlas",
        ],
        "publication_gates": {
            "bianchi_evidence_claim": "fail_diagnostic_only",
            "family_identification_claim": "fail_blocked_pre_native_atlas",
        },
        "required_gates": [
            "repo_local_observed_data_present",
            "manifest_metadata_present",
            "claim_firewall_caption_review",
        ],
        "title": title,
    }


def _write_figures(report: dict) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    # Figure 1: low-ell (ell=2,3) reconstructed map + preferred axis.
    fig = plt.figure(figsize=(7, 4.2))
    hp.mollview(
        report["_real"]["_map23"],
        title="Planck PR3 SMICA low-ell (ell=2,3) reconstruction",
        unit="uK",
        cmap="coolwarm",
        fig=fig.number,
        cbar=True,
    )
    axis_l, axis_b = report["low_ell_preferred_axis_galactic_lb_deg"]
    hp.projscatter(np.radians(90 - axis_b), np.radians(axis_l), marker="x", color="k", s=80)
    hp.projscatter(np.radians(90 - axis_b), np.radians(axis_l + 180), marker="x", color="k", s=80)
    fig.savefig(FIG_MAP, dpi=140)
    plt.close(fig)

    # Figure 2: observed statistics vs null distributions with p-values.
    keys = list(report["observed"])
    fig, axes = plt.subplots(2, 3, figsize=(12, 6.5))
    for ax, key in zip(axes.ravel(), keys):
        nulls = report["_nulls"][key]
        ax.hist(nulls, bins=40, color="#cbd5e1", edgecolor="none")
        ax.axvline(report["observed"][key], color="#dc2626", lw=2)
        ax.set_title(f"{key}\np={report['p_values'][key]:.4f}", fontsize=9)
        ax.tick_params(labelsize=7)
    fig.suptitle(
        "Planck low-ell statistics vs isotropic LambdaCDM null (diagnostic only)",
        fontsize=11,
    )
    fig.tight_layout()
    fig.savefig(FIG_SIG, dpi=140)
    plt.close(fig)

    for fig_path, title, extra in (
        (FIG_MAP, "Low-ell preferred axis", ["Axis is antipodal; descriptor only, no family label."]),
        (FIG_SIG, "Null-calibrated low-ell significance", ["Look-elsewhere across statistics tracked, not globally corrected."]),
    ):
        manifest = _figure_manifest(fig_path, report, title=title, extra_caveats=extra)
        manifest_path = fig_path.with_suffix("").with_name(fig_path.stem + ".manifest.json")
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _public_report(report: dict) -> dict:
    return {key: value for key, value in report.items() if not key.startswith("_")}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--null-count", type=int, default=DEFAULT_NULL_COUNT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--no-figures", action="store_true")
    args = parser.parse_args(argv)

    short, worktree = _git_state()
    command = "python scripts/make_lowell_morphology_real_map.py"
    report = build_report(
        n_null=args.null_count, generating_command=command, worktree_state=worktree
    )
    public = _public_report(report)
    rendered_json = json.dumps(public, indent=2, sort_keys=True) + "\n"
    rendered_md = render_markdown(report)

    if args.check:
        stale = []
        for path, content in ((OUT_JSON, rendered_json), (OUT_MD, rendered_md)):
            actual = path.read_text(encoding="utf-8") if path.exists() else None
            if actual != content:
                stale.append(path.relative_to(REPO_ROOT).as_posix())
        if stale:
            print("stale low-ell morphology artifacts:", *stale, sep="\n  - ")
            return 1
        print("low-ell morphology artifacts up to date")
        return 0

    OUT_JSON.write_text(rendered_json, encoding="utf-8")
    OUT_MD.write_text(rendered_md, encoding="utf-8")
    print(f"wrote {OUT_JSON.relative_to(REPO_ROOT)}")
    print(f"wrote {OUT_MD.relative_to(REPO_ROOT)}")
    if not args.no_figures:
        _write_figures(report)
        print(f"wrote {FIG_MAP.relative_to(REPO_ROOT)}")
        print(f"wrote {FIG_SIG.relative_to(REPO_ROOT)}")
    for key in report["observed"]:
        print(f"  {key}: obs={report['observed'][key]:.5g} p={report['p_values'][key]:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
