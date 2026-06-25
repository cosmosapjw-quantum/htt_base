"""EGS3 B3: vorticity re-opening complement (closes the NT2-B3 'to close').

NT2-B3 proved the vorticity term is a JOINT blind sector of {CMB-temperature,
radial peculiar velocity}: radial projection n^a Omega_ab n^b = 0 exactly, and
CMB-T is blind to the curl/Weyl sector at EGS order. The natural next question
('to close') is WHICH additional channel re-opens it. This module answers it
constructively:

  * TRANSVERSE (tangential) peculiar velocities: for an antisymmetric Omega and a
    transverse direction m perpendicular to the line of sight n, the response
    n^a Omega_ab m^b = (omega x n) . m is generically NONZERO -- the transverse
    velocity channel carries vorticity that the radial channel cannot.
  * CMB POLARIZATION B-modes couple to the magnetic Weyl tensor, re-opening the
    sector the temperature channel misses (registered here as a named channel;
    the quantitative transfer is the B1 semi-native calculator's remit).

So the no-go is exactly two channels wide, and these are the two that break it.
Algebraic check only; diagnostic-only; no detection.
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np


def antisymmetric_from_axial(omega: np.ndarray) -> np.ndarray:
    """Omega_ab with Omega_ab v^b = omega x v (axial vector -> antisymmetric)."""
    o = np.asarray(omega, dtype=float).reshape(3)
    return np.array([[0.0, -o[2], o[1]], [o[2], 0.0, -o[0]], [-o[1], o[0], 0.0]])


def radial_response(omega: np.ndarray, n_hat: np.ndarray) -> float:
    """n^a Omega_ab n^b -- identically 0 (radial no-go)."""
    Om = antisymmetric_from_axial(omega)
    n = np.asarray(n_hat, dtype=float)
    return float(n @ Om @ n)


def transverse_response(omega: np.ndarray, n_hat: np.ndarray, m_hat: np.ndarray) -> float:
    """n^a Omega_ab m^b = (omega x n) . m -- generically nonzero for m _|_ n."""
    Om = antisymmetric_from_axial(omega)
    n = np.asarray(n_hat, dtype=float)
    m = np.asarray(m_hat, dtype=float)
    return float(n @ Om @ m)


@dataclass(frozen=True)
class ReopenResult:
    radial_max_abs: float
    transverse_max_abs: float
    transverse_design_rank: int
    reopens: bool
    n_configs: int


def vorticity_reopening(n_configs: int = 500, seed: int = 91) -> ReopenResult:
    """Radial channel is identically blind; the transverse channel re-opens the
    vorticity sector (nonzero response, rank-3 design over the 3 curl modes)."""
    rng = np.random.default_rng(seed)
    radial_max = 0.0
    transverse_max = 0.0
    # transverse design: response of the 3 axial modes at random (n, m) pairs.
    rows = []
    for _ in range(n_configs):
        n = rng.normal(size=3); n /= np.linalg.norm(n)
        t = rng.normal(size=3); t -= (t @ n) * n; m = t / np.linalg.norm(t)   # m _|_ n
        omega = rng.normal(size=3)
        radial_max = max(radial_max, abs(radial_response(omega, n)))
        transverse_max = max(transverse_max, abs(transverse_response(omega, n, m)))
        rows.append([transverse_response(e, n, m) for e in np.eye(3)])
    rank = int(np.linalg.matrix_rank(np.array(rows), tol=1e-9))
    return ReopenResult(radial_max, transverse_max, rank,
                        reopens=bool(radial_max < 1e-12 and transverse_max > 1e-3 and rank == 3),
                        n_configs=int(n_configs))
