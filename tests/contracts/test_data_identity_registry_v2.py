"""PR-289 stable identity, refusal, and authorization separation contracts."""

from __future__ import annotations

import contextlib
import copy
from dataclasses import replace
import hashlib
import importlib.abc
import importlib.machinery
from io import BytesIO, StringIO
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import types

import pytest
import yaml

from common.data_identity import (
    AdmissionStatus,
    AggregateStatus,
    AuthorizationStatus,
    DataIdentityError,
    build_data_identity_v2_receipt,
    canonical_sha256,
    compute_source_locator_identity,
    evaluate_lane_identity,
    load_lane_registry,
    replay_lane_admission_decision,
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
CLAIM_LEDGER = ROOT / "docs/harness/CLAIM_LEDGER.md"
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
MODULE = ROOT / "htt/src/common/data_identity.py"
RUNNER = ROOT / "scripts/codex_harness/run_pr289_data_identity_v2.py"
TEST_FILE = Path(__file__).resolve()
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
            POLICY,
            RUNBOOKS,
            CLAIM_LEDGER,
            PR274_REGISTRY,
            PR274_RESULT,
            MODULE,
            RUNNER,
            TEST_FILE,
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


def _signed(payload: dict[str, object]) -> dict[str, object]:
    return {**payload, "profile_id": canonical_sha256(payload)}


def _binding_rows(components: list[dict[str, object]]) -> list[dict[str, object]]:
    ordinals: dict[str, int] = {}
    rows = []
    for component in components:
        component_id = str(component["component_id"])
        ordinal = ordinals.get(component_id, 0)
        ordinals[component_id] = ordinal + 1
        rows.append(
            {
                "component_id": component_id,
                "ordinal": ordinal,
                "relative_path": component["relative_path"],
                "byte_size": component["byte_size"],
                "content_sha256": "sha256:"
                + str(component["content_sha256"]).removeprefix("sha256:"),
            }
        )
    return rows


def _with_identity(
    payload: dict[str, object],
    field: str,
    bindings: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    if bindings is None:
        identity = canonical_sha256(payload)
    else:
        component_ids = {
            value
            for key, value in payload.items()
            if (key == "component_id" or key.endswith("_component_id"))
            and isinstance(value, str)
        }
        selected = [
            row for row in bindings if row["component_id"] in component_ids
        ]
        identity = canonical_sha256(
            {"relationship": payload, "component_bindings": selected}
        )
    return {**payload, field: identity}


def _native_profile(
    lane_id: str,
    product_id: str,
    components: list[dict[str, object]],
    evidence: dict[str, object],
) -> dict[str, object]:
    registry = load_lane_registry(REGISTRY_PATH)
    lane = registry.lane(lane_id)
    common: dict[str, object] = {
        "schema": lane.native_identity_schema,
        "lane_id": lane_id,
        "product_id": product_id,
        "component_bindings": _binding_rows(components),
    }
    bindings = common["component_bindings"]
    if lane_id == "PLANCK":
        pipelines = {}
        for name, prefix in (("SMICA", "smica"), ("COMMANDER", "commander")):
            unsigned = {
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
            }
            pipelines[name] = _with_identity(
                unsigned, "pipeline_identity", bindings
            )
        pair = _with_identity(
            {
                "smica_map_component_id": "smica_map",
                "commander_map_component_id": "commander_map",
                "sky_support_id": evidence["sky_support_id"],
                "pixelization_component_id": "pixelization",
            },
            "pair_id",
            bindings,
        )
        ffp10 = _with_identity(
            {
                "ensemble_kind": "FFP10",
                "inventory_component_id": "ffp10_null_inventory",
                "null_ensemble_id": evidence["null_ensemble_id"],
            },
            "null_identity",
            bindings,
        )
        return _signed(
            {**common, "pipelines": pipelines, "same_sky_pair": pair, "ffp10_null": ffp10}
        )
    if lane_id == "CF4":
        catalogue = _with_identity(
            {
                "catalogue_component_id": "catalogue",
                "row_selection_component_id": "row_selection",
                "covariance_component_id": "covariance",
                "row_selection_id": evidence["selection_id"],
                "covariance_id": evidence["covariance_id"],
            },
            "catalogue_identity",
            bindings,
        )
        semantics = _with_identity(
            {
                "frame_component_id": "frame_definition",
                "sign_component_id": "sign_convention",
                "units_component_id": "units_contract",
                "grouping_component_id": "grouping_definition",
                "depth_component_id": "depth_definition",
                "zoa_component_id": "zoa_definition",
                "coordinate_frame_id": evidence["coordinate_frame_id"],
                "sign_orientation_convention_id": evidence[
                    "sign_orientation_convention_id"
                ],
                "units_contract_id": evidence["units_contract_id"],
            },
            "semantics_identity",
            bindings,
        )
        return _signed({**common, "catalogue": catalogue, "semantics": semantics})
    if lane_id == "HSC_KIDS":
        children = {}
        for survey, prefix, calibration in (
            ("HSC", "hsc", "hsc_shear_calibration"),
            ("KIDS", "kids", "kids_shear_response"),
        ):
            unsigned = {
                "survey_id": survey,
                "product_component_id": f"{prefix}_product",
                "mask_component_id": f"{prefix}_mask",
                "randoms_component_id": f"{prefix}_randoms",
                "psf_component_id": f"{prefix}_psf",
                "n_z_component_id": f"{prefix}_n_z",
                "calibration_or_response_component_id": calibration,
                "covariance_component_id": f"{prefix}_covariance",
            }
            children[survey] = _with_identity(
                unsigned, "child_identity_id", bindings
            )
        cross = _with_identity(
            {
                "component_id": "hsc_kids_cross_covariance",
                "hsc_child_identity_id": children["HSC"]["child_identity_id"],
                "kids_child_identity_id": children["KIDS"]["child_identity_id"],
                "covariance_id": evidence["covariance_id"],
            },
            "cross_covariance_identity",
            bindings,
        )
        return _signed({**common, "children": children, "cross_covariance": cross})
    return _signed(common)


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
    evidence["native_identity_profile"] = _native_profile(
        lane_id, lane.product_id, components, evidence
    )
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


def _rewrite_evidence(
    descriptor: dict[str, object],
    mutate,
) -> None:
    root = Path(str(descriptor["root"]))
    evidence_path = root / str(descriptor["evidence_relative_path"])
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    mutate(evidence)
    evidence["source_locator_identity"] = compute_source_locator_identity(
        lane_id=evidence["lane_id"],
        product_id=evidence["product_id"],
        components=descriptor["components"],
        evidence_bindings=evidence,
    )
    evidence_path.write_text(
        json.dumps(evidence, sort_keys=True) + "\n", encoding="utf-8"
    )
    descriptor["evidence_sha256"] = _sha(evidence_path)


def _resign_nested(
    profile: dict[str, object], row: dict[str, object], identity_field: str
) -> None:
    unsigned = dict(row)
    unsigned.pop(identity_field)
    row[identity_field] = _with_identity(
        unsigned,
        identity_field,
        profile["component_bindings"],
    )[identity_field]


def _resign_record(record: dict[str, object]) -> None:
    stable = dict(record)
    for key in ("record_id", "inspection_receipt_id", "inspected_at_utc"):
        stable.pop(key)
    record["record_id"] = canonical_sha256(stable)
    inspection = dict(record)
    inspection.pop("inspection_receipt_id")
    record["inspection_receipt_id"] = canonical_sha256(inspection)


def _resign_bundle(payload: dict[str, object]) -> None:
    records = payload["records"]
    assert isinstance(records, list) and records
    payload["lane_admission_bundle_id"] = canonical_sha256(
        {
            "lane_id": payload["lane_id"],
            "product_id": payload["product_id"],
            "component_inventory_id": records[0]["component_inventory_id"],
            "record_ids": [row["record_id"] for row in records],
        }
    )


def _receipt(descriptors: dict[str, dict[str, object]]):
    source_bindings = _source_bindings()
    normalized_bindings = {
        path: "sha256:" + digest.removeprefix("sha256:")
        for path, digest in source_bindings.items()
    }
    return build_data_identity_v2_receipt(
        registry=load_lane_registry(REGISTRY_PATH),
        root_descriptors=descriptors,
        inspected_at_utc=STAMP_A,
        spec_path=SPEC,
        source_bindings=source_bindings,
        generation_identity={
            "schema": "common.source_bound_generation_identity.v1",
            "git_commit_or_worktree_state": "BOUND_SOURCE_WORKTREE:"
            + canonical_sha256(normalized_bindings),
            "generating_procedure": [
                "python3",
                "-B",
                "scripts/codex_harness/run_pr289_data_identity_v2.py",
                "build",
            ],
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
    assert spec["historical_boundary"]["v1_replay_commit"] == (
        "ff9ef9f45747e559c5343b463cf010dfc3a7432a"
    )
    assert policy["claim_ceiling"] == "diagnostic_only"
    assert policy["family_identification_gate"] == "BLOCKED_PRE_NATIVE_ATLAS"
    assert {
        "planck_native_profile_and_same_sky_replay",
        "cf4_native_catalogue_selection_covariance_replay",
        "hsc_kids_separate_child_and_cross_covariance_replay",
        "native_profile_export_replay_and_string_only_refusal",
    } <= set(policy["required_review_cells"])
    assert "generic record-id or string-only native admission" in policy[
        "forbidden_inputs"
    ]
    runbook_by_lane = {row["lane"]: row for row in runbooks["runbooks"]}
    assert "SMICA and Commander" in runbook_by_lane["PLANCK"][
        "required_input_contract"
    ]
    assert "row selection" in runbook_by_lane["CF4"][
        "required_input_contract"
    ]
    assert "cross-covariance" in runbook_by_lane["HSC_KIDS"][
        "required_input_contract"
    ]


def test_native_lane_registry_roles_are_exact_and_survey_specific() -> None:
    registry = load_lane_registry(REGISTRY_PATH)
    assert registry.lane("PLANCK").required_component_ids == (
        "smica_map",
        "commander_map",
        "smica_mask",
        "commander_mask",
        "smica_beam",
        "commander_beam",
        "smica_window_operator",
        "commander_window_operator",
        "smica_covariance",
        "commander_covariance",
        "pixelization",
        "native_selection",
        "ffp10_null_inventory",
    )
    assert registry.lane("CF4").required_component_ids == (
        "catalogue",
        "row_selection",
        "covariance",
        "frame_definition",
        "sign_convention",
        "units_contract",
        "grouping_definition",
        "depth_definition",
        "zoa_definition",
    )
    hsc_kids = registry.lane("HSC_KIDS")
    assert {"hsc_psf", "kids_psf", "hsc_n_z", "kids_n_z"} <= set(
        hsc_kids.required_component_ids
    )
    assert {
        "hsc_shear_calibration",
        "kids_shear_response",
        "hsc_covariance",
        "kids_covariance",
        "hsc_kids_cross_covariance",
    } <= set(hsc_kids.required_component_ids)


@pytest.mark.parametrize("lane_id", ("PLANCK", "CF4", "HSC_KIDS"))
def test_complete_native_profiles_admit_and_replay_exactly(
    tmp_path: Path, lane_id: str
) -> None:
    registry = load_lane_registry(REGISTRY_PATH)
    decision = evaluate_lane_identity(
        registry=registry,
        lane_id=lane_id,
        descriptor=_valid_descriptor(tmp_path / lane_id.lower(), lane_id),
        inspected_at_utc=STAMP_A,
    )
    assert decision.status is AdmissionStatus.ADMITTED_IDENTITY_ONLY
    assert decision.records
    profile_ids = {row.native_identity_profile_id for row in decision.records}
    assert profile_ids == {
        decision.records[0].native_identity_profile["profile_id"]
    }
    replayed = replay_lane_admission_decision(
        decision.as_payload(), registry=registry
    )
    assert replayed.as_payload() == decision.as_payload()


def test_exported_record_component_ordinal_fails_closed(tmp_path: Path) -> None:
    registry = load_lane_registry(REGISTRY_PATH)
    decision = evaluate_lane_identity(
        registry=registry,
        lane_id="PLANCK",
        descriptor=_valid_descriptor(tmp_path / "planck", "PLANCK"),
        inspected_at_utc=STAMP_A,
    )
    payload = decision.as_payload()
    payload["records"][0]["component_ordinal"] = 1
    with pytest.raises(DataIdentityError, match="one native component role"):
        replay_lane_admission_decision(payload, registry=registry)


def test_exported_record_replay_revalidates_all_semantic_fields(
    tmp_path: Path,
) -> None:
    registry = load_lane_registry(REGISTRY_PATH)
    decision = evaluate_lane_identity(
        registry=registry,
        lane_id="PLANCK",
        descriptor=_valid_descriptor(tmp_path / "planck", "PLANCK"),
        inspected_at_utc=STAMP_A,
    )
    payload = decision.as_payload()
    payload["records"][0].update(
        {
            "source_locator_kind": "unregistered_locator_kind",
            "regular_file_status": "NOT_VERIFIED",
            "symlink_status": "ALIAS_PRESENT",
            "license_status": "UNBOUND",
            "units_contract_id": "",
            "coordinate_frame_id": "",
            "sign_orientation_convention_id": "",
            "directional_convention_id": "",
            "mask_id": "",
            "selection_id": "",
            "covariance_id": "",
            "covariance_status": "INVALID",
            "transfer_source": "native_bass",
            "transfer_function_spec_id": "unregistered-native-spec",
            "transfer_provenance_status": "NATIVE_VALIDATED",
            "sky_support_status": "INVALID",
        }
    )
    _resign_record(payload["records"][0])
    _resign_bundle(payload)
    with pytest.raises(DataIdentityError):
        replay_lane_admission_decision(payload, registry=registry)


def test_repeated_role_replay_requires_each_ordinal_once(tmp_path: Path) -> None:
    registry = load_lane_registry(REGISTRY_PATH)
    decision = evaluate_lane_identity(
        registry=registry,
        lane_id="DESI",
        descriptor=_valid_descriptor(tmp_path / "desi", "DESI"),
        inspected_at_utc=STAMP_A,
    )
    payload = decision.as_payload()
    positions = [
        index
        for index, record in enumerate(payload["records"])
        if record["component_id"] == "ezmock_inventory"
    ][:2]
    payload["records"][positions[0]] = copy.deepcopy(
        payload["records"][positions[1]]
    )
    _resign_bundle(payload)
    with pytest.raises(DataIdentityError, match="ordinal|inventory"):
        replay_lane_admission_decision(payload, registry=registry)


def test_generic_record_id_or_string_profile_cannot_admit_planck(
    tmp_path: Path,
) -> None:
    registry = load_lane_registry(REGISTRY_PATH)
    descriptor = _valid_descriptor(tmp_path / "planck")

    def mutate(evidence: dict[str, object]) -> None:
        evidence["native_identity_profile"] = {
            "schema": "common.planck_native_identity.v1",
            "record_ids": ["generic-record-id"],
        }

    _rewrite_evidence(descriptor, mutate)
    decision = evaluate_lane_identity(
        registry=registry,
        lane_id="PLANCK",
        descriptor=descriptor,
        inspected_at_utc=STAMP_A,
    )
    assert decision.status is AdmissionStatus.REJECTED_MISSING_SEMANTIC_CONTRACT
    assert not decision.records


@pytest.mark.parametrize(
    "mutation",
    ("pipeline_collapse", "different_sky", "missing_ffp10", "operator_alias"),
)
def test_planck_native_relationship_mutations_fail_closed(
    tmp_path: Path, mutation: str
) -> None:
    registry = load_lane_registry(REGISTRY_PATH)
    descriptor = _valid_descriptor(tmp_path / mutation)

    def mutate(evidence: dict[str, object]) -> None:
        profile = evidence["native_identity_profile"]
        if mutation == "pipeline_collapse":
            pipeline = profile["pipelines"]["COMMANDER"]
            pipeline["map_component_id"] = "smica_map"
            _resign_nested(profile, pipeline, "pipeline_identity")
        elif mutation == "different_sky":
            pair = profile["same_sky_pair"]
            pair["sky_support_id"] = "sky:other-release:v1"
            _resign_nested(profile, pair, "pair_id")
        elif mutation == "missing_ffp10":
            null = profile["ffp10_null"]
            null["inventory_component_id"] = "native_selection"
            _resign_nested(profile, null, "null_identity")
        else:
            pipeline = profile["pipelines"]["COMMANDER"]
            pipeline["window_operator_component_id"] = "smica_window_operator"
            _resign_nested(profile, pipeline, "pipeline_identity")
        unsigned_profile = dict(profile)
        unsigned_profile.pop("profile_id")
        profile["profile_id"] = canonical_sha256(unsigned_profile)

    _rewrite_evidence(descriptor, mutate)
    decision = evaluate_lane_identity(
        registry=registry,
        lane_id="PLANCK",
        descriptor=descriptor,
        inspected_at_utc=STAMP_A,
    )
    assert decision.status is AdmissionStatus.REJECTED_MISSING_SEMANTIC_CONTRACT
    assert not decision.records


@pytest.mark.parametrize("field", ("covariance_status", "sky_support_status"))
def test_planck_applicable_native_roles_reject_not_applicable_status(
    tmp_path: Path, field: str
) -> None:
    registry = load_lane_registry(REGISTRY_PATH)
    descriptor = _valid_descriptor(tmp_path / field, "PLANCK")
    _rewrite_evidence(
        descriptor,
        lambda evidence: evidence.__setitem__(field, "NOT_APPLICABLE"),
    )
    decision = evaluate_lane_identity(
        registry=registry,
        lane_id="PLANCK",
        descriptor=descriptor,
        inspected_at_utc=STAMP_A,
    )
    assert decision.status is AdmissionStatus.REJECTED_MISSING_SEMANTIC_CONTRACT
    assert not decision.records


@pytest.mark.parametrize(
    "field",
    ("catalogue_component_id", "row_selection_id", "covariance_id", "frame"),
)
def test_cf4_exact_catalogue_and_semantic_roles_fail_closed(
    tmp_path: Path, field: str
) -> None:
    registry = load_lane_registry(REGISTRY_PATH)
    descriptor = _valid_descriptor(tmp_path / field, "CF4")

    def mutate(evidence: dict[str, object]) -> None:
        profile = evidence["native_identity_profile"]
        if field == "frame":
            row = profile["semantics"]
            row["coordinate_frame_id"] = "frame:wrong:v1"
            identity_field = "semantics_identity"
        else:
            row = profile["catalogue"]
            row[field] = "row_selection" if field.endswith("component_id") else "wrong:v1"
            identity_field = "catalogue_identity"
        _resign_nested(profile, row, identity_field)
        unsigned_profile = dict(profile)
        unsigned_profile.pop("profile_id")
        profile["profile_id"] = canonical_sha256(unsigned_profile)

    _rewrite_evidence(descriptor, mutate)
    decision = evaluate_lane_identity(
        registry=registry,
        lane_id="CF4",
        descriptor=descriptor,
        inspected_at_utc=STAMP_A,
    )
    assert decision.status is AdmissionStatus.REJECTED_MISSING_SEMANTIC_CONTRACT
    assert not decision.records


@pytest.mark.parametrize("field", ("psf", "n_z", "calibration", "cross_covariance"))
def test_hsc_and_kids_child_identities_remain_separate(
    tmp_path: Path, field: str
) -> None:
    registry = load_lane_registry(REGISTRY_PATH)
    descriptor = _valid_descriptor(tmp_path / field, "HSC_KIDS")

    def mutate(evidence: dict[str, object]) -> None:
        profile = evidence["native_identity_profile"]
        if field == "cross_covariance":
            cross = profile["cross_covariance"]
            cross["component_id"] = "hsc_covariance"
            _resign_nested(profile, cross, "cross_covariance_identity")
        else:
            kids = profile["children"]["KIDS"]
            source = {
                "psf": "hsc_psf",
                "n_z": "hsc_n_z",
                "calibration": "hsc_shear_calibration",
            }[field]
            target = {
                "psf": "psf_component_id",
                "n_z": "n_z_component_id",
                "calibration": "calibration_or_response_component_id",
            }[field]
            kids[target] = source
            _resign_nested(profile, kids, "child_identity_id")
            cross = profile["cross_covariance"]
            cross["kids_child_identity_id"] = kids["child_identity_id"]
            _resign_nested(profile, cross, "cross_covariance_identity")
        unsigned_profile = dict(profile)
        unsigned_profile.pop("profile_id")
        profile["profile_id"] = canonical_sha256(unsigned_profile)

    _rewrite_evidence(descriptor, mutate)
    decision = evaluate_lane_identity(
        registry=registry,
        lane_id="HSC_KIDS",
        descriptor=descriptor,
        inspected_at_utc=STAMP_A,
    )
    assert decision.status is AdmissionStatus.REJECTED_MISSING_SEMANTIC_CONTRACT
    assert not decision.records


@pytest.mark.parametrize(
    ("lane_id", "component_id", "identity_path", "unchanged_path"),
    (
        (
            "PLANCK",
            "smica_map",
            ("pipelines", "SMICA", "pipeline_identity"),
            ("pipelines", "COMMANDER", "pipeline_identity"),
        ),
        (
            "CF4",
            "catalogue",
            ("catalogue", "catalogue_identity"),
            ("semantics", "semantics_identity"),
        ),
        (
            "HSC_KIDS",
            "hsc_psf",
            ("children", "HSC", "child_identity_id"),
            ("children", "KIDS", "child_identity_id"),
        ),
    ),
)
def test_native_child_identities_bind_exact_component_bytes(
    tmp_path: Path,
    lane_id: str,
    component_id: str,
    identity_path: tuple[str, ...],
    unchanged_path: tuple[str, ...],
) -> None:
    descriptor = _valid_descriptor(tmp_path / lane_id.lower(), lane_id)
    components = descriptor["components"]
    root = Path(descriptor["root"])
    evidence = json.loads(
        (root / descriptor["evidence_relative_path"]).read_text(encoding="utf-8")
    )
    before = evidence["native_identity_profile"]
    changed = json.loads(json.dumps(components))
    row = next(value for value in changed if value["component_id"] == component_id)
    row["content_sha256"] = "f" * 64
    after = _native_profile(lane_id, evidence["product_id"], changed, evidence)

    def value_at(payload: dict[str, object], path: tuple[str, ...]):
        value = payload
        for key in path:
            value = value[key]
        return value

    assert value_at(before, identity_path) != value_at(after, identity_path)
    assert value_at(before, unchanged_path) == value_at(after, unchanged_path)


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


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        (
            "git_commit_or_worktree_state",
            "BOUND_SOURCE_WORKTREE:sha256:" + "0" * 64,
            "generation identity source binding drifted",
        ),
        (
            "generating_procedure",
            ["python3", "-B", "scripts/codex_harness/run_pr289_data_identity_v2.py", "check"],
            "generation procedure is not the exact build argv",
        ),
        (
            "generating_procedure",
            [
                "/usr/bin/python3",
                "-B",
                "scripts/codex_harness/run_pr289_data_identity_v2.py",
                "build",
            ],
            "generation procedure is not the exact build argv",
        ),
    ),
)
def test_claim_receipt_generation_identity_fails_closed(
    field: str, value: object, message: str
) -> None:
    source_bindings = _source_bindings()
    generation_identity = {
        "schema": "common.source_bound_generation_identity.v1",
        "git_commit_or_worktree_state": "BOUND_SOURCE_WORKTREE:"
        + canonical_sha256(
            {
                path: "sha256:" + digest.removeprefix("sha256:")
                for path, digest in source_bindings.items()
            }
        ),
        "generating_procedure": [
            "python3",
            "-B",
            "scripts/codex_harness/run_pr289_data_identity_v2.py",
            "build",
        ],
    }
    generation_identity[field] = value
    with pytest.raises(DataIdentityError, match=message):
        build_data_identity_v2_receipt(
            registry=load_lane_registry(REGISTRY_PATH),
            root_descriptors={},
            inspected_at_utc=STAMP_A,
            spec_path=SPEC,
            source_bindings=source_bindings,
            generation_identity=generation_identity,
        )


def test_claim_receipt_requires_runbook_and_claim_ledger_bindings() -> None:
    source_bindings = _source_bindings()
    source_bindings.pop(str(CLAIM_LEDGER.relative_to(ROOT)))
    normalized = {
        path: "sha256:" + digest.removeprefix("sha256:")
        for path, digest in source_bindings.items()
    }
    with pytest.raises(DataIdentityError, match="required source binding missing"):
        build_data_identity_v2_receipt(
            registry=load_lane_registry(REGISTRY_PATH),
            root_descriptors={},
            inspected_at_utc=STAMP_A,
            spec_path=SPEC,
            source_bindings=source_bindings,
            generation_identity={
                "schema": "common.source_bound_generation_identity.v1",
                "git_commit_or_worktree_state": "BOUND_SOURCE_WORKTREE:"
                + canonical_sha256(normalized),
                "generating_procedure": [
                    "python3",
                    "-B",
                    "scripts/codex_harness/run_pr289_data_identity_v2.py",
                    "build",
                ],
            },
        )


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


def test_runner_refuses_hardlinked_output_before_payload_generation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from scripts.codex_harness import run_pr289_data_identity_v2 as runner

    generated = tmp_path / "docs/generated"
    generated.mkdir(parents=True)
    outside = tmp_path / "outside.json"
    outside.write_text("preserve\n", encoding="utf-8")
    destination = generated / "receipt.json"
    destination.hardlink_to(outside)
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    monkeypatch.setattr(runner, "OUTPUT", destination)

    def must_not_build(*_args, **_kwargs):
        raise AssertionError("payload generation ran before destination preflight")

    monkeypatch.setattr(runner, "_build", must_not_build)
    assert runner._write() == 1
    assert outside.read_text(encoding="utf-8") == "preserve\n"


def test_runner_check_rejects_hardlinked_receipt(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from scripts.codex_harness import run_pr289_data_identity_v2 as runner

    generated = tmp_path / "docs/generated"
    generated.mkdir(parents=True)
    payload = {"terminal": "PASS_DATA_IDENTITY_V2_PREFLIGHT"}
    outside = tmp_path / "outside.json"
    outside.write_bytes(runner._encoded(payload))
    destination = generated / "receipt.json"
    destination.hardlink_to(outside)
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    monkeypatch.setattr(runner, "OUTPUT", destination)
    monkeypatch.setattr(runner, "_build", lambda root=tmp_path: payload)

    with pytest.raises(RuntimeError, match="single-link regular"):
        runner._check(root=tmp_path)


def test_runner_reloads_exact_candidate_module_over_preloaded_replacement(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from scripts.codex_harness import run_pr289_data_identity_v2 as runner

    fake = types.ModuleType("common.data_identity")

    def must_not_execute(*_args, **_kwargs):
        raise AssertionError("preloaded replacement module executed")

    fake.build_data_identity_v2_receipt = must_not_execute
    fake.load_lane_registry = must_not_execute
    monkeypatch.setitem(sys.modules, "common.data_identity", fake)
    payload = runner._build()
    assert payload["terminal"] == "PASS_DATA_IDENTITY_V2_PREFLIGHT"
    loaded = sys.modules["common.data_identity"]
    assert Path(loaded.__file__).resolve() == MODULE.resolve()


def test_runner_executes_only_the_verified_candidate_module_bytes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from scripts.codex_harness import run_pr289_data_identity_v2 as runner

    module_name = "common.data_identity"
    expected = MODULE.resolve()

    class InconsistentLoader(importlib.abc.Loader):
        def exec_module(self, module) -> None:
            module.__file__ = str(expected)

            class Receipt:
                def as_payload(self):
                    return {
                        "terminal": "INCONSISTENT_LOADER_EXECUTED",
                        "aggregate_status": "NO_ADMITTED_IDENTITIES",
                        "authorization_receipts": [
                            {"status": "NOT_AUTHORIZED"} for _ in range(6)
                        ],
                    }

            def load_lane_registry(_path):
                return object()

            def build_data_identity_v2_receipt(**_kwargs):
                return Receipt()

            load_lane_registry.__module__ = module_name
            build_data_identity_v2_receipt.__module__ = module_name
            module.load_lane_registry = load_lane_registry
            module.build_data_identity_v2_receipt = build_data_identity_v2_receipt

        def get_data(self, _path: str) -> bytes:
            return expected.read_bytes()

    loader = InconsistentLoader()

    class Finder(importlib.abc.MetaPathFinder):
        def find_spec(self, fullname, _path, _target=None):
            if fullname != module_name:
                return None
            spec = importlib.machinery.ModuleSpec(
                fullname, loader, origin=str(expected)
            )
            spec.has_location = True
            return spec

    monkeypatch.setattr(sys, "meta_path", [Finder(), *sys.meta_path])
    payload = runner._build()
    assert payload["terminal"] == "PASS_DATA_IDENTITY_V2_PREFLIGHT"


def test_runner_output_parent_replacement_fails_closed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from scripts.codex_harness import run_pr289_data_identity_v2 as runner

    root = tmp_path / "repo"
    generated = root / "docs/generated"
    outside = tmp_path / "outside"
    generated.mkdir(parents=True)
    outside.mkdir()
    output = generated / "receipt.json"

    def replace_parent_during_build(root: Path = root):
        generated.rename(root / "docs/generated-before-build")
        generated.symlink_to(outside, target_is_directory=True)
        return {
            "terminal": "PASS_DATA_IDENTITY_V2_PREFLIGHT",
            "receipt_content_id": "sha256:" + "0" * 64,
        }

    monkeypatch.setattr(runner, "ROOT", root)
    monkeypatch.setattr(runner, "OUTPUT", output)
    monkeypatch.setattr(runner, "_build", replace_parent_during_build)
    with contextlib.redirect_stdout(StringIO()):
        with pytest.raises(RuntimeError, match="parent|directory"):
            runner._write()
    assert not (outside / "receipt.json").exists()


def test_runner_late_build_parent_replacement_fails_closed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from scripts.codex_harness import run_pr289_data_identity_v2 as runner

    root = tmp_path / "repo"
    generated = root / "docs/generated"
    detached = root / "docs/generated-detached"
    generated.mkdir(parents=True)
    output = generated / "receipt.json"
    payload = {
        "terminal": "PASS_DATA_IDENTITY_V2_PREFLIGHT",
        "receipt_content_id": "sha256:" + "0" * 64,
    }
    real_replace = runner.os.replace

    def replace_after_precheck(
        source,
        destination,
        *,
        src_dir_fd=None,
        dst_dir_fd=None,
    ):
        generated.rename(detached)
        generated.mkdir()
        return real_replace(
            source,
            destination,
            src_dir_fd=src_dir_fd,
            dst_dir_fd=dst_dir_fd,
        )

    monkeypatch.setattr(runner, "ROOT", root)
    monkeypatch.setattr(runner, "OUTPUT", output)
    monkeypatch.setattr(runner, "_build", lambda root=root: payload)
    monkeypatch.setattr(runner.os, "replace", replace_after_precheck)
    with contextlib.redirect_stdout(StringIO()):
        with pytest.raises(RuntimeError, match="parent|directory"):
            runner._write()
    assert not output.exists()


def test_runner_late_check_parent_replacement_fails_closed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from scripts.codex_harness import run_pr289_data_identity_v2 as runner

    root = tmp_path / "repo"
    generated = root / "docs/generated"
    detached = root / "docs/generated-detached"
    generated.mkdir(parents=True)
    output = generated / "receipt.json"
    payload = {
        "terminal": "PASS_DATA_IDENTITY_V2_PREFLIGHT",
        "receipt_content_id": "sha256:" + "0" * 64,
    }
    output.write_bytes(runner._encoded(payload))
    real_read = runner._read_bound_output
    calls = 0

    def read_after_precheck(*, output: Path, parent_fd: int) -> bytes:
        nonlocal calls
        calls += 1
        if calls == 2:
            generated.rename(detached)
            generated.mkdir()
            (generated / output.name).write_bytes(b"replacement\n")
        return real_read(output=output, parent_fd=parent_fd)

    monkeypatch.setattr(runner, "ROOT", root)
    monkeypatch.setattr(runner, "OUTPUT", output)
    monkeypatch.setattr(runner, "_build", lambda root=root: payload)
    monkeypatch.setattr(runner, "_read_bound_output", read_after_precheck)
    with contextlib.redirect_stdout(StringIO()):
        with pytest.raises(RuntimeError, match="parent|directory"):
            runner._check(root=root)
    assert output.read_bytes() == b"replacement\n"


def test_receipt_generation_identity_is_interpreter_alias_independent() -> None:
    from scripts.codex_harness import run_pr289_data_identity_v2 as runner

    identity = runner._generation_identity(runner._source_bindings())
    assert identity["generating_procedure"][0] == "python3"
    for executable in (Path("/usr/bin/python"), Path("/usr/bin/python3")):
        if not executable.exists():
            continue
        completed = subprocess.run(
            [
                str(executable),
                "-B",
                "scripts/codex_harness/run_pr289_data_identity_v2.py",
                "check",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr


@pytest.mark.parametrize("kind", ("traversal", "symlink"))
def test_portable_archive_extraction_rejects_unsafe_members(
    tmp_path: Path, kind: str
) -> None:
    from scripts.codex_harness import run_pr289_data_identity_v2 as runner

    archive_bytes = BytesIO()
    with tarfile.open(fileobj=archive_bytes, mode="w") as archive:
        if kind == "traversal":
            info = tarfile.TarInfo("../escape.txt")
            raw = b"escape"
            info.size = len(raw)
            archive.addfile(info, BytesIO(raw))
        else:
            info = tarfile.TarInfo("linked")
            info.type = tarfile.SYMTYPE
            info.linkname = "outside"
            archive.addfile(info)
    archive_bytes.seek(0)
    destination = tmp_path / "clean"
    destination.mkdir()
    with tarfile.open(fileobj=archive_bytes, mode="r:") as archive:
        with pytest.raises(RuntimeError, match="unsafe archive member"):
            runner._safe_extract_archive(archive, destination)
    assert not (tmp_path / "escape.txt").exists()
