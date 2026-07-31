"""PR-274 repository-bound data-admission contracts."""

from __future__ import annotations

import copy
import hashlib
import inspect
import json
from pathlib import Path
import subprocess
import sys

import pytest
import yaml

from common.vector_tensor_data_admission import (
    AdmissionVerdict,
    DataAdmissionError,
    IdentityStatus,
    NO_ADMITTED_DATA_PILOT,
    PilotAuthorizationStatus,
    VectorTensorDataCandidate,
    build_data_admission_report,
    candidate_from_mapping,
    candidates_from_registry,
    canonical_sha256,
    evaluate_data_candidate,
)
from htt.infer.vector_tensor_data_admission import (
    future_pilot_candidate_ids,
    require_future_pilot_eligibility,
)


ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "docs/research_program/vector_tensor/pr274_spec.yaml"
POLICY = ROOT / "docs/research_program/vector_tensor/pr274_publication_policy.json"
BACKLOG = ROOT / "docs/codex_handoff/pr_backlog.yaml"
STATUS = ROOT / "docs/codex_handoff/pr_status.yaml"
REGISTRY = (
    ROOT
    / "docs/research_program/vector_tensor/data_admission/"
    "PR274_CANDIDATE_INPUTS.yaml"
)
RESULT = (
    ROOT
    / "docs/research_program/vector_tensor/data_admission/"
    "PR274_ADMISSION_RESULT.json"
)
BUILDER = ROOT / "scripts/codex_harness/build_pr274_data_admission.py"
EXACT_IDS = (
    "PLANCK_PR3_FFP10_SMICA_COMPACT_REFERENCE",
    "CF4_QUERY_BATCH_COMPACT_REFERENCE",
    "DESI_DR1_PR151_PARTIAL_BACKGROUND",
    "PLANCK_NAME_ONLY_CONTROL",
    "HSC_NAME_ONLY_CONTROL",
    "KIDS_NAME_ONLY_CONTROL",
)


def _yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _registry():
    return _yaml(REGISTRY)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _bound_candidate_payload(repository_root: Path) -> dict[str, object]:
    component_dir = repository_root / "inputs"
    component_dir.mkdir(parents=True, exist_ok=True)
    payloads = {
        "data": b"data-bytes-v1\n",
        "mask": b"mask-bytes-v1\n",
        "covariance": b"covariance-bytes-v1\n",
    }
    components: dict[str, dict[str, str]] = {}
    for role, raw in payloads.items():
        path = component_dir / f"{role}.bin"
        path.write_bytes(raw)
        components[role] = {
            "path": path.relative_to(repository_root).as_posix(),
            "sha256": f"sha256:{hashlib.sha256(raw).hexdigest()}",
            "binding_status": "BOUND",
        }
    required = [
        "observer_feature",
        "mask_support",
        "covariance",
        "transfer_provenance",
    ]
    return {
        "candidate_id": "TEST_REPOSITORY_BOUND_INPUT",
        "product_name": "Internal test product",
        "artifact_mode": "observed_candidate",
        "source_identity": "repository:test-product-v1",
        "source_identity_status": "BOUND",
        "release_version": "test-release-v1",
        "release_status": "BOUND",
        "license_identity": "repository:test-license-v1",
        "license_status": "BOUND",
        "acquisition_status": "COMPLETE",
        "background_pr": "NONE",
        "sky_support_status": "BOUND",
        "transfer_provenance": "none_observer_side",
        "required_fields": required,
        "available_fields": list(required),
        "components": components,
    }


def _single_candidate_registry(candidate: dict[str, object]) -> dict[str, object]:
    return {
        "schema": "htt.pr274.vector_tensor_data_candidates.v1",
        "registry_id": "PR274-CANDIDATE-INPUTS-V1",
        "frozen_on": "2026-07-30",
        "scope": "test-only admission contract",
        "observed_data_execution_authorized": False,
        "claim_ceiling": "diagnostic_only",
        "candidates": [candidate],
    }


def _source_evidence() -> dict[str, str]:
    return {"test/source": f"sha256:{'0' * 64}"}


