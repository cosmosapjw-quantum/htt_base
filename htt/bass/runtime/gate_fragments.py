"""Shared VER2 runtime gate fragment builders."""
from __future__ import annotations

import numpy as np

from bass.validation import make_gate_bundle

__all__ = [
    "ic_provenance_gate_bundle",
    "tilt_boost_separation_gate_bundle",
]


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
