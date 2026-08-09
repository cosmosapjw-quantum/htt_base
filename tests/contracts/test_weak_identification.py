"""PR-283 weak source identification and mandatory open-set abstention."""

from __future__ import annotations

from copy import copy, deepcopy
from dataclasses import replace
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest
import yaml

from common.anchor_geometry import NormalizerKind, NormalizerPurpose, NormalizerSpec
from common.anchored_response_geometry import anchored_numeric_content_id
from common.open_set_response_classes import (
    OpenSetClassificationStatus,
    OpenSetResponseError,
    ResponseClassSourceSemantics,
    ResponseSupportKind,
    SourceSeparationGateStatus,
    build_response_class_manifold,
    build_response_equivalence_report,
    classify_open_set_response,
)
from common.source_separation import (
    SourceSeparationDecision,
    SourceSeparationDecisionStatus,
    SourceSeparationError,
    build_weak_identification_threshold_contract,
    evaluate_source_separation,
)
from common.transfer_registry import TransferSource
from htt.departure.velocity_frame_decomposition import (
    ResponseProviderAvailability,
    ResponseProviderKind,
    SourceHypothesis,
    SourceResponseGeometryStatus,
    VelocityComponent,
    measure_source_response_geometry,
    register_source_response_provider,
)
from htt.statistics.open_set_response_classes import source_separation_gate_from_pr256
from scripts.codex_harness import run_pr283_weak_identification as pr283_runner


ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "docs/research_program/post_pr275/pr283_spec.yaml"
POLICY = ROOT / "docs/research_program/post_pr275/pr283_publication_policy.json"
RECEIPT = ROOT / "docs/generated/pr283_weak_identification_receipt.json"
UNITS = "dimensionless_beta_c_equals_1"


def _id(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("ascii")).hexdigest()


def _thresholds(*, angle: float = 0.2, relative_singular: float = 0.01):
    return build_weak_identification_threshold_contract(
        minimum_principal_angle_radians=angle,
        minimum_normalizer_bound_relative_joint_singular_value=relative_singular,
        parameter_coordinate_units=UNITS,
    )


def _provider(
    hypothesis: SourceHypothesis,
    response: np.ndarray,
    *,
    provider_id: str,
):
    local = hypothesis is SourceHypothesis.LOCAL_BOOST
    return register_source_response_provider(
        provider_id=provider_id,
        hypothesis=hypothesis,
        velocity_component=(VelocityComponent.BETA_MO if local else VelocityComponent.BETA_RM),
        provider_kind=ResponseProviderKind.ANALYTIC,
        availability=ResponseProviderAvailability.AVAILABLE,
        observable_labels=("obs-x", "obs-y"),
        parameter_labels=(("beta_MO_amplitude",) if local else ("beta_RM_amplitude",)),
        response=response,
        transfer_id=_id("pr283-transfer-none"),
        transfer_source=TransferSource.NONE,
        basis="registered synthetic basis",
        epoch_window="registered synthetic window",
        assumptions=("first-order analytic response",),
        caveats=("hypothesis-only response",),
    )


def _normalizer(*, global_scale: float = 1.0) -> NormalizerSpec:
    return NormalizerSpec(
        normalizer_id="pr283-dimensionless-beta-normalizer",
        kind=NormalizerKind.MES_ANCHORED,
        purposes=(NormalizerPurpose.RESPONSE_CONDITIONING,),
        coordinate_labels=("beta_MO_amplitude", "beta_RM_amplitude"),
        coordinate_map=((1.0, 0.0), (0.0, global_scale)),
        source_identity="PR283-DIMENSIONLESS-BETA-C-EQUALS-ONE",
        assumptions=("dimensionless beta coordinates with c equals one",),
    )