def test_pr274_spec_card_and_policy_keep_execution_separate() -> None:
    spec = _yaml(SPEC)
    policy = _json(POLICY)
    backlog = _yaml(BACKLOG)
    card = next(row for row in backlog["prs"] if row["id"] == "PR-274")

    assert spec["dependencies"] == card["depends"] == ["PR-273"]
    assert spec["owner"] == card["owner"] == "OBSSTAT"
    assert spec["claim_ceiling"] == policy["claim_ceiling"] == "diagnostic_only"
    assert spec["separate_data_execution_authorization_present"] is False
    assert spec["pilot_execution_in_this_change_set"] == "forbidden"
    assert card["scientific_artifact_mode"] == "data_admission_preflight"
    assert policy["ordinary_agent_push_forbidden"] is True
    assert policy["family_identification_gate"] == "BLOCKED_PRE_NATIVE_ATLAS"


def test_frozen_inputs_match_bytes_and_live_pr151_semantics() -> None:
    spec = _yaml(SPEC)
    for label, record in spec["frozen_inputs"].items():
        path = ROOT / record["path"]
        if "sha256" in record:
            assert _sha(path) == record["sha256"], label
        else:
            assert record["identity_mode"] == "live_semantic"
    status = _yaml(STATUS)
    assert "PR-151" in status["background_in_progress"]
    assert status["background_execution_contracts"]["PR-151"] == {
        "kind": "acquisition",
        "allowed_phase": "acquire",
        "partial_scientific_use": "forbidden",
    }
    assert status["execution_resolutions"]["PR-273"][
        "success_dependency_satisfied"
    ] is True


def test_registry_has_exact_closed_membership_and_no_execution_authority() -> None:
    raw = _registry()
    candidates = candidates_from_registry(raw)
    assert tuple(value.candidate_id for value in candidates) == EXACT_IDS
    assert raw["observed_data_execution_authorized"] is False
    assert raw["claim_ceiling"] == "diagnostic_only"
    for candidate in candidates:
        assert tuple(value.role for value in candidate.components) == (
            "data",
            "mask",
            "covariance",
        )


def test_registry_refuses_unknown_fields_duplicate_ids_and_bad_enums() -> None:
    unknown = copy.deepcopy(_registry())
    unknown["candidates"][0]["surprise"] = True
    with pytest.raises(DataAdmissionError, match="fields drifted"):
        candidates_from_registry(unknown)

    duplicate = copy.deepcopy(_registry())
    duplicate["candidates"][1]["candidate_id"] = duplicate["candidates"][0][
        "candidate_id"
    ]
    with pytest.raises(DataAdmissionError, match="must be unique"):
        candidates_from_registry(duplicate)

    bad_enum = copy.deepcopy(_registry())
    bad_enum["candidates"][0]["source_identity_status"] = "TRUST_ME"
    with pytest.raises(DataAdmissionError, match="unsupported value"):
        candidates_from_registry(bad_enum)


def test_candidate_factory_and_content_seal_are_fail_closed(
    tmp_path: Path,
) -> None:
    with pytest.raises(DataAdmissionError, match="factory-built"):
        VectorTensorDataCandidate(
            candidate_id="direct",
            product_name="direct",
            artifact_mode="observed_candidate",
            source_identity="direct",
            source_identity_status=IdentityStatus.BOUND,
            release_version="direct",
            release_status=IdentityStatus.BOUND,
            license_identity="direct",
            license_status=IdentityStatus.BOUND,
            acquisition_status="COMPLETE",
            background_pr="NONE",
            sky_support_status="BOUND",
            transfer_provenance="none_observer_side",
            required_fields=("field",),
            available_fields=("field",),
            components=(),
        )
    candidate = candidate_from_mapping(_bound_candidate_payload(tmp_path))
    assert candidate.content_id.startswith("sha256:")
    object.__setattr__(candidate, "source_identity", "mutated")
    with pytest.raises(DataAdmissionError, match="identity drifted"):
        candidate.as_payload()


@pytest.mark.smoke
def test_frozen_registry_closes_as_no_admitted_data_pilot() -> None:
    payload = _json(RESULT)
    assert payload["status"] == NO_ADMITTED_DATA_PILOT
    assert payload["candidate_count"] == 6
    assert payload["admitted_count"] == 0
    assert payload["admitted_candidate_ids"] == []
    assert payload["pilot_executed"] is False
    assert payload["separate_execution_authorization_present"] is False
    assert all(row["verdict"] == "REJECTED" for row in payload["decisions"])
    assert payload["content_id"] == canonical_sha256(
        {key: value for key, value in payload.items() if key != "content_id"}
    )


