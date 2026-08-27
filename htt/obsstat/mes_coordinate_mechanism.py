"""Exact scalar MES coordinate mechanism for the frozen 301-row pool."""

from __future__ import annotations

import math
from typing import Mapping

import numpy as np

from htt.core.ssot import C


FACTORIAL_CELL_IDS = (
    "EPS_LINEAR",
    "SQUARE_ONLY",
    "CARRIER_ONLY",
    "MES_SQUARED",
)


def epsilon_from_cl(cl_values: object, ell: int) -> np.ndarray:
    values = np.asarray(cl_values, dtype=float)
    if ell not in (2, 3) or values.ndim != 1 or np.any(~np.isfinite(values)) or np.any(values < 0.0):
        raise ValueError("C_l values and ell must define finite nonnegative l=2/3 amplitudes")
    return np.sqrt((2 * ell + 1) * values / (4.0 * math.pi)) / C.T0_uK


def mes_carriers(
    epsilon2: object,
    epsilon3: object,
    *,
    epsilon1: float,
) -> tuple[np.ndarray, np.ndarray]:
    eps2 = np.asarray(epsilon2, dtype=float)
    eps3 = np.asarray(epsilon3, dtype=float)
    if eps2.shape != eps3.shape or eps2.ndim != 1 or np.any(~np.isfinite(eps2)) or np.any(~np.isfinite(eps3)) or np.any(eps2 < 0.0) or np.any(eps3 < 0.0):
        raise ValueError("epsilon2 and epsilon3 must be aligned nonnegative vectors")
    if isinstance(epsilon1, bool) or not np.isfinite(epsilon1) or epsilon1 < 0.0:
        raise ValueError("epsilon1 must be a finite nonnegative premise")
    return (
        (5.0 / 3.0) * epsilon1 + 3.0 * eps2 + (3.0 / 7.0) * eps3,
        (10.0 / 3.0) * epsilon1 + (2.0 / 15.0) * eps2,
    )


def mes_coordinate_forward(
    epsilon2: object,
    epsilon3: object,
    *,
    epsilon1: float,
) -> tuple[np.ndarray, np.ndarray]:
    sigma, omega = mes_carriers(epsilon2, epsilon3, epsilon1=epsilon1)
    return 1.5 * sigma**2, 1.5 * omega**2


def mes_coordinate_inverse(
    sigma2_max: object,
    w2_max: object,
) -> tuple[np.ndarray, np.ndarray]:
    sigma = np.asarray(sigma2_max, dtype=float)
    omega = np.asarray(w2_max, dtype=float)
    if sigma.shape != omega.shape or sigma.ndim != 1 or np.any(~np.isfinite(sigma)) or np.any(~np.isfinite(omega)) or np.any(sigma < 0.0) or np.any(omega < 0.0):
        raise ValueError("squared MES coordinates must be aligned nonnegative vectors")
    epsilon2 = np.sqrt((75.0 / 2.0) * omega)
    epsilon3 = np.sqrt((98.0 / 27.0) * sigma) - 7.0 * epsilon2
    if np.any(epsilon3 < -1e-18):
        raise ValueError("squared MES coordinates lie outside the nonnegative inverse domain")
    return epsilon2, np.maximum(epsilon3, 0.0)


def factorial_coordinate_cells(source_rows: object) -> Mapping[str, np.ndarray]:
    rows = np.asarray(source_rows, dtype=float)
    if rows.shape[1:] != (12,) or rows.ndim != 2 or np.any(~np.isfinite(rows)):
        raise ValueError("source rows must be a finite N by 12 feature pool")
    eps2 = epsilon_from_cl(rows[:, 0], 2)
    eps3 = epsilon_from_cl(rows[:, 1], 3)
    carrier_sigma, carrier_omega = mes_carriers(eps2, eps3, epsilon1=0.0)
    morphology = rows[:, 4:]
    return {
        "EPS_LINEAR": np.column_stack((eps2, eps3, morphology)),
        "SQUARE_ONLY": np.column_stack((eps2**2, eps3**2, morphology)),
        "CARRIER_ONLY": np.column_stack((carrier_sigma, carrier_omega, morphology)),
        "MES_SQUARED": np.column_stack((1.5 * carrier_sigma**2, 1.5 * carrier_omega**2, morphology)),
    }


def epsilon1_grid() -> np.ndarray:
    return np.linspace(0.0, 1.0e-5, 101)


__all__ = [
    "FACTORIAL_CELL_IDS",
    "epsilon1_grid",
    "epsilon_from_cl",
    "factorial_coordinate_cells",
    "mes_carriers",
    "mes_coordinate_forward",
    "mes_coordinate_inverse",
]
