"""Finite, selected-pixel Planck harmonic response. No physical EGS map."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.linalg import qr, solve_triangular, lstsq


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def fit_response(design: np.ndarray, selected: np.ndarray, fit_lmax: int = 5):
    """QR OLS on W=1 selected pixels, W=0 elsewhere; high ell 6..16.

    ``design`` has real harmonics ell 0..16 in ell,m0,cos,sin order.
    The 253 high columns always refer to ell 6..16, even if the fitted
    subspace extends into that range; included columns then have zero leakage.
    """
    y = np.asarray(design, dtype=np.float64)
    support = np.asarray(selected, dtype=bool)
    nfit = (fit_lmax + 1) ** 2
    if (y.ndim != 2 or y.shape[1] != 289 or support.shape != (len(y),)
            or fit_lmax not in (5, 8, 12) or support.sum() < nfit
            or not np.isfinite(y[support]).all()):
        raise ValueError("finite full ell0..16 design and supported fit required")
    low = y[support, :nfit]
    high = y[support, 36:289]
    q, r = qr(low, mode="economic", check_finite=False)
    singular_low = np.linalg.svd(r, compute_uv=False)
    condition = float(singular_low[0] / singular_low[-1])
    if singular_low[-1] <= 0 or condition > 1e6:
        raise ValueError("low harmonic fit rank/conditioning gate failed")
    # A_L Y_H = R^-1 Q^T Y_H; never materialize the pixel projector A_L.
    k = solve_triangular(r, q.T @ high, check_finite=False)
    identity = solve_triangular(r, q.T @ low, check_finite=False)
    residual = float(np.max(np.abs(identity - np.eye(nfit))))
    if residual > 1e-10 or not np.isfinite(k).all():
        raise ValueError("low harmonic identity or response nonfinite")
    return {"K_full_fit": k, "K_ell23": k[4:16], "K_ell2to5": k[4:36],
            "Q": q, "R": r, "low_design": low, "high_design": high,
            "condition": condition, "rank_low": nfit, "identity_residual": residual,
            "n_selected": int(support.sum()), "fit_lmax": fit_lmax}


def fit_vector(response: dict, pixel_values: np.ndarray) -> np.ndarray:
    values = np.asarray(pixel_values, dtype=np.float64)
    if values.shape != (response["n_selected"],) or not np.isfinite(values).all():
        raise ValueError("one finite selected-pixel vector required")
    return solve_triangular(response["R"], response["Q"].T @ values,
                            check_finite=False)


def spectrum(k: np.ndarray) -> dict:
    s = np.linalg.svd(k, compute_uv=False)
    rank = int(np.linalg.matrix_rank(k))
    return {"shape": list(k.shape), "operator_norm": float(s[0]),
            "frobenius_norm": float(np.linalg.norm(k)), "rank": rank,
            "singular_values": s.tolist(),
            "condition_nonzero": float(s[0] / s[rank - 1]) if rank else None}


def per_shell(k: np.ndarray) -> list[dict]:
    rows = []
    for ell in range(6, 17):
        start, stop = ell * ell - 36, (ell + 1) ** 2 - 36
        block = k[:, start:stop]
        rows.append({"ell": ell, "columns": [start, stop],
                     "operator_norm": float(np.linalg.norm(block, 2)),
                     "frobenius_norm": float(np.linalg.norm(block))})
    return rows


def injection_checks(response: dict, seed: int = 164303) -> dict:
    low = response["low_design"]
    high = response["high_design"]
    k = response["K_full_fit"]
    nfit = low.shape[1]
    eye = np.eye(nfit)
    low_error = max(float(np.max(np.abs(fit_vector(response, low[:, j]) - eye[:, j])))
                    for j in range(nfit))
    # Independent LAPACK least squares checks a few individual high modes.
    columns = [0, 6, 20, 100, 252]
    unit_error = max(float(np.max(np.abs(lstsq(low, high[:, j],
                                                check_finite=False)[0] - k[:, j])))
                     for j in columns)
    rng = np.random.default_rng(seed)
    a_low = rng.normal(size=nfit)
    a_high = rng.normal(size=253)
    direct = fit_vector(response, low @ a_low + high @ a_high)
    predicted = a_low + k @ a_high
    random_error = float(np.max(np.abs(direct - predicted)))
    leakage = direct - a_low
    high_norm = float(np.linalg.norm(a_high))
    leakage_norm = float(np.linalg.norm(leakage))
    bound = float(np.linalg.norm(k, 2) * high_norm)
    if low_error > 1e-10 or unit_error > 1e-10 or random_error > 1e-10:
        raise ValueError("finite harmonic injection identity failed")
    if leakage_norm > bound * (1 + 1e-12):
        raise ValueError("finite response norm inequality failed")
    return {"seed": seed, "low_unit_max_error": low_error,
            "high_unit_max_error": unit_error, "random_superposition_max_error": random_error,
            "random_high_norm": high_norm, "random_leakage_norm": leakage_norm,
            "random_bound": bound, "bound_holds": True}


def source_result(response: dict, observed_selected: np.ndarray,
                  reference_retained: np.ndarray) -> dict:
    fitted = fit_vector(response, observed_selected)
    reference = np.asarray(reference_retained, dtype=np.float64)
    if reference.shape != (32,):
        raise ValueError("Loop5 retained 32 coefficient reference required")
    delta = fitted[4:36] - reference
    maximum = float(np.max(np.abs(delta)))
    if maximum > 1e-8:
        raise ValueError(f"same-source Loop5 regression failed: {maximum}")
    return {"fitted_ell0_to5_microK": fitted.tolist(),
            "loop5_retained_max_abs_delta_microK": maximum,
            "selected_map_residual_rms_microK": float(np.linalg.norm(
                observed_selected - response["low_design"] @ fitted)
                / np.sqrt(response["n_selected"]))}


def json_dump_create(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(payload, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