def _source_fixture(
    *,
    angle: float = math.pi / 2.0,
    global_amplitude: float = 1.0,
    normalizer_global_scale: float = 1.0,
):
    covariance = np.eye(2)
    local_response = np.asarray([[1.0], [0.0]], dtype=float)
    global_response = global_amplitude * np.asarray(
        [[math.cos(angle)], [math.sin(angle)]], dtype=float
    )
    local_id = _id("pr283-local-provider")
    global_id = _id("pr283-global-provider")
    normalizer = _normalizer(global_scale=normalizer_global_scale)
    report = measure_source_response_geometry(
        local_provider=_provider(
            SourceHypothesis.LOCAL_BOOST,
            local_response,
            provider_id=local_id,
        ),
        global_provider=_provider(
            SourceHypothesis.GLOBAL_TILT,
            global_response,
            provider_id=global_id,
        ),
        covariance=covariance,
        normalizer=normalizer,
        covariance_id=anchored_numeric_content_id(covariance),
        mask_id=_id("pr283-mask"),
        separation_threshold_radians=0.2,
    )
    classes = (
        build_response_class_manifold(
            class_id="response-class-local",
            support_kind=ResponseSupportKind.FINITE_ANALYTIC_SUPPORT,
            provider_id=local_id,
            observable_labels=("obs-x", "obs-y"),
            convention_id=_id("pr283-convention"),
            nuisance_policy_id=_id("pr283-nuisance-none"),
            support_nodes=[[-3.0, 0.0]],
            transfer_source=TransferSource.NONE,
            source_semantics=ResponseClassSourceSemantics.LOCAL_BOOST,
            source_response_id=anchored_numeric_content_id(local_response),
        ),
        build_response_class_manifold(
            class_id="response-class-global",
            support_kind=ResponseSupportKind.FINITE_ANALYTIC_SUPPORT,
            provider_id=global_id,
            observable_labels=("obs-x", "obs-y"),
            convention_id=_id("pr283-convention"),
            nuisance_policy_id=_id("pr283-nuisance-none"),
            support_nodes=[[3.0, 0.0]],
            transfer_source=TransferSource.NONE,
            source_semantics=ResponseClassSourceSemantics.GLOBAL_TILT,
            source_response_id=anchored_numeric_content_id(global_response),
        ),
    )
    equivalence = build_response_equivalence_report(
        classes=classes,
        covariance=covariance,
        nuisance_tangent=None,
        equivalence_squared_distance_tolerance=0.1,
        absolute_tolerance=1.0e-12,
        relative_tolerance=1.0e-12,
    )
    gate = source_separation_gate_from_pr256(
        report,
        classes=classes,
        covariance=covariance,
        nuisance_tangent=None,
        normalizer=normalizer,
        threshold_contract=_thresholds(),
    )
    return report, classes, equivalence, gate, covariance


def _classify(
    classes,
    equivalence,
    gate,
    covariance,
    *,
    observation=(-3.0, 0.0),
):
    return classify_open_set_response(
        observation=observation,
        classes=classes,
        equivalence_report=equivalence,
        covariance=covariance,
        nuisance_tangent=None,
        unknown_squared_distance_threshold=4.0,
        decision_squared_margin=0.5,
        covariance_null_tolerance=1.0e-10,
        absolute_tolerance=1.0e-12,
        relative_tolerance=1.0e-12,
        source_separation_gate=gate,
    )


def test_spec_freezes_g4_claim_and_representation_boundary() -> None:
    spec = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    assert spec["pr_id"] == "PR-283"
    assert spec["gate"]["gate_id"] == "G4"
    assert spec["change_set_id"] == policy["change_set_id"]
    assert spec["publication_group_id"] == policy["publication_group_id"]
    assert spec["claim_tier"] == "diagnostic_only"
    assert spec["transfer_source"] == "none"
    assert spec["observed_data_executed"] is spec["public_use"] is False
    assert spec["family_identification_gate"] == "BLOCKED_PRE_NATIVE_ATLAS"
    assert "not invariant" in spec["threshold_contract"]["representation_boundary"]
    assert "cannot contain more entries" in spec["threshold_contract"][
        "singular_value_cardinality"
    ]
    assert "before response-equivalence" in spec["runtime_contract"][
        "weak_gate_precedence"
    ]
    assert spec["mathematical_boundary"]["source_registry_status"] == (
        "ORACLE_VERIFIED"
    )
    assert spec["mathematical_boundary"]["source_proof_adjudication_status"] == (
        "NOT_ADJUDICATED"
    )
    mutation_ids = {row["mutation_id"] for row in spec["mutation_registry"]}
    assert {
        "MU283-THRESHOLD-OMISSION",
        "MU283-SOURCE-REPORT-REPLAY-DRIFT",
    } <= mutation_ids


