"""
bass/background/bianchi_types.py  (v4.0 extension)
===================================================

Bianchi type classification with all 10 types + FLRW.

Extends the v3.0 skeleton (I, V, VII_h, IX) to the complete classification:
  Class A (a_twist = 0): I, II, VI_0, VII_0, VIII, IX
  Class B (a_twist ≠ 0): III, IV, V, VI_h, VII_h

Convention
----------
Following Pontzen & Challinor (PRD 79, 103518, 2009; arXiv:0901.2122), we
use the frame where a_α = (0, a, 0) so that the Jacobi constraint
n^{αβ} a_β = 0 implies n₂ = 0 for Class B. This differs from the "canonical"
Ellis-MacCallum frame (a along axis 1, n₁ = 0) by an SO(3) rotation; the
physics is invariant.

Canonical sign pattern (after automorphism scaling)
-----------------------------------------------------

  Type         Class   a    (n₁, n₂, n₃)         h                FLRW limit
  I            A       0    (0, 0, 0)            —                k = 0
  II           A       0    (+, 0, 0)            —                —
  VI₀          A       0    (+, 0, −)            —                —         [= h→0⁻ of VI_h]
  VII₀         A       0    (+, 0, +)            —                k = 0     [= h→0⁺ of VII_h]
  VIII         A       0    (−, +, +)            —                —
  IX           A       0    (+, +, +)            —                k = +1
  V            B       +    (0, 0, 0)            —                k = −1
  IV           B       +    (0, 0, +)            —                NONE      [Class B, no FLRW limit]
  III          B       +    (+, 0, −)            −1               —         [= VI_{-1}]
  VI_h         B       +    (+, 0, −)            h ∈ (−∞,−1)∪(−1,0)  —
  VII_h        B       +    (+, 0, +)            h > 0            k = −1

The group parameter h = a² / (n₁ n₃) is defined when n₁ n₃ ≠ 0.

References
----------
  Ellis & MacCallum, Commun. Math. Phys. 12, 108 (1969)
  Wainwright & Ellis, Dynamical Systems in Cosmology (CUP, 1997)
  Pontzen & Challinor, PRD 79, 103518 (2009)
  Krasiński et al., Gen. Rel. Grav. 35, 475 (2003)  [proper attribution]
  /mnt/project/bianchi_background_survey_v2.md §A
  ch04_bianchi_bounds.tex §sec:nine-types
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal, Optional, Tuple

import numpy as np


_IDENTITY_AXIS_PERMUTATION = (0, 1, 2)
_PC_TO_VER2_CLASS_B_AXIS_PERMUTATION = (1, 0, 2)


@dataclass(frozen=True)
class BianchiBranchPolicy:
    """Branch-admissibility metadata for the common VER2 backend.

    The packet SSOT requires every algebra object to carry explicit branch
    metadata rather than letting downstream modules infer it from type-name
    conditionals. The strings below are intentionally policy labels, not
    runtime allow/block booleans owned by a different package.
    """

    orthogonal_allowed: bool
    tilted_allowed: bool
    constraint_policy_required: str


@dataclass(frozen=True)
class BianchiAlgebra:
    """Canonical VER2 algebra object for all eleven Bianchi types.

    This is the skeleton/contract surface requested by `SK-01S1`. It sits
    alongside the older `StructureConstants` helper without replacing it, so
    reduced pre-VER2 paths can continue to import `StructureConstants` until
    the full solver packets land.

    Conventions follow `docs/ver2_upgrade/*`:
    - Class-A/B metadata is explicit.
    - The canonical class-B axis places `a_alpha` on the first axis.
    - The sign convention for `h` is recorded in metadata.
    - All later solver modules should consume only `(a, n, C)` and branch
      metadata, not handwritten type-name logic.
    """

    type_name: str
    a: np.ndarray
    n: np.ndarray
    C: np.ndarray
    h_parameter: float | None
    class_label: Literal["A", "B"]
    h_convention: str
    axis_permutation: Tuple[int, int, int]
    branch_policy: BianchiBranchPolicy

    def __post_init__(self) -> None:
        a = np.asarray(self.a, dtype=np.float64)
        n = np.asarray(self.n, dtype=np.float64)
        C = np.asarray(self.C, dtype=np.float64)
        if a.shape != (3,):
            raise ValueError(f"BianchiAlgebra.a must have shape (3,), got {a.shape}")
        if n.shape != (3, 3):
            raise ValueError(f"BianchiAlgebra.n must have shape (3,3), got {n.shape}")
        if C.shape != (3, 3, 3):
            raise ValueError(f"BianchiAlgebra.C must have shape (3,3,3), got {C.shape}")
        object.__setattr__(self, "a", a)
        object.__setattr__(self, "n", n)
        object.__setattr__(self, "C", C)
        self.validate()

    @property
    def jacobi_violation(self) -> np.ndarray:
        return self.n @ self.a

    @property
    def jacobi_residual_norm(self) -> float:
        return float(np.linalg.norm(self.jacobi_violation))

    @property
    def antisymmetry_residual_norm(self) -> float:
        return float(np.max(np.abs(self.C + np.swapaxes(self.C, 1, 2))))

    def supports_branch(self, branch: Literal["orthogonal", "tilted"]) -> bool:
        if branch == "orthogonal":
            return self.branch_policy.orthogonal_allowed
        if branch == "tilted":
            return self.branch_policy.tilted_allowed
        raise KeyError(f"Unknown branch {branch!r}")

    def validate(self, *, atol: float = 1e-12) -> None:
        if not np.allclose(self.n, self.n.T, atol=atol):
            raise ValueError(f"{self.type_name}: n must be symmetric in the VER2 contract")
        if self.antisymmetry_residual_norm > atol:
            raise ValueError(
                f"{self.type_name}: C^gamma_(alpha beta) must be antisymmetric in "
                f"lower indices; residual={self.antisymmetry_residual_norm:.3e}"
            )
        if self.jacobi_residual_norm > atol:
            raise ValueError(
                f"{self.type_name}: Jacobi residual ||n @ a||={self.jacobi_residual_norm:.3e} "
                f"exceeds tolerance {atol:.1e}"
            )


@dataclass(frozen=True)
class FamilySpec:
    """Registry-level family metadata frozen by ver3 PR-02."""

    family: str
    algebra: BianchiAlgebra
    class_label: Literal["A", "B"]
    isotropic_anchor: bool
    orthogonal_global_tilt_local_boost_split: Literal["frozen"]
    preferred_backend: str
    generic_fallback: str
    ic_provenance_status: Literal["strong", "residual-backed", "template-card"]
    canonical_gauge: str
    release_status: Literal["registry-complete"]

    def as_metadata_dict(self) -> dict[str, object]:
        return {
            "family": self.family,
            "class_label": self.class_label,
            "isotropic_anchor": self.isotropic_anchor,
            "orthogonal_global_tilt_local_boost_split": self.orthogonal_global_tilt_local_boost_split,
            "preferred_backend": self.preferred_backend,
            "generic_fallback": self.generic_fallback,
            "ic_provenance_status": self.ic_provenance_status,
            "canonical_gauge": self.canonical_gauge,
            "release_status": self.release_status,
            "h_parameter": self.algebra.h_parameter,
            "constraint_policy_required": self.algebra.branch_policy.constraint_policy_required,
        }


def _epsilon_3d() -> np.ndarray:
    eps = np.zeros((3, 3, 3), dtype=np.float64)
    eps[0, 1, 2] = eps[1, 2, 0] = eps[2, 0, 1] = +1.0
    eps[0, 2, 1] = eps[2, 1, 0] = eps[1, 0, 2] = -1.0
    return eps


def build_structure_tensor(a_vec: np.ndarray, n_mat: np.ndarray) -> np.ndarray:
    """Build `C^gamma_{alpha beta}` from the VER2 `(a, n)` split."""
    a = np.asarray(a_vec, dtype=np.float64)
    n = np.asarray(n_mat, dtype=np.float64)
    delta = np.eye(3, dtype=np.float64)
    eps = _epsilon_3d()
    C = np.zeros((3, 3, 3), dtype=np.float64)
    for gamma in range(3):
        for alpha in range(3):
            for beta in range(3):
                term_a = a[alpha] * delta[beta, gamma] - a[beta] * delta[alpha, gamma]
                term_n = float(np.sum(eps[alpha, beta, :] * n[:, gamma]))
                C[gamma, alpha, beta] = term_a + term_n
    return C


def _branch_policy_for_type(label: str) -> BianchiBranchPolicy:
    policies = {
        "I": BianchiBranchPolicy(True, True, "codazzi_balanced_total_momentum"),
        "II": BianchiBranchPolicy(True, True, "codazzi_project_shear_or_tilt"),
        "III": BianchiBranchPolicy(True, True, "class_b_codazzi_projection"),
        "IV": BianchiBranchPolicy(True, True, "class_b_codazzi_projection"),
        "V": BianchiBranchPolicy(True, True, "class_b_divergence_tilt_coupling"),
        "VI_0": BianchiBranchPolicy(True, True, "class_a_zero_flux_or_codazzi"),
        "VI_h": BianchiBranchPolicy(True, True, "class_b_generic_h_constraint"),
        "VII_0": BianchiBranchPolicy(True, True, "class_a_helical_codazzi"),
        "VII_h": BianchiBranchPolicy(True, True, "class_b_helical_codazzi"),
        "VIII": BianchiBranchPolicy(True, True, "class_a_semisimple_codazzi"),
        "IX": BianchiBranchPolicy(True, True, "config_domain_restricted_tilt"),
        "FLRW": BianchiBranchPolicy(True, True, "flat_zero_flux"),
    }
    return policies[label]


def build_bianchi_algebra(label: str, **kwargs) -> BianchiAlgebra:
    """Return the canonical VER2 algebra object for one type label.

    Legacy `StructureConstants` use the Pontzen-Challinor class-B frame
    (`a_alpha = (0,a,0)`). The VER2 solver docs instead freeze the canonical
    class-B axis as `a_alpha = (a,0,0)`. This builder performs that axis
    reconciliation once and stores the permutation explicitly so downstream
    packets do not need to remember both conventions.
    """

    sc = get_type(label, **kwargs)
    if sc.is_class_a:
        a = np.zeros(3, dtype=np.float64)
        n = np.diag([sc.n1, sc.n2, sc.n3]).astype(np.float64)
        axis_permutation = _IDENTITY_AXIS_PERMUTATION
    else:
        a = np.array([sc.a_twist, 0.0, 0.0], dtype=np.float64)
        n = np.diag([0.0, sc.n1, sc.n3]).astype(np.float64)
        axis_permutation = _PC_TO_VER2_CLASS_B_AXIS_PERMUTATION
    C = build_structure_tensor(a, n)
    h_parameter = None if label in {"FLRW", "I", "II", "IV", "V", "VI_0", "VII_0", "VIII", "IX"} else sc.h_parameter
    return BianchiAlgebra(
        type_name=label,
        a=a,
        n=n,
        C=C,
        h_parameter=h_parameter,
        class_label="A" if sc.is_class_a else "B",
        h_convention="h = a^2/(n2*n3) in canonical VER2 class-B axes",
        axis_permutation=axis_permutation,
        branch_policy=_branch_policy_for_type(label),
    )


def all_bianchi_algebras() -> dict[str, BianchiAlgebra]:
    """Build the full 11-type VER2 algebra registry plus FLRW."""
    return {label: build_bianchi_algebra(label) for label in ["FLRW", *ALL_BIANCHI_TYPES]}


_PREFERRED_BACKEND = {
    "FLRW": "isotropic_trivial",
    "I": "plane_wave_cartesian",
    "II": "nil_heisenberg",
    "III": "class_b_hyperbolic_branch",
    "IV": "solvable_group_chart",
    "V": "hyperbolic_open_modes",
    "VI_0": "solvable_intrinsic_modes",
    "VI_h": "class_b_negative_h_modes",
    "VII_0": "helical_euclidean_modes",
    "VII_h": "helical_open_positive_h_modes",
    "VIII": "sl2r_noncompact_backend",
    "IX": "wigner_d_compact_backend",
}

_IC_PROVENANCE_STATUS = {
    "FLRW": "strong",
    "I": "strong",
    "II": "residual-backed",
    "III": "residual-backed",
    "IV": "residual-backed",
    "V": "strong",
    "VI_0": "residual-backed",
    "VI_h": "residual-backed",
    "VII_0": "strong",
    "VII_h": "strong",
    "VIII": "residual-backed",
    "IX": "strong",
}

_ISOTROPIC_ANCHORS = {"FLRW", "I", "V", "VII_0", "VII_h", "IX"}


def _build_h_consistent_class_b_algebra(label: str, h: float) -> BianchiAlgebra:
    n1 = 1.0e-2
    if label == "VI_h":
        if h >= 0.0 or abs(h + 1.0) < 1.0e-6:
            raise ValueError("VI_h requires h < 0 and h != -1")
        n3 = -1.0e-2
        a_twist = math.sqrt(abs(h * n1 * n3))
        return build_bianchi_algebra(label, n1=n1, n3=n3, a_twist=a_twist)
    if label == "VII_h":
        if h <= 0.0:
            raise ValueError("VII_h requires h > 0")
        n3 = 1.0e-2
        a_twist = math.sqrt(h * n1 * n3)
        return build_bianchi_algebra(label, n1=n1, n3=n3, a_twist=a_twist)
    raise ValueError(f"h-override is not supported for {label}")


def get_family_spec(name: str, h: float | None = None) -> FamilySpec:
    """Return the canonical ver3 registry contract for one family.

    ``h`` overrides are only legal for the class-B continuous families
    ``VI_h`` and ``VII_h``. All other families are branch-fixed.
    """

    if h is not None and name not in {"VI_h", "VII_h"}:
        raise ValueError(f"h override is only supported for VI_h/VII_h, not {name}")
    algebra = _build_h_consistent_class_b_algebra(name, h) if h is not None else build_bianchi_algebra(name)
    return FamilySpec(
        family=name,
        algebra=algebra,
        class_label=algebra.class_label,
        isotropic_anchor=name in _ISOTROPIC_ANCHORS,
        orthogonal_global_tilt_local_boost_split="frozen",
        preferred_backend=_PREFERRED_BACKEND[name],
        generic_fallback="generic_collocation",
        ic_provenance_status=_IC_PROVENANCE_STATUS[name],
        canonical_gauge=(
            "class_b_axis_a=(a,0,0), n=diag(0,n2,n3)"
            if algebra.class_label == "B"
            else "class_a_axis_identity"
        ),
        release_status="registry-complete",
    )


def all_family_specs() -> dict[str, FamilySpec]:
    """Return the registry-complete family contract table for FLRW + all eleven types."""

    return {label: get_family_spec(label) for label in ["FLRW", *ALL_BIANCHI_TYPES]}


def rescale_bianchi_algebra(algebra: BianchiAlgebra, scale: float) -> BianchiAlgebra:
    """Return a uniformly rescaled algebra with unchanged type metadata.

    The VER2 Hamiltonian closure can solve for a single algebra scale while
    preserving the Bianchi type and the group parameter ``h``. Under this
    uniform rescaling, ``a_alpha``, ``n_ab``, and ``C^gamma_{alpha beta}``
    all scale linearly, while branch metadata and axis conventions remain
    unchanged.
    """

    factor = float(scale)
    if factor < 0.0:
        raise ValueError(f"algebra scale must be non-negative; got {scale!r}")
    return BianchiAlgebra(
        type_name=algebra.type_name,
        a=algebra.a * factor,
        n=algebra.n * factor,
        C=algebra.C * factor,
        h_parameter=algebra.h_parameter,
        class_label=algebra.class_label,
        h_convention=algebra.h_convention,
        axis_permutation=algebra.axis_permutation,
        branch_policy=algebra.branch_policy,
    )

@dataclass(frozen=True)
class StructureConstants:
    """Bianchi group structure constants in the Pontzen-Challinor frame.

    Parameters
    ----------
    n1, n2, n3 : float
        Diagonal structure constants. Class B convention: n₂ = 0.
    a_twist : float
        Twist parameter. a = 0 for Class A (I, II, VI₀, VII₀, VIII, IX);
        a ≠ 0 for Class B (III, IV, V, VI_h, VII_h).
    label : str
        Human-readable Bianchi type label.
    no_flrw_limit : bool
        True for types that admit no FLRW limit (II, III, IV, VI₀, VI_h, VIII).
        These are cosmologically marginal but still evaluable within the master
        departure identity; x_C is well-defined even if there is no ΛCDM limit
        to compare against.
    """
    n1: float = 0.0
    n2: float = 0.0
    n3: float = 0.0
    a_twist: float = 0.0
    label: str = "unspecified"
    no_flrw_limit: bool = False

    # ── Algebraic properties ─────────────────────────────────

    @property
    def is_class_a(self) -> bool:
        """Class A: a_twist = 0 (unimodular group)."""
        return abs(self.a_twist) < 1e-15

    @property
    def is_class_b(self) -> bool:
        return not self.is_class_a

    @property
    def h_parameter(self) -> float:
        """Group parameter h = a²/(n₁ n₃). Defined when n₁ n₃ ≠ 0.

        Types III (h = −1), VI_h (h ∈ (−∞,−1)∪(−1,0)), VII_h (h > 0).
        Returns 0 if undefined.
        """
        if abs(self.n1) < 1e-30 or abs(self.n3) < 1e-30:
            return 0.0
        return self.a_twist ** 2 / (self.n1 * self.n3)

    @property
    def sqrt_h(self) -> float:
        """√h where h is the group parameter. Used in VII_h simplified advection."""
        hp = self.h_parameter
        return math.sqrt(hp) if hp > 0 else 0.0

    @property
    def delta_n(self) -> float:
        """Δn ≡ n₃ - n₁. Enters the harmonic advection recurrence."""
        return self.n3 - self.n1

    @property
    def trace_n(self) -> float:
        """n₁ + n₂ + n₃. Used in spatial Ricci scalar construction."""
        return self.n1 + self.n2 + self.n3

    @property
    def n_diag(self) -> Tuple[float, float, float]:
        return (self.n1, self.n2, self.n3)

    # ── Jacobi identity validation ──────────────────────────

    def jacobi_residual(self) -> float:
        """The Jacobi identity requires n^{αβ} a_β = 0.

        In our frame a_β = (0, a_twist, 0), so:
            (n^{αβ} a_β)_α = (n_{α2}) a_twist  for each α
        With n_{αβ} diagonal, only the α = 2 component is nonzero:
            residual = n_2 × a_twist

        For Class A (a_twist = 0) or when n_2 = 0, residual = 0.

        Returns
        -------
        float
            Residual |n_{2} × a_twist|. Should be 0 for all valid Bianchi types.
        """
        return abs(self.n2 * self.a_twist)

    def validate(self) -> None:
        """Raise ValueError if the structure constants violate Jacobi identity."""
        res = self.jacobi_residual()
        if res > 1e-12:
            raise ValueError(
                f"Jacobi identity violated for type {self.label}: "
                f"n_2 × a_twist = {res:.3e} ≠ 0 "
                f"(n_2 = {self.n2}, a_twist = {self.a_twist})"
            )

    # ── Curvature character ─────────────────────────────────

    @property
    def spatial_ricci_sign(self) -> int:
        """Sign of the spatial Ricci scalar ³R (from the group character).

        Returns +1 (closed), -1 (open), or 0 (flat). Approximate — the exact
        sign depends on the relative magnitudes for VIII and mixed-sign types.
        """
        n1, n2, n3 = self.n_diag
        a = self.a_twist
        # Flat: all zero or Type V-like (all n_i = 0, a > 0 gives negative curvature via a²)
        if abs(n1) < 1e-30 and abs(n2) < 1e-30 and abs(n3) < 1e-30:
            if abs(a) < 1e-30:
                return 0  # Type I (flat)
            else:
                return -1  # Type V (open)
        # IX: all n_i > 0
        if n1 > 0 and n2 > 0 and n3 > 0:
            return +1
        # VIII, VI₀, VI_h, III: mixed signs → typically negative or open
        # VII₀, VII_h: (+, 0, +) → can be flat or negative depending on h
        if n1 * n3 < 0:  # VI family
            return -1
        return -1  # default for mixed sign


# ──────────────────────────────────────────────────────────────
# Factory functions — all 10 Bianchi types + FLRW
# ──────────────────────────────────────────────────────────────

def flrw_constants() -> StructureConstants:
    """FLRW: all structure constants zero (flat spatial sections)."""
    return StructureConstants(
        n1=0.0, n2=0.0, n3=0.0, a_twist=0.0,
        label="FLRW", no_flrw_limit=False,
    )


# ── Class A types (a_twist = 0) ─────────────────────────────

def type_i_constants() -> StructureConstants:
    """Type I: abelian group, flat anisotropic (Kasner-like).

    (n₁, n₂, n₃) = (0, 0, 0), a = 0. Simplest anisotropic model.
    No spatial curvature, no advection, no polarization rotation.
    FLRW limit: k = 0 (σ → 0).
    """
    return StructureConstants(
        n1=0.0, n2=0.0, n3=0.0, a_twist=0.0,
        label="I", no_flrw_limit=False,
    )


def type_ii_constants(n1: float = 1.0e-2) -> StructureConstants:
    """Type II: Heisenberg group.

    (n₁, n₂, n₃) = (+, 0, 0), a = 0.
    Spatial curvature from n₁ alone. No FLRW limit.

    Parameters
    ----------
    n1 : float
        Positive eigenvalue (default small for near-FLRW behaviour).
    """
    if n1 <= 0:
        raise ValueError(f"Type II requires n1 > 0, got n1 = {n1}")
    return StructureConstants(
        n1=n1, n2=0.0, n3=0.0, a_twist=0.0,
        label="II", no_flrw_limit=True,
    )


def type_vi0_constants(n1: float = 1.0e-2, n3: float = -1.0e-2) -> StructureConstants:
    """Type VI₀: e(1,1) Lie algebra.

    (n₁, n₂, n₃) = (+, 0, −), a = 0. Mixed-sign Class A.
    Equivalent to h → 0⁻ limit of VI_h. No FLRW limit.

    Parameters
    ----------
    n1 : float
        Positive eigenvalue.
    n3 : float
        Negative eigenvalue.
    """
    if n1 <= 0 or n3 >= 0:
        raise ValueError(f"Type VI₀ requires n1 > 0 and n3 < 0, got n1={n1}, n3={n3}")
    return StructureConstants(
        n1=n1, n2=0.0, n3=n3, a_twist=0.0,
        label="VI_0", no_flrw_limit=True,
    )


def type_vii0_constants(n1: float = 1.0e-2, n3: float = 1.0e-2) -> StructureConstants:
    """Type VII₀: e(2) Lie algebra (Euclidean group).

    (n₁, n₂, n₃) = (+, 0, +), a = 0. Both positive, Class A.
    Equivalent to h → 0⁺ limit of VII_h. FLRW limit: k = 0.

    Parameters
    ----------
    n1, n3 : float
        Both positive eigenvalues.
    """
    if n1 <= 0 or n3 <= 0:
        raise ValueError(f"Type VII₀ requires n1 > 0 and n3 > 0, got n1={n1}, n3={n3}")
    return StructureConstants(
        n1=n1, n2=0.0, n3=n3, a_twist=0.0,
        label="VII_0", no_flrw_limit=False,
    )


def type_viii_constants(
    n1: float = -1.0e-2, n2: float = 1.0e-2, n3: float = 1.0e-2
) -> StructureConstants:
    """Type VIII: sl(2,ℝ) Lie algebra.

    (n₁, n₂, n₃) = (−, +, +), a = 0. One negative eigenvalue. Class A.
    No FLRW limit. Note: n₂ ≠ 0 for this type (departs from "n₂ = 0" convention
    for Class B, but Class A has no Jacobi constraint forcing n₂ = 0).
    """
    if n1 >= 0 or n2 <= 0 or n3 <= 0:
        raise ValueError(
            f"Type VIII requires n1 < 0, n2 > 0, n3 > 0, got n1={n1}, n2={n2}, n3={n3}"
        )
    return StructureConstants(
        n1=n1, n2=n2, n3=n3, a_twist=0.0,
        label="VIII", no_flrw_limit=True,
    )


def type_ix_constants(n: float = 1.0e-2) -> StructureConstants:
    """Type IX: so(3) Lie algebra (Mixmaster model).

    (n₁, n₂, n₃) = (+, +, +), a = 0. Closed universe. FLRW limit: k = +1.

    Default choice n₁ = n₂ = n₃ corresponds to the isotropic BKL background.
    """
    if n <= 0:
        raise ValueError(f"Type IX requires n > 0, got n = {n}")
    return StructureConstants(
        n1=n, n2=n, n3=n, a_twist=0.0,
        label="IX", no_flrw_limit=False,
    )


# ── Class B types (a_twist ≠ 0, n₂ = 0 from Jacobi) ────────

def type_v_constants(a_twist: float = 1.0e-2) -> StructureConstants:
    """Type V: open FLRW analogue, maximally symmetric.

    (n₁, n₂, n₃) = (0, 0, 0), a ≠ 0. No n_i contribution.
    FLRW limit: k = −1 (σ → 0).

    Parameters
    ----------
    a_twist : float
        Positive twist parameter. Unit normalized to 1.0 in some conventions;
        we keep it as an explicit parameter.
    """
    if a_twist <= 0:
        raise ValueError(f"Type V requires a_twist > 0, got a_twist = {a_twist}")
    return StructureConstants(
        n1=0.0, n2=0.0, n3=0.0, a_twist=a_twist,
        label="V", no_flrw_limit=False,
    )


def type_iv_constants(
    n3: float = 1.0e-2, a_twist: float = 1.0e-2
) -> StructureConstants:
    """Type IV: Class B, (0, 0, +), a ≠ 0.

    CRITICAL: Type IV admits NO FLRW limit. It is cosmologically marginal
    (ch04 §sec:classAB notes it does not admit an FLRW limit). However, the
    master departure identity x_C = Σ² - W² + Ω_tilt + Ω_{k,aniso} remains
    well-defined for this type, and it serves as a cross-falsifiability probe:
    the pipeline should return decisively negative ln B for Type IV because
    the data are close to FLRW.

    Parameters
    ----------
    n3 : float
        Positive eigenvalue.
    a_twist : float
        Positive twist parameter.
    """
    if n3 <= 0 or a_twist <= 0:
        raise ValueError(
            f"Type IV requires n3 > 0 and a_twist > 0, got n3={n3}, a_twist={a_twist}"
        )
    return StructureConstants(
        n1=0.0, n2=0.0, n3=n3, a_twist=a_twist,
        label="IV", no_flrw_limit=True,
    )


def type_iii_constants(
    n1: float = 1.0e-2, a_twist: Optional[float] = None
) -> StructureConstants:
    """Type III = VI_{-1}: special case of VI_h with h = −1.

    (n₁, n₂, n₃) = (+, 0, −), a ≠ 0. h = a²/(n₁ n₃) = −1 enforced.
    No FLRW limit. Class B.

    Parameters
    ----------
    n1 : float
        Positive eigenvalue.
    a_twist : float, optional
        If None, derived from h = -1: a_twist = √(-n1 × n3) = √(n1 × |n3|).
        The enforced constraint is n3 = -a_twist²/n1.
    """
    if n1 <= 0:
        raise ValueError(f"Type III requires n1 > 0, got n1 = {n1}")
    if a_twist is None:
        # Default: match |n3| = n1 so h = a²/(n1 × -n1) requires a² = n1²
        a_twist = n1
    # Enforce h = -1: n3 = -a² / n1
    n3 = -(a_twist ** 2) / n1
    return StructureConstants(
        n1=n1, n2=0.0, n3=n3, a_twist=a_twist,
        label="III", no_flrw_limit=True,
    )


def type_vih_constants(
    n1: float = 1.0e-2, n3: float = -2.0e-3, a_twist: float = 5.0e-3
) -> StructureConstants:
    """Type VI_h: Class B, (+, 0, −), a ≠ 0, h < 0 and h ≠ −1.

    Parameters (n1, n3, a_twist) must satisfy h = a²/(n₁ n₃) ∈ (−∞, −1) ∪ (−1, 0).
    No FLRW limit. Distinct from Type III (h = −1).

    Parameters
    ----------
    n1 : float
        Positive eigenvalue.
    n3 : float
        Negative eigenvalue.
    a_twist : float
        Positive twist parameter. Chosen so h ≠ −1.
    """
    if n1 <= 0 or n3 >= 0 or a_twist <= 0:
        raise ValueError(
            f"Type VI_h requires n1 > 0, n3 < 0, a_twist > 0, "
            f"got n1={n1}, n3={n3}, a_twist={a_twist}"
        )
    sc = StructureConstants(
        n1=n1, n2=0.0, n3=n3, a_twist=a_twist,
        label="VI_h", no_flrw_limit=True,
    )
    h = sc.h_parameter
    if abs(h + 1.0) < 1e-6:
        raise ValueError(
            f"Type VI_h requires h ≠ −1 (h = −1 is Type III). Got h = {h:.4f}. "
            f"Adjust (n1, n3, a_twist) so a²/(n1 n3) ≠ −1."
        )
    return sc


def type_viih_constants(
    n1: float = 1.8e-2, n3: float = 1.0e-2, a_twist: float = 5.5e-3
) -> StructureConstants:
    """Type VII_h: Class B, (+, 0, +), a ≠ 0, h > 0.

    The principal CMB Bianchi type — produces spiral patterns.
    FLRW limit: k = −1 (sending σ → 0).

    Default values from Pontzen & Challinor (2007) "close-to-FRW" model, giving
    h = a²/(n1 n3) = (5.5e-3)² / (1.8e-2 × 1.0e-2) = 0.168.

    Parameters
    ----------
    n1, n3 : float
        Both positive eigenvalues.
    a_twist : float
        Positive twist parameter.
    """
    if n1 <= 0 or n3 <= 0 or a_twist <= 0:
        raise ValueError(
            f"Type VII_h requires n1 > 0, n3 > 0, a_twist > 0, "
            f"got n1={n1}, n3={n3}, a_twist={a_twist}"
        )
    return StructureConstants(
        n1=n1, n2=0.0, n3=n3, a_twist=a_twist,
        label="VII_h", no_flrw_limit=False,
    )


# ──────────────────────────────────────────────────────────────
# Type registry and lookup
# ──────────────────────────────────────────────────────────────

TYPE_REGISTRY = {
    "FLRW":   flrw_constants,
    "I":      type_i_constants,
    "II":     type_ii_constants,
    "III":    type_iii_constants,
    "IV":     type_iv_constants,
    "V":      type_v_constants,
    "VI_0":   type_vi0_constants,
    "VI_h":   type_vih_constants,
    "VII_0":  type_vii0_constants,
    "VII_h":  type_viih_constants,
    "VIII":   type_viii_constants,
    "IX":     type_ix_constants,
}

ALL_BIANCHI_TYPES = [
    "I", "II", "III", "IV", "V", "VI_0", "VI_h", "VII_0", "VII_h", "VIII", "IX"
]

CLASS_A_TYPES = ["I", "II", "VI_0", "VII_0", "VIII", "IX"]
CLASS_B_TYPES = ["III", "IV", "V", "VI_h", "VII_h"]

# Types that admit an FLRW limit (for comparator analysis)
TYPES_WITH_FLRW_LIMIT = ["I", "V", "VII_0", "VII_h", "IX"]

# Types flagged as cosmologically marginal (no FLRW limit)
MARGINAL_TYPES = ["II", "III", "IV", "VI_0", "VI_h", "VIII"]


def get_type(label: str, **kwargs) -> StructureConstants:
    """Look up a Bianchi type factory by label.

    Parameters
    ----------
    label : str
        Bianchi type label. One of: FLRW, I, II, III, IV, V, VI_0, VI_h,
        VII_0, VII_h, VIII, IX.
    **kwargs
        Keyword arguments forwarded to the factory (e.g., n1, n3, a_twist).

    Returns
    -------
    StructureConstants
        Validated structure constants. Raises if Jacobi identity violated.
    """
    if label not in TYPE_REGISTRY:
        raise KeyError(
            f"Unknown Bianchi type '{label}'. Valid labels: {list(TYPE_REGISTRY)}"
        )
    sc = TYPE_REGISTRY[label](**kwargs)
    sc.validate()
    return sc
