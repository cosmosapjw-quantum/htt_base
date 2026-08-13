"""PR-291 CF4 preactivation and synthetic operator contracts.

The suite never opens a CF4 catalogue root.  It freezes only synthetic
operator arithmetic, exact identity/provenance checks, and a non-execution
decision whose current terminal remains predecessor-blocked.
"""

from __future__ import annotations

import hashlib
import importlib.util
from io import BytesIO
import json
from pathlib import Path
import shutil
import sys
import tarfile
import types
import copy

import numpy as np
import pytest
import yaml

import common.cf4_observed_lane_activation as cf4_activation_module
from common.cf4_observed_lane_activation import (
    CF4_NONEXECUTION_SOURCE_PATHS,
    Cf4ObservedLaneActivationError,
    build_cf4_activation_decision,
    build_cf4_nonexecution_receipt,
    canonical_json_bytes,
)
from common.data_identity import (
    build_not_authorized_receipt,
    canonical_sha256,
    evaluate_lane_identity,
    load_lane_registry,
)
from common.source_separation import (
    SourceSeparationDecisionStatus,
    build_weak_identification_threshold_contract,
    evaluate_source_separation,
)
from htt.obsstat.cf4_post275_lane import (
    CF4_FEATURE_ORDER_ID,
    CF4_OPERATOR_IDENTITY_FIELDS,
    Cf4Post275Error,
    analyze_synthetic_eigenspace_drift,
    analyze_synthetic_response_nullspace,
    analyze_synthetic_shear,
    build_cf4_gate_snapshot,
    build_cf4_moment_design,
    build_structural_identified_set,
    build_synthetic_depth_zoa_path,
    compare_correlated_estimands,
    fit_synthetic_cf4_moments,
    legacy_wf_curl_selfcheck,
    validate_cf4_operator_identity,
)
from tests.contracts.test_data_identity_registry_v2 import _valid_descriptor


ROOT = Path(__file__).resolve().parents[2]
SPEC_REL = Path("docs/research_program/post_pr275/pr291_spec.yaml")
STATUS_REL = Path("docs/codex_handoff/pr_status.yaml")
IDENTITY_REL = Path("docs/generated/pr289_data_identity_v2_receipt.json")
PR287_REL = Path("docs/generated/pr287_fresh_blind_typed_replay_receipt.json")
REGISTRY_REL = Path(
    "docs/research_program/post_pr275/data_registry_v2/LANE_REGISTRY_V2.json"
)


def _sha_id(label: str) -> str:
    return "sha256:" + hashlib.sha256(label.encode("ascii")).hexdigest()


def _identity() -> dict[str, str]:
    identity = {
        name: f"pr291:{name}:synthetic-v1"
        for name in CF4_OPERATOR_IDENTITY_FIELDS
    }
    identity.update(
        {
            "covariance_id": _sha_id("pr291-covariance"),
            "response_id": _sha_id("pr291-response"),
            "estimand_id": _sha_id("pr291-source-geometry"),
            "feature_order_id": CF4_FEATURE_ORDER_ID,
        }
    )
    return identity


def _weak_source_decision(identity: dict[str, str], response):
    return evaluate_source_separation(
        source_geometry_report_id=identity["estimand_id"],
        covariance_id=identity["covariance_id"],
        nuisance_tangent_id=_sha_id("pr291-nuisance"),
        normalizer_id=response.normalizer_id,
        normalizer_source_identity="PR291-SYNTHETIC-DIMENSIONLESS-NORMALIZER",
        normalizer_coordinate_map_id=_sha_id("pr291-normalizer-map"),
        parameter_coordinate_units="dimensionless_beta_c_equals_1",
        provider_available=True,
        covariance_supported=True,
        local_parameter_count=1,
        global_parameter_count=1,
        local_rank=1,
        global_rank=1,
        joint_rank=2,
        principal_angles_radians=(0.1,),
        joint_singular_values=(1.0, 0.05),
        threshold_contract=build_weak_identification_threshold_contract(
            minimum_principal_angle_radians=0.2,
            minimum_normalizer_bound_relative_joint_singular_value=0.01,
        ),
    )


def _directions_and_distances() -> tuple[np.ndarray, np.ndarray]:
    raw = np.asarray(
        [
            (1, 0, 0),
            (-1, 0, 0),
            (0, 1, 0),
            (0, -1, 0),
            (0, 0, 1),
            (0, 0, -1),
            (1, 1, 0),
            (1, -1, 0),
            (1, 0, 1),
            (1, 0, -1),
            (0, 1, 1),
            (0, 1, -1),
            (1, 1, 1),
            (-1, 1, 1),
        ],
        dtype=float,
    )
    directions = raw / np.linalg.norm(raw, axis=1)[:, None]
    distances = np.linspace(20.0, 150.0, directions.shape[0])
    return directions, distances


def _depth_rows() -> tuple[dict[str, object], ...]:
    return (
        {
            "depth_mpc": 50.0,
            "support_unit_ids": ("g1", "g2", "g3", "g4"),
        },
        {
            "depth_mpc": 100.0,
            "support_unit_ids": ("g1", "g2", "g3"),
        },
        {
            "depth_mpc": 150.0,
            "support_unit_ids": ("g1", "g2"),
        },
    )


def _copy_activation_inputs(tmp_path: Path) -> Path:
    identity = json.loads((ROOT / IDENTITY_REL).read_text(encoding="utf-8"))
    sources = tuple(Path(value) for value in identity["source_bindings"])
    for relative in (SPEC_REL, STATUS_REL, IDENTITY_REL, *sources):
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, destination)
    return tmp_path