def test_planck_and_cf4_references_do_not_count_as_repository_binding() -> None:
    decisions = {row["candidate_id"]: row for row in _json(RESULT)["decisions"]}
    planck = decisions["PLANCK_PR3_FFP10_SMICA_COMPACT_REFERENCE"]
    cf4 = decisions["CF4_QUERY_BATCH_COMPACT_REFERENCE"]
    assert "source_identity_not_bound" in planck["blockers"]
    assert "license_identity_not_bound" in planck["blockers"]
    assert "data_component_not_bound" in planck["blockers"]
    assert "covariance_component_not_bound" in planck["blockers"]
    assert "source_identity_not_bound" in cf4["blockers"]
    assert "release_version_not_bound" in cf4["blockers"]
    assert "mask_component_not_bound" in cf4["blockers"]
    assert "covariance_component_not_bound" in cf4["blockers"]


def test_pr151_partial_background_input_is_explicitly_rejected() -> None:
    decisions = {row["candidate_id"]: row for row in _json(RESULT)["decisions"]}
    row = decisions["DESI_DR1_PR151_PARTIAL_BACKGROUND"]
    assert "observed_candidate_artifact_mode_required" in row["blockers"]
    assert "partial_or_incomplete_acquisition_forbidden" in row["blockers"]
    assert "pr151_partial_scientific_use_forbidden" in row["blockers"]
    assert row["pilot_authorization_status"] == "NOT_ELIGIBLE"
    assert _json(RESULT)["pr151_status"] == "background_in_progress"
    assert _json(RESULT)["pr151_partial_scientific_use"] == "forbidden"


@pytest.mark.parametrize(
    "candidate_id",
    (
        "PLANCK_NAME_ONLY_CONTROL",
        "HSC_NAME_ONLY_CONTROL",
        "KIDS_NAME_ONLY_CONTROL",
    ),
)
def test_dataset_name_alone_is_never_source_identity(candidate_id: str) -> None:
    decisions = {row["candidate_id"]: row for row in _json(RESULT)["decisions"]}
    blockers = decisions[candidate_id]["blockers"]
    assert "source_identity_not_bound" in blockers
    assert "dataset_name_is_not_source_identity" in blockers
    assert "partial_or_incomplete_acquisition_forbidden" in blockers


def test_complete_repository_binding_is_only_admitted_for_later_authorization(
    tmp_path: Path,
) -> None:
    candidate = candidate_from_mapping(_bound_candidate_payload(tmp_path))
    decision = evaluate_data_candidate(
        candidate,
        repository_root=tmp_path,
        separate_execution_authorization=False,
    )
    assert decision.verdict == AdmissionVerdict.ADMITTED
    assert decision.blockers == ()
    assert decision.pilot_authorization_status == (
        PilotAuthorizationStatus.AWAITING_SEPARATE_AUTHORIZATION
    )
    assert tuple(role for role, _ in decision.verified_component_sha256) == (
        "data",
        "mask",
        "covariance",
    )

    report = build_data_admission_report(
        report_id="TEST-REPORT",
        registry_payload=_single_candidate_registry(
            _bound_candidate_payload(tmp_path)
        ),
        repository_root=tmp_path,
        source_evidence=_source_evidence(),
        pr151_status="background_in_progress",
        pr151_partial_scientific_use="forbidden",
        separate_execution_authorization_present=False,
    )
    assert future_pilot_candidate_ids(report) == (
        "TEST_REPOSITORY_BOUND_INPUT",
    )
    with pytest.raises(
        DataAdmissionError,
        match="AWAITING_EXECUTION_AUTHORIZATION",
    ):
        require_future_pilot_eligibility(report)
    assert report.pilot_executed is False


def test_separate_authorization_never_changes_pilot_executed_flag(
    tmp_path: Path,
) -> None:
    report = build_data_admission_report(
        report_id="TEST-AUTHORIZED-NOT-EXECUTED",
        registry_payload=_single_candidate_registry(
            _bound_candidate_payload(tmp_path)
        ),
        repository_root=tmp_path,
        source_evidence=_source_evidence(),
        pr151_status="background_in_progress",
        pr151_partial_scientific_use="forbidden",
        separate_execution_authorization_present=True,
    )
    assert report.status == "ADMITTED_INPUTS_AUTHORIZED_NOT_EXECUTED"
    assert report.pilot_executed is False
    assert require_future_pilot_eligibility(report) == (
        "TEST_REPOSITORY_BOUND_INPUT",
    )


