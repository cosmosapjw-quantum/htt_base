"""VER2 Weyl/Bianchi diagnostic hooks for the BASS S1 lane."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from bass.background.constraints import BackgroundConstraintResiduals
from bass.background.geometry import TetradGeometry, curl_pstf2, pstf_rank2

__all__ = [
    "WeylDiagnostics",
    "magnetic_weyl_from_curl_sigma",
    "electric_weyl_from_shear_rhs",
    "build_weyl_diagnostics",
]


@dataclass(frozen=True)
class WeylDiagnostics:
    """Diagnostic Weyl block for one homogeneous background state."""

    electric: np.ndarray
    magnetic: np.ndarray
    bianchi_identity_residual: np.ndarray


def magnetic_weyl_from_curl_sigma(
    sigma_ab: np.ndarray,
    geometry: TetradGeometry,
) -> np.ndarray:
    """`H^Weyl_ab = curl(sigma)_ab` in the VER2 homogeneous background."""
    sigma = pstf_rank2(sigma_ab)
    return curl_pstf2(sigma, geometry.Gamma)


def electric_weyl_from_shear_rhs(
    *,
    sigma_ab: np.ndarray,
    sigma_dot_ab: np.ndarray,
    H: float,
    pi_ab: np.ndarray | None = None,
    kappa: float = 1.0,
) -> np.ndarray:
    """Diagnostic electric Weyl tensor from the shear propagation identity."""
    sigma = pstf_rank2(sigma_ab)
    sigma_dot = pstf_rank2(sigma_dot_ab)
    pi = np.zeros((3, 3), dtype=np.float64) if pi_ab is None else pstf_rank2(pi_ab)
    quadratic = pstf_rank2(sigma @ sigma)
    return pstf_rank2(-sigma_dot - 2.0 * float(H) * sigma - quadratic + 0.5 * kappa * pi)


def build_weyl_diagnostics(
    *,
    sigma_ab: np.ndarray,
    sigma_dot_ab: np.ndarray,
    H: float,
    geometry: TetradGeometry,
    residuals: BackgroundConstraintResiduals,
    pi_ab: np.ndarray | None = None,
    kappa: float = 1.0,
) -> WeylDiagnostics:
    """Bundle Weyl diagnostics with the current Bianchi-identity hook."""
    return WeylDiagnostics(
        electric=electric_weyl_from_shear_rhs(
            sigma_ab=sigma_ab,
            sigma_dot_ab=sigma_dot_ab,
            H=H,
            pi_ab=pi_ab,
            kappa=kappa,
        ),
        magnetic=magnetic_weyl_from_curl_sigma(sigma_ab, geometry),
        bianchi_identity_residual=residuals.twice_contracted_bianchi,
    )
