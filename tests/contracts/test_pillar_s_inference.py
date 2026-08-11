"""PR-272 preregistered Pillar-S inference-validation contracts."""

from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest
import yaml

from common.conditional_exceedance import (
    ConditionalExceedanceError,
    ConditioningSource,
    ExceedanceLane,
    SamplingLaw,
    build_likelihood_objective,
    build_sampling_draws,
    build_sampling_law_spec,
)
from common.vector_tensor_statistical_inference import (
    CLAIM_CEILING,
    EXPECTED_SPEC_SHA256,
    EXPECTED_VT_IDS,
    ModelCandidate,
    PillarSInferenceError,
    SourceDisposition,
    ValidationStatus,
    build_joint_anchor_law,
    build_mio_depth_cross_check,
    calibrate_split_max_statistic,
    derive_registered_seed,
    evaluate_depth_local_global,
    evaluate_depth_multiplicity,
    evaluate_joint_anchor_coverage,
    evaluate_matched_counterpair_power,
    evaluate_open_set_validation,
    evaluate_registered_composition,
    evaluate_weak_identification,
    joint_fieller_interval,
    load_pillar_s_inference_registry,
    load_preregistered_design,
    require_simultaneous_control,
    resolve_preregistered_frozen_input,
)


ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "docs/research_program/vector_tensor/pr272_spec.yaml"
REGISTRY = ROOT / (
    "docs/research_program/vector_tensor/proofs/"
    "PILLAR_S_INFERENCE_VALIDATION_V1.yaml"
)
BACKLOG = ROOT / "docs/codex_handoff/pr_backlog.yaml"
STATUS = ROOT / "docs/codex_handoff/pr_status.yaml"


@pytest.fixture(scope="module")
def design():
    return load_preregistered_design(ROOT)


@pytest.fixture(scope="module")
def registry():
    return load_pillar_s_inference_registry(ROOT)


@pytest.fixture(scope="module")
def raw_results():
    return yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))[
        "validation_results"
    ]


def test_spec_is_frozen_before_results_and_dependency_open(design) -> None:
    backlog = yaml.safe_load(BACKLOG.read_text(encoding="utf-8"))
    status = yaml.safe_load(STATUS.read_text(encoding="utf-8"))
    card = next(card for card in backlog["prs"] if card["id"] == "PR-272")
    assert design["schema"] == "htt.pr272.pillar_s_inference.spec.v1"
    assert design["frozen_before_result_inspection"] is True
    assert design["design_revision"] == 3
    assert design["revision_frozen_before_rerun"] is True
    assert design["dependencies"] == ["PR-271"]
    assert card["depends"] == ["PR-271"]
    assert card["owner"] == "HTT"
    assert set(card["contributors"]) == {"COMMON", "MIO"}
    assert "PR-271" in status["completed"]
    assert set(design["selection"]["vt_inference_ids"]) == EXPECTED_VT_IDS
    assert design["claim_ceiling"] == CLAIM_CEILING
    assert design["observed_data_execution"] == "forbidden"


def test_preregistration_bytes_and_input_hashes_are_load_bearing(
    design, tmp_path: Path
) -> None:
    assert EXPECTED_SPEC_SHA256 == (
        "4ab978cf971e565dd6a598bd795249555a717aefa8f6c89b26727fdf58f7f9a2"
    )
    for name, record in design["frozen_inputs"].items():
        source = resolve_preregistered_frozen_input(ROOT, name, record)
        assert (
            hashlib.sha256(source.read_bytes()).hexdigest()
            == record["sha256"]
        )
    drifted_root = tmp_path / "repo"
    path = drifted_root / "docs/research_program/vector_tensor/pr272_spec.yaml"
    path.parent.mkdir(parents=True)
    path.write_bytes(SPEC.read_bytes() + b"\n")
    with pytest.raises(PillarSInferenceError, match="bytes drifted"):
        load_preregistered_design(drifted_root)


