"""PR-289 stable identity, refusal, and authorization separation contracts."""

from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path

import pytest
import yaml

from common.data_identity import (
    AdmissionStatus,
    AggregateStatus,
    AuthorizationStatus,
    DataIdentityError,
    build_data_identity_v2_receipt,
    compute_source_locator_identity,
    evaluate_lane_identity,
    load_lane_registry,
    registered_mutation_ids,
)


ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = (
    ROOT
    / "docs/research_program/post_pr275/data_registry_v2/"
    "LANE_REGISTRY_V2.json"
)
SPEC = ROOT / "docs/research_program/post_pr275/pr289_spec.yaml"
POLICY = ROOT / "docs/research_program/post_pr275/pr289_publication_policy.json"
BACKLOG = ROOT / "docs/codex_handoff/pr_backlog.yaml"
RUNBOOKS = ROOT / "docs/research_program/post_pr275/data_runbooks.yaml"
PR274_REGISTRY = (
    ROOT
    / "docs/research_program/vector_tensor/data_admission/"
    "PR274_DATA_IDENTITY_REGISTRY.yaml"
)
PR274_RESULT = (
    ROOT
    / "docs/research_program/vector_tensor/data_admission/"
    "PR274_ADMISSION_RESULT.json"
)
STAMP_A = "2026-08-09T00:00:00+00:00"
STAMP_B = "2026-08-09T00:01:00+00:00"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_bindings() -> dict[str, str]:
    return {
        str(path.relative_to(ROOT)): _sha(path)
        for path in (
            REGISTRY_PATH,
            SPEC,
            PR274_REGISTRY,
            PR274_RESULT,
        )
    }


def _base_evidence(lane_id: str, product_id: str) -> dict[str, object]:
    return {
        "schema": "common.data_identity_evidence.v2",
        "lane_id": lane_id,
        "product_id": product_id,
        "source_locator_identity": "pending",
        "release_name": f"{lane_id} registered release",
        "release_version": f"{lane_id.lower()}-v1",
        "release_identity": f"docs:pr289/{lane_id.lower()}-release-v1",
        "license_identity": "spdx:CC-BY-4.0",
        "license_status": "BOUND",
        "units_contract_id": f"units:{lane_id}:v1",
        "coordinate_frame_id": f"frame:{lane_id}:v1",
        "sign_orientation_convention_id": f"sign:{lane_id}:v1",
        "directional_convention_id": f"direction:{lane_id}:v1",
        "harmonic_convention_id": f"harmonic:{lane_id}:v1",
        "mask_id": f"mask:{lane_id}:v1",
        "selection_id": f"selection:{lane_id}:v1",
        "sky_support_id": f"sky:{lane_id}:v1",
        "covariance_id": f"covariance:{lane_id}:v1",
        "covariance_status": "REGISTERED",
        "null_ensemble_id": f"null:{lane_id}:v1",
        "null_ensemble_status": "REGISTERED",
        "transfer_source": "none",
        "transfer_function_spec_id": "none",
        "transfer_provenance_status": "NOT_APPLICABLE",
        "sky_support_status": "REGISTERED",
    }


def _valid_descriptor(
    root: Path,
    lane_id: str = "PLANCK",
    *,
    acquisition_status: str = "COMPLETE",
    name_only: bool = False,
) -> dict[str, object]:
    registry = load_lane_registry(REGISTRY_PATH)
    lane = registry.lane(lane_id)
    root.mkdir(parents=True, exist_ok=True)
    components: list[dict[str, object]] = []
    for index, component_id in enumerate(lane.expected_component_sequence):
        relative = f"components/{index:04d}-{component_id}.bin"
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = f"{lane_id}:{component_id}:{index}\n".encode("ascii")
        path.write_bytes(raw)
        components.append(
            {
                "component_id": component_id,
                "relative_path": relative,
                "byte_size": len(raw),
                "content_sha256": hashlib.sha256(raw).hexdigest(),
            }
        )
    evidence = _base_evidence(lane_id, lane.product_id)
    evidence["source_locator_identity"] = compute_source_locator_identity(
        lane_id=lane_id,
        product_id=lane.product_id,
        components=components,
        evidence_bindings=evidence,
    )
    evidence_path = root / "identity/evidence.json"
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(
        json.dumps(evidence, sort_keys=True) + "\n", encoding="utf-8"
    )
    return {
        "root": str(root),
        "evidence_relative_path": "identity/evidence.json",
        "evidence_sha256": _sha(evidence_path),
        "components": components,
        "acquisition_status": acquisition_status,
        "name_only": name_only,
    }