def test_source_layout_policy_commands_use_the_portable_pr283_runner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, ...]] = []

    def record(paths: tuple[str, ...]) -> int:
        calls.append(paths)
        return 0

    monkeypatch.setattr(pr283_runner, "_pytest", record)
    assert pr283_runner.main(["caller-migrations"]) == 0
    assert calls.pop() == (
        "tests/pr_cards/test_pr_258_open_set_response_classes.py",
        "tests/contracts/test_anisotropy_type_report.py",
        "tests/integration/test_vector_tensor_blind_synthetic.py",
    )
    assert pr283_runner.main(["harness-portability"]) == 0
    assert calls.pop() == ("tests/contracts/test_harness_profiles_v4.py",)

    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    commands = {row["id"]: row["argv"] for row in policy["required_commands"]}
    assert commands["pr283-source-replay-caller-migrations"][-1] == (
        "caller-migrations"
    )
    assert commands["pr283-harness-portability"][-1] == "harness-portability"


def test_full_rank_small_angle_is_explicit_weak_identification() -> None:
    report, classes, equivalence, gate, covariance = _source_fixture(angle=0.1)
    assert report.status is SourceResponseGeometryStatus.SUM_ONLY
    assert report.local_rank == report.global_rank == 1
    assert report.joint_rank == 2
    assert report.direct_sum is True
    assert gate.status is SourceSeparationGateStatus.WEAKLY_IDENTIFIED
    assert gate.source_separation_decision is not None
    assert (
        gate.source_separation_decision.status
        is SourceSeparationDecisionStatus.WEAKLY_IDENTIFIED
    )
    classified = _classify(classes, equivalence, gate, covariance)
    assert classified.status is OpenSetClassificationStatus.TYPE_UNIDENTIFIED
    assert classified.candidate_class_id is None
    assert classified.returned_equivalence_class == ("response-class-local",)
    assert all(
        value.startswith("response-class-")
        for value in classified.returned_equivalence_class
    )


def test_weak_identification_precedes_unknown_distance_abstention() -> None:
    _, classes, equivalence, gate, covariance = _source_fixture(angle=0.1)
    classified = _classify(
        classes,
        equivalence,
        gate,
        covariance,
        observation=(100.0, 0.0),
    )
    assert classified.status is OpenSetClassificationStatus.TYPE_UNIDENTIFIED
    assert classified.candidate_class_id is None
    assert classified.returned_equivalence_class == ("response-class-global",)


def test_weak_identification_precedes_response_equivalence_label() -> None:
    _, classes, _, gate, covariance = _source_fixture(angle=0.1)
    equivalence = build_response_equivalence_report(
        classes=classes,
        covariance=covariance,
        nuisance_tangent=None,
        equivalence_squared_distance_tolerance=40.0,
        absolute_tolerance=1.0e-12,
        relative_tolerance=1.0e-12,
    )
    classified = _classify(classes, equivalence, gate, covariance)
    assert classified.status is OpenSetClassificationStatus.TYPE_UNIDENTIFIED
    assert classified.candidate_class_id is None
    assert classified.returned_equivalence_class == equivalence.components[0]


def test_full_rank_small_normalizer_bound_singular_value_abstains() -> None:
    report, classes, equivalence, gate, covariance = _source_fixture(
        angle=math.pi / 2.0,
        global_amplitude=0.005,
    )
    assert report.status is SourceResponseGeometryStatus.SEPARABLE_CANDIDATE
    assert gate.status is SourceSeparationGateStatus.WEAKLY_IDENTIFIED
    assert (
        gate.source_separation_decision.minimum_relative_joint_singular_value
        == pytest.approx(0.005)
    )
    assert _classify(classes, equivalence, gate, covariance).candidate_class_id is None


