"""bass/hierarchy/boost_kernel.py (FB-3.3) — axi-symmetric PSTF
boost projection seed.

FB-3.3 introduces a single public surface that every tilt consumer
can route PSTF multipoles through when the tilt direction ``v̂_e`` is
axis-aligned. At the FB-3.3 seed stage the implementation is kept
deliberately minimal: the β=0 path is the byte-identical identity,
the β>0 on-axis path applies the linearised Challinor 2000 aberration
kernel to the PSTF tower, and every off-axis direction raises
``NotImplementedError`` so that the FB-5.2 off-axis helical Wigner
rotation rotation remains the documented follow-up.

Why a seed (not the full Wigner-D projection)
---------------------------------------------
The full non-perturbative boost projection on PSTF moments (Pontzen-
Challinor 2011 §3; Challinor 2000) requires the Wigner-d small-d
matrix elements at arbitrary ``v̂_e`` directions. The axis-aligned
subset is the degenerate case of that projection where only the
m=0 PSTF components couple under the boost; its linearised form
reduces to

    Π'_ℓ = Π_ℓ + β [ (ℓ / (2ℓ − 1)) Π_{ℓ − 1}
                    − ((ℓ + 1) / (2ℓ + 3)) Π_{ℓ + 1} ]
                                        (Challinor 2000 eq (26),
                                         m=0 PSTF projection)

on the m=0 scalar components of the PSTF tower. At the FB-3.3 seed
surface we ship exactly this linear form on the `axisymmetric_coeffs`
field (the m=0 scalar slice), leaving the full Wigner-d lift and the
non-perturbative `cosh β + sinh β ê·v̂_e` exact kernel for FB-5 / a
future phase that closes the off-axis subset.

β=0 path preserves byte-identity of every caller that does not yet
route multipoles through this module.

Scope pins
----------
- On-axis ``v̂_e`` means ``v̂_e`` is aligned with one of the three
  orthonormal tetrad axes ``e_1, e_2, e_3`` within a documented
  tolerance. The default SSOT (``V_HAT_E_DEFAULT = (1, 0, 0)``,
  FB02-F1) is on-axis by construction.
- Off-axis directions raise ``NotImplementedError`` with a reference
  to the FB-5.2 reserved session.
- Only the m=0 component is boosted at the seed stage. The audit
  records this scope restriction so future phases can remove it
  without silently altering semantics.

References
----------
- Challinor 2000, *PRD* 62, 043002 — non-linear CMB boost kernel;
  eq (26) is the linearised PSTF m=0 recurrence shipped here.
- Pontzen & Challinor 2011 — full Wigner-d axi-symmetric projection
  (FB-5 target).
- ``docs/lowell_bianchi/00_conventions.md §2`` — v̂_e SSOT.
- ``docs/lowell_bianchi/extended_coverage/FB8_DISCRIMINATOR_SDD.md``
  §3 — the FB-8 aberration kernel shares the same linear Challinor
  form on the observer side.
"""
from __future__ import annotations

from typing import Tuple

import numpy as np

from bass.species.tilted import V_HAT_E_DEFAULT, V_HAT_NORM_TOL


__all__ = [
    "boost_project_axisymmetric",
    "is_axis_aligned",
    "AXIS_ALIGNMENT_TOL",
]


AXIS_ALIGNMENT_TOL: float = 1e-10
"""Tolerance on ``|v̂_e × e_k|`` for declaring ``v̂_e`` axis-aligned
to one of the three orthonormal tetrad axes. Tight because the
caller supplies a literal unit vector; drift past this threshold is
treated as an off-axis direction and routed to the FB-5.2
``NotImplementedError`` branch."""


def is_axis_aligned(
    v_hat_e: Tuple[float, float, float],
    *,
    tol: float = AXIS_ALIGNMENT_TOL,
) -> bool:
    """Return True iff ``v̂_e`` coincides with ±e_k for some k ∈ {0,1,2}.

    A vector is axis-aligned when exactly one component has magnitude
    1 ± tol and the other two are below tol in absolute value. The
    default SSOT ``V_HAT_E_DEFAULT = (1, 0, 0)`` is axis-aligned by
    construction.
    """
    arr = np.asarray(v_hat_e, dtype=np.float64)
    if arr.shape != (3,):
        raise ValueError(
            f"v_hat_e must have shape (3,), got {arr.shape}"
        )
    mags = np.abs(arr)
    big = mags > (1.0 - tol)
    small = mags < tol
    return int(big.sum()) == 1 and int(small.sum()) == 2