def _stub_source_bindings(decision=None) -> dict[str, str]:
    paths = set(CF4_NONEXECUTION_SOURCE_PATHS)
    if decision is not None:
        for row in decision.dependency_snapshot:
            terminal = row.get("terminal_receipt")
            if isinstance(terminal, dict) and terminal.get("file_sha256"):
                paths.add(terminal["path"])
    return {path: "sha256:" + "1" * 64 for path in paths}


def _generation_identity() -> dict[str, str]:
    return {
        "source_commit_or_external_candidate_seal_id": "sha256:" + "2" * 64,
        "worktree_state": "source_hash_bound_dirty_or_committed",
        "exact_replay_environment": "repository_python_contract",
    }


def _install_admitted_cf4_identity(
    *,
    root: Path,
    descriptor_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutate_decision=None,
) -> None:
    registry = load_lane_registry(root / REGISTRY_REL)
    lane = registry.lane("CF4")
    descriptor = _valid_descriptor(descriptor_root, "CF4")
    decision = evaluate_lane_identity(
        registry=registry,
        lane_id="CF4",
        descriptor=descriptor,
        inspected_at_utc="2026-08-09T00:00:00+00:00",
    )
    assert decision.complete
    decision_payload = decision.as_payload()
    if mutate_decision is not None:
        mutate_decision(decision_payload)
    authorization_payload = build_not_authorized_receipt(
        lane, decision
    ).as_payload()

    receipt_path = root / IDENTITY_REL
    payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    payload["lane_decisions"] = [
        decision_payload if row["lane_id"] == "CF4" else row
        for row in payload["lane_decisions"]
    ]
    payload["authorization_receipts"] = [
        authorization_payload if row["lane_id"] == "CF4" else row
        for row in payload["authorization_receipts"]
    ]
    payload.pop("receipt_content_id", None)
    content_id = "sha256:" + hashlib.sha256(
        canonical_json_bytes(payload)
    ).hexdigest()
    payload["receipt_content_id"] = content_id
    receipt_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    monkeypatch.setattr(
        cf4_activation_module, "_EXPECTED_PR289_RECEIPT_CONTENT_ID", content_id
    )


def test_live_preactivation_is_blocked_without_observed_side_effects() -> None:
    observed = ROOT / "docs/research_program/post_pr275/data_runs/cf4/results"
    before = observed.exists()
    decision = build_cf4_activation_decision(repository_root=ROOT)
    assert decision.terminal == "BLOCKED_PREDECESSOR_FINAL_SUCCESS"
    assert decision.observed_data_executed is False
    assert decision.numeric_outputs_written == ()
    assert decision.network_or_download_side_effect is False
    assert observed.exists() is before


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("scientific_boundary", "claim_tier"), "C6"),
        (("scientific_boundary", "public_use"), True),
        (("scientific_boundary", "family_identification_gate"), "PASS"),
        (("human_execution_gate", "trusted_hmac_key_sha256"), "f" * 64),
        (("human_execution_gate", "freshness_contract", "nonce_required"), False),
        (("data_identity_contract", "forbidden_admission_shortcuts"), []),
        (("pipeline_contract", "exact_estimand_order"), []),
        (("pipeline_contract", "full_covariance_contract", "diagonal_shortcut_allowed"), True),
        (("pipeline_contract", "legacy_disposition", "physical_vorticity_claim"), "SUPPORTED"),
        (("pipeline_contract", "legacy_disposition", "potential_flow_claim"), "SUPPORTED"),
        (("pipeline_contract", "synthetic_contract_fixture", "cannot_support"), ["nothing"]),
        (("output_contract", "current_allowed_outputs"), ["observed_result"]),
        (("output_contract", "output_containment", "preflight_before_payload_generation"), False),
        (("output_contract", "future_observed_result_contract", "current_status"), "ENABLED"),
        (("output_contract", "future_observed_result_contract", "required_metadata"), []),
        (("output_contract", "future_observed_result_contract", "status_value_contract", "sky_support_status", "allowed_values"), ["UNKNOWN"]),
        (("output_contract", "future_observed_result_contract", "status_value_contract", "null_mock_status", "missing_unknown_or_not_evaluated"), "ALLOW"),
        (("output_contract", "future_observed_result_contract", "fixed_firewall_values", "public_use"), True),
        (("output_contract", "future_observed_result_contract", "content_binding_rule"), "self hash only"),
    ],
)
def test_spec_relaxations_fail_closed(
    tmp_path: Path, path: tuple[str, ...], value: object
) -> None:
    root = _copy_activation_inputs(tmp_path)
    spec_path = root / SPEC_REL
    payload = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    cursor = payload
    for key in path[:-1]:
        cursor = cursor[key]
    cursor[path[-1]] = value
    spec_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    with pytest.raises(Cf4ObservedLaneActivationError):
        build_cf4_activation_decision(repository_root=root)


def test_pr289_provenance_is_replayed_before_lane_admission(tmp_path: Path) -> None:
    root = _copy_activation_inputs(tmp_path)
    identity_path = root / IDENTITY_REL
    payload = json.loads(identity_path.read_text(encoding="utf-8"))
    payload["registry_content_id"] = "sha256:" + "f" * 64
    payload.pop("receipt_content_id")
    payload["receipt_content_id"] = "sha256:" + hashlib.sha256(
        canonical_json_bytes(payload)
    ).hexdigest()
    identity_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    with pytest.raises(Cf4ObservedLaneActivationError):
        build_cf4_activation_decision(repository_root=root)


