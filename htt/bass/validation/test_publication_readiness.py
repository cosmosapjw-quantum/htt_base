from __future__ import annotations

import numpy as np
import pytest

from common.contracts import ArtifactManifest, SolverCoreOutput

from bass.forward import write_output_archive
from bass.los.families.residual_report import default_family_residual_report
from bass.validation import GATE_LADDER
from bass.validation.publication_readiness import (
    assert_publication_claim_allowed,
    build_family_readiness_manifest,
    evaluate_publication_claim,
)


def _manifest() -> ArtifactManifest:
    return ArtifactManifest(
        artifact_id="bass.validation.publication-readiness",
        artifact_path="artifacts/bass/publication_readiness",
        owner="BASS",
        implementation_scope="canonical_BASS",
        claim_tier="conditional",
        production_status="production_candidate",
        created_by="test-suite",
        git_commit="deadbeef",
        config_hash="cfg",
        input_hashes=["seed"],
        code_version="0.0-test",
        schema_version="ver3-v0",
    )


def _output() -> SolverCoreOutput:
    lmax = 2
    size = (lmax + 1) ** 2
    payload = {
        "representation": "ver2_native_pstf_sphere_reconstruction",
        "coefficient_representation": "ver2_native_pstf_final_slice",
        "ell_max": lmax,
        "values": np.linspace(0.0, 8.0e-6, size),
    }
    return SolverCoreOutput(
        alm_T=payload,
        alm_E={**payload, "values": np.linspace(1.0e-6, 9.0e-6, size)},
        alm_B={**payload, "values": np.zeros(size)},
        map_T=None,
        map_Q=None,
        map_U=None,
        deterministic_template={"kind": "test"},
        anisotropic_covariance=None,
        metadata={
            "bianchi_type": "I",
            "bianchi_branch": "orthogonal",
            "harmonic_basis": "m_explicit",
            "eb_sign_convention": "cmb",
            "multipole_cutoff": lmax,
            "tilt_enabled": False,
            "thomson_mode": "electron_frame_projected",
            "map_output_support": "not_implemented",
            "tilt_boost_separation": "explicit_nonmerged",
        },
        manifest=_manifest(),
    )


def test_family_manifest_separates_registry_from_output_readiness() -> None:
    manifest = build_family_readiness_manifest()
    assert len(manifest) == 12
    assert manifest["I"].registry_exists is True
    assert manifest["I"].backend_evidence_status == "not_provided"
    assert manifest["I"].output_ready is False
    assert "backend_residual_pack_not_provided" in manifest["I"].block_reasons
    assert manifest["II"].registry_exists is True
    assert manifest["II"].output_ready is False
    assert manifest["II"].ic_status == "residual-backed"
    assert "backend_residual_pack_not_provided" in manifest["II"].block_reasons


def test_family_manifest_uses_residual_pack_evidence_without_promoting_ic() -> None:
    packs = default_family_residual_report()
    manifest = build_family_readiness_manifest(family_residual_packs=packs)
    assert manifest["I"].backend_evidence_status == "residual_pack_passed"
    assert manifest["I"].backend_evidence_passed is True
    assert manifest["I"].output_ready is True
    assert manifest["II"].backend_evidence_status == "residual_pack_passed"
    assert manifest["II"].backend_evidence_passed is True
    assert manifest["II"].output_ready is True
    assert manifest["VII_0"].backend_evidence_status == "residual_pack_passed"
    assert manifest["VII_0"].output_ready is True
    assert manifest["VI_0"].backend_evidence_status == "residual_pack_passed"
    assert manifest["VI_0"].output_ready is True
    assert manifest["VII_h"].backend_evidence_status == "residual_pack_passed"
    assert manifest["VII_h"].output_ready is True
    assert manifest["III"].backend_evidence_status == "residual_pack_passed"
    assert manifest["III"].output_ready is True
    assert manifest["IV"].backend_evidence_status == "residual_pack_passed"
    assert manifest["IV"].output_ready is True
    assert manifest["VI_h"].backend_evidence_status == "residual_pack_passed"
    assert manifest["VI_h"].output_ready is True
    assert manifest["VIII"].backend_evidence_status == "residual_pack_passed"
    assert manifest["VIII"].output_ready is True
    assert manifest["II"].ic_status == "residual-backed"


