"""R49 canonical Bianchi convention bridge and exact dual-route geometry oracle.

Bridges Pontzen-Challinor (`StructureConstants`, `bass.tilt.species_tilt`) and
VER2 canonical (`BianchiAlgebra`, `bass.background.geometry`) representations
across all 12 homogeneous types (`FLRW` and the 11 Bianchi Class A / Class B
types) without mutating or breaking frozen VER2 regression modules.

Key features:
1. Exact bijective O(3) frame transformation on `(a_alpha, n^{alpha beta})`,
   explicitly carrying pseudotensor parity `n' = det(M) M n M^T` for both
   improper permutations (`det(M) = -1`, e.g. `(1, 0, 2)`) and proper `SO(3)`
   rotations (`det(M) = +1`).
2. Explicit structure-tensor `a`-sign convention tracking (`+1` for VER2
   `C^gamma_{alpha beta} = eps_{alpha beta delta} n^{delta gamma} + a_alpha delta^gamma_beta - a_beta delta^gamma_alpha`,
   `-1` for Pontzen-Challinor/species_tilt `eps n + delta^gamma_alpha a_beta - delta^gamma_beta a_alpha`).
3. Regularized Class-B `h` parameterization supporting `h = -1` (`III <-> VI_{-1}`)
   and `h = -1/9` (`VI_{-1/9}`) without division by zero or silent relabeling.
4. Exact dual-route Class A/B spatial Ricci oracle (`exact_spatial_ricci_from_compact`),
   including the Class-B symmetric `a x n` off-diagonal coupling omitted by the
   diagonal-only compact helper in `geometry.py`, matching `spatial_ricci_from_connection`
   to `< 1e-15` in any O(3) frame.
5. Structural `ActionEquivalenceSet` metadata recording locally isometric /
   FLRW-limit equivalent group actions (`I ~ VII_0` for flat space,
   `V ~ VII_h` for hyperbolic space, and `III ~ VI_{-1}`).
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Literal

import numpy as np

from bass.background.bianchi_types import (
    ALL_BIANCHI_TYPES,
    BianchiAlgebra,
    BianchiBranchPolicy,
    CLASS_A_TYPES,
    CLASS_B_TYPES,
    MARGINAL_TYPES,
    StructureConstants,
    TYPES_WITH_FLRW_LIMIT,
    build_bianchi_algebra,
    get_type,
)
from bass.background.geometry import (
    connection_from_commutators,
    div_pstf2,
    pstf_rank2,
    spatial_ricci_from_connection,
)

__all__ = [
    "ALL_TWELVE_FAMILIES",
    "LEVI_CIVITA_3D",
    "PC_TO_VER2_IMPROPER_PERMUTATION",
    "PC_TO_VER2_PROPER_ROTATION",
    "VER2_TO_PC_PROPER_ROTATION",
    "ActionEquivalenceSet",
    "BIANCHI_ACTION_EQUIVALENCE_CLASSES",
    "ConventionSpec",
    "StructureTriple",
    "CanonicalBridgeReport",
    "build_structure_tensor_with_sign",
    "transform_structure_pair",
    "compute_regularized_h",
    "exact_spatial_ricci_from_compact",
    "exact_momentum_divergence",
    "structure_constants_to_triple",
    "algebra_to_triple",
    "structure_constants_to_ver2_algebra",
    "ver2_algebra_to_structure_constants",
    "action_equivalence_for_family",
    "verify_convention_bridge_family",
    "verify_all_families_convention_bridge",
]

ALL_TWELVE_FAMILIES: tuple[str, ...] = ("FLRW", *ALL_BIANCHI_TYPES)


def _build_levi_civita_3d() -> np.ndarray:
    eps = np.zeros((3, 3, 3), dtype=np.float64)
    eps[0, 1, 2] = eps[1, 2, 0] = eps[2, 0, 1] = 1.0
    eps[0, 2, 1] = eps[2, 1, 0] = eps[1, 0, 2] = -1.0
    return eps


LEVI_CIVITA_3D: np.ndarray = _build_levi_civita_3d()

# Improper permutation matrix swapping axis 0 and axis 1 (det = -1).
# Maps Pontzen-Challinor Class-B axis ordering (e_0, e_1, e_2) with a along axis 1
# to VER2 axis ordering with a along axis 0.
PC_TO_VER2_IMPROPER_PERMUTATION: np.ndarray = np.array(
    [[0.0, 1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 1.0]],
    dtype=np.float64,
)

# Proper SO(3) rotation by -pi/2 around axis 2 (det = +1):
# e'_0 = e_1, e'_1 = -e_0, e'_2 = e_2. Preserves spatial handedness cleanly.
PC_TO_VER2_PROPER_ROTATION: np.ndarray = np.array(
    [[0.0, 1.0, 0.0], [-1.0, 0.0, 0.0], [0.0, 0.0, 1.0]],
    dtype=np.float64,
)

VER2_TO_PC_PROPER_ROTATION: np.ndarray = PC_TO_VER2_PROPER_ROTATION.T.copy()


@dataclass(frozen=True)
class ActionEquivalenceSet:
    """Group-action equivalence metadata under fixed local spatial geometry."""

    equivalence_id: str
    member_families: tuple[str, ...]
    spatial_curvature_sign: Literal["flat_k0", "negative_k", "positive_k", "anisotropic_marginal"]
    has_flrw_limit: bool
    geometric_orbit: str
    identifiability_note: str


BIANCHI_ACTION_EQUIVALENCE_CLASSES: dict[str, ActionEquivalenceSet] = {
    "FLAT_K0_FLRW_LIMIT": ActionEquivalenceSet(
        equivalence_id="FLAT_K0_FLRW_LIMIT",
        member_families=("FLRW", "I", "VII_0"),
        spatial_curvature_sign="flat_k0",
        has_flrw_limit=True,
        geometric_orbit="Euclidean R^3 homogeneous hypersurface (abelian I and E(2) VII_0)",
        identifiability_note=(
            "Types I and VII_0 both act transitively on flat R^3 and share identical "
            "isotropic limit; helical VII_0 modes can mimic flat shear+dipole locally."
        ),
    ),
    "OPEN_KNEG_FLRW_LIMIT": ActionEquivalenceSet(
        equivalence_id="OPEN_KNEG_FLRW_LIMIT",
        member_families=("V", "VII_h"),
        spatial_curvature_sign="negative_k",
        has_flrw_limit=True,
        geometric_orbit="Hyperbolic H^3 homogeneous hypersurface (isotropic V and tilted/helical VII_h)",
        identifiability_note=(
            "Types V and VII_h both have negative spatial curvature k<0 and admit FLRW "
            "open limits; non-axisymmetric/helical VII_h degenerates with V+boost when |n|/|a|->0 or k_hel->0."
        ),
    ),
    "CLOSED_KPOS_FLRW_LIMIT": ActionEquivalenceSet(
        equivalence_id="CLOSED_KPOS_FLRW_LIMIT",
        member_families=("IX",),
        spatial_curvature_sign="positive_k",
        has_flrw_limit=True,
        geometric_orbit="3-sphere S^3 (SU(2)) homogeneous hypersurface",
        identifiability_note="Unique Bianchi family with closed S^3 spatial curvature in FLRW limit.",
    ),
    "TYPE_III_VI_MINUS_ONE": ActionEquivalenceSet(
        equivalence_id="TYPE_III_VI_MINUS_ONE",
        member_families=("III", "VI_h(h=-1)"),
        spatial_curvature_sign="anisotropic_marginal",
        has_flrw_limit=False,
        geometric_orbit="H^2 x R product geometry corresponding to Class B n_2*n_3 = -a^2 (h = -1)",
        identifiability_note="Type III is canonically isomorphic to Bianchi VI_h at h = -1.",
    ),
    "MARGINAL_CLASS_A_II": ActionEquivalenceSet(
        equivalence_id="MARGINAL_CLASS_A_II",
        member_families=("II",),
        spatial_curvature_sign="anisotropic_marginal",
        has_flrw_limit=False,
        geometric_orbit="Heisenberg nilmanifold (n eigenvalues +,0,0)",
        identifiability_note="No FLRW limit; out of scope for linearized_near_flrw transfer.",
    ),
    "MARGINAL_CLASS_A_VI0": ActionEquivalenceSet(
        equivalence_id="MARGINAL_CLASS_A_VI0",
        member_families=("VI_0",),
        spatial_curvature_sign="anisotropic_marginal",
        has_flrw_limit=False,
        geometric_orbit="Sol geometry E(1,1) (n eigenvalues +,0,-)",
        identifiability_note="No FLRW limit; out of scope for linearized_near_flrw transfer.",
    ),
    "MARGINAL_CLASS_A_VIII": ActionEquivalenceSet(
        equivalence_id="MARGINAL_CLASS_A_VIII",
        member_families=("VIII",),
        spatial_curvature_sign="anisotropic_marginal",
        has_flrw_limit=False,
        geometric_orbit="SL(2,R) universal cover (n eigenvalues -,+,+)",
        identifiability_note="No FLRW limit; out of scope for linearized_near_flrw transfer.",
    ),
    "MARGINAL_CLASS_B_IV": ActionEquivalenceSet(
        equivalence_id="MARGINAL_CLASS_B_IV",
        member_families=("IV",),
        spatial_curvature_sign="anisotropic_marginal",
        has_flrw_limit=False,
        geometric_orbit="Class-B degenerate n rank-1 (n2*n3 = 0, a != 0, h -> inf/0 boundary)",
        identifiability_note="No FLRW limit; regularized without dividing by n2*n3.",
    ),
    "MARGINAL_CLASS_B_VIH": ActionEquivalenceSet(
        equivalence_id="MARGINAL_CLASS_B_VIH",
        member_families=("VI_h",),
        spatial_curvature_sign="anisotropic_marginal",
        has_flrw_limit=False,
        geometric_orbit="Class-B h < 0 (n2*n3 < 0, including special shear-curl locus h = -1/9)",
        identifiability_note="No FLRW limit; includes special h = -1/9 locus handled without singularity.",
    ),
}


def action_equivalence_for_family(family: str) -> ActionEquivalenceSet:
    """Return the `ActionEquivalenceSet` governing local geometric/orbit degeneracy."""
    norm = "VI_h(h=-1)" if family == "VI_-1" else family
    for eq in BIANCHI_ACTION_EQUIVALENCE_CLASSES.values():
        if norm in eq.member_families:
            return eq
    raise KeyError(f"Unknown Bianchi/FLRW family {family!r}")


@dataclass(frozen=True)
class ConventionSpec:
    """Explicit triad-orientation and structure-tensor convention descriptor."""

    frame_name: str
    a_sign: Literal[1, -1]
    basis_matrix: np.ndarray

    def __post_init__(self) -> None:
        if self.a_sign not in (1, -1):
            raise ValueError(f"a_sign must be +1 or -1, got {self.a_sign!r}")
        M = np.asarray(self.basis_matrix, dtype=np.float64)
        if M.shape != (3, 3):
            raise ValueError(f"basis_matrix must be (3, 3), got {M.shape}")
        if not np.allclose(M @ M.T, np.eye(3), atol=1.0e-12):
            raise ValueError("basis_matrix must be orthogonal (M @ M.T == I)")
        object.__setattr__(self, "basis_matrix", M)


@dataclass(frozen=True)
class StructureTriple:
    """Explicit `(a, n, a_sign)` representation with regularized `h` bookkeeping."""

    type_name: str
    a: np.ndarray
    n: np.ndarray
    a_sign: Literal[1, -1]
    frame_name: str
    class_label: Literal["A", "B"]
    h_parameter: float | None
    h_numerator_a_sq: float
    h_denominator_minor: float

    def __post_init__(self) -> None:
        a_arr = np.asarray(self.a, dtype=np.float64)
        n_arr = np.asarray(self.n, dtype=np.float64)
        if a_arr.shape != (3,) or n_arr.shape != (3, 3):
            raise ValueError("Invalid shapes for (a, n) in StructureTriple")
        if not np.allclose(n_arr, n_arr.T, atol=1.0e-13):
            raise ValueError("Matrix n must be symmetric")
        object.__setattr__(self, "a", a_arr)
        object.__setattr__(self, "n", 0.5 * (n_arr + n_arr.T))

    def structure_tensor(self) -> np.ndarray:
        """Compute `C[gamma, alpha, beta]` with explicit `self.a_sign`."""
        return build_structure_tensor_with_sign(self.a, self.n, a_sign=self.a_sign)

    def jacobi_residual(self) -> float:
        """Euclidean norm of the Jacobi vector `n @ a` (must vanish identically)."""
        return float(np.linalg.norm(self.n @ self.a))

    def is_special_class_b_locus(self, tol: float = 1.0e-10) -> str | None:
        """Identify `h = -1` (Type III) or `h = -1/9` (exceptional VI_{-1/9}) safely."""
        if self.class_label == "A":
            return None
        # Check algebraic identity a^2 + n2*n3 == 0 (h = -1) and 9 a^2 + n2*n3 == 0 (h = -1/9)
        if abs(self.h_numerator_a_sq) < tol and abs(self.h_denominator_minor) < tol:
            return "Type_V_isotropic_hyperbolic"
        if abs(self.h_numerator_a_sq + self.h_denominator_minor) < tol:
            return "h_equals_minus_1_Type_III_equivalent"
        if abs(9.0 * self.h_numerator_a_sq + self.h_denominator_minor) < tol:
            return "h_equals_minus_one_ninth_exceptional_VI_h"
        if abs(self.h_denominator_minor) < tol and abs(self.h_numerator_a_sq) > tol:
            return "h_denominator_zero_Type_IV_or_V"
        return None


def compute_regularized_h(
    a: np.ndarray,
    n: np.ndarray,
    tol: float = 1.0e-14,
) -> tuple[float | None, float, float]:
    """Compute `(h, a^2, prod_perp)` without division by zero.

    Uses the 2x2 transverse minor of `n` in the subspace orthogonal to `a`:
    let `D = n^2_tr - (tr(n)^2 - tr(n^2))/2` on the plane orthogonal to `a_hat`;
    specifically in invariant form since `n @ a = 0` when Jacobi holds:
    `minor_perp = 0.5 * ((tr n)^2 - tr(n^2))` when `a` lies in the null space of `n`
    (the exact product of the two transverse eigenvalues `n_2 * n_3`).
    """
    a_arr = np.asarray(a, dtype=np.float64)
    n_arr = np.asarray(n, dtype=np.float64)
    a_sq = float(a_arr @ a_arr)
    if a_sq <= tol:
        return None, 0.0, 0.0
    # When n @ a = 0, one eigenvalue along a is 0, and the product of the other
    # two eigenvalues equals the trace of the adjugate on the a-orthogonal plane:
    minor_perp = 0.5 * (float(np.trace(n_arr)) ** 2 - float(np.sum(n_arr * n_arr)))
    if abs(minor_perp) <= tol:
        return None, a_sq, float(minor_perp)
    return float(a_sq / minor_perp), a_sq, float(minor_perp)


def build_structure_tensor_with_sign(
    a: np.ndarray,
    n: np.ndarray,
    *,
    a_sign: Literal[1, -1] = 1,
) -> np.ndarray:
    """Build `C[gamma, alpha, beta]` with `[e_alpha, e_beta] = C^gamma_{alpha beta} e_gamma`.

    When `a_sign == +1` (VER2 convention):
        C^gamma_{alpha beta} = eps_{alpha beta delta} n^{delta gamma}
                             + (a_alpha delta^gamma_beta - a_beta delta^gamma_alpha).
    When `a_sign == -1` (Pontzen-Challinor / `species_tilt` convention):
        C^gamma_{alpha beta} = eps_{alpha beta delta} n^{delta gamma}
                             - (a_alpha delta^gamma_beta - a_beta delta^gamma_alpha)
                             = eps_{alpha beta delta} n^{delta gamma}
                             + (delta^gamma_alpha a_beta - delta^gamma_beta a_alpha).
    """
    if a_sign not in (1, -1):
        raise ValueError(f"a_sign must be +1 or -1, got {a_sign!r}")
    a_arr = np.asarray(a, dtype=np.float64)
    n_arr = np.asarray(n, dtype=np.float64)
    delta = np.eye(3, dtype=np.float64)
    term_n = np.einsum("abd,dg->gab", LEVI_CIVITA_3D, n_arr)
    term_a = float(a_sign) * (
        np.einsum("a,bg->gab", a_arr, delta) - np.einsum("b,ag->gab", a_arr, delta)
    )
    return term_n + term_a


def transform_structure_pair(
    a: np.ndarray,
    n: np.ndarray,
    basis_matrix: np.ndarray,
    *,
    a_sign_in: Literal[1, -1] = 1,
    a_sign_out: Literal[1, -1] = 1,
) -> tuple[np.ndarray, np.ndarray, float]:
    """Transform `(a, n)` under an orthonormal basis change `e'_i = M_i^j e_j`.

    Preserves the geometric Lie bracket `[e'_i, e'_j] = C'^k_{ij} e'_k` identically:
    - `n' = det(M) * (M @ n @ M.T)` (pseudotensor factor accounts for parity flips)
    - `a' = (a_sign_in * a_sign_out) * (M @ a)` (polar vector + sign convention adapter).

    Returns `(a_prime, n_prime, det_M)`.
    """
    M = np.asarray(basis_matrix, dtype=np.float64)
    if M.shape != (3, 3) or not np.allclose(M @ M.T, np.eye(3), atol=1.0e-12):
        raise ValueError("basis_matrix must be a 3x3 orthogonal matrix")
    det_m = float(np.linalg.det(M))
    if abs(abs(det_m) - 1.0) > 1.0e-10:
        raise ValueError(f"det(basis_matrix) must be +/-1, got {det_m}")
    det_sign = 1.0 if det_m > 0.0 else -1.0
    a_arr = np.asarray(a, dtype=np.float64)
    n_arr = np.asarray(n, dtype=np.float64)
    sign_factor = float(a_sign_in * a_sign_out)
    a_prime = sign_factor * (M @ a_arr)
    n_prime = det_sign * (M @ n_arr @ M.T)
    n_prime = 0.5 * (n_prime + n_prime.T)
    return a_prime, n_prime, det_sign


def exact_spatial_ricci_from_compact(
    a: np.ndarray,
    n: np.ndarray,
    *,
    a_sign: Literal[1, -1] = 1,
) -> tuple[np.ndarray, float, np.ndarray]:
    """Exact spatial Ricci tensor `R_{ij}`, scalar `R`, and PSTF `R_{<ij>}`.

    Implements the complete Ellis-MacCallum compact formula valid for ALL Class A
    and Class B Bianchi types in any `O(3)` spatial frame:
        R_{ij} = 2 n_{ik} n^k_j - (tr n) n_{ij}
                 + (eps_{ikl} a_eff^k n^l_j + eps_{jkl} a_eff^k n^l_i)
                 - delta_{ij} (2 a_eff^2 + tr(n^2) - 0.5 * (tr n)^2),
    where `a_eff = a_sign * a`. Matches `spatial_ricci_from_connection` to < 1e-15.
    """
    a_eff = float(a_sign) * np.asarray(a, dtype=np.float64)
    n_arr = 0.5 * (np.asarray(n, dtype=np.float64) + np.asarray(n, dtype=np.float64).T)
    tr_n = float(np.trace(n_arr))
    n_sq = float(np.sum(n_arr * n_arr))
    a_sq = float(a_eff @ a_eff)

    # Antisymmetric/symmetric a x n coupling: vanishes in Class A, essential off-diagonal in Class B.
    axn = np.einsum("icd,c,dj->ij", LEVI_CIVITA_3D, a_eff, n_arr)
    ricci_iso = 2.0 * a_sq + n_sq - 0.5 * (tr_n ** 2)
    ricci_tensor = 2.0 * (n_arr @ n_arr) - tr_n * n_arr + (axn + axn.T) - ricci_iso * np.eye(3)
    ricci_tensor = 0.5 * (ricci_tensor + ricci_tensor.T)
    ricci_scalar = float(np.trace(ricci_tensor))
    ricci_pstf = pstf_rank2(ricci_tensor)
    return ricci_tensor, ricci_scalar, ricci_pstf


def exact_momentum_divergence(
    sigma_ab: np.ndarray,
    a: np.ndarray,
    n: np.ndarray,
    *,
    a_sign: Literal[1, -1] = 1,
) -> np.ndarray:
    """Compute covariant spatial divergence `(div sigma)_i = D_j sigma^j_i`.

    Algebraically identical (to < 1e-15) to `div_pstf2(sigma_ab, Gamma)` for
    `Gamma = connection_from_commutators(build_structure_tensor_with_sign(a, n, a_sign=a_sign))`:
        D_j sigma^j_i = - (sigma_{jk} eps_{kil} n_{lj} + 3 a_sign sigma_{ij} a_j).
    The Codazzi / Einstein momentum constraint is `D_j sigma^j_i - kappa q_i = 0`.
    """
    sigma = pstf_rank2(np.asarray(sigma_ab, dtype=np.float64))
    a_eff = float(a_sign) * np.asarray(a, dtype=np.float64)
    n_arr = np.asarray(n, dtype=np.float64)
    return -(np.einsum("jk,kil,lj->i", sigma, LEVI_CIVITA_3D, n_arr) + 3.0 * (sigma @ a_eff))


def structure_constants_to_triple(
    sc: StructureConstants,
    *,
    target_frame: Literal["pontzen_challinor", "ver2_proper", "ver2_improper"] = "pontzen_challinor",
    a_sign_out: Literal[1, -1] = 1,
) -> StructureTriple:
    """Convert PC `StructureConstants` into `StructureTriple` in requested frame."""
    a_pc = np.array([0.0, sc.a_twist, 0.0], dtype=np.float64)
    n_pc = np.diag([sc.n1, sc.n2, sc.n3]).astype(np.float64)
    if target_frame == "pontzen_challinor":
        M = np.eye(3, dtype=np.float64)
        frame_label = "pontzen_challinor"
    elif target_frame == "ver2_proper":
        M = PC_TO_VER2_PROPER_ROTATION
        frame_label = "ver2_proper"
    elif target_frame == "ver2_improper":
        M = PC_TO_VER2_IMPROPER_PERMUTATION
        frame_label = "ver2_improper"
    else:
        raise ValueError(f"Unknown target_frame {target_frame!r}")

    a_out, n_out, _ = transform_structure_pair(
        a_pc, n_pc, M, a_sign_in=1, a_sign_out=a_sign_out
    )
    h_reg, a_sq, minor_perp = compute_regularized_h(a_out, n_out)
    class_label: Literal["A", "B"] = "B" if abs(sc.a_twist) > 0.0 else "A"
    return StructureTriple(
        type_name=sc.label,
        a=a_out,
        n=n_out,
        a_sign=a_sign_out,
        frame_name=frame_label,
        class_label=class_label,
        h_parameter=h_reg,
        h_numerator_a_sq=a_sq,
        h_denominator_minor=minor_perp,
    )


def algebra_to_triple(algebra: BianchiAlgebra) -> StructureTriple:
    """Wrap an existing VER2 `BianchiAlgebra` as an inspected `StructureTriple`."""
    h_reg, a_sq, minor_perp = compute_regularized_h(algebra.a, algebra.n)
    return StructureTriple(
        type_name=algebra.type_name,
        a=algebra.a,
        n=algebra.n,
        a_sign=1,
        frame_name="ver2_canonical",
        class_label="B" if algebra.class_label == "B" else "A",
        h_parameter=h_reg,
        h_numerator_a_sq=a_sq,
        h_denominator_minor=minor_perp,
    )


def _infer_bianchi_type_name(
    a_ver2: np.ndarray,
    n_ver2: np.ndarray,
    requested_label: str | None = None,
    tol: float = 1.0e-12,
) -> str:
    if requested_label in ALL_TWELVE_FAMILIES:
        return requested_label
    eigvals = np.linalg.eigvalsh(0.5 * (n_ver2 + n_ver2.T))
    pos = int(np.sum(eigvals > tol))
    neg = int(np.sum(eigvals < -tol))
    a_norm = float(np.linalg.norm(a_ver2))
    if a_norm <= tol:
        if pos == 0 and neg == 0:
            return "I"
        if (pos, neg) in ((1, 0), (0, 1)):
            return "II"
        if (pos, neg) == (1, 1):
            return "VI_0"
        if (pos, neg) in ((2, 0), (0, 2)):
            return "VII_0"
        if (pos, neg) in ((2, 1), (1, 2)):
            return "VIII"
        return "IX"
    h_val, a_sq, minor_perp = compute_regularized_h(a_ver2, n_ver2, tol=tol * tol)
    if (pos, neg) == (0, 0):
        return "V"
    if (pos, neg) in ((1, 0), (0, 1)):
        return "IV"
    if (pos, neg) == (1, 1):
        if h_val is not None and abs(h_val + 1.0) <= 1.0e-9:
            return "III"
        return "VI_h"
    if (pos, neg) in ((2, 0), (0, 2)):
        return "VII_h"
    raise ValueError(
        f"Inconsistent eigenvalues ({pos} pos, {neg} neg) with non-zero Class-B a={a_norm:.3e}"
    )


def structure_constants_to_ver2_algebra(
    sc: StructureConstants,
    *,
    use_proper_rotation: bool = True,
) -> BianchiAlgebra:
    """Convert `StructureConstants` (PC frame) to exact `BianchiAlgebra` (VER2 frame).

    Unlike `bianchi_types.get_family_spec('VI_h', h=-1)` which rejects `h = -1`,
    this converter cleanly handles Type `III`, `VI_{-1}`, and `VI_{-1/9}` directly
    through `BianchiAlgebra` without division by zero or relabeling errors.
    """
    target: Literal["ver2_proper", "ver2_improper"] = (
        "ver2_proper" if use_proper_rotation else "ver2_improper"
    )
    triple = structure_constants_to_triple(sc, target_frame=target, a_sign_out=1)
    C = triple.structure_tensor()
    perm = (0, 1, 2) if use_proper_rotation else (1, 0, 2)
    label = _infer_bianchi_type_name(triple.a, triple.n, requested_label=sc.label)
    canonical_for_policy = "I" if label == "FLRW" else label
    policy = build_bianchi_algebra(canonical_for_policy).branch_policy
    return BianchiAlgebra(
        type_name=canonical_for_policy if sc.label == "FLRW" else label,
        a=triple.a,
        n=triple.n,
        C=C,
        h_parameter=triple.h_parameter,
        class_label=triple.class_label,
        h_convention=(
            "Regularized h = a^2 / ((tr(n)^2 - tr(n^2))/2) in VER2 orthonormal frame "
            f"({'SO(3) proper' if use_proper_rotation else 'O(3) permutation det=-1'})"
        ),
        axis_permutation=perm,
        branch_policy=policy,
    )


def ver2_algebra_to_structure_constants(
    algebra: BianchiAlgebra,
    *,
    use_proper_rotation: bool = True,
) -> StructureConstants:
    """Invert VER2 `BianchiAlgebra` back to Pontzen-Challinor `StructureConstants`."""
    M = VER2_TO_PC_PROPER_ROTATION if use_proper_rotation else PC_TO_VER2_IMPROPER_PERMUTATION
    a_pc, n_pc, _ = transform_structure_pair(
        algebra.a, algebra.n, M, a_sign_in=1, a_sign_out=1
    )
    if np.linalg.norm(n_pc - np.diag(np.diag(n_pc))) > 1.0e-10:
        raise ValueError(
            "Only axis-aligned BianchiAlgebra instances map cleanly to diagonal StructureConstants"
        )
    a_twist = float(a_pc[1])
    if np.hypot(a_pc[0], a_pc[2]) > 1.0e-12:
        raise ValueError(
            f"Expected Class-B vector along axis 1 in PC frame, got a_pc={a_pc.tolist()}"
        )
    label = _infer_bianchi_type_name(algebra.a, algebra.n, requested_label=algebra.type_name)
    return StructureConstants(
        n1=float(n_pc[0, 0]),
        n2=float(n_pc[1, 1]),
        n3=float(n_pc[2, 2]),
        a_twist=a_twist,
        label=label,
        no_flrw_limit=(label in MARGINAL_TYPES),
    )


@dataclass(frozen=True)
class CanonicalBridgeReport:
    """Machine-readable dual-route verification report for one homogeneous family."""

    family: str
    class_label: str
    has_flrw_limit: bool
    equivalence_id: str
    a_ver2_proper: tuple[float, float, float]
    n_diag_ver2_proper: tuple[float, float, float]
    h_parameter: float | None
    special_locus: str | None
    jacobi_residual: float
    dual_route_ricci_error_ver2: float
    dual_route_ricci_error_random_so3: float
    dual_route_ricci_error_improper_o3: float
    momentum_divergence_identity_error: float
    lie_bracket_roundtrip_error: float
    pc_vs_ver2_proper_ricci_diff_after_rotation: float
    passed: bool


def verify_convention_bridge_family(
    family: str,
    *,
    h: float | None = None,
    seed: int = 20261115,
) -> CanonicalBridgeReport:
    """Verify Jacobi, exact compact Ricci, momentum divergence, and O(3) bridge."""
    if family == "FLRW":
        sc = StructureConstants(0.0, 0.0, 0.0, 0.0, label="FLRW", no_flrw_limit=False)
    elif family == "VI_h" and h is not None:
        # Handle arbitrary negative h cleanly, including h = -1 and h = -1/9!
        a_val = 0.005
        n1_val = 0.01
        n3_val = -(a_val ** 2) / (abs(float(h)) * n1_val) if float(h) < 0.0 else (a_val ** 2) / (float(h) * n1_val)
        sc_label = "III" if abs(float(h) + 1.0) < 1.0e-12 else ("VII_h" if float(h) > 0.0 else "VI_h")
        sc = StructureConstants(n1=n1_val, n2=0.0, n3=n3_val, a_twist=a_val, label=sc_label, no_flrw_limit=(float(h) <= 0.0))
    else:
        sc = get_type(family)

    triple_pc = structure_constants_to_triple(sc, target_frame="pontzen_challinor", a_sign_out=1)
    alg_ver2 = structure_constants_to_ver2_algebra(sc, use_proper_rotation=True)
    triple_ver2 = algebra_to_triple(alg_ver2)
    sc_back = ver2_algebra_to_structure_constants(alg_ver2, use_proper_rotation=True)
    triple_pc_back = structure_constants_to_triple(sc_back, target_frame="pontzen_challinor", a_sign_out=1)

    C_ver2 = triple_ver2.structure_tensor()
    R_conn_v2, _, _ = spatial_ricci_from_connection(C_ver2)
    R_comp_v2, _, _ = exact_spatial_ricci_from_compact(triple_ver2.a, triple_ver2.n, a_sign=1)
    ricci_err_v2 = float(np.max(np.abs(R_conn_v2 - R_comp_v2)))

    # Proper SO(3) test + relation to PC Ricci: R_ver2 == R_rot @ R_pc @ R_rot^T
    R_conn_pc, _, _ = spatial_ricci_from_connection(triple_pc.structure_tensor())
    M_prop = PC_TO_VER2_PROPER_ROTATION
    pc_rot_diff = float(np.max(np.abs(R_conn_v2 - M_prop @ R_conn_pc @ M_prop.T)))

    rng = np.random.default_rng(seed)
    Q, _ = np.linalg.qr(rng.normal(size=(3, 3)))
    if np.linalg.det(Q) < 0.0:
        Q[:, 0] *= -1.0
    a_so3, n_so3, _ = transform_structure_pair(triple_ver2.a, triple_ver2.n, Q, a_sign_in=1, a_sign_out=1)
    C_so3 = build_structure_tensor_with_sign(a_so3, n_so3, a_sign=1)
    R_conn_so3, _, _ = spatial_ricci_from_connection(C_so3)
    R_comp_so3, _, _ = exact_spatial_ricci_from_compact(a_so3, n_so3, a_sign=1)
    ricci_err_so3 = float(np.max(np.abs(R_conn_so3 - R_comp_so3)))

    # Improper O(3) transformation with opposite a_sign = -1 simultaneously!
    M_imp = Q.copy()
    M_imp[2, :] *= -1.0
    a_imp, n_imp, _ = transform_structure_pair(
        triple_ver2.a, triple_ver2.n, M_imp, a_sign_in=1, a_sign_out=-1
    )
    C_imp = build_structure_tensor_with_sign(a_imp, n_imp, a_sign=-1)
    R_conn_imp, _, _ = spatial_ricci_from_connection(C_imp)
    R_comp_imp, _, _ = exact_spatial_ricci_from_compact(a_imp, n_imp, a_sign=-1)
    ricci_err_imp = float(np.max(np.abs(R_conn_imp - R_comp_imp)))

    # Exact momentum divergence check across arbitrary symmetric trace-free sigma
    S_raw = rng.normal(size=(3, 3))
    S_pstf = pstf_rank2(0.5 * (S_raw + S_raw.T))
    Gamma_so3 = connection_from_commutators(C_so3)
    div_conn = div_pstf2(S_pstf, Gamma_so3)
    div_alg = exact_momentum_divergence(S_pstf, a_so3, n_so3, a_sign=1)
    div_err = float(np.max(np.abs(div_conn - div_alg)))

    roundtrip_err = float(np.max(np.abs(triple_pc.structure_tensor() - triple_pc_back.structure_tensor())))
    jac_res = triple_ver2.jacobi_residual()
    eq_set = action_equivalence_for_family(family)
    passed = (
        jac_res < 1.0e-14
        and ricci_err_v2 < 1.0e-14
        and ricci_err_so3 < 1.0e-14
        and ricci_err_imp < 1.0e-14
        and div_err < 1.0e-14
        and roundtrip_err < 1.0e-14
        and pc_rot_diff < 1.0e-14
    )
    return CanonicalBridgeReport(
        family=family,
        class_label=triple_ver2.class_label,
        has_flrw_limit=(family in TYPES_WITH_FLRW_LIMIT or family == "FLRW"),
        equivalence_id=eq_set.equivalence_id,
        a_ver2_proper=tuple(float(x) for x in triple_ver2.a),
        n_diag_ver2_proper=tuple(float(x) for x in np.diag(triple_ver2.n)),
        h_parameter=triple_ver2.h_parameter,
        special_locus=triple_ver2.is_special_class_b_locus(),
        jacobi_residual=jac_res,
        dual_route_ricci_error_ver2=ricci_err_v2,
        dual_route_ricci_error_random_so3=ricci_err_so3,
        dual_route_ricci_error_improper_o3=ricci_err_imp,
        momentum_divergence_identity_error=div_err,
        lie_bracket_roundtrip_error=roundtrip_err,
        pc_vs_ver2_proper_ricci_diff_after_rotation=pc_rot_diff,
        passed=passed,
    )


def verify_all_families_convention_bridge() -> dict[str, Any]:
    """Run convention bridge verification across all 12 families plus h=-1 and h=-1/9."""
    reports: dict[str, Any] = {}
    all_ok = True
    for fam in ALL_TWELVE_FAMILIES:
        rep = verify_convention_bridge_family(fam)
        reports[fam] = rep.__dict__
        all_ok = all_ok and rep.passed
    for label, h_val in (("VI_minus_1_equals_III", -1.0), ("VI_minus_1_over_9", -1.0 / 9.0)):
        rep = verify_convention_bridge_family("VI_h", h=h_val)
        reports[label] = rep.__dict__
        all_ok = all_ok and rep.passed
    return {
        "all_passed": all_ok,
        "families_tested": list(reports.keys()),
        "equivalence_classes": {
            k: {
                "equivalence_id": v.equivalence_id,
                "member_families": list(v.member_families),
                "spatial_curvature_sign": v.spatial_curvature_sign,
                "has_flrw_limit": v.has_flrw_limit,
            }
            for k, v in BIANCHI_ACTION_EQUIVALENCE_CLASSES.items()
        },
        "reports": reports,
    }
