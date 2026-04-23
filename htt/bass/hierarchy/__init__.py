"""bass.hierarchy (LB-2a) — PSTF multipole storage and orthogonal RHS subset.

This subpackage holds the exact 1+3 covariant PSTF hierarchy machinery
used by the low-ℓ Bianchi solver. LB-2a delivers the storage layer
(``PSTFTensor``, ``PSTFHierarchyState``) plus the subset of the nine-
term RHS that is active for orthogonal Bianchi I / V / VII₀ at
homogeneous background (``T1``, ``T2``, ``T3``, ``T8``, ``T9``).

``T4``, ``T5``, ``T6``, ``T7`` and the combined
``hierarchy_rhs_photon`` driver are deferred to LB-2b.

References
----------
- ``docs/lowell_bianchi/02_multipole_hierarchy_spec.md`` (spec).
- ``docs/lowell_bianchi/00_conventions.md §5`` (PSTF packing).
- Ellis, Maartens, MacCallum *Relativistic Cosmology* §4.5-4.6.
- lowell reference §6 (nine-term hierarchy).
"""
from bass.hierarchy.closure_interface import (
    ClosureStrategy,
    HardCutClosure,
)
from bass.hierarchy.closure import (
    FreeStreamingClosure,
    PowerLawExtrapolationClosure,
    TCAClosure,
    build_default_closure,
)
from bass.hierarchy.closure_diagnostics import measure_closure_error
from bass.hierarchy.collision_interface import (
    CollisionOperator,
    ZeroCollisionOperator,
)
from bass.hierarchy.contractions import (
    L_MAX_CACHED,
    pstf_pack,
    pstf_unpack,
    stf_basis,
    sym_trace_free,
    verify_pstf_invariants,
)
from bass.hierarchy.pstf_tensor import (
    PSTFHierarchyState,
    PSTFTensor,
    hierarchy_total_size,
    pack_hierarchy,
    pstf_from_tensor,
    pstf_to_tensor,
    unpack_hierarchy,
    zero_hierarchy,
    zero_pstf,
)
from bass.hierarchy.hierarchy_rhs import (
    hierarchy_rhs_neutrino,
    hierarchy_rhs_photon,
    proper_shear_at_eta,
)
from bass.hierarchy.terms import (
    T1_expansion,
    T2_gradient,
    T3_divergence,
    T4_accel_divergence,
    T5_accel_gradient,
    T6_vorticity,
    T7_shear_up,
    T8_shear_same,
    T9_shear_down,
    zero_nabla_operator,
)
from bass.hierarchy.nabla_dispatch import (
    DEFERRED_FB22_TYPES,
    DEFERRED_FB23_TYPES,
    HarmonicMode,
    SUPPORTED_FB21_TYPES,
    SUPPORTED_FB22_TYPES,
    SUPPORTED_FB23_TYPES,
    SUPPORTED_TYPES,
    make_nabla_tilde,
    scalar_laplacian_eigenvalue,
)
from bass.hierarchy.tilt_kinematics import (
    accel_from_tilt,
    vorticity_from_tilt,
)
from bass.hierarchy.boost_kernel import (
    AXIS_ALIGNMENT_TOL,
    boost_project_axisymmetric,
    is_axis_aligned,
)
from bass.hierarchy.frame_contracts import (
    BoostOrder,
    FrameSplitMetadata,
    PhotonDirectionConvention,
    PolarizationPhaseConvention,
)
from bass.hierarchy.pstf_radiation import (
    RadiationNormalization,
    RadiationPSTFState,
    TruncationMetadata,
    make_radiation_state,
    project_from_angular_samples,
    reconstruct_on_sphere,
)
from bass.hierarchy.seed_compatibility import (
    PackedRegularSeedInjection,
    RegularSeedDescriptor,
    RegularSeedState,
    SeedAssignmentFrame,
    SeedConvention,
    SeedConstraintProjection,
    build_constraint_projection,
    build_flrw_regular_seed,
    project_packed_regular_seed,
    promote_tilted_seed,
)
from bass.hierarchy.ver3_layout_protocol import (
    SECTOR_ORDER,
    HierarchyLayout,
    evaluate_reduced_local_rhs,
    assemble_hierarchy_ops,
    assemble_free_streaming_block,
    assemble_mixing_block,
    assemble_explicit_block,
    assemble_implicit_block,
    assemble_mass_matrix,
    assemble_source_vector,
    build_hierarchy_layout,
    build_layout_manifest,
    flatten,
    unflatten,
)
from bass.hierarchy.ver3_state_contracts import (
    CanonicalLayoutProjection,
    HierarchyState,
    project_runtime_native_state,
)