def test_pr282_relocation_preserves_pr272_frozen_foundations(design) -> None:
    record = design["frozen_inputs"]["pr271_statistical_foundations"]
    current = ROOT / record["path"]
    assert hashlib.sha256(current.read_bytes()).hexdigest() != record["sha256"]

    resolved = resolve_preregistered_frozen_input(
        ROOT,
        "pr271_statistical_foundations",
        record,
    )
    assert resolved == ROOT / (
        "docs/research_program/vector_tensor/frozen_sources/"
        "pr272_vector_tensor_statistical_foundations.py"
    )
    assert hashlib.sha256(resolved.read_bytes()).hexdigest() == record["sha256"]

    relocation = json.loads(
        (
            ROOT
            / "docs/research_program/vector_tensor/integration/"
            "PR282_PR272_V1_RELOCATION.json"
        ).read_text(encoding="utf-8")
    )
    assert relocation == {
        "schema": "htt.pr282.frozen_source_relocation.v1",
        "relocation_id": "PR282-PR272-STATISTICAL-FOUNDATIONS-V1",
        "source_pr": "PR-272",
        "successor_pr": "PR-282",
        "entries": [
            {
                "frozen_input": "pr271_statistical_foundations",
                "original_path": record["path"],
                "relocated_path": (
                    "docs/research_program/vector_tensor/frozen_sources/"
                    "pr272_vector_tensor_statistical_foundations.py"
                ),
                "sha256": record["sha256"],
                "allowed_use": "exact historical PR-272 replay only",
                "caveat": (
                    "PR-282 exact-sign hardening is the current implementation; "
                    "this relocation cannot promote or reseal the PR-272 result"
                ),
            }
        ],
    }


@pytest.mark.parametrize(
    ("field", "value"),
    [
        (
            "relocated_path",
            "docs/research_program/vector_tensor/frozen_sources/duplicate.py",
        ),
        ("caveat", "historical replay"),
    ],
)
def test_pr282_relocation_rejects_weakened_binding(
    design,
    tmp_path: Path,
    field: str,
    value: str,
) -> None:
    record = design["frozen_inputs"]["pr271_statistical_foundations"]
    repo = tmp_path / "repo"
    original = repo / record["path"]
    original.parent.mkdir(parents=True)
    original.write_text("successor bytes\n", encoding="utf-8")

    frozen = repo / (
        "docs/research_program/vector_tensor/frozen_sources/"
        "pr272_vector_tensor_statistical_foundations.py"
    )
    frozen.parent.mkdir(parents=True)
    canonical_frozen = ROOT / (
        "docs/research_program/vector_tensor/frozen_sources/"
        "pr272_vector_tensor_statistical_foundations.py"
    )
    frozen.write_bytes(canonical_frozen.read_bytes())

    manifest_source = ROOT / (
        "docs/research_program/vector_tensor/integration/"
        "PR282_PR272_V1_RELOCATION.json"
    )
    manifest = json.loads(manifest_source.read_text(encoding="utf-8"))
    manifest["entries"][0][field] = value
    if field == "relocated_path":
        duplicate = repo / value
        duplicate.parent.mkdir(parents=True, exist_ok=True)
        duplicate.write_bytes(canonical_frozen.read_bytes())
    manifest_path = repo / manifest_source.relative_to(ROOT)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(PillarSInferenceError, match="relocation binding drifted"):
        resolve_preregistered_frozen_input(
            repo,
            "pr271_statistical_foundations",
            record,
        )


