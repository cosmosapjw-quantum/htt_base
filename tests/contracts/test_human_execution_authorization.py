from __future__ import annotations

import hashlib
import hmac
import json
from pathlib import Path

import pytest
import numpy as np

from common.data_identity import (
    _build_registered_native_profile,
    AdmissionStatus,
    canonical_sha256,
    compute_source_locator_identity,
    evaluate_lane_identity,
    load_lane_registry,
)
from common.human_execution_authorization import (
    AUTHORIZATION_DOMAIN,
    AUTHORIZATION_SCHEMA,
    HumanExecutionAuthorizationError,
    HumanExecutionAuthorizationReceiptV1,
    ValidatedHumanExecutionAuthorization,
    validate_human_execution_authorization,
)
from htt.infer.bayesian_production import (
    LaneReadinessStatus,
    ProductionBayesianError,
    assess_lane_readiness,
    build_posterior_consumer_plan,
    build_production_model_contract,
    build_sampler_posterior_lineage,
    load_observational_lane_descriptors,
)


ROOT = Path(__file__).resolve().parents[2]
REGISTRY = (
    ROOT
    / "docs/research_program/post_pr275/data_registry_v2/LANE_REGISTRY_V2.json"
)
COMMIT = "a" * 40
TREE = "b" * 40
EVALUATED = "2026-08-22T12:00:00Z"
KEY = b"test-only-external-authority-key"


def _canonical(payload: dict[str, object]) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _admitted_act(tmp_path: Path):
    registry = load_lane_registry(REGISTRY)
    lane = registry.lane("ACT")
    root = tmp_path / "act-input"
    root.mkdir()
    components: list[dict[str, object]] = []
    for ordinal, component_id in enumerate(lane.expected_component_sequence):
        relative = f"components/{ordinal:02d}-{component_id}.bin"
        path = root / relative
        path.parent.mkdir(exist_ok=True)
        raw = f"ACT:{component_id}:{ordinal}\n".encode("ascii")
        path.write_bytes(raw)
        digest = hashlib.sha256(raw).hexdigest()
        components.append(
            {
                "component_id": component_id,
                "relative_path": relative,
                "byte_size": len(raw),
                "content_sha256": digest,
            }
        )
    evidence: dict[str, object] = {
        "schema": "common.data_identity_evidence.v2",
        "lane_id": lane.lane_id,
        "product_id": lane.product_id,
        "source_locator_identity": "pending",
        "release_name": "ACT registered product",
        "release_version": "ACT-v1",
        "release_identity": "docs:pr304/act-release-v1",
        "license_identity": "spdx:CC-BY-4.0",
        "license_status": "BOUND",
        "units_contract_id": "units:ACT:v1",
        "coordinate_frame_id": "frame:ACT:v1",
        "sign_orientation_convention_id": "sign:ACT:v1",
        "directional_convention_id": "direction:ACT:v1",
        "harmonic_convention_id": "harmonic:ACT:v1",
        "mask_id": "mask:ACT:v1",
        "selection_id": "selection:ACT:v1",
        "sky_support_id": "sky:ACT:v1",
        "covariance_id": "covariance:ACT:v1",
        "covariance_status": "REGISTERED",
        "null_ensemble_id": "null:ACT:v1",
        "null_ensemble_status": "REGISTERED",
        "transfer_source": "none",
        "transfer_function_spec_id": "none",
        "transfer_provenance_status": "NOT_APPLICABLE",
        "sky_support_status": "REGISTERED",
        "native_identity_profile": {},
    }
    evidence["native_identity_profile"] = _build_registered_native_profile(
        lane, components, evidence
    )
    evidence["source_locator_identity"] = compute_source_locator_identity(
        lane_id=lane.lane_id,
        product_id=lane.product_id,
        components=components,
        evidence_bindings=evidence,
    )
    evidence_path = root / "identity/evidence.json"
    evidence_path.parent.mkdir()
    evidence_path.write_text(json.dumps(evidence, sort_keys=True) + "\n", encoding="utf-8")
    decision = evaluate_lane_identity(
        registry=registry,
        lane_id=lane.lane_id,
        descriptor={
            "root": str(root),
            "evidence_relative_path": "identity/evidence.json",
            "evidence_sha256": hashlib.sha256(evidence_path.read_bytes()).hexdigest(),
            "components": components,
            "acquisition_status": "COMPLETE",
            "name_only": False,
        },
        inspected_at_utc="2026-08-22T11:00:00Z",
    )
    assert decision.status is AdmissionStatus.ADMITTED_IDENTITY_ONLY
    return lane, decision


