#!/usr/bin/env python3
"""Real CF4 source-conditioned PR255-style Schur identification (no physical posterior)."""
from __future__ import annotations
import argparse
import hashlib
import json
import time
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from obsstat.cf4_apparent_kinematic_distribution import model_matrix
from obsstat.cf4_schur_information import SchurInformationError, profile_stf_information

EXPECTED_NPZ_SHA256 = "86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c"
EXPECTED_ID_SHA256 = "f54706b8ff5c50c25a5a74c4b153f7f9e719a28582db044e00e5930dd30e3c88"
PARENT_HEAD = "13d8d85fa470d645d008986e8f77d8d0f70fdf54"
REFERENCE_H0 = 74.6
REFERENCE_OM = .3153


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(4 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _row(name, mask, z, n, method, mu, error_reported):
    design = model_matrix(z[mask], n[mask], method[mask], include_method_slope=True,
                          omega_m=REFERENCE_OM, H0=REFERENCE_H0)
    err = np.sqrt(
        error_reported[mask] ** 2 + .15 ** 2
        + (250.0 * design["redshift_velocity_width_basis_mag_per_kms"]) ** 2
    )
    y = mu[mask] - design["reference_mu_mag"]
    p = profile_stf_information(design["design"], y, err, design["slices"]["shear"])
    return {
        "case": name,
        "n": int(np.sum(mask)),
        "method_counts": {str(m): int(np.sum(method[mask] == m)) for m in sorted(set(method[mask]))},
        "nuisance_rank": p["nuisance_rank"],
        "stf_rank": p["signal_rank"],
        "apparent_stf_coefficients": p["beta_signal"].tolist(),
        "apparent_stf_frobenius_norm": float(np.linalg.norm(p["beta_signal"])),
        "apparent_stf_norm_divided_by_3_NOT_PHYSICAL_SHEAR": float(np.linalg.norm(p["beta_signal"]) / 3),
        "conditional_5x5_covariance": p["signal_cov"].tolist(),
        "schur_fisher": p["fisher_profiled"].tolist(),
        "unprofiled_fisher": p["fisher_before_nuisance"].tolist(),
        "relative_information_eigenvalues_sorted": p["relative_information_eigenvalues"].tolist(),
        "relative_information_trace": p["relative_information_trace"],
        "uncertainty_hypervolume_inflation": p["uncertainty_hypervolume_inflation_vs_fixed_nuisance"],
        "projected_response_condition": p["projected_signal_condition"],
        "normalized_nuisance_condition": p["nuisance_condition_normalized"],
        "chi2_over_dof": p["chi2_profiled"] / p["dof"],
        "normal_equation_residual": p["normal_equation_residual"],
        "claim": "conditional linear apparent Hubble STF2, not cosmic shear or cosmological null probability",
    }


def run(input_npz: Path, parent_result: Path, out: Path):
    t0 = time.perf_counter()
    if out.exists():
        raise FileExistsError(f"create-only output: {out}")
    sha = digest(input_npz)
    if sha != EXPECTED_NPZ_SHA256:
        raise RuntimeError(f"source bytes changed, expected {EXPECTED_NPZ_SHA256}, found {sha}")
    with np.load(input_npz, allow_pickle=False) as source:
        z = source["z_CMB"]
        n = source["n_J2000"]
        mu = source["dmzp"]
        err = source["e_dmzp"]
        methods = source["method_family"]
        ids = source["group_id"]
    if (
        len(z) != 35970 or n.shape != (35970, 3)
        or hashlib.sha256(np.asarray(ids, dtype="<i8").tobytes()).hexdigest() != EXPECTED_ID_SHA256
    ):
        raise RuntimeError("CF4 selected source cohort ID or shape mismatch")
    if not np.array_equal(np.unique(methods), np.array(["FP", "OTHER", "SN", "TF"])):
        raise RuntimeError(f"unexpected pooled method labels: {np.unique(methods)}")
    allmask = np.ones(len(z), dtype=bool)
    runs = [("all", allmask)]
    for m in sorted(set(methods)):
        runs.append((f"exclude_{m}", methods != m))
    import healpy as hp
    patches = hp.vec2pix(1, n[:, 0], n[:, 1], n[:, 2])
    runs.extend((f"delete_patch_{j:02d}", patches != j) for j in range(12))
    results = {}
    for label, mask in runs:
        try:
            result = _row(label, mask, z, n, methods, mu, err)
            results[label] = result
            print(label, "n", result["n"], "min_lambda",
                  round(min(result["relative_information_eigenvalues_sorted"]), 8),
                  "STF_norm", round(result["apparent_stf_frobenius_norm"], 8),
                  flush=True)
        except SchurInformationError as exc:
            results[label] = {"status": "RANK_OR_DOMAIN_BLOCKED", "message": str(exc),
                              "n": int(mask.sum())}
            print(label, "RANK_OR_DOMAIN_BLOCKED", exc, flush=True)
    assert "stf_rank" in results["all"], "full source must be identifiable"
    with parent_result.open() as f:
        parent = json.load(f)
    old = parent["cases"]["fiducial_slope_f015_v250_z01_10"]
    full = results["all"]
    diff = np.asarray(full["apparent_stf_coefficients"]) - np.asarray(
        old["five_STF_apparent_shear_directional_H_fraction_coordinates"]
    )
    covdiff = np.asarray(full["conditional_5x5_covariance"]) - np.asarray(old["five_STF_conditional_covariance"])
    if np.max(abs(diff)) > 2e-10 or np.max(abs(covdiff)) > 2e-10:
        raise RuntimeError("new Schur implementation failed frozen full-QR numerical regression")
    survival = [
        bool("stf_rank" in results[f"delete_patch_{j:02d}"])
        for j in range(12)
    ]
    case = {
        "schema": "htt.CF4_actual_group_PR255_schur_identification/1",
        "tier": "OBSERVED_GROUP_CONDITIONAL_WORKING_LAW_NO_PHYSICAL_BIANCHI_INFERENCE",
        "input_npz_sha256": sha,
        "input_group_id_sha256": EXPECTED_ID_SHA256,
        "parent_result_sha256": digest(parent_result),
        "parent_head_at_source": PARENT_HEAD,
        "source_methods": sorted(set(methods)),
        "source_n": len(z),
        "reference": {
            "H0_km_s_Mpc": REFERENCE_H0, "Omega_m": REFERENCE_OM,
            "error_law": "sqrt(reported_eDMzp^2 + 0.15mag^2 + (250 km/s * dmu/dv(z))^2)",
            "nuisance": "method offsets/slopes + three bulk velocity + three angular dipoles",
            "STF_response": "five Frobenius-orthonormal apparent angular Hubble directions",
            "sky_regions": "HEALPix NSIDE=1, NEST=False in published J2000",
        },
        "source_comparisons": results,
        "regression_max_abs_coefficient_error": float(np.max(abs(diff))),
        "regression_max_abs_covariance_error": float(np.max(abs(covdiff))),
        "jackknife_ranks_survive_count": sum(survival),
        "jackknife_attempts": len(survival),
        "input_claim_ceiling": "the released group tables lack physical correlated likelihood and selection",
        "cross_source_comparison": "overlapping subsets of same CF4 catalogue, NOT independent draws or calibrated p values",
        "elapsed_seconds": time.perf_counter()-t0,
    }
    out.mkdir(parents=True)
    (out / "result.json").write_text(json.dumps(case, indent=2, ensure_ascii=False) + "\n")

    labels = list(results)
    valid = [k for k in labels if "stf_rank" in results[k]]
    fig, (a, b) = plt.subplots(1, 2, figsize=(13, 5), layout="constrained")
    for j, k in enumerate(valid):
        values = results[k]["relative_information_eigenvalues_sorted"]
        a.plot(np.arange(1, 6), values, marker=".", alpha=.5,
               linewidth=1 if k != "all" else 2.4, label=k if k == "all" else None)
    a.set(xlabel="Generalized STF information mode (ascending)", ylabel="Surviving information / fixed-nuisance",
          title="Schur information spectra across CF4 source windows", ylim=(0, 1.02))
    a.grid(alpha=.2)
    a.legend()
    coords = np.arange(len(valid))
    b.scatter([results[k]["apparent_stf_frobenius_norm"] for k in valid], coords)
    b.set_yticks(coords, valid, fontsize=7)
    b.set(xlabel="||gamma_app||, NOT geometry shear", title="Overlapping cohort / sky deletion sensitivity")
    b.grid(alpha=.2)
    fig.savefig(out / "cf4_schur_information_sensitivity.png", dpi=155)
    plt.close(fig)
    (out / "REPORT_KO.md").write_text(
        "# CF4 35,970-group 실제 관측원 조건부 Schur 식별성\n\n"
        f"입력 NPZ SHA256: {sha}; parent HEAD: {PARENT_HEAD}.\n\n"
        "모형: DMzp–flat LCDM (Vcmb/c) residual = apparent 5D STF2 + method intercept/slope"
        " + independent bulk/dipole nuisance. 고정 대각 Gaussian 오차 가정.\n\n"
        f"- Full-data nuisance 제거 전 대비 Schur 정보 fraction (ascending): "
        f"{full['relative_information_eigenvalues_sorted']}.\n"
        f"- 정보 trace retained: {full['relative_information_trace']:.6g}; "
        f"조건부 confidence ellipsoid 선형 크기와 별개인 hypervolume inflation "
        f"{full['uncertainty_hypervolume_inflation']:.6g}.\n"
        f"- Full-data apparent 5D norm {full['apparent_stf_frobenius_norm']:.9g}; "
        f"조건부 proxy /3 {full['apparent_stf_norm_divided_by_3_NOT_PHYSICAL_SHEAR']:.9g}.\n"
        f"- 12 delete-one-sky-patch rank passes: {sum(survival)}/12. "
        f"Frozen full-QR coefficient regression maxabs {np.max(abs(diff)):.3g}.\n\n"
        "방법 family 제외와 sky-region 삭제는 기존 동일 표본과 겹치는 민감도 검사다. "
        "이들 차이는 독립 표본 가설검정 통계량이 아니다. "
        "method intercept/slope에 정확히 놓이는 가우시안 calibration covariance는 "
        "해당 nuisance를 무제한 profile하면 Schur 정보에 영향을 주지 않는다는 "
        "선형대수 정리를 별도 synthetic SPD 확인했다. "
        "반면 angular/depth-correlated cosmic velocity covariance, 선택함수, "
        "물리적인 photon/geodesic 응답은 이 정리로 제거되지 않는다.\n\n"
        "**결론:** 이 결과는 조건부 관측 operator의 식별성이지 "
        "우주론적 비등방성/물리적 shear의 측정값이나 p-value가 아니다.\n",
        encoding="utf-8",
    )
    print("DONE", len(valid), "/", len(runs), "seconds", round(time.perf_counter()-t0, 3),
          "full lambda", full["relative_information_eigenvalues_sorted"])
    return case


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-npz", type=Path, required=True)
    parser.add_argument("--parent-result", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    a = parser.parse_args()
    run(a.input_npz, a.parent_result, a.output_dir)
