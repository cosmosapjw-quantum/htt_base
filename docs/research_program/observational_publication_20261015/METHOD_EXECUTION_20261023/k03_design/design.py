"""Retained-summary K03 Gaussian design sensitivity; no catalogue replay."""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import scipy
from scipy.stats import norm


HERE = Path(__file__).resolve().parent
EXECUTION = HERE.parent
REBOOT = EXECUTION.parent / "METHOD_REBOOT_20261023"
SOURCE_FILES = {
    "task_input": EXECUTION / "R24-K03-DESIGN_INPUT.json",
    "contract": EXECUTION / "ADVISED_CONTRACTS.json",
    "retained_input": REBOOT / "K03_INPUT.json",
    "retained_result": REBOOT / "RESULT.json",
}
EXPECTED_SHA256 = {
    "task_input": "46dfba636f42d18eef70804060d210b775319402139d602a29889943c4f53108",
    "contract": "9bd712d298f572e797731b359e8810ab89f902d9c5bd2879810b49895951b4bf",
    "retained_input": "f7c584074d95d94d4aca6981c55a3380915a130ef57c985c55054e445903f438",
    "retained_result": "4ddc83edff2883c305027e5d91d35c815dc11632727fd329e7646366d68b69b3",
}
EPSILONS = (0.01, 0.1, 0.3)
TAUS = (0.0, 0.1, 0.3, 1.0)
TARGETS = (0.5, 0.8, 0.9)
ALPHA = 0.05


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_sources() -> tuple[dict, dict]:
    for name, path in SOURCE_FILES.items():
        actual = sha256(path)
        if actual != EXPECTED_SHA256[name]:
            raise ValueError(f"{name} source identity mismatch: {actual}")
    task = json.loads(SOURCE_FILES["task_input"].read_text())
    if task["task_id"] != "R24-K03-DESIGN":
        raise ValueError("wrong task identity")
    return json.loads(SOURCE_FILES["retained_input"].read_text()), json.loads(
        SOURCE_FILES["retained_result"].read_text()
    )


def symmetric_inverse(matrix: np.ndarray) -> np.ndarray:
    result = np.linalg.solve(matrix, np.eye(matrix.shape[0]))
    return (result + result.T) / 2


def scaled_residual(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.linalg.norm(a - b, ord=np.inf) / max(1.0, np.linalg.norm(a, ord=np.inf), np.linalg.norm(b, ord=np.inf)))