def _receipt(descriptors: dict[str, dict[str, object]]):
    return build_data_identity_v2_receipt(
        registry=load_lane_registry(REGISTRY_PATH),
        root_descriptors=descriptors,
        inspected_at_utc=STAMP_A,
        spec_path=SPEC,
        source_bindings=_source_bindings(),
        generation_identity={
            "source_commit_or_external_candidate_seal_id": "a" * 40,
            "worktree_state": "external_candidate_seal",
        },
    )


def test_registry_spec_policy_and_pr274_boundary_are_exact() -> None:
    registry = load_lane_registry(REGISTRY_PATH)
    spec = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    backlog = yaml.safe_load(BACKLOG.read_text(encoding="utf-8"))
    runbooks = yaml.safe_load(RUNBOOKS.read_text(encoding="utf-8"))
    card = next(row for row in backlog["prs"] if row["id"] == "PR-289")

    assert tuple(lane.lane_id for lane in registry.lanes) == (
        "PLANCK",
        "CF4",
        "HSC_KIDS",
        "ACT",
        "DESI",
        "JWST_SN",
    )
    assert registry.lane("HSC_KIDS").required_human_gate_id == "H-HSC-KiDS"
    assert next(
        row for row in runbooks["runbooks"] if row["lane"] == "HSC_KIDS"
    )["execution_authorization_gate"] == "H-HSC-KiDS"
    assert card["authorization_domain"] == "workflow_only"
    assert spec["historical_boundary"]["v1_registry_sha256"] == _sha(
        PR274_REGISTRY
    )
    assert spec["historical_boundary"]["v1_result_sha256"] == _sha(PR274_RESULT)
    assert policy["claim_ceiling"] == "diagnostic_only"
    assert policy["family_identification_gate"] == "BLOCKED_PRE_NATIVE_ATLAS"


def test_clean_checkout_no_roots_is_explicit_pass_with_zero_admissions() -> None:
    receipt = _receipt({})
    assert receipt.terminal == "PASS_DATA_IDENTITY_V2_PREFLIGHT"
    assert receipt.aggregate_status is AggregateStatus.NO_ADMITTED_IDENTITIES
    assert [row.status for row in receipt.lane_decisions] == [
        AdmissionStatus.REJECTED_NOT_PRESENT
    ] * 6
    assert all(not row.records for row in receipt.lane_decisions)
    assert all(
        row.status is AuthorizationStatus.NOT_AUTHORIZED
        and row.exact_admission_record_ids == ()
        and row.human_gate_receipt_id is None
        and row.human_authority_identity is None
        and row.authorized_scope is None
        and row.issued_at_utc is None
        and row.expires_at_utc is None
        for row in receipt.authorization_receipts
    )
    assert tuple(row.mutation_id for row in receipt.mutation_results) == (
        registered_mutation_ids(SPEC)
    )
    assert all(
        row.executed and row.activated and row.killed
        for row in receipt.mutation_results
    )
    payload = receipt.as_payload()
    assert payload["observed_data_executed"] is False
    assert payload["public_use"] is False
    assert payload["transfer_source"] == "none"
    assert payload["family_identification_gate"] == "BLOCKED_PRE_NATIVE_ATLAS"


def test_planck_admission_is_stable_across_root_and_inspection_time(
    tmp_path: Path,
) -> None:
    registry = load_lane_registry(REGISTRY_PATH)
    descriptor_a = _valid_descriptor(tmp_path / "root-a")
    descriptor_b = _valid_descriptor(tmp_path / "root-b")
    decision_a = evaluate_lane_identity(
        registry=registry,
        lane_id="PLANCK",
        descriptor=descriptor_a,
        inspected_at_utc=STAMP_A,
    )
    decision_b = evaluate_lane_identity(
        registry=registry,
        lane_id="PLANCK",
        descriptor=descriptor_b,
        inspected_at_utc=STAMP_B,
    )
    assert decision_a.status is AdmissionStatus.ADMITTED_IDENTITY_ONLY
    assert decision_b.status is AdmissionStatus.ADMITTED_IDENTITY_ONLY
    assert decision_a.lane_admission_bundle_id == decision_b.lane_admission_bundle_id
    assert [row.record_id for row in decision_a.records] == [
        row.record_id for row in decision_b.records
    ]
    assert [row.inspection_receipt_id for row in decision_a.records] != [
        row.inspection_receipt_id for row in decision_b.records
    ]
    assert all(
        descriptor_a["root"] not in json.dumps(row.as_payload())
        for row in decision_a.records
    )
    receipt = _receipt({"PLANCK": descriptor_a})
    assert receipt.aggregate_status is AggregateStatus.PARTIAL_LANE_ADMISSION
    planck_auth = receipt.authorization_receipts[0]
    assert planck_auth.status is AuthorizationStatus.NOT_AUTHORIZED
    assert planck_auth.exact_admission_record_ids
    assert planck_auth.human_gate_receipt_id is None


