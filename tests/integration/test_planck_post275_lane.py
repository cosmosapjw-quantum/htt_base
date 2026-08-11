"""PR-290 Planck preactivation and synthetic-contract gates.

These tests never read observed Planck products.  They freeze the fail-closed
activation order, the external human-receipt boundary, and the numerical
contracts that may be exercised on explicitly synthetic rows.
"""

from __future__ import annotations

from fractions import Fraction
import hashlib
import hmac
import importlib.util
import json
import math
from pathlib import Path
import shutil
import stat
import sys
import types

import numpy as np
import pytest
import yaml

from common.data_identity import (
    AdmissionStatus,
    build_not_authorized_receipt,
    canonical_sha256 as identity_sha256,
    compute_source_locator_identity,
    evaluate_lane_identity,
    load_lane_registry,
)
from common.observed_lane_activation import (
    HUMAN_AUTHORIZATION_SCHEMA,
    REQUIRED_NONEXECUTION_SOURCE_PATHS,
    ObservedLaneActivationError,
    build_planck_activation_decision,
    build_planck_nonexecution_receipt,
    canonical_json_bytes,
)
from htt.obsstat.planck_post275_lane import (
    REQUIRED_MAP_PRODUCT_IDS,
    PlanckLaneContractError,
    biposh_feature_units,
    build_preactivation_capability_snapshot,
    observation_inclusive_max_scan,
    require_complete_component_operator_identities,
    require_common_operator_identity,
    validate_full_joint_covariance,
)
from htt.obsstat.biposh_smica import compute_biposh_from_alm
from htt.obsstat.boost_biposh_residual import ExactBoostOperator
from htt.obsstat.lowell_global_calibration import calibrate_max_scan


ROOT = Path(__file__).resolve().parents[2]
SPEC_REL = Path("docs/research_program/post_pr275/pr290_spec.yaml")
STATUS_REL = Path("docs/codex_handoff/pr_status.yaml")
IDENTITY_REL = Path("docs/generated/pr289_data_identity_v2_receipt.json")
REGISTRY_REL = Path(
    "docs/research_program/post_pr275/data_registry_v2/LANE_REGISTRY_V2.json"
)
PR287_TERMINAL_REL = Path(
    "docs/generated/pr287_fresh_blind_typed_replay_receipt.json"
)
PR288_TERMINAL_REL = Path("docs/generated/pr288_bayesian_semantics_receipt.json")
AUTH_REL = Path(
    "docs/research_program/post_pr275/data_runs/planck/"
    "H_PLANCK_EXECUTION_AUTHORIZATION.json"
)


def _copy_activation_inputs(tmp_path: Path) -> Path:
    identity = json.loads((ROOT / IDENTITY_REL).read_text(encoding="utf-8"))
    pr289_sources = tuple(Path(value) for value in identity["source_bindings"])
    for relative in (
        SPEC_REL,
        STATUS_REL,
        IDENTITY_REL,
        PR288_TERMINAL_REL,
        *pr289_sources,
    ):
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, destination)
    return tmp_path


