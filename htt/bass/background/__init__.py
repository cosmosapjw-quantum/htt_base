"""BASS background surfaces.

VER2 uses the canonical algebra/geometry/IC/evolution surfaces in this package
as the implementation anchor for background-side physics. The older reduced
`einstein_bianchi` path remains available for compatibility, but package-level
exports are now lazy so `bass.background` no longer pulls `bass.tilt` during
module initialization.
"""

from importlib import import_module

__all__ = [
    "BianchiAlgebra",
    "BianchiBranchPolicy",
    "FamilySpec",
    "StructureConstants",
    "build_structure_tensor",
    "build_bianchi_algebra",
    "all_bianchi_algebras",
    "get_family_spec",
    "all_family_specs",
    "rescale_bianchi_algebra",
    "get_type",
    "TetradGeometry",
    "pstf_rank2",
    "connection_from_commutators",
    "spatial_connection",
    "spatial_ricci_from_connection",
    "spatial_ricci_from_compact_formula",
    "dual_route_curvature_residual",
    "spatial_ricci",
    "div_vector",
    "div_pstf2",
    "curl_pstf2",
    "build_geometry",
    "MatterNormalFrameState",
    "BackgroundConstraintResiduals",
    "evaluate_background_constraints",
    "CodazziProjectionError",
    "CodazziProjectionMetadata",
    "InitialConditionMetadata",
    "OrthogonalInitialConditions",
    "TiltedInitialConditions",
    "solve_expanding_H",
    "project_shear_to_codazzi",
    "project_tilted_codazzi",
    "project_trace_free_shear",
    "build_orthogonal_initial_conditions",
    "build_tilted_initial_conditions",
    "BackgroundRhsAssembly",
    "assemble_background_rhs",
    "BackgroundEvolutionConfig",
    "BackgroundEvolutionResult",
    "solve_background_evolution",
    "WeylDiagnostics",
    "magnetic_weyl_from_curl_sigma",
    "electric_weyl_from_shear_rhs",
    "build_weyl_diagnostics",
]


_EXPORTS = {
    "BianchiAlgebra": ("bass.background.bianchi_types", "BianchiAlgebra"),
    "BianchiBranchPolicy": ("bass.background.bianchi_types", "BianchiBranchPolicy"),
    "FamilySpec": ("bass.background.bianchi_types", "FamilySpec"),
    "StructureConstants": ("bass.background.bianchi_types", "StructureConstants"),
    "build_structure_tensor": ("bass.background.bianchi_types", "build_structure_tensor"),
    "build_bianchi_algebra": ("bass.background.bianchi_types", "build_bianchi_algebra"),
    "all_bianchi_algebras": ("bass.background.bianchi_types", "all_bianchi_algebras"),
    "get_family_spec": ("bass.background.bianchi_types", "get_family_spec"),
    "all_family_specs": ("bass.background.bianchi_types", "all_family_specs"),
    "rescale_bianchi_algebra": ("bass.background.bianchi_types", "rescale_bianchi_algebra"),
    "get_type": ("bass.background.bianchi_types", "get_type"),
    "TetradGeometry": ("bass.background.geometry", "TetradGeometry"),
    "pstf_rank2": ("bass.background.geometry", "pstf_rank2"),
    "connection_from_commutators": ("bass.background.geometry", "connection_from_commutators"),
    "spatial_connection": ("bass.background.geometry", "spatial_connection"),
    "spatial_ricci_from_connection": ("bass.background.geometry", "spatial_ricci_from_connection"),
    "spatial_ricci_from_compact_formula": ("bass.background.geometry", "spatial_ricci_from_compact_formula"),
    "dual_route_curvature_residual": ("bass.background.geometry", "dual_route_curvature_residual"),
    "spatial_ricci": ("bass.background.geometry", "spatial_ricci"),
    "div_vector": ("bass.background.geometry", "div_vector"),
    "div_pstf2": ("bass.background.geometry", "div_pstf2"),
    "curl_pstf2": ("bass.background.geometry", "curl_pstf2"),
    "build_geometry": ("bass.background.geometry", "build_geometry"),
    "MatterNormalFrameState": ("bass.background.constraints", "MatterNormalFrameState"),
    "BackgroundConstraintResiduals": ("bass.background.constraints", "BackgroundConstraintResiduals"),
    "evaluate_background_constraints": ("bass.background.constraints", "evaluate_background_constraints"),
    "CodazziProjectionError": ("bass.background.initial_conditions", "CodazziProjectionError"),
    "CodazziProjectionMetadata": ("bass.background.initial_conditions", "CodazziProjectionMetadata"),
    "InitialConditionMetadata": ("bass.background.initial_conditions", "InitialConditionMetadata"),
    "OrthogonalInitialConditions": ("bass.background.initial_conditions", "OrthogonalInitialConditions"),
    "TiltedInitialConditions": ("bass.background.initial_conditions", "TiltedInitialConditions"),
    "solve_expanding_H": ("bass.background.initial_conditions", "solve_expanding_H"),
    "project_shear_to_codazzi": ("bass.background.initial_conditions", "project_shear_to_codazzi"),
    "project_tilted_codazzi": ("bass.background.initial_conditions", "project_tilted_codazzi"),
    "project_trace_free_shear": ("bass.background.initial_conditions", "project_trace_free_shear"),
    "build_orthogonal_initial_conditions": ("bass.background.initial_conditions", "build_orthogonal_initial_conditions"),
    "build_tilted_initial_conditions": ("bass.background.initial_conditions", "build_tilted_initial_conditions"),
    "BackgroundRhsAssembly": ("bass.background.rhs", "BackgroundRhsAssembly"),
    "assemble_background_rhs": ("bass.background.rhs", "assemble_background_rhs"),
    "BackgroundEvolutionConfig": ("bass.background.evolution", "BackgroundEvolutionConfig"),
    "BackgroundEvolutionResult": ("bass.background.evolution", "BackgroundEvolutionResult"),
    "solve_background_evolution": ("bass.background.evolution", "solve_background_evolution"),
    "WeylDiagnostics": ("bass.background.weyl", "WeylDiagnostics"),
    "magnetic_weyl_from_curl_sigma": ("bass.background.weyl", "magnetic_weyl_from_curl_sigma"),
    "electric_weyl_from_shear_rhs": ("bass.background.weyl", "electric_weyl_from_shear_rhs"),
    "build_weyl_diagnostics": ("bass.background.weyl", "build_weyl_diagnostics"),
}


def __getattr__(name: str):
    if name not in _EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attr_name = _EXPORTS[name]
    value = getattr(import_module(module_name), attr_name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
