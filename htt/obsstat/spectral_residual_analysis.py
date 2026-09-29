"""Covariance-aware, diagnostic-only CMB spectral residual analysis."""
from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import numpy as np


class SpectralContractError(ValueError):
    """Raised when arrays cannot be aligned without guessing a data law."""


@dataclass(frozen=True)
class Spectrum:
    dataset_id: str
    ell: np.ndarray
    values: np.ndarray
    spectrum: str
    quantity: str
    units: str
    error_lo: np.ndarray | None = None
    error_hi: np.ndarray | None = None
    covariance: np.ndarray | None = None
    window: np.ndarray | None = None
    overlap_family: str | None = None


def _vector(name: str, value: Any, *, length: int | None = None) -> np.ndarray:
    array = np.asarray(value, dtype=float)
    if array.ndim != 1 or (length is not None and len(array) != length):
        raise SpectralContractError(f"{name} must be a one-dimensional aligned vector")
    if not np.isfinite(array).all():
        raise SpectralContractError(f"{name} contains nonfinite values")
    return array


def validate_spectrum(item: Spectrum) -> Spectrum:
    ell = _vector("ell", item.ell)
    values = _vector("values", item.values, length=len(ell))
    if len(ell) == 0 or np.any(np.diff(ell) <= 0):
        raise SpectralContractError("ell must be non-empty and strictly increasing")
    if item.quantity not in {"Cl", "Dl"}:
        raise SpectralContractError("quantity must be exactly Cl or Dl")
    lo = _vector("error_lo", item.error_lo, length=len(ell)) if item.error_lo is not None else None
    hi = _vector("error_hi", item.error_hi, length=len(ell)) if item.error_hi is not None else None
    if (lo is None) != (hi is None) or (lo is not None and (np.any(lo <= 0) or np.any(hi <= 0))):
        raise SpectralContractError("asymmetric errors must be paired and strictly positive")
    covariance = None
    if item.covariance is not None:
        covariance = np.asarray(item.covariance, dtype=float)
        if covariance.shape != (len(ell), len(ell)) or not np.isfinite(covariance).all():
            raise SpectralContractError("covariance shape must match the selected spectral rows")
        if not np.allclose(covariance, covariance.T, rtol=1e-12, atol=1e-14):
            raise SpectralContractError("covariance must be symmetric")
        if np.linalg.eigvalsh(covariance).min(initial=0.0) < -1e-10 * max(1.0, np.max(np.abs(covariance))):
            raise SpectralContractError("covariance is not positive semidefinite")
    window = None
    if item.window is not None:
        window = np.asarray(item.window, dtype=float)
        if window.ndim != 2 or window.shape[0] != len(ell) or not np.isfinite(window).all():
            raise SpectralContractError("window rows must match observed bandpowers")
    return Spectrum(item.dataset_id, ell, values, item.spectrum, item.quantity, item.units,
                    lo, hi, covariance, window, item.overlap_family)


def cl_to_dl(ell: np.ndarray, values: np.ndarray, covariance: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray | None]:
    ell = _vector("ell", ell)
    values = _vector("values", values, length=len(ell))
    scale = ell * (ell + 1.0) / (2.0 * math.pi)
    transformed_covariance = None
    if covariance is not None:
        covariance = np.asarray(covariance, dtype=float)
        if covariance.shape != (len(ell), len(ell)):
            raise SpectralContractError("Cl covariance is not aligned with ell")
        transformed_covariance = scale[:, None] * covariance * scale[None, :]
    return scale * values, transformed_covariance


def project_window(window: np.ndarray, values: np.ndarray, covariance: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray | None]:
    window = np.asarray(window, dtype=float)
    values = _vector("window input", values)
    if window.ndim != 2 or window.shape[1] != len(values) or not np.isfinite(window).all():
        raise SpectralContractError("window columns must match the theory grid")
    projected_covariance = None
    if covariance is not None:
        covariance = np.asarray(covariance, dtype=float)
        if covariance.shape != (len(values), len(values)):
            raise SpectralContractError("window covariance is not aligned with theory grid")
        projected_covariance = window @ covariance @ window.T
    return window @ values, projected_covariance