def _payload(lane, decision, *, key: bytes = KEY, **overrides: object) -> dict[str, object]:
    unsigned: dict[str, object] = {
        "schema": AUTHORIZATION_SCHEMA,
        "lane_id": lane.lane_id,
        "exact_admission_record_ids": [record.record_id for record in decision.records],
        "lane_admission_bundle_id": decision.lane_admission_bundle_id,
        "analysis_plan_id": lane.analysis_plan_id,
        "required_human_gate_id": lane.required_human_gate_id,
        "authorized_scope": "admitted_act_observed_execution",
        "authorization_domain": AUTHORIZATION_DOMAIN,
        "candidate_commit": COMMIT,
        "candidate_tree": TREE,
        "issued_at_utc": "2026-08-22T11:45:00Z",
        "expires_at_utc": "2026-08-22T12:15:00Z",
        "nonce": "test-nonce-0001",
        "authority_key_id": "sha256:" + hashlib.sha256(key).hexdigest(),
    }
    unsigned.update(overrides)
    unsigned["authorization_id"] = canonical_sha256(unsigned)
    signed = {"authorization_id": unsigned.pop("authorization_id"), **unsigned}
    return {
        **signed,
        "authorization_hmac_sha256": hmac.new(key, _canonical(signed), hashlib.sha256).hexdigest(),
    }


def _validate(payload: dict[str, object], lane, decision, key_path: Path):
    return validate_human_execution_authorization(
        receipt_payload=payload,
        lane_spec=lane,
        admission_decision=decision,
        expected_candidate_commit=COMMIT,
        expected_candidate_tree=TREE,
        evaluated_at_utc=EVALUATED,
        authority_key_path=key_path,
    )


def test_validates_complete_admission_without_consuming_nonce(tmp_path: Path) -> None:
    lane, decision = _admitted_act(tmp_path)
    key_path = tmp_path.parent / "external-authority.key"
    key_path.write_bytes(KEY)
    validated = _validate(_payload(lane, decision), lane, decision, key_path)
    assert isinstance(validated, ValidatedHumanExecutionAuthorization)
    assert validated.receipt.exact_admission_record_ids == tuple(
        record.record_id for record in decision.records
    )
    assert validated.replayed_admission_bundle_id == decision.lane_admission_bundle_id
    assert validated.validated_at_utc == EVALUATED
    assert "nonce" not in validated.as_payload()
    object.__setattr__(validated.receipt, "candidate_tree", "f" * 40)
    with pytest.raises(HumanExecutionAuthorizationError, match="object drifted"):
        validated.as_payload()


@pytest.mark.parametrize(
    ("mutation", "match"),
    (
        (lambda payload: payload.__setitem__("lane_id", "PLANCK"), "lane does not match"),
        (lambda payload: payload.__setitem__("exact_admission_record_ids", list(reversed(payload["exact_admission_record_ids"]))), "ordering or membership"),
        (lambda payload: payload.__setitem__("exact_admission_record_ids", payload["exact_admission_record_ids"][:-1]), "ordering or membership"),
        (lambda payload: payload.__setitem__("exact_admission_record_ids", [payload["exact_admission_record_ids"][0]] * 2), "unique"),
        (lambda payload: payload.__setitem__("lane_admission_bundle_id", "sha256:" + "0" * 64), "admission bundle"),
        (lambda payload: payload.__setitem__("analysis_plan_id", "plan:wrong"), "analysis plan"),
        (lambda payload: payload.__setitem__("required_human_gate_id", "H-WRONG"), "human gate"),
        (lambda payload: payload.__setitem__("authorized_scope", "unknown_scope"), "scope"),
        (lambda payload: payload.__setitem__("authorization_domain", "unknown_domain"), "domain"),
        (lambda payload: payload.__setitem__("candidate_commit", "c" * 40), "candidate commit or tree"),
        (lambda payload: payload.__setitem__("candidate_tree", "d" * 40), "candidate commit or tree"),
    ),
)
def test_rejects_re_signed_binding_drift(tmp_path: Path, mutation, match: str) -> None:
    lane, decision = _admitted_act(tmp_path)
    key_path = tmp_path.parent / "external-authority.key"
    key_path.write_bytes(KEY)
    payload = _payload(lane, decision)
    unsigned = {key: value for key, value in payload.items() if key not in {"authorization_id", "authorization_hmac_sha256"}}
    mutation(unsigned)
    payload = _payload(lane, decision, **unsigned)
    with pytest.raises(HumanExecutionAuthorizationError, match=match):
        _validate(payload, lane, decision, key_path)


