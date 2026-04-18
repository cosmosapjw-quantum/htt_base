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
    # Driver (LB-2b)
    "hierarchy_rhs_photon",
    "hierarchy_rhs_neutrino",
    "proper_shear_at_eta",
]