def calculation(inp: dict, baseline: dict) -> dict:
    cov = np.asarray(inp["history_covariance_uasyr2"], dtype=float)
    joint = np.asarray(inp["joint_information"], dtype=float)
    if cov.shape != (3, 3) or joint.shape != (6, 6):
        raise ValueError("unexpected matrix dimensions")
    if not np.allclose(cov, cov.T, rtol=0, atol=1e-12) or not np.allclose(joint, joint.T, rtol=0, atol=1e-12):
        raise ValueError("input matrices must be symmetric")
    eigenvalues, vectors = np.linalg.eigh(cov)
    if eigenvalues[0] <= 0 or np.linalg.eigvalsh(joint)[0] <= 0:
        raise ValueError("input matrices must be positive definite")
    info0 = symmetric_inverse(cov)
    schur = joint[:3, :3] - joint[:3, 3:] @ np.linalg.solve(joint[3:, 3:], joint[3:, :3])
    original_schur_residual = scaled_residual(schur, info0)
    if original_schur_residual >= 1e-10:
        raise AssertionError("retained covariance is inconsistent with profiled joint information")

    k_over_r = inp["K_H_uasyr"] / inp["compensation_R"]
    rows = []
    max_update_residual = 0.0
    max_information_psd_violation = 0.0
    for direction in range(3):
        u = vectors[:, direction]
        previous_best = np.inf
        for tau in TAUS:
            updated_cov = cov + tau**2 * np.outer(u, u)
            updated_info = symmetric_inverse(updated_cov)
            # Independent Sherman--Morrison construction from the frozen profiled C_bb.
            v = info0 @ u
            updated_info_sm = info0 - tau**2 * np.outer(v, v) / (1 + tau**2 * float(u @ v))
            max_update_residual = max(max_update_residual, scaled_residual(updated_info, updated_info_sm))
            info_delta = (info0 - updated_info + (info0 - updated_info).T) / 2
            psd_violation = max(0.0, -float(np.linalg.eigvalsh(info_delta)[0]))
            max_information_psd_violation = max(max_information_psd_violation, psd_violation)
            best_info = float(np.linalg.eigvalsh(updated_info)[-1])
            if best_info > previous_best + 1e-10:
                raise AssertionError("best information increased after a PSD covariance addition")
            previous_best = best_info
            for epsilon in EPSILONS:
                amplitude = k_over_r * epsilon
                d_squared = amplitude**2 * best_info
                power = float(norm.cdf(norm.ppf(ALPHA) + np.sqrt(d_squared)))
                multipliers = {
                    str(target): float((norm.ppf(1 - ALPHA) + norm.ppf(target)) ** 2 / d_squared)
                    for target in TARGETS
                }
                rows.append({
                    "covariance_eigenvector_index": direction,
                    "original_covariance_eigenvalue_uasyr2": float(eigenvalues[direction]),
                    "tau_uasyr": tau,
                    "epsilon": epsilon,
                    "best_information_per_uasyr2": best_info,
                    "mahalanobis_max": float(np.sqrt(d_squared)),
                    "noncentrality_max": float(d_squared),
                    "oracle_level_005_power_upper": power,
                    "information_multiplier_to_oracle_power": multipliers,
                })
    if max_update_residual >= 1e-10 or max_information_psd_violation > 1e-10:
        raise AssertionError("inverse or PSD monotonicity check failed")
    reference = next(r for r in baseline["rows"] if r["epsilon"] == 0.1)
    reproduced = next(r for r in rows if r["epsilon"] == 0.1 and r["tau_uasyr"] == 0)
    baseline_difference = abs(reproduced["oracle_level_005_power_upper"] - reference["gaussian_level_005_power_upper"])
    if baseline_difference >= 1e-12:
        raise AssertionError("retained T6 baseline was not reproduced")
    return {
        "task_id": "R24-K03-DESIGN",
        "scope": "retained profiled C_bb Gaussian working experiment; conditional covariance scenarios",
        "alpha_one_sided": ALPHA,
        "original_covariance_eigenvalues_uasyr2": eigenvalues.tolist(),
        "covariance_update": "Cprime = Cbb + tau^2 uu^T; u is one unit eigenvector of original Cbb",
        "power_formula": "Phi(Phi^{-1}(alpha) + sqrt((K_H epsilon / R)^2 lambda_max(Cprime^{-1})))",
        "multiplier_formula": "(Phi^{-1}(1-alpha) + Phi^{-1}(target_power))^2 / dmax^2",
        "rows": rows,
        "checks": {
            "original_schur_vs_inverse_scaled_residual": original_schur_residual,
            "maximum_updated_inverse_vs_sherman_morrison_scaled_residual": max_update_residual,
            "maximum_information_psd_violation": max_information_psd_violation,
            "baseline_epsilon_01_power_absolute_difference": baseline_difference,
            "scaled_residual_limit": 1e-10,
        },
        "environment": {
            "python": platform.python_version(),
            "python_executable": sys.executable,
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "matplotlib": matplotlib.__version__,
        },
        "original_acceptance_promoted": False,
        "physical_remainder_status": "HOLD",
        "centroid_matter_response_status": "HOLD",
        "new_depth_vsh_moment_performance": "NOT_EVALUABLE",
    }


