"""Conditional five-coordinate optical STF image of the sealed distance fits.

This program reads stored fits only.  Its ellipsoids are fixed-law reference
scenarios; no source-qualified confidence coverage is asserted.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
from scipy.optimize import brentq
from scipy.stats import chi2

HERE = Path(__file__).resolve().parent
CAMPAIGN = HERE.parent
ROOT = HERE.parents[4]
INPUT = CAMPAIGN / "R24-OPTICAL-SHEAR_INPUT.json"
DISTANCE = CAMPAIGN / "distance/RESULT.json"
STF_NAMES = [f"STF_{j}" for j in range(1, 6)]
KAPPA = -math.log(10) / 5  # sigma_eff/H per magnitude-residual STF coordinate
REMAINDER_L2_RADII = (0.0, 0.05, 0.10, 0.25)
STF = np.array([
    np.diag([1., -1., 0.]) / math.sqrt(2),
    np.diag([-1., -1., 2.]) / math.sqrt(6),
    [[0., 1/math.sqrt(2), 0.], [1/math.sqrt(2), 0., 0.], [0., 0., 0.]],
    [[0., 0., 1/math.sqrt(2)], [0., 0., 0.], [1/math.sqrt(2), 0., 0.]],
    [[0., 0., 0.], [0., 0., 1/math.sqrt(2)], [0., 1/math.sqrt(2), 0.]],
])


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_sources() -> dict:
    assert sha(INPUT) == "af216d8bd92fcc4814294e785abdcb72b4576f685ca5ca18808841b5779d09e0"
    spec = json.loads(INPUT.read_text())
    actual = {}
    for item in spec["sources"]:
        path = ROOT / item["path"]
        digest = sha(path)
        if digest != item["sha256"]:
            raise ValueError(f"sealed input differs: {path}")
        if "bytes" in item and path.stat().st_size != item["bytes"]:
            raise ValueError(f"sealed size differs: {path}")
        actual[item["path"]] = {"sha256": digest, "bytes": path.stat().st_size}
    if spec["consumed_review"]["candidate_identity"] != "sha256:" + actual[str(DISTANCE.parent.relative_to(ROOT) / "ARTIFACT_MANIFEST.json")]["sha256"]:
        raise ValueError("review candidate does not match consumed manifest")
    return {"input_sha256": sha(INPUT), "sources": actual}


def symmetric_part(a: np.ndarray) -> np.ndarray:
    if np.max(np.abs(a - a.T)) > 1e-10:
        raise ValueError("full coefficient covariance asymmetric")
    return (a + a.T) / 2


def projected_max_norm(b: np.ndarray, C: np.ndarray, radius_sq: float) -> tuple[float, float]:
    """Exact max norm on (q-b)' C^-1 (q-b) <= radius_sq.

    The secular root is above the top covariance eigenvalue.  All actual
    strata have nonzero projection onto that eigenspace; special synthetic
    zero-center input uses the exact spectral answer.
    """
    eig, U = np.linalg.eigh(C)
    if eig[0] <= 0:
        raise ValueError("projected covariance not positive definite")
    z = U.T @ b
    if np.linalg.norm(b) < 1e-14:
        return math.sqrt(radius_sq * eig[-1]), 0.0
    def constraint(lam):
        return float(np.sum(eig * z*z / (lam-eig)**2) - radius_sq)
    low = float(np.nextafter(eig[-1], math.inf))
    if constraint(low) <= 0:
        raise ValueError("degenerate secular top-eigenspace requires separate boundary treatment")
    high = max(2*eig[-1], eig[-1] + np.linalg.norm(b)*math.sqrt(eig[-1]/radius_sq))
    while constraint(high) > 0:
        high *= 2
    lam = brentq(constraint, low, high, xtol=1e-14, rtol=1e-14)
    q = U @ (lam*z/(lam-eig))
    residual = abs(float((q-b) @ np.linalg.solve(C, q-b)) - radius_sq)
    if residual > 1e-9:
        raise ValueError(f"secular ellipsoid boundary error {residual}")
    return float(np.linalg.norm(q)), residual


def rotation_check(b: np.ndarray, C: np.ndarray) -> dict:
    # Deterministic proper rotation, independent of the fitting design.
    axis = np.array([2., -3., 5.]); axis /= np.linalg.norm(axis)
    x, y, z = axis
    skew = np.array([[0., -z, y], [z, 0., -x], [-y, x, 0.]])
    angle = 0.73
    R = np.eye(3) + math.sin(angle)*skew + (1-math.cos(angle))*(skew@skew)
    M = np.einsum("aij,ik,bkl,jl->ab", STF, R, STF, R)
    B = np.einsum("a,aij->ij", b, STF)
    rotated = R @ B @ R.T
    coeff = M @ b
    errors = [
        float(np.max(np.abs(np.einsum("a,aij->ij", coeff, STF)-rotated))),
        float(np.max(np.abs(M.T@M-np.eye(5)))),
        abs(float(np.linalg.norm(coeff)-np.linalg.norm(b))),
        float(np.max(np.abs(np.linalg.eigvalsh(M@C@M.T)-np.linalg.eigvalsh(C)))),
        abs(float(np.trace(rotated))),
        abs(float(np.linalg.det(R)-1)),
    ]
    if max(errors) > 1e-12:
        raise ValueError(f"STF rotation check failed: {errors}")
    return {"proper_rotation_angle_rad": angle, "max_reconstruction_orthogonality_norm_cov_trace_det_error": max(errors)}


def model_image(model: dict) -> dict:
    names = model["column_names_raw_units"]
    fit = model["full_fit"]
    if fit["coefficient_status"] != "IDENTIFIABLE" or fit["rank"] != len(names):
        raise ValueError("full model rank not identified")
    beta = np.asarray(fit["coefficient_raw_units"], dtype=float)
    full_cov = symmetric_part(np.asarray(fit["coefficient_covariance_raw_units"], dtype=float))
    if len(beta) != len(names) or full_cov.shape != (len(names), len(names)):
        raise ValueError("full coefficient/covariance dimension mismatch")
    if np.linalg.eigvalsh(full_cov)[0] <= 0:
        raise ValueError("full coefficient covariance not positive definite")
    indices = [names.index(n) for n in STF_NAMES]
    L = np.zeros((5, len(names)))
    L[np.arange(5), indices] = 1
    b = L @ beta
    C = symmetric_part(L @ full_cov @ L.T)
    q = KAPPA*b
    qcov = KAPPA*KAPPA*C
    B = np.einsum("a,aij->ij", b, STF)
    S = KAPPA*B
    if max(abs(float(np.trace(B))), abs(float(np.trace(S)))) > 1e-12:
        raise ValueError("STF trace failed")
    np.testing.assert_allclose(np.einsum("aij,bij->ab", STF, STF), np.eye(5), rtol=0, atol=1e-12)
    np.testing.assert_allclose(np.array([np.sum(B*t) for t in STF]), b, rtol=0, atol=1e-12)
    joint_radius_sq = float(chi2.ppf(.95, len(names)))
    norm_max, secular_residual = projected_max_norm(q, qcov, joint_radius_sq)
    zero_mahalanobis = float(q @ np.linalg.solve(qcov, q))
    lower = 0.0 if zero_mahalanobis <= joint_radius_sq + 1e-10 else None
    if lower is None:
        raise ValueError("actual lower norm needs nonzero-boundary solver")
    norm_center = float(np.linalg.norm(q))
    l2_center = math.sqrt(2/15)*norm_center
    l2_upper = math.sqrt(2/15)*norm_max
    intervals = []
    for r in REMAINDER_L2_RADII:
        # This is the normalized-form T2 algebraic image.  Physical T2
        # requires the missing common-congruence H and joint error event.
        upper = 1.25*(l2_upper+r)**2
        intervals.append({"declared_remainder_radius_L2_h2_over_H": r,
                          "conditional_sigma2_lower": 0.0,
                          "conditional_sigma2_upper": upper,
                          "width": upper,
                          "positive_lower_nonvacuous": False})
    return {
        "stf_status": "DEFINED_CONDITIONAL_MAGNITUDE_TENSOR",
        "coefficient_names_raw_units": names,
        "coefficient_full_raw_units": beta.tolist(),
        "coefficient_covariance_full_raw_units": full_cov.tolist(),
        "covariance_law": "stored full GLS coefficient covariance with training ML plug-in scale; all shared nuisance and cross-blocks retained",
        "stf_column_indices": indices,
        "stf_coefficient_mag": b.tolist(),
        "stf_covariance_mag2": C.tolist(),
        "stf_nuisance_crosscovariance": full_cov[np.ix_(indices, [i for i in range(len(names)) if i not in indices])].tolist(),
        "magnitude_residual_STF_J2000": B.tolist(),
        "sigma_eff_over_H_STF_J2000": S.tolist(),
        "sigma_eff_over_H_coordinates": q.tolist(),
        "sigma_eff_over_H_covariance": qcov.tolist(),
        "point_norm_sigma_eff_over_H": norm_center,
        "point_full_sky_L2_h2_over_H": l2_center,
        "point_sigma_eff2_over_6H2": norm_center**2/6,
        "reference_region": {
            "law": "fixed Gaussian coefficient law with stored plug-in covariance; chi-square radius is a declared algebraic reference only",
            "event": "all full p coefficients in one joint ellipsoid, nuisance retained before STF projection",
            "nominal_quantile": .95,
            "full_dimension": len(names),
            "radius_sq_chi2_p": joint_radius_sq,
            "zero_STF_mahalanobis_sq": zero_mahalanobis,
            "zero_inside": True,
            "norm_sigma_eff_over_H_interval": [lower, norm_max],
            "l2_h2_over_H_interval": [0., l2_upper],
            "secular_boundary_residual": secular_residual,
            "not_coverage": "estimated scale and covariance law, selected sample and finite-z response unqualified; no true 95 percent confidence claim"
        },
        "remainder_sensitivity": intervals,
        "physical_H_strata": {
            "H_absolute_from_free_intercept": "NOT_MEASURED",
            "H_minus_nonpositive": "UNBOUNDED_UPPER_IN_T2_QUOTIENT",
            "positive_joint_H_bounds": "UNAVAILABLE",
            "registered_G_congruence_map": "HOLD",
            "finite_z_boost_selection_calibration_remainder": "HOLD_NOT_MEASURED",
            "physical_T2_application": "HOLD"
        },
        "rotation_check": rotation_check(b, C),
    }


def no_stf_model(model: dict) -> dict:
    """Retain model A's whole state without inventing five absent coordinates."""
    names = model["column_names_raw_units"]
    fit = model["full_fit"]
    if any(name in names for name in STF_NAMES):
        raise ValueError("no-STF model unexpectedly contains STF coordinate")
    C = symmetric_part(np.asarray(fit["coefficient_covariance_raw_units"], dtype=float))
    return {"stf_status": "UNDEFINED_NO_STF_COORDINATES_IN_MODEL_A",
            "coefficient_names_raw_units": names,
            "coefficient_full_raw_units": fit["coefficient_raw_units"],
            "coefficient_covariance_full_raw_units": C.tolist(),
            "physical_shear_G": "HOLD_NOT_A_ZERO_SHEAR_MEASUREMENT"}