def test_rank_deficient_direct_sum_failure_remains_sum_only() -> None:
    report, classes, equivalence, gate, covariance = _source_fixture(angle=0.0)
    assert report.local_rank == report.global_rank == 1
    assert report.joint_rank == 1
    assert report.direct_sum is False
    assert gate.status is SourceSeparationGateStatus.SUM_ONLY
    assert _classify(classes, equivalence, gate, covariance).candidate_class_id is None


def test_well_separated_full_rank_case_remains_candidate_eligible() -> None:
    report, classes, equivalence, gate, covariance = _source_fixture()
    assert report.status is SourceResponseGeometryStatus.SEPARABLE_CANDIDATE
    assert gate.status is SourceSeparationGateStatus.SEPARABLE_CANDIDATE
    classified = _classify(classes, equivalence, gate, covariance)
    assert classified.status is OpenSetClassificationStatus.RESPONSE_CLASS_CANDIDATE
    assert classified.candidate_class_id == "response-class-local"


def test_threshold_equality_is_weak_and_content_addressed() -> None:
    contract = _thresholds()
    decision = evaluate_source_separation(
        source_geometry_report_id=_id("report"),
        covariance_id=_id("covariance"),
        nuisance_tangent_id=_id("nuisance"),
        normalizer_id="registered-normalizer",
        normalizer_source_identity="registered dimensionless beta convention",
        normalizer_coordinate_map_id=_id("normalizer-map"),
        parameter_coordinate_units=UNITS,
        provider_available=True,
        covariance_supported=True,
        local_parameter_count=1,
        global_parameter_count=1,
        local_rank=1,
        global_rank=1,
        joint_rank=2,
        principal_angles_radians=(0.2,),
        joint_singular_values=(1.0, 0.02),
        threshold_contract=contract,
    )
    assert decision.status is SourceSeparationDecisionStatus.WEAKLY_IDENTIFIED
    assert decision.principal_angles_content_id.startswith("sha256:")
    assert decision.joint_singular_values_content_id.startswith("sha256:")
    assert decision.decision_id.startswith("sha256:")


def test_joint_singular_value_count_cannot_exceed_parameter_dimension() -> None:
    with pytest.raises(SourceSeparationError, match="singular-value count"):
        evaluate_source_separation(
            source_geometry_report_id=_id("report-cardinality"),
            covariance_id=_id("covariance-cardinality"),
            nuisance_tangent_id=_id("nuisance-cardinality"),
            normalizer_id="registered-normalizer",
            normalizer_source_identity=(
                "registered dimensionless beta convention"
            ),
            normalizer_coordinate_map_id=_id("normalizer-map-cardinality"),
            parameter_coordinate_units=UNITS,
            provider_available=True,
            covariance_supported=True,
            local_parameter_count=1,
            global_parameter_count=1,
            local_rank=1,
            global_rank=1,
            joint_rank=2,
            principal_angles_radians=(math.pi / 2.0,),
            joint_singular_values=(1.0, 0.5, 0.1),
            threshold_contract=_thresholds(),
        )


def test_provider_covariance_component_and_joint_rank_precedence() -> None:
    base = {
        "source_geometry_report_id": _id("ladder-report"),
        "covariance_id": _id("ladder-covariance"),
        "nuisance_tangent_id": _id("ladder-nuisance"),
        "normalizer_id": "registered-normalizer",
        "normalizer_source_identity": "registered dimensionless beta convention",
        "normalizer_coordinate_map_id": _id("ladder-normalizer-map"),
        "parameter_coordinate_units": UNITS,
        "provider_available": True,
        "covariance_supported": True,
        "local_parameter_count": 1,
        "global_parameter_count": 1,
        "local_rank": 1,
        "global_rank": 1,
        "joint_rank": 2,
        "principal_angles_radians": (math.pi / 2.0,),
        "joint_singular_values": (1.0, 1.0),
        "threshold_contract": _thresholds(),
    }
    missing = evaluate_source_separation(
        **{
            **base,
            "provider_available": False,
            "covariance_supported": False,
            "local_rank": None,
            "global_rank": None,
            "joint_rank": None,
            "principal_angles_radians": (),
            "joint_singular_values": (),
        }
    )
    unsupported = evaluate_source_separation(
        **{**base, "covariance_supported": False}
    )
    component_deficient = evaluate_source_separation(
        **{**base, "local_rank": 0, "joint_rank": 1}
    )
    sum_only = evaluate_source_separation(**{**base, "joint_rank": 1})
    assert missing.status is SourceSeparationDecisionStatus.MISSING_RESPONSE_PROVIDER
    assert unsupported.status is SourceSeparationDecisionStatus.NON_IDENTIFIED
    assert component_deficient.status is SourceSeparationDecisionStatus.NON_IDENTIFIED
    assert sum_only.status is SourceSeparationDecisionStatus.SUM_ONLY


