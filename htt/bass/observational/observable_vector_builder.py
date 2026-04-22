"""VER2 `ObservableVector` extraction shells."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np

from common.contracts import ObservableVector, SkySupport, SolverCoreOutput

from bass.observational._manifest import (
    derive_manifest,
    sky_support_metadata,
    stable_payload_hash,
)
from bass.observational.covariance_sparse import (
    build_covariance_feature_summary,
    build_sparse_covariance_proxy,
)

__all__ = ["build_observable_vector_from_solver_output"]


def _mapping_or_none(value: object) -> Mapping[str, object] | None:
    return value if isinstance(value, Mapping) else None


def _default_cl(
    solver_output: SolverCoreOutput,
    covariance_bundle: Mapping[str, object] | None,
) -> dict[str, object]:
    if covariance_bundle is not None and isinstance(covariance_bundle.get("C_ell"), Mapping):
        return {
            channel: np.asarray(values, dtype=float)
            for channel, values in covariance_bundle["C_ell"].items()  # type: ignore[index]
        }
    return {}


def _covariance_readiness(
    covariance_bundle: Mapping[str, object] | None,
    covariance_features: Mapping[str, object] | None,
    biposh_payload: Mapping[str, object] | None,
) -> str:
    if covariance_bundle is None or covariance_features is None or biposh_payload is None:
        return "missing"
    if bool(covariance_features.get("supports_harmonic_gaussian", False)):
        psd_guard = _mapping_or_none(covariance_features.get("psd_guard"))
        symmetry_guard = _mapping_or_none(covariance_features.get("symmetry_guard"))
        invariant_guard = _mapping_or_none(covariance_features.get("invariant_guard"))
        if (
            psd_guard is not None
            and symmetry_guard is not None
            and invariant_guard is not None
            and bool(psd_guard.get("passed", False))
            and bool(symmetry_guard.get("passed", False))
            and bool(invariant_guard.get("passed", False))
        ):
            return "full"
    if bool(covariance_features.get("supports_full_biposh", False)):
        return "full"
    if bool(covariance_features.get("supports_basis_reduced_morphology", False)):
        return "reduced"
    return "proxy"


def _default_alm_features(
    solver_output: SolverCoreOutput,
    covariance_bundle: Mapping[str, object] | None,
    covariance_features: Mapping[str, object] | None,
    biposh_payload: Mapping[str, object] | None,
) -> dict[str, object]:
    covariance_readiness = _covariance_readiness(
        covariance_bundle,
        covariance_features,
        biposh_payload,
    )
    preferred_axis = None
    if covariance_bundle is not None and covariance_bundle.get("preferred_axis") is not None:
        preferred_axis = tuple(
            float(value)
            for value in np.asarray(covariance_bundle["preferred_axis"], dtype=float)
        )
    alm_representation = None
    observer_quadrature_points = None
    observer_quadrature_rule = None
    if isinstance(solver_output.alm_T, Mapping):
        alm_representation = str(solver_output.alm_T.get("representation", ""))
        directions = solver_output.alm_T.get("sphere_directions")
        if directions is not None:
            observer_quadrature_points = int(np.asarray(directions, dtype=float).shape[0])
        quadrature_rule = solver_output.alm_T.get("quadrature_rule")
        if quadrature_rule is not None:
            observer_quadrature_rule = str(quadrature_rule)
    observer_reconstruction_status = "unreported"
    if alm_representation in {
        "lowell_pstf_final_slice",
        "ver2_native_pstf_final_slice",
    }:
        observer_reconstruction_status = "final_slice_only_no_sphere_reconstruction"
    if alm_representation in {
        "lowell_pstf_sphere_reconstruction",
        "ver2_native_pstf_sphere_reconstruction",
        "tier_a_validation_reference_sphere_reconstruction",
    }:
        observer_reconstruction_status = "sphere_reconstructed_from_pstf"
    return {
        "harmonic_basis": str(solver_output.metadata["harmonic_basis"]),
        "eb_sign_convention": str(solver_output.metadata["eb_sign_convention"]),
        "observer_neutral": bool(solver_output.metadata.get("observer_neutral", True)),
        "bianchi_type": solver_output.metadata.get("bianchi_type"),
        "bianchi_branch": solver_output.metadata.get("bianchi_branch"),
        "solver_domain_scope": solver_output.metadata.get("solver_domain_scope"),
        "global_tilt_contract": solver_output.metadata.get("global_tilt_contract"),
        "local_boost_contract": solver_output.metadata.get("local_boost_contract"),
        "tilt_boost_separation": solver_output.metadata.get("tilt_boost_separation"),
        "preferred_axis": preferred_axis,
        "deterministic_template_present": solver_output.deterministic_template is not None,
        "propagator_ready": bool(solver_output.metadata.get("propagator_ready", False)),
        "propagator_readiness": solver_output.metadata.get(
            "propagator_readiness",
            "contract_only_unavailable",
        ),
        "propagator_exactness": solver_output.metadata.get(
            "propagator_exactness",
            solver_output.metadata.get(
                "propagator_readiness",
                "contract_only_unavailable",
            ),
        ),
        "backend_lookup_resolution_status": solver_output.metadata.get(
            "backend_lookup_resolution_status"
        ),
        "backend_verification_crosscheck_pass": bool(
            solver_output.metadata.get("backend_verification_crosscheck_pass", False)
        ),
        "b_mode_runtime_available": bool(
            solver_output.metadata.get("b_mode_runtime_available", False)
        ),
        "b_mode_payload_status": solver_output.metadata.get("b_mode_payload_status"),
        "canonical_projection_covered_mode_labels": list(
            solver_output.metadata.get("canonical_projection_covered_mode_labels", [])
        ),
        "covariance_readiness": covariance_readiness,
        "fitting_ready": covariance_readiness == "full",
        "off_diagonal_strategy": solver_output.metadata.get("off_diagonal_strategy"),
        "covariance_representation": None if biposh_payload is None else biposh_payload.get("representation"),
        "harmonic_gaussian_ready": False
        if covariance_features is None
        else bool(covariance_features.get("supports_harmonic_gaussian", False)),
        "harmonic_subspace_size": None
        if covariance_features is None
        or not isinstance(covariance_features.get("harmonic_gaussian_covariance"), Mapping)
        else int(
            covariance_features["harmonic_gaussian_covariance"].get(  # type: ignore[index]
                "subspace_size",
                0,
            )
        ),
        "observer_reconstruction_status": observer_reconstruction_status,
        "observer_quadrature_points": observer_quadrature_points,
        "observer_quadrature_rule": observer_quadrature_rule,
        "local_global_degeneracy": None
        if covariance_features is None
        else covariance_features.get("local_global_degeneracy"),
    }


def _default_scan_volume(
    solver_output: SolverCoreOutput,
    sky_support: SkySupport,
    *,
    ell_max: int,
    channels: tuple[str, ...],
    covariance_bundle: Mapping[str, object] | None,
    covariance_features: Mapping[str, object] | None,
    biposh_payload: Mapping[str, object] | None,
) -> dict[str, object]:
    reconstruction_status = "unreported"
    if isinstance(solver_output.alm_T, Mapping):
        representation = str(solver_output.alm_T.get("representation", ""))
        if representation in {
            "lowell_pstf_final_slice",
            "ver2_native_pstf_final_slice",
        }:
            reconstruction_status = "final_slice_only_no_sphere_reconstruction"
        if representation in {
            "lowell_pstf_sphere_reconstruction",
            "ver2_native_pstf_sphere_reconstruction",
            "tier_a_validation_reference_sphere_reconstruction",
        }:
            reconstruction_status = "sphere_reconstructed_from_pstf"
    base = {
        "definition": "lowell_observable_vector_skeleton",
        "ell_max": ell_max,
        "channels": list(channels),
        "harmonic_basis": str(solver_output.metadata["harmonic_basis"]),
        "bianchi_type": solver_output.metadata.get("bianchi_type"),
        "bianchi_branch": solver_output.metadata.get("bianchi_branch"),
        "solver_domain_scope": solver_output.metadata.get("solver_domain_scope"),
        "global_tilt_contract": solver_output.metadata.get("global_tilt_contract"),
        "local_boost_contract": solver_output.metadata.get("local_boost_contract"),
        "tilt_boost_separation": solver_output.metadata.get("tilt_boost_separation"),
        "covariance_readiness": _covariance_readiness(
            covariance_bundle,
            covariance_features,
            biposh_payload,
        ),
        "selection_mode": sky_support.selection_mode,
        "thomson_mode": str(solver_output.metadata["thomson_mode"]),
        "observer_reconstruction_status": reconstruction_status,
    }
    base["scan_volume_hash"] = stable_payload_hash(base)
    return base


def _resolved_channels(
    cl_payload: Mapping[str, object],
    *,
    biposh_payload: Mapping[str, object] | None,
    template_payload: Mapping[str, object] | None,
) -> tuple[str, ...]:
    ordered: list[str] = [
        channel
        for channel in ("TT", "TE", "EE", "BB", "TB", "EB")
        if channel in cl_payload
    ]
    if biposh_payload is not None:
        ordered.append("BiPoSH")
    if template_payload is not None:
        ordered.append("template")
    return tuple(ordered) or ("scalar_summary",)


def _observable_manifest_status(
    *,
    solver_output: SolverCoreOutput,
    sky_support: SkySupport,
    covariance_payload: Mapping[str, object] | None,
    covariance_readiness: str,
) -> tuple[str, tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    required_gates = (
        "covariance_features_present",
        "covariance_full_readiness",
        "sky_support_mock_calibrated",
        "covariance_psd_guard",
        "covariance_symmetry_guard",
        "covariance_invariant_guard",
    )
    failed: list[str] = []
    if covariance_payload is None:
        failed.append("covariance_features_present")
    if covariance_readiness != "full":
        failed.append("covariance_full_readiness")
    if sky_support.selection_mode != "mock_calibrated" or sky_support.mock_coverage_status != "adequate":
        failed.append("sky_support_mock_calibrated")
    if covariance_payload is not None:
        if not bool(covariance_payload["psd_guard"]["passed"]):
            failed.append("covariance_psd_guard")
        if not bool(covariance_payload["symmetry_guard"]["passed"]):
            failed.append("covariance_symmetry_guard")
        if not bool(covariance_payload["invariant_guard"]["passed"]):
            failed.append("covariance_invariant_guard")
    passed = tuple(gate for gate in required_gates if gate not in failed)
    if not failed:
        return "production_candidate", required_gates, passed, ()
    if covariance_payload is None:
        return "blocked_missing_covariance", required_gates, passed, tuple(failed)
    return "diagnostic_only", required_gates, passed, tuple(failed)


def build_observable_vector_from_solver_output(
    solver_output: SolverCoreOutput,
    *,
    sky_support: SkySupport,
    cl: Mapping[str, object] | None = None,
    alm_features: Mapping[str, object] | None = None,
    biposh: Mapping[str, object] | None = None,
    template_fit: Mapping[str, object] | None = None,
    covariance_features: Mapping[str, object] | None = None,
    scan_volume: Mapping[str, object] | None = None,
) -> ObservableVector:
    """Build a descriptive low-ell observable shell from a solver output."""
    if solver_output.manifest.owner != "BASS":
        raise ValueError("ObservableVector sources must be BASS-owned")
    covariance_bundle = _mapping_or_none(solver_output.anisotropic_covariance)
    cl_payload = dict(cl) if cl is not None else _default_cl(solver_output, covariance_bundle)
    ell_max = int(solver_output.metadata.get("multipole_cutoff", 0))
    if cl_payload:
        ell_max = max(
            ell_max,
            max(int(np.asarray(values).shape[0] - 1) for values in cl_payload.values()),
        )
    biposh_payload = dict(biposh) if biposh is not None else None
    covariance_payload = dict(covariance_features) if covariance_features is not None else None
    if covariance_bundle is not None:
        if biposh_payload is None:
            biposh_payload = build_sparse_covariance_proxy(
                covariance_bundle,
                harmonic_convention=str(solver_output.metadata["harmonic_basis"]),
                angular_payload=_mapping_or_none(solver_output.alm_T),
            )
        if covariance_payload is None:
            covariance_payload = build_covariance_feature_summary(
                covariance_bundle,
                harmonic_convention=str(solver_output.metadata["harmonic_basis"]),
                angular_payload=_mapping_or_none(solver_output.alm_T),
            )
    template_payload = dict(template_fit) if template_fit is not None else None
    if template_payload is None and solver_output.deterministic_template is not None:
        template_payload = dict(solver_output.deterministic_template)
        template_payload.setdefault("descriptive_only", True)
    channels = _resolved_channels(
        cl_payload,
        biposh_payload=biposh_payload,
        template_payload=template_payload,
    )
    feature_payload = (
        dict(alm_features)
        if alm_features is not None
        else _default_alm_features(
            solver_output,
            covariance_bundle,
            covariance_payload,
            biposh_payload,
        )
    )
    scan_payload = (
        dict(scan_volume)
        if scan_volume is not None
        else _default_scan_volume(
            solver_output,
            sky_support,
            ell_max=ell_max,
            channels=channels,
            covariance_bundle=covariance_bundle,
            covariance_features=covariance_payload,
            biposh_payload=biposh_payload,
        )
    )
    covariance_readiness = _covariance_readiness(
        covariance_bundle,
        covariance_payload,
        biposh_payload,
    )
    feature_payload.setdefault("covariance_readiness", covariance_readiness)
    feature_payload.setdefault("fitting_ready", covariance_readiness == "full")
    scan_payload.setdefault("covariance_readiness", covariance_readiness)
    scan_payload.setdefault("scan_volume_hash", stable_payload_hash(scan_payload))
    production_status, required_gates, passed_gates, failed_gates = _observable_manifest_status(
        solver_output=solver_output,
        sky_support=sky_support,
        covariance_payload=covariance_payload,
        covariance_readiness=covariance_readiness,
    )
    caveats = [
        "diagonal_cl_not_sufficient_for_directional_claims",
        "no_posterior_or_evidence_semantics",
    ]
    if covariance_readiness != "full":
        caveats.append(f"covariance_readiness_{covariance_readiness}")
        caveats.append("posterior_blocked_by_covariance_readiness")
    if biposh_payload is not None and biposh_payload.get("representation") == "sparse_mode_block_proxy":
        caveats.append("proxy_morphology_not_full_biposh")
    if biposh_payload is not None and biposh_payload.get("representation") == "low_ell_harmonic_sparse_basis":
        caveats.append("basis_reduced_covariance_not_full_biposh")
    if (
        covariance_payload is not None
        and bool(covariance_payload.get("supports_harmonic_gaussian", False))
    ):
        caveats = [item for item in caveats if item != "no_posterior_or_evidence_semantics"]
    if feature_payload.get("observer_reconstruction_status") == "final_slice_only_no_sphere_reconstruction":
        caveats.append("observer_reconstruction_bridge_pending")
    artifact_id = f"{solver_output.manifest.artifact_id}.observable_vector"
    artifact_path = (
        f"artifacts/bass/{artifact_id.replace('.', '_')}.json"
    )
    manifest = derive_manifest(
        solver_output.manifest,
        artifact_id=artifact_id,
        artifact_path=artifact_path,
        owner="BASS",
        implementation_scope="bass_py",
        claim_tier="conditional",
        production_status=production_status,
        caveats=tuple(caveats),
        required_gates=required_gates,
        passed_gates=passed_gates,
        failed_gates=failed_gates,
        statistics_definitions={
            "surface": "ObservableVector",
            "channels": list(channels),
            "ell_max": ell_max,
            "scan_volume_hash": str(scan_payload["scan_volume_hash"]),
            "sky_support": sky_support_metadata(sky_support),
            "covariance_representation": None if biposh_payload is None else biposh_payload.get("representation"),
            "covariance_readiness": covariance_readiness,
            "harmonic_gaussian_ready": False
            if covariance_payload is None
            else bool(covariance_payload.get("supports_harmonic_gaussian", False)),
            "local_global_degeneracy": None
            if covariance_payload is None
            else covariance_payload.get("local_global_degeneracy"),
        },
    )
    return ObservableVector(
        ell_max=ell_max,
        channels=channels,
        cl=cl_payload,
        alm_features=feature_payload,
        biposh=biposh_payload,
        template_fit=template_payload,
        covariance_features=covariance_payload,
        scan_volume=scan_payload,
        sky_support=sky_support,
        manifest=manifest,
    )
