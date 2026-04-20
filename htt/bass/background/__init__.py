"""BASS background surfaces.

The package currently contains both legacy/reduced background helpers and the
VER2 S1 skeleton contracts. The VER2 additions freeze algebra/geometry/
constraint ownership without yet replacing the older reduced solver.
"""

from bass.background.bianchi_types import (
    BianchiAlgebra,
    BianchiBranchPolicy,
    StructureConstants,
    all_bianchi_algebras,
    build_bianchi_algebra,
    build_structure_tensor,
    get_type,
)
from bass.background.constraints import (
    BackgroundConstraintResiduals,
    MatterNormalFrameState,
    evaluate_background_constraints,
)
from bass.background.geometry import (
    TetradGeometry,
    build_geometry,
    curl_pstf2,
    div_pstf2,
    div_vector,
    pstf_rank2,
    spatial_connection,
    spatial_ricci,
)
from bass.background.initial_conditions import (
    OrthogonalInitialConditions,
    TiltedInitialConditions,
    build_orthogonal_initial_conditions,
    build_tilted_initial_conditions,
    project_trace_free_shear,
    solve_expanding_H,
)
from bass.background.rhs import BackgroundRhsAssembly, assemble_background_rhs
from bass.background.weyl import (
    WeylDiagnostics,
    build_weyl_diagnostics,
    electric_weyl_from_shear_rhs,
    magnetic_weyl_from_curl_sigma,
)

__all__ = [
    "BianchiAlgebra",
    "BianchiBranchPolicy",
    "StructureConstants",
    "build_structure_tensor",
    "build_bianchi_algebra",
    "all_bianchi_algebras",
    "get_type",
    "TetradGeometry",
    "pstf_rank2",
    "spatial_connection",
    "spatial_ricci",
    "div_vector",
    "div_pstf2",
    "curl_pstf2",
    "build_geometry",
    "MatterNormalFrameState",
    "BackgroundConstraintResiduals",
    "evaluate_background_constraints",
    "OrthogonalInitialConditions",
    "TiltedInitialConditions",
    "solve_expanding_H",
    "project_trace_free_shear",
    "build_orthogonal_initial_conditions",
    "build_tilted_initial_conditions",
    "BackgroundRhsAssembly",
    "assemble_background_rhs",
    "WeylDiagnostics",
    "magnetic_weyl_from_curl_sigma",
    "electric_weyl_from_shear_rhs",
    "build_weyl_diagnostics",
]
