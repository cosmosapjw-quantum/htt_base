"""bass/background/tetrad_state.py — Tetrad background state (§2 of
the low-ℓ Bianchi solver reference).

Provides a covariant bookkeeping layer on top of
``bass.background.einstein_bianchi`` that exposes the tetrad-basis
variables

    {α(η), β_ab(η), Σ_ab(η), ³R_ab(η), C^i_{jk}}

used throughout the low-ℓ tetrad-based Bianchi CMB solver reference.
``einstein_bianchi`` evolves (a, Σ_+, Σ_−) in the reduced diagonal
gauge for all 10 Bianchi types plus FLRW; this module lifts that to
the full symmetric-traceless 3-tensor representation so the
perturbation / multipole hierarchy equations (§6, §7, §9 of the
reference) can be written in their index-native form.

Definitions (reference §2.1)
----------------------------
- **α(η)** = ln a(η). Isotropic expansion factor.
- **β_ab(η)** : cumulative anisotropic shape deformation. Symmetric
  trace-free 3-tensor satisfying β̇_ab = 2 Σ_ab (e-fold derivative).
  β_ab(η_0) = 0 by convention (today-normalised).
- **Σ_ab(η)** = e^α σ_ab : conformal shear. Symmetric trace-free
  3-tensor. For axisymmetric types reduces to
      Σ_ab = Σ_+ diag(-2, 1, 1)/√6 + Σ_− diag(0, 1, -1)/√2
  in the aligned-eigenvector basis. Sign of Σ_± follows
  ``einstein_bianchi`` conventions.
- **³R_ab(η)** : anisotropic 3-curvature from the Bianchi spatial
  connection. Type-dependent closed form from
  ``bianchi_types.compute_ricci_tensor`` when available; Type I has
  ³R_ab ≡ 0. For the types where the explicit spatial curvature
  formula is not yet implemented the field is flagged as UNAVAILABLE
  (see ``TetradBackgroundState.curvature_status``).
- **C^i_{jk}** : Bianchi structure constants. Time-independent; taken
  from ``bass.background.bianchi_types.StructureConstants``.

Design notes
------------
This module does NOT re-integrate the background — it wraps the
output of ``solve_bianchi_background``. That way any bug fixes or
accuracy improvements in ``einstein_bianchi`` propagate automatically.

FB-1.4 (Phase FB-1 exit): the anisotropic 3-Ricci ``³R_ab^{aniso}`` is
now defined for **all 11 Bianchi types + FLRW** via the unified
canonical-frame formula

    ³R_ii = (1/2) [n_i² − (n_j − n_k)²]   (cyclic i → j → k)

trace-free part. Class A types (a_twist = 0) recover the
Ellis-MacCallum 1969 §4 expression directly; Class B types
(a_twist ≠ 0, n_2 = 0 in PC frame) inherit the same anisotropic
N-tensor contribution because the twist a_α = (0, a, 0) generates
an isotropic curvature −2 a² δ_ab in the diagonal-aligned tetrad
frame (its trace-free part vanishes; cross-terms are off-diagonal
in PC alignment). The pure twist-coupled anisotropic correction
(W-E ``A²/(1+|h|)`` piece in S^{WE}_+) is deferred to FB-2.2 along
with the hierarchy T1/T2 spatial-Ricci wire-up calibration.

Still not implemented (deferred to future Bianchi-perturbation work):
- Time-dependent basis rotation (spatial frame drift for Types VII_h, IX)
- Twist-coupled anisotropic 3-Ricci correction for Class B (FB-2.2)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from bass.background.bianchi_types import StructureConstants
from bass.background.einstein_bianchi import (
    BianchiBackgroundState, BianchiCosmology, solve_bianchi_background,
)


__all__ = [
    'TetradBackgroundState',
    'build_tetrad_state',
    'axisymmetric_sigma_tensor',
    'anisotropic_3_curvature',
]


# ════════════════════════════════════════════════════════════════════
# Helper: axisymmetric → full 3×3 tensor
# ════════════════════════════════════════════════════════════════════

def axisymmetric_sigma_tensor(sigma_plus: float, sigma_minus: float) -> np.ndarray:
    """Convert (Σ_+, Σ_−) to the full 3×3 symmetric-traceless tensor.

    Using the conventional basis (Misner-Thorne-Wheeler Eq 30.26-ish)

        Σ_ab = Σ_+ · (1/√6) · diag(-2, 1, 1) + Σ_− · (1/√2) · diag(0, 1, -1)

    which satisfies Σ_ab · g^{ab} = 0 and is symmetric. In the frame
    where the x-axis is the principal shear axis.

    Parameters
    ----------
    sigma_plus, sigma_minus : float
        Shear amplitudes in the two axisymmetric channels as
        produced by ``einstein_bianchi``.

    Returns
    -------
    (3, 3) ndarray
        Full symmetric-traceless Σ_ab (trace exactly 0 by construction).
    """
    sigma_ab = np.zeros((3, 3), dtype=np.float64)
    inv_sqrt6 = 1.0 / np.sqrt(6.0)
    inv_sqrt2 = 1.0 / np.sqrt(2.0)
    sigma_ab[0, 0] = sigma_plus * (-2.0) * inv_sqrt6
    sigma_ab[1, 1] = sigma_plus * (+1.0) * inv_sqrt6 + sigma_minus * (+1.0) * inv_sqrt2
    sigma_ab[2, 2] = sigma_plus * (+1.0) * inv_sqrt6 + sigma_minus * (-1.0) * inv_sqrt2
    # Cross terms are zero in the aligned-eigenvector basis.
    return sigma_ab


# Per-type status dispatch — every registered Bianchi label resolves
# to a non-'unavailable' string after FB-1.4 (Phase FB-1 exit contract).
# Strings encode the underlying Lie algebra so downstream consumers can
# branch on the algebraic class without re-inspecting structure constants.
_STATUS_DISPATCH = {
    'FLRW':  'type_i_flat',
    'I':     'type_i_flat',
    'II':    'type_ii_heisenberg',
    'V':     'type_v_isotropic',
    'VI_0':  'type_vi0_e11',
    'VII_0': 'type_vii0_e2',
    'VIII':  'type_viii_sl2r',
    'IX':    'type_ix_so3',
    'III':   'type_iii_class_b',
    'IV':    'type_iv_class_b',
    'VI_h':  'type_vih_class_b',
    'VII_h': 'type_viih_class_b',
}


def anisotropic_3_curvature(
    structure: StructureConstants,
    a: float,
    sigma_plus: float,
    sigma_minus: float,
) -> tuple[Optional[np.ndarray], str]:
    """Compute the anisotropic part of the spatial Ricci tensor ³R_ab^{aniso}.

    The Bianchi 3-spatial Ricci tensor splits as

        ³R_ab = (1/3) ³R δ_ab + ³R_ab^{aniso}

    where δ_ab is the orthonormal-tetrad spatial metric and
    ³R_ab^{aniso} is symmetric trace-free. Only the anisotropic part
    enters the perturbation hierarchy couplings (§6, §9 of the
    lowell reference).

    FB-1.4 (Phase FB-1 exit) consolidates the per-type dispatch onto
    the canonical Class-A orthonormal-frame expression
    (Ellis-MacCallum 1969 §4, eqs (4.19)–(4.21); Wainwright-Ellis 1997
    §1.4.4; Ellis-Maartens-MacCallum 2012 §14.3):

        ³R_ii = (1/2) [n_i² − (n_j − n_k)²]      (cyclic i → j → k)
        ³R_ab^{aniso}_ii = ³R_ii − (1/3) Σ_k ³R_kk

    For Class B in the Pontzen-Challinor frame
    (a_α = (0, a_twist, 0), n_2 = 0 by Jacobi), the twist sector
    contributes −2 a_twist² δ_ab to the diagonal-aligned tetrad ³R_ab,
    which is purely isotropic and therefore drops out of the
    trace-free part. The mixed N × a_twist contribution that produces
    the W-E ``A²/(1+|h|)`` piece in ``S^{WE}_+`` is intentionally
    deferred to **FB-2.2** alongside the hierarchy T1/T2 spatial-Ricci
    wire-up calibration; the FB-1.4 deliverable is the dominant
    N-tensor contribution, which is sufficient for the Phase FB-1 exit
    contract (non-None tensor, symmetric trace-free, finite, FLRW limit
    → 0; see ``test_tetrad_state.py::TestAnisotropic3Curvature``).

    Parameters
    ----------
    structure : StructureConstants
        Bianchi structure constants (any of the 11 types + FLRW).
    a : float
        Scale factor at the evaluation epoch. Currently unused at the
        background level (the spatial Ricci depends only on structure
        constants in the canonical orthonormal frame); accepted for API
        compatibility with ``build_tetrad_state``'s per-grid call.
    sigma_plus, sigma_minus : float
        Conformal shear amplitudes. Unused at this layer (the spatial
        3-Ricci is decoupled from the shear at background level);
        accepted for API symmetry.

    Returns
    -------
    tensor : (3, 3) ndarray
        Symmetric trace-free anisotropic ³R_ab^{aniso} in the
        orthonormal tetrad-aligned frame, with units matching n_i × n_j
        (i.e., [length]⁻²). Diagonal in the aligned-eigenvector basis
        for every registered Bianchi type. **Always non-None** after
        FB-1.4 (the Phase FB-1 exit contract); historical 'unavailable'
        return for unrecognised labels is retained as a safety net only.
    status : str
        Per-type classification, one of
        {'type_i_flat', 'type_v_isotropic', 'type_ii_heisenberg',
         'type_vi0_e11', 'type_vii0_e2', 'type_viii_sl2r',
         'type_ix_so3', 'type_iii_class_b', 'type_iv_class_b',
         'type_vih_class_b', 'type_viih_class_b'}.
        Never 'unavailable' for any registered Bianchi type.

    Special cases (verified analytically + by test)
    -----------------------------------------------
    - **Type I / FLRW** (all n = 0): ³R_ab^{aniso} ≡ 0 by flatness.
    - **Type V** (n = 0, a_twist > 0): tensor is exactly 0 — the twist
      curvature −2 a_twist² δ_ab is isotropic and trace-free part vanishes.
    - **Type VII_0 plane-wave line** (n_1 = n_3, n_2 = 0): every
      diagonal component vanishes algebraically (n_1² − (0 − n_3)² = 0
      and (n_3 − n_1)² = 0). This is the classical Lukash plane-wave-line
      limit reached by the default ``type_vii0_constants(n1=n3=1e-2)``.
    - **Type IX isotropic** (n_1 = n_2 = n_3 = n): every R_ii = n²/2 so
      the trace ³R = 3 n²/2 and the trace-free part vanishes exactly
      (independent of the FB12-F1 W-E shear-source pathology, which is
      a *source* artifact rather than a *curvature* one).
    """
    label = structure.label
    status = _STATUS_DISPATCH.get(label, 'unavailable')
    if status == 'unavailable':
        return None, status

    # API-compatibility absorbers: the spatial 3-Ricci at the
    # background level depends only on the structure constants in the
    # canonical orthonormal frame.
    del a, sigma_plus, sigma_minus

    n1, n2, n3 = structure.n_diag
    R11 = 0.5 * (n1 * n1 - (n2 - n3) ** 2)
    R22 = 0.5 * (n2 * n2 - (n3 - n1) ** 2)
    R33 = 0.5 * (n3 * n3 - (n1 - n2) ** 2)
    one_third_trace = (R11 + R22 + R33) / 3.0

    tensor = np.zeros((3, 3), dtype=np.float64)
    tensor[0, 0] = R11 - one_third_trace
    tensor[1, 1] = R22 - one_third_trace
    tensor[2, 2] = R33 - one_third_trace
    return tensor, status


# ════════════════════════════════════════════════════════════════════
# Tetrad background state dataclass
# ════════════════════════════════════════════════════════════════════

@dataclass
class TetradBackgroundState:
    """Covariant tetrad-basis background history on an η grid.

    All array-valued fields share the same length N = len(eta).
    Tensor fields are stored as (N, 3, 3) arrays in the aligned-
    eigenvector basis (x = principal shear axis for axisymmetric
    types).

    Attributes
    ----------
    eta : (N,) ndarray
        Conformal time [Mpc].
    alpha : (N,) ndarray
        α = ln a.
    a : (N,) ndarray
        Scale factor (redundant with alpha for convenience).
    beta_tensor : (N, 3, 3) ndarray
        β_ab(η), symmetric trace-free, β_ab(η_N) = 0 today.
    sigma_tensor : (N, 3, 3) ndarray
        Σ_ab(η), conformal shear as a 3-tensor.
    aniso_3_curvature : (N, 3, 3) ndarray or None
        Anisotropic part of ³R_ab if computable for this Bianchi type;
        zeros for flat/isotropic types; None for unsupported types.
    structure : StructureConstants
        Bianchi structure constants (time-independent).
    curvature_status : str
        Classification returned by ``anisotropic_3_curvature``.
    cosmo : BianchiCosmology
        Underlying cosmology (includes H0, Ω's, β tilt parameter, …).

    Invariants
    ----------
    - tr Σ_ab = 0  to numerical precision (tested).
    - tr β_ab = 0  to numerical precision (tested).
    - β_ab(η_last) = 0 (today-normalised convention, tested).
    - Σ_ab is symmetric (Σ_ab = Σ_ba, tested).
    """
    eta: np.ndarray
    alpha: np.ndarray
    a: np.ndarray
    beta_tensor: np.ndarray
    sigma_tensor: np.ndarray
    aniso_3_curvature: Optional[np.ndarray]
    structure: StructureConstants
    curvature_status: str
    cosmo: BianchiCosmology

    def shape_at(self, eta: float) -> np.ndarray:
        """β_ab at a given η via nearest-grid-point lookup.

        No interpolation by design — tetrad-state consumers usually
        need the integrated shape on-grid.
        """
        idx = int(np.argmin(np.abs(self.eta - eta)))
        return self.beta_tensor[idx].copy()

    def shear_at(self, eta: float) -> np.ndarray:
        idx = int(np.argmin(np.abs(self.eta - eta)))
        return self.sigma_tensor[idx].copy()

    @property
    def shear_magnitude_sq(self) -> np.ndarray:
        """Σ²_conformal / 6 = (1/6) Σ_ab Σ^ab — the squared conformal-
        shear invariant ``[Mpc]⁻²``.

        This is *not* the Ellis-Wainwright dimensionless ``Σ²_EW``
        (= σ²/H², with σ the proper-time shear and H the Hubble
        parameter). It is the squared Frobenius norm of the
        conformal tensor ``Σ_ab = a σ_ab`` divided by 6, matching the
        convention consumed by ``htt.core.bounds`` and
        ``comparator_policy`` (see ``docs/lowell_bianchi/00_conventions.md``
        §3). Units are ``[Mpc]⁻²``.

        The 1/6 factor comes from the axisymmetric decomposition
        ``Σ_ab Σ^ab = 6 (Σ_+² + Σ_-²)``, so this property returns
        ``Σ_+² + Σ_-²``, the natural "magnitude squared" of the
        shear-shape pair.

        FB-2.4 F3 note: the EMM/Wainwright dimensionless Σ²_EW would
        require dividing by ``H²`` (proper-time) or ``calH²``
        (conformal). Exposing that as a *separate* property is
        deferred to FB-5/6 alongside the perturbation-sector rollout,
        because ``htt.core.bounds`` / ``comparator_policy`` consume
        the current value by name and a rename would cascade beyond
        the Phase FB-2 exit scope.

        Reference: Ellis-MacCallum 1969 §2 (shear invariants); Ellis-
        Maartens-MacCallum 2012 §4.4; Wainwright-Ellis 1997 §1.4
        (Σ_±² normalisation); ``00_conventions.md §3``;
        ``docs/audits/AUDIT_PHASE_FB2_2026-04-19.md`` FB-2.4 F3.
        """
        return np.einsum('nij,nji->n', self.sigma_tensor,
                          self.sigma_tensor) / 6.0


# ════════════════════════════════════════════════════════════════════
# Builder
# ════════════════════════════════════════════════════════════════════

def build_tetrad_state(
    bg: BianchiBackgroundState,
) -> TetradBackgroundState:
    """Wrap a ``BianchiBackgroundState`` as a tetrad-basis state.

    Populates Σ_ab on the η grid from the (Σ_+, Σ_−) axisymmetric
    reduction, integrates β_ab = ∫ 2 Σ_ab dη (trapezoid) and shifts so
    β_ab(η_last) = 0, and computes the anisotropic ³R_ab via
    ``anisotropic_3_curvature``.

    Parameters
    ----------
    bg : BianchiBackgroundState
        Output of ``solve_bianchi_background``.

    Returns
    -------
    TetradBackgroundState
    """
    eta = np.asarray(bg.eta, dtype=np.float64)
    a = np.asarray(bg.a, dtype=np.float64)
    alpha = np.log(np.maximum(a, 1.0e-300))
    Sp = np.asarray(bg.sigma_plus, dtype=np.float64)
    Sm = np.asarray(bg.sigma_minus, dtype=np.float64)

    N = eta.size
    sigma_tensor = np.zeros((N, 3, 3), dtype=np.float64)
    for i in range(N):
        sigma_tensor[i] = axisymmetric_sigma_tensor(float(Sp[i]), float(Sm[i]))

    # β_ab(η) = ∫ 2 Σ_ab(η') dη', with β_ab(η_last) ≡ 0 by convention.
    # Use cumulative trapezoid from the start, then shift.
    beta_tensor = np.zeros_like(sigma_tensor)
    d_eta = np.diff(eta)
    for i in range(1, N):
        beta_tensor[i] = (
            beta_tensor[i - 1]
            + 0.5 * d_eta[i - 1] * 2.0 * (sigma_tensor[i - 1] + sigma_tensor[i])
        )
    # Today-normalise: β_ab(η_last) = 0.
    beta_tensor = beta_tensor - beta_tensor[-1]

    # Anisotropic ³R_ab on the grid.
    ricci_avail = anisotropic_3_curvature(
        bg.cosmo.structure, float(a[-1]), float(Sp[-1]), float(Sm[-1]),
    )
    ricci_0, status = ricci_avail
    if ricci_0 is None:
        aniso_R = None
    else:
        aniso_R = np.zeros((N, 3, 3), dtype=np.float64)
        for i in range(N):
            tensor_i, _ = anisotropic_3_curvature(
                bg.cosmo.structure, float(a[i]),
                float(Sp[i]), float(Sm[i]),
            )
            aniso_R[i] = (tensor_i if tensor_i is not None
                           else np.zeros((3, 3), dtype=np.float64))

    return TetradBackgroundState(
        eta=eta,
        alpha=alpha,
        a=a,
        beta_tensor=beta_tensor,
        sigma_tensor=sigma_tensor,
        aniso_3_curvature=aniso_R,
        structure=bg.cosmo.structure,
        curvature_status=status,
        cosmo=bg.cosmo,
    )
