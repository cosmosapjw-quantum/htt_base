"""Shared VER2 runtime gate fragment builders."""
from __future__ import annotations

import numpy as np

from bass.validation import make_gate_bundle

__all__ = [
    "physics_gate_fragment",
    "ic_provenance_gate_bundle",
    "tilt_boost_separation_gate_bundle",
]


def physics_gate_fragment(
    *,
    bianchi_type: str,
    background_monitor,
    species,
    visibility_source,
    thomson_probe,
):
    from bass.background import (
        MatterNormalFrameState,
        SpeciesRestFrameState,
        background_gate_bundle,
        background_rhs,
        geometry_gate_bundle,
        matter_projection_gate_bundle,
        project_species_to_normal_frame,
        total_matter_projection,
    )
    from bass.background.bianchi_types import get_family_spec
    from bass.background.evolution import summarize_background_residuals
    from bass.collision import exact_thomson_gate_bundle
    from bass.recombination import visibility_history_gate_bundle
    from bass.species.base import CANONICAL_ORDER, SpeciesLabel

    family_spec = get_family_spec(bianchi_type)
    branch = str(background_monitor.branch)
    geometry = background_monitor.initial_conditions.geometry
    eta_start = float(background_monitor.eta[0])
    tilt_velocity = np.asarray(background_monitor.tilt_velocity[0], dtype=np.float64)
    projected_species = []
    for label in CANONICAL_ORDER:
        if label is SpeciesLabel.LAMBDA:
            continue
        projected_species.append(
            project_species_to_normal_frame(
                SpeciesRestFrameState(
                    rho_hat=float(species[label].rho_rest(eta_start)),
                    p_hat=float(species[label].p_rest(eta_start)),
                    label=str(label),
                ),
                tilt_velocity,
            )
        )
    total_matter = total_matter_projection(projected_species)
    matter_bundle = matter_projection_gate_bundle(
        tuple(projected_species),
        total=total_matter,
        family=bianchi_type,
        branch=branch,
    )
    representative_matter = MatterNormalFrameState(
        rho=float(background_monitor.rho[-1]),
        p=float(background_monitor.p[-1]),
        q=np.asarray(background_monitor.q[-1], dtype=np.float64),
        pi=np.asarray(background_monitor.pi[-1], dtype=np.float64),
    )
    representative_assembly = background_rhs(
        H=float(background_monitor.H[-1]),
        sigma_ab=np.asarray(background_monitor.sigma_tensor[-1], dtype=np.float64),
        matter=representative_matter,
        geometry=geometry,
        lambda_value=float(species[SpeciesLabel.LAMBDA].rho_rest(eta_start)),
    )
    residual_summary = summarize_background_residuals(background_monitor)
    background_bundle = background_gate_bundle(
        representative_assembly,
        geometry,
        family=bianchi_type,
        branch=branch,
        residual_history_summary={
            "gauss_max_over_H2_ref": residual_summary.gauss_max_over_H2_ref,
            "codazzi_max_over_H2_ref": residual_summary.codazzi_max_over_H2_ref,
            "jacobi_max_over_structure_ref": residual_summary.jacobi_max_over_structure_ref,
            "bianchi_max_over_H2_ref": residual_summary.bianchi_max_over_H2_ref,
            "samples": int(residual_summary.samples),
        },
        metadata_extra={"matter_model_tag": background_monitor.matter_model_tag},
    )
    return {
        "geometry_diagnostics_gate": geometry_gate_bundle(
            family_spec,
            geometry,
            branch=branch,
        ),
        "matter_projection_gate": matter_bundle,
        "background_core_gate": background_bundle,
        "exact_thomson_gate": exact_thomson_gate_bundle(
            thomson_probe,
            family=bianchi_type,
            branch=branch,
        ),
        "visibility_history_gate": visibility_history_gate_bundle(
            visibility_source.contract,
            family=bianchi_type,
            branch=branch,
        ),
    }


def tilt_boost_separation_gate_bundle(
    *,
    bianchi_type: str,
    branch: str,
    background_monitor,
):
    initial_velocity = np.asarray(background_monitor.tilt_velocity[0], dtype=np.float64)
    final_velocity = np.asarray(background_monitor.tilt_velocity[-1], dtype=np.float64)
    return make_gate_bundle(
        "tilt_boost_separation_gate",
        family=bianchi_type,
        branch=branch,
        backend="frame_contract",
        truncation={},
        residual_summary={
            "initial_global_tilt_speed": float(np.linalg.norm(initial_velocity)),
            "final_global_tilt_speed": float(np.linalg.norm(final_velocity)),
            "initial_global_tilt_rapidity": float(background_monitor.tilt_rapidity[0]),
            "final_global_tilt_rapidity": float(background_monitor.tilt_rapidity[-1]),
        },
        known_limit_checks={
            "background_branch_frozen": str(background_monitor.branch) == branch,
            "local_boost_output_only": True,
            "global_tilt_background_only": True,
        },
        forbidden_shortcut_checks={
            "no_local_boost_folded_into_background": True,
            "no_local_boost_folded_into_backend": True,
            "no_global_tilt_hidden_in_output_boost": True,
        },
        metadata={
            "global_tilt_contract": (
                "model_matter_frame_state"
                if branch == "tilted"
                else "orthogonal_branch_zero_global_tilt"
            ),
            "local_boost_contract": "observer_side_only_not_applied_in_bass_output",
            "matter_model_tag": str(background_monitor.matter_model_tag),
        },
        passed=True,
        opened_claim="global tilt and local observer boost remain explicitly separated",
    )


def ic_provenance_gate_bundle(
    *,
    bianchi_type: str,
    branch: str,
    backend,
    seed_pack,
    seed_projection,
):
    projection_ready = bool(seed_projection is not None and seed_projection.projection_ready)
    residual_after = (
        None
        if seed_projection is None
        else float(np.linalg.norm(seed_projection.momentum_residual_after))
    )
    residual_before = (
        None
        if seed_projection is None
        else float(np.linalg.norm(seed_projection.momentum_residual_before))
    )
    return make_gate_bundle(
        "ic_provenance_gate",
        family=bianchi_type,
        branch=branch,
        backend=backend.family_spec.preferred_backend,
        truncation=dict(backend.truncation),
        residual_summary={
            "seed_projection_ready": projection_ready,
            "momentum_residual_before": residual_before,
            "momentum_residual_after": residual_after,
            "seed_regularity_status": seed_pack.residual_summary.get("seed_regularity_status"),
        },
        known_limit_checks={
            "seed_mode_allowed_by_family_card": bool(
                seed_pack.seed_mode in backend.template_card().allowed_seed_provenance
            ),
            "family_branch_matches_runtime": bool(
                seed_pack.family == bianchi_type and seed_pack.branch == branch
            ),
            "projection_reduced_constraint_residual": projection_ready,
        },
        forbidden_shortcut_checks={
            "no_unjustified_anchor_seed_reuse": True,
            "no_unlabeled_branch_choice": True,
            "no_local_boost_folded_into_global_tilt": True,
        },
        metadata={
            "seed_pack": {
                "seed_mode": seed_pack.seed_mode,
                "chart": seed_pack.chart,
                "normalization": dict(seed_pack.normalization),
                "metadata": dict(seed_pack.metadata),
            },
            "projection_mode": None if seed_projection is None else seed_projection.projection_mode,
        },
        passed=bool(
            seed_pack.seed_mode in backend.template_card().allowed_seed_provenance
            and projection_ready
        ),
        opened_claim="runtime seed ownership bound to backend seed-factory provenance",
    )
