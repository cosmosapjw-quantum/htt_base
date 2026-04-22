"""bass/hierarchy/pstf_tensor.py (LB-2a) — PSTF tensor containers.

Provides ``PSTFTensor`` (a single rank-ℓ projected symmetric trace-free
tensor stored in the real spherical-harmonic packing) and
``PSTFHierarchyState`` (a full multipole tower ``{Π_0, Π_1, …, Π_L}``),
together with conversion utilities between the packed and full-tensor
representations.

Storage convention: packing is ``(2ℓ+1,)`` with index mapping

    i = 0, 1, …, 2ℓ   ↔   m = −ℓ, −ℓ+1, …, 0, …, +ℓ

in the real spherical-harmonic basis (see
``docs/lowell_bianchi/00_conventions.md §5`` and
``02_multipole_hierarchy_spec.md §2``). The basis tensors themselves
are computed in ``bass.hierarchy.contractions`` and shared between the
packed-to-full and the STF projector routines.

References
----------
- Ellis, Maartens, MacCallum §4.5 — moment expansion of the photon
  distribution function, PSTF tensor definition.
- Arfken-Weber-Harris *Mathematical Methods* Ch 16 — real spherical
  harmonics basis and the (2ℓ+1)-dimensional count.
- ``docs/lowell_bianchi/02_multipole_hierarchy_spec.md §2``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

import numpy as np

from bass.hierarchy.contractions import (
    pstf_pack,
    pstf_unpack,
    stf_basis,
)


__all__ = [
    "PSTFTensor",
    "PSTFHierarchyState",
    "zero_pstf",
    "zero_hierarchy",
    "pstf_from_tensor",
    "pstf_to_tensor",
    "pack_hierarchy",
    "unpack_hierarchy",
    "hierarchy_total_size",
]


def _trusted_pstf_tensor(ell: int, components: np.ndarray) -> "PSTFTensor":
    """Internal fast constructor for already-validated packed tensors."""
    tensor = object.__new__(PSTFTensor)
    tensor.ell = int(ell)
    tensor.components = components
    return tensor


def _trusted_hierarchy_state(
    L: int,
    tensors: List["PSTFTensor"],
) -> "PSTFHierarchyState":
    """Internal fast constructor for already-validated tower lists."""
    state = object.__new__(PSTFHierarchyState)
    state.L = int(L)
    state.tensors = tensors
    return state


@dataclass
class PSTFTensor:
    """Rank-ℓ projected symmetric trace-free tensor on 3-space.

    Attributes
    ----------
    ell : non-negative int
        Tensor rank (number of spatial indices).
    components : (2ℓ+1,) float64 or complex128 ndarray
        Packed amplitudes in the real spherical-harmonic basis,
        ordered ``m = -ℓ, …, 0, …, +ℓ``.

    Post-construction invariants
    ----------------------------
    - ``len(components) == 2*ell + 1``.
    - ``components.dtype`` is coerced to ``float64`` or ``complex128``
      depending on whether the input carries an imaginary lane.

    Reference: ``00_conventions.md §5``; Ellis §4.5.2.
    """

    ell: int
    components: np.ndarray

    def __post_init__(self) -> None:
        if not isinstance(self.ell, (int, np.integer)):
            raise TypeError(f"ell must be int, got {type(self.ell).__name__}")
        ell = int(self.ell)
        if ell < 0:
            raise ValueError(f"ell must be non-negative, got {ell}")
        self.ell = ell
        arr = np.asarray(self.components)
        dtype = np.complex128 if np.iscomplexobj(arr) else np.float64
        arr = arr.astype(dtype, copy=False)
        expected_shape = (2 * ell + 1,)
        if arr.shape != expected_shape:
            raise ValueError(
                f"components shape {arr.shape} != (2ℓ+1,) = {expected_shape}"
            )
        self.components = arr

    # --- Arithmetic -------------------------------------------------------

    def __add__(self, other: "PSTFTensor") -> "PSTFTensor":
        if not isinstance(other, PSTFTensor):
            return NotImplemented
        if self.ell != other.ell:
            raise ValueError(
                f"PSTFTensor ℓ mismatch: {self.ell} vs {other.ell}"
            )
        return _trusted_pstf_tensor(
            ell=self.ell,
            components=self.components + other.components,
        )

    def __sub__(self, other: "PSTFTensor") -> "PSTFTensor":
        if not isinstance(other, PSTFTensor):
            return NotImplemented
        if self.ell != other.ell:
            raise ValueError(
                f"PSTFTensor ℓ mismatch: {self.ell} vs {other.ell}"
            )
        return _trusted_pstf_tensor(
            ell=self.ell,
            components=self.components - other.components,
        )

    def __neg__(self) -> "PSTFTensor":
        return _trusted_pstf_tensor(ell=self.ell, components=-self.components)

    def __mul__(self, scalar: float | complex) -> "PSTFTensor":
        if isinstance(scalar, PSTFTensor):
            return NotImplemented
        scalar_arr = np.asarray(scalar)
        if scalar_arr.ndim != 0:
            return NotImplemented
        return _trusted_pstf_tensor(
            ell=self.ell,
            components=self.components * scalar_arr.item(),
        )

    __rmul__ = __mul__

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PSTFTensor):
            return NotImplemented
        return (
            self.ell == other.ell
            and np.array_equal(self.components, other.components)
        )

    def allclose(
        self, other: "PSTFTensor", rtol: float = 1e-10, atol: float = 1e-13
    ) -> bool:
        """Numerically-tolerant equality."""
        if self.ell != other.ell:
            return False
        return bool(
            np.allclose(self.components, other.components, rtol=rtol, atol=atol)
        )

    def norm(self) -> float:
        """Scalar invariant ``||Π||² = Π_{A_ℓ} Π^{A_ℓ}``.

        Because the packed basis is flat-orthonormal (``Q_ℓ^T Q_ℓ = I``),
        this reduces to ``Σ_m c_m²``.
        """
        return float(np.vdot(self.components, self.components).real)

    # --- Representations --------------------------------------------------

    def to_full_tensor(self) -> np.ndarray:
        """Return the rank-ℓ full-tensor representation (shape ``(3,)*ℓ``).

        For ``ℓ = 0`` the return is a 0-d ndarray. The result is
        automatically symmetric and trace-free by construction of the
        STF basis.

        Reference: 02_multipole_hierarchy_spec.md §2.3.
        """
        return pstf_unpack(self.components, self.ell)

    def copy(self) -> "PSTFTensor":
        return _trusted_pstf_tensor(self.ell, self.components.copy())


def zero_pstf(ell: int) -> PSTFTensor:
    """Factory: all-zero PSTFTensor of rank ``ell``.

    Reference: 02_multipole_hierarchy_spec.md §2.3.
    """
    if ell < 0:
        raise ValueError(f"ell must be non-negative, got {ell}")
    return _trusted_pstf_tensor(
        ell=ell,
        components=np.zeros(2 * ell + 1, dtype=np.float64),
    )


def pstf_from_tensor(tensor: np.ndarray) -> PSTFTensor:
    """Convert a full rank-ℓ tensor to its PSTFTensor projection.

    Any symmetric-trace-free content is preserved; traces and
    antisymmetric components are silently removed.

    Reference: Ellis §4.5 Clebsch-Gordan decomposition;
    02_multipole_hierarchy_spec.md §2.3.
    """
    arr = np.asarray(tensor)
    if arr.ndim == 0:
        ell = 0
    else:
        ell = arr.ndim
    components = pstf_pack(arr)
    return _trusted_pstf_tensor(ell=ell, components=components)


def pstf_to_tensor(pstf: PSTFTensor) -> np.ndarray:
    """Convert a PSTFTensor back to its rank-ℓ full-tensor representation.

    Inverse of ``pstf_from_tensor`` on the STF subspace.

    Reference: 02_multipole_hierarchy_spec.md §2.3.
    """
    return pstf.to_full_tensor()


# ════════════════════════════════════════════════════════════════════
#   Multipole tower container
# ════════════════════════════════════════════════════════════════════

def hierarchy_total_size(L: int) -> int:
    """Total number of packed components in a tower of depth ``L``.

    Formula: ``Σ_{ℓ=0}^{L} (2ℓ+1) = (L+1)²``.

    Reference: 02_multipole_hierarchy_spec.md §2.5.
    """
    if L < 0:
        raise ValueError(f"L must be non-negative, got {L}")
    return (L + 1) ** 2


@dataclass
class PSTFHierarchyState:
    """Tower ``{Π_0, Π_1, …, Π_L}`` of PSTF tensors.

    Attributes
    ----------
    L : int
        Highest multipole retained.
    tensors : list of PSTFTensor
        Length ``L + 1``. Entry at index ``ℓ`` has ``ell == ℓ``.

    Reference: 02_multipole_hierarchy_spec.md §2.5.
    """

    L: int
    tensors: List[PSTFTensor] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.L < 0:
            raise ValueError(f"L must be non-negative, got {self.L}")
        if len(self.tensors) != self.L + 1:
            raise ValueError(
                f"tensors length {len(self.tensors)} != L+1 = {self.L + 1}"
            )
        for ell, t in enumerate(self.tensors):
            if t.ell != ell:
                raise ValueError(
                    f"tensors[{ell}].ell = {t.ell}; expected {ell}"
                )

    @property
    def total_size(self) -> int:
        """Total packed length across all multipoles."""
        return hierarchy_total_size(self.L)

    def as_flat(self) -> np.ndarray:
        """Concatenate all component arrays into a single 1-D vector.

        This is the layout consumed by ``scipy.integrate.solve_ivp``.

        Reference: 02_multipole_hierarchy_spec.md §9.3.
        """
        return np.concatenate([t.components for t in self.tensors])

    @classmethod
    def from_flat(cls, flat: np.ndarray, L: int) -> "PSTFHierarchyState":
        """Inverse of ``as_flat`` — split a flat vector into a tower.

        Reference: 02_multipole_hierarchy_spec.md §9.3.
        """
        expected = hierarchy_total_size(L)
        arr = np.asarray(flat)
        dtype = np.complex128 if np.iscomplexobj(arr) else np.float64
        arr = arr.astype(dtype, copy=False)
        if arr.shape != (expected,):
            raise ValueError(
                f"flat shape {arr.shape} != ({expected},) for L={L}"
            )
        tensors: List[PSTFTensor] = []
        offset = 0
        for ell in range(L + 1):
            size = 2 * ell + 1
            comp = arr[offset:offset + size].copy()
            tensors.append(_trusted_pstf_tensor(ell=ell, components=comp))
            offset += size
        return _trusted_hierarchy_state(L=L, tensors=tensors)

    def copy(self) -> "PSTFHierarchyState":
        return _trusted_hierarchy_state(
            L=self.L,
            tensors=[t.copy() for t in self.tensors],
        )


def zero_hierarchy(L: int) -> PSTFHierarchyState:
    """Factory: all-zero multipole tower up to depth ``L``.

    Reference: 02_multipole_hierarchy_spec.md §2.5.
    """
    return _trusted_hierarchy_state(
        L=L,
        tensors=[zero_pstf(ell) for ell in range(L + 1)],
    )


def pack_hierarchy(state: PSTFHierarchyState) -> np.ndarray:
    """Pack a ``PSTFHierarchyState`` into a flat vector."""
    return state.as_flat()


def unpack_hierarchy(flat: np.ndarray, L: int) -> PSTFHierarchyState:
    """Unpack a flat vector into a ``PSTFHierarchyState``."""
    return PSTFHierarchyState.from_flat(flat, L)


# Silence unused-import warning on stf_basis (kept as explicit public
# dependency surface for downstream terms modules).
_ = stf_basis
_ = Tuple