@pytest.mark.parametrize(
    ("issued", "expires", "evaluated", "match"),
    (
        ("2026-08-22T12:01:00Z", "2026-08-22T12:10:00Z", EVALUATED, "future"),
        ("2026-08-22T11:29:00Z", "2026-08-22T11:59:00Z", EVALUATED, "expired"),
        ("2026-08-22T11:00:00Z", "2026-08-22T11:30:01Z", EVALUATED, "TTL"),
        (EVALUATED, EVALUATED, EVALUATED, "empty or reversed"),
    ),
)
def test_rejects_invalid_time_intervals(
    tmp_path: Path, issued: str, expires: str, evaluated: str, match: str
) -> None:
    lane, decision = _admitted_act(tmp_path)
    key_path = tmp_path.parent / "external-authority.key"
    key_path.write_bytes(KEY)
    payload = _payload(lane, decision, issued_at_utc=issued, expires_at_utc=expires)
    with pytest.raises(HumanExecutionAuthorizationError, match=match):
        validate_human_execution_authorization(
            receipt_payload=payload,
            lane_spec=lane,
            admission_decision=decision,
            expected_candidate_commit=COMMIT,
            expected_candidate_tree=TREE,
            evaluated_at_utc=evaluated,
            authority_key_path=key_path,
        )


def test_rejects_noncanonical_but_parseable_timestamp(tmp_path: Path) -> None:
    lane, decision = _admitted_act(tmp_path)
    key_path = tmp_path.parent / "external-authority.key"
    key_path.write_bytes(KEY)
    payload = _payload(
        lane,
        decision,
        issued_at_utc="2026-8-22T11:45:00Z",
    )
    with pytest.raises(HumanExecutionAuthorizationError, match="canonical UTC timestamp"):
        _validate(payload, lane, decision, key_path)


def test_rejects_forged_key_pr289_receipt_and_caller_capability(tmp_path: Path) -> None:
    lane, decision = _admitted_act(tmp_path)
    key_path = tmp_path.parent / "external-authority.key"
    key_path.write_bytes(KEY)
    forged = _payload(lane, decision)
    forged["authorization_hmac_sha256"] = "0" * 64
    with pytest.raises(HumanExecutionAuthorizationError, match="HMAC"):
        _validate(forged, lane, decision, key_path)

    unknown_key = _payload(lane, decision, authority_key_id="sha256:" + "f" * 64)
    with pytest.raises(HumanExecutionAuthorizationError, match="key id"):
        _validate(unknown_key, lane, decision, key_path)

    pr289 = __import__("common.data_identity", fromlist=["build_not_authorized_receipt"])
    pr289_receipt = pr289.build_not_authorized_receipt(lane, decision)
    with pytest.raises(HumanExecutionAuthorizationError, match="fields drifted"):
        _validate(pr289_receipt.as_payload(), lane, decision, key_path)

    receipt = HumanExecutionAuthorizationReceiptV1.from_payload(_payload(lane, decision))
    with pytest.raises(HumanExecutionAuthorizationError, match="validator-built"):
        ValidatedHumanExecutionAuthorization(
            receipt=receipt,
            replayed_lane_spec_content_id="sha256:" + "1" * 64,
            replayed_admission_bundle_id=decision.lane_admission_bundle_id,
            validated_at_utc=EVALUATED,
            validation_content_id="sha256:" + "2" * 64,
        )


def test_rejects_refused_admission_and_repository_key(tmp_path: Path) -> None:
    lane, admitted = _admitted_act(tmp_path)
    refused = evaluate_lane_identity(
        registry=load_lane_registry(REGISTRY),
        lane_id="ACT",
        descriptor=None,
        inspected_at_utc="2026-08-22T11:00:00Z",
    )
    assert refused.status is AdmissionStatus.REJECTED_NOT_PRESENT
    external_key = tmp_path.parent / "external-authority.key"
    external_key.write_bytes(KEY)
    with pytest.raises(HumanExecutionAuthorizationError, match="complete admitted"):
        _validate(_payload(lane, admitted), lane, refused, external_key)

    in_repository_key = ROOT / ".pr304-test-authority.key"
    with pytest.raises(HumanExecutionAuthorizationError, match="outside the repository"):
        _validate(_payload(lane, admitted), lane, admitted, in_repository_key)