def test_pr283_relocation_preserves_pr272_frozen_open_set_response(design) -> None:
    record = design["frozen_inputs"]["open_set_response"]
    current = ROOT / record["path"]
    assert hashlib.sha256(current.read_bytes()).hexdigest() != record["sha256"]

    resolved = resolve_preregistered_frozen_input(
        ROOT,
        "open_set_response",
        record,
    )
    expected_path = ROOT / (
        "docs/research_program/vector_tensor/frozen_sources/"
        "pr272_open_set_response_classes.py"
    )
    assert resolved == expected_path
    assert hashlib.sha256(resolved.read_bytes()).hexdigest() == record["sha256"]

    relocation = json.loads(
        (
            ROOT
            / "docs/research_program/vector_tensor/integration/"
            "PR283_PR272_OPEN_SET_V1_RELOCATION.json"
        ).read_text(encoding="utf-8")
    )
    assert relocation == {
        "schema": "htt.pr283.frozen_source_relocation.v1",
        "relocation_id": "PR283-PR272-OPEN-SET-RESPONSE-V1",
        "source_pr": "PR-272",
        "successor_pr": "PR-283",
        "entries": [
            {
                "frozen_input": "open_set_response",
                "original_path": record["path"],
                "relocated_path": (
                    "docs/research_program/vector_tensor/frozen_sources/"
                    "pr272_open_set_response_classes.py"
                ),
                "sha256": record["sha256"],
                "allowed_use": "exact historical PR-272 replay only",
                "caveat": (
                    "PR-283 weak-identification precedence is the current "
                    "implementation; this relocation cannot promote or reseal "
                    "the PR-272 result"
                ),
            }
        ],
    }


@pytest.mark.parametrize(
    ("field", "value"),
    [
        (
            "relocated_path",
            "docs/research_program/vector_tensor/frozen_sources/duplicate.py",
        ),
        ("caveat", "historical replay"),
    ],
)
def test_pr283_relocation_rejects_weakened_binding(
    design,
    tmp_path: Path,
    field: str,
    value: str,
) -> None:
    record = design["frozen_inputs"]["open_set_response"]
    repo = tmp_path / "repo"
    original = repo / record["path"]
    original.parent.mkdir(parents=True)
    original.write_text("successor bytes\n", encoding="utf-8")

    frozen_relative = (
        "docs/research_program/vector_tensor/frozen_sources/"
        "pr272_open_set_response_classes.py"
    )
    frozen = repo / frozen_relative
    frozen.parent.mkdir(parents=True)
    canonical_frozen = ROOT / frozen_relative
    frozen.write_bytes(canonical_frozen.read_bytes())

    manifest_source = ROOT / (
        "docs/research_program/vector_tensor/integration/"
        "PR283_PR272_OPEN_SET_V1_RELOCATION.json"
    )
    manifest = json.loads(manifest_source.read_text(encoding="utf-8"))
    manifest["entries"][0][field] = value
    if field == "relocated_path":
        duplicate = repo / value
        duplicate.parent.mkdir(parents=True, exist_ok=True)
        duplicate.write_bytes(canonical_frozen.read_bytes())
    manifest_path = repo / manifest_source.relative_to(ROOT)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(PillarSInferenceError, match="relocation binding drifted"):
        resolve_preregistered_frozen_input(
            repo,
            "open_set_response",
            record,
        )


def test_registry_has_exact_nine_rows_without_source_promotion(registry) -> None:
    assert {row.theorem_id for row in registry.records} == EXPECTED_VT_IDS
    assert len(registry.records) == 9
    assert all(
        row.evidence_grade == "SIMULATION_DIAGNOSTIC"
        for row in registry.records
    )
    assert all(row.claim_ceiling == CLAIM_CEILING for row in registry.records)
    assert registry.record("VT-S14").source_disposition is (
        SourceDisposition.PROGRAM_OBLIGATION_RETAINED
    )
    assert all(
        row.source_disposition
        is SourceDisposition.CONDITIONAL_PROGRAM_RETAINED
        for row in registry.records
        if row.theorem_id != "VT-S14"
    )
    assert registry.observed_data_used is False
    assert registry.source_status_promoted is False
    with pytest.raises(PillarSInferenceError, match="not an accepted proof"):
        registry.reject_raw_proof_count(9)