@pytest.mark.parametrize(
    ("mutation", "expected_blocker"),
    (
        ("hash", "data_sha256_mismatch"),
        ("parent", "data_path_not_repository_relative"),
        ("absolute", "data_path_not_repository_relative"),
        ("missing_field", "required_field_missing:observer_feature"),
        ("native_transfer", "pre_native_transfer_provenance_forbidden"),
    ),
)
def test_binding_and_semantic_mutations_fail_closed(
    tmp_path: Path,
    mutation: str,
    expected_blocker: str,
) -> None:
    payload = _bound_candidate_payload(tmp_path)
    if mutation == "hash":
        payload["components"]["data"]["sha256"] = f"sha256:{'f' * 64}"
    elif mutation == "parent":
        payload["components"]["data"]["path"] = "../outside.bin"
    elif mutation == "absolute":
        payload["components"]["data"]["path"] = "/tmp/outside.bin"
    elif mutation == "missing_field":
        payload["available_fields"].remove("observer_feature")
    elif mutation == "native_transfer":
        payload["transfer_provenance"] = "native_solver"
    candidate = candidate_from_mapping(payload)
    decision = evaluate_data_candidate(candidate, repository_root=tmp_path)
    assert decision.verdict == AdmissionVerdict.REJECTED
    assert expected_blocker in decision.blockers


def test_symlinked_component_or_parent_is_rejected(tmp_path: Path) -> None:
    payload = _bound_candidate_payload(tmp_path)
    target = tmp_path / "inputs" / "data.bin"
    link = tmp_path / "inputs" / "data-link.bin"
    link.symlink_to(target)
    payload["components"]["data"]["path"] = "inputs/data-link.bin"
    candidate = candidate_from_mapping(payload)
    decision = evaluate_data_candidate(candidate, repository_root=tmp_path)
    assert "data_path_symlink_forbidden" in decision.blockers

    real_dir = tmp_path / "real-components"
    real_dir.mkdir()
    nested = real_dir / "data.bin"
    nested.write_bytes(target.read_bytes())
    parent_link = tmp_path / "linked-components"
    parent_link.symlink_to(real_dir, target_is_directory=True)
    payload["components"]["data"]["path"] = "linked-components/data.bin"
    parent_candidate = candidate_from_mapping(payload)
    parent_decision = evaluate_data_candidate(
        parent_candidate,
        repository_root=tmp_path,
    )
    assert "data_path_symlink_forbidden" in parent_decision.blockers


def test_empty_admission_report_is_not_future_pilot_eligible() -> None:
    registry = _registry()
    report = build_data_admission_report(
        report_id="TEST-NO-ADMITTED-DATA",
        registry_payload=registry,
        repository_root=ROOT,
        source_evidence=_source_evidence(),
        pr151_status="background_in_progress",
        pr151_partial_scientific_use="forbidden",
    )
    assert future_pilot_candidate_ids(report) == ()
    with pytest.raises(DataAdmissionError, match=NO_ADMITTED_DATA_PILOT):
        require_future_pilot_eligibility(report)


def test_committed_result_is_deterministic_and_source_bound() -> None:
    completed = subprocess.run(
        [sys.executable, "-B", str(BUILDER), "--check"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    payload = _json(RESULT)
    source_evidence = payload["source_evidence"]
    assert source_evidence[
        "docs/codex_handoff/pr_status.yaml"
    ] == f"sha256:{_sha(STATUS)}"
    assert source_evidence[
        "docs/research_program/vector_tensor/data_admission/"
        "PR274_CANDIDATE_INPUTS.yaml"
    ] == f"sha256:{_sha(REGISTRY)}"


def test_owner_surfaces_expose_admission_not_observed_data_execution() -> None:
    import htt.infer.vector_tensor_data_admission as htt_surface
    import obsstat.vector_tensor_data_admission as obsstat_surface

    assert obsstat_surface.build_data_admission_report is (
        build_data_admission_report
    )
    assert tuple(htt_surface.__all__) == (
        "future_pilot_candidate_ids",
        "require_future_pilot_eligibility",
    )
    public_sources = (
        inspect.getsource(htt_surface),
        inspect.getsource(obsstat_surface),
    )
    assert all("def execute_" not in source for source in public_sources)
    assert _json(RESULT)["forbidden_use"][0] == "observed-data inference"
    assert "figures" not in _json(RESULT)
