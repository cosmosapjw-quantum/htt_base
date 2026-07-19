"""EGS3 A1 (flagship): graded-comparator identifiability rank theorem.

Framework upgrade. The report's signed scalar comparator
``x_C = Sigma^2 - W^2 + Omega_tilt + Omega_k`` contracts four physically
distinct invariants into one number, so a large shear and a large vorticity can
cancel (`Sigma^2 - W^2 ~ 0`) while the scalar is small. No FLRW or almost-EGS
inference follows. We promote the primary
object to the GRADED COMPARATOR VECTOR

    g = (Sigma^2, W^2, Omega_tilt, Omega_k) in R^4 ,   x_C = <c, g>,  c=(+1,-1,+1,+1),

so x_C is a derived linear summary and the sector identity is preserved.

A1 theorem (within the registered leading-channel response map). From the two
channels the program actually uses --- low-l CMB temperature and radial peculiar
velocity --- the data-identifiable subspace of g is exactly RANK 2: Sigma^2 (via
the CMB quadrupole, NT-A1) and Omega_tilt (via the CMB/velocity dipole). The
vorticity V^2 (legacy repository label W^2) and the anisotropic-curvature
Omega_k both have a zero response
column and so the rank count is 2 --- but they are NOT the same KIND of null
(the rank count alone cannot distinguish a genuine null from a Sigma^2-collinear
degeneracy; see `NULL_SECTOR_KIND` / `describe_null_sectors`):
  * V^2/W^2 is a structural null of the DECLARED leading-order response map:
    the registered CMB-temperature support column is zero at this order, and
    radial peculiar velocities carry no vorticity because
    n^a Omega_ab n^b = 0 exactly (PAPER-A A-radial-novortex). Transverse
    velocities re-open the radial projection. No all-order CMB-temperature or
    magnetic-Weyl equivalence is asserted; a full vorticity-specific transfer
    must be recalculated separately.
  * Omega_k is a LEADING-EGS-ORDER no-channel: no registered low-l channel sources
    the anisotropic spatial-curvature scalar at leading order. This is
    truncation-dependent and RE-OPENS beyond leading order (higher-order ISW,
    lensing, the native low-l Bianchi transfer) within the SAME channels.
Hence x_C's sign-cancellation is a projection artifact: it mixes a reachable
(Sigma^2) and an unreachable (W^2) sector into one coordinate. This unifies
NT2-B3 (blind sector) and PAPER-A (rank) on the redesigned variable.

Diagnostic-only / conditional structural theorem; no detection, no family ID.
The response design encodes the leading-EGS-order channel sensitivities as a
documented {0,1} support pattern; the *rank/null structure* is the robust
content, exact response amplitudes need the covariant transfer (EGS3-B1).
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np

SECTORS = ("Sigma2", "W2", "Omega_tilt", "Omega_k")
NONNEGATIVE_SECTORS = ("Sigma2", "W2", "Omega_tilt")   # x_C summary sign vector
COMPARATOR_SIGNS = np.array([+1.0, -1.0, +1.0, +1.0])   # c: x_C = c . g

# Channel-observable rows; columns are (Sigma2, W2, Omega_tilt, Omega_k).
# 1 = the channel observable responds to that sector at leading EGS order; 0 =
# zero in the declared response map (radial no-go / registered leading-order
# CMB-temperature support / no low-l curvature source).
CHANNELS = ("cmb_quadrupole", "cmb_dipole", "radial_velocity_dipole")
_RESPONSE_SUPPORT = {
    "cmb_quadrupole":        (1.0, 0.0, 0.0, 0.0),   # shear sources C2 (NT-A1)
    "cmb_dipole":            (0.0, 0.0, 1.0, 0.0),   # tilt rapidity -> dipole
    "radial_velocity_dipole":(0.0, 0.0, 1.0, 0.0),   # bulk flow = tilt; no curl
}

# The two null sectors are NOT the same KIND of null (audit FM2 / external review).
# Both give a zero response column and the SAME rank-2 count, but the rank count
# ALONE cannot characterise them -- a leading-order zero column is indistinguishable
# by rank from a genuine null or a Sigma2-collinear degeneracy. This annotation
# records which holds:
#   * W2  -- a structural null of THIS registered leading-order map. Radial
#            peculiar velocities satisfy n.Omega.n == 0 exactly; the declared
#            CMB-temperature column is zero at this order. No all-order or
#            magnetic-Weyl claim is made. Transverse velocities re-open the
#            radial projection; a full transfer requires separate calculation.
#   * Omega_k -- a LEADING-EGS-ORDER no-channel. No registered low-l channel sources
#            the anisotropic spatial-curvature scalar AT LEADING ORDER; this is
#            truncation-dependent and RE-OPENS beyond leading order (higher-order ISW,
#            lensing, the full native low-l Bianchi transfer) within the SAME channels.
NULL_SECTOR_KIND = {
    "W2": {
        "kind": "structural_null",
        "scope": "registered_leading_egs_response_map_only",
        "order_dependence": "not_claimed_beyond_registered_map",
        "reason": "radial n.Omega.n=0 exactly + registered leading-order CMB-temperature response column zero",
        "reopens_via": ("transverse_peculiar_velocity", "full_vorticity_specific_transfer"),
    },
    "Omega_k": {
        "kind": "no_channel_leading_order",
        "order_dependence": "leading_egs_order_only",
        "reason": "no leading-EGS-order low-l channel sources the anisotropic-curvature scalar",
        "reopens_via": ("higher_order_isw", "lensing", "native_low_ell_transfer"),
    },
}


@dataclass(frozen=True)
class GradedComparator:
    g: np.ndarray            # (Sigma2, W2, Omega_tilt, Omega_k)
    x_C: float               # derived linear summary c . g
    sector_filling: dict     # per-nonnegative-sector fraction of x_max

    def as_dict(self) -> dict:
        return {"sectors": list(SECTORS), "g": self.g.tolist(), "x_C": self.x_C,
                "sector_filling": self.sector_filling}


def graded_comparator(sigma2: float, w2: float, omega_tilt: float, omega_k: float,
                      x_max: float = 9.25e-6) -> GradedComparator:
    """Build the graded comparator vector and its derived signed summary x_C.

    Per-sector filling is defined only on the nonnegative sectors (so it never
    inherits the sign-cancellation pathology of F = x_C/x_max)."""
    g = np.array([float(sigma2), float(w2), float(omega_tilt), float(omega_k)], dtype=float)
    if np.any(g[[0, 1, 2]] < 0.0):
        raise ValueError("Sigma2, W2, Omega_tilt must be nonnegative")
    if x_max <= 0.0:
        raise ValueError("x_max must be positive")
    x_c = float(COMPARATOR_SIGNS @ g)
    filling = {SECTORS[i]: float(g[i] / x_max) for i in (0, 1, 2)}
    return GradedComparator(g=g, x_C=x_c, sector_filling=filling)


def channel_response_design(channels: tuple[str, ...] = CHANNELS) -> np.ndarray:
    """Stacked leading-EGS-order response design D (n_obs x 4) for g."""
    return np.array([_RESPONSE_SUPPORT[c] for c in channels], dtype=float)


@dataclass(frozen=True)
class IdentifiabilityRank:
    rank: int
    reachable_sectors: tuple[str, ...]
    null_sectors: tuple[str, ...]
    design_shape: tuple[int, int]


def identifiable_rank(design: np.ndarray | None = None, *, tol: float = 1e-12) -> IdentifiabilityRank:
    """A1: the identifiable subspace of g is the column space of the stacked
    channel response; report its rank and which sectors are reachable vs in the
    joint null."""
    d = channel_response_design() if design is None else np.asarray(design, dtype=float)
    s = np.linalg.svd(d, compute_uv=False)
    rank = int(np.sum(s > tol * (s[0] if s.size else 1.0)))
    col_norms = np.linalg.norm(d, axis=0)
    reachable = tuple(SECTORS[i] for i in range(4) if col_norms[i] > tol)
    null = tuple(SECTORS[i] for i in range(4) if col_norms[i] <= tol)
    return IdentifiabilityRank(rank=rank, reachable_sectors=reachable,
                               null_sectors=null, design_shape=d.shape)


def describe_null_sectors(null_sectors: tuple[str, ...] | None = None) -> dict:
    """Per-sector null KIND for the identifiability null (audit FM2).

    Distinguishes the structural zero column for V2/W2 in the registered
    leading-order response map from the leading-EGS-order no-channel
    (Omega_k). The two are NOT the same null even though both produce a zero
    response column and the same rank-2 count. No order-independent or Weyl
    statement is inferred for V2/W2: transverse velocities or a separately
    derived full vorticity transfer can re-open it. Omega_k instead re-opens
    within the same channels beyond leading EGS order (higher-order ISW,
    lensing, the native low-l transfer). Returns the
    `NULL_SECTOR_KIND` record for each null sector that carries one."""
    if null_sectors is None:
        null_sectors = identifiable_rank().null_sectors
    return {s: NULL_SECTOR_KIND[s] for s in null_sectors if s in NULL_SECTOR_KIND}