def test_registry_generator_is_deterministic() -> None:
    subprocess.run(
        [
            sys.executable,
            "-B",
            str(
                ROOT
                / "scripts/codex_harness/"
                "build_pr272_pillar_s_inference.py"
            ),
            "--check",
        ],
        cwd=ROOT,
        check=True,
    )


@pytest.mark.parametrize(
    ("mutation", "value"),
    [
        ("source_status_promoted", True),
        ("observed_data_used", True),
        ("raw_count_publication", "ALLOWED"),
    ],
)
def test_registry_hostile_top_level_mutations_fail_closed(
    tmp_path: Path, mutation: str, value: object
) -> None:
    payload = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    payload[mutation] = value
    path = tmp_path / f"{mutation}.yaml"
    path.write_text(
        yaml.safe_dump(payload, sort_keys=False), encoding="utf-8"
    )
    with pytest.raises(PillarSInferenceError, match="registry bytes drifted"):
        load_pillar_s_inference_registry(ROOT, path)


def test_registered_results_preserve_all_required_failures(raw_results) -> None:
    assert (
        raw_results["VT-S3"]["correct"]["status"]
        == ValidationStatus.VALIDATED_REGISTERED_SYNTHETIC.value
    )
    assert (
        raw_results["VT-S3"]["misspecified_covariance_negative_control"][
            "status"
        ]
        == ValidationStatus.FAILED_MISSPECIFIED_COVARIANCE.value
    )
    assert raw_results["VT-S3"]["misspecified_failure_preserved"] is True
    assert raw_results["VT-S5"]["registered_failure_map"] == []
    assert len(raw_results["VT-S5"]["adversarial_failure_map"]) == 1
    assert raw_results["VT-S6"]["marginal_only_mutation"] == "REFUSED"
    assert raw_results["VT-S9"]["unadjusted_failure_preserved"] is True
    assert (
        raw_results["VT-S10"]["weak"]["status"]
        == ValidationStatus.ABSTAIN_WEAK_IDENTIFICATION.value
    )
    assert (
        raw_results["VT-S11"]["rank_loss"]["status"]
        == ValidationStatus.ABSTAIN_NON_IDENTIFIED.value
    )
    assert raw_results["SBC-HTT-COMPUTATION"]["all_misspecified_fail"] is True


def test_seed_family_and_every_derived_stream_are_recorded() -> None:
    payload = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    receipt = payload["random_stream_receipt"]
    assert receipt["registered_seed_family"] == [
        272003,
        272005,
        272007,
        272009,
        272011,
    ]
    assert len(receipt["derived_streams"]) == 36
    assert receipt["seed_family_load_bearing"] is True
    assert all(
        isinstance(value, int) and 0 <= value < 2**63
        for value in receipt["derived_streams"].values()
    )


def test_every_registered_seed_family_member_is_execution_load_bearing(
    design,
) -> None:
    stream = design["preregistration"]["random_stream"]
    registered = tuple(stream["seed_family"])
    cells = (
        ("VT-S3", "calibration"),
        ("VT-S5-0", "registered-coverage"),
        ("PR272-SBC", "calibrated"),
        ("VT-S14", "global"),
    )
    baseline = tuple(
        derive_registered_seed(
            stream["master_seed"], registered, cell, family
        )
        for cell, family in cells
    )
    for index in range(len(registered)):
        mutated = list(registered)
        mutated[index] += 1_000_000 + index
        changed = tuple(
            derive_registered_seed(
                stream["master_seed"], mutated, cell, family
            )
            for cell, family in cells
        )
        assert all(left != right for left, right in zip(baseline, changed))