def run() -> dict:
    sources = check_sources()
    d = json.loads(DISTANCE.read_text())
    if d["cohort"]["released"] != 274 or d["cohort"]["undefined"] != 354:
        raise ValueError("sealed cohort sizes changed")
    out = {
        "task": "R24-OPTICAL-SHEAR",
        "source": sources,
        "owner": "HTT observational scenario analysis",
        "claim_tier": "C0_CONDITIONAL_TENSOR_SCENARIO",
        "observed_runtime": "UNKNOWN",
        "input_cohort": {"selected": 628, "released": 274, "undefined": 354},
        "convention": "J2000 n points observer to source; magnitude residual quadrupole B:nn; sigma_eff/H=-(ln10/5)B in small-anisotropy fixed-redshift scenario; STF Frobenius-orthonormal basis from sealed distance code",
        "reference_law": "stored full GLS coefficient covariance times training ML plug-in scale; fixed Gaussian algebraic reference, no qualified survey confidence coverage",
        "scenario_remainder_radii_L2_h2_over_H": list(REMAINDER_L2_RADII),
        "physical_shear_G": "HOLD_NO_REGISTERED_CONGRUENCE_MAP_OR_MEASURED_REMAINDER",
        "original_acceptance": "UNCHANGED_17_OF_42_EXTERNAL_OR_18_OF_42_ANALYTIC_ALTERNATE",
        "scenarios": {},
    }
    for scenario, block in d["scenarios"].items():
        models = block["models"]
        out["scenarios"][scenario] = {
            "a_mag": block["a_mag"], "b_mag": block["b_mag"],
            "models": {"A_calibration_flow": no_stf_model(models["A_calibration_flow"]),
                       **{name: model_image(models[name]) for name in ("B_optical_STF", "C_union")}}
        }
    HERE.joinpath("RESULT.json").write_text(json.dumps(out, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"task": out["task"], "scenarios": len(out["scenarios"]),
                      "tensor_images": 8, "all_zero_inside": True,
                      "physical_shear_G": out["physical_shear_G"]}))
    return out


if __name__ == "__main__":
    run()