def plot(result: dict) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(11.2, 8.2), constrained_layout=True)
    colors = ("#23678a", "#647a4e")
    for ax, epsilon in zip(axes.flat[:3], EPSILONS):
        for direction in (0, 1):
            chosen = [r for r in result["rows"] if r["epsilon"] == epsilon and r["covariance_eigenvector_index"] == direction]
            ax.plot([r["tau_uasyr"] for r in chosen],
                    [(r["oracle_level_005_power_upper"] - ALPHA) * 1e6 for r in chosen],
                    "o-", color=colors[direction], label="Cbb eigenvector 1" if direction == 0 else "eigenvectors 2 and 3 (identical bound)")
        ax.set(title=f"Allowed-domain epsilon = {epsilon:g}", xlabel="Added SD tau (microarcsec/year)",
               ylabel="Oracle power above 5%, ppm")
        ax.grid(alpha=0.25)
    axes.flat[0].legend(fontsize=8)
    ax = axes.flat[3]
    for direction in (0, 1):
        chosen = [r for r in result["rows"] if r["epsilon"] == 0.3 and r["covariance_eigenvector_index"] == direction]
        ax.plot([r["tau_uasyr"] for r in chosen],
                [r["information_multiplier_to_oracle_power"]["0.8"] / 1e7 for r in chosen],
                "o-", color=colors[direction])
    ax.set(title="80% target, epsilon = 0.3",
           xlabel="Added SD tau (microarcsec/year)", ylabel="Required information multiplier (x 10^7)")
    ax.grid(alpha=0.25)
    fig.suptitle("K03 retained Gaussian design sensitivity (conditional oracle bound)", fontsize=14)
    fig.savefig(HERE / "POWER_SENSITIVITY.png", dpi=180)
    fig.savefig(HERE / "POWER_SENSITIVITY.pdf", metadata={"CreationDate": None, "ModDate": None})
    plt.close(fig)