def test_split_max_q_calibration_separates_covariance_identity() -> None:
    calibration = np.asarray(
        [[-2.0], [-1.5], [-1.0], [-0.5], [0.0], [0.5], [1.0], [1.5], [2.0]]
    )
    evaluation = np.asarray([[-1.0], [0.0], [1.0], [1.9]])
    report = calibrate_split_max_statistic(
        calibration,
        evaluation,
        alpha=0.2,
        family_confidence=0.90,
        retain_lower_bound=0.0,
        calibration_covariance_id="C",
        evaluation_covariance_id="C",
    )
    assert report.status is ValidationStatus.VALIDATED_REGISTERED_SYNTHETIC
    assert report.critical_order == 8
    assert report.simultaneous_coverage == 1.0
    require_simultaneous_control(report)
    wrong = calibrate_split_max_statistic(
        calibration,
        evaluation,
        alpha=0.2,
        family_confidence=0.90,
        retain_lower_bound=0.0,
        calibration_covariance_id="C",
        evaluation_covariance_id="C-mutated",
    )
    assert wrong.status is ValidationStatus.FAILED_MISSPECIFIED_COVARIANCE
    assert wrong.failure_visible is True
    with pytest.raises(PillarSInferenceError, match="claim refused"):
        require_simultaneous_control(wrong)


def test_optimizer_point_cannot_become_sampling_draws() -> None:
    law = build_sampling_law_spec(
        law_id="PR272-OBJECTIVE-LAW",
        sampling_law=SamplingLaw.PROFILE_LIKELIHOOD,
        conditioning_source=ConditioningSource.PROFILED,
        lane=ExceedanceLane.HTT_OBJECTIVE,
        source_identity="PR272 registered synthetic objective",
        covariance_id="PR272-COV",
        transfer_source="none",
        assumptions=("objective is not a probability law",),
    )
    objective = build_likelihood_objective(
        objective_id="PR272-OBJECTIVE",
        law=law,
        coordinate_names=("eta",),
        coordinates=((-1.0,), (0.0,), (1.0,)),
        objective_values=(1.0, 0.0, 1.0),
        optimizer_point=(0.0,),
        source_artifact_id="PR272-OBJECTIVE-SOURCE",
    )
    assert objective.optimizer_point == (0.0,)
    with pytest.raises(ConditionalExceedanceError, match="not sampling draws"):
        build_sampling_draws(
            draws_id="PR272-FORGED-OPTIMIZER-DRAWS",
            law=law,
            values=objective.optimizer_point,
            source_artifact_id="PR272-FORGED",
            sample_unit="objective",
        )


def test_joint_random_anchor_requires_cross_covariance_and_is_bounded() -> None:
    with pytest.raises(PillarSInferenceError, match="marginal"):
        build_joint_anchor_law(
            law_id="marginals-only",
            mean=(1.0, 2.0),
            covariance=((0.16, 0.0), (0.0, 0.09)),
            sample_size=64,
            joint_cross_covariance_declared=False,
        )
    law = build_joint_anchor_law(
        law_id="joint-v1",
        mean=(1.0, 2.0),
        covariance=((0.16, 0.06), (0.06, 0.09)),
        sample_size=64,
        joint_cross_covariance_declared=True,
    )
    interval = joint_fieller_interval(
        1.0, 2.0, law=law, normal_critical_value=1.959963984540054
    )
    assert interval.status is ValidationStatus.VALIDATED_REGISTERED_SYNTHETIC
    assert interval.lower < 0.5 < interval.upper
    unbounded = joint_fieller_interval(
        1.0, 0.0, law=law, normal_critical_value=1.959963984540054
    )
    assert unbounded.status is ValidationStatus.INCONCLUSIVE_UNBOUNDED
    assert unbounded.lower is None and unbounded.upper is None


def test_joint_anchor_coverage_keeps_unbounded_failure_visible() -> None:
    law = build_joint_anchor_law(
        law_id="joint-coverage",
        mean=(1.0, 2.0),
        covariance=((0.16, 0.06), (0.06, 0.09)),
        sample_size=64,
        joint_cross_covariance_declared=True,
    )
    report = evaluate_joint_anchor_coverage(
        ((1.0, 2.0), (1.0, 0.0)),
        law=law,
        true_ratio=0.5,
        normal_critical_value=1.959963984540054,
        family_confidence=0.90,
        retain_lower_bound=0.0,
    )
    assert report.unbounded_count == 1
    assert report.status is ValidationStatus.FAILED_REGISTERED_COVERAGE


