"""bass/hierarchy/nabla_dispatch.py (FB-2.1) — ∇̃ harmonic-mode dispatch.

Explicit dispatch table for the spatial covariant derivative ``∇̃_a``
on Bianchi homogeneous 3-spaces, decomposed in the per-type harmonic
basis ``Y_k(x)``. The operator acts diagonally on each mode:

    ∇̃_a [Π(η) Y_k(x)] = i k_a Π(η) Y_k(x)

for the plane-wave family (FLRW / I / V / VII_0) and discretely on the
S³ spectrum for Bianchi IX (``∇̃² Y_{ℓ,m} = −ℓ(ℓ+2) Y_{ℓ,m}``).

Scope — FB-2.1 (this module)
----------------------------

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
+----------+-------------------------------------------------------+

Deferred:
- Class A II / VI_0 / VIII         → ``NotImplementedError('FB-2.2')``
- Class B III / IV / VI_h / VII_h  → ``NotImplementedError('FB-2.3')``

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
    "DEFERRED_FB22_TYPES",
    "DEFERRED_FB23_TYPES",
]


# ════════════════════════════════════════════════════════════════════
#   Dispatch registries — source of truth for FB-2.X rotation
# ════════════════════════════════════════════════════════════════════

SUPPORTED_FB21_TYPES: tuple[str, ...] = ("FLRW", "I", "V", "VII_0", "IX")
"""Bianchi types with an explicit ∇̃ dispatch as of FB-2.1."""

DEFERRED_FB22_TYPES: tuple[str, ...] = ("II", "VI_0", "VIII")
"""Class A types whose ∇̃ dispatch is scheduled for FB-2.2."""

DEFERRED_FB23_TYPES: tuple[str, ...] = ("III", "IV", "VI_h", "VII_h")
"""Class B (twist-coupled) types whose ∇̃ dispatch is scheduled for FB-2.3."""


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


_VALIDATORS: dict[str, Callable[[StructureConstants, HarmonicMode], None]] = {
    "FLRW": _validate_mode_flrw,
    "I": _validate_mode_typeI,
    "V": _validate_mode_typeV,
    "VII_0": _validate_mode_typeVII0,
    "IX": _validate_mode_typeIX,
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
      ``IX`` (with ``ell >= 1``) → plane-wave action ``i k_a``.
    - ``II``, ``VI_0``, ``VIII`` → :class:`NotImplementedError` ("FB-2.2").
    - ``III``, ``IV``, ``VI_h``, ``VII_h`` → :class:`NotImplementedError`
      ("FB-2.3"; twist-coupled dispatch).

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
    if label in SUPPORTED_FB21_TYPES:
        _VALIDATORS[label](structure, mode)
        return _plane_wave_operator(mode.k_vec)
    if label in DEFERRED_FB22_TYPES:
        raise NotImplementedError(
            f"∇̃ dispatch for Bianchi type {label!r} is deferred to FB-2.2 "
            f"(Class A II / VI_0 / VIII — spatial Ricci tensor coupling)."
        )
    if label in DEFERRED_FB23_TYPES:
        raise NotImplementedError(
            f"∇̃ dispatch for Bianchi type {label!r} is deferred to FB-2.3 "
            f"(Class B III / IV / VI_h / VII_h — twist-coupled structure "
            f"constants)."
        )
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

    Raises
    ------
    ValueError
        If ``mode.type_label != structure.label``.
    NotImplementedError
        For deferred types (FB-2.2 / FB-2.3).

    References
    ----------
    - Harrison 1967, *Rev. Mod. Phys.* 39, 862 — open-FLRW hyperbolic
      decomposition.
    - Lifshitz-Khalatnikov 1963, *Adv. Phys.* 12, 185 — S³ harmonics.
    - Ellis-Maartens-MacCallum 2012 §16.2 — mode-eigenvalue table.
    """
    if mode.type_label != structure.label:
        raise ValueError(
            f"HarmonicMode.type_label={mode.type_label!r} does not match "
            f"structure.label={structure.label!r}."
        )
    label = structure.label
    if label in SUPPORTED_FB21_TYPES:
        _VALIDATORS[label](structure, mode)
    elif label in DEFERRED_FB22_TYPES:
        raise NotImplementedError(
            f"scalar_laplacian_eigenvalue for {label!r} is deferred to FB-2.2."
        )
    elif label in DEFERRED_FB23_TYPES:
        raise NotImplementedError(
            f"scalar_laplacian_eigenvalue for {label!r} is deferred to FB-2.3."
        )
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
    # FLRW, I, VII_0 (axis-aligned symmetric line).
    return -k2