def _activate_predecessors(root: Path) -> None:
    path = root / STATUS_REL
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    completed = payload.setdefault("completed", [])
    resolutions = payload.setdefault("execution_resolutions", {})
    terminals = {
        "PR-287": "PASS_FRESH_BLIND_TYPED_REPLAY",
        "PR-288": "PASS_BAYESIAN_SEMANTICS_REPAIR",
        "PR-289": "PASS_DATA_IDENTITY_V2_PREFLIGHT",
    }
    for index, pr_id in enumerate(("PR-202", "PR-287", "PR-288", "PR-289")):
        if pr_id not in completed:
            completed.append(pr_id)
        resolutions[pr_id] = {
            "resolution": "COMPLETED_SUCCESS",
            "candidate_sha": f"{index + 1:040x}",
            "success_dependency_satisfied": True,
            "observed_data_executed": False,
            "public_use": False,
        }
        if pr_id in terminals:
            resolutions[pr_id]["terminal"] = terminals[pr_id]
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    unsigned = {
        "schema": "HTT_PR287_FRESH_BLIND_TYPED_REPLAY_RECEIPT_V1",
        "terminal": terminals["PR-287"],
        "synthetic_only": True,
    }
    terminal = {
        **unsigned,
        "receipt_content_id": "sha256:"
        + hashlib.sha256(canonical_json_bytes(unsigned)).hexdigest(),
    }
    terminal_path = root / PR287_TERMINAL_REL
    terminal_path.parent.mkdir(parents=True, exist_ok=True)
    terminal_path.write_text(
        json.dumps(terminal, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _stub_source_bindings(decision=None) -> dict[str, str]:
    paths = set(REQUIRED_NONEXECUTION_SOURCE_PATHS)
    if decision is not None:
        for row in decision.dependency_snapshot:
            terminal = row.get("terminal_receipt")
            if isinstance(terminal, dict) and terminal.get("file_sha256") is not None:
                paths.add(terminal["path"])
    return {path: "sha256:" + "1" * 64 for path in paths}


def _stub_generation_identity() -> dict[str, str]:
    return {
        "source_commit_or_external_candidate_seal_id": "sha256:" + "2" * 64,
        "worktree_state": "source_hash_bound_dirty_or_committed",
        "exact_replay_environment": "repository_python_contract",
    }


def _planck_native_descriptor(root: Path) -> dict[str, object]:
    registry = load_lane_registry(root / REGISTRY_REL)
    lane = registry.lane("PLANCK")
    data_root = (root / "synthetic-planck-native-profile").resolve()
    data_root.mkdir(parents=True, exist_ok=True)
    components: list[dict[str, object]] = []
    bindings: list[dict[str, object]] = []
    for index, component_id in enumerate(lane.expected_component_sequence):
        relative = f"components/{index:04d}-{component_id}.bin"
        path = data_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = f"PLANCK:{component_id}:{index}\n".encode("ascii")
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
        bindings.append(
            {
                "component_id": component_id,
                "ordinal": 0,
                "relative_path": relative,
                "byte_size": len(raw),
                "content_sha256": "sha256:" + digest,
            }
        )
    evidence: dict[str, object] = {
        "schema": "common.data_identity_evidence.v2",
        "lane_id": "PLANCK",
        "product_id": lane.product_id,
        "source_locator_identity": "pending",
        "release_name": "Planck registered synthetic contract release",
        "release_version": "planck-v1",
        "release_identity": "docs:pr290/planck-native-profile-v1",
        "license_identity": "spdx:CC-BY-4.0",
        "license_status": "BOUND",
        "units_contract_id": "units:PLANCK:v1",
        "coordinate_frame_id": "frame:PLANCK:Galactic:v1",
        "sign_orientation_convention_id": "sign:PLANCK:v1",
        "directional_convention_id": "direction:PLANCK:v1",
        "harmonic_convention_id": "harmonic:PLANCK:v1",
        "mask_id": "mask:PLANCK:paired:v1",
        "selection_id": "selection:PLANCK:native:v1",
        "sky_support_id": "sky:PLANCK:same-sky:v1",
        "covariance_id": "covariance:PLANCK:joint:v1",
        "covariance_status": "REGISTERED",
        "null_ensemble_id": "null:PLANCK:FFP10:v1",
        "null_ensemble_status": "REGISTERED",
        "transfer_source": "none",
        "transfer_function_spec_id": "none",
        "transfer_provenance_status": "NOT_APPLICABLE",
        "sky_support_status": "REGISTERED",
    }

    def relationship(
        unsigned: dict[str, object], identity_field: str
    ) -> dict[str, object]:
        component_ids = {
            value
            for key, value in unsigned.items()
            if (key == "component_id" or key.endswith("_component_id"))
            and isinstance(value, str)
        }
        selected = [
            row for row in bindings if row["component_id"] in component_ids
        ]
        return {
            **unsigned,
            identity_field: identity_sha256(
                {
                    "relationship": unsigned,
                    "component_bindings": selected,
                }
            ),
        }

    pipelines = {}
    for name, prefix in (("SMICA", "smica"), ("COMMANDER", "commander")):
        pipelines[name] = relationship(
            {
                "pipeline": name,
                "map_component_id": f"{prefix}_map",
                "mask_component_id": f"{prefix}_mask",
                "beam_component_id": f"{prefix}_beam",
                "window_operator_component_id": f"{prefix}_window_operator",
                "covariance_component_id": f"{prefix}_covariance",
                "pixelization_component_id": "pixelization",
                "native_selection_component_id": "native_selection",
                "sky_support_id": evidence["sky_support_id"],
                "harmonic_convention_id": evidence["harmonic_convention_id"],
            },
            "pipeline_identity",
        )
    same_sky = relationship(
        {
            "smica_map_component_id": "smica_map",
            "commander_map_component_id": "commander_map",
            "sky_support_id": evidence["sky_support_id"],
            "pixelization_component_id": "pixelization",
        },
        "pair_id",
    )
    ffp10 = relationship(
        {
            "ensemble_kind": "FFP10",
            "inventory_component_id": "ffp10_null_inventory",
            "null_ensemble_id": evidence["null_ensemble_id"],
        },
        "null_identity",
    )
    unsigned_profile = {
        "schema": lane.native_identity_schema,
        "lane_id": "PLANCK",
        "product_id": lane.product_id,
        "component_bindings": bindings,
        "pipelines": pipelines,
        "same_sky_pair": same_sky,
        "ffp10_null": ffp10,
    }
    evidence["native_identity_profile"] = {
        **unsigned_profile,
        "profile_id": identity_sha256(unsigned_profile),
    }
    evidence["source_locator_identity"] = compute_source_locator_identity(
        lane_id="PLANCK",
        product_id=lane.product_id,
        components=components,
        evidence_bindings=evidence,
    )
    evidence_path = data_root / "identity/evidence.json"
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(
        json.dumps(evidence, sort_keys=True) + "\n", encoding="utf-8"
    )
    return {
        "root": str(data_root),
        "evidence_relative_path": "identity/evidence.json",
        "evidence_sha256": hashlib.sha256(evidence_path.read_bytes()).hexdigest(),
        "components": components,
        "acquisition_status": "COMPLETE",
        "name_only": False,
    }


def _admit_planck_identity(root: Path) -> tuple[str, tuple[str, ...]]:
    path = root / IDENTITY_REL
    payload = json.loads(path.read_text(encoding="utf-8"))
    registry = load_lane_registry(root / REGISTRY_REL)
    lane = registry.lane("PLANCK")
    decision = evaluate_lane_identity(
        registry=registry,
        lane_id="PLANCK",
        descriptor=_planck_native_descriptor(root),
        inspected_at_utc="2026-08-09T00:00:00+00:00",
    )
    assert decision.status is AdmissionStatus.ADMITTED_IDENTITY_ONLY
    assert tuple(record.component_id for record in decision.records) == (
        lane.expected_component_sequence
    )
    decision_payload = decision.as_payload()
    authorization_payload = build_not_authorized_receipt(
        lane, decision
    ).as_payload()
    for index, row in enumerate(payload["lane_decisions"]):
        if row["lane_id"] == "PLANCK":
            payload["lane_decisions"][index] = decision_payload
    for row in payload["lane_and_product_identities"]:
        if row["lane_id"] == "PLANCK":
            row.update(
                {
                    "status": "ADMITTED_IDENTITY_ONLY",
                    "lane_admission_bundle_id": decision.lane_admission_bundle_id,
                    "native_identity_profile_id": (
                        decision.records[0].native_identity_profile_id
                    ),
                }
            )
    for index, row in enumerate(payload["authorization_receipts"]):
        if row["lane_id"] == "PLANCK":
            payload["authorization_receipts"][index] = authorization_payload
    payload["aggregate_status"] = "PARTIAL_LANE_ADMISSION"
    payload.pop("receipt_content_id", None)
    payload["receipt_content_id"] = "sha256:" + hashlib.sha256(
        canonical_json_bytes(payload)
    ).hexdigest()
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return (
        str(decision.lane_admission_bundle_id),
        tuple(record.record_id for record in decision.records),
    )


def _resign_planck_receipt(payload: dict[str, object]) -> None:
    decision = next(
        row
        for row in payload["lane_decisions"]
        if row["lane_id"] == "PLANCK"
    )
    records = decision["records"]
    for record in records:
        stable = dict(record)
        for key in ("record_id", "inspection_receipt_id", "inspected_at_utc"):
            stable.pop(key)
        record["record_id"] = identity_sha256(stable)
        inspection = dict(record)
        inspection.pop("inspection_receipt_id")
        record["inspection_receipt_id"] = identity_sha256(inspection)
    bundle = identity_sha256(
        {
            "lane_id": decision["lane_id"],
            "product_id": decision["product_id"],
            "component_inventory_id": records[0]["component_inventory_id"],
            "record_ids": [record["record_id"] for record in records],
        }
    )
    decision["lane_admission_bundle_id"] = bundle
    profile_id = records[0]["native_identity_profile_id"]
    lane_identity = next(
        row
        for row in payload["lane_and_product_identities"]
        if row["lane_id"] == "PLANCK"
    )
    lane_identity["lane_admission_bundle_id"] = bundle
    lane_identity["native_identity_profile_id"] = profile_id
    authorization = next(
        row
        for row in payload["authorization_receipts"]
        if row["lane_id"] == "PLANCK"
    )
    authorization["exact_admission_record_ids"] = [
        record["record_id"] for record in records
    ]
    authorization["lane_admission_bundle_id"] = bundle
    authorization.pop("authorization_id", None)
    authorization["authorization_id"] = identity_sha256(authorization)
    payload.pop("receipt_content_id", None)
    payload["receipt_content_id"] = "sha256:" + hashlib.sha256(
        canonical_json_bytes(payload)
    ).hexdigest()


def _configure_test_authority(root: Path, key: bytes) -> None:
    path = root / SPEC_REL
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["human_execution_gate"]["trusted_hmac_key_sha256"] = hashlib.sha256(
        key
    ).hexdigest()
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _write_authorization(
    root: Path,
    *,
    key: bytes,
    bundle: str,
    record_ids: tuple[str, ...],
    gate_id: str = "H-PLANCK",
    issued: str = "2026-08-09T00:00:00+00:00",
    expires: str = "2026-08-09T00:20:00+00:00",
) -> None:
    unsigned = {
        "schema": HUMAN_AUTHORIZATION_SCHEMA,
        "status": "AUTHORIZED",
        "lane_id": "PLANCK",
        "gate_id": gate_id,
        "analysis_plan_id": "plan:PR290-PLANCK-LOWELL-V1",
        "authorized_scope": "admitted_planck_observed_execution",
        "lane_admission_bundle_id": bundle,
        "exact_admission_record_ids": list(record_ids),
        "human_authority_identity": "owner:external-human",
        "authority_key_id": "H-PLANCK-OWNER-HMAC-V1",
        "issued_at_utc": issued,
        "expires_at_utc": expires,
        "nonce": "test-only-nonce-0001",
        "authorization_domain": "lane_data_execution",
    }
    payload = {
        **unsigned,
        "authorization_hmac_sha256": hmac.new(
            key, canonical_json_bytes(unsigned), hashlib.sha256
        ).hexdigest(),
    }
    path = root / AUTH_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    status_path = root / STATUS_REL
    status_payload = yaml.safe_load(status_path.read_text(encoding="utf-8"))
    status_payload["external_events"]["H-PLANCK"]["status"] = "AUTHORIZED"
    status_path.write_text(
        yaml.safe_dump(status_payload, sort_keys=False), encoding="utf-8"
    )


def test_live_preactivation_stops_at_predecessor_without_numeric_writes() -> None:
    observed_dir = ROOT / "docs/research_program/post_pr275/data_runs/planck/results"
    before = observed_dir.exists()
    decision = build_planck_activation_decision(repository_root=ROOT)
    assert decision.terminal == "BLOCKED_PREDECESSOR_FINAL_SUCCESS"
    assert decision.observed_data_executed is False
    assert decision.numeric_outputs_written == ()
    assert decision.network_or_download_side_effect is False
    assert observed_dir.exists() is before


def test_activation_precedence_separates_dependency_admission_and_human_gate(
    tmp_path: Path,
) -> None:
    root = _copy_activation_inputs(tmp_path)
    _activate_predecessors(root)
    decision = build_planck_activation_decision(repository_root=root)
    assert decision.terminal == "BLOCKED_DATA_IDENTITY_ADMISSION"

    bundle, records = _admit_planck_identity(root)
    decision = build_planck_activation_decision(repository_root=root)
    assert decision.terminal == "BLOCKED_HUMAN_EXECUTION_AUTHORIZATION"
    assert decision.data_identity_snapshot["lane_admission_bundle_id"] == bundle
    assert tuple(decision.data_identity_snapshot["record_ids"]) == records
    assert decision.data_identity_snapshot["record_count"] == 13
    assert tuple(decision.data_identity_snapshot["component_ids"]) == (
        load_lane_registry(root / REGISTRY_REL)
        .lane("PLANCK")
        .expected_component_sequence
    )
    assert decision.data_identity_snapshot["canonical_record_replay"] is True


def test_record_id_only_planck_admission_is_rejected(tmp_path: Path) -> None:
    root = _copy_activation_inputs(tmp_path)
    _activate_predecessors(root)
    path = root / IDENTITY_REL
    payload = json.loads(path.read_text(encoding="utf-8"))
    decision = next(
        row
        for row in payload["lane_decisions"]
        if row["lane_id"] == "PLANCK"
    )
    record_ids = ["sha256:" + str(index) * 64 for index in range(1, 5)]
    decision.update(
        {
            "status": "ADMITTED_IDENTITY_ONLY",
            "reasons": [],
            "records": [{"record_id": value} for value in record_ids],
            "lane_admission_bundle_id": "sha256:" + "a" * 64,
        }
    )
    authorization = next(
        row
        for row in payload["authorization_receipts"]
        if row["lane_id"] == "PLANCK"
    )
    authorization["exact_admission_record_ids"] = record_ids
    authorization["lane_admission_bundle_id"] = decision[
        "lane_admission_bundle_id"
    ]
    payload.pop("receipt_content_id", None)
    payload["receipt_content_id"] = "sha256:" + hashlib.sha256(
        canonical_json_bytes(payload)
    ).hexdigest()
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    observed = build_planck_activation_decision(repository_root=root)
    assert observed.terminal == "BLOCKED_DATA_IDENTITY_ADMISSION"
    assert "canonical native-record replay failed" in observed.reasons[0]


def test_recomputed_record_ids_cannot_hide_incomplete_native_profile(
    tmp_path: Path,
) -> None:
    root = _copy_activation_inputs(tmp_path)
    _activate_predecessors(root)
    _admit_planck_identity(root)
    path = root / IDENTITY_REL
    payload = json.loads(path.read_text(encoding="utf-8"))
    decision = next(
        row
        for row in payload["lane_decisions"]
        if row["lane_id"] == "PLANCK"
    )
    for record in decision["records"]:
        profile = dict(record["native_identity_profile"])
        profile.pop("profile_id")
        profile.pop("ffp10_null")
        profile["profile_id"] = identity_sha256(profile)
        record["native_identity_profile"] = profile
        record["native_identity_profile_id"] = profile["profile_id"]
    _resign_planck_receipt(payload)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    observed = build_planck_activation_decision(repository_root=root)
    assert observed.terminal == "BLOCKED_DATA_IDENTITY_ADMISSION"
    assert "canonical native-record replay failed" in observed.reasons[0]


def test_runner_ignores_preloaded_common_and_identity_modules(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_activation = types.ModuleType("common.observed_lane_activation")
    fake_identity = types.ModuleType("common.data_identity")

    def fail_if_called(*args, **kwargs):
        raise AssertionError("preloaded module executed")

    fake_activation.build_planck_activation_decision = fail_if_called
    fake_activation.build_planck_nonexecution_receipt = fail_if_called
    fake_identity.replay_lane_admission_decision = fail_if_called
    monkeypatch.setitem(
        sys.modules, "common.observed_lane_activation", fake_activation
    )
    monkeypatch.setitem(sys.modules, "common.data_identity", fake_identity)
    runner_path = ROOT / "scripts/codex_harness/run_pr290_planck_lane.py"
    runner_spec = importlib.util.spec_from_file_location(
        "_pr290_hostile_runner", runner_path
    )
    assert runner_spec is not None and runner_spec.loader is not None
    runner = importlib.util.module_from_spec(runner_spec)
    runner_spec.loader.exec_module(runner)
    receipt = runner._build(ROOT)
    assert receipt["terminal"] == "BLOCKED_PREDECESSOR_FINAL_SUCCESS"


@pytest.mark.parametrize("mutation", ["status_terminal", "receipt_terminal"])
def test_required_predecessor_terminals_are_replayed_not_copied(
    tmp_path: Path, mutation: str
) -> None:
    root = _copy_activation_inputs(tmp_path)
    _activate_predecessors(root)
    if mutation == "status_terminal":
        path = root / STATUS_REL
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        payload["execution_resolutions"]["PR-287"]["terminal"] = (
            "SUBSTITUTED_WRONG_TERMINAL"
        )
        path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    else:
        path = root / PR287_TERMINAL_REL
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["terminal"] = "SUBSTITUTED_WRONG_TERMINAL"
        payload.pop("receipt_content_id")
        payload["receipt_content_id"] = "sha256:" + hashlib.sha256(
            canonical_json_bytes(payload)
        ).hexdigest()
        path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    decision = build_planck_activation_decision(repository_root=root)
    assert decision.terminal == "BLOCKED_PREDECESSOR_FINAL_SUCCESS"
    assert any("terminal" in reason for reason in decision.reasons)


def test_external_human_authorization_is_hmac_bound_and_still_cannot_run_operator(
    tmp_path: Path,
) -> None:
    root = _copy_activation_inputs(tmp_path / "repo")
    _activate_predecessors(root)
    bundle, records = _admit_planck_identity(root)
    key = b"pr290 external test authority key"
    _configure_test_authority(root, key)
    key_path = tmp_path / "external-authority.key"
    key_path.write_bytes(key)
    _write_authorization(root, key=key, bundle=bundle, record_ids=records)

    decision = build_planck_activation_decision(
        repository_root=root,
        authority_key_path=key_path,
        evaluated_at_utc="2026-08-09T00:10:00+00:00",
    )
    assert decision.terminal == "BLOCKED_OPERATOR_IMPLEMENTATION"
    assert decision.human_gate_snapshot["status"] == "AUTHORIZED_VERIFIED"
    assert decision.observed_data_executed is False


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("wrong_gate", "gate"),
        ("stale", "expired"),
        ("forged", "HMAC"),
    ],
)
def test_human_authorization_mutations_fail_closed(
    tmp_path: Path, mutation: str, message: str
) -> None:
    root = _copy_activation_inputs(tmp_path / "repo")
    _activate_predecessors(root)
    bundle, records = _admit_planck_identity(root)
    key = b"pr290 external test authority key"
    _configure_test_authority(root, key)
    key_path = tmp_path / "external-authority.key"
    key_path.write_bytes(key)
    _write_authorization(
        root,
        key=key,
        bundle=bundle,
        record_ids=records,
        gate_id="H-CF4" if mutation == "wrong_gate" else "H-PLANCK",
        expires=(
            "2026-08-09T00:05:00+00:00"
            if mutation == "stale"
            else "2026-08-09T00:20:00+00:00"
        ),
    )
    if mutation == "forged":
        path = root / AUTH_REL
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["authorization_hmac_sha256"] = "0" * 64
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    decision = build_planck_activation_decision(
        repository_root=root,
        authority_key_path=key_path,
        evaluated_at_utc="2026-08-09T00:10:00+00:00",
    )
    assert decision.terminal == "BLOCKED_HUMAN_EXECUTION_AUTHORIZATION"
    assert any(message.lower() in reason.lower() for reason in decision.reasons)


def test_nonexecution_receipt_is_self_bound_and_claim_safe() -> None:
    decision = build_planck_activation_decision(repository_root=ROOT)
    receipt = build_planck_nonexecution_receipt(
        decision=decision,
        source_bindings=_stub_source_bindings(decision),
        generation_identity=_stub_generation_identity(),
    )
    unsigned = dict(receipt)
    content_id = unsigned.pop("receipt_content_sha256")
    assert content_id == "sha256:" + hashlib.sha256(
        canonical_json_bytes(unsigned)
    ).hexdigest()
    assert receipt["numeric_outputs_written"] == []
    assert receipt["observed_data_executed"] is False
    assert receipt["public_use"] is False
    assert receipt["family_identification_gate"] == "BLOCKED_PRE_NATIVE_ATLAS"


def test_activation_decision_rejects_post_factory_mutation() -> None:
    decision = build_planck_activation_decision(repository_root=ROOT)
    decision.data_identity_snapshot["satisfied"] = True
    with pytest.raises(ObservedLaneActivationError, match="identity drifted"):
        build_planck_nonexecution_receipt(
            decision=decision,
            source_bindings=_stub_source_bindings(decision),
            generation_identity=_stub_generation_identity(),
        )


def test_claim_promotion_spec_mutations_fail_before_dependency_evaluation(
    tmp_path: Path,
) -> None:
    root = _copy_activation_inputs(tmp_path)
    path = root / SPEC_REL
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["scientific_boundary"]["claim_level"]["level"] = "C6"
    payload["scientific_boundary"]["scientific_artifact_mode"] = "public_claim"
    payload["allowed_uses"].append("public manuscript scientific use")
    payload["forbidden_uses"] = []
    payload["artifact_ownership"][
        "observable_features_morphology_axes_and_null_features"
    ] = "MIO"
    future = payload["output_contract"]["future_observed_result_contract"]
    future["current_status"] = "ENABLED"
    future["required_metadata"].remove("artifact_owner")
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    decision = build_planck_activation_decision(repository_root=root)
    assert decision.terminal == "BLOCKED_CONTRACT_INVALID"
    assert "scientific boundary" in decision.reasons[0]


@pytest.mark.parametrize(
    "mutation",
    (
        "allow_observed_output",
        "clear_forbidden_outputs",
        "clear_synthetic_ceiling",
        "drop_commander",
        "drop_local_boost_status",
        "drop_global_tilt_status",
        "different_observation_null_pipeline",
    ),
)
def test_r2_structured_output_and_pipeline_mutations_fail_closed(
    tmp_path: Path, mutation: str
) -> None:
    root = _copy_activation_inputs(tmp_path / mutation)
    path = root / SPEC_REL
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    pipeline = payload["pipeline_contract"]
    output = payload["output_contract"]
    if mutation == "allow_observed_output":
        output["current_allowed_outputs"].append("observed_p_value")
    elif mutation == "clear_forbidden_outputs":
        output["current_forbidden_outputs"] = []
    elif mutation == "clear_synthetic_ceiling":
        pipeline["synthetic_contract_fixture"]["cannot_support"] = []
    elif mutation == "drop_commander":
        pipeline["observation_products"] = ["SMICA"]
    elif mutation == "drop_local_boost_status":
        del pipeline["response_and_active_estimand_status"]["local_boost"]
    elif mutation == "drop_global_tilt_status":
        del pipeline["response_and_active_estimand_status"]["global_tilt"]
    else:
        pipeline["identical_observation_null_pipeline"] = False
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    decision = build_planck_activation_decision(repository_root=root)
    assert decision.terminal == "BLOCKED_CONTRACT_INVALID"


@pytest.mark.parametrize(
    "mutation",
    (
        "registry_content_id",
        "registry_source_binding",
        "nonregistry_source_binding",
        "missing_source_binding",
    ),
)
def test_pr289_admission_replays_canonical_registry_and_sources(
    tmp_path: Path, mutation: str
) -> None:
    root = _copy_activation_inputs(tmp_path / mutation)
    _activate_predecessors(root)
    _admit_planck_identity(root)
    path = root / IDENTITY_REL
    payload = json.loads(path.read_text(encoding="utf-8"))
    registry_path = (
        "docs/research_program/post_pr275/data_registry_v2/"
        "LANE_REGISTRY_V2.json"
    )
    if mutation == "registry_content_id":
        payload["registry_content_id"] = "sha256:" + "f" * 64
    elif mutation == "registry_source_binding":
        payload["source_bindings"][registry_path] = "sha256:" + "e" * 64
    elif mutation == "nonregistry_source_binding":
        key = "htt/src/common/data_identity.py"
        payload["source_bindings"][key] = "sha256:" + "d" * 64
    else:
        payload["source_bindings"].pop("htt/src/common/data_identity.py")
    payload.pop("receipt_content_id", None)
    payload["receipt_content_id"] = "sha256:" + hashlib.sha256(
        canonical_json_bytes(payload)
    ).hexdigest()
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    decision = build_planck_activation_decision(repository_root=root)
    assert decision.terminal == "BLOCKED_CONTRACT_INVALID"
    assert any(
        token in decision.reasons[0]
        for token in ("registry", "source binding")
    )


@pytest.mark.parametrize("channel", ["source_key", "generation_key"])
def test_nonexecution_builder_rejects_claim_channel_injection(channel: str) -> None:
    decision = build_planck_activation_decision(repository_root=ROOT)
    bindings = _stub_source_bindings(decision)
    generation = _stub_generation_identity()
    if channel == "source_key":
        bindings.pop(next(iter(bindings)))
        bindings["Bianchi " + "geometry detected"] = "sha256:" + "3" * 64
    else:
        generation["Bianchi " + "family identified"] = "yes"
    with pytest.raises(
        ObservedLaneActivationError,
        match="source binding inventory|generation identity field inventory",
    ):
        build_planck_nonexecution_receipt(
            decision=decision,
            source_bindings=bindings,
            generation_identity=generation,
        )


def test_observation_inclusive_global_rank_closes_exact_counterexample() -> None:
    rows = np.array(
        [
            [0.7124909382, -0.4582932305],
            [-0.0194839346, 1.6279099650],
            [0.5488777725, 1.4096506226],
        ]
    )
    ranks = [
        observation_inclusive_max_scan(rows, ("high", "high"), observation_index=i)
        .global_p
        for i in range(3)
    ]
    legacy = [
        Fraction(
            round(
                calibrate_max_scan(
                    rows[i], np.delete(rows, i, axis=0), ["high", "high"]
                ).global_p
                * 3
            ),
            3,
        )
        for i in range(3)
    ]
    assert legacy == [Fraction(1, 3), Fraction(1, 3), Fraction(1)]
    assert ranks == [Fraction(2, 3), Fraction(2, 3), Fraction(1)]
    assert sum(rank <= Fraction(1, 3) for rank in ranks) == 0


def test_observation_inclusive_global_rank_is_permutation_equivariant() -> None:
    rows = np.array(
        [[0.3, -1.0], [1.2, 0.1], [-0.4, 2.0], [0.8, -0.3]], dtype=float
    )
    original = observation_inclusive_max_scan(
        rows, ("two-sided", "high"), observation_index=2
    )
    permutation = np.array([2, 0, 3, 1])
    permuted = observation_inclusive_max_scan(
        rows[permutation], ("two-sided", "high"), observation_index=0
    )
    assert permuted.global_p == original.global_p
    assert permuted.observation_max_score == original.observation_max_score


@pytest.mark.parametrize(
    "bad_rows",
    [np.array([[1.0, math.nan], [2.0, 3.0]]), np.array([[1.0, 2.0]])],
)
def test_global_rank_rejects_nonfinite_or_singleton_rows(bad_rows: np.ndarray) -> None:
    with pytest.raises(PlanckLaneContractError):
        observation_inclusive_max_scan(bad_rows, ("high", "high"))


def test_common_operator_identity_and_full_covariance_fail_closed() -> None:
    identity = {
        "pipeline_id": "planck:operator:v1",
        "map_product_id": REQUIRED_MAP_PRODUCT_IDS["SMICA"],
        "beam_id": "beam:target:v1",
        "pixel_window_id": "pixel:nside64:v1",
        "mask_id": "mask:common:v1",
        "mask_deconvolution_id": "coupling-inverse:v1",
        "harmonic_convention_id": "harmonic:cs:v1",
        "estimator_family_id": "estimator:lowell:v1",
        "feature_order_id": "features:planck:v1",
        "covariance_id": "cov:paired:v1",
        "null_ensemble_id": "ffp10:matched:v1",
        "look_elsewhere_family_id": "scan:registered:v1",
        "response_id": "response:boost-only:v1",
        "units_id": "units:microK_CMB:v1",
    }
    require_common_operator_identity(identity, dict(identity))
    drifted = dict(identity)
    drifted["mask_id"] = "mask:different"
    with pytest.raises(PlanckLaneContractError, match="identical"):
        require_common_operator_identity(identity, drifted)

    commander = dict(identity)
    commander["map_product_id"] = REQUIRED_MAP_PRODUCT_IDS["Commander"]
    complete = require_complete_component_operator_identities(
        {"SMICA": identity, "Commander": commander},
        {"SMICA": dict(identity), "Commander": dict(commander)},
    )
    assert tuple(complete) == ("SMICA", "Commander")
    with pytest.raises(PlanckLaneContractError, match="component inventory"):
        require_complete_component_operator_identities(
            {"SMICA": identity}, {"SMICA": dict(identity)}
        )
    collapsed = dict(identity)
    collapsed["map_product_id"] = "planck:smica-or-commander:v1"
    with pytest.raises(PlanckLaneContractError, match="map-product identity"):
        require_complete_component_operator_identities(
            {"SMICA": collapsed, "Commander": dict(collapsed)},
            {"SMICA": dict(collapsed), "Commander": dict(collapsed)},
        )

    accepted = validate_full_joint_covariance(
        np.array([[2.0, 0.4], [0.4, 1.0]]), ("C2", "A22")
    )
    assert accepted["rank"] == 2
    assert accepted["off_diagonal_present"] is True
    with pytest.raises(PlanckLaneContractError, match="diagonal"):
        validate_full_joint_covariance(np.eye(2), ("C2", "A22"))
    with pytest.raises(PlanckLaneContractError, match="positive definite"):
        validate_full_joint_covariance(
            np.array([[1.0, 2.0], [2.0, 1.0]]), ("C2", "A22")
        )


def test_biposh_units_and_scale_laws_are_quadratic_and_quartic() -> None:
    import healpy as hp

    alm = np.zeros(hp.Alm.getsize(2), dtype=np.complex128)
    alm[hp.Alm.getidx(2, 2, 0)] = 1.0
    alm[hp.Alm.getidx(2, 2, 1)] = 0.2 + 0.1j
    first = compute_biposh_from_alm(alm, 2, L_values=(2,))
    scaled = compute_biposh_from_alm(3.0 * alm, 2, L_values=(2,))
    assert scaled.power_by_L[2] / first.power_by_L[2] == pytest.approx(81.0)
    first_norm = np.linalg.norm([coefficient.value for coefficient in first.coefficients])
    scaled_norm = np.linalg.norm([coefficient.value for coefficient in scaled.coefficients])
    assert scaled_norm / first_norm == pytest.approx(9.0)
    units = biposh_feature_units("microK_CMB")
    assert units == {
        "alm": "microK_CMB",
        "cl": "microK_CMB^2",
        "biposh_A": "microK_CMB^2",
        "biposh_D": "microK_CMB^4",
        "s_one_half": "microK_CMB^4",
        "power_tensor": "dimensionless",
        "parity_ratio": "dimensionless",
        "axis_score": "dimensionless",
    }
    spec = yaml.safe_load((ROOT / SPEC_REL).read_text(encoding="utf-8"))
    frozen = spec["pipeline_contract"]["harmonic_and_unit_contract"]
    assert frozen["cl_units"] == units["cl"]
    assert frozen["biposh_A_units"] == units["biposh_A"]
    assert frozen["biposh_D_units"] == units["biposh_D"]
    assert frozen["s_one_half_units"] == units["s_one_half"]


def test_preactivation_snapshot_keeps_unimplemented_science_typed() -> None:
    snapshot = build_preactivation_capability_snapshot()
    assert snapshot["mask_deconvolution"] == "BLOCKED_UNDECONVOLVED"
    assert snapshot["multipole_vectors"] == "BLOCKED_EXTRACTOR_UNAVAILABLE"
    assert snapshot["global_response"] == "BLOCKED_UNBOUND_GLOBAL_RESPONSE"
    assert snapshot["local_boost"] == "synthetic_operator_contract_only"
    assert snapshot["global_tilt"] == "BLOCKED_UNBOUND_GLOBAL_RESPONSE"
    assert snapshot["local_global_rank"] == "NOT_MEASURED"
    assert snapshot["Q"] == "BLOCKED_NO_DEPARTURE_BUNDLE_BUDGET"
    assert snapshot["F"] == "BLOCKED_NO_SIGN_CLEAN_XC_AND_CEILING"
    assert snapshot["Pi"] == "BLOCKED_NO_Q_OR_F_MEASURE"
    assert snapshot["G_F"] == "NOT_APPLICABLE_NO_DEPTH_AXIS"
    assert snapshot["family_identification_gate"] == "BLOCKED_PRE_NATIVE_ATLAS"
    assert all(not isinstance(value, (int, float)) for value in snapshot.values())


def test_exact_boost_zero_is_finite_identity_and_domain_is_checked() -> None:
    import healpy as hp

    operator = ExactBoostOperator(nside=1, lmax=1, beta=0.0)
    theta, phi = hp.pix2ang(1, np.arange(hp.nside2npix(1)))
    assert np.all(np.isfinite(operator.doppler))
    assert np.all(operator.doppler == 1.0)
    assert np.allclose(operator._theta_ab, theta)
    assert np.allclose(operator._phi_ab, phi)
    for invalid in (math.nan, math.inf, 1.0, -1.0):
        with pytest.raises(ValueError, match="beta"):
            ExactBoostOperator(nside=1, lmax=1, beta=invalid)


def _load_runner_module():
    path = ROOT / "scripts/codex_harness/run_pr290_planck_lane.py"
    spec = importlib.util.spec_from_file_location("run_pr290_planck_lane", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_output_preflight_rejects_hardlink_before_payload_generation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runner = _load_runner_module()
    root = _copy_activation_inputs(tmp_path / "repo")
    output = root / (
        "docs/research_program/post_pr275/data_runs/planck/"
        "PR290_NONEXECUTION_RECEIPT.json"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    outside = tmp_path / "outside.json"
    outside.write_text("preserve\n", encoding="utf-8")
    output.hardlink_to(outside)
    called = False

    def forbidden_build(*_args, **_kwargs):
        nonlocal called
        called = True
        raise AssertionError("payload builder ran before destination preflight")

    monkeypatch.setattr(runner, "_build", forbidden_build)
    before = outside.read_bytes()
    assert runner._write(root=root, output=output) == 1
    assert called is False
    assert outside.read_bytes() == before


def test_result_directory_creation_during_payload_build_blocks_receipt_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runner = _load_runner_module()
    root = tmp_path / "repo"
    output = root / (
        "docs/research_program/post_pr275/data_runs/planck/"
        "PR290_NONEXECUTION_RECEIPT.json"
    )
    output.parent.mkdir(parents=True)
    observed = root / "docs/research_program/post_pr275/data_runs/planck/results"

    def racing_build(*_args, **_kwargs):
        observed.mkdir()
        return {
            "terminal": "BLOCKED_PREDECESSOR_FINAL_SUCCESS",
            "numeric_outputs_written": [],
            "observed_data_executed": False,
        }

    monkeypatch.setattr(runner, "_build", racing_build)
    assert runner._write(root=root, output=output) == 1
    assert observed.is_dir()
    assert not output.exists()


def test_output_preflight_rejects_symlink_parent_and_existing_result_directory(
    tmp_path: Path,
) -> None:
    runner = _load_runner_module()
    root = tmp_path / "repo"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    aliased_parent = root / "docs"
    aliased_parent.symlink_to(outside, target_is_directory=True)
    output = aliased_parent / "PR290_NONEXECUTION_RECEIPT.json"
    with pytest.raises(RuntimeError, match="parent"):
        runner._validate_output_destinations(
            root=root,
            output=output,
            observed_result_directory=root / "results",
            require_existing=False,
        )

    clean_root = tmp_path / "clean-repo"
    output = clean_root / "receipts/nonexecution.json"
    output.parent.mkdir(parents=True)
    result_directory = clean_root / "results"
    result_directory.mkdir()
    with pytest.raises(RuntimeError, match="result directory"):
        runner._validate_output_destinations(
            root=clean_root,
            output=output,
            observed_result_directory=result_directory,
            require_existing=False,
        )


def test_atomic_write_rejects_rebound_output_parent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runner = _load_runner_module()
    root = tmp_path / "repo"
    output = root / "receipts/nonexecution.json"
    output.parent.mkdir(parents=True)
    observed = root / "results"
    displaced_parent = tmp_path / "displaced-receipts"
    real_replace = runner.os.replace
    rebound = False

    def rebind_then_replace(*args, **kwargs):
        nonlocal rebound
        if not rebound:
            output.parent.rename(displaced_parent)
            output.parent.mkdir(parents=True)
            rebound = True
        return real_replace(*args, **kwargs)

    monkeypatch.setattr(runner.os, "replace", rebind_then_replace)
    with pytest.raises(RuntimeError, match="parent|commit"):
        runner._atomic_write(
            output,
            b"{}\n",
            root=root,
            observed_result_directory=observed,
        )
    assert not output.exists()
    assert not (displaced_parent / output.name).exists()


def test_atomic_write_rechecks_results_after_directory_fsync(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runner = _load_runner_module()
    root = tmp_path / "repo"
    output = root / "receipts/nonexecution.json"
    output.parent.mkdir(parents=True)
    observed = root / "results"
    real_fsync = runner.os.fsync
    injected = False

    def fsync_then_create_results(file_descriptor: int) -> None:
        nonlocal injected
        real_fsync(file_descriptor)
        mode = runner.os.fstat(file_descriptor).st_mode
        if stat.S_ISDIR(mode) and not injected:
            observed.mkdir()
            injected = True

    monkeypatch.setattr(runner.os, "fsync", fsync_then_create_results)
    with pytest.raises(RuntimeError, match="result directory"):
        runner._atomic_write(
            output,
            b"{}\n",
            root=root,
            observed_result_directory=observed,
        )
    assert observed.is_dir()
    assert not output.exists()