def test_depth_multiplicity_requires_nested_same_target() -> None:
    calibration = np.zeros((19, 2))
    evaluation = np.zeros((20, 2))
    with pytest.raises(PillarSInferenceError, match="same centered target"):
        evaluate_depth_multiplicity(
            calibration,
            evaluation,
            alpha=0.10,
            family_confidence=0.90,
            retain_lower_bound=0.0,
            covariance_id="C",
            same_centered_target=False,
            nested_path=True,
        )
    with pytest.raises(PillarSInferenceError, match="nested path"):
        evaluate_depth_multiplicity(
            calibration,
            evaluation,
            alpha=0.10,
            family_confidence=0.90,
            retain_lower_bound=0.0,
            covariance_id="C",
            same_centered_target=True,
            nested_path=False,
        )


def test_weak_identification_abstains_at_full_rank() -> None:
    weak = evaluate_weak_identification(
        np.diag((1.0, 0.4, 0.02)),
        np.eye(3),
        covariance_id="C",
        expected_covariance_id="C",
        singular_value_floor=0.05,
        local_response_space=((1.0,), (0.0,), (0.0,)),
        global_response_space=(
            (np.cos(0.02),),
            (np.sin(0.02),),
            (0.0,),
        ),
        principal_angle_floor_radians=0.05,
        perturbation_radius=0.01,
    )
    assert weak.supported_rank == 3
    assert weak.status is ValidationStatus.ABSTAIN_WEAK_IDENTIFICATION
    assert weak.worst_case_parameter_error_bound == pytest.approx(0.5)
    with pytest.raises(PillarSInferenceError, match="wrong covariance"):
        evaluate_weak_identification(
            np.eye(2),
            np.eye(2),
            covariance_id="C-mutated",
            expected_covariance_id="C",
            singular_value_floor=0.05,
            local_response_space=((1.0,), (0.0,)),
            global_response_space=((0.0,), (1.0,)),
            principal_angle_floor_radians=0.05,
            perturbation_radius=0.01,
        )


def test_composition_is_only_a_registered_linear_cell() -> None:
    orbit = np.eye(3)
    response = np.vstack((np.eye(3), np.ones(3)))
    report = evaluate_registered_composition(
        orbit,
        response,
        rank_tolerance=1.0e-12,
        registered_linear_cell_only=True,
    )
    assert report.status is ValidationStatus.VALIDATED_REGISTERED_LINEAR_CELL
    assert report.global_orbit_separation_claimed is False
    response[:, 2] = 0.0
    failed = evaluate_registered_composition(
        orbit,
        response,
        rank_tolerance=1.0e-12,
        registered_linear_cell_only=True,
    )
    assert failed.status is ValidationStatus.ABSTAIN_NON_IDENTIFIED
    with pytest.raises(PillarSInferenceError, match="registered linear cell"):
        evaluate_registered_composition(
            orbit,
            np.vstack((np.eye(3), np.ones(3))),
            rank_tolerance=1.0e-12,
            registered_linear_cell_only=False,
        )


def test_matched_counterpair_refuses_scalar_or_anchor_drift() -> None:
    zeros = np.zeros((8, 2))
    with pytest.raises(PillarSInferenceError, match="exactly equal"):
        evaluate_matched_counterpair_power(
            zeros,
            zeros,
            np.ones((8, 2)),
            scalar_differences=np.r_[1.0, np.zeros(7)],
            anchor_differences=np.zeros(8),
            alpha=0.20,
            family_confidence=0.90,
            minimum_power_lower_bound=0.0,
        )