def test_records_and_authorizations_are_factory_only(tmp_path: Path) -> None:
    import common.data_identity as contracts

    receipt = _receipt({"PLANCK": _valid_descriptor(tmp_path / "planck")})
    record = receipt.lane_decisions[0].records[0]
    authorization = receipt.authorization_receipts[0]
    with pytest.raises(DataIdentityError, match="factory-built"):
        replace(record)
    with pytest.raises(DataIdentityError, match="factory-built"):
        replace(authorization)
    with pytest.raises(DataIdentityError, match="cannot construct authorization"):
        replace(
            authorization,
            status=AuthorizationStatus.AUTHORIZED,
            _construction_token=contracts._AUTH_TOKEN,
        )


@pytest.mark.parametrize(
    ("mutation", "expected"),
    (
        ("root_symlink", AdmissionStatus.BLOCKED_PATH_ESCAPE_OR_MUTATION),
        ("parent_symlink", AdmissionStatus.REJECTED_SYMLINK_OR_ALIAS),
        ("hardlink", AdmissionStatus.REJECTED_SYMLINK_OR_ALIAS),
        ("size", AdmissionStatus.REJECTED_IDENTITY_MISMATCH),
        ("hash", AdmissionStatus.REJECTED_IDENTITY_MISMATCH),
        ("missing_component", AdmissionStatus.REJECTED_INCOMPLETE_COMPONENT_SET),
        ("reordered", AdmissionStatus.REJECTED_INCOMPLETE_COMPONENT_SET),
    ),
)
def test_path_size_hash_and_inventory_attacks_fail_closed(
    tmp_path: Path, mutation: str, expected: AdmissionStatus
) -> None:
    registry = load_lane_registry(REGISTRY_PATH)
    root = tmp_path / "planck"
    descriptor = _valid_descriptor(root)
    if mutation == "root_symlink":
        alias = tmp_path / "alias"
        alias.symlink_to(root, target_is_directory=True)
        descriptor["root"] = str(alias)
    elif mutation == "parent_symlink":
        original = root / descriptor["components"][0]["relative_path"]
        outside = tmp_path / "outside"
        outside.mkdir()
        moved = outside / "component.bin"
        original.replace(moved)
        (root / "linked-parent").symlink_to(outside, target_is_directory=True)
        descriptor["components"][0]["relative_path"] = "linked-parent/component.bin"
    elif mutation == "hardlink":
        component = root / descriptor["components"][0]["relative_path"]
        (tmp_path / "outside-hardlink.bin").hardlink_to(component)
    elif mutation == "size":
        descriptor["components"][0]["byte_size"] += 1
    elif mutation == "hash":
        descriptor["components"][0]["content_sha256"] = "0" * 64
    elif mutation == "missing_component":
        descriptor["components"].pop()
    else:
        descriptor["components"].reverse()
    decision = evaluate_lane_identity(
        registry=registry,
        lane_id="PLANCK",
        descriptor=descriptor,
        inspected_at_utc=STAMP_A,
    )
    assert decision.status is expected
    assert not decision.records


@pytest.mark.parametrize("mutation", ("duplicate_key", "nonfinite", "placeholder"))
def test_typed_evidence_rejects_noncanonical_or_placeholder_provenance(
    tmp_path: Path, mutation: str
) -> None:
    registry = load_lane_registry(REGISTRY_PATH)
    root = tmp_path / "planck"
    descriptor = _valid_descriptor(root)
    evidence_path = root / descriptor["evidence_relative_path"]
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    if mutation == "duplicate_key":
        evidence_path.write_text(
            '{"schema":"common.data_identity_evidence.v2",'
            '"schema":"common.data_identity_evidence.v2"}\n',
            encoding="utf-8",
        )
    elif mutation == "nonfinite":
        evidence["covariance_id"] = float("nan")
        evidence_path.write_text(
            json.dumps(evidence, allow_nan=True) + "\n", encoding="utf-8"
        )
    else:
        evidence["release_version"] = "v"
        evidence_path.write_text(json.dumps(evidence) + "\n", encoding="utf-8")
    descriptor["evidence_sha256"] = _sha(evidence_path)
    decision = evaluate_lane_identity(
        registry=registry,
        lane_id="PLANCK",
        descriptor=descriptor,
        inspected_at_utc=STAMP_A,
    )
    assert decision.status in {
        AdmissionStatus.REJECTED_MISSING_RELEASE_OR_LICENSE,
        AdmissionStatus.REJECTED_MISSING_SEMANTIC_CONTRACT,
    }
    assert not decision.records