def report(result: dict) -> None:
    baseline = [r for r in result["rows"] if r["tau_uasyr"] == 0 and r["covariance_eigenvector_index"] == 0]
    lines = [
        "# R24-K03-DESIGN: retained Gaussian power sensitivity",
        "",
        "This is a conditional design calculation from the retained profiled history covariance. No catalogue replay, new observational moment, or physical response estimate was made. The one-sided level is 0.05. The illustrative domain R||b|| <= epsilon is not a physical remainder certificate.",
        "",
        "The maximum Mahalanobis separation is (K_H epsilon/R) sqrt(lambda_max(Cprime^{-1})). The simple-direction Gaussian Neyman-Pearson power is an oracle upper bound for each scenario. Every target multiplier scales *all* information at the scenario's covariance and holds the response law fixed; it is a requirement, not a demonstrated achievable observing program.",
        "",
        "| epsilon | baseline upper power | baseline power excess (ppm) | baseline information multiplier for 50% | 80% | 90% |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for r in baseline:
        m = r["information_multiplier_to_oracle_power"]
        lines.append(f"| {r['epsilon']:g} | {r['oracle_level_005_power_upper']:.12f} | {(r['oracle_level_005_power_upper'] - ALPHA)*1e6:.6f} | {m['0.5']:.6g} | {m['0.8']:.6g} | {m['0.9']:.6g} |")
    lines.extend([
        "", "The original covariance eigenvalues (ascending, in (microarcsec/year)^2) are " + ", ".join(f"{x:.9f}" for x in result["original_covariance_eigenvalues_uasyr2"]) + ". Each row below adds a rank-one PSD covariance term along one of those *original* eigenvectors.",
        "", "Eigenvector 1 controls the best allowed direction at baseline. Adding variance along it lowers the oracle power; by tau=0.3 its updated eigenvalue exceeds the second eigenvalue, so the optimum switches to eigenvector 2 and the bound plateaus. Adding variance along eigenvector 2 or 3 alone leaves the first eigenvector as the best direction, hence their identical bound in the figure. This is an optimized-direction upper bound; power for a fixed physical direction can change even when this maximum does not.",
        "", "| eigenvector (ascending eigenvalue) | tau (microarcsec/year) | best information / baseline | power excess at epsilon=.3 (ppm) | 80% information multiplier at epsilon=.3 |",
        "|---:|---:|---:|---:|---:|",
    ])
    baseline_info = baseline[0]["best_information_per_uasyr2"]
    for direction in range(3):
        for tau in TAUS:
            r = next(r for r in result["rows"] if r["covariance_eigenvector_index"] == direction and r["tau_uasyr"] == tau and r["epsilon"] == 0.3)
            lines.append(f"| {direction+1} | {tau:g} | {r['best_information_per_uasyr2']/baseline_info:.9f} | {(r['oracle_level_005_power_upper']-ALPHA)*1e6:.6f} | {r['information_multiplier_to_oracle_power']['0.8']:.6g} |")
    checks = result["checks"]
    lines.extend([
        "", "The inverse of the retained Cbb agrees with the Schur complement of the six-parameter joint information: scaled residual " + f"{checks['original_schur_vs_inverse_scaled_residual']:.3g}" + ". Across all updates, direct inverse versus Sherman-Morrison scaled residual is at most " + f"{checks['maximum_updated_inverse_vs_sherman_morrison_scaled_residual']:.3g}" + "; maximum negative eigenvalue magnitude of I0-Iprime is " + f"{checks['maximum_information_psd_violation']:.3g}" + ". The epsilon=.1, tau=0 T6 power differs from the retained result by " + f"{checks['baseline_epsilon_01_power_absolute_difference']:.3g}" + ".",
        "", "## Acquisition needed to change the design", "",
        "The retained Cbb and six-parameter F quantify this existing experiment. I checked the selected-row cache `/mnt/extdrive/workdir/htt_open_data/a22_20261023/quaia_join/quaia_gaia_full_join.npz`: it has 755850 selected rows with reported Quaia z, sky directions, proper motions, per-source errors/correlation, and template fields. The frozen `/mnt/extdrive/workdir/htt_open_data/a22_20261023/astrometry/full_stats.npz` stores the 102-column G and score; `/mnt/extdrive/workdir/htt_open_data/k03_pm_20261023/cross_moments.npz` stores 6x6 A, 6x102 K, and the six-score for the already-run history/local fit. Those files permit a separately contracted finite reported-z design experiment, but they do not contain expanded depth/VSH moments.",
        "", "For actual depth-layer or VSH performance, define the new channel response and windows at the specified epoch/units, then obtain its X^T W X, X^T W Z, Z^T W Z and cross-depth/channel blocks under a declared covariance and selection law. The stored per-source 2x2 errors supply only the old block-diagonal working weights; spatial/source correlations, cross-channel covariance, selected reported-to-true-depth law, nuisance profiling, and optical/radio centroid and matter response must be qualified for physical use. Their expanded Schur information is absent, so a specific new-design improvement factor is NOT_EVALUABLE. The table states the required information multiplier in the retained working model.",
        "", "Original centroid/matter response and the neglected physical remainder remain HOLD. R23-Q's used ultra escalation is unchanged. This result does not promote original K03 acceptance or claim an empirical physical exclusion.",
        "", "Figure: [PNG](POWER_SENSITIVITY.png) · [PDF](POWER_SENSITIVITY.pdf). Complete numeric rows and checks are in [RESULT.json](RESULT.json).",
    ])
    (HERE / "REPORT.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    inp, baseline = load_sources()
    result = calculation(inp, baseline)
    (HERE / "RESULT.json").write_text(json.dumps(result, indent=2) + "\n")
    plot(result)
    report(result)
    manifest = {
        "task_id": "R24-K03-DESIGN",
        "base_head": "dfaf171c37f2636c942a99bf2b9803b57295ac14",
        "source_sha256": {name: sha256(path) for name, path in SOURCE_FILES.items()},
        "output_sha256": {name: sha256(HERE / name) for name in ("design.py", "RESULT.json", "REPORT.md", "POWER_SENSITIVITY.png", "POWER_SENSITIVITY.pdf")},
        "original_acceptance_promoted": False,
    }
    (HERE / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"rows": len(result["rows"]), "checks": result["checks"], "environment": result["environment"]}, indent=2))


if __name__ == "__main__":
    main()