def test_open_set_split_must_freeze_before_evaluation() -> None:
    with pytest.raises(PillarSInferenceError, match="freeze"):
        evaluate_open_set_validation(
            ((-2.0, 0.0), (2.0, 0.0)),
            (0, 1),
            ((-2.0, 0.0), (2.0, 0.0)),
            (0, 1),
            ((0.0, 3.0),),
            known_centres=((-2.0, 0.0), (2.0, 0.0)),
            alpha=0.20,
            family_confidence=0.90,
            minimum_known_coverage_lower_bound=0.0,
            minimum_unknown_abstention_lower_bound=0.0,
            thresholds_frozen_before_evaluation=False,
        )


def test_depth_local_global_keeps_htt_and_mio_ownership_separate() -> None:
    covariance = np.eye(4)
    local = np.asarray((0.25, 0.5, 0.75, 1.0))
    global_ = np.ones(4)
    data = 4.0 * local
    htt_report = evaluate_depth_local_global(
        data,
        covariance=covariance,
        covariance_id="C",
        local_design=local,
        global_design=global_,
        mask_path_id="nested-mask",
        transfer_source="none",
    )
    assert htt_report.likelihood_owner == "HTT"
    assert htt_report.selected_candidate is ModelCandidate.LOCAL
    mio_report = build_mio_depth_cross_check(
        data,
        local_design=local,
        global_design=global_,
        mask_path_id="nested-mask",
    )
    assert mio_report.owner == "MIO"
    assert mio_report.likelihood_present is False
    assert mio_report.posterior_present is False
    assert mio_report.evidence_present is False
    assert mio_report.local_residual_norm < mio_report.global_residual_norm


def test_depth_local_global_abstains_for_proportional_designs() -> None:
    design = np.asarray((1.0, 2.0, 3.0, 4.0))
    report = evaluate_depth_local_global(
        design,
        covariance=np.eye(4),
        covariance_id="identity",
        local_design=design,
        global_design=2.0 * design,
        mask_path_id="nested-mask",
        transfer_source="none",
    )
    assert report.status is ValidationStatus.ABSTAIN_NON_IDENTIFIED
    assert report.selected_candidate is ModelCandidate.INDETERMINATE

    near_overlap = evaluate_depth_local_global(
        design,
        covariance=np.eye(4),
        covariance_id="identity",
        local_design=design,
        global_design=design + np.asarray((0.0, 0.0, 0.0, 1.0e-8)),
        mask_path_id="nested-mask",
        transfer_source="none",
        principal_angle_floor_radians=1.0e-6,
    )
    assert near_overlap.status is ValidationStatus.ABSTAIN_NON_IDENTIFIED
    assert near_overlap.selected_candidate is ModelCandidate.INDETERMINATE


def test_depth_local_global_refuses_nonfinite_large_scale_fit() -> None:
    local = np.asarray((1.0e200, 1.0e200))
    global_ = np.asarray((1.0e200, 1.0e200 + 2.0e185))
    with pytest.raises(PillarSInferenceError, match="finite GLS"):
        evaluate_depth_local_global(
            local,
            covariance=np.eye(2),
            covariance_id="identity",
            local_design=local,
            global_design=global_,
            mask_path_id="nested-mask",
            transfer_source="none",
            principal_angle_floor_radians=1.0e-12,
        )


def test_depth_local_global_refuses_nonfinite_extreme_covariance_fit() -> None:
    local = np.asarray((0.25, 0.5, 0.75, 1.0))
    global_ = np.ones(4)
    with pytest.raises(PillarSInferenceError, match="finite GLS"):
        evaluate_depth_local_global(
            local,
            covariance=np.diag((1.0e-320, 1.0, 2.0, 3.0)),
            covariance_id="extreme-spd",
            local_design=local,
            global_design=global_,
            mask_path_id="nested-mask",
            transfer_source="none",
        )