def test_desi_partial_precedes_name_only_and_missing_root(tmp_path: Path) -> None:
    registry = load_lane_registry(REGISTRY_PATH)
    descriptor = {
        "root": str(tmp_path / "missing"),
        "evidence_relative_path": "identity/evidence.json",
        "evidence_sha256": "0" * 64,
        "components": [],
        "acquisition_status": "PARTIAL_BACKGROUND",
        "name_only": True,
    }
    decision = evaluate_lane_identity(
        registry=registry,
        lane_id="DESI",
        descriptor=descriptor,
        inspected_at_utc=STAMP_A,
    )
    assert decision.status is AdmissionStatus.BLOCKED_PR151_INCOMPLETE
    assert any("PR-151" in reason for reason in decision.reasons)
    assert any("does not exist" in reason for reason in decision.reasons)


def test_hsc_kids_name_only_is_typed_refusal(tmp_path: Path) -> None:
    registry = load_lane_registry(REGISTRY_PATH)
    descriptor = _valid_descriptor(
        tmp_path / "hsc-kids", "HSC_KIDS", name_only=True
    )
    decision = evaluate_lane_identity(
        registry=registry,
        lane_id="HSC_KIDS",
        descriptor=descriptor,
        inspected_at_utc=STAMP_A,
    )
    assert decision.status is AdmissionStatus.REJECTED_NAME_ONLY
    assert not decision.records


def test_mutation_execution_cannot_be_omitted_or_hardcoded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import common.data_identity as contracts

    expected = registered_mutation_ids(SPEC)
    original = contracts._run_registered_mutations
    monkeypatch.setattr(
        contracts,
        "_run_registered_mutations",
        lambda mutation_ids, **kwargs: original(mutation_ids, **kwargs)[:-1],
    )
    with pytest.raises(DataIdentityError, match="omitted or reordered"):
        _receipt({})


def test_mutation_receipt_uses_the_live_rejection_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import common.data_identity as contracts

    registry = load_lane_registry(REGISTRY_PATH)
    admitted = evaluate_lane_identity(
        registry=registry,
        lane_id="PLANCK",
        descriptor=_valid_descriptor(tmp_path / "admitted"),
        inspected_at_utc=STAMP_A,
    )
    assert admitted.status is AdmissionStatus.ADMITTED_IDENTITY_ONLY
    monkeypatch.setattr(
        contracts,
        "evaluate_lane_identity",
        lambda **_kwargs: admitted,
    )
    results = contracts._run_registered_mutations(
        ("MU289-SIZE",),
        registry=registry,
        spec_path=SPEC,
        source_bindings=_source_bindings(),
    )
    assert results[0].executed is True
    assert results[0].activated is True
    assert results[0].killed is False
    with pytest.raises(DataIdentityError, match="did not fail closed"):
        contracts.validate_mutation_results(("MU289-SIZE",), results)


def test_regular_file_read_detects_mid_inspection_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import common.data_identity as contracts

    path = tmp_path / "mutable.bin"
    path.write_bytes(b"original")
    expected = path.lstat()
    real_fstat = contracts.os.fstat
    calls = 0

    def mutating_fstat(descriptor: int):
        nonlocal calls
        calls += 1
        if calls == 2:
            path.write_bytes(b"mutated-and-longer")
        return real_fstat(descriptor)

    monkeypatch.setattr(contracts.os, "fstat", mutating_fstat)
    with pytest.raises(DataIdentityError, match="changed during inspection"):
        contracts._read_regular_bytes(
            path, field_name="test component", expected_info=expected
        )


def test_unknown_lane_and_noncanonical_descriptor_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(DataIdentityError, match="unregistered root"):
        _receipt({"UNKNOWN": {}})
    registry = load_lane_registry(REGISTRY_PATH)
    decision = evaluate_lane_identity(
        registry=registry,
        lane_id="PLANCK",
        descriptor={"root": str(tmp_path)},
        inspected_at_utc=STAMP_A,
    )
    assert decision.status is AdmissionStatus.REJECTED_IDENTITY_MISMATCH
