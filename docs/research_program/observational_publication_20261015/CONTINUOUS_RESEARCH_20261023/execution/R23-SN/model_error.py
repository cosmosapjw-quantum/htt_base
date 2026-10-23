"""Public MODEL000 SALT2 model-error fit for the frozen SN010010 rows.

This is a conditional source calculation. It cannot reconstruct the private
Pantheon+ nominal model or the unpublished PS1 FITRES record.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
from scipy.linalg import solve_triangular
from scipy.optimize import least_squares

HERE = Path(__file__).resolve().parent
OLD = HERE.parents[2] / "ADVERSARIAL_AUDIT_20261022/continuation/sn010010"
spec = importlib.util.spec_from_file_location("retained_sn010010_refit", OLD / "refit.py")
old = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = old
spec.loader.exec_module(old)
sncosmo = old.sncosmo


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def frozen_data():
    rows, _, published, _ = old.read_inputs()
    retained = json.loads((OLD / "RESULT.json").read_text())["baseline"]
    selected = retained["selected_rows"]
    assert len(selected) == 23 and len(rows) == 59
    kept = [rows[i] for i in selected]
    assert [r["row"] for r in kept] == selected
    times = np.array([r["mjd"] - old.CFG["T_ref_MJD"] for r in kept])
    bands = np.array([r["band"] for r in kept])
    y = np.array([r["flux"] for r in kept])
    err = np.array([r["error"] for r in kept])
    assert (err > 0).all()
    return times, bands, y, err, published, retained


def rest_bandpasses(exp, z):
    """Fold the same observer-frame MW extinction into rest-frame filters."""
    result = {}
    for name, b in exp.bands.items():
        wave = b["wave"]
        dx = wave[1] - wave[0]
        weights = np.full(len(wave), dx)
        weights[[0, -1]] *= .5
        trans = b["kernel"] / (wave * weights)
        attenuation = 10 ** (-.4 * old.extinction.fitzpatrick99(
            wave, old.CFG["MW"]["Rv"] * old.CFG["MW"]["raw_EBV"] * old.CFG["MW"]["scale"],
            old.CFG["MW"]["Rv"]))
        result[name] = sncosmo.Bandpass(wave / (1 + z), trans * attenuation, name="PS1-" + name + "-MW-rest")
    return result


def covariance(exp, theta, times, bands, errors, z, restbands):
    dt0, lnx0, x1, c = theta
    exp.source.set(x0=np.exp(lnx0), x1=x1, c=c)
    phase = (times - dt0) / (1 + z)
    assigned = np.array([restbands[name] for name in bands], dtype=object)
    rcov = exp.source.bandflux_rcov(assigned, phase)
    flux = exp.predict(theta, times, bands, z)
    modelcov = np.outer(flux, flux) * rcov
    total = np.diag(errors ** 2) + modelcov
    if not np.isfinite(total).all() or not np.allclose(total, total.T, atol=1e-9):
        raise ArithmeticError("invalid public model covariance")
    chol = np.linalg.cholesky(total)
    return flux, rcov, modelcov, total, chol


def fit_modelcov(exp, initial, times, bands, y, errors, z, restbands):
    """Iterated fixed-covariance chi-square fit; no variance tuning or clipping."""
    lower = np.array([-5., -30., -3., -.3])
    upper = np.array([5., 0., 3., .3])
    theta = initial.copy()
    iterations = []
    for iteration in range(16):
        _, _, _, _, chol = covariance(exp, theta, times, bands, errors, z, restbands)

        def residual(v):
            return solve_triangular(chol, exp.predict(v, times, bands, z) - y, lower=True)

        sol = least_squares(residual, theta, bounds=(lower, upper), x_scale="jac",
                            xtol=1e-11, ftol=1e-11, gtol=1e-10, max_nfev=300)
        if not sol.success or not np.isfinite(sol.x).all():
            raise ArithmeticError("public model-covariance fit failed")
        move = float(np.max(np.abs(sol.x - theta)))
        iterations.append({"iteration": iteration, "theta": sol.x.tolist(),
                           "fixed_cov_chi2": float(sol.fun @ sol.fun), "max_parameter_move": move})
        theta = sol.x
        if move < 2e-7:
            break
    else:
        raise ArithmeticError("public model-covariance iteration did not converge")
    flux, rcov, modelcov, total, chol = covariance(exp, theta, times, bands, errors, z, restbands)
    white = solve_triangular(chol, flux - y, lower=True)
    singular = np.linalg.svd(sol.jac / np.linalg.norm(sol.jac, axis=0), compute_uv=False)
    if (singular[-1] < singular[0] * 1e-10 or
            not np.all(theta > lower + 1e-7) or not np.all(theta < upper - 1e-7)):
        raise ArithmeticError("rank or fit bounds failed")
    return theta, rcov, modelcov, total, white, iterations, singular


def main():
    times, bands, y, errors, published, retained = frozen_data()
    exp = old.Experiment()
    z = old.CFG["zHEL"]
    restbands = rest_bandpasses(exp, z)
    old_theta = np.array(retained["theta"])
    original_chi2 = float(np.sum(((exp.predict(old_theta, times, bands, z) - y) / errors) ** 2))
    if abs(original_chi2 - retained["chi2"]) > 1e-6:
        raise ArithmeticError("retained original failure not reproduced at frozen theta")
    theta, rcov, mcov, cov, white, iterations, singular = fit_modelcov(
        exp, old_theta, times, bands, y, errors, z, restbands)
    chi2 = float(white @ white)
    par = np.array([float(published["PKMJD"]) - old.CFG["T_ref_MJD"],
                    np.log(float(published["x0"])), float(published["x1"]), float(published["c"])])
    defects = {"x0_relative": float(np.exp(theta[1] - par[1]) - 1),
               "x1": float(theta[2] - par[2]), "c": float(theta[3] - par[3]),
               "t0_day": float(theta[0] - par[0])}
    parity = all(abs(v) <= old.CFG["published_parity_tolerances"][k] for k, v in defects.items())
    result = {
        "task_id": "R23-SN", "owner": "htt", "claim_tier": "C0_PUBLIC_MODEL_CONDITIONAL_RESPONSE",
        "source": "released c447 MODEL000, sncosmo SALT2Source.bandflux_rcov, frozen original rows",
        "source_model_is_nominal_producer_model": "UNKNOWN",
        "original_baseline": {"chi2": retained["chi2"], "ndof": 19,
                              "reduced_chi2": retained["reduced_chi2"],
                              "adequacy": "BASELINE_ADEQUACY_HOLD", "threshold": 3},
        "public_modelcov_fit": {"theta": theta.tolist(), "chi2": chi2, "ndof": 19,
                                "reduced_chi2": chi2 / 19,
                                "conditional_screen": "PASS" if chi2 / 19 <= 3 else "HOLD",
                                "published_parity": "WITHIN_FROZEN_TOLERANCES" if parity else "NOT_REPRODUCED",
                                "published_defects": defects,
                                "scaled_jacobian_singular_values": singular.tolist(),
                                "iteration_trace": iterations},
        "covariance_diagnostics": {"model_diag_min": float(np.diag(mcov).min()),
                                   "model_diag_max": float(np.diag(mcov).max()),
                                   "total_eigen_min": float(np.linalg.eigvalsh(cov).min()),
                                   "relative_offdiag_max": float(np.max(np.abs(rcov - np.diag(np.diag(rcov))))),
                                   "retained_n": len(y)},
        "input_sha256": {"old_result": sha(OLD / "RESULT.json"), "old_config": sha(OLD / "CONFIG.json"),
                         "old_source_identities": sha(OLD / "SOURCE_IDENTITIES.json"),
                         "PPLUS.yml": sha(old.RAW / "7_PIPPIN/PPLUS.yml"),
                         "SALT2.INFO": sha(old.RAW / "3_SALT2/SALT2_B21trained_withsys/SALT2.MODEL000/SALT2.INFO")},
        "parity_source": "published Pantheon_SH0ES.dat summary; observed producer FITRES unavailable",
        "limitations": ["Public B21 MODEL000 identity is not the private FITMODEL_NAME binding in PPLUS.yml.",
                        "PS1.nml and observed PFITdatawithsys FITRES for CID 010010 are absent.",
                        "sncosmo relative model covariance is a supported public-source calculation, not a verified SNANA nominal likelihood.",
                        "INFO MAGERR_FLOOR, ERRMAP_KCOR_OPT, and any private cuts are not silently applied.",
                        "Original diagonal failure and threshold remain binding; no reboost or global response promoted."]}
    (HERE / "RESULT.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"original_chi2": original_chi2, "conditional_chi2": chi2,
                      "conditional_reduced_chi2": chi2 / 19, "published_parity": parity,
                      "iterations": len(iterations)}))


if __name__ == "__main__":
    main()
