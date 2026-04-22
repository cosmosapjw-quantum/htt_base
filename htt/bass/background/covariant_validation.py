"""All-family tetrad/PSTF covariant validation reports."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Mapping

import numpy as np

from bass.background.bianchi_types import (
    ALL_BIANCHI_TYPES,
    FamilySpec,
    get_family_spec,
)
from bass.background.constraints import MatterNormalFrameState
from bass.background.initial_conditions import (
    OrthogonalInitialConditions,
    TiltedInitialConditions,
    build_orthogonal_initial_conditions,
    build_tilted_initial_conditions,
)
from bass.background.rhs import assemble_background_rhs
from bass.background.weyl import build_weyl_diagnostics
from bass.los import build_backend
from bass.tilt.species_tilt import TiltedSpeciesParams, decompose_tilted_species

__all__ = [
    "CovariantResidualPack",
    "FamilyBranchValidationReport",
    "build_covariant_residual_pack",
    "build_family_branch_validation_report",
    "build_all_family_branch_validation_matrix",
]


@dataclass(frozen=True)
class CovariantResidualPack:
    gauss_abs: float
    gauss_over_H2_ref: float
    codazzi_norm: float
    codazzi_over_H2_ref: float
    jacobi_norm: float
    jacobi_over_structure_ref: float
    dual_route_curvature: float
    dual_route_curvature_over_structure_ref: float
    bianchi_norm: float
    bianchi_over_H2_ref: float
    electric_norm: float
    electric_over_H2_ref: float
    magnetic_norm: float
    magnetic_over_H2_ref: float
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", dict(self.metadata))


@dataclass(frozen=True)
class FamilyBranchValidationReport:
    family: str
    branch: Literal["orthogonal", "tilted"]
    class_label: Literal["A", "B"]
    isotropic_anchor: bool
    global_tilt_present: bool
    local_boost_present: bool
    preferred_backend: str
    operator_kernel_family: str
    backend_release_status: str
    hierarchy_size: int
    residuals: CovariantResidualPack
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", dict(self.metadata))


def _normal_frame_state(
    initial_conditions: OrthogonalInitialConditions | TiltedInitialConditions,
) -> MatterNormalFrameState:
    matter = initial_conditions.matter
    if isinstance(matter, MatterNormalFrameState):
        return matter
    return MatterNormalFrameState(
        rho=float(matter.rho),
        p=float(matter.p),
        q=np.asarray(matter.q, dtype=np.float64),
        pi=np.asarray(matter.pi, dtype=np.float64),
    )


def build_covariant_residual_pack(
    *,
    H: float,
    geometry,
    residuals,
    electric: np.ndarray,
    magnetic: np.ndarray,
    branch: str,
    global_tilt_present: bool,
) -> CovariantResidualPack:
    """Normalize the core Einstein/Bianchi/Weyl diagnostics."""

    H_ref = max(abs(float(H)), 1.0e-30)
    H2_ref = H_ref * H_ref
    structure_ref = max(float(np.linalg.norm(geometry.algebra.C)), 1.0e-30)
    dual_route = float(geometry.dual_route_curvature_residual_norm)
    if not np.isfinite(dual_route):
        dual_route = float("nan")
    codazzi_norm = float(np.linalg.norm(residuals.codazzi))
    jacobi_norm = float(np.linalg.norm(residuals.jacobi))
    bianchi_norm = float(np.linalg.norm(residuals.twice_contracted_bianchi))
    electric_norm = float(np.linalg.norm(np.asarray(electric, dtype=np.float64)))
    magnetic_norm = float(np.linalg.norm(np.asarray(magnetic, dtype=np.float64)))
    return CovariantResidualPack(
        gauss_abs=float(abs(residuals.gauss)),
        gauss_over_H2_ref=float(abs(residuals.gauss)) / H2_ref,
        codazzi_norm=codazzi_norm,
        codazzi_over_H2_ref=codazzi_norm / H2_ref,
        jacobi_norm=jacobi_norm,
        jacobi_over_structure_ref=jacobi_norm / structure_ref,
        dual_route_curvature=dual_route,
        dual_route_curvature_over_structure_ref=dual_route / structure_ref,
        bianchi_norm=bianchi_norm,
        bianchi_over_H2_ref=bianchi_norm / H2_ref,
        electric_norm=electric_norm,
        electric_over_H2_ref=electric_norm / H2_ref,
        magnetic_norm=magnetic_norm,
        magnetic_over_H2_ref=magnetic_norm / H2_ref,
        metadata={
            "branch": branch,
            "global_tilt_present": bool(global_tilt_present),
            "local_boost_present": False,
            "dual_route_status": geometry.dual_route_status,
            "compact_formula_status": geometry.compact_formula_status,
            "twice_contracted_bianchi_contract": "energy_continuity_plus_momentum_constraint",
        },
    )


def _counterstreaming_species(tilt_speed: float) -> tuple:
    left = decompose_tilted_species(
        TiltedSpeciesParams(
            rho_hat=1.0,
            p_hat=0.0,
            v=np.array([tilt_speed, 0.0, 0.0], dtype=np.float64),
            label="left_counterstream",
        )
    )
    right = decompose_tilted_species(
        TiltedSpeciesParams(
            rho_hat=1.0,
            p_hat=0.0,
            v=np.array([-tilt_speed, 0.0, 0.0], dtype=np.float64),
            label="right_counterstream",
        )
    )
    return (left, right)


def _build_branch_initial_conditions(
    spec: FamilySpec,
    branch: Literal["orthogonal", "tilted"],
    *,
    tilt_speed: float,
    lambda_value: float,
) -> OrthogonalInitialConditions | TiltedInitialConditions:
    if branch == "orthogonal":
        return build_orthogonal_initial_conditions(
            algebra=spec.algebra,
            rho=1.0,
            p=0.0,
            sigma_ab=np.zeros((3, 3), dtype=np.float64),
            lambda_value=lambda_value,
            closure="solve_H",
        )
    return build_tilted_initial_conditions(
        algebra=spec.algebra,
        species=_counterstreaming_species(tilt_speed),
        sigma_ab=np.zeros((3, 3), dtype=np.float64),
        lambda_value=lambda_value,
        closure="solve_H",
    )


def build_family_branch_validation_report(
    family: str | FamilySpec,
    branch: Literal["orthogonal", "tilted"],
    *,
    truncation: Mapping[str, object] | None = None,
    tilt_speed: float = 0.1,
    lambda_value: float = 0.0,
) -> FamilyBranchValidationReport:
    """Build a branch-aware covariant validation report for one family."""

    spec = get_family_spec(family) if isinstance(family, str) else family
    if not spec.algebra.supports_branch(branch):
        raise ValueError(f"{spec.family} does not support branch {branch!r}")
    branch_ic = _build_branch_initial_conditions(
        spec,
        branch,
        tilt_speed=tilt_speed,
        lambda_value=lambda_value,
    )
    normal_frame = _normal_frame_state(branch_ic)
    assembly = assemble_background_rhs(
        H=float(branch_ic.H),
        sigma_ab=np.asarray(branch_ic.sigma_ab, dtype=np.float64),
        matter=normal_frame,
        geometry=branch_ic.geometry,
        lambda_value=lambda_value,
    )
    weyl = build_weyl_diagnostics(
        sigma_ab=np.asarray(branch_ic.sigma_ab, dtype=np.float64),
        sigma_dot_ab=np.asarray(assembly.sigma_dot, dtype=np.float64),
        H=float(branch_ic.H),
        geometry=branch_ic.geometry,
        residuals=assembly.residuals,
        pi_ab=normal_frame.pi,
    )
    trunc = {"ell_max": 2, "mode_labels": ("m0",)} if truncation is None else dict(truncation)
    backend = build_backend(spec, truncation=trunc)
    ops = backend.operator_factory(
        {
            "branch": branch,
            "state_tag": "covariant_validation",
            "opacity_data": {"Gamma_T": 0.0},
            "source_tables": {},
        }
    )
    global_tilt_present = branch == "tilted"
    residual_pack = build_covariant_residual_pack(
        H=float(branch_ic.H),
        geometry=branch_ic.geometry,
        residuals=assembly.residuals,
        electric=weyl.electric,
        magnetic=weyl.magnetic,
        branch=branch,
        global_tilt_present=global_tilt_present,
    )
    return FamilyBranchValidationReport(
        family=spec.family,
        branch=branch,
        class_label=spec.class_label,
        isotropic_anchor=spec.isotropic_anchor,
        global_tilt_present=global_tilt_present,
        local_boost_present=False,
        preferred_backend=spec.preferred_backend,
        operator_kernel_family=ops.operator_kernel_family,
        backend_release_status=ops.release_status,
        hierarchy_size=int(ops.mass_matrix.shape[0]),
        residuals=residual_pack,
        metadata={
            "constraint_policy_required": spec.algebra.branch_policy.constraint_policy_required,
            "global_tilt_contract": (
                "model_matter_frame_state"
                if global_tilt_present
                else "orthogonal_branch_zero_global_tilt"
            ),
            "local_boost_contract": "observer_side_only_not_applied_in_background_or_backend",
            "orthogonal_global_tilt_local_boost_split": spec.orthogonal_global_tilt_local_boost_split,
            "ic_provenance_status": spec.ic_provenance_status,
            "backend_seed_provenance_mode": ops.seed_provenance_mode,
            "species_channels": (
                len(branch_ic.matter.species)
                if isinstance(branch_ic, TiltedInitialConditions)
                else 0
            ),
        },
    )


def build_all_family_branch_validation_matrix(
    *,
    families: tuple[str, ...] | None = None,
    include_tilted: bool = True,
    truncation: Mapping[str, object] | None = None,
    tilt_speed: float = 0.1,
) -> dict[tuple[str, str], FamilyBranchValidationReport]:
    """Instantiate covariant validation reports for every requested family branch."""

    labels = tuple(ALL_BIANCHI_TYPES if families is None else families)
    out: dict[tuple[str, str], FamilyBranchValidationReport] = {}
    for family in labels:
        out[(family, "orthogonal")] = build_family_branch_validation_report(
            family,
            "orthogonal",
            truncation=truncation,
            tilt_speed=tilt_speed,
        )
        if include_tilted:
            out[(family, "tilted")] = build_family_branch_validation_report(
                family,
                "tilted",
                truncation=truncation,
                tilt_speed=tilt_speed,
            )
    return out