def test_exact_nine_role_cf4_native_admission_replays(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _copy_activation_inputs(tmp_path / "repo")
    _install_admitted_cf4_identity(
        root=root,
        descriptor_root=tmp_path / "cf4-native",
        monkeypatch=monkeypatch,
    )
    decision = build_cf4_activation_decision(repository_root=root)
    snapshot = decision.data_identity_snapshot
    assert snapshot["satisfied"] is True
    assert snapshot["record_count"] == 9
    assert tuple(snapshot["component_ids"]) == (
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
    assert snapshot["canonical_record_replay"] is True
    assert snapshot["native_identity_profile"]["schema"] == (
        "common.cf4_native_identity.v1"
    )


def test_record_count_shortcut_cannot_substitute_for_nine_role_replay(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def truncate_and_reseal(payload: dict[str, object]) -> None:
        records = payload["records"][:3]
        payload["records"] = records
        payload["lane_admission_bundle_id"] = canonical_sha256(
            {
                "lane_id": payload["lane_id"],
                "product_id": payload["product_id"],
                "component_inventory_id": records[0]["component_inventory_id"],
                "record_ids": [row["record_id"] for row in records],
            }
        )

    root = _copy_activation_inputs(tmp_path / "repo")
    _install_admitted_cf4_identity(
        root=root,
        descriptor_root=tmp_path / "cf4-shortcut",
        monkeypatch=monkeypatch,
        mutate_decision=truncate_and_reseal,
    )
    decision = build_cf4_activation_decision(repository_root=root)
    snapshot = decision.data_identity_snapshot
    assert snapshot["satisfied"] is False
    assert snapshot["canonical_record_replay"] is False
    assert any("canonical native-record replay failed" in reason for reason in snapshot["reasons"])


def test_missing_pr287_receipt_is_a_predecessor_blocker_not_an_admission() -> None:
    assert not (ROOT / PR287_REL).exists()
    decision = build_cf4_activation_decision(repository_root=ROOT)
    row = next(item for item in decision.dependency_snapshot if item["pr_id"] == "PR-287")
    assert row["satisfied"] is False
    assert decision.data_identity_snapshot["admission_status"] == "REJECTED_NOT_PRESENT"
    assert decision.human_authorization_snapshot["status"] == "NOT_EVALUATED_PREDECESSOR_BLOCKED"


def test_unregistered_pr287_receipt_identity_cannot_unlock_dependency(
    tmp_path: Path,
) -> None:
    root = _copy_activation_inputs(tmp_path)
    status_path = root / STATUS_REL
    status = yaml.safe_load(status_path.read_text(encoding="utf-8"))
    for index, pr_id in enumerate(("PR-201", "PR-287", "PR-289"), start=1):
        status.setdefault("completed", []).append(pr_id)
        row = {
            "resolution": "COMPLETED_SUCCESS",
            "candidate_sha": f"{index:040x}",
            "success_dependency_satisfied": True,
            "observed_data_executed": False,
            "public_use": False,
        }
        if pr_id == "PR-287":
            row["terminal"] = "PASS_FRESH_BLIND_TYPED_REPLAY"
        if pr_id == "PR-289":
            row["terminal"] = "PASS_DATA_IDENTITY_V2_PREFLIGHT"
        status.setdefault("execution_resolutions", {})[pr_id] = row
    status_path.write_text(yaml.safe_dump(status, sort_keys=False), encoding="utf-8")
    unsigned = {
        "schema": "HTT_PR287_FRESH_BLIND_TYPED_REPLAY_RECEIPT_V1",
        "terminal": "PASS_FRESH_BLIND_TYPED_REPLAY",
        "synthetic_only": True,
    }
    receipt = {
        **unsigned,
        "receipt_content_id": "sha256:"
        + hashlib.sha256(canonical_json_bytes(unsigned)).hexdigest(),
    }
    receipt_path = root / PR287_REL
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    decision = build_cf4_activation_decision(repository_root=root)
    assert decision.terminal == "BLOCKED_PREDECESSOR_FINAL_SUCCESS"
    row = next(item for item in decision.dependency_snapshot if item["pr_id"] == "PR-287")
    assert any(
        "frozen terminal receipt identity is unregistered" in reason
        for reason in row["reasons"]
    )


def test_untrusted_hmac_receipt_has_no_preactivation_acceptance_path(
    tmp_path: Path,
) -> None:
    root = _copy_activation_inputs(tmp_path)
    auth = (
        root
        / "docs/research_program/post_pr275/data_runs/cf4/"
        "H_CF4_EXECUTION_AUTHORIZATION.json"
    )
    auth.parent.mkdir(parents=True, exist_ok=True)
    auth.write_text(
        json.dumps(
            {
                "schema": "common.human_execution_authorization.v1",
                "status": "AUTHORIZED",
                "lane_id": "CF4",
                "gate_id": "H-CF4",
                "authorization_hmac_sha256": "f" * 64,
            }
        ),
        encoding="utf-8",
    )
    decision = build_cf4_activation_decision(repository_root=root)
    assert decision.terminal == "BLOCKED_PREDECESSOR_FINAL_SUCCESS"
    assert decision.human_authorization_snapshot["trusted_hmac_key_sha256"] is None
    assert decision.human_authorization_snapshot["authorized"] is False


def test_operator_identity_is_exact_and_nonempty() -> None:
    identity = _identity()
    assert validate_cf4_operator_identity(identity) == identity
    malformed = dict(identity)
    malformed.pop("row_identity_id")
    with pytest.raises(Cf4Post275Error):
        validate_cf4_operator_identity(malformed)


def test_synthetic_monopole_bulk_shear_design_has_rank_nine_and_recovers() -> None:
    directions, distances = _directions_and_distances()
    design = build_cf4_moment_design(directions, distances, _identity())
    assert design.rank == 9
    coefficients = np.asarray([11.0, 2.0, -3.0, 5.0, 0.4, -0.2, 0.1, 0.05, -0.08])
    velocities = np.asarray(design.matrix) @ coefficients
    covariance = np.eye(len(velocities)) * 2.0
    covariance += 0.05 * (np.ones_like(covariance) - np.eye(len(velocities)))
    report = fit_synthetic_cf4_moments(
        velocities, design=design, covariance=covariance
    )
    assert np.allclose(report.coefficients, coefficients, rtol=0.0, atol=1e-10)
    assert report.effective_rank == 9
    assert report.observed_data_executed is False
    assert report.units[0] == "km_per_s"
    assert set(report.units[4:]) == {"km_per_s_per_Mpc"}


@pytest.mark.parametrize("distance_scale", (1.0e-200, 1.0e200))
def test_design_rank_is_invariant_to_distance_unit_rescaling(
    distance_scale: float,
) -> None:
    directions, distances = _directions_and_distances()
    design = build_cf4_moment_design(
        directions, distances * distance_scale, _identity()
    )
    assert design.rank == 9
    assert all(np.isfinite(design.column_scales))


def test_stf_diagonal_coordinates_reconstruct_axis_components() -> None:
    directions, distances = _directions_and_distances()
    design = build_cf4_moment_design(directions, distances, _identity())
    matrix = np.asarray(design.matrix)
    assert design.feature_names[4:6] == ("shear_Sxx", "shear_Syy")
    assert np.allclose(matrix[0, 4:6], (distances[0], 0.0))
    assert np.allclose(matrix[2, 4:6], (0.0, distances[2]))
    assert np.allclose(matrix[4, 4:6], (-distances[4], -distances[4]))
    sxx, syy = 0.4, -0.2
    szz = -sxx - syy
    assert matrix[0, 4] * sxx + matrix[0, 5] * syy == pytest.approx(
        distances[0] * sxx
    )
    assert matrix[2, 4] * sxx + matrix[2, 5] * syy == pytest.approx(
        distances[2] * syy
    )
    assert matrix[4, 4] * sxx + matrix[4, 5] * syy == pytest.approx(
        distances[4] * szz
    )


def test_synthetic_fit_rejects_diagonal_indefinite_and_rank_deficient_inputs() -> None:
    directions, distances = _directions_and_distances()
    design = build_cf4_moment_design(directions, distances, _identity())
    velocities = np.zeros(len(directions))
    with pytest.raises(Cf4Post275Error, match="diagonal"):
        fit_synthetic_cf4_moments(velocities, design=design, covariance=np.eye(len(directions)))
    bad = np.eye(len(directions))
    bad[0, 0] = -1.0
    bad[0, 1] = bad[1, 0] = 0.1
    with pytest.raises(Cf4Post275Error, match="positive definite"):
        fit_synthetic_cf4_moments(velocities, design=design, covariance=bad)
    with pytest.raises(Cf4Post275Error, match="rank nine|column normalizer"):
        build_cf4_moment_design(directions[:8], distances[:8], _identity())

    ill_conditioned = np.eye(len(directions))
    ill_conditioned[0, 0] = 1.0e-13
    ill_conditioned[0, 1] = ill_conditioned[1, 0] = 1.0e-8
    with pytest.raises(Cf4Post275Error, match="ill-conditioned"):
        fit_synthetic_cf4_moments(
            velocities, design=design, covariance=ill_conditioned
        )


def test_cross_catalogue_covariance_changes_exact_quadratic_form() -> None:
    result = compare_correlated_estimands(
        [1.0, 0.0],
        [0.0, 0.0],
        covariance_a=np.eye(2),
        covariance_b=np.eye(2),
        cross_covariance=0.9 * np.eye(2),
        feature_ids=("bulk_x", "bulk_y"),
    )
    assert result.chi_square == pytest.approx(5.0)
    assert result.dof == 2
    assert result.same_catalogue_cross_dependence_used is True


def test_depth_zoa_path_is_nested_and_identity_bound() -> None:
    identity = _identity()
    report = build_synthetic_depth_zoa_path(
        _depth_rows(), operator_identity=identity
    )
    assert report.path.nesting_rule == "TARGET_SUPPORT_SUBSET_OF_SOURCE"
    assert report.zoa_mask_id == identity["zone_of_avoidance_mask_id"]
    assert report.grouping_id == identity["grouping_id"]
    assert report.depth_definition_id == identity["depth_path_id"]
    assert len(set(report.row_identity_ids)) == 3
    with pytest.raises(Cf4Post275Error, match="nested"):
        build_synthetic_depth_zoa_path(
            (
                {"depth_mpc": 50.0, "support_unit_ids": ("g1",)},
                {"depth_mpc": 100.0, "support_unit_ids": ("g2",)},
            ),
            operator_identity=identity,
        )
    with pytest.raises(Cf4Post275Error, match="field inventory"):
        build_synthetic_depth_zoa_path(
            (
                {
                    "depth_mpc": 50.0,
                    "support_unit_ids": ("g1", "g2"),
                    "caller_selection_id": "forged-selection",
                },
                {
                    "depth_mpc": 100.0,
                    "support_unit_ids": ("g1",),
                    "caller_selection_id": "forged-selection",
                },
            ),
            operator_identity=identity,
        )


@pytest.mark.parametrize(
    "identity_field",
    (
        "catalogue_product_id",
        "grouping_id",
        "row_identity_id",
        "selection_id",
        "covariance_id",
        "depth_path_id",
        "zone_of_avoidance_mask_id",
    ),
)
def test_depth_path_identity_is_derived_from_each_native_role(
    identity_field: str,
) -> None:
    identity = _identity()
    baseline = build_synthetic_depth_zoa_path(
        _depth_rows(), operator_identity=identity
    )
    mutated = dict(identity)
    mutated[identity_field] = _sha_id("mutated-" + identity_field)
    observed = build_synthetic_depth_zoa_path(
        _depth_rows(), operator_identity=mutated
    )
    assert observed.path.content_id != baseline.path.content_id


def test_degenerate_shear_and_structural_set_abstain() -> None:
    identity = _identity()
    shear = analyze_synthetic_shear(
        np.diag([1.0, 1.0, -2.0]),
        covariance_id=identity["covariance_id"],
        response_id=identity["response_id"],
    )
    response = analyze_synthetic_response_nullspace(
        [[1.0, 0.0, 1.0], [0.0, 1.0, 1.0]],
        [[1.0, 0.2], [0.2, 1.0]],
        covariance_id=identity["covariance_id"],
        response_id=identity["response_id"],
        parameter_labels=("local", "global", "nuisance"),
        parameter_roles=("LOCAL", "GLOBAL", "NUISANCE"),
    )
    source_decision = _weak_source_decision(identity, response)
    assert shear.identification_status == "WEAKLY_IDENTIFIED"
    assert shear.required_action == "RESPONSE_EQUIVALENCE_ABSTENTION"
    identified = build_structural_identified_set(
        lower=-2.0,
        upper=4.0,
        nuisance_box_id="nuisance:synthetic:v1",
        response=response,
        source_separation=source_decision,
    )
    assert identified["status"] == "BOUNDED_BUT_NOT_POINT_IDENTIFIED"
    assert identified["reported_point"] is None
    assert identified["confidence_level"] is None
    assert identified["response_content_id"] == response.content_id
    assert identified["source_separation_decision_id"] == source_decision.decision_id


def test_registered_thresholds_cannot_be_overridden_by_callers() -> None:
    identity = _identity()
    with pytest.raises(TypeError, match="eigengap_floor"):
        analyze_synthetic_shear(
            np.diag([-2.0, 0.5, 1.5]),
            covariance_id=identity["covariance_id"],
            response_id=identity["response_id"],
            eigengap_floor=2.0,
        )
    with pytest.raises(TypeError, match="eigengap_floor"):
        analyze_synthetic_eigenspace_drift(
            np.diag([-2.0, 0.5, 1.5]),
            np.diag([-2.0, 0.5, 1.5]),
            reference_depth_id="near",
            candidate_depth_id="far",
            depth_path_content_id="depth-path",
            covariance_id=identity["covariance_id"],
            response_id=identity["response_id"],
            eigengap_floor=2.0,
        )
    with pytest.raises(TypeError, match="rank_tolerance"):
        analyze_synthetic_response_nullspace(
            np.eye(2),
            [[1.0, 0.2], [0.2, 1.0]],
            covariance_id=identity["covariance_id"],
            response_id=identity["response_id"],
            parameter_labels=("local", "global"),
            parameter_roles=("LOCAL", "GLOBAL"),
            rank_tolerance=2.0,
        )


def test_structural_identified_set_rejects_singleton_and_untyped_evidence() -> None:
    identity = _identity()
    response = analyze_synthetic_response_nullspace(
        [[1.0, 0.0, 1.0], [0.0, 1.0, 1.0]],
        [[1.0, 0.2], [0.2, 1.0]],
        covariance_id=identity["covariance_id"],
        response_id=identity["response_id"],
        parameter_labels=("local", "global", "nuisance"),
        parameter_roles=("LOCAL", "GLOBAL", "NUISANCE"),
    )
    decision = _weak_source_decision(identity, response)
    with pytest.raises(Cf4Post275Error, match="strictly ordered"):
        build_structural_identified_set(
            lower=3.0,
            upper=3.0,
            nuisance_box_id="nuisance:synthetic:v1",
            response=response,
            source_separation=decision,
        )
    with pytest.raises(TypeError, match="unexpected keyword"):
        build_structural_identified_set(
            lower=-2.0,
            upper=4.0,
            identification_status="WEAKLY_IDENTIFIED",
            nuisance_box_id="nuisance:synthetic:v1",
            response_id=response.response_id,
        )


@pytest.mark.parametrize("scale", (1.0e-100, 1.0e100))
def test_relative_eigengap_classification_is_unit_scale_invariant(
    scale: float,
) -> None:
    tensor = scale * np.diag([1.0, 1.0 + 1.0e-11, -2.0 - 1.0e-11])
    report = analyze_synthetic_shear(
        tensor,
        covariance_id="covariance:synthetic:v1",
        response_id="response:synthetic:v1",
    )
    assert report.identification_status == "WEAKLY_IDENTIFIED"
    assert report.required_action == "RESPONSE_EQUIVALENCE_ABSTENTION"


def test_response_rank_is_whitened_column_scale_invariant_and_roles_are_typed() -> None:
    response = np.asarray([[1.0, 0.0, 1.0], [0.0, 1.0, 1.0]])
    covariance = np.asarray([[1.0, 0.2], [0.2, 1.0]])
    baseline = analyze_synthetic_response_nullspace(
        response,
        covariance,
        covariance_id="covariance:synthetic:v1",
        response_id="response:synthetic:v1",
        parameter_labels=("local", "global", "nuisance"),
        parameter_roles=("LOCAL", "GLOBAL", "NUISANCE"),
    )
    rescaled = analyze_synthetic_response_nullspace(
        response * np.asarray([1.0e-200, 1.0e200, 1.0]),
        covariance,
        covariance_id="covariance:synthetic:v1",
        response_id="response:synthetic:v1",
        parameter_labels=("local", "global", "nuisance"),
        parameter_roles=("LOCAL", "GLOBAL", "NUISANCE"),
    )
    assert (baseline.response_rank, baseline.nullity, baseline.status) == (
        rescaled.response_rank,
        rescaled.nullity,
        rescaled.status,
    )
    payload = baseline.as_payload()
    assert payload["relative_singular_floor"] == 1.0e-12
    assert payload["response_rank"] == 2
    assert payload["nullity"] == 1
    assert payload["normalized_response_content_id"].startswith("sha256:")
    assert payload["covariance_content_id"].startswith("sha256:")
    assert payload["content_id"] == baseline.content_id
    with pytest.raises(Cf4Post275Error, match="labels or roles"):
        analyze_synthetic_response_nullspace(
            response,
            covariance,
            covariance_id="covariance:synthetic:v1",
            response_id="response:synthetic:v1",
            parameter_labels=("one", "two", "three"),
            parameter_roles=("NUISANCE", "NUISANCE", "NUISANCE"),
        )
    ill_conditioned = np.asarray([[1.0e-13, 1.0e-8], [1.0e-8, 1.0]])
    with pytest.raises(Cf4Post275Error, match="ill-conditioned"):
        analyze_synthetic_response_nullspace(
            response,
            ill_conditioned,
            covariance_id="covariance:synthetic:v1",
            response_id="response:synthetic:v1",
            parameter_labels=("local", "global", "nuisance"),
            parameter_roles=("LOCAL", "GLOBAL", "NUISANCE"),
        )


def test_gate_replays_null_basis_and_exact_source_rank() -> None:
    directions, distances = _directions_and_distances()
    identity = _identity()
    depth = build_synthetic_depth_zoa_path(
        _depth_rows(), operator_identity=identity
    )
    design = build_cf4_moment_design(directions, distances, identity)
    shear = analyze_synthetic_shear(
        np.diag([2.0, -0.5, -1.5]),
        covariance_id=identity["covariance_id"],
        response_id=identity["response_id"],
    )
    eigenspace = analyze_synthetic_eigenspace_drift(
        np.diag([1.0, 1.0 + 1e-11, -2.0 - 1e-11]),
        np.diag([1.0 + 1e-11, 1.0, -2.0 - 1e-11]),
        reference_depth_id=depth.path.strata[0].stratum_id,
        candidate_depth_id=depth.path.strata[1].stratum_id,
        depth_path_content_id=depth.path.content_id,
        covariance_id=identity["covariance_id"],
        response_id=identity["response_id"],
    )
    response = analyze_synthetic_response_nullspace(
        [[1.0, 0.0, 1.0], [0.0, 1.0, 1.0]],
        [[1.0, 0.2], [0.2, 1.0]],
        covariance_id=identity["covariance_id"],
        response_id=identity["response_id"],
        parameter_labels=("local", "global", "nuisance"),
        parameter_roles=("LOCAL", "GLOBAL", "NUISANCE"),
    )
    decision = _weak_source_decision(identity, response)

    forged_basis = copy.deepcopy(response)
    object.__setattr__(
        forged_basis,
        "right_null_basis",
        ((1.0, 0.0, 0.0),),
    )
    with pytest.raises(Cf4Post275Error, match="null basis|identity drifted"):
        build_cf4_gate_snapshot(
            design=design,
            depth=depth,
            shear=shear,
            eigenspace_drift=eigenspace,
            response=forged_basis,
            source_separation=decision,
        )

    rank_one = analyze_synthetic_response_nullspace(
        [[1.0, 1.0, 1.0], [2.0, 2.0, 2.0]],
        [[1.0, 0.2], [0.2, 1.0]],
        covariance_id=identity["covariance_id"],
        response_id=identity["response_id"],
        parameter_labels=("local", "global", "nuisance"),
        parameter_roles=("LOCAL", "GLOBAL", "NUISANCE"),
    )
    assert (rank_one.response_rank, rank_one.nullity) == (1, 2)
    with pytest.raises(Cf4Post275Error, match="rank/nullity"):
        build_cf4_gate_snapshot(
            design=design,
            depth=depth,
            shear=shear,
            eigenspace_drift=eigenspace,
            response=rank_one,
            source_separation=_weak_source_decision(identity, rank_one),
        )


def test_eigenspace_drift_uses_path_bound_projectors_not_basis_vectors() -> None:
    depth = build_synthetic_depth_zoa_path(
        _depth_rows(), operator_identity=_identity()
    )
    epsilon = 1e-11
    reference = np.diag([1.0, 1.0 + epsilon, -2.0 - epsilon])
    angle = np.pi / 4.0
    within_cluster = np.asarray(
        [
            [np.cos(angle), -np.sin(angle), 0.0],
            [np.sin(angle), np.cos(angle), 0.0],
            [0.0, 0.0, 1.0],
        ]
    )
    candidate = within_cluster @ reference @ within_cluster.T
    report = analyze_synthetic_eigenspace_drift(
        reference,
        candidate,
        reference_depth_id=depth.path.strata[0].stratum_id,
        candidate_depth_id=depth.path.strata[1].stratum_id,
        depth_path_content_id=depth.path.content_id,
        covariance_id=_identity()["covariance_id"],
        response_id=_identity()["response_id"],
    )
    assert report.identification_status == "WEAKLY_IDENTIFIED"
    assert report.required_action == "EIGENSPACE_EQUIVALENCE_ABSTENTION"
    assert report.cluster_index_groups == ((0,), (1, 2))
    assert report.maximum_subspace_angle_radians == pytest.approx(0.0, abs=1e-7)
    assert max(report.projector_frobenius_distances) == pytest.approx(0.0, abs=1e-7)


def test_eigenspace_drift_detects_rotation_of_the_degenerate_subspace() -> None:
    depth = build_synthetic_depth_zoa_path(
        _depth_rows(), operator_identity=_identity()
    )
    epsilon = 1e-11
    reference = np.diag([1.0, 1.0 + epsilon, -2.0 - epsilon])
    angle = np.pi / 6.0
    rotate_plane = np.asarray(
        [
            [1.0, 0.0, 0.0],
            [0.0, np.cos(angle), -np.sin(angle)],
            [0.0, np.sin(angle), np.cos(angle)],
        ]
    )
    candidate = rotate_plane @ reference @ rotate_plane.T
    report = analyze_synthetic_eigenspace_drift(
        reference,
        candidate,
        reference_depth_id=depth.path.strata[0].stratum_id,
        candidate_depth_id=depth.path.strata[1].stratum_id,
        depth_path_content_id=depth.path.content_id,
        covariance_id=_identity()["covariance_id"],
        response_id=_identity()["response_id"],
    )
    assert report.maximum_subspace_angle_radians == pytest.approx(angle)
    assert max(report.projector_frobenius_distances) > 0.0


def test_gate_snapshot_and_legacy_curl_preserve_claim_ceiling() -> None:
    directions, distances = _directions_and_distances()
    identity = _identity()
    depth = build_synthetic_depth_zoa_path(
        _depth_rows(), operator_identity=identity
    )
    design = build_cf4_moment_design(directions, distances, identity)
    shear = analyze_synthetic_shear(
        np.diag([2.0, -0.5, -1.5]),
        covariance_id=identity["covariance_id"],
        response_id=identity["response_id"],
    )
    response = analyze_synthetic_response_nullspace(
        [[1.0, 0.0, 1.0], [0.0, 1.0, 1.0]],
        [[1.0, 0.2], [0.2, 1.0]],
        covariance_id=identity["covariance_id"],
        response_id=identity["response_id"],
        parameter_labels=("local", "global", "nuisance"),
        parameter_roles=("LOCAL", "GLOBAL", "NUISANCE"),
    )
    eigenspace = analyze_synthetic_eigenspace_drift(
        np.diag([1.0, 1.0 + 1e-9, -2.0 - 1e-9]),
        np.diag([1.0 + 1e-9, 1.0, -2.0 - 1e-9]),
        reference_depth_id=depth.path.strata[0].stratum_id,
        candidate_depth_id=depth.path.strata[1].stratum_id,
        depth_path_content_id=depth.path.content_id,
        covariance_id=identity["covariance_id"],
        response_id=identity["response_id"],
    )
    source_decision = _weak_source_decision(identity, response)
    assert source_decision.status is SourceSeparationDecisionStatus.WEAKLY_IDENTIFIED
    assert response.response_rank == 2
    assert response.nullity == 1
    assert np.allclose(
        np.asarray([[1.0, 0.0, 1.0], [0.0, 1.0, 1.0]])
        @ np.asarray(response.right_null_basis).T,
        0.0,
        atol=1e-12,
    )
    gates = build_cf4_gate_snapshot(
        design=design,
        depth=depth,
        shear=shear,
        eigenspace_drift=eigenspace,
        response=response,
        source_separation=source_decision,
    )
    assert tuple(gates) == ("G4", "G5", "G6", "G7")
    assert gates["G7"]["family_identification_gate"] == "BLOCKED_PRE_NATIVE_ATLAS"
    assert gates["G7"]["unidentified_direction_count"] == 1
    curl = legacy_wf_curl_selfcheck()
    assert curl["curl_div_ratio"] == pytest.approx(0.0089)
    assert curl["physical_vorticity_claim"] == "FORBIDDEN"
    assert curl["potential_flow_claim"] == "FORBIDDEN"


def test_gate_snapshot_rejects_nonweak_source_decision_and_identity_drift() -> None:
    directions, distances = _directions_and_distances()
    identity = _identity()
    depth = build_synthetic_depth_zoa_path(
        _depth_rows(), operator_identity=identity
    )
    design = build_cf4_moment_design(directions, distances, identity)
    shear = analyze_synthetic_shear(
        np.diag([2.0, -0.5, -1.5]),
        covariance_id=identity["covariance_id"],
        response_id=identity["response_id"],
    )
    response = analyze_synthetic_response_nullspace(
        [[1.0, 0.0, 1.0], [0.0, 1.0, 1.0]],
        [[1.0, 0.2], [0.2, 1.0]],
        covariance_id=identity["covariance_id"],
        response_id=identity["response_id"],
        parameter_labels=("local", "global", "nuisance"),
        parameter_roles=("LOCAL", "GLOBAL", "NUISANCE"),
    )
    eigenspace = analyze_synthetic_eigenspace_drift(
        np.diag([1.0, 1.0 + 1e-9, -2.0 - 1e-9]),
        np.diag([1.0 + 1e-9, 1.0, -2.0 - 1e-9]),
        reference_depth_id=depth.path.strata[0].stratum_id,
        candidate_depth_id=depth.path.strata[1].stratum_id,
        depth_path_content_id=depth.path.content_id,
        covariance_id=identity["covariance_id"],
        response_id=identity["response_id"],
    )
    separable = evaluate_source_separation(
        **{
            **{
                "source_geometry_report_id": identity["estimand_id"],
                "covariance_id": identity["covariance_id"],
                "nuisance_tangent_id": _sha_id("pr291-nuisance"),
                "normalizer_id": response.normalizer_id,
                "normalizer_source_identity": "PR291-SYNTHETIC-DIMENSIONLESS-NORMALIZER",
                "normalizer_coordinate_map_id": _sha_id("pr291-normalizer-map"),
                "parameter_coordinate_units": "dimensionless_beta_c_equals_1",
                "provider_available": True,
                "covariance_supported": True,
                "local_parameter_count": 1,
                "global_parameter_count": 1,
                "local_rank": 1,
                "global_rank": 1,
                "joint_rank": 2,
                "principal_angles_radians": (1.0,),
                "joint_singular_values": (1.0, 0.5),
                "threshold_contract": build_weak_identification_threshold_contract(
                    minimum_principal_angle_radians=0.2,
                    minimum_normalizer_bound_relative_joint_singular_value=0.01,
                ),
            }
        }
    )
    with pytest.raises(Cf4Post275Error, match="G4 requires"):
        build_cf4_gate_snapshot(
            design=design,
            depth=depth,
            shear=shear,
            eigenspace_drift=eigenspace,
            response=response,
            source_separation=separable,
        )

    drifted = _identity()
    drifted["depth_path_id"] = _sha_id("wrong-depth")
    drifted_design = build_cf4_moment_design(directions, distances, drifted)
    with pytest.raises(Cf4Post275Error, match="operator/depth identity"):
        build_cf4_gate_snapshot(
            design=drifted_design,
            depth=depth,
            shear=shear,
            eigenspace_drift=eigenspace,
            response=response,
            source_separation=_weak_source_decision(drifted, response),
        )


def test_nonexecution_receipt_is_content_bound_and_has_no_numbers() -> None:
    decision = build_cf4_activation_decision(repository_root=ROOT)
    receipt = build_cf4_nonexecution_receipt(
        decision=decision,
        source_bindings=_stub_source_bindings(decision),
        generation_identity=_generation_identity(),
    )
    seal = receipt.pop("receipt_content_sha256")
    assert seal == "sha256:" + hashlib.sha256(canonical_json_bytes(receipt)).hexdigest()
    assert receipt["numeric_outputs_written"] == []
    assert receipt["observed_data_executed"] is False
    assert receipt["public_use"] is False
    assert receipt["family_identification_gate"] == "BLOCKED_PRE_NATIVE_ATLAS"


def _load_runner():
    path = ROOT / "scripts/codex_harness/run_pr291_cf4_lane.py"
    spec = importlib.util.spec_from_file_location("pr291_cf4_runner_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_runner_ignores_preloaded_activation_and_identity_modules(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_cf4 = types.ModuleType("common.cf4_observed_lane_activation")
    fake_predecessor = types.ModuleType("common.observed_lane_activation")
    fake_identity = types.ModuleType("common.data_identity")

    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("preloaded module executed")

    fake_cf4.build_cf4_activation_decision = fail_if_called
    fake_cf4.build_cf4_nonexecution_receipt = fail_if_called
    fake_predecessor._load_pr289_identity_module = fail_if_called
    fake_predecessor._validate_pr289_receipt_provenance = fail_if_called
    fake_identity.replay_lane_admission_decision = fail_if_called
    monkeypatch.setitem(sys.modules, "common.cf4_observed_lane_activation", fake_cf4)
    monkeypatch.setitem(sys.modules, "common.observed_lane_activation", fake_predecessor)
    monkeypatch.setitem(sys.modules, "common.data_identity", fake_identity)

    receipt = _load_runner()._build(ROOT)
    assert receipt["terminal"] == "BLOCKED_PREDECESSOR_FINAL_SUCCESS"
    assert receipt["observed_data_executed"] is False


def test_runner_ignores_preloaded_pr290_transaction_module(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    marker: list[str] = []
    fake = types.ModuleType("run_pr290_planck_lane")

    def fake_validate_output_destinations(**_kwargs: object) -> None:
        marker.append("forged_validate_called")

    def fake_atomic_write(output: Path, payload: bytes, **_kwargs: object) -> None:
        marker.append("forged_atomic_write_called")
        output.write_bytes(payload)

    fake._validate_output_destinations = fake_validate_output_destinations
    fake._atomic_write = fake_atomic_write
    fake._encoded = lambda payload: json.dumps(
        payload, sort_keys=True, separators=(",", ":")
    ).encode("ascii")
    fake._tracked_manifest = lambda *_args, **_kwargs: {}
    fake._tracked_paths = lambda *_args, **_kwargs: ()
    monkeypatch.setitem(sys.modules, "run_pr290_planck_lane", fake)

    runner = _load_runner()
    outside = tmp_path / "outside-root.json"
    assert runner._write(root=ROOT, output=outside) == 1
    assert marker == []
    assert not outside.exists()


@pytest.mark.parametrize("member_kind", ("traversal", "symlink"))
def test_runner_safe_archive_extraction_rejects_escape_and_links(
    tmp_path: Path, member_kind: str
) -> None:
    runner = _load_runner()
    stream = BytesIO()
    with tarfile.open(fileobj=stream, mode="w") as archive:
        if member_kind == "traversal":
            data = b"escape"
            member = tarfile.TarInfo("../escape.txt")
            member.size = len(data)
            archive.addfile(member, BytesIO(data))
        else:
            member = tarfile.TarInfo("linked")
            member.type = tarfile.SYMTYPE
            member.linkname = "../escape.txt"
            archive.addfile(member)
    stream.seek(0)
    destination = tmp_path / "extract"
    destination.mkdir()
    with tarfile.open(fileobj=stream, mode="r:") as archive:
        with pytest.raises(RuntimeError, match="unsafe archive member"):
            runner._safe_extract_archive(archive, destination)


@pytest.mark.parametrize("destination_kind", ("symlink", "hardlink", "results"))
def test_runner_refuses_unsafe_destinations_before_payload_generation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, destination_kind: str
) -> None:
    runner = _load_runner()
    output = tmp_path / "receipt.json"
    outside = tmp_path / "outside.json"
    outside.write_text("sentinel", encoding="utf-8")
    if destination_kind == "symlink":
        output.symlink_to(outside)
    elif destination_kind == "hardlink":
        output.hardlink_to(outside)
    else:
        results = tmp_path / runner.OBSERVED_RESULT_DIRECTORY.relative_to(runner.ROOT)
        results.mkdir(parents=True)
    called = False

    def forbidden_build(root: Path):
        nonlocal called
        called = True
        raise AssertionError("payload generation ran before destination preflight")

    monkeypatch.setattr(runner, "_build", forbidden_build)
    assert runner._write(root=tmp_path, output=output) == 1
    assert called is False
    assert outside.read_text(encoding="utf-8") == "sentinel"