def boost_project_axisymmetric(
    axisymmetric_coeffs: np.ndarray,
    beta: float,
    v_hat_e: Tuple[float, float, float] = V_HAT_E_DEFAULT,
    *,
    tol: float = AXIS_ALIGNMENT_TOL,
) -> np.ndarray:
    """Linear axi-symmetric PSTF boost projection (FB-3.3 seed).

    Takes the m=0 scalar slice of a PSTF multipole tower of length
    ``L_max + 1`` and returns the aberration-boosted slice. The β=0
    path is the byte-identical identity; β>0 applies the linearised
    Challinor 2000 eq (26) recurrence

        Π'_ℓ = Π_ℓ + β [ (ℓ / (2ℓ − 1)) Π_{ℓ − 1}
                        − ((ℓ + 1) / (2ℓ + 3)) Π_{ℓ + 1} ].

    The recurrence is applied in-bounds: at ``ℓ = 0`` the first
    neighbour is absent and drops; at ``ℓ = L_max`` the second
    neighbour is absent and drops. This is the standard truncated-
    tower treatment; callers that need the untruncated high-ℓ
    behaviour should pass a longer tower.

    Parameters
    ----------
    axisymmetric_coeffs : ndarray of shape ``(L_max + 1,)``
        m=0 scalar slice of the PSTF tower. Real-valued. Other
        m-components are left untouched; the caller composes the
        boosted m=0 slice back with the unchanged m ≠ 0 components
        externally.
    beta : float
        Boost magnitude, ``0 ≤ β < 1``. ``β = 0`` returns the input
        array byte-identically (fresh copy) — guarantees the FB-3.2
        regression anchor survives this surface landing.
    v_hat_e : tuple of three floats, default ``V_HAT_E_DEFAULT``
        Direction of the boost. Must be axis-aligned; off-axis
        inputs raise ``NotImplementedError`` (FB-5.2 reserved).
    tol : float
        Axis-alignment tolerance. Defaults to ``AXIS_ALIGNMENT_TOL``.

    Returns
    -------
    ndarray of shape ``(L_max + 1,)``, float64
        Boosted m=0 slice. A fresh array; callers may mutate freely.

    Raises
    ------
    ValueError
        If ``axisymmetric_coeffs`` is not 1-D, or if ``beta`` is out
        of the ``[0, 1)`` admissible range.
    NotImplementedError
        If ``v̂_e`` is not axis-aligned within ``tol``. The error
        message references the FB-5.2 reserved session where the
        off-axis Wigner-d projection lands.

    Reference: Challinor 2000 eq (26); Pontzen-Challinor 2011 §3;
    ``docs/lowell_bianchi/extended_coverage/FB8_DISCRIMINATOR_SDD.md``
    §3 (sibling aberration surface on the observer side).
    """
    arr = np.asarray(axisymmetric_coeffs, dtype=np.float64)
    if arr.ndim != 1:
        raise ValueError(
            f"axisymmetric_coeffs must be 1-D (m=0 PSTF slice), "
            f"got shape {arr.shape}"
        )
    beta_val = float(beta)
    if not np.isfinite(beta_val):
        raise ValueError(f"beta must be finite; got {beta!r}")
    if beta_val < 0.0 or beta_val >= 1.0:
        raise ValueError(
            f"beta must satisfy 0 ≤ β < 1; got beta={beta_val!r}"
        )
    if beta_val == 0.0:
        return arr.copy()

    if not is_axis_aligned(v_hat_e, tol=tol):
        raise NotImplementedError(
            f"boost_project_axisymmetric: off-axis v̂_e={tuple(v_hat_e)!r} "
            f"requires the Wigner-d helical rotation, reserved for FB-5.2. "
            f"For FB-3.3 pass an axis-aligned direction (e.g. the "
            f"V_HAT_E_DEFAULT = {V_HAT_E_DEFAULT!r})."
        )

    # Linearised Challinor 2000 eq (26) on the m=0 slice.
    L_plus_1 = arr.size
    out = arr.copy()
    for ell in range(L_plus_1):
        delta = 0.0
        if ell - 1 >= 0:
            delta += (ell / (2.0 * ell - 1.0)) * arr[ell - 1]
        if ell + 1 < L_plus_1:
            delta -= ((ell + 1.0) / (2.0 * ell + 3.0)) * arr[ell + 1]
        out[ell] = arr[ell] + beta_val * delta

    # Hide the unused-import reminder — V_HAT_NORM_TOL is deliberately
    # re-exported elsewhere in the tilt stack and imported here to pin
    # the SSOT alignment; no runtime use.
    _ = V_HAT_NORM_TOL
    return out
