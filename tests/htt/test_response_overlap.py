from __future__ import annotations

import json

import numpy as np
import pytest

from common.transfer_registry import TransferFunctionSpec, TransferValidRange


_COMMAND = "python -m pytest tests/htt/test_response_overlap.py -q"
_WORKTREE = "test-worktree"
_INPUT_HASHES = ("sha256:" + "a" * 64,)


def _transfer_metadata(transfer_id: str) -> dict[str, object]:
    spec = TransferFunctionSpec(
        transfer_id=transfer_id,
        source="AniCLASS_external",
        family="BianchiI",
        valid_range=TransferValidRange(k_min=1.0e-5, k_max=0.2, ell_min=2, ell_max=30),
        observable_kind="template",
        normalization="unit_primordial_curvature",
        calibration_status="external_calibrated",
        caveats=("external-transfer path", "transfer-conditional result"),
        source_ref=f"aniclass:{transfer_id}",
    )
    return spec.to_metadata()


def _audit_kwargs(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "local_boost_response": (1.0, 0.0),
        "global_tilt_response": (0.0, 1.0),
        "covariance": np.eye(2),
        "observable_labels": ("dipole", "depth"),
        "artifact_id": "htt-response-overlap-fixture",
        "artifact_path": "memory://htt-response-overlap-fixture.json",
        "input_hashes": _INPUT_HASHES,
        "generating_command": _COMMAND,
        "worktree_state": _WORKTREE,
        "sky_support_status": "pr040_sky_support_attached",
        "mask_status": "mask_hash_recorded",
        "covariance_status": "diagnostic_covariance_supplied",
        "null_mock_status": "rank_audit_without_null_fpr",
    }
    values.update(overrides)
    return values


def test_response_overlap_computes_rho_and_full_rank_manifest():
    from htt.departure.response_overlap import (
        build_response_overlap_audit,
        require_rank_audit_for_model_run,
    )

    audit = build_response_overlap_audit(**_audit_kwargs())
    payload = audit.as_payload()

    assert audit.rho_LB_GT == pytest.approx(0.0)
    assert audit.projected_rank == 2
    assert audit.rank_status == "full_rank"
    assert audit.claim_status == "identifiable_diagnostic_candidate"
    assert audit.model_run_gate["allowed"] is True
    assert audit.singular_values == pytest.approx((1.0, 1.0))
    assert require_rank_audit_for_model_run(audit) is audit
    assert payload["manifest"]["owner"] == "HTT"
    assert payload["manifest"]["implementation_scope"] == "htt"
    assert payload["manifest"]["claim_tier"] == "diagnostic_only"
    assert payload["transfer_source"] == "none"
    assert payload["sky_support_status"] == "pr040_sky_support_attached"
    assert payload["covariance_status"] == "diagnostic_covariance_supplied"


def test_rank_deficient_responses_emit_no_claim_and_block_model_run():
    from htt.departure.response_overlap import (
        build_response_overlap_audit,
        require_rank_audit_for_model_run,
    )

    audit = build_response_overlap_audit(
        **_audit_kwargs(
            local_boost_response=(1.0, 0.0),
            global_tilt_response=(2.0, 0.0),
        )
    )

    assert audit.rho_LB_GT == pytest.approx(1.0)
    assert audit.projected_rank == 1
    assert audit.rank_status == "rank_deficient"
    assert audit.claim_status == "no_claim"
    assert audit.model_run_gate["allowed"] is False
    assert "rank_deficient" in audit.no_claim_reasons
    with pytest.raises(RuntimeError, match="rank audit"):
        require_rank_audit_for_model_run(audit)


def test_rank_precondition_guard_ignores_mutable_gate_tampering():
    from htt.departure.response_overlap import (
        build_response_overlap_audit,
        require_rank_audit_for_model_run,
    )

    audit = build_response_overlap_audit(
        **_audit_kwargs(
            local_boost_response=(1.0, 0.0),
            global_tilt_response=(2.0, 0.0),
        )
    )

    with pytest.raises(TypeError):
        audit.model_run_gate["allowed"] = True
    object.__setattr__(
        audit,
        "model_run_gate",
        {"allowed": True, "blocked_reasons": []},
    )
    with pytest.raises(RuntimeError, match="rank audit"):
        require_rank_audit_for_model_run(audit)


def test_nuisance_projection_can_remove_identifiability():
    from htt.departure.response_overlap import build_response_overlap_audit

    audit = build_response_overlap_audit(
        **_audit_kwargs(
            local_boost_response=(1.0, 0.0, 0.0),
            global_tilt_response=(1.0, 1.0, 0.0),
            covariance=np.eye(3),
            observable_labels=("dipole", "depth", "template"),
            nuisance_responses=((1.0, 0.0, 0.0),),
        )
    )

    assert audit.nuisance_projection_status == "projected"
    assert audit.nuisance_rank == 1
    assert audit.projected_rank == 1
    assert audit.rank_status == "rank_deficient"
    assert audit.model_run_gate["allowed"] is False
    assert "zero_projected_response" in audit.no_claim_reasons


def test_response_overlap_rejects_invalid_shapes_and_covariance():
    from htt.departure.response_overlap import build_response_overlap_audit

    with pytest.raises(ValueError, match="same length"):
        build_response_overlap_audit(
            **_audit_kwargs(global_tilt_response=(0.0, 1.0, 0.0))
        )

    bad_covariance = np.array([[1.0, 0.0], [0.0, -0.1]])
    with pytest.raises(ValueError, match="positive semidefinite"):
        build_response_overlap_audit(**_audit_kwargs(covariance=bad_covariance))

    with pytest.raises(ValueError, match="square"):
        build_response_overlap_audit(**_audit_kwargs(covariance=(1.0, 2.0)))


def test_response_overlap_preserves_external_transfer_provenance():
    from htt.departure.response_overlap import build_response_overlap_audit

    metadata = _transfer_metadata("aniclass.response.overlap.v1")
    audit = build_response_overlap_audit(
        **_audit_kwargs(
            transfer_source="AniCLASS_external",
            transfer_spec_id="aniclass.response.overlap.v1",
            transfer_metadata=metadata,
        )
    )
    payload = audit.as_payload()
    payload_text = json.dumps(payload, sort_keys=True).lower()

    assert payload["transfer_source"] == "AniCLASS_external"
    assert payload["transfer_spec_id"] == "aniclass.response.overlap.v1"
    assert payload["transfer_metadata"]["transfer_id"] == "aniclass.response.overlap.v1"
    assert "external-transfer path" in payload_text
    assert ("native_" + "validated") not in payload_text
    assert ("native " + "solver result") not in payload_text


def test_response_overlap_rejects_inference_or_claim_drift_metadata():
    from htt.departure.response_overlap import build_response_overlap_audit

    for key in (
        "post" + "erior_odds",
        "evidence_weight",
        "family" + "_rank",
        "geo" + "metry_label",
    ):
        with pytest.raises(ValueError, match="reserved"):
            build_response_overlap_audit(
                **_audit_kwargs(artifact_metadata={key: "bad"})
            )


def test_response_overlap_package_exports():
    from htt.departure import ResponseOverlapAudit, build_response_overlap_audit
    from htt.departure.response_overlap import ResponseOverlapAudit as ModuleAudit

    assert ResponseOverlapAudit is ModuleAudit
    assert callable(build_response_overlap_audit)