def test_normalizer_map_identity_exposes_representation_dependence() -> None:
    baseline, _, _, baseline_gate, _ = _source_fixture()
    scaled, _, _, scaled_gate, _ = _source_fixture(
        normalizer_global_scale=0.001
    )
    assert baseline.minimum_principal_angle_radians == pytest.approx(
        scaled.minimum_principal_angle_radians
    )
    assert (
        baseline.normalizer_coordinate_map_id
        != scaled.normalizer_coordinate_map_id
    )
    assert baseline.joint_singular_values != scaled.joint_singular_values
    assert (
        baseline_gate.status
        is SourceSeparationGateStatus.SEPARABLE_CANDIDATE
    )
    assert scaled_gate.status is SourceSeparationGateStatus.WEAKLY_IDENTIFIED
    assert (
        baseline_gate.source_separation_decision.decision_id
        != scaled_gate.source_separation_decision.decision_id
    )


def test_threshold_must_match_the_geometry_measurement() -> None:
    report, classes, _, _, covariance = _source_fixture(angle=0.1)
    with pytest.raises(OpenSetResponseError, match="threshold"):
        source_separation_gate_from_pr256(
            report,
            classes=classes,
            covariance=covariance,
            nuisance_tangent=None,
            normalizer=_normalizer(),
            threshold_contract=_thresholds(angle=0.1),
        )


def test_source_geometry_is_replayed_before_pr283_projection() -> None:
    report, classes, _, _, covariance = _source_fixture(angle=0.1)
    mutant = copy(report)
    object.__setattr__(mutant, "principal_angles_radians", (math.pi / 2.0,))
    object.__setattr__(
        mutant,
        "minimum_principal_angle_radians",
        math.pi / 2.0,
    )

    with pytest.raises(OpenSetResponseError, match="failed exact replay"):
        source_separation_gate_from_pr256(
            mutant,
            classes=classes,
            covariance=covariance,
            nuisance_tangent=None,
            normalizer=_normalizer(),
            threshold_contract=_thresholds(),
        )


def test_pr283_threshold_contract_cannot_be_omitted() -> None:
    report, classes, _, _, covariance = _source_fixture(
        angle=math.pi / 2.0,
        global_amplitude=0.005,
    )

    with pytest.raises(OpenSetResponseError, match="threshold_contract"):
        source_separation_gate_from_pr256(
            report,
            classes=classes,
            covariance=covariance,
            nuisance_tangent=None,
            normalizer=_normalizer(),
            threshold_contract=None,
        )


def test_source_separation_decision_cannot_be_directly_forged() -> None:
    with pytest.raises(SourceSeparationError, match="factory-derived"):
        SourceSeparationDecision(
            status=SourceSeparationDecisionStatus.SEPARABLE_CANDIDATE,
            source_geometry_report_id=_id("forged"),
            covariance_id=_id("covariance"),
            nuisance_tangent_id=_id("nuisance"),
            normalizer_id="normalizer",
            normalizer_source_identity="source",
            normalizer_coordinate_map_id=_id("normalizer-map"),
            parameter_coordinate_units=UNITS,
            provider_available=True,
            covariance_supported=True,
            local_parameter_count=1,
            global_parameter_count=1,
            local_rank=1,
            global_rank=1,
            joint_rank=2,
            principal_angles_radians=(math.pi / 2.0,),
            principal_angles_content_id=_id("angles"),
            joint_singular_values=(1.0, 1.0),
            joint_singular_values_content_id=_id("singular"),
            minimum_principal_angle_radians=math.pi / 2.0,
            minimum_relative_joint_singular_value=1.0,
            threshold_contract=_thresholds(),
        )


