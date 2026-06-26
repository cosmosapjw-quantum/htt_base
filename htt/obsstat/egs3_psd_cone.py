"""EGS3 revisionary redesign: the PSD-cone-valued sector comparator.

The graded upgrade (`egs3_graded_comparator`) already cured the signed scalar
``x_C = Sigma^2 - W^2 + Omega_tilt + Omega_k`` by exposing the four sectors
individually as a vector ``g``. This module takes the next, structural step
registered in the EGS3 plan (Part 1, revisionary redesign): the primary
diagnostic object becomes a real symmetric **PSD matrix comparator** ``M >= 0``
whose labelled spectrum (the diagonal in the sector eigenbasis) ARE the four
sector invariants.  A single object then unifies what were four separate
statements:

  * x_C as a functional of M          --  x_C = tr(C M),  C = diag(+1,-1,+1,+1)
  * admissible set                    --  the PSD cone (PAPER-B B-psd moment cone)
  * identifiability (A1 / NT2-B3)     --  reachable EIGENDIRECTIONS of M; the
                                          blind sector {W^2, Omega_k} is the
                                          structural NULL (kernel) of the
                                          measurement map M |-> P_R M P_R
  * two-sided bracket (NT2-B1)        --  membership in a convex cone-SHELL
                                          {M >= 0 : s_lo < lambda_Sigma(M) < s_hi},
                                          which excludes the FLRW vertex
                                          (lambda_Sigma = 0).

This is a *representation* change only.  It ships behind the additive graded
upgrade and is GATED by a bit-identical regression: ``xc_from_matrix`` must
reproduce the graded ``x_C`` exactly (`tests/contracts/test_psd_cone_redesign`,
`research_gates/egs3/tests/test_egs3_axis_psd`).  No detection, no family/
geometry, no native-solver claim; the claim envelope is unchanged.

The construction is diagonal in the sector eigenbasis (the sectors are
*labelled* eigen-invariants, no cross-sector correlation is asserted); that is
the conservative special case of the general PSD comparator and is exactly what
makes the spectrum equal to ``g`` and the trace identity exact.  Off-diagonal
(cross-sector) structure is a strict superset reserved for the native solver and
is NOT used here.
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np

from htt.obsstat.egs3_graded_comparator import (
    SECTORS, COMPARATOR_SIGNS, channel_response_design,
)

# Signature operator C: x_C = tr(C M).  Diagonal because M is diagonal in the
# sector eigenbasis, so tr(C M) = sum_i c_i M_ii = <c, g>.
SECTOR_SIGNATURE = np.diag(COMPARATOR_SIGNS)


def sector_matrix(g: np.ndarray | tuple[float, float, float, float]) -> np.ndarray:
    """Embed the graded sector vector g as the 4x4 labelled-eigenbasis comparator
    M = diag(Sigma^2, W^2, Omega_tilt, Omega_k).  The sectors are the spectrum."""
    g = np.asarray(g, dtype=float)
    if g.shape != (4,):
        raise ValueError("g must have shape (4,) = (Sigma2, W2, Omega_tilt, Omega_k)")
    return np.diag(g)


def sectors_from_matrix(M: np.ndarray) -> np.ndarray:
    """Recover the labelled sector invariants g (the diagonal/spectrum of M)."""
    M = np.asarray(M, dtype=float)
    return np.diag(M).copy()


def xc_from_matrix(M: np.ndarray) -> float:
    """x_C as a functional of the comparator: x_C = tr(C M).

    Bit-identical to the graded summary <c, g> because M is diagonal in the
    sector eigenbasis (gated by the EGS3 PSD contract)."""
    M = np.asarray(M, dtype=float)
    return float(np.trace(SECTOR_SIGNATURE @ M))


@dataclass(frozen=True)
class Admissibility:
    is_admissible: bool
    min_eigenvalue: float
    negative_sectors: tuple[str, ...]


def admissibility(M: np.ndarray, *, tol: float = 1e-15) -> Admissibility:
    """PAPER-B moment-cone membership: M is an admissible departure second-moment
    iff M >= 0 (PSD).  Fail-closed: any negative labelled invariant ejects M from
    the cone.  This is the structural admissible set the redesign replaces the
    ad-hoc x_max ceiling with."""
    M = np.asarray(M, dtype=float)
    evals = np.linalg.eigvalsh(0.5 * (M + M.T))
    lam_min = float(evals.min())
    diag = np.diag(M)
    neg = tuple(SECTORS[i] for i in range(4) if diag[i] < -tol)
    return Admissibility(is_admissible=lam_min >= -tol,
                         min_eigenvalue=lam_min, negative_sectors=neg)


def reachable_projector(*, tol: float = 1e-12) -> np.ndarray:
    """Orthogonal projector P_R onto the reachable eigendirections, i.e. the
    column space of the leading-EGS-order channel response design.  In the sector
    eigenbasis this is diag over {Sigma2, Omega_tilt}."""
    d = channel_response_design()
    # column space of d^T (sectors that any channel reaches)
    u, s, _ = np.linalg.svd(d.T, full_matrices=True)
    r = int(np.sum(s > tol * (s[0] if s.size else 1.0)))
    basis = u[:, :r]
    return basis @ basis.T


@dataclass(frozen=True)
class EigenIdentifiability:
    reachable_rank: int
    reachable_sectors: tuple[str, ...]
    null_sectors: tuple[str, ...]
    null_residual: float          # ||(I-P_R) M restricted to recovered|| -> 0
    reachable_recovers_sectors: bool


def eigen_identifiability(M: np.ndarray, *, tol: float = 1e-12) -> EigenIdentifiability:
    """A1 / NT2-B3 as one eigendirection statement.  The measurement map sends
    M |-> P_R M P_R; the reachable sectors are the eigendirections P_R keeps and
    the blind sector is the structural NULL (the W^2, Omega_k eigenvectors are in
    ker P_R, so their invariants are annihilated)."""
    M = np.asarray(M, dtype=float)
    P = reachable_projector(tol=tol)
    diagP = np.diag(P)
    reachable = tuple(SECTORS[i] for i in range(4) if diagP[i] > 0.5)
    null = tuple(SECTORS[i] for i in range(4) if diagP[i] <= 0.5)
    # measured comparator keeps reachable invariants, annihilates the null ones
    M_meas = P @ M @ P
    g = np.diag(M)
    g_meas = np.diag(M_meas)
    reach_idx = [i for i in range(4) if diagP[i] > 0.5]
    null_idx = [i for i in range(4) if diagP[i] <= 0.5]
    recovers = bool(np.allclose([g_meas[i] for i in reach_idx],
                                [g[i] for i in reach_idx], atol=1e-12))
    null_resid = float(np.linalg.norm([g_meas[i] for i in null_idx]))
    return EigenIdentifiability(reachable_rank=len(reachable),
                                reachable_sectors=reachable, null_sectors=null,
                                null_residual=null_resid,
                                reachable_recovers_sectors=recovers)


@dataclass(frozen=True)
class ConeShell:
    lambda_sigma: float
    s_lo: float
    s_hi: float
    in_shell: bool
    excludes_vertex: bool      # s_lo > 0 -> the FLRW shear-free vertex is excluded


def cone_shell_membership(M: np.ndarray, s_lo: float, s_hi: float) -> ConeShell:
    """NT2-B1 as convex cone-shell membership.  The shear eigenvalue
    lambda_Sigma = e_Sigma^T M e_Sigma must satisfy s_lo < lambda_Sigma < s_hi
    with s_lo > 0, i.e. M lies in the convex slice
    {M >= 0} intersect {lambda_Sigma > s_lo} intersect {lambda_Sigma < s_hi},
    which excludes the shear-free vertex (lambda_Sigma = 0)."""
    M = np.asarray(M, dtype=float)
    if s_lo > s_hi:
        raise ValueError("s_lo must not exceed s_hi")
    lam = float(M[0, 0])                       # Sigma^2 eigenvalue
    return ConeShell(lambda_sigma=lam, s_lo=float(s_lo), s_hi=float(s_hi),
                     in_shell=(s_lo < lam < s_hi), excludes_vertex=(s_lo > 0.0))


def bracket_shell_from_a2a3(a2: float, a3: float) -> tuple[float, float]:
    """Lower/upper shear-eigenvalue bracket from the observed quadrupole+octupole,
    via the NT2-B1 covariant two-sided bracket (egs2_shear_bracket)."""
    from htt.obsstat.egs2_shear_bracket import shear_lower, shear_upper
    return float(shear_lower(a2, a3)), float(shear_upper(a2))


def convex_combination_is_admissible(M1: np.ndarray, M2: np.ndarray,
                                     t: float = 0.5) -> bool:
    """The admissible set is a convex cone: if M1, M2 >= 0 then t M1 + (1-t) M2 >= 0
    for t in [0,1].  (Used by the gate to witness convexity of the redesign's
    admissible set, the property the scalar x_max ceiling lacked.)"""
    if not 0.0 <= t <= 1.0:
        raise ValueError("t must be in [0, 1]")
    Mc = t * np.asarray(M1, float) + (1.0 - t) * np.asarray(M2, float)
    return admissibility(Mc).is_admissible