def test_depth_local_global_rank_uses_covariance_whitened_design() -> None:
    local = np.asarray((1.0, 0.0))
    global_ = np.asarray((1.0, 1.0e-16))
    report = evaluate_depth_local_global(
        local,
        covariance=np.diag((1.0, 1.0e-32)),
        covariance_id="anisotropic",
        local_design=local,
        global_design=global_,
        mask_path_id="nested-mask",
        transfer_source="none",
    )
    assert report.status is ValidationStatus.VALIDATED_REGISTERED_SYNTHETIC
    assert report.selected_candidate is ModelCandidate.LOCAL


def test_depth_local_global_refuses_zero_design_with_typed_error() -> None:
    with pytest.raises(PillarSInferenceError, match="design must be nonzero"):
        evaluate_depth_local_global(
            (0.0, 0.0),
            covariance=np.eye(2),
            covariance_id="identity",
            local_design=(0.0, 0.0),
            global_design=(1.0, 0.0),
            mask_path_id="nested-mask",
            transfer_source="none",
        )


def test_public_facades_enforce_owner_boundary() -> None:
    import htt.infer.vector_tensor_validation as htt_surface
    import mio.formalism.vector_tensor_validation as mio_surface

    assert "evaluate_depth_local_global" in htt_surface.__all__
    assert "build_mio_depth_cross_check" in mio_surface.__all__
    assert "evaluate_depth_local_global" not in mio_surface.__all__
    assert not hasattr(mio_surface, "HttDepthDiscriminationReport")
    assert not hasattr(mio_surface, "PosteriorExceedance")


def test_generated_metrics_meet_frozen_bounds_without_relabeling(
    raw_results,
) -> None:
    assert raw_results["VT-S3"]["correct"]["coverage_lower_bound"] >= 0.92
    assert raw_results["VT-S5"]["minimum_family_wise_lower"] >= 0.92
    assert raw_results["VT-S6"]["coverage"]["coverage_lower_bound"] >= 0.92
    assert (
        raw_results["VT-S9"]["report"]["adjusted_familywise_error_rate"]
        <= 0.06
    )
    assert (
        raw_results["VT-S9"]["report"]["unadjusted_familywise_error_rate"]
        >= 0.10
    )
    assert raw_results["VT-S12"]["alternative_power_lower_bound"] >= 0.80
    assert raw_results["VT-S13"]["known_coverage_lower_bound"] >= 0.92
    assert raw_results["VT-S13"]["unknown_abstention_lower_bound"] >= 0.95
    assert raw_results["VT-S14"]["correct_selection_lower_bound"] >= 0.80
    assert (
        raw_results["SBC-HTT-COMPUTATION"]["calibrated"]["verdict"]
        == "calibrated"
    )
    assert (
        raw_results["SBC-HTT-COMPUTATION"]["calibrated"]["aggregation"]
        == "pooled_seed_family_rank_uniformity"
    )
    assert len(
        raw_results["SBC-HTT-COMPUTATION"]["calibrated"]["member_runs"]
    ) == 5


def test_registered_reports_are_immutable_dataclasses(raw_results) -> None:
    report = calibrate_split_max_statistic(
        np.zeros((19, 1)),
        np.zeros((20, 1)),
        alpha=0.10,
        family_confidence=0.90,
        retain_lower_bound=0.0,
        calibration_covariance_id="C",
        evaluation_covariance_id="C",
    )
    forged = replace(
        report,
        status=ValidationStatus.VALIDATED_REGISTERED_SYNTHETIC,
        evaluation_covariance_id="forged",
    )
    with pytest.raises(PillarSInferenceError, match="claim refused"):
        require_simultaneous_control(forged)
    assert raw_results["VT-S14"]["HTT_owner"] == "HTT"
    for key in (
        "MIO_local_diagnostic_cross_check",
        "MIO_global_diagnostic_cross_check",
    ):
        report_payload = raw_results["VT-S14"][key]
        assert report_payload["likelihood_present"] is False
        assert report_payload["posterior_present"] is False
        assert report_payload["evidence_present"] is False
    assert not any(
        "truth" in key.lower() for key in raw_results["VT-S14"]
    )
