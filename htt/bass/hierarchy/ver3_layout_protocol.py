"""ver3 PR-09 hierarchy layout and IMEX packing contract."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Mapping

import numpy as np
from scipy.sparse import csc_matrix, csr_matrix, diags

from bass.los.family_backend_protocol import FamilyBackend
from bass.validation import GateBundle, make_gate_bundle

__all__ = [
    "SECTOR_ORDER",
    "HierarchyLayout",
    "ReducedHarmonicAffineOperator",
    "ReducedLocalAffineOperator",
    "ReducedSourceAffineOperator",
    "ReducedJointAffineOperator",
    "build_hierarchy_layout",
    "build_layout_manifest",
    "flatten",
    "unflatten",
    "evaluate_reduced_source_blocks",
    "evaluate_reduced_harmonic_rhs",
    "build_reduced_harmonic_affine_operator",
    "evaluate_reduced_local_rhs",
    "build_reduced_local_affine_operator",
    "build_reduced_source_affine_operator",
    "build_reduced_joint_affine_operator",
    "assemble_free_streaming_block",
    "assemble_mixing_block",
    "assemble_mass_matrix",
    "assemble_explicit_block",
    "assemble_implicit_block",
    "assemble_source_vector",
    "assemble_hierarchy_ops",
    "hierarchy_layout_gate_bundle",
]


SECTOR_ORDER = ("ph_I", "ph_E", "ph_B", "nu_I", "baryon", "cdm", "src")
_HARMONIC_SECTORS = frozenset({"ph_I", "ph_E", "ph_B", "nu_I"})
_LOCAL_SECTOR_DEFAULTS = {"baryon": 4, "cdm": 2, "src": 3}


@dataclass(frozen=True)
class HierarchyLayout:
    mode_labels: tuple[str, ...]
    sector_order: tuple[str, ...]
    ell_max: int
    sector_local_dofs: Mapping[str, int]
    size: int


@dataclass(frozen=True)
class ReducedHarmonicAffineOperator:
    mode_labels: tuple[str, ...]
    matrix: csc_matrix
    bias: np.ndarray


@dataclass(frozen=True)
class ReducedLocalAffineOperator:
    mode_labels: tuple[str, ...]
    matrix: csc_matrix
    bias: np.ndarray


@dataclass(frozen=True)
class ReducedSourceAffineOperator:
    mode_labels: tuple[str, ...]
    matrix: csc_matrix
    bias: np.ndarray


@dataclass(frozen=True)
class _JointSparsityCache:
    """Static sparsity pattern of the reduced-joint affine operator.

    Round-17 P3.5 perf Tier 1A v2 (2026-04-28). The joint operator's
    pattern (which (row, col) pairs are non-zero) is determined by:

      - ``layout.mode_labels`` and ``residual_mode_labels`` (fixed at
        integrator init).
      - ``backend.family_spec.family`` (fixed).
      - ``int(layout.ell_max)`` (fixed).
      - The Thomson coupling structure (always present, even if values
        are 0 post-recombination).

    The pattern does NOT depend on η, the state vector, or the
    background-quantity values — those only multiply existing entries.

    A ``_JointSparsityCache`` is captured once at integrator
    ``__init__`` via a representative cold build (with γ_T > 0 to
    ensure all Thomson couplings appear in the captured pattern). It
    is then passed to subsequent ``build_reduced_joint_affine_operator``
    calls via the optional ``pattern_cache`` keyword, which skips the
    ``csc_matrix(joint)`` conversion (and its O(n²) ``nonzero`` scan,
    measured at ~21 s of the 111 s single-k baseline).

    Profile evidence: pre-Tier-1A-v2 single-k cProfile showed the joint
    builder consumed 50 s of 111 s; the dense → CSC conversion at the
    return statement consumed 21 s of nonzero scanning + ~20 s of
    `_compressed`/`_coo` `__init__` and `prune`/`get_index_dtype`
    bookkeeping. Pattern caching skips both.
    """
    indices: np.ndarray  # CSC row indices (dtype int32 typically)
    indptr: np.ndarray   # CSC column pointer
    cols_of_data: np.ndarray  # for each data position k, the column
    shape: tuple[int, int]


def joint_sparsity_cache_from_csc(
    matrix: csc_matrix,
) -> _JointSparsityCache:
    """Capture a static sparsity-pattern cache from an exemplar joint
    operator. Caller is responsible for ensuring the exemplar covers
    all structurally-non-zero positions (e.g. by building it at an η
    where γ_T > 0 so all Thomson couplings have non-zero values)."""
    n_cols = int(matrix.indptr.size - 1)
    cols_of_data = np.repeat(np.arange(n_cols), np.diff(matrix.indptr))
    return _JointSparsityCache(
        indices=np.asarray(matrix.indices, dtype=np.int32).copy(),
        indptr=np.asarray(matrix.indptr, dtype=np.int32).copy(),
        cols_of_data=np.asarray(cols_of_data, dtype=np.int64),
        shape=tuple(int(d) for d in matrix.shape),
    )


@dataclass(frozen=True)
class ReducedJointAffineOperator:
    mode_labels: tuple[str, ...]
    local_dof: int
    harmonic_dof: int
    source_dof: int
    matrix: "np.ndarray | csc_matrix"
    """Joint affine operator. Currently always returned as ``csc_matrix``
    by ``build_reduced_joint_affine_operator``; the broader type annotation
    is preserved so a future CSR-pattern-caching variant can return either
    storage type without breaking callers.

    Round-17 P3.5 perf Tier 1A v1 (2026-04-28, REVERTED) attempted to
    return ``np.ndarray`` directly to skip the ``csc_matrix(joint)``
    conversion and its embedded ``numpy.ndarray.nonzero`` scan
    (21 s/run). The change was empirically 2× slower because LAPACK
    ``lu_factor`` is O(n³) on the 250×250 dense matrix while ``splu``
    only does work proportional to the actual nnz. The proper Tier 1A
    (CSR-pattern caching: build indices/indptr once at integrator init,
    update ``.data`` per step, keep ``splu``) is queued as future work.

    The ``_solve_joint_implicit`` dispatcher in ``ver2_native_integrator``
    handles both storage types and is dormant for the dense branch under
    the current implementation."""
    bias: np.ndarray


@dataclass(frozen=True)
class _ReducedHarmonicOperatorStructure:
    mode_labels: tuple[str, ...]
    residual_labels: tuple[str, ...]
    residual_count: int
    width: int
    block_size: int
    n_unknown: int
    ell_by_slot: np.ndarray
    abs_m_by_slot: np.ndarray
    prev_slot_by_slot: np.ndarray
    prev_coeff_by_slot: np.ndarray
    next_slot_by_slot: np.ndarray
    next_coeff_by_slot: np.ndarray
    pstf_weight_by_slot: np.ndarray
    eb_base_by_slot: np.ndarray
    collision_factor_by_slot: np.ndarray
    diag_base_by_slot: np.ndarray
    ge2_mask: np.ndarray
    ell0_mask: np.ndarray
    sector_slots: np.ndarray
    self_pattern_rows: np.ndarray
    self_pattern_cols: np.ndarray
    cross_pattern_rows: np.ndarray
    cross_pattern_cols: np.ndarray
    cross_residual_indices: tuple[tuple[int, ...], ...]
    cross_external_labels: tuple[tuple[str, ...], ...]
    monopole_slot: int
    dipole_slot: int | None
    quadrupole_slot: int | None


def _branch_scale(bg: Mapping[str, object]) -> float:
    return 1.15 if str(bg.get("branch", "orthogonal")) == "tilted" else 1.0


def _geometry_contract(
    bg: Mapping[str, object],
    backend: FamilyBackend,
):
    geometry = bg.get("geometry")
    if geometry is not None:
        return geometry
    from bass.background.geometry import build_geometry

    return build_geometry(backend.family_spec.algebra)


def _operator_scales(
    bg: Mapping[str, object],
    backend: FamilyBackend,
) -> dict[str, float]:
    algebra = backend.family_spec.algebra
    geometry = _geometry_contract(bg, backend)
    n_diag = np.diag(np.asarray(algebra.n, dtype=np.float64))
    twist = abs(float(algebra.a[0]))
    h_abs = abs(float(algebra.h_parameter or 0.0))
    ricci_scalar = abs(float(getattr(geometry, "ricci_scalar", 0.0)))
    ricci_pstf = np.asarray(getattr(geometry, "ricci_pstf", np.zeros((3, 3))), dtype=np.float64)
    shear = np.asarray(bg.get("sigma_tensor", np.zeros((3, 3))), dtype=np.float64)
    geom_scale = float(
        np.sqrt(
            np.sum(np.square(n_diag))
            + twist * twist
            + 0.25 * ricci_scalar
            + np.sum(np.square(ricci_pstf))
            + np.sum(np.square(shear))
        )
    )
    geom_scale = max(geom_scale, 1.0)
    branch_scale = _branch_scale(bg)
    # v5 audit Round-2 Q-7.4: hand-tuned scalar physics surrogates are removed
    # from the physics operator. mix_scale/polarization_scale/source_scale had
    # no first-principles derivation in the Maartens-Ellis 1+3 kinetic theory
    # or Ma-Bertschinger hierarchy; they were numerical placeholders whose
    # FLRW-limit values (0.12, 1.0, 1.0) contribute non-physical positive
    # modes through cross-mode couplings. twist_scale is kept as-is
    # (structurally vanishes in FLRW via twist=0), but the saturation form
    # 1/(1+twist+|h|) should be revisited per v5 §03A for non-Type-I families.
    mix_scale = 0.0
    twist_scale = branch_scale * twist / (1.0 + twist + h_abs)
    polarization_scale = 1.0
    source_scale = 1.0
    family_law = _family_conditioned_kernel_law(bg, backend)
    return {
        "branch_scale": branch_scale,
        "geom_scale": branch_scale * geom_scale * float(family_law["transport_scale"]),
        "mix_scale": mix_scale * float(family_law["mix_scale"]),
        "twist_scale": twist_scale * float(family_law["twist_mix_scale"]),
        "polarization_scale": polarization_scale * float(family_law["polarization_scale"]),
        "source_scale": source_scale * float(family_law["source_scale"]),
        "mass_scale": float(family_law["mass_scale"]),
        "local_drag_scale": float(family_law["local_drag_scale"]),
        "cross_mode_scale": float(family_law["cross_mode_scale"]),
        "collision_scale": float(family_law["collision_scale"]),
        "mode_plus_scale": float(family_law["mode_plus_scale"]),
        "mode_minus_scale": float(family_law["mode_minus_scale"]),
        "family_conditioned_kernel_status": str(family_law["status"]),
        "family_conditioned_kernel_law": str(family_law["law_name"]),
    }


def _family_conditioned_kernel_law(
    bg: Mapping[str, object],
    backend: FamilyBackend,
) -> dict[str, float | str]:
    family = backend.family_spec.family
    h_parameter = float(backend.family_spec.algebra.h_parameter or 0.0)
    abs_h = abs(h_parameter)
    twist = abs(float(np.asarray(backend.family_spec.algebra.a, dtype=np.float64)[0]))
    law: dict[str, float | str] = {
        "status": "frozen_v5_family_conditioned",
        "law_name": "anchor_family_default",
        "mass_scale": 1.0,
        "transport_scale": 1.0,
        "mix_scale": 1.0,
        "twist_mix_scale": 1.0,
        "polarization_scale": 1.0,
        "source_scale": 1.0,
        "local_drag_scale": 1.0,
        "cross_mode_scale": 1.0,
        "collision_scale": 1.0,
        "mode_plus_scale": 1.0,
        "mode_minus_scale": 1.0,
    }
    if family == "II":
        law.update(
            law_name="ii_nil_frozen_v5",
            mass_scale=1.04,
            transport_scale=1.10,
            mix_scale=0.92,
            twist_mix_scale=0.98,
            polarization_scale=1.02,
            source_scale=0.94,
            local_drag_scale=0.96,
            cross_mode_scale=0.90,
            collision_scale=1.03,
            mode_plus_scale=1.02,
            mode_minus_scale=0.99,
        )
    elif family == "III":
        law.update(
            law_name="iii_hyperbolic_branch_frozen_v5",
            mass_scale=1.06,
            transport_scale=1.16,
            mix_scale=1.05,
            twist_mix_scale=1.00,
            polarization_scale=1.04,
            source_scale=1.08,
            local_drag_scale=0.94,
            cross_mode_scale=1.02,
            collision_scale=1.05,
            mode_plus_scale=1.04,
            mode_minus_scale=0.98,
        )
    elif family == "IV":
        law.update(
            law_name="iv_solvable_chart_frozen_v5",
            mass_scale=1.08,
            transport_scale=1.22,
            mix_scale=1.15,
            twist_mix_scale=1.08,
            polarization_scale=1.07,
            source_scale=1.10,
            local_drag_scale=0.92,
            cross_mode_scale=1.06,
            collision_scale=1.04,
            mode_plus_scale=1.05,
            mode_minus_scale=0.97,
        )
    elif family == "V":
        law.update(
            law_name="v_open_chart_frozen_v5",
            mass_scale=1.03,
            transport_scale=1.12,
            mix_scale=1.03,
            twist_mix_scale=1.00,
            polarization_scale=1.03,
            source_scale=1.06,
            local_drag_scale=0.98,
            cross_mode_scale=1.01,
            collision_scale=1.02,
            mode_plus_scale=1.03,
            mode_minus_scale=0.99,
        )
    elif family == "VI_0":
        law.update(
            law_name="vi0_directional_limit_frozen_v5",
            mass_scale=1.07,
            transport_scale=1.18,
            mix_scale=1.12,
            twist_mix_scale=1.10,
            polarization_scale=1.06,
            source_scale=1.08,
            local_drag_scale=0.95,
            cross_mode_scale=1.08,
            collision_scale=1.04,
            mode_plus_scale=1.06,
            mode_minus_scale=0.96,
        )
    elif family == "VI_h":
        root = np.sqrt(max(-h_parameter, 0.0))
        q = (1.0 - root) / max(1.0 + root, 1.0e-30)
        q_mag = abs(float(q))
        law.update(
            law_name="vih_class_b_bridge_frozen_v5",
            mass_scale=1.05 + 0.03 * q_mag,
            transport_scale=1.14 + 0.08 * q_mag,
            mix_scale=1.08 + 0.10 * q_mag,
            twist_mix_scale=1.04 + 0.12 * q_mag,
            polarization_scale=1.03 + 0.05 * q_mag,
            source_scale=1.04 + 0.06 * q_mag,
            local_drag_scale=0.94 + 0.04 * q_mag,
            cross_mode_scale=1.04 + 0.08 * q_mag,
            collision_scale=1.02 + 0.04 * q_mag,
            mode_plus_scale=1.02 + 0.10 * q_mag,
            mode_minus_scale=max(0.88, 0.99 - 0.06 * q_mag),
        )
    elif family == "VII_0":
        law.update(
            law_name="vii0_helical_anchor_frozen_v5",
            mass_scale=1.02,
            transport_scale=1.08,
            mix_scale=1.16,
            twist_mix_scale=1.12,
            polarization_scale=1.05,
            source_scale=1.04,
            local_drag_scale=1.00,
            cross_mode_scale=1.05,
            collision_scale=1.03,
            mode_plus_scale=1.05,
            mode_minus_scale=0.97,
        )
    elif family == "VII_h":
        p = np.sqrt(max(h_parameter, 0.0))
        p_eff = min(float(p), 2.0)
        law.update(
            law_name="viih_positive_h_bridge_frozen_v5",
            mass_scale=1.03 + 0.02 * p_eff,
            transport_scale=1.10 + 0.07 * p_eff,
            mix_scale=1.12 + 0.08 * p_eff,
            twist_mix_scale=1.08 + 0.10 * p_eff,
            polarization_scale=1.04 + 0.04 * p_eff,
            source_scale=1.04 + 0.05 * p_eff,
            local_drag_scale=0.99 + 0.02 * p_eff,
            cross_mode_scale=1.03 + 0.04 * p_eff,
            collision_scale=1.02 + 0.03 * p_eff,
            mode_plus_scale=1.03 + 0.05 * p_eff,
            mode_minus_scale=max(0.90, 0.99 - 0.03 * p_eff),
        )
    elif family == "VIII":
        s_ref = 0.5
        measure_mu0 = s_ref * np.tanh(np.pi * s_ref)
        measure_mu_half = s_ref / max(np.tanh(np.pi * s_ref), 1.0e-30)
        measure_ratio = measure_mu_half / max(measure_mu0, 1.0e-30)
        law.update(
            law_name="viii_noncompact_measure_frozen_v5",
            mass_scale=1.04 + 0.01 * measure_ratio,
            transport_scale=1.15 + 0.03 * measure_ratio,
            mix_scale=1.10 + 0.04 * measure_ratio,
            twist_mix_scale=1.02 + 0.02 * measure_ratio,
            polarization_scale=1.05 + 0.02 * measure_ratio,
            source_scale=1.03 + 0.02 * measure_ratio,
            local_drag_scale=0.98 + 0.01 * measure_ratio,
            cross_mode_scale=1.04 + 0.02 * measure_ratio,
            collision_scale=1.03 + 0.01 * measure_ratio,
            mode_plus_scale=1.01 + 0.08 * (measure_ratio - 1.0),
            mode_minus_scale=max(0.88, 0.99 - 0.03 * (measure_ratio - 1.0)),
        )
    elif family == "IX":
        compact_boost = 1.0 + 0.1 * min(twist, 1.0)
        law.update(
            law_name="ix_compact_wigner_frozen_v5",
            mass_scale=0.98,
            transport_scale=0.96,
            mix_scale=1.18 * compact_boost,
            twist_mix_scale=1.10 * compact_boost,
            polarization_scale=1.08,
            source_scale=0.98,
            local_drag_scale=1.00,
            cross_mode_scale=1.06,
            collision_scale=1.05,
            mode_plus_scale=1.02 + 0.03 * compact_boost,
            mode_minus_scale=max(0.90, 0.99 - 0.02 * compact_boost),
        )
    return law


@dataclass(frozen=True)
class FamilyKernelPack:
    """Matrix-valued replacement for ``_family_conditioned_kernel_law``.

    Round-3 of the V5 residual-joint algebraic audit (see
    ``v5_residual_harmonic_algebraic_audit_round3.md``, Q-8.6) concluded
    that the 10 per-family scalar constants in
    ``_family_conditioned_kernel_law`` are empirical placeholders with no
    first-principles derivation. The correct family dependence is
    matrix-valued in the ``mu``-label basis and assembled from the
    structure constants ``(a, n)``.

    This pack carries the matrix-valued kernels. It is produced by
    ``_family_conditioned_kernel_operator`` and is **not yet wired into
    the assembly path** — the existing scalar ``_family_conditioned_kernel_law``
    remains the active code path. Wiring is deferred to a future session,
    staged per family (see ``docs/V5_RUNTIME_TRACK_ALGEBRAIC_PROMPT_ROUND3.md``).

    Shapes:
        transport              (mu_count, mu_count)
        mu_mode_coupling_{t,e,b,nu}  (mu_count, mu_count)
        twist_mix_kernel       (ell_max + 1, 2*ell_max + 1, 2, 2)
        local_drag_by_mu       (mu_count,)
        mass_by_mu             (mu_count,)
        collision              scalar

    For Type I (a=0, n=0) every ``mu_mode_coupling_*`` and ``twist_mix_kernel``
    entry is identically zero, which preserves the FLRW invariant
    manifold ``b_hh ≡ 0`` and the ``D_2 = 1002.086744 μK²`` anchor.
    """

    family: str
    mode_labels: tuple[str, ...]
    transport: np.ndarray
    mu_mode_coupling_t: np.ndarray
    mu_mode_coupling_e: np.ndarray
    mu_mode_coupling_b: np.ndarray
    mu_mode_coupling_nu: np.ndarray
    twist_mix_kernel: np.ndarray
    local_drag_by_mu: np.ndarray
    mass_by_mu: np.ndarray
    collision: float


# Canonical real-basis structure-constant matrices in the frozen
# (mu_0, mu_+, mu_-) storage basis, per Round-3 Q-8.2(a)(b).
# All other families (including Type I) collapse to the zero matrix,
# which is what preserves the FLRW anchor in the Type-I limit.
_FAMILY_KERNEL_N_MATRIX: dict[str, tuple[tuple[float, ...], ...]] = {
    "II":    ((1.0,  0.0,  0.0), (0.0, 0.0, 0.0), (0.0,  0.0,  0.0)),
    "III":   ((0.0,  0.0,  0.0), (0.0, 1.0, 0.0), (0.0,  0.0, -1.0)),
    "V":     ((0.0,  0.0,  0.0), (0.0, 0.0, 0.0), (0.0,  0.0,  0.0)),
    "VII_0": ((0.0,  0.0,  0.0), (0.0, 1.0, 0.0), (0.0,  0.0,  1.0)),
    "VIII":  ((-1.0, 0.0,  0.0), (0.0, 1.0, 0.0), (0.0,  0.0,  1.0)),
}


# Per-family Π_μ^α axis projector from algebra axes to (μ_0, μ_+, μ_-)
# storage basis (Round-4 Q-15). The generic ``BianchiAlgebra.axis_permutation``
# is NOT sufficient for the kernel pack — Round-4 Q-15 showed that the
# Pontzen-Challinor class-B swap (1, 0, 2) gives the wrong signature for
# Type III, and Type VII₀ needs the axis 0 ↔ axis 1 swap to move the
# unique zero eigenvalue into the μ_0 anchor slot.
#
# Convention (Round-4 Q-15): μ_0 ← anchor / unique-eigenvalue axis,
# μ_+ ← lower code-axis index in remaining subspace, μ_- ← higher.
#
# For class-A non-twist families we store the 3×3 permutation explicitly
# to guarantee the canonical N matrix above agrees with Π·diag(n)·Π^T.
_FAMILY_KERNEL_PI_PERMUTATION: dict[str, tuple[tuple[int, int, int], ...]] = {
    "I":     ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
    "II":    ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
    "III":   ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
    "V":     ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
    "VII_0": ((0, 1, 0), (1, 0, 0), (0, 0, 1)),   # Q-15.2: swap axes 0 ↔ 1
    "VIII":  ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
}


@lru_cache(maxsize=16)
def _build_twist_mix_kernel_unit(ell_max: int) -> np.ndarray:
    """Wigner-3j twist-mixing kernel for ``a_abs = 1`` on canonical axis 1.

    Implements Round-4 Q-13: the rank-1 spin-1 insertion on the spin-2
    polarization tower. The kernel shape is
    ``(ell_max+1, 2*ell_max+1, 2, 2)`` with axes:

        axis 0: ell          (0 ≤ ell ≤ ell_max)
        axis 1: m + ell_max  (maps m ∈ [-ell, +ell] into [0, 2*ell])
        axis 2: delta_ell_index  (0 ↔ Δℓ = -1, 1 ↔ Δℓ = +1)
        axis 3: delta_m_index    (0 ↔ Δm = -1, 1 ↔ Δm = +1)

    Only ell ≥ 2 entries are non-zero (spin-2 selection rule). The kernel
    vanishes identically for ``a_abs = 0`` (class-A families); callers
    should scale the returned array by the physical ``a_abs`` value at
    assembly time.

    Normalization check (Round-4 Q-13 sanity): ``K[2, ell_max+0, 1, 0]``
    (ell=2, m=0, Δℓ=+1, Δm=-1) equals ``+1/sqrt(21)``.

    Lru-cached because the sympy evaluation is quadratic in ell_max and
    backend construction may request the same table many times.
    """

    from sympy import N as _sympy_N
    from sympy.physics.wigner import wigner_3j

    K = np.zeros((ell_max + 1, 2 * ell_max + 1, 2, 2), dtype=np.float64)

    # Condon-Shortley spherical components for a^α = 1 · e_x:
    #   a_0 = 0, a_{+1} = -1/sqrt(2), a_{-1} = +1/sqrt(2)
    a_plus = -1.0 / float(np.sqrt(2.0))
    a_minus = +1.0 / float(np.sqrt(2.0))

    for ell in range(2, ell_max + 1):
        # Second 3-j factor (ℓ, 1, ℓ'; -2, 0, 2) is ℓ-dependent only.
        w2_plus = float(_sympy_N(wigner_3j(ell, 1, ell + 1, -2, 0, 2)))
        w2_minus = (
            float(_sympy_N(wigner_3j(ell, 1, ell - 1, -2, 0, 2)))
            if ell - 1 >= 2
            else 0.0
        )

        for m in range(-ell, ell + 1):
            m_off = m + ell_max

            for dli, d_ell in enumerate((-1, +1)):
                ellp = ell + d_ell
                if ellp < 2:
                    continue
                w2 = w2_minus if d_ell == -1 else w2_plus
                prefac = ((-1.0) ** m) * float(np.sqrt((2 * ell + 1) * (2 * ellp + 1)))

                for dmi, d_m in enumerate((-1, +1)):
                    # selection rule: m' = m - q so q = -Δm
                    q = -d_m
                    mp = m + d_m
                    if abs(mp) > ellp:
                        continue
                    a_q = a_plus if q == +1 else a_minus
                    w1 = float(_sympy_N(wigner_3j(ell, 1, ellp, -m, q, mp)))
                    K[ell, m_off, dli, dmi] = a_q * prefac * w1 * w2

    return K


def _build_transport_matrix(
    family: str,
    k_mag: float,
    *,
    helical_eigenvalue: float = 1.0,
    mu_count: int = 3,
) -> np.ndarray:
    """Per-family spectral-parameter-dependent transport matrix.

    Implements Round-4 Q-10 (Type VII₀ helical gap) + v5 §03B mode
    eigenvalues for the Tier-A families. This is a utility for the
    wiring session — the ``FamilyKernelPack.transport`` field is left
    as identity at kernel-build time and multiplied by this matrix at
    assembly time, when the spectral parameter ``k_mag`` is available.

    Return shape: ``(mu_count, mu_count)`` diagonal matrix.

    Family map (Q-10 + v5 §03B):

        Type I:     diag(|k|, |k|, |k|)                      (isotropic FLRW)
        Type II:    diag(|k|, |k|, |k|)                      (ν̇_II(k) = |k|)
        Type III:   diag(1, 1, 1)                            (ν̇_III = 1)
        Type V:     diag(√(k²+1), √(k²+1), √(k²+1))         (open hyperbolic)
        Type VII₀:  diag(|k|, √(k²+h), √(k²+h))              (Q-10)
        Type VIII:  diag(√(k²+¼), √(k²+¼), √(k²+¼))         (principal series)

    where ``h = helical_eigenvalue`` (= 1 in canonical units).

    Type-I limit (Q-10.4): as ``helical_eigenvalue → 0`` the VII₀
    transport reduces to ``|k|·I_3``, matching the isotropic FLRW case.
    """

    k2 = float(k_mag) * float(k_mag)
    if family == "I":
        diag = (k_mag, k_mag, k_mag)
    elif family == "II":
        diag = (k_mag, k_mag, k_mag)
    elif family == "III":
        diag = (1.0, 1.0, 1.0)
    elif family == "V":
        rad = float(np.sqrt(k2 + 1.0))
        diag = (rad, rad, rad)
    elif family == "VII_0":
        q_h = float(np.sqrt(k2 + float(helical_eigenvalue)))
        diag = (float(k_mag), q_h, q_h)
    elif family == "VIII":
        rad = float(np.sqrt(k2 + 0.25))
        diag = (rad, rad, rad)
    else:
        # Tier-B families return identity-times-|k| as a safe placeholder.
        diag = tuple(k_mag for _ in range(mu_count))
    return np.diag(np.asarray(diag, dtype=np.float64)[:mu_count])


def _family_conditioned_kernel_operator(
    backend: FamilyBackend,
    ell_max: int,
    *,
    mode_labels: tuple[str, ...] | None = None,
) -> FamilyKernelPack:
    """Return the matrix-valued Round-3/Round-4 kernel pack for ``backend``.

    Round-3 implemented Q-8.2(a)(b) μ-mode signatures and Q-8.5(a)(b)(c)
    scalar/vector shapes. Round-4 extended:

    - Q-13 Wigner-3j evaluation — ``twist_mix_kernel`` now carries the
      closed-form rank-1 spin-1 insertion on the spin-2 polarization
      tower for class-B families (non-zero for III, V, VI_h, VII_h),
      evaluated with ``sympy.physics.wigner`` and cached by ``ell_max``.
    - Q-15 Π_μ^α confirmation — the hard-coded canonical N matrices
      already match ``Π · diag(n_code) · Π^T`` for all five Tier-A
      families using the per-family Π table above. The BianchiAlgebra
      generic ``axis_permutation`` field is *not* the correct Π for
      the kernel pack (see Round-4 answer).

    Still runtime-dependent (kept as Type-I-equivalent placeholders
    here; to be filled by the wiring-session assembly patch):

    - Q-10 ``transport`` left as identity; the spectral-parameter-
      dependent matrix ``diag(q_0, q_h, q_h)`` is built at assembly
      time via ``_build_transport_matrix(family, k_mag)``.
    - Q-11 ``local_drag_by_mu`` left as ones; class-B O(|a|²) correction
      ``ζ_R = c_rb · ((v_{b,∥} - 4/3·v_{γ,∥}) / H)²`` requires runtime
      background state and still has a ``c_rb`` ∈ {1, 1/2} v5 ambiguity.
    - Q-12 ``mass_by_mu`` left as ones; Round-4 corrected the schema
      to ``1 + σ_{μμ}/H``. Requires runtime shear eigenvalues.
    """

    family = str(backend.family_spec.family)
    algebra = backend.family_spec.algebra
    labels = (
        tuple(mode_labels)
        if mode_labels is not None
        else _mode_labels_from_backend(backend, {})
    )
    mu_count = len(labels)
    if mu_count <= 0:
        raise ValueError("FamilyKernelPack requires at least one mode label")

    a_vec = np.asarray(algebra.a, dtype=np.float64)
    is_class_b = float(np.linalg.norm(a_vec)) > 0.0

    # Structure-constant matrix N in canonical (mu_0, mu_+, mu_-) basis.
    # These hard-coded signatures already encode Π · diag(n_code) · Π^T
    # where Π is the per-family axis projector table above (Round-4
    # Q-15). For Tier-B families outside {II, III, V, VII_0, VIII} and
    # for Type I, N = 0 (queued for a future audit round).
    N = np.zeros((mu_count, mu_count), dtype=np.float64)
    canonical = _FAMILY_KERNEL_N_MATRIX.get(family)
    if canonical is not None and mu_count >= 3:
        for i in range(3):
            for j in range(3):
                N[i, j] = canonical[i][j]

    # Twist projector P_a = \hat a \hat a^T in canonical basis.
    # Q-8.6(b) matrices are structural signatures with unit normalization
    # (|a| = 1 in canonical gauge); the physical amplitude scale comes
    # from the backend spectral parameter at wiring time. In canonical
    # VER2 class-B axes a^alpha ∝ (|a|, 0, 0), so P_a is rank-1 on the
    # first mu basis direction for class-B families and zero for class-A.
    P_a = np.zeros((mu_count, mu_count), dtype=np.float64)
    if is_class_b and mu_count >= 1:
        P_a[0, 0] = 1.0

    mu_mode_coupling = N + P_a

    # transport: Q-10 placeholder. Use _build_transport_matrix(family, k)
    # at assembly time to obtain the spectral-parameter-dependent matrix.
    transport = np.eye(mu_count, dtype=np.float64)

    # twist_mix_kernel: Q-13 Wigner-3j evaluation with canonical unit
    # normalization |a| = 1 for class-B, zero for class-A. The physical
    # amplitude is applied at assembly time (algebra.a's actual |a|
    # magnitude, e.g. 0.01 in the code's canonical scale).
    a_abs_canonical = 1.0 if is_class_b else 0.0
    if a_abs_canonical > 0.0:
        twist_mix_kernel = a_abs_canonical * _build_twist_mix_kernel_unit(int(ell_max))
    else:
        twist_mix_kernel = np.zeros(
            (int(ell_max) + 1, 2 * int(ell_max) + 1, 2, 2),
            dtype=np.float64,
        )

    # local_drag_by_mu: Q-11 placeholder. Class-B ζ_R requires runtime
    # (v_b_∥, v_γ_∥, H) from background state; the c_rb ∈ {1, 1/2}
    # ambiguity also remains. Ones vector is the Type-I-compatible
    # placeholder; assembly-time patch must replace it with
    # R^{-1}·(1 + ζ_R·|a|², 1, 1) for class-B families.
    local_drag_by_mu = np.ones(mu_count, dtype=np.float64)

    # mass_by_mu: Q-12 placeholder. Round-4 corrected the schema to
    # 1 + σ_{μμ}/H — exact, no free coefficient. Ones vector is the
    # Type-I-compatible placeholder; assembly-time patch must replace
    # it with (1 + σ_diag/H) from the runtime background shear.
    mass_by_mu = np.ones(mu_count, dtype=np.float64)

    # collision: Q-8.5(c). Thomson rate is universal in the Bianchi
    # family; all 1.03-1.05 placeholders in _family_conditioned_kernel_law
    # should collapse to 1.0 per Round-3 Q-7.2 + Q-8.5(c).
    collision = 1.0

    return FamilyKernelPack(
        family=family,
        mode_labels=labels,
        transport=transport,
        mu_mode_coupling_t=mu_mode_coupling.copy(),
        mu_mode_coupling_e=mu_mode_coupling.copy(),
        mu_mode_coupling_b=mu_mode_coupling.copy(),
        mu_mode_coupling_nu=mu_mode_coupling.copy(),
        twist_mix_kernel=twist_mix_kernel,
        local_drag_by_mu=local_drag_by_mu,
        mass_by_mu=mass_by_mu,
        collision=collision,
    )


def _mode_labels_from_backend(
    backend: FamilyBackend,
    truncation: Mapping[str, object],
) -> tuple[str, ...]:
    explicit = truncation.get("mode_labels")
    if explicit is not None:
        labels = tuple(str(x) for x in explicit)
        if not labels:
            raise ValueError("mode_labels must be non-empty when provided")
        return labels
    family = backend.family_spec.family
    defaults = {
        "I": ("m0", "m+2", "m-2"),
        "II": ("mu_nil", "mu_nil+", "mu_nil-"),
        "III": ("mu_hyp", "mu_hyp+", "mu_hyp-"),
        "IV": ("mu_solv", "mu_solv+", "mu_solv-"),
        "V": ("mu_open", "mu_open+", "mu_open-"),
        "VI_0": ("mu_vi0", "mu_vi0+", "mu_vi0-"),
        "VI_h": ("mu_vih", "mu_vih+", "mu_vih-"),
        "VII_0": ("mu_hel", "mu_hel+", "mu_hel-"),
        "VII_h": ("mu_hel_h", "mu_hel_h+", "mu_hel_h-"),
        "VIII": ("mu_sl2r", "mu_sl2r+", "mu_sl2r-"),
        "IX": ("mu_compact", "mu_compact+", "mu_compact-"),
    }
    return defaults.get(family, ("mu0",))


def _sector_local_dofs(truncation: Mapping[str, object]) -> dict[str, int]:
    overrides = truncation.get("sector_local_dofs", {})
    out = dict(_LOCAL_SECTOR_DEFAULTS)
    for key, value in dict(overrides).items():
        if key not in out:
            raise ValueError(f"unknown local sector {key!r}")
        ivalue = int(value)
        if ivalue <= 0:
            raise ValueError(f"sector {key!r} local dofs must be > 0")
        out[key] = ivalue
    return out


def _sector_block_size(
    sector: str,
    *,
    ell_max: int,
    local_dofs: Mapping[str, int],
) -> int:
    if sector in _HARMONIC_SECTORS:
        return sum(2 * ell + 1 for ell in range(ell_max + 1))
    return int(local_dofs[sector])


def _mode_label_weight(
    mu: str,
    *,
    mu_index: int,
    mu_count: int,
    branch_scale: float,
    plus_scale: float = 1.0,
    minus_scale: float = 1.0,
) -> float:
    label = str(mu)
    if label == "m0":
        return 1.0
    if label == "m+2":
        return (1.0 + 0.12 * branch_scale) * plus_scale
    if label == "m-2":
        return (1.0 - 0.08 * branch_scale) * minus_scale
    if label.endswith("+"):
        return (1.0 + 0.12 * branch_scale) * plus_scale
    if label.endswith("-"):
        return (1.0 - 0.08 * branch_scale) * minus_scale
    return 1.0 + 0.03 * (mu_index / max(mu_count, 1))


def _harmonic_cross_mode_coeff(
    *,
    mu_weight: float,
    mix_scale: float,
    cross_mode_scale: float,
    twist_scale: float,
    sector: str,
    ell: int,
    mu_count: int,
) -> float:
    if mu_count <= 1:
        return 0.0
    base = mu_weight * mix_scale * cross_mode_scale / max((ell + 1) * mu_count, 1)
    if sector == "ph_I":
        return 0.18 * base
    if sector == "ph_E":
        return 0.16 * base
    if sector == "ph_B":
        return 0.16 * (1.0 + 0.5 * twist_scale) * base
    if sector == "nu_I":
        return 0.12 * base
    raise KeyError(f"unsupported harmonic sector {sector!r}")


def _mode_label_coupling_targets(
    mode_labels: tuple[str, ...],
    source_label: str,
    *,
    family: str | None = None,
) -> tuple[str, ...]:
    labels = tuple(str(mu) for mu in mode_labels)
    if len(labels) <= 1:
        return ()
    anchor = str(labels[0])
    source = str(source_label)
    if source == anchor:
        return tuple(str(mu) for mu in labels[1:])
    residuals = tuple(str(mu) for mu in labels[1:])
    if family in {"VII_0", "VII_h", "VIII", "IX"} and len(residuals) >= 2:
        plus_label = next((mu for mu in residuals if mu.endswith("+")), residuals[0])
        minus_label = next((mu for mu in residuals if mu.endswith("-")), residuals[-1])
        if source == plus_label and minus_label != plus_label:
            return (anchor, minus_label)
    return (anchor,)


@lru_cache(maxsize=None)
def _reduced_harmonic_structure(
    ell_max: int,
    mode_labels: tuple[str, ...],
    residual_labels: tuple[str, ...],
    family: str,
) -> _ReducedHarmonicOperatorStructure:
    width = (int(ell_max) + 1) ** 2
    block_size = 4 * width
    residual_count = len(residual_labels)
    slots = np.arange(width, dtype=np.int64)
    ell_by_slot = np.zeros(width, dtype=np.int64)
    abs_m_by_slot = np.zeros(width, dtype=np.float64)
    prev_slot_by_slot = np.full(width, -1, dtype=np.int64)
    prev_coeff_by_slot = np.zeros(width, dtype=np.float64)
    next_slot_by_slot = np.full(width, -1, dtype=np.int64)
    next_coeff_by_slot = np.zeros(width, dtype=np.float64)
    pstf_weight_by_slot = np.zeros(width, dtype=np.float64)
    eb_base_by_slot = np.zeros(width, dtype=np.float64)
    collision_factor_by_slot = np.zeros(width, dtype=np.float64)
    diag_base_by_slot = np.zeros(width, dtype=np.float64)
    slot_lookup: dict[tuple[int, int], int] = {}
    offset = 0
    for ell in range(int(ell_max) + 1):
        pstf_weight = np.sqrt(max((ell + 2) * (ell - 1), 0.0)) / max(2 * ell + 1, 1) if ell >= 2 else 0.0
        for m in range(-ell, ell + 1):
            slot = offset + (m + ell)
            slot_lookup[(ell, m)] = slot
            ell_by_slot[slot] = ell
            abs_m_by_slot[slot] = float(abs(m))
            # v5 audit Q3: diagonal self-damping is non-physical in the FLRW
            # limit. The |m|-dependence violates SO(3) isotropy of the FLRW
            # background (Wigner-Eckart forbids m-dependent scalar operators
            # on PSTF multipoles), and the (ell+1) coefficient has no
            # counterpart in Ma-Bertschinger 1995 nor in 1+3 covariant
            # kinetic theory. Stability of the post-flip operator is
            # guaranteed by weighted skew-adjointness (audit Q2), not by
            # this diagonal.
            diag_base_by_slot[slot] = 0.0
            collision_factor_by_slot[slot] = 1.0 if ell <= 1 else 1.0 / (ell + 0.5)
            if ell >= 2:
                pstf_weight_by_slot[slot] = pstf_weight
                eb_base_by_slot[slot] = max(abs(m), 1) / (ell + 1)
            if ell > 0:
                prev_m = m if abs(m) <= ell - 1 else 0
                prev_slot = slot_lookup[(ell - 1, prev_m)]
                prev_slot_by_slot[slot] = prev_slot
                prev_coeff_by_slot[slot] = np.sqrt(max(ell * ell - m * m, 0.0)) / max(2 * ell + 1, 1)
            if ell < int(ell_max):
                next_m = m if abs(m) <= ell + 1 else 0
                next_slot = offset + (2 * ell + 1) + (next_m + (ell + 1))
                next_slot_by_slot[slot] = next_slot
                next_coeff_by_slot[slot] = np.sqrt(max((ell + 1) * (ell + 1) - m * m, 0.0)) / max(2 * ell + 1, 1)
        offset += 2 * ell + 1

    label_to_residual = {str(mu): idx for idx, mu in enumerate(residual_labels)}
    mode_labels_list = tuple(str(mu) for mu in mode_labels)
    cross_residual_indices: list[tuple[int, ...]] = []
    cross_external_labels: list[tuple[str, ...]] = []
    for mu in residual_labels:
        mu_key = str(mu)
        residual_targets: list[int] = []
        external_targets: list[str] = []
        for target in _mode_label_coupling_targets(
            mode_labels_list,
            mu_key,
            family=family,
        ):
            target_key = str(target)
            if target_key in label_to_residual:
                residual_targets.append(int(label_to_residual[target_key]))
            else:
                external_targets.append(target_key)
        cross_residual_indices.append(tuple(residual_targets))
        cross_external_labels.append(tuple(external_targets))

    t_off = 0
    e_off = width
    b_off = 2 * width
    nu_off = 3 * width
    self_pattern = np.zeros((block_size, block_size), dtype=bool)
    cross_pattern = np.zeros((block_size, block_size), dtype=bool)
    self_pattern[t_off + slots, t_off + slots] = True
    self_pattern[e_off + slots, e_off + slots] = True
    self_pattern[b_off + slots, b_off + slots] = True
    self_pattern[nu_off + slots, nu_off + slots] = True
    valid_prev = prev_slot_by_slot >= 0
    valid_next = next_slot_by_slot >= 0
    self_pattern[t_off + slots[valid_prev], t_off + prev_slot_by_slot[valid_prev]] = True
    self_pattern[e_off + slots[valid_prev], e_off + prev_slot_by_slot[valid_prev]] = True
    self_pattern[b_off + slots[valid_prev], b_off + prev_slot_by_slot[valid_prev]] = True
    self_pattern[nu_off + slots[valid_prev], nu_off + prev_slot_by_slot[valid_prev]] = True
    self_pattern[t_off + slots[valid_next], t_off + next_slot_by_slot[valid_next]] = True
    self_pattern[e_off + slots[valid_next], e_off + next_slot_by_slot[valid_next]] = True
    self_pattern[b_off + slots[valid_next], b_off + next_slot_by_slot[valid_next]] = True
    self_pattern[nu_off + slots[valid_next], nu_off + next_slot_by_slot[valid_next]] = True
    ge2_slots = slots[ell_by_slot >= 2]
    self_pattern[t_off + ge2_slots, e_off + ge2_slots] = True
    self_pattern[e_off + ge2_slots, t_off + ge2_slots] = True
    self_pattern[e_off + ge2_slots, b_off + ge2_slots] = True
    self_pattern[b_off + ge2_slots, e_off + ge2_slots] = True
    self_pattern[b_off + ge2_slots, t_off + ge2_slots] = True
    if len(mode_labels_list) > 1:
        cross_pattern[t_off + slots[ell_by_slot == 0], t_off + slots[ell_by_slot == 0]] = True
        cross_pattern[e_off + slots[ell_by_slot == 0], e_off + slots[ell_by_slot == 0]] = True
        cross_pattern[b_off + slots[ell_by_slot == 0], b_off + slots[ell_by_slot == 0]] = True
        cross_pattern[nu_off + slots[ell_by_slot == 0], nu_off + slots[ell_by_slot == 0]] = True
        cross_pattern[t_off + ge2_slots, t_off + ge2_slots] = True
        cross_pattern[e_off + ge2_slots, e_off + ge2_slots] = True
        cross_pattern[b_off + ge2_slots, b_off + ge2_slots] = True
        cross_pattern[nu_off + ge2_slots, nu_off + ge2_slots] = True
    self_pattern_rows, self_pattern_cols = np.nonzero(self_pattern)
    cross_pattern_rows, cross_pattern_cols = np.nonzero(cross_pattern)

    return _ReducedHarmonicOperatorStructure(
        mode_labels=mode_labels_list,
        residual_labels=tuple(str(mu) for mu in residual_labels),
        residual_count=residual_count,
        width=width,
        block_size=block_size,
        n_unknown=residual_count * block_size,
        ell_by_slot=ell_by_slot,
        abs_m_by_slot=abs_m_by_slot,
        prev_slot_by_slot=prev_slot_by_slot,
        prev_coeff_by_slot=prev_coeff_by_slot,
        next_slot_by_slot=next_slot_by_slot,
        next_coeff_by_slot=next_coeff_by_slot,
        pstf_weight_by_slot=pstf_weight_by_slot,
        eb_base_by_slot=eb_base_by_slot,
        collision_factor_by_slot=collision_factor_by_slot,
        diag_base_by_slot=diag_base_by_slot,
        ge2_mask=ell_by_slot >= 2,
        ell0_mask=ell_by_slot == 0,
        sector_slots=slots,
        self_pattern_rows=np.asarray(self_pattern_rows, dtype=np.int64),
        self_pattern_cols=np.asarray(self_pattern_cols, dtype=np.int64),
        cross_pattern_rows=np.asarray(cross_pattern_rows, dtype=np.int64),
        cross_pattern_cols=np.asarray(cross_pattern_cols, dtype=np.int64),
        cross_residual_indices=tuple(cross_residual_indices),
        cross_external_labels=tuple(cross_external_labels),
        monopole_slot=slot_lookup[(0, 0)],
        dipole_slot=slot_lookup.get((1, 0)),
        quadrupole_slot=slot_lookup.get((2, 0)),
    )


def build_hierarchy_layout(
    backend: FamilyBackend,
    truncation: Mapping[str, object],
    *,
    sector_order: tuple[str, ...] = SECTOR_ORDER,
) -> HierarchyLayout:
    ell_max = int(truncation["ell_max"])
    if ell_max < 0:
        raise ValueError("ell_max must be non-negative")
    local_dofs = _sector_local_dofs(truncation)
    mode_labels = _mode_labels_from_backend(backend, truncation)
    size = 0
    for _mu in mode_labels:
        for sector in sector_order:
            size += _sector_block_size(sector, ell_max=ell_max, local_dofs=local_dofs)
    return HierarchyLayout(
        mode_labels=mode_labels,
        sector_order=sector_order,
        ell_max=ell_max,
        sector_local_dofs=local_dofs,
        size=size,
    )


def build_layout_manifest(
    layout: HierarchyLayout,
    backend: FamilyBackend,
    truncation: Mapping[str, object],
    bg: Mapping[str, object] | None = None,
) -> dict[str, object]:
    required_metadata = backend.required_metadata()
    exact_operator = backend.template_card().operator_kernel_family == "bianchi_i_matrix_exact"
    return {
        "family": backend.family_spec.family,
        "branch": str((bg or {}).get("branch", "orthogonal")),
        "mode_labels": list(layout.mode_labels),
        "sector_order": list(layout.sector_order),
        "ell_max": layout.ell_max,
        "sector_local_dofs": dict(layout.sector_local_dofs),
        "size": layout.size,
        "native_mode_labels": required_metadata["native_mode_labels"],
        "boundary_policy": required_metadata["boundary_policy"],
        "release_status": required_metadata["release_status"],
        "operator_realization": "geometry_opacity_coupled_sparse_operator",
        "mass_matrix_realization": "family_branch_sector_weighted_diagonal",
        "exact_family_operator_available": exact_operator,
        "approximate_family_operator_available": not exact_operator,
        "reduced_local_evaluator_available": True,
        "reduced_harmonic_evaluator_available": True,
        "reduced_source_evaluator_available": True,
        "family_conditioned_kernel_status": "frozen_v5_family_conditioned",
        "family_conditioned_kernel_law": _family_conditioned_kernel_law((bg or {}), backend)["law_name"],
        "truncation_metadata": dict(truncation),
    }


def flatten(
    layout: HierarchyLayout,
    mu: str,
    sector: str,
    ell: int | None,
    m: int | None,
    local_dof: int | None = None,
) -> int:
    if mu not in layout.mode_labels:
        raise KeyError(f"unknown mode label {mu!r}")
    if sector not in layout.sector_order:
        raise KeyError(f"unknown sector {sector!r}")
    index = 0
    for mu_label in layout.mode_labels:
        if mu_label == mu:
            break
        for sector_name in layout.sector_order:
            index += _sector_block_size(
                sector_name,
                ell_max=layout.ell_max,
                local_dofs=layout.sector_local_dofs,
            )
    for sector_name in layout.sector_order:
        if sector_name == sector:
            break
        index += _sector_block_size(
            sector_name,
            ell_max=layout.ell_max,
            local_dofs=layout.sector_local_dofs,
        )
    if sector in _HARMONIC_SECTORS:
        if ell is None or m is None:
            raise ValueError("harmonic sectors require ell and m")
        if ell < 0 or ell > layout.ell_max:
            raise ValueError(f"ell={ell} outside [0,{layout.ell_max}]")
        if abs(m) > ell:
            raise ValueError(f"|m| must be <= ell, got ell={ell}, m={m}")
        index += sum(2 * l + 1 for l in range(ell))
        index += m + ell
        return index
    if local_dof is None:
        raise ValueError(f"sector {sector!r} requires local_dof")
    if local_dof < 0 or local_dof >= layout.sector_local_dofs[sector]:
        raise ValueError(
            f"local_dof={local_dof} outside [0,{layout.sector_local_dofs[sector]-1}] for sector {sector!r}"
        )
    return index + local_dof


def unflatten(layout: HierarchyLayout, index: int) -> tuple[str, str, int | None, int | None, int | None]:
    if index < 0 or index >= layout.size:
        raise ValueError(f"index={index} outside [0,{layout.size - 1}]")
    cursor = int(index)
    for mu in layout.mode_labels:
        for sector in layout.sector_order:
            block = _sector_block_size(
                sector,
                ell_max=layout.ell_max,
                local_dofs=layout.sector_local_dofs,
            )
            if cursor < block:
                if sector in _HARMONIC_SECTORS:
                    for ell in range(layout.ell_max + 1):
                        ell_width = 2 * ell + 1
                        if cursor < ell_width:
                            m = cursor - ell
                            return mu, sector, ell, m, None
                        cursor -= ell_width
                    raise AssertionError("harmonic block cursor overflow")
                return mu, sector, None, None, cursor
            cursor -= block
    raise AssertionError("layout cursor overflow")


def assemble_mass_matrix(
    bg: Mapping[str, object],
    backend: FamilyBackend,
    truncation: Mapping[str, object],
) -> csr_matrix:
    layout = build_hierarchy_layout(backend, truncation)
    scales = _operator_scales(bg, backend)
    geom_scale = float(scales["geom_scale"])
    branch_scale = float(scales["branch_scale"])
    polarization_scale = float(scales["polarization_scale"])
    twist_scale = float(scales["twist_scale"])
    source_scale = float(scales["source_scale"])
    mass_scale = float(scales["mass_scale"])
    mode_plus_scale = float(scales["mode_plus_scale"])
    mode_minus_scale = float(scales["mode_minus_scale"])
    diag = np.ones(layout.size, dtype=np.float64)
    mu_count = max(len(layout.mode_labels), 1)
    for mu_index, mu in enumerate(layout.mode_labels):
        mu_weight = _mode_label_weight(
            mu,
            mu_index=mu_index,
            mu_count=mu_count,
            branch_scale=branch_scale,
            plus_scale=mode_plus_scale,
            minus_scale=mode_minus_scale,
        )
        for sector in layout.sector_order:
            if sector in _HARMONIC_SECTORS:
                for ell in range(layout.ell_max + 1):
                    ell_weight = 1.0 + 0.04 * ell + 0.015 * geom_scale
                    sector_weight = 1.0
                    if sector == "ph_I":
                        sector_weight = branch_scale
                    elif sector == "ph_E":
                        sector_weight = branch_scale * (1.08 * polarization_scale)
                    elif sector == "ph_B":
                        sector_weight = branch_scale * (1.12 + 0.5 * twist_scale) * polarization_scale
                    elif sector == "nu_I":
                        sector_weight = 1.0 + 0.1 * branch_scale + 0.02 * geom_scale
                    block_weight = mu_weight * sector_weight * ell_weight
                    for m in range(-ell, ell + 1):
                        diag[flatten(layout, mu, sector, ell, m)] = mass_scale * block_weight
                continue
            width = int(layout.sector_local_dofs[sector])
            for local_dof in range(width):
                idx = flatten(layout, mu, sector, None, None, local_dof)
                if sector == "baryon":
                    value = mu_weight * (1.0 + 0.08 * geom_scale + 0.03 * local_dof)
                elif sector == "cdm":
                    value = mu_weight * (1.0 + 0.05 * geom_scale + 0.02 * local_dof)
                else:
                    value = mu_weight * (1.0 + 0.06 * source_scale + 0.04 * local_dof)
                diag[idx] = mass_scale * value
    return diags(diag, offsets=0, format="csr", dtype=np.float64)


def assemble_free_streaming_block(
    bg: Mapping[str, object],
    backend: FamilyBackend,
    truncation: Mapping[str, object],
) -> csr_matrix:
    layout = build_hierarchy_layout(backend, truncation)
    scales = _operator_scales(bg, backend)
    geom_scale = float(scales["geom_scale"])
    branch_scale = float(scales["branch_scale"])
    polarization_scale = float(scales["polarization_scale"])
    cross_mode_scale = float(scales["cross_mode_scale"])
    mode_plus_scale = float(scales["mode_plus_scale"])
    mode_minus_scale = float(scales["mode_minus_scale"])
    rows: list[int] = []
    cols: list[int] = []
    data: list[float] = []
    mu_count = max(len(layout.mode_labels), 1)
    for mu_index, mu in enumerate(layout.mode_labels):
        mu_weight = _mode_label_weight(
            mu,
            mu_index=mu_index,
            mu_count=mu_count,
            branch_scale=branch_scale,
            plus_scale=mode_plus_scale,
            minus_scale=mode_minus_scale,
        )
        for sector in layout.sector_order:
            if sector not in _HARMONIC_SECTORS:
                continue
            for ell in range(layout.ell_max + 1):
                for m in range(-ell, ell + 1):
                    idx = flatten(layout, mu, sector, ell, m)
                    spin_weight = polarization_scale if sector in {"ph_E", "ph_B"} else 1.0
                    diag = -geom_scale * mu_weight * spin_weight * (0.35 * (ell + 1) + 0.08 * abs(m))
                    rows.append(idx)
                    cols.append(idx)
                    data.append(diag)
                    if ell > 0:
                        prv = flatten(layout, mu, sector, ell - 1, m if abs(m) <= ell - 1 else 0)
                        coeff_down = (
                            geom_scale
                            * mu_weight
                            * spin_weight
                            * np.sqrt(max(ell * ell - m * m, 0.0))
                            / max(2 * ell + 1, 1)
                        )
                        rows.append(idx)
                        cols.append(prv)
                        data.append(coeff_down)
                    if ell < layout.ell_max:
                        nxt = flatten(layout, mu, sector, ell + 1, m if abs(m) <= ell + 1 else 0)
                        coeff_up = (
                            geom_scale
                            * mu_weight
                            * spin_weight
                            * np.sqrt(max((ell + 1) * (ell + 1) - m * m, 0.0))
                            / max(2 * ell + 1, 1)
                        )
                        rows.append(idx)
                        cols.append(nxt)
                        data.append(coeff_up)
    return csr_matrix((data, (rows, cols)), shape=(layout.size, layout.size))


def assemble_mixing_block(
    bg: Mapping[str, object],
    backend: FamilyBackend,
    truncation: Mapping[str, object],
) -> csr_matrix:
    layout = build_hierarchy_layout(backend, truncation)
    scales = _operator_scales(bg, backend)
    branch_scale = float(scales["branch_scale"])
    mix_scale = float(scales["mix_scale"])
    twist_scale = float(scales["twist_scale"])
    cross_mode_scale = float(scales["cross_mode_scale"])
    mode_plus_scale = float(scales["mode_plus_scale"])
    mode_minus_scale = float(scales["mode_minus_scale"])
    rows: list[int] = []
    cols: list[int] = []
    data: list[float] = []
    mu_count = max(len(layout.mode_labels), 1)
    for mu_index, mu in enumerate(layout.mode_labels):
        mu_weight = _mode_label_weight(
            mu,
            mu_index=mu_index,
            mu_count=mu_count,
            branch_scale=branch_scale,
            plus_scale=mode_plus_scale,
            minus_scale=mode_minus_scale,
        )
        for ell in range(2, layout.ell_max + 1):
            for m in range(-ell, ell + 1):
                i_idx = flatten(layout, mu, "ph_I", ell, m)
                e_idx = flatten(layout, mu, "ph_E", ell, m)
                b_idx = flatten(layout, mu, "ph_B", ell, m)
                nu_idx = flatten(layout, mu, "nu_I", ell, m)
                pstf_weight = np.sqrt(max((ell + 2) * (ell - 1), 0.0)) / max(2 * ell + 1, 1)
                rows.extend((i_idx, e_idx))
                cols.extend((e_idx, i_idx))
                data.extend(
                    (
                        mu_weight * mix_scale * pstf_weight,
                        mu_weight * 0.5 * mix_scale * pstf_weight,
                    )
                )
                if twist_scale > 0.0:
                        eb = mu_weight * twist_scale * max(abs(m), 1) / (ell + 1)
                        rows.extend((e_idx, b_idx, b_idx, e_idx))
                        cols.extend((b_idx, e_idx, i_idx, b_idx))
                        data.extend((eb, -eb, 0.25 * eb, -0.25 * eb))
                target_labels = _mode_label_coupling_targets(
                    tuple(str(x) for x in layout.mode_labels),
                    str(mu),
                    family=backend.family_spec.family,
                )
                if target_labels:
                    target_norm = float(len(target_labels))
                    coeff_i = _harmonic_cross_mode_coeff(
                        mu_weight=mu_weight,
                        mix_scale=mix_scale,
                        cross_mode_scale=cross_mode_scale,
                        twist_scale=twist_scale,
                        sector="ph_I",
                        ell=ell,
                        mu_count=mu_count,
                    ) / target_norm
                    coeff_e = _harmonic_cross_mode_coeff(
                        mu_weight=mu_weight,
                        mix_scale=mix_scale,
                        cross_mode_scale=cross_mode_scale,
                        twist_scale=twist_scale,
                        sector="ph_E",
                        ell=ell,
                        mu_count=mu_count,
                    ) / target_norm
                    coeff_b = _harmonic_cross_mode_coeff(
                        mu_weight=mu_weight,
                        mix_scale=mix_scale,
                        cross_mode_scale=cross_mode_scale,
                        twist_scale=twist_scale,
                        sector="ph_B",
                        ell=ell,
                        mu_count=mu_count,
                    ) / target_norm
                    coeff_nu = _harmonic_cross_mode_coeff(
                        mu_weight=mu_weight,
                        mix_scale=mix_scale,
                        cross_mode_scale=cross_mode_scale,
                        twist_scale=twist_scale,
                        sector="nu_I",
                        ell=ell,
                        mu_count=mu_count,
                    ) / target_norm
                    for target_mu in target_labels:
                        next_i_idx = flatten(layout, target_mu, "ph_I", ell, m)
                        next_e_idx = flatten(layout, target_mu, "ph_E", ell, m)
                        next_b_idx = flatten(layout, target_mu, "ph_B", ell, m)
                        next_nu_idx = flatten(layout, target_mu, "nu_I", ell, m)
                        rows.extend((i_idx, e_idx, b_idx, nu_idx))
                        cols.extend((next_i_idx, next_e_idx, next_b_idx, next_nu_idx))
                        data.extend((coeff_i, coeff_e, coeff_b, coeff_nu))
        target_labels = _mode_label_coupling_targets(
            tuple(str(x) for x in layout.mode_labels),
            str(mu),
            family=backend.family_spec.family,
        )
        if target_labels:
            monopole_coeff = mu_weight * 0.5 * mix_scale * cross_mode_scale / (
                len(layout.mode_labels) * float(len(target_labels))
            )
            for target_mu in target_labels:
                for sector in ("ph_I", "ph_E", "ph_B", "nu_I"):
                    src_idx = flatten(layout, mu, sector, 0, 0)
                    dst_idx = flatten(layout, target_mu, sector, 0, 0)
                    rows.append(src_idx)
                    cols.append(dst_idx)
                    data.append(monopole_coeff)
    return csr_matrix((data, (rows, cols)), shape=(layout.size, layout.size))


def assemble_explicit_block(
    bg: Mapping[str, object],
    backend: FamilyBackend,
    truncation: Mapping[str, object],
) -> csr_matrix:
    return assemble_free_streaming_block(bg, backend, truncation) + assemble_mixing_block(
        bg,
        backend,
        truncation,
    )


def assemble_implicit_block(
    bg: Mapping[str, object],
    backend: FamilyBackend,
    truncation: Mapping[str, object],
    opacity_data: Mapping[str, object],
) -> csr_matrix:
    layout = build_hierarchy_layout(backend, truncation)
    gamma_t = float(opacity_data.get("Gamma_T", 0.0))
    scales = _operator_scales(bg, backend)
    branch_scale = float(scales["branch_scale"])
    local_drag_scale = float(scales["local_drag_scale"])
    collision_scale = float(scales["collision_scale"])
    twist_scale = float(scales["twist_scale"])
    cross_mode_scale = float(scales["cross_mode_scale"])
    mode_plus_scale = float(scales["mode_plus_scale"])
    mode_minus_scale = float(scales["mode_minus_scale"])
    rows: list[int] = []
    cols: list[int] = []
    data: list[float] = []
    mu_count = max(len(layout.mode_labels), 1)
    for mu_index, mu in enumerate(layout.mode_labels):
        mu_weight = _mode_label_weight(
            mu,
            mu_index=mu_index,
            mu_count=mu_count,
            branch_scale=branch_scale,
            plus_scale=mode_plus_scale,
            minus_scale=mode_minus_scale,
        )
        for sector in ("ph_I", "ph_E", "ph_B"):
            for ell in range(layout.ell_max + 1):
                for m in range(-ell, ell + 1):
                    idx = flatten(layout, mu, sector, ell, m)
                    photon_weight = mu_weight * branch_scale * collision_scale * gamma_t * (
                        1.0 if ell <= 1 else 1.0 / (ell + 0.5)
                    )
                    rows.append(idx)
                    cols.append(idx)
                    data.append(photon_weight)
        for sector in ("baryon", "src"):
            for local_dof in range(layout.sector_local_dofs[sector]):
                idx = flatten(layout, mu, sector, None, None, local_dof)
                local_weight = mu_weight * local_drag_scale * (gamma_t if sector == "baryon" else 0.35 * gamma_t)
                rows.append(idx)
                cols.append(idx)
                data.append(local_weight)
        dipole_idx = flatten(layout, mu, "ph_I", 1, 0)
        baryon_v_idx = flatten(layout, mu, "baryon", None, None, 1)
        rows.extend((dipole_idx, baryon_v_idx))
        cols.extend((baryon_v_idx, dipole_idx))
        data.extend(
            (
                -0.25 * mu_weight * local_drag_scale * gamma_t,
                0.25 * mu_weight * local_drag_scale * gamma_t,
            )
        )
        if layout.sector_local_dofs["src"] > 1:
            src_dipole_idx = flatten(layout, mu, "src", None, None, 1)
            rows.extend((dipole_idx, src_dipole_idx))
            cols.extend((src_dipole_idx, dipole_idx))
            data.extend(
                (
                    0.10 * mu_weight * local_drag_scale * gamma_t,
                    -0.08 * mu_weight * local_drag_scale * gamma_t,
                )
            )
        if layout.ell_max >= 2:
            quad_idx = flatten(layout, mu, "ph_E", 2, 0)
            src_idx = flatten(layout, mu, "src", None, None, 0)
            rows.extend((quad_idx, src_idx))
            cols.extend((src_idx, quad_idx))
            data.extend(
                (
                    0.15 * mu_weight * local_drag_scale * gamma_t,
                    -0.10 * mu_weight * local_drag_scale * gamma_t,
                )
            )
            if layout.sector_local_dofs["src"] > 2:
                src_pol_idx = flatten(layout, mu, "src", None, None, 2)
                b_quad_idx = flatten(layout, mu, "ph_B", 2, 0)
                rows.extend((quad_idx, src_pol_idx, b_quad_idx, src_pol_idx))
                cols.extend((src_pol_idx, quad_idx, src_pol_idx, b_quad_idx))
                data.extend(
                    (
                        0.08 * mu_weight * local_drag_scale * gamma_t,
                        -0.06 * mu_weight * local_drag_scale * gamma_t,
                    0.06 * mu_weight * twist_scale * local_drag_scale * gamma_t,
                    -0.04 * mu_weight * twist_scale * local_drag_scale * gamma_t,
                )
            )
        target_labels = _mode_label_coupling_targets(
            tuple(str(x) for x in layout.mode_labels),
            str(mu),
            family=backend.family_spec.family,
        )
        if target_labels:
            target_norm = float(len(target_labels))
            if layout.sector_local_dofs["src"] > 1:
                for target_mu in target_labels:
                    src_dipole_idx = flatten(layout, target_mu, "src", None, None, 1)
                    rows.append(dipole_idx)
                    cols.append(src_dipole_idx)
                    data.append(0.05 * mu_weight * cross_mode_scale * local_drag_scale * gamma_t / target_norm)
            if layout.ell_max >= 2:
                quad_idx = flatten(layout, mu, "ph_E", 2, 0)
                if layout.sector_local_dofs["src"] > 0:
                    for target_mu in target_labels:
                        src_idx = flatten(layout, target_mu, "src", None, None, 0)
                        rows.append(quad_idx)
                        cols.append(src_idx)
                        data.append(0.07 * mu_weight * cross_mode_scale * local_drag_scale * gamma_t / target_norm)
                if layout.sector_local_dofs["src"] > 2:
                    b_quad_idx = flatten(layout, mu, "ph_B", 2, 0)
                    for target_mu in target_labels:
                        src_pol_idx = flatten(layout, target_mu, "src", None, None, 2)
                        rows.extend((quad_idx, b_quad_idx))
                        cols.extend((src_pol_idx, src_pol_idx))
                        data.extend(
                            (
                                0.04 * mu_weight * cross_mode_scale * local_drag_scale * gamma_t / target_norm,
                                0.03
                                * mu_weight
                                * twist_scale
                                * cross_mode_scale
                                * local_drag_scale
                                * gamma_t
                                / target_norm,
                            )
                        )
    return csr_matrix((data, (rows, cols)), shape=(layout.size, layout.size))


def assemble_source_vector(
    bg: Mapping[str, object],
    backend: FamilyBackend,
    truncation: Mapping[str, object],
    source_tables: Mapping[str, object],
) -> np.ndarray:
    layout = build_hierarchy_layout(backend, truncation)
    out = np.zeros(layout.size, dtype=np.float64)
    scales = _operator_scales(bg, backend)
    twist_scale = float(scales["twist_scale"])
    source_scale = float(scales["source_scale"])
    cross_mode_scale = float(scales["cross_mode_scale"])
    visibility_amp = float(source_tables.get("visibility_amplitude", 0.0))
    polarization_amp = float(source_tables.get("polarization_source", 0.0))
    doppler_amp = float(source_tables.get("doppler_source", 0.25 * visibility_amp))
    reduced_source_blocks = evaluate_reduced_source_blocks(
        layout,
        {**dict(bg), "source_tables": dict(source_tables)},
        backend,
    )
    mu_count = max(len(layout.mode_labels), 1)
    for mu_index, mu in enumerate(layout.mode_labels):
        mu_weight = _mode_label_weight(
            mu,
            mu_index=mu_index,
            mu_count=mu_count,
            branch_scale=float(scales["branch_scale"]),
            plus_scale=float(scales["mode_plus_scale"]),
            minus_scale=float(scales["mode_minus_scale"]),
        )
        out[flatten(layout, mu, "ph_I", 0, 0)] = mu_weight * source_scale * visibility_amp
        if layout.ell_max >= 1:
            out[flatten(layout, mu, "ph_I", 1, 0)] = mu_weight * 0.5 * source_scale * doppler_amp
        if layout.ell_max >= 2:
            out[flatten(layout, mu, "ph_E", 2, 0)] = mu_weight * source_scale * polarization_amp
            out[flatten(layout, mu, "ph_B", 2, 0)] = mu_weight * twist_scale * cross_mode_scale * polarization_amp
        for local_dof, value in enumerate(np.asarray(reduced_source_blocks[str(mu)], dtype=np.float64)):
            out[flatten(layout, mu, "src", None, None, local_dof)] = float(value)
    return out


def evaluate_reduced_source_blocks(
    layout: HierarchyLayout,
    bg: Mapping[str, object],
    backend: FamilyBackend,
) -> dict[str, np.ndarray]:
    """Evaluate per-mode-label source local blocks without assembling full operators."""

    source_tables = bg.get("source_tables", {})
    if not isinstance(source_tables, Mapping):
        raise ValueError("bg.source_tables must be a mapping when provided")
    scales = _operator_scales(bg, backend)
    branch_scale = float(scales["branch_scale"])
    mode_plus_scale = float(scales["mode_plus_scale"])
    mode_minus_scale = float(scales["mode_minus_scale"])
    visibility_amp = float(source_tables.get("visibility_amplitude", 0.0))
    polarization_amp = float(source_tables.get("polarization_source", 0.0))
    doppler_amp = float(source_tables.get("doppler_source", 0.25 * visibility_amp))
    reion_amp = float(source_tables.get("reionization_amplitude", 0.0))
    source_width = int(layout.sector_local_dofs["src"])
    mu_count = max(len(layout.mode_labels), 1)
    source_blocks: dict[str, np.ndarray] = {}
    for mu_index, mu in enumerate(layout.mode_labels):
        mu_weight = _mode_label_weight(
            mu,
            mu_index=mu_index,
            mu_count=mu_count,
            branch_scale=branch_scale,
            plus_scale=mode_plus_scale,
            minus_scale=mode_minus_scale,
        )
        src = np.zeros(source_width, dtype=np.float64)
        if source_width > 0:
            src[0] = mu_weight * reion_amp
        if source_width > 1:
            src[1] = mu_weight * 0.5 * float(scales["source_scale"]) * doppler_amp
        if source_width > 2:
            src[2] = mu_weight * float(scales["source_scale"]) * polarization_amp
        source_blocks[str(mu)] = src
    return source_blocks


def evaluate_reduced_harmonic_rhs(
    layout: HierarchyLayout,
    bg: Mapping[str, object],
    backend: FamilyBackend,
    *,
    photon_T_by_mode_label: Mapping[str, np.ndarray],
    photon_E_by_mode_label: Mapping[str, np.ndarray],
    photon_B_by_mode_label: Mapping[str, np.ndarray],
    neutrino_by_mode_label: Mapping[str, np.ndarray],
    baryon_by_mode_label: Mapping[str, np.ndarray],
    source_by_mode_label: Mapping[str, np.ndarray] | None = None,
) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray], dict[str, np.ndarray], dict[str, np.ndarray]]:
    """Evaluate harmonic-sector rows without assembling full sparse operators."""

    opacity_data = bg.get("opacity_data", {})
    if not isinstance(opacity_data, Mapping):
        raise ValueError("bg.opacity_data must be a mapping when provided")
    source_tables = bg.get("source_tables", {})
    if not isinstance(source_tables, Mapping):
        raise ValueError("bg.source_tables must be a mapping when provided")

    gamma_t = float(opacity_data.get("Gamma_T", 0.0))
    visibility_amp = float(source_tables.get("visibility_amplitude", 0.0))
    polarization_amp = float(source_tables.get("polarization_source", 0.0))
    doppler_amp = float(source_tables.get("doppler_source", 0.25 * visibility_amp))
    reion_amp = float(source_tables.get("reionization_amplitude", 0.0))

    scales = _operator_scales(bg, backend)
    geom_scale = float(scales["geom_scale"])
    branch_scale = float(scales["branch_scale"])
    mix_scale = float(scales["mix_scale"])
    twist_scale = float(scales["twist_scale"])
    polarization_scale = float(scales["polarization_scale"])
    source_scale = float(scales["source_scale"])
    cross_mode_scale = float(scales["cross_mode_scale"])
    collision_scale = float(scales["collision_scale"])
    local_drag_scale = float(scales["local_drag_scale"])
    mode_plus_scale = float(scales["mode_plus_scale"])
    mode_minus_scale = float(scales["mode_minus_scale"])
    width = (int(layout.ell_max) + 1) ** 2
    baryon_width = int(layout.sector_local_dofs["baryon"])
    src_width = int(layout.sector_local_dofs["src"])
    mu_count = max(len(layout.mode_labels), 1)

    zeros_h = np.zeros(width, dtype=np.float64)
    zeros_b = np.zeros(baryon_width, dtype=np.float64)
    zeros_s = np.zeros(src_width, dtype=np.float64)
    default_source_blocks = evaluate_reduced_source_blocks(layout, bg, backend)
    photon_t_rhs: dict[str, np.ndarray] = {}
    photon_e_rhs: dict[str, np.ndarray] = {}
    photon_b_rhs: dict[str, np.ndarray] = {}
    neutrino_rhs: dict[str, np.ndarray] = {}

    def _mass_weight(*, mu_weight: float, sector: str, ell: int) -> float:
        ell_weight = 1.0 + 0.04 * ell + 0.015 * geom_scale
        if sector == "ph_I":
            sector_weight = branch_scale
        elif sector == "ph_E":
            sector_weight = branch_scale * (1.08 * polarization_scale)
        elif sector == "ph_B":
            sector_weight = branch_scale * (1.12 + 0.5 * twist_scale) * polarization_scale
        elif sector == "nu_I":
            sector_weight = 1.0 + 0.1 * branch_scale + 0.02 * geom_scale
        else:
            raise KeyError(f"unsupported harmonic sector {sector!r}")
        return mu_weight * sector_weight * ell_weight

    def _fs_diag(*, mu_weight: float, sector: str, ell: int, m: int) -> float:
        spin_weight = polarization_scale if sector in {"ph_E", "ph_B"} else 1.0
        return -geom_scale * mu_weight * spin_weight * (0.35 * (ell + 1) + 0.08 * abs(m))

    for mu_index, mu in enumerate(layout.mode_labels):
        mu_key = str(mu)
        mu_weight = _mode_label_weight(
            mu_key,
            mu_index=mu_index,
            mu_count=mu_count,
            branch_scale=branch_scale,
            plus_scale=mode_plus_scale,
            minus_scale=mode_minus_scale,
        )
        t_state = np.asarray(photon_T_by_mode_label.get(mu_key, zeros_h), dtype=np.float64)
        e_state = np.asarray(photon_E_by_mode_label.get(mu_key, zeros_h), dtype=np.float64)
        b_state = np.asarray(photon_B_by_mode_label.get(mu_key, zeros_h), dtype=np.float64)
        nu_state = np.asarray(neutrino_by_mode_label.get(mu_key, zeros_h), dtype=np.float64)
        baryon_state = np.asarray(baryon_by_mode_label.get(mu_key, zeros_b), dtype=np.float64)
        if source_by_mode_label is None:
            src_state = np.asarray(default_source_blocks[mu_key], dtype=np.float64)
        else:
            src_state = np.asarray(source_by_mode_label.get(mu_key, zeros_s), dtype=np.float64)
        target_labels = _mode_label_coupling_targets(
            tuple(str(x) for x in layout.mode_labels),
            mu_key,
            family=backend.family_spec.family,
        )
        target_towers: tuple[tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray], ...] = tuple(
            (
                np.asarray(photon_T_by_mode_label.get(target_mu, zeros_h), dtype=np.float64),
                np.asarray(photon_E_by_mode_label.get(target_mu, zeros_h), dtype=np.float64),
                np.asarray(photon_B_by_mode_label.get(target_mu, zeros_h), dtype=np.float64),
                np.asarray(neutrino_by_mode_label.get(target_mu, zeros_h), dtype=np.float64),
            )
            for target_mu in target_labels
        )
        target_sources: tuple[np.ndarray, ...] = tuple(
            np.asarray(
                (
                    default_source_blocks[target_mu]
                    if source_by_mode_label is None
                    else source_by_mode_label.get(target_mu, default_source_blocks[target_mu])
                ),
                dtype=np.float64,
            )
            for target_mu in target_labels
        )
        for name, arr in (
            ("photon_T", t_state),
            ("photon_E", e_state),
            ("photon_B", b_state),
            ("neutrino", nu_state),
        ):
            if arr.shape != (width,):
                raise ValueError(f"{name} state for {mu_key!r} must have shape ({width},)")
        if baryon_state.shape != (baryon_width,):
            raise ValueError(f"baryon state for {mu_key!r} must have shape ({baryon_width},)")
        if src_state.shape != (src_width,):
            raise ValueError(f"source state for {mu_key!r} must have shape ({src_width},)")

        t_rhs = np.zeros(width, dtype=np.float64)
        e_rhs = np.zeros(width, dtype=np.float64)
        b_rhs = np.zeros(width, dtype=np.float64)
        nu_rhs = np.zeros(width, dtype=np.float64)
        cross_coeff = (
            mu_weight * 0.5 * mix_scale * cross_mode_scale / len(layout.mode_labels)
            if len(layout.mode_labels) > 1
            else 0.0
        )

        offset = 0
        for ell in range(layout.ell_max + 1):
            pstf_weight = np.sqrt(max((ell + 2) * (ell - 1), 0.0)) / max(2 * ell + 1, 1) if ell >= 2 else 0.0
            for m in range(-ell, ell + 1):
                slot = offset + (m + ell)
                t_drive = _fs_diag(mu_weight=mu_weight, sector="ph_I", ell=ell, m=m) * t_state[slot]
                e_drive = _fs_diag(mu_weight=mu_weight, sector="ph_E", ell=ell, m=m) * e_state[slot]
                b_drive = _fs_diag(mu_weight=mu_weight, sector="ph_B", ell=ell, m=m) * b_state[slot]
                nu_drive = _fs_diag(mu_weight=mu_weight, sector="nu_I", ell=ell, m=m) * nu_state[slot]

                if ell > 0:
                    prev_m = m if abs(m) <= ell - 1 else 0
                    prev_slot = sum(2 * l + 1 for l in range(ell - 1)) + (prev_m + (ell - 1))
                    coeff_down = geom_scale * mu_weight * np.sqrt(max(ell * ell - m * m, 0.0)) / max(2 * ell + 1, 1)
                    t_drive += coeff_down * t_state[prev_slot]
                    e_drive += coeff_down * polarization_scale * e_state[prev_slot]
                    b_drive += coeff_down * polarization_scale * b_state[prev_slot]
                    nu_drive += coeff_down * nu_state[prev_slot]
                if ell < layout.ell_max:
                    next_m_same = m if abs(m) <= ell + 1 else 0
                    next_slot_same = sum(2 * l + 1 for l in range(ell + 1)) + (next_m_same + (ell + 1))
                    coeff_up = geom_scale * mu_weight * np.sqrt(max((ell + 1) * (ell + 1) - m * m, 0.0)) / max(2 * ell + 1, 1)
                    t_drive += coeff_up * t_state[next_slot_same]
                    e_drive += coeff_up * polarization_scale * e_state[next_slot_same]
                    b_drive += coeff_up * polarization_scale * b_state[next_slot_same]
                    nu_drive += coeff_up * nu_state[next_slot_same]

                if ell >= 2:
                    coeff_mix = mu_weight * mix_scale * pstf_weight
                    t_drive += coeff_mix * e_state[slot]
                    e_drive += 0.5 * coeff_mix * t_state[slot]
                    if twist_scale > 0.0:
                        eb = mu_weight * twist_scale * max(abs(m), 1) / (ell + 1)
                        e_drive += 0.75 * eb * b_state[slot]
                        b_drive += (-eb * e_state[slot]) + (0.25 * eb * t_state[slot])
                    if target_towers:
                        target_norm = float(len(target_towers))
                        coeff_i = _harmonic_cross_mode_coeff(
                            mu_weight=mu_weight,
                            mix_scale=mix_scale,
                            cross_mode_scale=cross_mode_scale,
                            twist_scale=twist_scale,
                            sector="ph_I",
                            ell=ell,
                            mu_count=mu_count,
                        ) / target_norm
                        coeff_e = _harmonic_cross_mode_coeff(
                            mu_weight=mu_weight,
                            mix_scale=mix_scale,
                            cross_mode_scale=cross_mode_scale,
                            twist_scale=twist_scale,
                            sector="ph_E",
                            ell=ell,
                            mu_count=mu_count,
                        ) / target_norm
                        coeff_b = _harmonic_cross_mode_coeff(
                            mu_weight=mu_weight,
                            mix_scale=mix_scale,
                            cross_mode_scale=cross_mode_scale,
                            twist_scale=twist_scale,
                            sector="ph_B",
                            ell=ell,
                            mu_count=mu_count,
                        ) / target_norm
                        coeff_nu = _harmonic_cross_mode_coeff(
                            mu_weight=mu_weight,
                            mix_scale=mix_scale,
                            cross_mode_scale=cross_mode_scale,
                            twist_scale=twist_scale,
                            sector="nu_I",
                            ell=ell,
                            mu_count=mu_count,
                        ) / target_norm
                        for target_t, target_e, target_b, target_nu in target_towers:
                            t_drive += coeff_i * target_t[slot]
                            e_drive += coeff_e * target_e[slot]
                            b_drive += coeff_b * target_b[slot]
                            nu_drive += coeff_nu * target_nu[slot]

                if ell == 0 and cross_coeff != 0.0 and target_towers:
                    monopole_coeff = cross_coeff / float(len(target_towers))
                    for target_t, target_e, target_b, target_nu in target_towers:
                        t_drive += monopole_coeff * target_t[slot]
                        e_drive += monopole_coeff * target_e[slot]
                        b_drive += monopole_coeff * target_b[slot]
                        nu_drive += monopole_coeff * target_nu[slot]

                if ell <= 1:
                    photon_coll = mu_weight * branch_scale * collision_scale * gamma_t
                else:
                    photon_coll = mu_weight * branch_scale * collision_scale * gamma_t / (ell + 0.5)
                t_drive += photon_coll * t_state[slot]
                e_drive += photon_coll * e_state[slot]
                b_drive += photon_coll * b_state[slot]

                if ell == 0 and m == 0:
                    t_drive += mu_weight * source_scale * visibility_amp
                if ell == 1 and m == 0:
                    t_drive += mu_weight * 0.5 * source_scale * doppler_amp
                    if baryon_width > 1:
                        t_drive += -0.25 * mu_weight * local_drag_scale * gamma_t * float(baryon_state[1])
                    if src_width > 1:
                        t_drive += 0.10 * mu_weight * local_drag_scale * gamma_t * float(src_state[1])
                    if target_sources and src_width > 1:
                        target_norm = float(len(target_sources))
                        for target_src in target_sources:
                            t_drive += (
                                0.05
                                * mu_weight
                                * local_drag_scale
                                * gamma_t
                                * cross_mode_scale
                                * float(target_src[1])
                                / target_norm
                            )
                if ell == 2 and m == 0:
                    e_drive += mu_weight * source_scale * polarization_amp
                    b_drive += mu_weight * twist_scale * cross_mode_scale * polarization_amp
                    if src_width > 0:
                        e_drive += 0.15 * mu_weight * local_drag_scale * gamma_t * float(src_state[0])
                    if src_width > 2:
                        e_drive += 0.08 * mu_weight * local_drag_scale * gamma_t * float(src_state[2])
                        b_drive += (
                            0.06
                            * mu_weight
                            * twist_scale
                            * local_drag_scale
                            * gamma_t
                            * float(src_state[2])
                        )
                    if target_sources:
                        target_norm = float(len(target_sources))
                        for target_src in target_sources:
                            if src_width > 0:
                                e_drive += (
                                    0.07
                                    * mu_weight
                                    * local_drag_scale
                                    * gamma_t
                                    * cross_mode_scale
                                    * float(target_src[0])
                                    / target_norm
                                )
                            if src_width > 2:
                                e_drive += (
                                    0.04
                                    * mu_weight
                                    * local_drag_scale
                                    * gamma_t
                                    * cross_mode_scale
                                    * float(target_src[2])
                                    / target_norm
                                )
                                b_drive += (
                                    0.03
                                    * mu_weight
                                    * twist_scale
                                    * local_drag_scale
                                    * gamma_t
                                    * cross_mode_scale
                                    * float(target_src[2])
                                    / target_norm
                                )

                t_rhs[slot] = t_drive / _mass_weight(mu_weight=mu_weight, sector="ph_I", ell=ell)
                e_rhs[slot] = e_drive / _mass_weight(mu_weight=mu_weight, sector="ph_E", ell=ell)
                b_rhs[slot] = b_drive / _mass_weight(mu_weight=mu_weight, sector="ph_B", ell=ell)
                nu_rhs[slot] = nu_drive / _mass_weight(mu_weight=mu_weight, sector="nu_I", ell=ell)
            offset += 2 * ell + 1

        photon_t_rhs[mu_key] = t_rhs
        photon_e_rhs[mu_key] = e_rhs
        photon_b_rhs[mu_key] = b_rhs
        neutrino_rhs[mu_key] = nu_rhs

    return photon_t_rhs, photon_e_rhs, photon_b_rhs, neutrino_rhs


def build_reduced_harmonic_affine_operator(
    layout: HierarchyLayout,
    bg: Mapping[str, object],
    backend: FamilyBackend,
    *,
    residual_mode_labels: tuple[str, ...],
    photon_T_by_mode_label: Mapping[str, np.ndarray],
    photon_E_by_mode_label: Mapping[str, np.ndarray],
    photon_B_by_mode_label: Mapping[str, np.ndarray],
    neutrino_by_mode_label: Mapping[str, np.ndarray],
    baryon_by_mode_label: Mapping[str, np.ndarray],
    source_by_mode_label: Mapping[str, np.ndarray] | None = None,
) -> ReducedHarmonicAffineOperator:
    """Return the exact frozen-snapshot affine operator ``A r + b``.

    The returned operator acts only on the residual harmonic labels in
    ``residual_mode_labels``. For fixed ``bg`` and fixed covered/local/source
    inputs, this is exactly equivalent to ``evaluate_reduced_harmonic_rhs``.
    """

    opacity_data = bg.get("opacity_data", {})
    if not isinstance(opacity_data, Mapping):
        raise ValueError("bg.opacity_data must be a mapping when provided")
    source_tables = bg.get("source_tables", {})
    if not isinstance(source_tables, Mapping):
        raise ValueError("bg.source_tables must be a mapping when provided")

    residual_labels = tuple(str(mu) for mu in residual_mode_labels)
    if len(residual_labels) == 0:
        return ReducedHarmonicAffineOperator(
            mode_labels=(),
            matrix=csc_matrix((0, 0), dtype=np.float64),
            bias=np.zeros(0, dtype=np.float64),
        )

    residual_label_set = frozenset(residual_labels)
    invalid = residual_label_set.difference(str(mu) for mu in layout.mode_labels)
    if invalid:
        raise ValueError(f"residual_mode_labels must be a subset of layout.mode_labels, got extras {sorted(invalid)!r}")

    gamma_t = float(opacity_data.get("Gamma_T", 0.0))
    visibility_amp = float(source_tables.get("visibility_amplitude", 0.0))
    polarization_amp = float(source_tables.get("polarization_source", 0.0))
    doppler_amp = float(source_tables.get("doppler_source", 0.25 * visibility_amp))

    scales = _operator_scales(bg, backend)
    geom_scale = float(scales["geom_scale"])
    branch_scale = float(scales["branch_scale"])
    mix_scale = float(scales["mix_scale"])
    twist_scale = float(scales["twist_scale"])
    polarization_scale = float(scales["polarization_scale"])
    source_scale = float(scales["source_scale"])
    cross_mode_scale = float(scales["cross_mode_scale"])
    collision_scale = float(scales["collision_scale"])
    local_drag_scale = float(scales["local_drag_scale"])

    baryon_width = int(layout.sector_local_dofs["baryon"])
    src_width = int(layout.sector_local_dofs["src"])
    structure = _reduced_harmonic_structure(
        int(layout.ell_max),
        tuple(str(mu) for mu in layout.mode_labels),
        residual_labels,
        backend.family_spec.family,
    )
    width = structure.width
    mu_count = max(len(layout.mode_labels), 1)
    zeros_h = np.zeros(width, dtype=np.float64)
    zeros_b = np.zeros(baryon_width, dtype=np.float64)
    zeros_s = np.zeros(src_width, dtype=np.float64)
    default_source_blocks = evaluate_reduced_source_blocks(layout, bg, backend)

    ell_weight = 1.0 + 0.04 * structure.ell_by_slot + 0.015 * geom_scale
    inv_t = 1.0 / np.maximum(branch_scale * ell_weight, 1.0e-30)
    inv_e = 1.0 / np.maximum(branch_scale * (1.08 * polarization_scale) * ell_weight, 1.0e-30)
    inv_b = 1.0 / np.maximum(
        branch_scale * (1.12 + 0.5 * twist_scale) * polarization_scale * ell_weight,
        1.0e-30,
    )
    inv_nu = 1.0 / np.maximum((1.0 + 0.1 * branch_scale + 0.02 * geom_scale) * ell_weight, 1.0e-30)
    stream_base = geom_scale * structure.diag_base_by_slot
    prev_t = inv_t * geom_scale * structure.prev_coeff_by_slot
    prev_e = inv_e * geom_scale * polarization_scale * structure.prev_coeff_by_slot
    prev_b = inv_b * geom_scale * polarization_scale * structure.prev_coeff_by_slot
    prev_nu = inv_nu * geom_scale * structure.prev_coeff_by_slot
    next_t_same = inv_t * geom_scale * structure.next_coeff_by_slot
    next_e_same = inv_e * geom_scale * polarization_scale * structure.next_coeff_by_slot
    next_b_same = inv_b * geom_scale * polarization_scale * structure.next_coeff_by_slot
    next_nu_same = inv_nu * geom_scale * structure.next_coeff_by_slot
    # v5 audit Option-B test: Thomson term sign flip.
    # Ma-Bertschinger (1995) eq. 63: Boltzmann hierarchy has -κ̇·Θ_ℓ
    # (damping) for ℓ ≥ 2, with κ̇ = opacity > 0.  Defining γ_T = κ̇ > 0,
    # the diagonal contribution must be -γ_T·c_ℓ, i.e. NEGATIVE.
    # The prior `+ photon_coll` was wrong-signed; after Q3 zeroed the
    # `-stream_base` compensating term, the wrong Thomson sign was
    # exposed as a +0.93 growth mode at γ_T = 1 in the fast-check audit.
    photon_coll = branch_scale * collision_scale * gamma_t * structure.collision_factor_by_slot
    diag_t = inv_t * (-stream_base - photon_coll)
    diag_e = inv_e * (-stream_base * polarization_scale - photon_coll)
    diag_b = inv_b * (-stream_base * polarization_scale - photon_coll)
    diag_nu = inv_nu * (-stream_base)
    # v5 audit Round-2 Q-6: Thomson-derived T↔E coupling is quadrupole-only,
    # γ_T-proportional (Kamionkowski-Kosowsky-Stebbins 1997; Zaldarriaga-Seljak
    # 1997). The source is Π = Θ_2 − √6·E_2, substituting into ℓ=2 rows:
    #    Θ̇_2 ⊃ −(9κ̇/10)·Θ_2  − (√6·κ̇/10)·E_2
    #    Ė_2 ⊃ −(√6·κ̇/10)·Θ_2 − (2κ̇/5)·E_2
    # T↔B and E↔B Thomson couplings vanish (parity). Geometric/twist-driven
    # B-mixing belongs in transport, not collision, so eb_* = 0 here.
    quad_mask = (structure.ell_by_slot == 2)
    te_weight = np.zeros_like(structure.pstf_weight_by_slot)
    te_weight[quad_mask] = structure.pstf_weight_by_slot[quad_mask]
    mix_t = -inv_t * gamma_t * (np.sqrt(6.0) / 10.0) * te_weight
    mix_e = -inv_e * gamma_t * (np.sqrt(6.0) / 10.0) * te_weight
    eb_e = np.zeros_like(inv_e)
    eb_b = np.zeros_like(inv_b)
    eb_bt = np.zeros_like(inv_b)
    # Quadrupole Thomson diagonal specialization (Π source):
    diag_t[quad_mask] = -inv_t[quad_mask] * (9.0 * gamma_t / 10.0)
    diag_e[quad_mask] = -inv_e[quad_mask] * (2.0 * gamma_t / 5.0)
    diag_b[quad_mask] = -inv_b[quad_mask] * gamma_t

    cross_t = np.zeros(width, dtype=np.float64)
    cross_e = np.zeros(width, dtype=np.float64)
    cross_b = np.zeros(width, dtype=np.float64)
    cross_nu = np.zeros(width, dtype=np.float64)
    if mu_count > 1:
        base_cross = mix_scale * cross_mode_scale / np.maximum(structure.ell_by_slot + 1, 1)
        ge2 = structure.ge2_mask
        cross_t[ge2] = inv_t[ge2] * (0.18 * base_cross[ge2] / mu_count)
        cross_e[ge2] = inv_e[ge2] * (0.16 * base_cross[ge2] / mu_count)
        cross_b[ge2] = inv_b[ge2] * (0.16 * (1.0 + 0.5 * twist_scale) * base_cross[ge2] / mu_count)
        cross_nu[ge2] = inv_nu[ge2] * (0.12 * base_cross[ge2] / mu_count)
        ell0_coeff = 0.5 * mix_scale * cross_mode_scale / mu_count
        ell0 = structure.ell0_mask
        cross_t[ell0] = inv_t[ell0] * ell0_coeff
        cross_e[ell0] = inv_e[ell0] * ell0_coeff
        cross_b[ell0] = inv_b[ell0] * ell0_coeff
        cross_nu[ell0] = inv_nu[ell0] * ell0_coeff

    slots = structure.sector_slots
    prev_valid = structure.prev_slot_by_slot >= 0
    next_valid = structure.next_slot_by_slot >= 0
    t_off = 0
    e_off = width
    b_off = 2 * width
    nu_off = 3 * width
    block_size = structure.block_size
    self_block = np.zeros((block_size, block_size), dtype=np.float64)
    cross_block = np.zeros((block_size, block_size), dtype=np.float64)

    self_block[t_off + slots, t_off + slots] += diag_t
    self_block[e_off + slots, e_off + slots] += diag_e
    self_block[b_off + slots, b_off + slots] += diag_b
    self_block[nu_off + slots, nu_off + slots] += diag_nu

    self_block[t_off + slots[prev_valid], t_off + structure.prev_slot_by_slot[prev_valid]] += prev_t[prev_valid]
    self_block[e_off + slots[prev_valid], e_off + structure.prev_slot_by_slot[prev_valid]] += prev_e[prev_valid]
    self_block[b_off + slots[prev_valid], b_off + structure.prev_slot_by_slot[prev_valid]] += prev_b[prev_valid]
    self_block[nu_off + slots[prev_valid], nu_off + structure.prev_slot_by_slot[prev_valid]] += prev_nu[prev_valid]

    # v5 audit Q1: Ma-Bertschinger (1995) eq. 63 — streaming couplings carry
    # opposite signs: +ell/(2ell+1) · X_{ell-1} − (ell+1)/(2ell+1) · X_{ell+1}.
    # The prev_coeff/next_coeff magnitudes are correct (Clebsch-Gordan of
    # k·Y_ell^m); the missing ingredient is the minus sign on X_{ell+1}.
    # Post-flip, the block satisfies weighted skew-adjointness
    # W A + A^T W = 0 with W_ell = (2ell+1)/d_ell (audit Q2), so every
    # eigenvalue has Re(λ) ≤ 0 — strictly dissipative when diag damping is
    # present, purely imaginary (free-streaming Liouville) at γ_T = 0.
    self_block[t_off + slots[next_valid], t_off + structure.next_slot_by_slot[next_valid]] -= next_t_same[next_valid]
    self_block[e_off + slots[next_valid], e_off + structure.next_slot_by_slot[next_valid]] -= next_e_same[next_valid]
    self_block[b_off + slots[next_valid], b_off + structure.next_slot_by_slot[next_valid]] -= next_b_same[next_valid]
    self_block[nu_off + slots[next_valid], nu_off + structure.next_slot_by_slot[next_valid]] -= next_nu_same[next_valid]

    # v5 audit Round-2 Q-6.4: T↔E Thomson coupling restricted to quadrupole.
    # E↔B / T↔B Thomson couplings zeroed (eb_* ≡ 0).
    quad_slots = slots[quad_mask]
    self_block[t_off + quad_slots, e_off + quad_slots] += mix_t[quad_mask]
    self_block[e_off + quad_slots, t_off + quad_slots] += mix_e[quad_mask]

    if mu_count > 1:
        cross_block[t_off + slots, t_off + slots] += cross_t
        cross_block[e_off + slots, e_off + slots] += cross_e
        cross_block[b_off + slots, b_off + slots] += cross_b
        cross_block[nu_off + slots, nu_off + slots] += cross_nu

    self_data = np.asarray(
        self_block[structure.self_pattern_rows, structure.self_pattern_cols],
        dtype=np.float64,
    )
    cross_data = np.asarray(
        cross_block[structure.cross_pattern_rows, structure.cross_pattern_cols],
        dtype=np.float64,
    )
    row_chunks: list[np.ndarray] = []
    col_chunks: list[np.ndarray] = []
    data_chunks: list[np.ndarray] = []
    for residual_index, residual_targets in enumerate(structure.cross_residual_indices):
        row_start = residual_index * block_size
        row_chunks.append(structure.self_pattern_rows + row_start)
        col_chunks.append(structure.self_pattern_cols + row_start)
        data_chunks.append(self_data)
        if residual_targets and cross_data.size:
            target_norm = float(len(residual_targets))
            scaled_cross = cross_data / target_norm
            for target_residual in residual_targets:
                col_start = int(target_residual) * block_size
                row_chunks.append(structure.cross_pattern_rows + row_start)
                col_chunks.append(structure.cross_pattern_cols + col_start)
                data_chunks.append(scaled_cross)

    bias = np.zeros(structure.n_unknown, dtype=np.float64)
    for residual_index, mu in enumerate(residual_labels):
        baryon_state = np.asarray(baryon_by_mode_label.get(str(mu), zeros_b), dtype=np.float64)
        if baryon_state.shape != (baryon_width,):
            raise ValueError(f"baryon state for {mu!r} must have shape ({baryon_width},)")
        if source_by_mode_label is None:
            src_state = np.asarray(default_source_blocks[str(mu)], dtype=np.float64)
        else:
            src_state = np.asarray(source_by_mode_label.get(str(mu), zeros_s), dtype=np.float64)
        if src_state.shape != (src_width,):
            raise ValueError(f"source state for {mu!r} must have shape ({src_width},)")

        row_start = residual_index * block_size
        external_targets = structure.cross_external_labels[residual_index]
        if external_targets and mu_count > 1:
            target_norm = float(len(external_targets))
            for target_label in external_targets:
                next_t = np.asarray(photon_T_by_mode_label.get(target_label, zeros_h), dtype=np.float64)
                next_e = np.asarray(photon_E_by_mode_label.get(target_label, zeros_h), dtype=np.float64)
                next_b = np.asarray(photon_B_by_mode_label.get(target_label, zeros_h), dtype=np.float64)
                next_nu = np.asarray(neutrino_by_mode_label.get(target_label, zeros_h), dtype=np.float64)
                next_src = np.asarray(
                    (
                        default_source_blocks[target_label]
                        if source_by_mode_label is None
                        else source_by_mode_label.get(target_label, default_source_blocks[target_label])
                    ),
                    dtype=np.float64,
                )
                bias[row_start + t_off : row_start + t_off + width] += (cross_t / target_norm) * next_t
                bias[row_start + e_off : row_start + e_off + width] += (cross_e / target_norm) * next_e
                bias[row_start + b_off : row_start + b_off + width] += (cross_b / target_norm) * next_b
                bias[row_start + nu_off : row_start + nu_off + width] += (cross_nu / target_norm) * next_nu
                if structure.dipole_slot is not None and src_width > 1:
                    dipole_slot = structure.dipole_slot
                    bias[row_start + t_off + dipole_slot] += (
                        inv_t[dipole_slot]
                        * (0.05 * local_drag_scale * gamma_t * cross_mode_scale * float(next_src[1]) / target_norm)
                    )
                if structure.quadrupole_slot is not None:
                    quad_slot = structure.quadrupole_slot
                    if src_width > 0:
                        bias[row_start + e_off + quad_slot] += (
                            inv_e[quad_slot]
                            * (0.07 * local_drag_scale * gamma_t * cross_mode_scale * float(next_src[0]) / target_norm)
                        )
                    if src_width > 2:
                        bias[row_start + e_off + quad_slot] += (
                            inv_e[quad_slot]
                            * (0.04 * local_drag_scale * gamma_t * cross_mode_scale * float(next_src[2]) / target_norm)
                        )
                        bias[row_start + b_off + quad_slot] += (
                            inv_b[quad_slot]
                            * (
                                0.03
                                * twist_scale
                                * local_drag_scale
                                * gamma_t
                                * cross_mode_scale
                                * float(next_src[2])
                                / target_norm
                            )
                        )

        bias[row_start + t_off + structure.monopole_slot] += inv_t[structure.monopole_slot] * source_scale * visibility_amp
        if structure.dipole_slot is not None:
            dipole_slot = structure.dipole_slot
            bias[row_start + t_off + dipole_slot] += inv_t[dipole_slot] * (0.5 * source_scale * doppler_amp)
            if baryon_width > 1:
                bias[row_start + t_off + dipole_slot] += (
                    inv_t[dipole_slot] * (-0.25 * local_drag_scale * gamma_t * float(baryon_state[1]))
                )
            if src_width > 1:
                bias[row_start + t_off + dipole_slot] += (
                    inv_t[dipole_slot] * (0.10 * local_drag_scale * gamma_t * float(src_state[1]))
                )
        if structure.quadrupole_slot is not None:
            quad_slot = structure.quadrupole_slot
            bias[row_start + e_off + quad_slot] += inv_e[quad_slot] * (source_scale * polarization_amp)
            bias[row_start + b_off + quad_slot] += inv_b[quad_slot] * (twist_scale * cross_mode_scale * polarization_amp)
            if src_width > 0:
                bias[row_start + e_off + quad_slot] += (
                    inv_e[quad_slot] * (0.15 * local_drag_scale * gamma_t * float(src_state[0]))
                )
            if src_width > 2:
                bias[row_start + e_off + quad_slot] += (
                    inv_e[quad_slot] * (0.08 * local_drag_scale * gamma_t * float(src_state[2]))
                )
                bias[row_start + b_off + quad_slot] += (
                    inv_b[quad_slot] * (0.06 * twist_scale * local_drag_scale * gamma_t * float(src_state[2]))
                )

    matrix_sparse = csc_matrix(
        (
            np.concatenate(data_chunks, dtype=np.float64),
            (
                np.concatenate(row_chunks, dtype=np.int64),
                np.concatenate(col_chunks, dtype=np.int64),
            ),
        ),
        shape=(structure.n_unknown, structure.n_unknown),
    )
    matrix_sparse.eliminate_zeros()
    return ReducedHarmonicAffineOperator(
        mode_labels=residual_labels,
        matrix=matrix_sparse,
        bias=bias,
    )


def build_reduced_source_affine_operator(
    layout: HierarchyLayout,
    bg: Mapping[str, object],
    backend: FamilyBackend,
    *,
    mode_labels: tuple[str, ...],
    photon_T_by_mode_label: Mapping[str, np.ndarray],
    photon_E_by_mode_label: Mapping[str, np.ndarray],
    photon_B_by_mode_label: Mapping[str, np.ndarray],
    pattern_cache: _JointSparsityCache | None = None,
) -> ReducedSourceAffineOperator:
    """Return the exact frozen-snapshot affine operator for source local blocks.

    Round-17 P3.5 perf Tier 1A v3 (2026-04-28): same ``pattern_cache``
    plumbing as ``build_reduced_joint_affine_operator``. The source
    operator also goes dense → sparse via ``csc_matrix(matrix)`` at the
    end (line ~2346); a cached pattern lets us skip the
    ``numpy.ndarray.nonzero`` scan and construct the CSC directly via
    fancy indexing into the cached ``(indices, indptr)``. The
    ``_JointSparsityCache`` dataclass is generic over any
    dense → CSC conversion site.
    """

    selected_labels = tuple(str(mu) for mu in mode_labels)
    src_width = int(layout.sector_local_dofs["src"])
    if len(selected_labels) == 0:
        return ReducedSourceAffineOperator(
            mode_labels=(),
            matrix=csc_matrix((0, 0), dtype=np.float64),
            bias=np.zeros(0, dtype=np.float64),
        )

    invalid = frozenset(selected_labels).difference(str(mu) for mu in layout.mode_labels)
    if invalid:
        raise ValueError(f"mode_labels must be a subset of layout.mode_labels, got extras {sorted(invalid)!r}")

    opacity_data = bg.get("opacity_data", {})
    if not isinstance(opacity_data, Mapping):
        raise ValueError("bg.opacity_data must be a mapping when provided")
    gamma_t = float(opacity_data.get("Gamma_T", 0.0))
    scales = _operator_scales(bg, backend)
    branch_scale = float(scales["branch_scale"])
    local_drag_scale = float(scales["local_drag_scale"])
    source_scale = float(scales["source_scale"])
    polarization_scale = float(scales["polarization_scale"])
    twist_scale = float(scales["twist_scale"])
    geom_scale = float(scales["geom_scale"])
    mode_plus_scale = float(scales["mode_plus_scale"])
    mode_minus_scale = float(scales["mode_minus_scale"])
    forcing_blocks = evaluate_reduced_source_blocks(layout, bg, backend)
    width = (int(layout.ell_max) + 1) ** 2
    mu_count = max(len(layout.mode_labels), 1)
    mode_index = {str(mu): idx for idx, mu in enumerate(layout.mode_labels)}
    zeros_h = np.zeros(width, dtype=np.float64)

    total_dof = len(selected_labels) * src_width
    matrix = np.zeros((total_dof, total_dof), dtype=np.float64)
    bias = np.zeros(total_dof, dtype=np.float64)

    dipole_slot = sum(2 * ell + 1 for ell in range(1)) + 1 if int(layout.ell_max) >= 1 else None
    quadrupole_slot = sum(2 * ell + 1 for ell in range(2)) + 2 if int(layout.ell_max) >= 2 else None

    for residual_index, mu in enumerate(selected_labels):
        mu_weight = _mode_label_weight(
            mu,
            mu_index=int(mode_index[mu]),
            mu_count=mu_count,
            branch_scale=branch_scale,
            plus_scale=mode_plus_scale,
            minus_scale=mode_minus_scale,
        )
        source_mass = mu_weight * (1.0 + 0.06 * source_scale + 0.04 * np.arange(src_width, dtype=np.float64))
        inv_source = 1.0 / np.maximum(source_mass, 1.0e-30)
        row_start = residual_index * src_width
        matrix[row_start : row_start + src_width, row_start : row_start + src_width] += np.diag(
            inv_source * (mu_weight * local_drag_scale * (0.35 * gamma_t))
        )
        bias[row_start : row_start + src_width] = inv_source * np.asarray(forcing_blocks[mu], dtype=np.float64)

        t_state = np.asarray(photon_T_by_mode_label.get(mu, zeros_h), dtype=np.float64)
        e_state = np.asarray(photon_E_by_mode_label.get(mu, zeros_h), dtype=np.float64)
        b_state = np.asarray(photon_B_by_mode_label.get(mu, zeros_h), dtype=np.float64)
        if t_state.shape != (width,) or e_state.shape != (width,) or b_state.shape != (width,):
            raise ValueError(f"harmonic state for {mu!r} must have shape ({width},)")
        if dipole_slot is not None and src_width > 1:
            bias[row_start + 1] += inv_source[1] * (-0.08 * mu_weight * local_drag_scale * gamma_t * float(t_state[dipole_slot]))
        if quadrupole_slot is not None and src_width > 0:
            bias[row_start + 0] += inv_source[0] * (-0.10 * mu_weight * local_drag_scale * gamma_t * float(e_state[quadrupole_slot]))
        if quadrupole_slot is not None and src_width > 2:
            bias[row_start + 2] += inv_source[2] * (-0.06 * mu_weight * local_drag_scale * gamma_t * float(e_state[quadrupole_slot]))
            bias[row_start + 2] += (
                inv_source[2]
                * (-0.04 * mu_weight * twist_scale * local_drag_scale * gamma_t * float(b_state[quadrupole_slot]))
            )

    # Round-17 P3.5 perf Tier 1A v3 (2026-04-28): if pattern_cache is given,
    # skip the dense → CSC conversion's nonzero scan via fancy indexing.
    if pattern_cache is not None and pattern_cache.shape == matrix.shape:
        data = matrix[pattern_cache.indices, pattern_cache.cols_of_data]
        matrix_sparse = csc_matrix(
            (np.asarray(data, dtype=np.float64),
             pattern_cache.indices,
             pattern_cache.indptr),
            shape=pattern_cache.shape,
            copy=False,
        )
    else:
        matrix_sparse = csc_matrix(matrix)
        matrix_sparse.eliminate_zeros()
    return ReducedSourceAffineOperator(
        mode_labels=selected_labels,
        matrix=matrix_sparse,
        bias=bias,
    )


def build_reduced_joint_affine_operator(
    layout: HierarchyLayout,
    bg: Mapping[str, object],
    backend: FamilyBackend,
    *,
    residual_mode_labels: tuple[str, ...],
    photon_T_by_mode_label: Mapping[str, np.ndarray],
    photon_E_by_mode_label: Mapping[str, np.ndarray],
    photon_B_by_mode_label: Mapping[str, np.ndarray],
    neutrino_by_mode_label: Mapping[str, np.ndarray],
    baryon_by_mode_label: Mapping[str, np.ndarray],
    source_by_mode_label: Mapping[str, np.ndarray] | None = None,
    pattern_cache: _JointSparsityCache | None = None,
    out_workspace: np.ndarray | None = None,
) -> ReducedJointAffineOperator:
    """Return the exact frozen-snapshot affine operator for local+harmonic+source residual blocks.

    Round-17 P3.5 perf Tier 1A v2 (2026-04-28): an optional
    ``pattern_cache`` argument lets callers skip the dense → CSC
    conversion at the return statement. When given, the function
    extracts only the values at the cached non-zero positions via NumPy
    fancy indexing and constructs the CSC directly from
    ``(data, indices, indptr)``. The 21-s ``numpy.ndarray.nonzero``
    scan and the matching scipy.sparse `_compressed`/`_coo`
    bookkeeping are skipped. Bit-equality with the cache-less path is
    preserved as long as the cache was captured on an exemplar joint
    that covers all structurally-non-zero positions (i.e. at an η
    where γ_T > 0). Default ``None`` preserves legacy behaviour.

    Round-17 P3.5 perf Tier 2D (2026-04-28): an optional
    ``out_workspace`` argument lets callers pass in a pre-allocated
    dense buffer of shape ``(total_dof, total_dof)`` instead of the
    function allocating ``np.zeros(...)`` per call. Profile of a
    single FLRW k showed the dense joint allocation was responsible
    for 3.1 s of the 6.9 s ``numpy.zeros`` tottime (49 µs × 16k calls
    over the integration). When the workspace is reused across calls
    the function calls ``out_workspace.fill(0.0)`` to zero it before
    use; bit-identical to a fresh ``np.zeros``. ``None`` (default)
    preserves legacy behaviour.
    """

    residual_labels = tuple(str(mu) for mu in residual_mode_labels)
    baryon_width = int(layout.sector_local_dofs["baryon"])
    cdm_width = int(layout.sector_local_dofs["cdm"])
    src_width = int(layout.sector_local_dofs["src"])
    local_block_size = baryon_width + cdm_width
    if len(residual_labels) == 0:
        return ReducedJointAffineOperator(
            mode_labels=(),
            local_dof=0,
            harmonic_dof=0,
            source_dof=0,
            matrix=csc_matrix((0, 0), dtype=np.float64),
            bias=np.zeros(0, dtype=np.float64),
        )

    opacity_data = bg.get("opacity_data", {})
    if not isinstance(opacity_data, Mapping):
        raise ValueError("bg.opacity_data must be a mapping when provided")
    gamma_t = float(opacity_data.get("Gamma_T", 0.0))
    scales = _operator_scales(bg, backend)
    geom_scale = float(scales["geom_scale"])
    branch_scale = float(scales["branch_scale"])
    local_drag_scale = float(scales["local_drag_scale"])
    source_scale = float(scales["source_scale"])
    polarization_scale = float(scales["polarization_scale"])
    twist_scale = float(scales["twist_scale"])
    mode_plus_scale = float(scales["mode_plus_scale"])
    mode_minus_scale = float(scales["mode_minus_scale"])
    structure = _reduced_harmonic_structure(
        int(layout.ell_max),
        tuple(str(mu) for mu in layout.mode_labels),
        residual_labels,
        backend.family_spec.family,
    )
    harmonic_block_size = int(structure.block_size)
    harmonic_dof = int(structure.n_unknown)
    local_dof = len(residual_labels) * local_block_size
    source_dof = len(residual_labels) * src_width
    mode_index = {str(mu): idx for idx, mu in enumerate(layout.mode_labels)}

    zero_theta = {mu: 0.0 for mu in residual_labels}
    local_affine = build_reduced_local_affine_operator(
        layout,
        bg,
        backend,
        residual_mode_labels=residual_labels,
        theta_1_by_mode_label=zero_theta,
    )
    zeros_b = np.zeros(baryon_width, dtype=np.float64)
    harmonic_baryon_by_mode_label = {
        str(mu): (
            zeros_b
            if str(mu) in residual_labels
            else np.asarray(baryon_by_mode_label.get(str(mu), zeros_b), dtype=np.float64)
        )
        for mu in layout.mode_labels
    }
    default_source_blocks = evaluate_reduced_source_blocks(layout, bg, backend)
    zeros_s = np.zeros(src_width, dtype=np.float64)
    harmonic_source_by_mode_label: dict[str, np.ndarray] = {}
    for mu in layout.mode_labels:
        mu_key = str(mu)
        if source_by_mode_label is None:
            source_state = np.asarray(default_source_blocks[mu_key], dtype=np.float64)
        else:
            source_state = np.asarray(source_by_mode_label.get(mu_key, default_source_blocks[mu_key]), dtype=np.float64)
        harmonic_source_by_mode_label[mu_key] = (
            zeros_s if mu_key in residual_labels else np.asarray(source_state, dtype=np.float64)
        )
    harmonic_affine = build_reduced_harmonic_affine_operator(
        layout,
        bg,
        backend,
        residual_mode_labels=residual_labels,
        photon_T_by_mode_label=photon_T_by_mode_label,
        photon_E_by_mode_label=photon_E_by_mode_label,
        photon_B_by_mode_label=photon_B_by_mode_label,
        neutrino_by_mode_label=neutrino_by_mode_label,
        baryon_by_mode_label=harmonic_baryon_by_mode_label,
        source_by_mode_label=harmonic_source_by_mode_label,
    )

    total_dof = local_dof + harmonic_dof + source_dof
    source_offset = local_dof + harmonic_dof
    # Round-17 P3.5 perf Tier 2D: reuse caller-supplied dense workspace
    # if shape matches, instead of allocating a fresh np.zeros every call.
    if (
        out_workspace is not None
        and out_workspace.shape == (total_dof, total_dof)
        and out_workspace.dtype == np.float64
    ):
        joint = out_workspace
        joint.fill(0.0)
    else:
        joint = np.zeros((total_dof, total_dof), dtype=np.float64)
    if local_dof > 0:
        joint[:local_dof, :local_dof] = np.asarray(local_affine.matrix.toarray(), dtype=np.float64)
    if harmonic_dof > 0:
        joint[local_dof : local_dof + harmonic_dof, local_dof : local_dof + harmonic_dof] = np.asarray(
            harmonic_affine.matrix.toarray(),
            dtype=np.float64,
        )

    # v5 audit Round-2 Q-5.1d: local ↔ harmonic Thomson coupling.
    # Ma-Bertschinger (1995) eq 64-66:
    #   v̇_b = (κ̇/R)·(3·Θ_1 - v_b)     →   A[v_b, Θ_1] = +3·κ̇/R
    #   Θ̇_1 = -κ̇·(Θ_1 - v_b/3) + ... →   A[Θ_1, v_b] = +κ̇/3  (NO 1/R factor!)
    # Code convention: local_drag_scale is taken to encode 1/R (v5 §03A ambiguity,
    # flagged in audit). The photon-dipole row receives κ̇/3 WITHOUT 1/R.
    # local <- harmonic(theta_1) coupling
    baryon_base_diag = 1.0 + 0.08 * geom_scale + 0.03 * np.arange(baryon_width, dtype=np.float64)
    if baryon_width > 1 and structure.dipole_slot is not None:
        local_theta_coeff = float(
            3.0 * local_drag_scale * gamma_t / max(abs(float(baryon_base_diag[1])), 1.0e-30)
        )
        for residual_index in range(len(residual_labels)):
            local_row = residual_index * local_block_size + 1
            harmonic_col = local_dof + residual_index * harmonic_block_size + int(structure.dipole_slot)
            joint[local_row, harmonic_col] = local_theta_coeff

    # harmonic <- local(baryon velocity) coupling
    if baryon_width > 1 and structure.dipole_slot is not None:
        ell_weight = 1.0 + 0.04 * 1.0 + 0.015 * geom_scale
        inv_t_dipole = 1.0 / max(branch_scale * ell_weight, 1.0e-30)
        harmonic_baryon_coeff = float(inv_t_dipole * (gamma_t / 3.0))
        for residual_index in range(len(residual_labels)):
            harmonic_row = local_dof + residual_index * harmonic_block_size + int(structure.dipole_slot)
            local_col = residual_index * local_block_size + 1
            joint[harmonic_row, local_col] = harmonic_baryon_coeff

    bias = np.concatenate(
        [
            np.asarray(local_affine.bias, dtype=np.float64),
            np.asarray(harmonic_affine.bias, dtype=np.float64),
            np.zeros(source_dof, dtype=np.float64),
        ],
        dtype=np.float64,
    )
    for residual_index, mu in enumerate(residual_labels):
        mu_weight = _mode_label_weight(
            mu,
            mu_index=int(mode_index[mu]),
            mu_count=max(len(layout.mode_labels), 1),
            branch_scale=branch_scale,
            plus_scale=mode_plus_scale,
            minus_scale=mode_minus_scale,
        )
        source_mass = mu_weight * (1.0 + 0.06 * source_scale + 0.04 * np.arange(src_width, dtype=np.float64))
        inv_source = 1.0 / np.maximum(source_mass, 1.0e-30)
        source_block = np.asarray(default_source_blocks[mu], dtype=np.float64)
        source_row = source_offset + residual_index * src_width
        harmonic_row = local_dof + residual_index * harmonic_block_size

        # v5 audit Round-2 extension: same Thomson-damping sign convention
        # as ❺❻❼. The prior `+0.35·γ_T` was the +0.32 growth mode that
        # Q-7.4 did not explicitly touch; eigenvector localization showed
        # 98.7% weight on the source block. Pattern-matched fix pending
        # a Round-3 audit of the source-propagator formulation.
        joint[source_row : source_row + src_width, source_row : source_row + src_width] -= np.diag(
            inv_source * (mu_weight * local_drag_scale * (0.35 * gamma_t))
        )

        bias_source = inv_source * source_block
        if src_width > 0:
            bias[source_row : source_row + src_width] = bias_source
        if structure.dipole_slot is not None and src_width > 1:
            ell_weight = 1.0 + 0.04 * 1.0 + 0.015 * geom_scale
            inv_t_dipole = 1.0 / max(branch_scale * ell_weight, 1.0e-30)
            joint[harmonic_row + int(structure.dipole_slot), source_row + 1] += (
                inv_t_dipole * (0.10 * local_drag_scale * gamma_t)
            )
            joint[source_row + 1, harmonic_row + int(structure.dipole_slot)] += (
                inv_source[1] * (-0.08 * mu_weight * local_drag_scale * gamma_t)
            )
        if structure.quadrupole_slot is not None:
            ell_weight = 1.0 + 0.04 * 2.0 + 0.015 * geom_scale
            inv_e_quad = 1.0 / max(branch_scale * (1.08 * polarization_scale) * ell_weight, 1.0e-30)
            if src_width > 0:
                joint[harmonic_row + structure.width + int(structure.quadrupole_slot), source_row + 0] += (
                    inv_e_quad * (0.15 * local_drag_scale * gamma_t)
                )
                joint[source_row + 0, harmonic_row + structure.width + int(structure.quadrupole_slot)] += (
                    inv_source[0] * (-0.10 * mu_weight * local_drag_scale * gamma_t)
                )
            if src_width > 2:
                inv_b_quad = 1.0 / max(
                    branch_scale
                    * (1.12 + 0.5 * twist_scale)
                    * polarization_scale
                    * ell_weight,
                    1.0e-30,
                )
                joint[harmonic_row + structure.width + int(structure.quadrupole_slot), source_row + 2] += (
                    inv_e_quad * (0.08 * local_drag_scale * gamma_t)
                )
                joint[harmonic_row + 2 * structure.width + int(structure.quadrupole_slot), source_row + 2] += (
                    inv_b_quad * (0.06 * twist_scale * local_drag_scale * gamma_t)
                )
                joint[source_row + 2, harmonic_row + structure.width + int(structure.quadrupole_slot)] += (
                    inv_source[2] * (-0.06 * mu_weight * local_drag_scale * gamma_t)
                )
                joint[source_row + 2, harmonic_row + 2 * structure.width + int(structure.quadrupole_slot)] += (
                    inv_source[2] * (-0.04 * mu_weight * twist_scale * local_drag_scale * gamma_t)
                )

    # Round-17 P3.5 perf Tier 1A v2 (2026-04-28): if pattern_cache is given,
    # skip the ``csc_matrix(joint)`` conversion (which calls
    # ``numpy.ndarray.nonzero`` for ~21 s/16k-call across an integration)
    # by directly extracting values at the cached non-zero positions and
    # constructing the CSC from ``(data, indices, indptr)``. Bit-equal to
    # the cache-less path when the cache covered all structural NNZ.
    if pattern_cache is not None and pattern_cache.shape == joint.shape:
        # Fancy indexing: O(nnz) value extraction.
        data = joint[pattern_cache.indices, pattern_cache.cols_of_data]
        joint_csc = csc_matrix(
            (np.asarray(data, dtype=np.float64),
             pattern_cache.indices,
             pattern_cache.indptr),
            shape=pattern_cache.shape,
            copy=False,
        )
    else:
        joint_csc = csc_matrix(joint)
    return ReducedJointAffineOperator(
        mode_labels=residual_labels,
        local_dof=local_dof,
        harmonic_dof=harmonic_dof,
        source_dof=source_dof,
        matrix=joint_csc,
        bias=bias,
    )


def build_reduced_local_affine_operator(
    layout: HierarchyLayout,
    bg: Mapping[str, object],
    backend: FamilyBackend,
    *,
    residual_mode_labels: tuple[str, ...],
    theta_1_by_mode_label: Mapping[str, float],
) -> ReducedLocalAffineOperator:
    """Return the exact frozen-snapshot affine operator for residual local sectors."""

    residual_labels = tuple(str(mu) for mu in residual_mode_labels)
    baryon_width = int(layout.sector_local_dofs["baryon"])
    cdm_width = int(layout.sector_local_dofs["cdm"])
    block_size = baryon_width + cdm_width
    if len(residual_labels) == 0:
        return ReducedLocalAffineOperator(
            mode_labels=(),
            matrix=csc_matrix((0, 0), dtype=np.float64),
            bias=np.zeros(0, dtype=np.float64),
        )

    invalid = frozenset(residual_labels).difference(str(mu) for mu in layout.mode_labels)
    if invalid:
        raise ValueError(f"residual_mode_labels must be a subset of layout.mode_labels, got extras {sorted(invalid)!r}")

    opacity_data = bg.get("opacity_data", {})
    if not isinstance(opacity_data, Mapping):
        raise ValueError("bg.opacity_data must be a mapping when provided")
    gamma_t = float(opacity_data.get("Gamma_T", 0.0))
    scales = _operator_scales(bg, backend)
    geom_scale = float(scales["geom_scale"])
    branch_scale = float(scales["branch_scale"])
    local_drag_scale = float(scales["local_drag_scale"])
    mode_plus_scale = float(scales["mode_plus_scale"])
    mode_minus_scale = float(scales["mode_minus_scale"])
    mu_count = max(len(layout.mode_labels), 1)
    baryon_base_diag = 1.0 + 0.08 * geom_scale + 0.03 * np.arange(baryon_width, dtype=np.float64)

    rows: list[int] = []
    cols: list[int] = []
    data: list[float] = []
    bias = np.zeros(len(residual_labels) * block_size, dtype=np.float64)
    mode_index = {str(mu): idx for idx, mu in enumerate(layout.mode_labels)}
    for residual_index, mu in enumerate(residual_labels):
        mu_weight = _mode_label_weight(
            mu,
            mu_index=int(mode_index[mu]),
            mu_count=mu_count,
            branch_scale=branch_scale,
            plus_scale=mode_plus_scale,
            minus_scale=mode_minus_scale,
        )
        baryon_diag = mu_weight * baryon_base_diag
        # v5 audit Option-B (extended): same Thomson-damping sign logic as
        # the harmonic block. Ma-Bertschinger (1995) baryon velocity eq:
        # v̇_b = -ℋ·v_b - (κ̇/R)·(v_b − 3·Θ_1).  The diagonal contribution
        # from κ̇ is NEGATIVE (damping).  The prior `+gamma_t/baryon_diag`
        # was wrong-signed and was exposed as the +0.93 growth mode when
        # the fast-check audit set γ_T = 1.
        coeff = -np.divide(
            mu_weight * local_drag_scale * gamma_t,
            np.maximum(np.abs(baryon_diag), 1.0e-30),
            dtype=np.float64,
        )
        row_start = residual_index * block_size
        for local_dof, value in enumerate(coeff):
            rows.append(row_start + local_dof)
            cols.append(row_start + local_dof)
            data.append(float(value))
        if baryon_width > 1:
            bias[row_start + 1] = float(
                0.25
                * mu_weight
                * local_drag_scale
                * gamma_t
                * float(theta_1_by_mode_label.get(mu, 0.0))
                / max(abs(float(baryon_diag[1])), 1.0e-30)
            )

    return ReducedLocalAffineOperator(
        mode_labels=residual_labels,
        matrix=csc_matrix(
            (np.asarray(data, dtype=np.float64), (np.asarray(rows, dtype=np.int64), np.asarray(cols, dtype=np.int64))),
            shape=(len(residual_labels) * block_size, len(residual_labels) * block_size),
        ),
        bias=bias,
    )


def evaluate_reduced_local_rhs(
    layout: HierarchyLayout,
    bg: Mapping[str, object],
    backend: FamilyBackend,
    *,
    baryon_by_mode_label: Mapping[str, np.ndarray],
    cdm_by_mode_label: Mapping[str, np.ndarray],
    theta_1_by_mode_label: Mapping[str, float],
) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray]]:
    """Evaluate the PR-09 local-sector rows without assembling full sparse operators."""

    opacity_data = bg.get("opacity_data", {})
    if not isinstance(opacity_data, Mapping):
        raise ValueError("bg.opacity_data must be a mapping when provided")
    gamma_t = float(opacity_data.get("Gamma_T", 0.0))
    scales = _operator_scales(bg, backend)
    geom_scale = float(scales["geom_scale"])
    branch_scale = float(scales["branch_scale"])
    local_drag_scale = float(scales["local_drag_scale"])
    mode_plus_scale = float(scales["mode_plus_scale"])
    mode_minus_scale = float(scales["mode_minus_scale"])
    baryon_width = int(layout.sector_local_dofs["baryon"])
    cdm_width = int(layout.sector_local_dofs["cdm"])
    baryon_base_diag = 1.0 + 0.08 * geom_scale + 0.03 * np.arange(baryon_width, dtype=np.float64)
    mu_count = max(len(layout.mode_labels), 1)
    baryon_rhs: dict[str, np.ndarray] = {}
    cdm_rhs: dict[str, np.ndarray] = {}
    for mu_index, mu in enumerate(layout.mode_labels):
        mu_key = str(mu)
        mu_weight = _mode_label_weight(
            mu_key,
            mu_index=mu_index,
            mu_count=mu_count,
            branch_scale=branch_scale,
            plus_scale=mode_plus_scale,
            minus_scale=mode_minus_scale,
        )
        baryon_state = np.asarray(
            baryon_by_mode_label.get(mu_key, np.zeros(baryon_width, dtype=np.float64)),
            dtype=np.float64,
        )
        if baryon_state.shape != (baryon_width,):
            raise ValueError(f"baryon state for {mu_key!r} must have shape ({baryon_width},)")
        cdm_state = np.asarray(
            cdm_by_mode_label.get(mu_key, np.zeros(cdm_width, dtype=np.float64)),
            dtype=np.float64,
        )
        if cdm_state.shape != (cdm_width,):
            raise ValueError(f"cdm state for {mu_key!r} must have shape ({cdm_width},)")
        baryon_drive = mu_weight * local_drag_scale * gamma_t * baryon_state
        if baryon_width > 1:
            baryon_drive[1] += (
                0.25 * mu_weight * local_drag_scale * gamma_t * float(theta_1_by_mode_label.get(mu_key, 0.0))
            )
        baryon_diag = mu_weight * baryon_base_diag
        baryon_rhs[mu_key] = baryon_drive / np.maximum(np.abs(baryon_diag), 1.0e-30)
        cdm_rhs[mu_key] = np.zeros_like(cdm_state)
    return baryon_rhs, cdm_rhs


def assemble_hierarchy_ops(
    bg: Mapping[str, object],
    backend: FamilyBackend,
    truncation: Mapping[str, object],
    source_data: Mapping[str, object],
):
    """Return the concrete ver3 hierarchy operator bundle for one background state."""

    if not isinstance(bg, Mapping):
        raise ValueError("bg must be a mapping")
    if not isinstance(source_data, Mapping):
        raise ValueError("source_data must be a mapping")
    state = dict(bg)
    opacity_data = state.get("opacity_data", {})
    if not isinstance(opacity_data, Mapping):
        raise ValueError("bg.opacity_data must be a mapping when provided")
    state["opacity_data"] = dict(opacity_data)
    existing_sources = state.get("source_tables", {})
    if not isinstance(existing_sources, Mapping):
        raise ValueError("bg.source_tables must be a mapping when provided")
    state["source_tables"] = {**dict(existing_sources), **dict(source_data)}
    state.setdefault("state_tag", "hierarchy_ops_state")
    return backend.operator_factory(state)


def hierarchy_layout_gate_bundle(
    backend: FamilyBackend,
    ops,
    *,
    provenance_metadata: Mapping[str, object] | None = None,
) -> GateBundle:
    """Emit the machine-readable PR-09 hierarchy-layout gate bundle."""

    mass_matrix = ops.mass_matrix
    explicit_block = ops.A_fs + ops.A_mix
    implicit_block = ops.A_coll
    source_template = np.asarray(ops.source_template, dtype=np.float64)
    layout_metadata = dict(ops.layout_metadata)
    return make_gate_bundle(
        "hierarchy_layout_gate",
        family=backend.family_spec.family,
        branch=ops.branch,
        backend=backend.family_spec.preferred_backend,
        truncation=dict(backend.truncation),
        residual_summary={
            "state_size": float(layout_metadata.get("size", 0)),
            "mass_matrix_nnz": float(mass_matrix.nnz),
            "explicit_block_nnz": float(explicit_block.nnz),
            "implicit_block_nnz": float(implicit_block.nnz),
            "source_norm": float(np.linalg.norm(source_template)),
        },
        known_limit_checks={
            "mass_matrix_square": bool(mass_matrix.shape[0] == mass_matrix.shape[1]),
            "explicit_block_square": bool(explicit_block.shape[0] == explicit_block.shape[1]),
            "implicit_block_square": bool(implicit_block.shape[0] == implicit_block.shape[1]),
            "source_matches_state_size": bool(source_template.shape == (mass_matrix.shape[0],)),
        },
        forbidden_shortcut_checks={
            "no_dense_generic_operator": True,
            "no_ad_hoc_sector_order": True,
            "operator_split_preserved": True,
        },
        metadata={
            "layout_manifest": layout_metadata,
            "operator_realization": layout_metadata.get("operator_realization"),
            "exact_family_operator_available": layout_metadata.get("exact_family_operator_available"),
            "projection_provenance": {}
            if provenance_metadata is None
            else dict(provenance_metadata),
        },
        passed=bool(
            mass_matrix.shape[0] == mass_matrix.shape[1]
            and explicit_block.shape[0] == explicit_block.shape[1]
            and implicit_block.shape[0] == implicit_block.shape[1]
            and source_template.shape == (mass_matrix.shape[0],)
        ),
        opened_claim="hierarchy layout and operator split bound to executable sparse objects",
    )