def test_decision_and_report_identity_drift_fail_closed() -> None:
    _, _, _, gate, _ = _source_fixture(angle=0.1)
    decision = gate.source_separation_decision
    with pytest.raises(SourceSeparationError):
        replace(decision, principal_angles_content_id=_id("forged-angles"))
    with pytest.raises(SourceSeparationError):
        replace(decision, joint_singular_values_content_id=_id("forged-singular"))
    with pytest.raises(SourceSeparationError):
        replace(decision, normalizer_coordinate_map_id=_id("forged-normalizer"))


def test_generated_receipt_replays_and_records_complete_mutation_evidence() -> None:
    subprocess.run(
        [sys.executable, "-B", "scripts/codex_harness/run_pr283_weak_identification.py", "check"],
        cwd=ROOT,
        check=True,
    )
    payload = json.loads(RECEIPT.read_text(encoding="utf-8"))
    spec = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    assert payload["terminal"]["g4_outcome"] == "PASS_WEAK_IDENTIFICATION_ABSTENTION"
    assert len(payload["mutations"]) == len(spec["mutation_registry"]) == 10
    assert all(
        row["executed"] and row["activated"] and row["killed"]
        for row in payload["mutations"]
    )
    assert payload["claim_tier"] == "diagnostic_only"
    assert payload["observed_data_executed"] is payload["public_use"] is False
    assert payload["family_identification_gate"] == "BLOCKED_PRE_NATIVE_ATLAS"
    assert payload["mathematical_boundary"]["source_oracle"][
        "registry_status"
    ] == "ORACLE_VERIFIED"
    conditional = payload["mathematical_boundary"]["conditional_algebra"]
    assert conditional["obligation_id"] == "VT-T12"
    assert conditional["aggregate_cas_verdict"] == "CAS_4AXIS_PASS"
    assert conditional["source_proof_adjudication_status"] == "NOT_ADJUDICATED"
    assert payload["mathematical_boundary"]["pr283_effect"] == (
        "runtime_execution_without_proof_promotion"
    )
    unsigned = dict(payload)
    recorded = unsigned.pop("artifact_content_sha256")
    assert recorded == hashlib.sha256(
        json.dumps(
            unsigned,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")
    ).hexdigest()


def test_runner_refuses_hardlinked_output_before_build(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    generated = tmp_path / "docs/generated"
    generated.mkdir(parents=True)
    outside = tmp_path / "outside.json"
    outside.write_text("preserve\n", encoding="utf-8")
    destination = generated / "receipt.json"
    destination.hardlink_to(outside)
    monkeypatch.setattr(pr283_runner, "ROOT", tmp_path)
    monkeypatch.setattr(pr283_runner, "OUTPUT", destination)

    def must_not_build():
        raise AssertionError("builder ran before destination preflight")

    monkeypatch.setattr(pr283_runner, "_build_artifact", must_not_build)
    assert pr283_runner.main(["build"]) == 1
    assert outside.read_text(encoding="utf-8") == "preserve\n"


@pytest.mark.parametrize(
    "defect",
    ("omitted", "duplicate", "reordered", "inconsistent_flags"),
)
def test_mutation_result_completeness_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
    defect: str,
) -> None:
    original = pr283_runner._run_mutations

    def defective(contexts):
        rows = deepcopy(original(contexts))
        if defect == "omitted":
            return rows[:-1]
        if defect == "duplicate":
            return [rows[0], rows[0], *rows[2:]]
        if defect == "reordered":
            return [rows[1], rows[0], *rows[2:]]
        for row in rows:
            row["executed"] = False
            row["activated"] = False
            row["killed"] = True
        return rows

    monkeypatch.setattr(pr283_runner, "_run_mutations", defective)
    artifact = pr283_runner._build_artifact()
    assert artifact["terminal"]["g4_outcome"] == pr283_runner.BLOCK_TOKEN
    assert artifact["terminal"]["reasons"]