def test_publication_grade_11_family_solver_opens_with_all_residual_packs() -> None:
    manifest = build_family_readiness_manifest(
        family_residual_packs=default_family_residual_report(),
    )
    decision = evaluate_publication_claim(
        "publication_grade_11_family_solver",
        family_manifest=manifest,
    )
    assert decision.allowed is True
    assert decision.blockers == ()
    assert_publication_claim_allowed(
        "publication_grade_11_family_solver",
        family_manifest=manifest,
    )


def test_family_backend_residual_evidence_claim_requires_all_packs() -> None:
    packs = default_family_residual_report()
    manifest = build_family_readiness_manifest(family_residual_packs=packs)
    decision = evaluate_publication_claim(
        "family_backend_residual_evidence",
        family_manifest=manifest,
    )
    assert decision.allowed is True

    broken = dict(packs)
    payload = broken["II"].as_payload()
    payload["passed"] = False
    payload["violated_tolerances"] = ["nil_chart_regularity"]
    broken["II"] = payload
    blocked_manifest = build_family_readiness_manifest(family_residual_packs=broken)
    blocked = evaluate_publication_claim(
        "family_backend_residual_evidence",
        family_manifest=blocked_manifest,
    )
    assert blocked.allowed is False
    assert any(blocker.startswith("II:") for blocker in blocked.blockers)


def test_full_anisotropic_polarization_requires_b_runtime_and_support() -> None:
    blocked = evaluate_publication_claim(
        "full_anisotropic_polarization_output",
        output_metadata={
            "thomson_mode": "electron_frame_projected",
            "b_mode_runtime_available": False,
            "b_mode_output_support": "flrw_zero_only",
            "tilt_boost_separation": "explicit_nonmerged",
        },
    )
    assert blocked.allowed is False
    assert "b_runtime" in blocked.blockers
    assert "b_support" in blocked.blockers

    opened = evaluate_publication_claim(
        "full_anisotropic_polarization_output",
        output_metadata={
            "thomson_mode": "electron_frame_exact_wrapper",
            "b_mode_runtime_available": True,
            "b_mode_output_support": "wigner_d_path_b",
            "tilt_boost_separation": "explicit_nonmerged",
        },
    )
    assert opened.allowed is True


def test_statistics_ready_likelihood_requires_gate_and_metadata() -> None:
    gates = {gate: True for gate in GATE_LADDER[:-1]}
    opened = evaluate_publication_claim(
        "statistics_ready_likelihood",
        gate_registry=gates,
        output_metadata={
            "covariance_readiness": "full",
            "diagnostic_only": False,
            "fitting_allowed": True,
            "statistics_owner": "bass.inference.live_binding",
            "statistics_readiness_decision": {"allowed": True},
        },
    )
    assert opened.allowed is True

    blocked = evaluate_publication_claim(
        "statistics_ready_likelihood",
        gate_registry={},
        output_metadata={
            "covariance_readiness": "proxy",
            "diagnostic_only": True,
            "fitting_allowed": False,
        },
    )
    assert blocked.allowed is False
    assert set(blocked.blockers) == {
        "gate_allowed",
        "covariance_full",
        "not_diagnostic_only",
        "fitting_allowed",
        "statistics_decision_allowed",
        "statistics_owner_is_inference",
    }


def test_harmonic_output_archive_claim_uses_file_validator(tmp_path) -> None:
    write_output_archive(_output(), tmp_path)
    decision = evaluate_publication_claim(
        "harmonic_output_archive",
        archive_dir=str(tmp_path),
    )
    assert decision.allowed is True
    assert decision.evidence["archive_valid"] is True


def test_optimization_same_physics_requires_all_axes() -> None:
    blocked = evaluate_publication_claim(
        "optimization_same_physics",
        output_metadata={
            "optimization_same_equations": True,
            "optimization_same_tolerance": True,
            "optimization_same_cutoff": False,
            "optimization_same_observable": True,
            "optimization_identity_status": "within_declared_tolerance",
        },
    )
    assert blocked.allowed is False
    assert blocked.blockers == ("same_cutoff",)

    opened = evaluate_publication_claim(
        "optimization_same_physics",
        output_metadata={
            "optimization_same_equations": True,
            "optimization_same_tolerance": True,
            "optimization_same_cutoff": True,
            "optimization_same_observable": True,
            "optimization_identity_status": "bit_identical",
        },
    )
    assert opened.allowed is True
