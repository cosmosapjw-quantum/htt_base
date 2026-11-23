"""R99: shared angular nuisance propagated through actual Gaia normal equations.

This supplies a declared covariance contribution and a supported-subspace
diagnostic. It does not calibrate the Gaia sky or add the contribution to a
jackknife covariance that may already contain spatial systematics.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import platform
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "docs/research_program/observational_publication_20261015"
R98 = BASE / "R98_FOURTH_RESEARCH_CYCLE_20261123"
OUT = BASE / "R99_FIFTH_BLOCKER_RESOLUTION_20261123"


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda: f.read(2**20), b""):
            h.update(b)
    return h.hexdigest()


def patch_response(normal_by_patch, components=6):
    """Return J[p, coefficient, shared-field component] in one fixed basis."""
    f = np.asarray(normal_by_patch, dtype=float)
    if f.ndim != 3 or f.shape[1] != f.shape[2]:
        raise ValueError("patch normal matrices must have shape (patch, d, d)")
    if not np.isfinite(f).all() or not 1 <= components <= f.shape[1]:
        raise ValueError("finite matrices and supported component count required")
    if not np.allclose(f, f.swapaxes(1, 2), rtol=1e-11, atol=1e-12):
        raise ValueError("normal matrices must be symmetric")
    total = f.sum(axis=0)
    e = np.linalg.eigvalsh(total)
    if e[0] <= 0:
        raise ValueError("normal matrix is not positive definite")
    return np.linalg.solve(total, f)[:, :, :components]


def chord_kernel(centers, angle_degrees):
    """PSD restriction of a Euclidean RBF to unit patch-center vectors."""
    n = np.asarray(centers, dtype=float)
    if n.ndim != 2 or n.shape[1] != 3 or not np.isfinite(n).all():
        raise ValueError("finite patch-center 3-vectors required")
    if not np.allclose(np.sum(n*n, axis=1), 1.0, atol=1e-12, rtol=0):
        raise ValueError("patch centers must be unit vectors")
    if not np.isfinite(angle_degrees) or not 0 < angle_degrees <= 180:
        raise ValueError("angular scale must be in (0, 180] degrees")
    ell = 2*np.sin(np.deg2rad(angle_degrees)/2)
    d2 = np.maximum(0.0, 2-2*(n@n.T))
    return np.exp(-d2/(2*ell*ell))


def covariance_from_response(response, kernel):
    """Shared field covariance; latent component variance is one."""
    j = np.asarray(response, dtype=float)
    k = np.asarray(kernel, dtype=float)
    if j.ndim != 3 or k.shape != (j.shape[0], j.shape[0]):
        raise ValueError("response/kernel dimensions differ")
    if not np.isfinite(j).all() or not np.isfinite(k).all():
        raise ValueError("finite response and kernel required")
    if not np.allclose(k, k.T, rtol=1e-12, atol=1e-14):
        raise ValueError("kernel is not symmetric")
    eig = np.linalg.eigvalsh(k)
    if eig[0] < -1e-12*max(1.0, eig[-1]):
        raise ValueError("kernel is not positive semidefinite")
    c = np.einsum("pdr,pq,qer->de", j, k, j, optimize=True)
    return (c+c.T)/2


def joint_covariance(responses, kernel):
    j = np.asarray(responses, dtype=float)
    if j.ndim != 4:
        raise ValueError("responses must be (fit, patch, d, field)")
    merged = j.transpose(1, 0, 2, 3).reshape(j.shape[1], -1, j.shape[3])
    return covariance_from_response(merged, kernel)


def supported_subspace(theta, covariance, relative_tolerance=1e-10):
    """Report tested and untested components; no chi-square calibration."""
    y = np.asarray(theta, dtype=float)
    c = np.asarray(covariance, dtype=float)
    if c.shape != (len(y), len(y)) or not np.isfinite(c).all():
        raise ValueError("invalid covariance")
    if not np.isfinite(y).all() or not 0 < relative_tolerance < 1:
        raise ValueError("invalid vector/tolerance")
    if not np.allclose(c, c.T, rtol=1e-10, atol=1e-11):
        raise ValueError("covariance is not symmetric")
    ev, u = np.linalg.eigh((c+c.T)/2)
    scale = float(ev[-1])
    if scale < 0 or ev[0] < -1e-10*max(scale, 0.0):
        raise ValueError("covariance has a materially negative eigenvalue")
    use = ev > relative_tolerance*scale if scale > 0 else np.zeros(len(ev), dtype=bool)
    projection = u[:, use]@(u[:, use].T@y)
    remainder = y-projection
    q = float(np.sum(((u[:, use].T@y)/np.sqrt(ev[use]))**2))
    ynorm = float(np.hypot.reduce(y))
    remainder_norm = float(np.hypot.reduce(remainder))
    return {
        "dimension": len(y), "rank": int(use.sum()),
        "supported_quadratic_form": q,
        "coefficient_euclidean_norm_microasyr": ynorm,
        "supported_component_norm_microasyr": float(np.linalg.norm(projection)),
        "unsupported_component_norm_microasyr": remainder_norm,
        "unsupported_squared_norm_fraction": (remainder_norm/ynorm)**2 if ynorm else 0.0,
        "orthogonality_residual": float(abs(projection@remainder)),
        "relative_eigenvalue_cut": relative_tolerance,
        "calibrated_p": None,
        "nullspace_is_unmeasured_not_zero": True,
    }


def run(output=OUT/"GAIA_SHARED_FIELD_RESULTS.json"):
    import healpy as hp
    t0 = time.monotonic()
    source = R98/"GAIA_FULL_SHARED_PATCH.json"
    old = json.loads(source.read_text())
    meta = old["joint_160d_patch_covariance"]
    cache = Path(meta["cache_path"])
    actual_sha = sha256(cache)
    if actual_sha != meta["sha256"]:
        raise RuntimeError("Gaia sufficient-statistic cache no longer matches R98")
    with np.load(cache, allow_pickle=False) as data:
        names = [str(v) for v in data["names"]]
        if names != meta["order"]:
            raise RuntimeError("fit order differs from source receipt")
        matrices = {name: data[name+"__F"].copy() for name in names}
        rhs = {name: data[name+"__s"].copy() for name in names}
        patch_cov = data["cov"].copy()
    j = np.stack([patch_response(matrices[n], 6) for n in names])
    nfit, npatch, dim, nf = j.shape
    if (nfit, npatch, dim, nf) != (10, 48, 16, 6):
        raise RuntimeError("unexpected actual-source response population")
    eye = np.eye(dim)[:, :nf]
    constant_error = float(np.max(np.abs(j.sum(axis=1)-eye[None])))
    if constant_error > 3e-11:
        raise RuntimeError("constant common-field response identity failed")
    theta = np.concatenate([np.asarray(old["fits"][n]["coefs_microasyr"]) for n in names])
    subspace = supported_subspace(theta, patch_cov)
    # Independent refit: modify native RHS in mas/year and solve again.
    g = 5*np.sin(np.arange(npatch*nf).reshape(npatch, nf)+0.5)
    refit_errors = {}
    for a, name in enumerate(names):
        f = matrices[name]
        total = f.sum(axis=0)
        s = rhs[name].sum(axis=0)
        shift = np.einsum("pdr,pr->d", f[:, :, :nf], g)/1000
        refit = 1000*(np.linalg.solve(total, s+shift)-np.linalg.solve(total, s))
        pred = np.einsum("pdr,pr->d", j[a], g)
        refit_errors[name] = float(np.max(np.abs(refit-pred)))
    if max(refit_errors.values()) > 3e-10:
        raise RuntimeError("shared field disagrees with actual-source RHS refit")
    centers = np.asarray(hp.pix2vec(2, np.arange(48))).T
    pairs = [(x["a"], x["b"]) for x in old["comparisons"]]
    scenarios = []
    arrays = {"responses": j, "fit_names": np.asarray(names)}
    for angle in (15., 30., 60.):
        kernel = chord_kernel(centers, angle)
        full = joint_covariance(j, kernel)
        ev = np.linalg.eigvalsh(full)
        if ev[0] < -1e-10*max(ev[-1], 1.0):
            raise RuntimeError("shared covariance lost positivity")
        contrasts = []
        for a, b in pairs:
            ia, ib = names.index(a), names.index(b)
            shared = covariance_from_response(j[ia]-j[ib], kernel)
            independent = (covariance_from_response(j[ia], kernel)
                           + covariance_from_response(j[ib], kernel))
            delta = (np.asarray(old["fits"][a]["coefs_microasyr"])
                     -np.asarray(old["fits"][b]["coefs_microasyr"]))
            sectors = {}
            for sector, sl in (("glide", slice(0,3)), ("spin", slice(3,6)),
                               ("E2", slice(6,11)), ("B2", slice(11,16))):
                tr = float(np.trace(shared[sl, sl]))
                sectors[sector] = {
                    "unit_field_variance_trace": tr,
                    "observed_coefficient_difference_norm_microasyr": float(np.linalg.norm(delta[sl])),
                    "field_amplitude_for_equal_norm_and_rms_microasyr": float(np.linalg.norm(delta[sl])/np.sqrt(tr)) if tr > 0 else None,
                    "amplitude_is_scenario_not_estimate": True,
                }
            contrasts.append({
                "a": a, "b": b,
                "trace_shared_unit_field": float(np.trace(shared)),
                "trace_independent_unit_fields": float(np.trace(independent)),
                "trace_ratio_shared_over_independent": float(np.trace(shared)/np.trace(independent)),
                "sectors": sectors,
            })
        arrays["cov_angle_"+str(int(angle))] = full
        scenarios.append({
            "angular_scale_degrees": angle, "latent_component_sd_microasyr": 1.0,
            "covariance_trace": float(np.trace(full)),
            "min_eigenvalue": float(ev[0]), "max_eigenvalue": float(ev[-1]),
            "contrasts": contrasts,
        })
    # K=11^T gives one common glide/spin field and exact contrast cancellation.
    jdiff = j[names.index("quaia_z0")]-j[names.index("quaia_z3")]
    constant_contrast = covariance_from_response(jdiff, np.ones((48,48)))
    coefficient_ref = np.max(np.abs(jdiff.sum(axis=0)))
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    covfile = output.with_name("GAIA_SHARED_FIELD_COVARIANCES.npz")
    np.savez_compressed(covfile, **arrays)
    report = {
        "schema": "htt.r99.shared_angular_field/1",
        "owner": "obsstat", "status": "MODEL_CONDITIONAL_COMPUTATION",
        "source_baseline": "eee33d7ed33e1af10d7c6a3c453810ecb227e461",
        "inputs": {
            str(source): {"sha256": sha256(source)},
            str(cache): {"sha256": actual_sha},
            "source_census_reused_from_R98": old["source_row_census"],
        },
        "source_rows_reread_this_run": 0,
        "actual_full_source_sufficient_statistics_used": True,
        "formula": "J_ap=F_a^-1 F_ap E; C_ab=s^2 J_a(K tensor I6)J_b^T",
        "component_order": ["glide_x","glide_y","glide_z","spin_x","spin_y","spin_z"],
        "patches": {"nside":2, "ordering":"RING", "count":48},
        "same_systematic_field_shared_by_all_fits": True,
        "constant_field_response_max_error": constant_error,
        "constant_field_contrast_response_max_error": float(coefficient_ref),
        "constant_field_contrast_covariance_max_abs": float(np.max(np.abs(constant_contrast))),
        "actual_rhs_refit_max_error_by_fit": refit_errors,
        "rank47_supported_and_unsupported_components": subspace,
        "scenarios": scenarios,
        "covariance_artifact": {"path":str(covfile), "sha256":sha256(covfile)},
        "limitations": [
            "Coarse piecewise 48-patch vector-field sensitivity, not fitted AGIS/AGN law.",
            "Amplitude belongs to six Cartesian glide/spin template coefficient fields.",
            "No joint covariance sum with spatial jackknife: unknown double counting.",
            "Small-angle and intra-patch correlations are unrepresented.",
            "No physical Pi, normal-frame vorticity or cosmological detection.",
            "Field amplitude matching a coefficient RMS is not a parameter estimate.",
        ],
        "physical_Pi": None,
        "environment": {"python":platform.python_version(),"numpy":np.__version__,
                        "platform":platform.platform()},
        "runtime_seconds": time.monotonic()-t0,
        "code_sha256": sha256(__file__),
    }
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)+"\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUT/"GAIA_SHARED_FIELD_RESULTS.json")
    args = parser.parse_args()
    result = run(args.output)
    print(json.dumps({"output":str(args.output),
                      "rhs_refit_max_error":max(result["actual_rhs_refit_max_error_by_fit"].values()),
                      "constant_contrast_response":result["constant_field_contrast_response_max_error"],
                      "subspace":result["rank47_supported_and_unsupported_components"],
                      "runtime_seconds":result["runtime_seconds"]}, indent=2))