def analyze_residuals(observed: Spectrum, theory_ell: Any, theory_values: Any, *, theory_quantity: str) -> dict[str, Any]:
    observed = validate_spectrum(observed)
    theory_ell = _vector("theory_ell", theory_ell)
    theory_values = _vector("theory_values", theory_values, length=len(theory_ell))
    if theory_quantity not in {"Cl", "Dl"}:
        raise SpectralContractError("theory quantity must be exactly Cl or Dl")
    if theory_quantity != observed.quantity:
        if theory_quantity == "Cl" and observed.quantity == "Dl":
            theory_values, _ = cl_to_dl(theory_ell, theory_values)
        else:
            scale = theory_ell * (theory_ell + 1.0) / (2.0 * math.pi)
            if np.any(scale == 0):
                raise SpectralContractError("cannot convert Dl to Cl at ell zero")
            theory_values = theory_values / scale
    if observed.window is not None:
        if observed.window.shape[1] != len(theory_values):
            raise SpectralContractError("window/theory length mismatch; refusing truncation")
        expected, _ = project_window(observed.window, theory_values)
    else:
        if observed.ell[0] < theory_ell[0] or observed.ell[-1] > theory_ell[-1]:
            raise SpectralContractError("theory grid does not cover observed ell range")
        expected = np.interp(observed.ell, theory_ell, theory_values)
    residual = observed.values - expected
    diagonal_proxy = None
    if observed.error_lo is not None:
        sigma = np.where(residual >= 0.0, observed.error_lo, observed.error_hi)
        diagonal_proxy = float(np.sum((residual / sigma) ** 2))
    full_quadratic = None
    covariance_rank = None
    if observed.covariance is not None:
        inverse = np.linalg.pinv(observed.covariance, hermitian=True)
        full_quadratic = float(residual @ inverse @ residual)
        covariance_rank = int(np.linalg.matrix_rank(observed.covariance))
    return {
        "schema": "htt.spectral_residual_analysis/v1",
        "dataset_id": observed.dataset_id,
        "spectrum": observed.spectrum,
        "quantity": observed.quantity,
        "units": observed.units,
        "ell": observed.ell.tolist(),
        "observed": observed.values.tolist(),
        "theory": expected.tolist(),
        "residual": residual.tolist(),
        "error_lo": observed.error_lo.tolist() if observed.error_lo is not None else None,
        "error_hi": observed.error_hi.tolist() if observed.error_hi is not None else None,
        "full_covariance_quadratic": full_quadratic,
        "covariance_rank": covariance_rank,
        "diagonal_error_quadratic_proxy": diagonal_proxy,
        "law_status": "FULL_COVARIANCE_DIAGNOSTIC" if full_quadratic is not None else "DIAGONAL_PROXY_ONLY",
        "p_value": None,
        "claim_ceiling": "diagnostic residuals only; no likelihood, p-value, or cross-survey stacking",
    }


def spectrum_from_npz(path: str | Path, *, dataset_id: str, metadata: Mapping[str, Any]) -> Spectrum:
    """Load only the common explicit spectrum schema; reject release containers."""
    with np.load(Path(path), allow_pickle=False) as arrays:
        keys = set(arrays.files)
        if not {"ell", "dl"}.issubset(keys):
            raise SpectralContractError("NPZ is not the explicit ell/dl spectrum schema")
        ell = arrays["ell"].copy()
        values = arrays["dl"].copy()
        lo = arrays["err_lo"].copy() if "err_lo" in keys else arrays["dl_err"].copy() if "dl_err" in keys else None
        hi = arrays["err_hi"].copy() if "err_hi" in keys else lo.copy() if lo is not None else None
        covariance = arrays["covariance"].copy() if "covariance" in keys else arrays["cov"].copy() if "cov" in keys else None
        window = arrays["window"].copy() if "window" in keys else None
    return validate_spectrum(Spectrum(
        dataset_id=dataset_id, ell=ell, values=values,
        spectrum=str(metadata.get("spectrum", "UNKNOWN")), quantity="Dl",
        units=str(metadata.get("unit", "UNAVAILABLE")), error_lo=lo, error_hi=hi,
        covariance=covariance, window=window,
        overlap_family=str(metadata["overlap_family"]) if metadata.get("overlap_family") else None,
    ))


def write_outputs(result: Mapping[str, Any], output_dir: str | Path) -> dict[str, str]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    stem = str(result["dataset_id"]).replace("/", "_").replace(".", "_")
    csv_path = output / f"{stem}_spectral_residuals.csv"
    json_path = output / f"{stem}_spectral_analysis.json"
    plot_path = output / f"{stem}_spectral_residuals.png"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["ell", "observed", "theory", "residual", "error_lo", "error_hi", "units"])
        for index, ell in enumerate(result["ell"]):
            writer.writerow([ell, result["observed"][index], result["theory"][index], result["residual"][index],
                             result["error_lo"][index] if result["error_lo"] else "",
                             result["error_hi"][index] if result["error_hi"] else "", result["units"]])
    json_path.write_text(json.dumps(dict(result), indent=2, allow_nan=False) + "\n", encoding="utf-8")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    figure, axis = plt.subplots(figsize=(7, 4))
    residual = np.asarray(result["residual"])
    if result["error_lo"] is not None:
        axis.errorbar(result["ell"], residual, yerr=np.vstack([result["error_lo"], result["error_hi"]]), fmt=".", capsize=2)
    else:
        axis.plot(result["ell"], residual, ".")
    axis.axhline(0.0, color="black", linewidth=0.8)
    axis.set(xlabel="ell", ylabel=f"observed - reference [{result['units']}]", title=str(result["dataset_id"]))
    figure.tight_layout()
    figure.savefig(plot_path, dpi=140)
    plt.close(figure)
    return {"csv": str(csv_path), "json": str(json_path), "plot": str(plot_path)}
