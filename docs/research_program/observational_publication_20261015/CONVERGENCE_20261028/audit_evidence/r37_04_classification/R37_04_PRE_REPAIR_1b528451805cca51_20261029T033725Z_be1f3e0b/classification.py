"""Finite, conditional Ricci-family compatibility from retained R36 results.

No old producer is imported or rerun. All norms use the source's u_*^2 unit.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.stats import chi2

OUT = Path(__file__).resolve().parent
CONV = OUT.parents[1]
BASE = CONV.parent
REPO = CONV.parents[3]
TABLE = BASE / "OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-10-GEOMETRY-IMAGE/TABLE.json"
STATUS = TABLE.with_name("PUBLICATION_STATUS.json")
GOAL3 = CONV / "imports/four_goals/lanes/GOAL3_CLASSIFICATION.json"
REVIEW = CONV / "imports/four_goals/lanes/INDEPENDENT_REVIEW.json"
EXPECTED = {
    TABLE: "eaf4e567f856a8d01e40f6721613239b8f64e6dc0fbe7d5b35070bfc9faeb363",
    GOAL3: "51d18036b5b56bf359a7e0dce1e8ce811e0f88e19ec15991559ef871048e3dd8",
    REVIEW: "c4fb380e87eb51482c7fd8178a17386b666bac541c5e6594ec3bf16af72846a2",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stf(a: np.ndarray) -> np.ndarray:
    return (a + a.T) / 2 - np.trace(a) * np.eye(3) / 3


def orbit_distance(a: np.ndarray, b: np.ndarray) -> float:
    """Exact SO(3) Frobenius orbit distance for one symmetric tensor per family."""
    return float(np.linalg.norm(np.linalg.eigvalsh(a) - np.linalg.eigvalsh(b)))


def exact_compatibility(y: np.ndarray, means: dict[str, np.ndarray], tau: float) -> list[str]:
    """Closed joint 6D profile tube; y is [trace/sqrt(3), STF5, calibration]."""
    adeq = (y[0] - y[6]) / np.sqrt(2)
    eigy = np.linalg.eigvalsh(stf_from_coords(y[1:6]))
    return [name for name, a in means.items()
            if np.hypot(np.linalg.norm(eigy - np.linalg.eigvalsh(stf(a))),
                        adeq - np.trace(a) / np.sqrt(6)) <= tau + 1e-12]


B = np.array([
    np.diag([1, -1, 0]) / np.sqrt(2),
    np.diag([1, 1, -2]) / np.sqrt(6),
    [[0, 1/np.sqrt(2), 0], [1/np.sqrt(2), 0, 0], [0, 0, 0]],
    [[0, 0, 1/np.sqrt(2)], [0, 0, 0], [1/np.sqrt(2), 0, 0]],
    [[0, 0, 0], [0, 0, 1/np.sqrt(2)], [0, 1/np.sqrt(2), 0]],
], dtype=float)


def coords(a: np.ndarray) -> np.ndarray:
    return np.einsum("aij,ij->a", B, a)


def stf_from_coords(c: np.ndarray) -> np.ndarray:
    return np.einsum("a,aij->ij", c, B)


def raw_mean(a: np.ndarray) -> np.ndarray:
    return np.r_[np.trace(a) / np.sqrt(3), coords(stf(a)), 0.0]


def fixed_q_radius() -> dict:
    """Recheck imported sharp witness without importing its producer."""
    q = np.diag([-1/np.sqrt(2), 0.0, 1/np.sqrt(2)])
    w = np.array([np.sqrt(10)/4, 1.0, np.sqrt(10)/4])
    eye = np.eye(3)

    def octupole(x):
        qx = q @ x
        return ((np.einsum("i,jk->ijk", x, q) + np.einsum("j,ik->ijk", x, q)
                 + np.einsum("k,ij->ijk", x, q))/3
                - 2/15*(np.einsum("ij,k->ijk", eye, qx)
                         + np.einsum("ik,j->ijk", eye, qx)
                         + np.einsum("jk,i->ijk", eye, qx)))

    o = octupole(w)
    v = np.einsum("ijk,jk->i", o, q)
    m = np.trace(q @ q)/3*eye + 2/5*q @ q
    distances = np.abs(v)/np.sqrt(np.diag(m))
    k = int(np.argmin(distances))
    perturb = -v[k]/m[k, k]*octupole(eye[k])
    boundary = o + perturb
    assert abs(np.linalg.norm(o)-1) < 1e-14
    assert abs(np.linalg.norm(perturb)-distances[k]) < 1e-14
    assert abs(np.einsum("ijk,jk->i", boundary, q)[k]) < 1e-14
    return {"radius": float(distances[k]), "nearest_hyperplane": k,
            "attaining_perturbation_norm": float(np.linalg.norm(perturb)),
            "boundary_chirality": float(np.linalg.det(np.column_stack([
                np.einsum("ijk,jk->i", boundary, q),
                q @ np.einsum("ijk,jk->i", boundary, q),
                q @ q @ np.einsum("ijk,jk->i", boundary, q)]))),
            "domain": "Q fixed, simple spectrum; ambient STF rank-3 O Frobenius ball; not uncertain Q or fixed O norm"}


def main() -> None:
    for path, expected in EXPECTED.items():
        assert sha(path) == expected, (path, sha(path))
    src = json.loads(TABLE.read_text())
    prior = json.loads(GOAL3.read_text())
    publication = json.loads(STATUS.read_text())
    assert publication["status"] == "FORMALLY_QUALIFIED_SCOPED_CONDITIONAL_PRODUCT"
    assert prior["source_table_git_blob"] == "1ae270fec9ae55375c01ec1f346f8755d9257049"
    ii = np.array(src["controls"]["II"]["ricci"], float)
    vii = np.array(src["controls"]["VII0matched"]["ricci"], float)
    assert abs(np.trace(ii)-np.trace(vii)) < 1e-14
    assert abs(orbit_distance(ii, vii) - src["matched_orbit_separation"]) < 1e-14
    source_radii = {name: float(src["images"][name]["ricci_F_bound"])
                    for name in ("II", "VII0matched")}
    assert abs(sum(source_radii.values())-src["matched_tensor_radius_sum"]) < 1e-13
    assert np.linalg.norm(np.array(src["controls"]["I"]["ricci"]) -
                          np.array(src["controls"]["flatVII0"]["ricci"])) < 1e-14

    # Scaling the source's structure coefficients by a scales spatial Ricci by a^2.
    # This is a declared one-parameter family of instantaneous supplied geometries.
    amplitudes = np.array([0., .125, .25, .375, .5, .625, .75, .875, 1.])
    sigmas = np.array([.03, .06, .12, .18, .27])
    errors = np.array([0., .1, .2])
    r95 = float(np.sqrt(chi2.ppf(.95, 6)))
    rows = []
    for a in amplitudes:
        means = {"II": a*a*ii, "VII0matched": a*a*vii}
        delta = orbit_distance(*means.values())
        stf_norms = {name: float(np.linalg.norm(stf(t))) for name, t in means.items()}
        radial_gap = abs(stf_norms["II"] - stf_norms["VII0matched"])
        y_ii = raw_mean(means["II"])
        y_mid = (raw_mean(means["II"]) + raw_mean(means["VII0matched"])) / 2
        # The midpoint in this source frame is a diagnostic point, not necessarily
        # the closest orbit midpoint. Exact orbit midpoint uses sorted eigenvalues.
        eig_mid = (np.linalg.eigvalsh(means["II"]) + np.linalg.eigvalsh(means["VII0matched"])) / 2
        y_orbit_mid = raw_mean(np.diag(eig_mid))
        for sigma in sigmas:
            for eps in errors:
                tau = r95*sigma + eps
                row = {
                    "amplitude": float(a), "noise_sigma": float(sigma), "joint_response_error": float(eps),
                    "joint_95_noise_radius": r95*sigma, "tube_radius": float(tau),
                    "exact_orbit_center_separation": delta,
                    "certified_exclusive_margin": delta-2*tau,
                    "strong_quadratic_STF_norm_gap": radial_gap,
                    "strong_quadratic_exclusive_margin": radial_gap-2*tau,
                    "II_center_compatible": "|".join(exact_compatibility(y_ii, means, tau)),
                    "orbit_midpoint_compatible": "|".join(exact_compatibility(y_orbit_mid, means, tau)),
                    "source_frame_midpoint_compatible": "|".join(exact_compatibility(y_mid, means, tau)),
                    "trace_difference": float(np.trace(means["II"])-np.trace(means["VII0matched"])),
                    "quadratic_STF_II": stf_norms["II"]**2,
                    "quadratic_STF_VII0": stf_norms["VII0matched"]**2,
                    "R36_source_radii_applicable": bool(a == 1),
                    "R36_source_bound_margin": (delta-sum(source_radii.values())-2*r95*sigma) if a == 1 else "",
                    "R36_source_II_center_compatible": ("|".join(name for name, tensor in means.items()
                        if np.hypot(np.linalg.norm(np.linalg.eigvalsh(stf_from_coords(y_ii[1:6]))
                                             -np.linalg.eigvalsh(stf(tensor))),
                                    (y_ii[0]-y_ii[6])/np.sqrt(2)-np.trace(tensor)/np.sqrt(6))
                           <= r95*sigma+source_radii[name]+1e-12)) if a == 1 else "",
                }
                rows.append(row)
    with (OUT/"FAMILY_SEPARATION.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, rows[0]); writer.writeheader(); writer.writerows(rows)

    # Fixed-amplitude pairwise differences span the STF5 image; the seventh raw
    # coordinate is nuisance and the sixth profiled coordinate is adequacy.
    rng = np.random.default_rng(202610294)
    lr_max = 0.0
    rotation_max = 0.0
    for _ in range(200):
        rot = Rotation.random(random_state=rng).as_matrix()
        q1 = Rotation.random(random_state=rng).as_matrix()
        q2 = Rotation.random(random_state=rng).as_matrix()
        m1 = raw_mean(q1 @ ii @ q1.T)
        m2 = raw_mean(q2 @ vii @ q2.T)
        y = rng.normal(size=7)
        n = np.array([1., 0, 0, 0, 0, 0, 1.])
        p = np.eye(7)-np.outer(n, n)/2
        full = np.dot(p@(y-m2), p@(y-m2))-np.dot(p@(y-m1), p@(y-m1))
        compressed = np.dot(y[1:6]-m2[1:6], y[1:6]-m2[1:6])-np.dot(y[1:6]-m1[1:6], y[1:6]-m1[1:6])
        lr_max = max(lr_max, abs(full-compressed))
        rotation_max = max(rotation_max, abs(orbit_distance(rot@ii@rot.T, rot@vii@rot.T)-orbit_distance(ii, vii)))
    assert lr_max < 1e-12 and rotation_max < 1e-12
    assert abs(np.linalg.matrix_rank(np.eye(7)-np.outer(n,n)/2)-6) == 0
    # In a single fixed-amplitude experiment an off-family trace displacement
    # survives the nuisance projection and can reject all listed families.
    y_bad = raw_mean(ii).copy(); y_bad[0] += 1
    tau_bad = r95*.12 + .1
    assert not exact_compatibility(y_bad, {"II":ii,"VII0matched":vii}, tau_bad)
    chirality = fixed_q_radius()
    assert abs(chirality["radius"]-1/np.sqrt(3)) < 1e-14

    result = {
        "schema": "htt.r37.family_compatibility/1", "owner": "R37-04-CLASSIFICATION",
        "claim_tier": "conditional finite geometry-response method; no observed family identification",
        "artifact_mode": "source-qualified conditional numeric/analytic", "allowed_use": "P2/P5 finite methods/report delta",
        "forbidden_uses": ["observed Bianchi label", "native solver or full T/E/B atlas", "independent combination with Gaia/CF4/PM"],
        "transfer_source": "none; instantaneous R36 geometry", "null_status": "synthetic Gaussian control only; empirical nulls unavailable",
        "covariance_status": "declared common sigma^2 I7 with one common calibration nuisance; no observed covariance",
        "orientation": "proper SO(3), oriented orthonormal triad, epsilon123=+1; isotropic Frobenius tensor metric",
        "frame_units": "R36 hypersurface-normal frame; spatial Ricci in u_*^2; amplitudes dimensionless",
        "input_sha256": {str(path.relative_to(REPO)): sha(path) for path in EXPECTED},
        "script_sha256": sha(Path(__file__)),
        "source_publication_status": publication["status"],
        "family_domain": "For each fixed a in [0,1], structure coefficients are multiplied by a, Ricci by a^2; SO(3) orientations independent per family; no physical history or sky transfer assumed",
        "amplitude_grid": amplitudes.tolist(), "noise_grid": sigmas.tolist(), "joint_error_grid": errors.tolist(),
        "analytic_orbit_gap": "sqrt(2) a^2 exactly for the two supplied Ricci spectra; finite grid evaluates this formula, not a minimizer approximation",
        "analytic_global_domain_gap": 0.0,
        "R36_source_set_bounds_at_amplitude_1": {"per_family_Frobenius_radii": source_radii,
            "sum": sum(source_radii.values()), "no_noise_center_set": ["II"],
            "margin_at_sigma_0p12": orbit_distance(ii,vii)-sum(source_radii.values())-2*r95*.12,
            "scope": "Conservative R36 deterministic ellipsoid-image bounds; only bound at supplied a=1. Added synthetic Gaussian noise is a declared sensitivity, not measured noise."},
        "flrw_origin": "Both scaled families meet at Ricci=0 for a=0; I and flatVII0 are equivalent local flat presentations at all source control values",
        "witness": {"II_eigenvalues": np.linalg.eigvalsh(ii).tolist(), "VII0_eigenvalues": np.linalg.eigvalsh(vii).tolist(),
                    "trace_each": float(np.trace(ii)), "tr_R2": [float(np.trace(ii@ii)), float(np.trace(vii@vii))],
                    "STF_norms": [float(np.linalg.norm(stf(ii))), float(np.linalg.norm(stf(vii)))],
                    "strong_scalar_STF_quadratic_gap": float(np.linalg.norm(stf(vii))**2-np.linalg.norm(stf(ii))**2)},
        "common_event": {"alpha": .05, "profiled_dimension": 6, "noise_quantile": r95,
                         "tube_formula": "tau=sqrt(chi2_6(.95))*sigma+epsilon, one joint event and one joint response-error ball",
                         "coverage": "at least .95 for a listed true family under this declared zero-bias Gaussian law and bounded deterministic error"},
        "carrier": {"fixed_amplitude_pairwise_LR_dimension": 5, "profiled_raw_dimension": 6,
                    "discarded_adequacy_dimension": 1, "max_full_vs_carrier_squared_distance_difference": lr_max,
                    "adequacy_coordinate": "(y_trace-y_calibration)/sqrt(2)-tr(R)/sqrt(6)",
                    "varying_amplitude_warning": "If a is fitted jointly rather than conditioned, trace changes and the common carrier must include the sixth profiled coordinate."},
        "orientation_check_max_absolute_error": rotation_max,
        "out_of_family_control": {"raw_trace_shift": 1.0, "adequacy_residual": float(1/np.sqrt(2)),
                                  "tube_at_sigma_0p12_epsilon_0p1": tau_bad,
                                  "compatible_set": []},
        "prior_saved_MC_at_a1_epsilon0p1": prior["monte_carlo"],
        "prior_saved_MC_scope": "50,000 synthetic draws per noise level; reused, not replayed; frequencies are not analytic probabilities or empirical null coverage",
        "fixed_Q_chirality": chirality,
        "gauss_bridge": "R3 = E + pi/2 - h Sigma + STF(Sigma^2) + [2rho+2Lambda-6h^2+Sigma:Sigma] I/3 in declared kappa=1 units; shear alone does not supply E or pi",
        "classification_limit": "II/VII0 separation is for supplied instantaneous scaled fixtures and the declared response law; no universal Bianchi type classification",
        "original42": "17/42 scientific; separate analytic 18/42; no promotion by this product",
        "artifact_metadata": {
            name: {"owner": "R37-04-CLASSIFICATION", "claim_tier": "conditional finite methods",
                   "artifact_mode": "synthetic/analytic", "allowed_use": "source-qualified P2/P5 finite comparison",
                   "transfer_source": "none", "null_status": "synthetic only",
                   "covariance_status": "same declared Gaussian law and nuisance; no observed covariance",
                   "forbidden_use": "empirical Bianchi family identification"}
            for name in ("FAMILY_SEPARATION.csv", "family_compatibility_vs_amplitude.pdf",
                         "separation_vs_error_budget.pdf", "adequacy_residual.pdf",
                         "chirality_stability_radius.pdf")},
    }
    (OUT/"FAMILY_COMPATIBILITY_RESULT.json").write_text(json.dumps(result, indent=2)+"\n")
    plot(amplitudes, sigmas, errors, r95, rows)
    print(json.dumps({"rows":len(rows), "orbit_gap_a1":orbit_distance(ii,vii),
                      "LR_error":lr_max,"rotation_error":rotation_max,"fixed_Q_radius":chirality["radius"]}))


def plot(amplitudes, sigmas, errors, r95, rows):
    plt.rcParams.update({"font.size": 9})
    fig, ax = plt.subplots(figsize=(6.4, 4.2), layout="constrained")
    for sigma in [.03, .12, .27]:
        tau = r95*sigma+.1
        ax.plot(amplitudes, np.sqrt(2)*amplitudes**2-2*tau, label=f"sigma={sigma:g}")
    ax.axhline(0, color="black", lw=.8)
    ax.set(xlabel="Structure amplitude a", ylabel="Exclusive separation margin (u_*^2)",
           title="II/VII0 compatibility, common error 0.1")
    ax.legend(); fig.savefig(OUT/"family_compatibility_vs_amplitude.pdf"); plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.4, 4.2), layout="constrained")
    for a in [.25,.5,1.]:
        for sigma in [.03,.12]:
            ax.plot(errors, np.sqrt(2)*a*a-2*(r95*sigma+errors), marker="o", label=f"a={a:g}, sigma={sigma:g}")
    ax.axhline(0, color="black", lw=.8)
    ax.set(xlabel="Joint response-error radius (u_*^2)", ylabel="Certified margin (u_*^2)",
           title="Exact orbit gap minus two common tube radii")
    ax.legend(fontsize=7, ncol=2); fig.savefig(OUT/"separation_vs_error_budget.pdf"); plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.4, 4.2), layout="constrained")
    residual = np.linspace(0, 1, 200)
    tau = r95*.12+.1
    ax.plot(residual, residual, label="Profiled discarded-space residual")
    ax.axhline(tau, color="firebrick", label=f"Joint tube at sigma=.12, eps=.1: {tau:.3f}")
    ax.scatter([1/np.sqrt(2)], [1/np.sqrt(2)], color="black", label="Out-of-family trace shift")
    ax.set(xlabel="Raw trace-only shift", ylabel="Adequacy norm (u_*^2)",
           title="Five STF LR coordinates miss an out-of-family trace")
    ax.legend(fontsize=8); fig.savefig(OUT/"adequacy_residual.pdf"); plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.4, 3.6), layout="constrained")
    radius = 1/np.sqrt(3)
    x = np.linspace(0, .9, 200)
    ax.plot(x, radius-x, label="Signed guarantee margin")
    ax.axhline(0, color="black", lw=.8)
    ax.axvline(radius, color="firebrick", ls="--", label=f"Sharp radius = {radius:.6f}")
    ax.set(xlabel="Ambient octupole Frobenius error, Q fixed", ylabel="Radius minus error",
           title="Exact fixed-Q chirality sign stability")
    ax.legend(fontsize=8); fig.savefig(OUT/"chirality_stability_radius.pdf"); plt.close(fig)


if __name__ == "__main__":
    main()