def test_rejects_symlinked_external_authority_key(tmp_path: Path) -> None:
    lane, decision = _admitted_act(tmp_path)
    key_path = tmp_path.parent / "external-authority.key"
    key_path.write_bytes(KEY)
    symlink_path = tmp_path.parent / "external-authority-link.key"
    symlink_path.symlink_to(key_path)
    with pytest.raises(HumanExecutionAuthorizationError, match="one external regular file"):
        _validate(_payload(lane, decision), lane, decision, symlink_path)


def test_readiness_splits_authorization_sampler_start_and_posterior_consumers(
    tmp_path: Path,
) -> None:
    lane, decision = _admitted_act(tmp_path)
    descriptor = next(
        row
        for row in load_observational_lane_descriptors(
            ROOT / "docs/research_program/post_pr275/pr299_spec.yaml"
        )
        if row.lane_id == "H-ACT"
    )
    contract = build_production_model_contract(
        lane_id="H-ACT",
        model_id="act-contract-test",
        parameter_schema={"amplitude": {"support": "real", "role": "signal"}},
        likelihood_identity="sha256:" + "1" * 64,
        prior_identity="sha256:" + "2" * 64,
        data_identity="sha256:" + "3" * 64,
        covariance_identity="sha256:" + "4" * 64,
        block_ids=("ACT-a", "ACT-b"),
        response_rank=1,
        likelihood_normalized=True,
        prior_normalized=True,
        log_likelihood=lambda theta: -float(np.dot(theta, theta)),
        prior_transform=lambda unit: np.asarray(unit),
        replicate_generator=lambda theta, rng: np.asarray(theta) + rng.normal(size=len(theta)),
        discrepancies={"amplitude": lambda observed, replicated: float(np.sum(observed - replicated))},
    )
    assert assess_lane_readiness(descriptor, model_contract=contract).status is (
        LaneReadinessStatus.BLOCKED_DATA_ADMISSION_UNBOUND
    )
    assert assess_lane_readiness(
        descriptor, model_contract=contract, admission_decision=decision
    ).status is LaneReadinessStatus.BLOCKED_HUMAN_AUTHORIZATION

    key_path = tmp_path.parent / "external-authority.key"
    key_path.write_bytes(KEY)
    validated = _validate(_payload(lane, decision), lane, decision, key_path)
    ready = assess_lane_readiness(
        descriptor,
        model_contract=contract,
        admission_decision=decision,
        validated_human_authorization=validated,
    )
    assert ready.status is LaneReadinessStatus.READY_TO_START_SAMPLER
    assert ready.observed_data_executed is False

    lineage = build_sampler_posterior_lineage(
        contract=contract,
        samples=np.array([[0.0], [1.0], [2.0]]),
        normalized_weights=np.array([0.2, 0.3, 0.5]),
        sampler_settings={"nlive": 200, "dlogz": 0.1, "bound": "multi", "sample": "rwalk", "seed": 7},
        resampling_rule="systematic",
    )
    assert assess_lane_readiness(
        descriptor,
        model_contract=contract,
        admission_decision=decision,
        validated_human_authorization=validated,
        posterior_lineage=lineage,
    ).status is LaneReadinessStatus.BLOCKED_SAMPLER_TERMINAL
    consumer = build_posterior_consumer_plan(
        contract=contract,
        lineage=lineage,
        ppc_discrepancy_ids=("amplitude",),
        loo_block_ids=("ACT-a", "ACT-b"),
    )
    assert assess_lane_readiness(
        descriptor,
        model_contract=contract,
        admission_decision=decision,
        validated_human_authorization=validated,
        posterior_lineage=lineage,
        posterior_consumer_plan=consumer,
    ).status is LaneReadinessStatus.READY_FOR_POSTERIOR_CONSUMERS
    object.__setattr__(validated.receipt, "candidate_commit", "e" * 40)
    with pytest.raises(ProductionBayesianError, match="content identity drifted"):
        assess_lane_readiness(
            descriptor,
            model_contract=contract,
            admission_decision=decision,
            validated_human_authorization=validated,
        )