__all__ = [
    # Storage
    "PSTFTensor",
    "PSTFHierarchyState",
    "zero_pstf",
    "zero_hierarchy",
    "pstf_from_tensor",
    "pstf_to_tensor",
    "pack_hierarchy",
    "unpack_hierarchy",
    "hierarchy_total_size",
    # Contractions
    "sym_trace_free",
    "pstf_pack",
    "pstf_unpack",
    "stf_basis",
    "verify_pstf_invariants",
    "L_MAX_CACHED",
    # Terms
    "T1_expansion",
    "T2_gradient",
    "T3_divergence",
    "T4_accel_divergence",
    "T5_accel_gradient",
    "T6_vorticity",
    "T7_shear_up",
    "T8_shear_same",
    "T9_shear_down",
    "zero_nabla_operator",
    # Interfaces
    "ClosureStrategy",
    "HardCutClosure",
    "CollisionOperator",
    "ZeroCollisionOperator",
    # Closure strategies (LB-3)
    "FreeStreamingClosure",
    "PowerLawExtrapolationClosure",
    "TCAClosure",
    "build_default_closure",
    "measure_closure_error",
    # Driver (LB-2b)
    "hierarchy_rhs_photon",
    "hierarchy_rhs_neutrino",
    "proper_shear_at_eta",
    # ∇̃ dispatch (FB-2.1 + FB-2.2 + FB-2.3)
    "HarmonicMode",
    "make_nabla_tilde",
    "scalar_laplacian_eigenvalue",
    "SUPPORTED_FB21_TYPES",
    "SUPPORTED_FB22_TYPES",
    "SUPPORTED_FB23_TYPES",
    "SUPPORTED_TYPES",
    "DEFERRED_FB22_TYPES",
    "DEFERRED_FB23_TYPES",
    # Tilt kinematic adapters (FB-3.2, extended FB-3.3)
    "accel_from_tilt",
    "vorticity_from_tilt",
    # Axi-symmetric boost projection seed (FB-3.3)
    "AXIS_ALIGNMENT_TOL",
    "boost_project_axisymmetric",
    "is_axis_aligned",
    # VER2 S2 frame split / radiation / seed contracts
    "PhotonDirectionConvention",
    "PolarizationPhaseConvention",
    "BoostOrder",
    "FrameSplitMetadata",
    "RadiationNormalization",
    "TruncationMetadata",
    "RadiationPSTFState",
    "make_radiation_state",
    "project_from_angular_samples",
    "reconstruct_on_sphere",
    "SeedConvention",
    "SeedAssignmentFrame",
    "RegularSeedDescriptor",
    "RegularSeedState",
    "SeedConstraintProjection",
    "PackedRegularSeedInjection",
    "build_flrw_regular_seed",
    "promote_tilted_seed",
    "build_constraint_projection",
    "project_packed_regular_seed",
    # ver3 PR-09 hierarchy layout and IMEX packing
    "SECTOR_ORDER",
    "CanonicalLayoutProjection",
    "HierarchyState",
    "HierarchyLayout",
    "build_hierarchy_layout",
    "build_layout_manifest",
    "flatten",
    "unflatten",
    "evaluate_reduced_local_rhs",
    "assemble_hierarchy_ops",
    "assemble_free_streaming_block",
    "assemble_mixing_block",
    "assemble_mass_matrix",
    "assemble_explicit_block",
    "assemble_implicit_block",
    "assemble_source_vector",
    "project_runtime_native_state",
]
