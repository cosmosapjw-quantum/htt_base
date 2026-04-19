"""bass/hierarchy/nabla_dispatch.py (FB-2.1 + FB-2.2 + FB-2.3) — ∇̃ harmonic-mode dispatch.

Explicit dispatch table for the spatial covariant derivative ``∇̃_a``
on Bianchi homogeneous 3-spaces, decomposed in the per-type harmonic
basis ``Y_k(x)``. The operator acts diagonally on each mode:

    ∇̃_a [Π(η) Y_k(x)] = i k_a Π(η) Y_k(x)

for the plane-wave family (FLRW / I / V / VII_0 / II / VI_0 / VIII /
III / IV / VI_h / VII_h — on their supported axis-aligned subsets)
and discretely on the S³ spectrum for Bianchi IX
(``∇̃² Y_{ℓ,m} = −ℓ(ℓ+2) Y_{ℓ,m}``).

Scope — FB-2.1 + FB-2.2 + FB-2.3 (this module)
----------------------------------------------

Supported per-type dispatch:

+----------+-------------------------------------------------------+
| Type     | Harmonic decomposition                                |
+==========+=======================================================+
| FLRW     | Plane wave ``e^{i k·x}`` on flat 3-space              |
| I        | Plane wave (flat anisotropic Kasner; identical to FLRW|
|          | in a Cartesian tetrad, since n_i = a = 0)             |
| V        | Hyperbolic harmonics (Harrison 1967); ``∇̃² = −(k²+a²)`` |
|          | for open FLRW analogue                                |
| VII_0    | Plane wave with helical phase from e(2) Lie algebra;  |
|          | on the symmetric line ``n_1 = n_3`` and axis-aligned  |
|          | mode (k ∥ e_2) the helical phase vanishes and the     |
|          | action reduces to FLRW                                |
| IX       | Discrete S³ spectrum (Lifshitz-Khalatnikov 1963);     |
|          | scalar Laplacian eigenvalue ``−ℓ(ℓ+2)`` for ℓ ≥ 1     |
| II       | Heisenberg Lie algebra; center = ``span{e_1}``.       |
|          | FB-2.2 restricts to modes along the center            |
|          | (``k_vec = (k_1, 0, 0)``) where the Heisenberg        |
|          | cocycle vanishes and ``∇̃`` reduces to a plane wave    |
|          | with ``∇̃² = −k_1²``                                    |
| VI_0     | ``e(1,1)`` Lie algebra; abelian subalgebra            |
|          | = ``span{e_1, e_3}`` (since ``[e_1, e_3] = n_2 e_2``   |
|          | and ``n_2 = 0`` in the PC frame). FB-2.2 restricts    |
|          | to modes with ``k_2 = 0``; Laplacian eigenvalue       |
|          | ``∇̃² = −(k_1² + k_3²)``                                |
| VIII     | ``sl(2, ℝ)`` Lie algebra; 1-dim Cartan subalgebra     |
|          | = ``span{e_1}`` (the sign-different eigenvalue in     |
|          | the diagonal N convention ``n_1 < 0``). FB-2.2        |
|          | restricts to modes ``k_vec = (k_1, 0, 0)`` along      |
|          | the hyperbolic Cartan axis; Laplacian                 |
|          | ``∇̃² = −k_1²``                                         |
| III      | Class B, h = -1 canonical. Structure constants have  |
|          | a twist sector ``a_α = (0, a_twist, 0)``; PC-frame    |
|          | commutator ``[e_3, e_1] = 0`` because ``n_2 = 0``     |
|          | (Jacobi). FB-2.3 restricts to ``k_vec = (k_1, 0,      |
|          | k_3)`` modes on the abelian ``(e_1, e_3)`` 2-plane.   |
|          | Laplacian carries a Harrison-style twist offset       |
|          | ``λ = −(|k|² + a_twist²/(1+|h|))`` (for III the       |
|          | factor is ``1/2`` because ``|h|=1``).                 |
| IV       | Class B marginal, ``(0, 0, +)`` with ``a_twist > 0``. |
|          | ``h = 0`` (since ``n_1 = 0``). FB-2.3 axis-aligned    |
|          | ``k_2 = 0`` reduction; ``λ = −(|k|² + a_twist²)``     |
|          | (Harrison-V analogue when ``h → 0``).                 |
| VI_h     | Class B open-hyperbolic-like; ``h ∈ (−∞,−1)∪(−1,0)``. |
|          | FB-2.3 axis-aligned ``k_2 = 0`` reduction on the      |
|          | abelian 2-plane; Laplacian                             |
|          | ``λ = −(|k|² + a_twist²/(1+|h|))`` — matches the      |
|          | FB14-F1 W-E ``S^{WE}_+`` shear-source twist piece     |
|          | denominator.                                          |
| VII_h    | Class B, h > 0 — the Pontzen-Challinor spiral type    |
|          | (principal Bianchi CMB anomaly). FB-2.3 axis-aligned  |
|          | ``k_2 = 0`` reduction on the abelian 2-plane;         |
|          | Laplacian ``λ = −(|k|² + a_twist²/(1+h))`` —          |
|          | PC 2007 spiral-mode damping factor matching FB14-F1.  |
+----------+-------------------------------------------------------+

Deferred:
- Off-axis modes on VII_0 / II / VI_0 /    → ``NotImplementedError('FB-5.2')``
  VIII / III / IV / VI_h / VII_h              (full Wigner rotation /
  (generic non-commuting direction)           Grushin / SL(2,R)
                                              principal series /
                                              Class B helical lift)

FB-2.2 / FB-2.3 design rationale — axis-aligned restriction
-----------------------------------------------------------

For a Bianchi type whose Lie algebra is non-abelian, a *generic*
spatial mode ``Y_k`` couples to the structure constants through a
Wigner rotation of spin-1 components (VII_0 / VII_h) or a Grushin-
type reduction (II / VI_0 / VIII / III / VI_h). These couplings are
not plane-wave eigenmodes and require the FB-5 perturbation-sector
state machine to evolve. For the FB-2.x deliverables — which are the
*dispatch tables* consumed by the hierarchy RHS for a static
background contribution — we restrict to the **abelian subalgebra**
of each Lie algebra, where the cocycle vanishes identically and the
plane-wave operator is exact. The non-abelian directions raise an
explicit ``NotImplementedError("FB-5.2")`` so no silent approximation
can leak into downstream code.

Per-type abelian subalgebras (in the PC frame, diagonal ``N``):

    II     :  span{e_1}          (center of Heisenberg)
    VI_0   :  span{e_1, e_3}     ([e_1, e_3] = n_2 e_2 = 0)
    VIII   :  span{e_1}          (Cartan subalgebra; sign-different n_1)
    III    :  span{e_1, e_3}     ([e_3, e_1] = n_2 e_2 = 0 in PC Jacobi)
    IV     :  span{e_1, e_3}     (n_2 = 0 in PC Jacobi; twist along e_2)
    VI_h   :  span{e_1, e_3}     (same as VI_0; twist lifts Laplacian offset)
    VII_h  :  span{e_1, e_3}     (same as VII_0; twist lifts Laplacian offset)

Class B twist structure
-----------------------

Class B (III / IV / VI_h / VII_h) all carry the twist vector
``a_α = (0, a_twist, 0)`` in the PC frame along with diagonal
``N = diag(n_1, 0, n_3)`` (Jacobi identity forces ``n_2 = 0``). On
the abelian ``(e_1, e_3)`` 2-plane the structure-constant commutator
vanishes, so a scalar mode ``Y = e^{i k · x}`` with ``k_2 = 0`` is
an exact plane-wave eigenmode of ``∇̃``. The **scalar Laplacian** on
this subset acquires a curvature offset from the twist sector
analogous to Harrison 1967's Type V formula ``λ = −(|k|² + a²)``;
the Class B generalisation we implement is

    λ = −(|k|² + a_twist² / (1 + |h|))

which reduces to the Harrison-V limit as ``h → 0`` (and matches the
FB14-F1 ``(2/3) A²/(1+|h|)`` piece of ``S^{WE}_+`` in the twist-
coupled shear source). For Type III (h = −1 canonical) the factor
``1/(1+|h|) = 1/2``; for Type IV (h = 0) it is 1; for VI_h and VII_h
it follows the continuous h-parametrisation.

References for the algebraic classification: Wainwright & Ellis
(1997) §1.4.4 + §2.5 + §9.1 (Class B reduction); Ellis-Maartens-
MacCallum (2012) §14.3 + §16; Harrison 1967 eq (4.5) (hyperbolic
twist offset); Pontzen & Challinor 2007 eq (2.12) (VII_h spiral
harmonics). FB-2.1 locked FLRW / I / V / VII_0-symmetric / IX;
FB-2.2 extended to II / VI_0 / VIII abelian subalgebras and wired
hierarchy T1 / T2 spatial-Ricci couplings (see ``terms.py``);
FB-2.3 closes the Class B twist-coupled dispatch on the abelian
``(e_1, e_3)`` 2-plane for III / IV / VI_h / VII_h.

Design — callable contract
--------------------------

``make_nabla_tilde(structure, mode)`` returns a callable

    op(tensor: ndarray, kind: str = 'gradient') -> ndarray

matching the ``zero_nabla_operator`` signature in ``terms.py``, but with
**complex-valued** output (the ``i`` factor from ``∇̃_a = i k_a`` makes
the harmonic-mode amplitude complex in general). For ``kind='gradient'``
the output rank is input rank + 1 with the new index prepended. For
``kind='divergence'`` the contraction is over the **last** axis of the
input tensor (matching the Ellis ``∇̃^b Π_{A_ℓ b}`` convention used by
``T3_divergence``).

Note that the production hierarchy driver ``hierarchy_rhs_photon`` is
real-dtype-only (LB-2b); wiring a complex-valued ``nabla_operator`` into
the driver is deferred to Phase FB-5 (perturbation sector k ≠ 0). This
FB-2.1 module supplies the dispatch table that FB-5 will consume.

References
----------
- ``lowell_bianchi_solver_reference.md §6`` — multipole hierarchy with
  ``∇̃_a`` couplings (T2/T3).
- Wainwright & Ellis, *Dynamical Systems in Cosmology* (CUP 1997) §2.5,
  §9.1 — per-type Killing vectors and invariant basis.
- Ellis, Maartens, MacCallum 2012 §4.6, §16 — PSTF hierarchy and mode
  decomposition.
- Harrison 1967, *Rev. Mod. Phys.* 39, 862 — hyperbolic harmonics for
  open FLRW (k = −1).
- Lifshitz & Khalatnikov 1963, *Adv. Phys.* 12, 185 — S³ harmonic
  decomposition for Bianchi IX (ℓ ≤ n cutoff).
- Pontzen & Challinor 2007, *MNRAS* 380, 1387 — VII_h spiral harmonics
  (helical phase structure).
- ``docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 FB-2.1``.
- ``docs/lowell_bianchi/00_conventions.md §1, §5`` — tetrad indexing.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

import numpy as np

from bass.background.bianchi_types import StructureConstants


__all__ = [
    "HarmonicMode",
    "make_nabla_tilde",
    "scalar_laplacian_eigenvalue",
    "SUPPORTED_FB21_TYPES",
    "SUPPORTED_FB22_TYPES",
    "SUPPORTED_FB23_TYPES",
    "SUPPORTED_TYPES",
    "DEFERRED_FB22_TYPES",
    "DEFERRED_FB23_TYPES",
]


# ════════════════════════════════════════════════════════════════════
#   Dispatch registries — source of truth for FB-2.X rotation
# ════════════════════════════════════════════════════════════════════

SUPPORTED_FB21_TYPES: tuple[str, ...] = ("FLRW", "I", "V", "VII_0", "IX")
"""Bianchi types with an explicit ∇̃ dispatch as of FB-2.1."""

SUPPORTED_FB22_TYPES: tuple[str, ...] = ("II", "VI_0", "VIII")
"""Class A types whose ∇̃ dispatch lands in FB-2.2 (axis-aligned subset
on each type's abelian subalgebra). Off-axis / generic modes raise
``NotImplementedError('FB-5.2')`` at validation time."""

SUPPORTED_FB23_TYPES: tuple[str, ...] = ("III", "IV", "VI_h", "VII_h")
"""Class B (twist-coupled) types whose ∇̃ dispatch lands in FB-2.3.
Each supports the axis-aligned subset on the abelian ``(e_1, e_3)``
2-plane (``k_2 = 0``); the scalar Laplacian eigenvalue carries a
Harrison-V-style ``a_twist² / (1 + |h|)`` offset. Off-axis modes
(generic ``k_2 ≠ 0``) raise ``NotImplementedError('FB-5.2')``."""

SUPPORTED_TYPES: tuple[str, ...] = (
    SUPPORTED_FB21_TYPES + SUPPORTED_FB22_TYPES + SUPPORTED_FB23_TYPES
)
"""Union of FB-2.1 / FB-2.2 / FB-2.3 supported types — used by
hierarchy drivers to gate the explicit dispatch before raising."""

DEFERRED_FB22_TYPES: tuple[str, ...] = ()
"""Retained for backward compatibility with the FB-2.1 partition test.
After FB-2.2 landed, this tuple is empty — II / VI_0 / VIII moved to
:data:`SUPPORTED_FB22_TYPES`."""

DEFERRED_FB23_TYPES: tuple[str, ...] = ()
"""Retained for backward compatibility with the FB-2.1 / FB-2.2
partition tests. After FB-2.3 landed, this tuple is empty — the four
Class B types (III / IV / VI_h / VII_h) moved to
:data:`SUPPORTED_FB23_TYPES`."""


# ════════════════════════════════════════════════════════════════════
#   HarmonicMode descriptor
# ════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class HarmonicMode:
    """Harmonic-mode label for a Bianchi type's ``∇̃`` eigenbasis.

    One instance describes **one** eigenmode ``Y_k`` of the spatial
    Laplacian on the Bianchi 3-space. Its interpretation depends on the
    ``type_label``:

    - ``FLRW`` / ``I``: ``k_vec`` is the Cartesian plane-wave momentum;
      the Laplacian eigenvalue is ``−|k_vec|²``.
    - ``V``: ``k_vec`` is the Harrison (1967) hyperbolic-mode label in
      the open-FLRW sense; ``∇̃² = −(|k_vec|² + a_twist²)``.
    - ``VII_0``: ``k_vec`` is the plane-wave momentum in the tetrad
      frame; on the symmetric line ``n_1 = n_3`` with ``k_vec`` aligned
      with the e_2 symmetry axis, the helical phase is absent and the
      action is identical to FLRW.
    - ``IX``: ``k_vec`` is the *unit direction* of the mode × the
      spin-1 eigenvalue ``√(ℓ(ℓ+2))``; ``ell`` must be provided with
      ``ell ≥ 1`` and ``ell ≤ some cutoff n`` (Lifshitz-Khalatnikov
      ``ℓ ≤ n`` bound is enforced by the caller at FB-5; FB-2.1 only
      validates ``ell ≥ 1``).

    Parameters
    ----------
    type_label : str
        Bianchi type label (must be in :data:`SUPPORTED_FB21_TYPES` for
        the FB-2.1 dispatch to succeed).
    k_vec : ndarray of shape (3,)
        Real-valued mode vector in the tetrad basis (units: 1/Mpc).
    ell : int, optional
        S³ scalar-harmonic index for ``IX``. Must satisfy ``ell >= 1``;
        higher-rank tensor harmonics on S³ require the full SO(4)
        representation theory (deferred to FB-5.1). Ignored for plane-
        wave types.

    References
    ----------
    - FLRW / I: Ma-Bertschinger 1995 §4.
    - V: Harrison 1967 eq (4.5).
    - VII_0: Pontzen & Challinor 2007 eq (2.12) (helical Q-mode).
    - IX: Lifshitz-Khalatnikov 1963 §4 (S³ spherical harmonics).
    """

    type_label: str
    k_vec: np.ndarray
    ell: Optional[int] = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "k_vec", np.asarray(self.k_vec, dtype=np.float64)
        )
        if self.k_vec.shape != (3,):
            raise ValueError(
                f"HarmonicMode.k_vec must have shape (3,), "
                f"got {self.k_vec.shape}"
            )
        if self.type_label == "IX":
            if self.ell is None:
                raise ValueError(
                    "HarmonicMode for IX requires an explicit ell >= 1 "
                    "(S³ scalar-harmonic index)."
                )
            if int(self.ell) < 1:
                raise ValueError(
                    f"IX harmonic ell must be >= 1 (constant mode has no "
                    f"gradient), got ell={self.ell}."
                )


# ════════════════════════════════════════════════════════════════════
#   Core plane-wave operator (shared by FLRW / I / V / VII_0 / IX)
# ════════════════════════════════════════════════════════════════════

def _plane_wave_operator(
    k_vec: np.ndarray,
) -> Callable[[np.ndarray, str], np.ndarray]:
    """Return the harmonic-mode ``∇̃ = i k`` operator as a (tensor, kind) callable.

    Acting on ``Π Y_k``:

    - ``gradient``: rank ℓ → ℓ + 1, with the new index prepended:
      ``(i k_a) ⊗ Π``.
    - ``divergence``: rank ℓ → ℓ − 1, contracted over the last axis:
      ``i k^b Π_{…b}``.

    The ``i`` factor promotes the return dtype to ``complex128``; the
    caller is responsible for managing real/complex composition.

    Reference: Ellis-Maartens-MacCallum 2012 §16.1 (mode decomposition).
    """
    i_k = 1j * k_vec.astype(np.complex128)

    def op(tensor: np.ndarray, kind: str = "gradient") -> np.ndarray:
        arr = np.asarray(tensor)
        if arr.ndim == 0:
            arr_c = np.asarray(arr, dtype=np.complex128)
            if kind == "gradient":
                return i_k * arr_c  # rank-1 from rank-0
            if kind == "divergence":
                raise ValueError(
                    "divergence of a rank-0 tensor is not defined"
                )
            raise ValueError(
                f"kind must be 'gradient' or 'divergence', got {kind!r}"
            )
        arr_c = arr.astype(np.complex128, copy=False)
        if kind == "gradient":
            # New index prepended: shape (3,) + arr.shape.
            return np.tensordot(i_k, arr_c, axes=0)
        if kind == "divergence":
            # Contract i_k (axis 0) against the LAST axis of arr_c.
            # Result shape: arr.shape[:-1] — rank reduced by 1.
            return np.tensordot(arr_c, i_k, axes=([arr_c.ndim - 1], [0]))
        raise ValueError(
            f"kind must be 'gradient' or 'divergence', got {kind!r}"
        )

    return op


# ════════════════════════════════════════════════════════════════════
#   Per-type mode-label validators (FB-2.1)
# ════════════════════════════════════════════════════════════════════

def _validate_mode_flrw(structure: StructureConstants, mode: HarmonicMode) -> None:
    """FLRW: any real 3-vector ``k`` is a valid plane-wave momentum.

    The only regularity requirement is that ``k`` be finite.
    """
    if not np.all(np.isfinite(mode.k_vec)):
        raise ValueError(f"FLRW mode k_vec must be finite, got {mode.k_vec}")


def _validate_mode_typeI(structure: StructureConstants, mode: HarmonicMode) -> None:
    """Bianchi I: identical to FLRW (n_i = a_twist = 0 → flat tetrad)."""
    if not np.all(np.isfinite(mode.k_vec)):
        raise ValueError(f"Type I mode k_vec must be finite, got {mode.k_vec}")


def _validate_mode_typeV(structure: StructureConstants, mode: HarmonicMode) -> None:
    """Bianchi V: Harrison hyperbolic mode. k is real in the tetrad frame;
    the hyperbolic eigenvalue carries the ``a_twist`` shift via
    ``∇̃² = −(|k|² + a²)`` — enforced by
    ``scalar_laplacian_eigenvalue``, not by mode validation.
    """
    if not np.all(np.isfinite(mode.k_vec)):
        raise ValueError(f"Type V mode k_vec must be finite, got {mode.k_vec}")
    if structure.a_twist <= 0:
        raise ValueError(
            f"Type V requires a_twist > 0, got a_twist={structure.a_twist}"
        )


def _validate_mode_typeVII0(
    structure: StructureConstants, mode: HarmonicMode
) -> None:
    """Bianchi VII_0: plane wave with helical phase from e(2) Lie algebra.

    FB-2.1 supports the **axis-aligned symmetric-line reduction**: when
    ``n_1 = n_3`` and the mode vector is aligned with the e_2 symmetry
    axis (``k_vec = (0, k2, 0)``), the helical phase rotation around
    e_2 is degenerate and ``∇̃`` acts as a flat plane wave. Generic
    off-axis modes (non-trivial Wigner rotation of spin-1 components)
    are reserved for FB-5.2.
    """
    if not np.all(np.isfinite(mode.k_vec)):
        raise ValueError(f"VII_0 mode k_vec must be finite, got {mode.k_vec}")
    if structure.n1 <= 0 or structure.n3 <= 0:
        raise ValueError(
            f"VII_0 requires n_1 > 0 and n_3 > 0, got "
            f"(n_1, n_3) = ({structure.n1}, {structure.n3})"
        )
    # Symmetric line n_1 = n_3 + axis-aligned mode on e_2: helical
    # phase vanishes and action reduces to FLRW. Off-line / off-axis
    # modes require the FB-5.2 generic Wigner rotation operator.
    symmetric_line = abs(structure.n1 - structure.n3) <= 1e-12 * max(
        abs(structure.n1), abs(structure.n3), 1.0
    )
    axis_aligned_e2 = (
        abs(mode.k_vec[0]) <= 1e-14 * max(np.linalg.norm(mode.k_vec), 1.0)
        and abs(mode.k_vec[2]) <= 1e-14 * max(np.linalg.norm(mode.k_vec), 1.0)
    )
    if not (symmetric_line and axis_aligned_e2):
        raise NotImplementedError(
            "FB-2.1 VII_0 dispatch supports only the axis-aligned "
            "symmetric-line reduction (n_1 = n_3, k_vec ∥ e_2). "
            "Generic off-axis helical-phase Wigner rotation is deferred "
            "to FB-5.2 (perturbation-sector harmonic mode decomposition)."
        )


def _validate_mode_typeIX(
    structure: StructureConstants, mode: HarmonicMode
) -> None:
    """Bianchi IX: discrete S³ spectrum. Caller must supply ``ell >= 1``.

    The plane-wave operator is applied with ``|k_vec|`` representing the
    spin-1 eigenvalue on the S³ Laplacian; ``∇̃² → −ℓ(ℓ+2)`` enforced
    by :func:`scalar_laplacian_eigenvalue`.
    """
    if not np.all(np.isfinite(mode.k_vec)):
        raise ValueError(f"IX mode k_vec must be finite, got {mode.k_vec}")
    # Already validated in HarmonicMode.__post_init__ that ell >= 1.
    if structure.n1 <= 0 or structure.n2 <= 0 or structure.n3 <= 0:
        raise ValueError(
            f"IX requires n_1, n_2, n_3 > 0, got n_diag={structure.n_diag}"
        )


# ════════════════════════════════════════════════════════════════════
#   FB-2.2 — per-type validators for II / VI_0 / VIII
# ════════════════════════════════════════════════════════════════════

def _k_component_is_zero(component: float, k_norm: float) -> bool:
    """Tolerance-aware zero check for one Cartesian ``k_vec`` component.

    Uses a ``1e-14 × max(|k|, 1)`` absolute threshold so that modes
    pure-aligned with an axis are accepted at float-arithmetic
    roundoff while generic off-axis modes are rejected.
    """
    return abs(component) <= 1e-14 * max(k_norm, 1.0)


def _validate_mode_typeII(
    structure: StructureConstants, mode: HarmonicMode
) -> None:
    """Bianchi II (Heisenberg): axis-aligned mode on the center ``e_1``.

    The Heisenberg Lie algebra has ``[e_2, e_3] = n_1 e_1`` with all
    other brackets vanishing; ``e_1`` is therefore the 1-dim center of
    the algebra. A scalar plane-wave mode ``Y_k = e^{i k_1 x_1}`` feels
    no Heisenberg cocycle because the twist term acts as
    ``(n_1 x_2) ∂_1``, which only affects modes with non-zero ``k_2``
    or ``k_3`` content. FB-2.2 dispatches exactly this axis-aligned
    subset (``k_vec = (k_1, 0, 0)``); the generic off-axis (Grushin-
    type) spectrum is deferred to FB-5.2.

    Reference: Wainwright-Ellis 1997 §1.4.4 (Heisenberg group); Folland
    *Harmonic Analysis in Phase Space* §1.4 (Heisenberg Laplacian
    Schrödinger reduction).
    """
    if not np.all(np.isfinite(mode.k_vec)):
        raise ValueError(f"Type II mode k_vec must be finite, got {mode.k_vec}")
    if structure.n1 <= 0:
        raise ValueError(
            f"Type II requires n_1 > 0, got n_1 = {structure.n1}"
        )
    k_norm = float(np.linalg.norm(mode.k_vec))
    if not (
        _k_component_is_zero(mode.k_vec[1], k_norm)
        and _k_component_is_zero(mode.k_vec[2], k_norm)
    ):
        raise NotImplementedError(
            "FB-2.2 Type II dispatch supports only axis-aligned modes "
            "on the Heisenberg center (k_vec = (k_1, 0, 0)). Generic "
            "off-axis modes couple to the Heisenberg cocycle and "
            "require the Grushin harmonic-oscillator decomposition — "
            "deferred to FB-5.2 (perturbation-sector harmonic modes)."
        )


def _validate_mode_typeVI0(
    structure: StructureConstants, mode: HarmonicMode
) -> None:
    """Bianchi VI_0 (``e(1,1)``): axis-aligned on the 2-D abelian plane.

    In our PC frame with diagonal ``N = diag(n_1, 0, n_3)`` (``n_1 > 0``,
    ``n_3 < 0``), the structure constants ``C^c_{ab} = ε_{abd} n^{dc}``
    give ``[e_1, e_3] = n_2 e_2 = 0`` (since ``n_2 = 0``). Thus
    ``span{e_1, e_3}`` is an abelian 2-plane, while ``e_2`` is the
    non-abelian direction. A scalar mode with ``k_2 = 0`` lives entirely
    on the abelian plane and ``∇̃`` acts as a pure plane wave with
    eigenvalue ``−(k_1² + k_3²)``. Off-plane modes (``k_2 ≠ 0``) feel
    the hyperbolic boost generated by ``e_2`` and require the FB-5.2
    generalised dispatch.

    Reference: Wainwright-Ellis 1997 §1.4.4 (``e(1,1)`` algebra);
    Ellis-Maartens-MacCallum 2012 §14.3 (Bianchi VI_0 classification).
    """
    if not np.all(np.isfinite(mode.k_vec)):
        raise ValueError(f"VI_0 mode k_vec must be finite, got {mode.k_vec}")
    if structure.n1 <= 0 or structure.n3 >= 0:
        raise ValueError(
            f"VI_0 requires n_1 > 0 and n_3 < 0 (mixed sign), got "
            f"(n_1, n_3) = ({structure.n1}, {structure.n3})"
        )
    k_norm = float(np.linalg.norm(mode.k_vec))
    if not _k_component_is_zero(mode.k_vec[1], k_norm):
        raise NotImplementedError(
            "FB-2.2 Type VI_0 dispatch supports only modes on the "
            "abelian (e_1, e_3) plane (k_2 = 0). Modes with non-zero "
            "k_2 couple to the hyperbolic boost of e(1,1) and require "
            "the FB-5.2 generalised Wigner-rotation dispatch."
        )


def _validate_mode_typeVIII(
    structure: StructureConstants, mode: HarmonicMode
) -> None:
    """Bianchi VIII (``sl(2, ℝ)``): axis-aligned on the hyperbolic Cartan.

    ``sl(2, ℝ)`` is semisimple with rank 1: its Cartan subalgebra is
    1-dimensional. In the diagonal-``N`` convention with
    ``N = diag(n_1, n_2, n_3)``, ``n_1 < 0, n_2, n_3 > 0``, the sign-
    different direction ``e_1`` is the "hyperbolic" Cartan generator;
    the corresponding 1-parameter subgroup is abelian. FB-2.2 restricts
    the dispatch to ``k_vec = (k_1, 0, 0)`` modes along this Cartan
    direction, where ``∇̃`` acts as a plane wave with eigenvalue
    ``−k_1²``. Generic modes mixing with ``e_2, e_3`` decompose into
    principal-series representations of ``SL(2, ℝ)`` and are deferred
    to FB-5.2.

    Reference: Wainwright-Ellis 1997 §1.4.4 (``sl(2, ℝ)`` algebra);
    Bargmann 1947 (SL(2,R) principal series); Pontzen & Challinor 2007
    for the CMB-side anisotropy structure.
    """
    if not np.all(np.isfinite(mode.k_vec)):
        raise ValueError(f"VIII mode k_vec must be finite, got {mode.k_vec}")
    if structure.n1 >= 0 or structure.n2 <= 0 or structure.n3 <= 0:
        raise ValueError(
            f"VIII requires n_1 < 0, n_2 > 0, n_3 > 0, got "
            f"n_diag = {structure.n_diag}"
        )
    k_norm = float(np.linalg.norm(mode.k_vec))
    if not (
        _k_component_is_zero(mode.k_vec[1], k_norm)
        and _k_component_is_zero(mode.k_vec[2], k_norm)
    ):
        raise NotImplementedError(
            "FB-2.2 Type VIII dispatch supports only axis-aligned modes "
            "on the 1-D Cartan (k_vec = (k_1, 0, 0) with n_1 < 0 the "
            "hyperbolic direction). Generic modes require the SL(2,R) "
            "principal-series decomposition — deferred to FB-5.2."
        )


# ════════════════════════════════════════════════════════════════════
#   FB-2.3 — per-type validators for Class B III / IV / VI_h / VII_h
# ════════════════════════════════════════════════════════════════════


def _validate_class_b_axis_aligned_k2_zero(
    label: str,
    structure: StructureConstants,
    mode: HarmonicMode,
) -> None:
    """Shared Class B axis-aligned guard: ``k_2 = 0`` on abelian plane.

    In the PC frame the Jacobi identity ``n^{αβ} a_β = 0`` with
    ``a_β = (0, a_twist, 0)`` forces ``n_2 = 0`` for every Class B
    type. Consequently the commutator ``[e_3, e_1] = n_2 e_2 = 0``
    and ``span{e_1, e_3}`` is an abelian 2-subalgebra. A scalar mode
    ``Y = e^{i k · x}`` with ``k_2 = 0`` lives entirely on this plane
    and ``∇̃`` acts as a pure plane wave. Modes with ``k_2 ≠ 0``
    couple to the e_2 twist generator and require the FB-5.2
    generalised dispatch.
    """
    if not np.all(np.isfinite(mode.k_vec)):
        raise ValueError(
            f"Type {label} mode k_vec must be finite, got {mode.k_vec}"
        )
    if structure.a_twist <= 0:
        raise ValueError(
            f"Class B Type {label} requires a_twist > 0, got "
            f"a_twist = {structure.a_twist}"
        )
    k_norm = float(np.linalg.norm(mode.k_vec))
    if not _k_component_is_zero(mode.k_vec[1], k_norm):
        raise NotImplementedError(
            f"FB-2.3 Type {label} dispatch supports only axis-aligned "
            f"modes on the abelian (e_1, e_3) 2-plane (k_2 = 0). "
            f"Modes with non-zero k_2 couple to the e_2 twist "
            f"generator a_α = (0, a_twist, 0) and require the FB-5.2 "
            f"generalised helical/Wigner-rotation dispatch."
        )


def _validate_mode_typeIII(
    structure: StructureConstants, mode: HarmonicMode
) -> None:
    """Bianchi III = VI_{h=-1}: Class B canonical (h = −1).

    Structure constants: ``(n_1, n_2, n_3) = (+, 0, −)`` with
    ``a_twist > 0`` satisfying ``a_twist² = −n_1 · n_3`` (i.e. ``h = −1``
    exactly). FB-2.3 restricts the dispatch to the abelian plane
    ``k_2 = 0`` where ``∇̃`` acts as a plane wave; the scalar Laplacian
    carries the Harrison-V-style offset ``−(|k|² + a_twist²/2)``
    (h-factor ``1/(1+|h|) = 1/2`` at ``|h| = 1``).

    Reference: Wainwright-Ellis 1997 §9.1 (Class B subfamilies);
    Ellis-MacCallum 1969 (Type III = VI_{-1} identification).
    """
    _validate_class_b_axis_aligned_k2_zero("III", structure, mode)
    if structure.n1 <= 0 or structure.n3 >= 0:
        raise ValueError(
            f"Type III requires n_1 > 0 and n_3 < 0, got "
            f"(n_1, n_3) = ({structure.n1}, {structure.n3})"
        )


def _validate_mode_typeIV(
    structure: StructureConstants, mode: HarmonicMode
) -> None:
    """Bianchi IV: Class B marginal, ``(0, 0, +)`` with ``a_twist > 0``.

    Structure constants have ``n_1 = n_2 = 0`` and ``n_3 > 0``, giving
    ``h = a_twist² / (n_1 · n_3) = 0`` (our convention: ``h = 0`` when
    ``n_1 · n_3 = 0``). FB-2.3 restricts to the abelian
    ``span{e_1, e_3}`` 2-plane (``k_2 = 0``); ``∇̃`` acts as a plane
    wave, and the Laplacian carries the Harrison-V offset
    ``−(|k|² + a_twist²)`` (h-factor 1 when ``|h| = 0``).

    Type IV admits no FLRW limit — see ``type_iv_constants`` docstring
    for the falsifiability motivation.

    Reference: Wainwright-Ellis 1997 §9.1 Table (Bianchi IV marginal);
    Ellis-MacCallum 1969 §4 (Type IV classification).
    """
    _validate_class_b_axis_aligned_k2_zero("IV", structure, mode)
    if structure.n3 <= 0 or abs(structure.n1) > 1e-30:
        raise ValueError(
            f"Type IV requires n_1 = 0 and n_3 > 0, got "
            f"(n_1, n_3) = ({structure.n1}, {structure.n3})"
        )


def _validate_mode_typeVIh(
    structure: StructureConstants, mode: HarmonicMode
) -> None:
    """Bianchi VI_h (h ∈ (−∞,−1) ∪ (−1, 0)): Class B open-hyperbolic.

    Structure constants: ``(n_1, n_2, n_3) = (+, 0, −)`` with
    ``a_twist > 0``, ``h = a_twist² / (n_1 · n_3)`` negative and not
    equal to −1 (that special value is Type III). FB-2.3 restricts to
    the abelian plane ``k_2 = 0``; Laplacian
    ``−(|k|² + a_twist²/(1+|h|))`` — the denominator matches the
    FB14-F1 ``(2/3) A²/(1+|h|)`` piece of ``S^{WE}_+``.

    Reference: Wainwright-Ellis 1997 §9.1 (VI_h); Ellis-Maartens-
    MacCallum 2012 §14.3 (class B spatial Ricci).
    """
    _validate_class_b_axis_aligned_k2_zero("VI_h", structure, mode)
    if structure.n1 <= 0 or structure.n3 >= 0:
        raise ValueError(
            f"Type VI_h requires n_1 > 0 and n_3 < 0, got "
            f"(n_1, n_3) = ({structure.n1}, {structure.n3})"
        )
    h = structure.h_parameter
    if abs(h + 1.0) <= 1e-12:
        raise ValueError(
            f"Type VI_h requires h ≠ −1 (h = −1 is Type III), got h = {h}"
        )


def _validate_mode_typeVIIh(
    structure: StructureConstants, mode: HarmonicMode
) -> None:
    """Bianchi VII_h (h > 0): Class B Pontzen-Challinor spiral type.

    Structure constants: ``(n_1, n_2, n_3) = (+, 0, +)`` with
    ``a_twist > 0``, ``h = a_twist² / (n_1 · n_3) > 0``. FB-2.3
    restricts to the abelian plane ``k_2 = 0``; ``∇̃`` acts as a
    plane wave, and the scalar Laplacian carries the PC 2007 spiral-
    damping offset ``−(|k|² + a_twist²/(1+h))`` (matching the FB14-F1
    shear-source ``(2/3) A²/(1+h)`` twist piece).

    Reference: Pontzen & Challinor 2007 eq (2.12) (VII_h spiral
    harmonics); Wainwright-Ellis 1997 §9.1 (VII_h); Pontzen 2009
    (Bianchi CMB signature).
    """
    _validate_class_b_axis_aligned_k2_zero("VII_h", structure, mode)
    if structure.n1 <= 0 or structure.n3 <= 0:
        raise ValueError(
            f"Type VII_h requires n_1 > 0 and n_3 > 0, got "
            f"(n_1, n_3) = ({structure.n1}, {structure.n3})"
        )


_VALIDATORS: dict[str, Callable[[StructureConstants, HarmonicMode], None]] = {
    "FLRW": _validate_mode_flrw,
    "I": _validate_mode_typeI,
    "V": _validate_mode_typeV,
    "VII_0": _validate_mode_typeVII0,
    "IX": _validate_mode_typeIX,
    "II": _validate_mode_typeII,
    "VI_0": _validate_mode_typeVI0,
    "VIII": _validate_mode_typeVIII,
    "III": _validate_mode_typeIII,
    "IV": _validate_mode_typeIV,
    "VI_h": _validate_mode_typeVIh,
    "VII_h": _validate_mode_typeVIIh,
}


# ════════════════════════════════════════════════════════════════════
#   Public API
# ════════════════════════════════════════════════════════════════════

def make_nabla_tilde(
    structure: StructureConstants,
    mode: HarmonicMode,
) -> Callable[[np.ndarray, str], np.ndarray]:
    """Build the harmonic-mode ``∇̃`` operator for a given Bianchi type.

    Returns a callable ``op(tensor, kind='gradient'|'divergence')`` with
    the same signature as :func:`bass.hierarchy.terms.zero_nabla_operator`
    but **complex-valued** output (``dtype = complex128``).

    Dispatch:

    - ``FLRW``, ``I``, ``V``, ``VII_0`` (axis-aligned symmetric line),
      ``IX`` (with ``ell >= 1``) → plane-wave action ``i k_a``
      (FB-2.1).
    - ``II`` (``k_vec = (k_1, 0, 0)``), ``VI_0`` (``k_2 = 0``),
      ``VIII`` (``k_vec = (k_1, 0, 0)``) → plane-wave action ``i k_a``
      on each type's abelian subalgebra (FB-2.2).
    - ``III`` / ``IV`` / ``VI_h`` / ``VII_h`` (``k_2 = 0``) →
      plane-wave action ``i k_a`` on the Class B abelian
      ``(e_1, e_3)`` 2-plane; scalar Laplacian carries the
      Harrison-V twist offset ``a_twist²/(1+|h|)`` (FB-2.3).
    - Off-axis modes on any of the non-abelian types →
      :class:`NotImplementedError` ("FB-5.2"; generalised Wigner /
      principal-series / Grushin / helical decomposition).

    The ``structure.label`` drives the dispatch; ``mode.type_label``
    must match, otherwise ``ValueError``.

    Parameters
    ----------
    structure : StructureConstants
        Bianchi group structure constants (``bass.background.bianchi_types``).
    mode : HarmonicMode
        Harmonic-mode label for the ``∇̃`` eigenbasis.

    Raises
    ------
    ValueError
        If ``mode.type_label != structure.label`` or the mode is
        malformed (non-finite ``k_vec``, wrong ``ell`` on IX, etc.).
    NotImplementedError
        For Bianchi types deferred to FB-2.2 / FB-2.3, or for VII_0
        modes off the symmetric / axis-aligned line.

    References
    ----------
    - ``docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 FB-2.1``.
    - Ellis, Maartens, MacCallum 2012 §16.1 (mode decomposition).
    """
    if mode.type_label != structure.label:
        raise ValueError(
            f"HarmonicMode.type_label={mode.type_label!r} does not match "
            f"structure.label={structure.label!r}."
        )

    label = structure.label
    if label in SUPPORTED_TYPES:
        _VALIDATORS[label](structure, mode)
        return _plane_wave_operator(mode.k_vec)
    raise ValueError(f"Unknown Bianchi type label: {label!r}")


def scalar_laplacian_eigenvalue(
    structure: StructureConstants,
    mode: HarmonicMode,
) -> float:
    """Return the scalar Laplacian eigenvalue ``λ`` such that
    ``∇̃² Y_k = λ Y_k``.

    Per-type formulae:

    - ``FLRW``, ``I``, ``VII_0`` (axis-aligned symmetric line):
      ``λ = −|k_vec|²``.
    - ``V``: ``λ = −(|k_vec|² + a_twist²)`` (Harrison 1967 eq 4.5;
      hyperbolic-harmonic spectrum with the ``a²`` offset from the
      negatively curved 3-space).
    - ``IX``: ``λ = −ℓ(ℓ+2)`` (Lifshitz-Khalatnikov 1963 §4; S³
      scalar-harmonic spectrum, independent of ``k_vec`` magnitude).
    - ``II``, ``VIII`` (axis-aligned on the Cartan / center):
      ``λ = −k_1²`` — the plane-wave restriction on the 1-D abelian
      subalgebra (FB-2.2).
    - ``VI_0`` (``k_2 = 0``): ``λ = −(k_1² + k_3²)`` — plane-wave
      restriction on the 2-D abelian ``e(1,1)`` plane (FB-2.2).
    - ``III``, ``IV``, ``VI_h``, ``VII_h`` (``k_2 = 0``):
      ``λ = −(|k_vec|² + a_twist²/(1+|h|))`` — Harrison-V twist offset
      generalised to Class B; ``h = a_twist²/(n_1 n_3)``. At ``h = 0``
      (Type IV / Type V limit) the denominator is 1 (Harrison-V
      recovery); at ``|h| = 1`` (Type III canonical) it is 2 (the
      half-twist offset). Matches the FB14-F1 shear-source
      ``(2/3) A²/(1+|h|)`` piece (FB-2.3).

    Raises
    ------
    ValueError
        If ``mode.type_label != structure.label``.
    NotImplementedError
        For off-axis subsets on II / VI_0 / VIII / VII_0 /
        III / IV / VI_h / VII_h (FB-5.2).

    References
    ----------
    - Harrison 1967, *Rev. Mod. Phys.* 39, 862 — open-FLRW hyperbolic
      decomposition.
    - Lifshitz-Khalatnikov 1963, *Adv. Phys.* 12, 185 — S³ harmonics.
    - Ellis-Maartens-MacCallum 2012 §16.2 — mode-eigenvalue table.
    - Wainwright-Ellis 1997 §1.4.4 / §9.1 — Class A Lie algebras and
      Class B subfamilies (twist-coupled abelian subalgebras).
    - Pontzen & Challinor 2007 eq (2.12) — VII_h spiral harmonics.
    """
    if mode.type_label != structure.label:
        raise ValueError(
            f"HarmonicMode.type_label={mode.type_label!r} does not match "
            f"structure.label={structure.label!r}."
        )
    label = structure.label
    if label in SUPPORTED_TYPES:
        _VALIDATORS[label](structure, mode)
    else:
        raise ValueError(f"Unknown Bianchi type label: {label!r}")

    k2 = float(np.dot(mode.k_vec, mode.k_vec))
    if label == "IX":
        ell = int(mode.ell)  # type: ignore[arg-type]
        return -float(ell * (ell + 2))
    if label == "V":
        # Harrison 1967 eq (4.5): Δ Y = -(k² + a²) Y on open-FLRW-like
        # hyperbolic 3-space; a_twist is the curvature scale.
        return -(k2 + float(structure.a_twist) ** 2)
    if label in SUPPORTED_FB23_TYPES:
        # Class B twist offset: Harrison-V generalisation with the
        # h-dependent denominator that matches the FB14-F1 W-E
        # ``S^{WE}_+`` ``(2/3) A²/(1+|h|)`` piece. At h → 0 this
        # reduces to the Harrison-V form ``−(k² + a²)``; at
        # |h| = 1 (Type III) the factor is 1/2.
        a = float(structure.a_twist)
        h_denom = 1.0 + abs(float(structure.h_parameter))
        return -(k2 + a * a / h_denom)
    # FLRW, I, VII_0 (axis-aligned symmetric line), II (axis-aligned),
    # VI_0 (k_2 = 0), VIII (axis-aligned on Cartan) — all reduce to
    # ``−|k_vec|²`` on their respective supported axis-aligned subsets.
    # The abelian-subalgebra restriction was enforced by the per-type
    # validator above.
    return -k2
