"""PR-255 anchored response geometry and nonlinearity phase gates."""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest
import yaml

from common.anchor_geometry import (
    NormalizerKind,
    NormalizerPurpose,
    NormalizerSpec,
)
from common.anchored_response_geometry import (
    AnchoredResponseGeometryError,
    AnchoredResponseGeometryReport,
    AnchoredResponseStatus,
    IdentifiedSetContractionStatus,
    NonlinearityDGPKind,
    NonlinearityPhaseStatus,
    SchurMorphologyInformationReport,
    anchored_numeric_content_id,
    measure_anchored_response_geometry,
    measure_schur_morphology_information,
)
from htt.statistics import (
    AnchoredResponseGeometryReport as HttAnchoredResponseGeometryReport,
)
from htt.statistics import (
    SchurMorphologyInformationReport as HttSchurMorphologyInformationReport,
)
from htt.statistics import build_mes_information_gain_compatibility_view
from common.transfer_registry import TransferSource
from scripts.codex_harness.run_pr255_response_geometry_benchmark import (
    BASELINE_OBSERVABLE_DESCRIPTOR,
    MAX_MCSE,
    MASK_DESCRIPTOR,
    MORPHOLOGY_OBSERVABLE_DESCRIPTOR,
    PHASE_COVARIANCE_ID,
    TRANSFER_DESCRIPTOR,
    _semantic_receipt as _benchmark_semantic_receipt,
    build_payload,
)


ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "docs/research_program/premise_anchor/pr255_spec.yaml"
RECEIPT = (
    ROOT
    / "docs/generated/pr255_response_geometry/"
    "response_geometry_benchmark.json"
)
INTEGRATION_RUNNER = (
    ROOT / "scripts/codex_harness/run_pr255_integration.py"
)
DIRECT_FISHER_ORACLE = (
    ROOT
    / "scripts/codex_harness/"
    "run_pr255_response_geometry_oracle.py"
)
PUBLICATION_POLICY = (
    ROOT
    / "docs/research_program/premise_anchor/"
    "pr255_publication_policy.json"
)
def _test_receipt(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


TRANSFER_ID = _test_receipt("pr255-test-synthetic-transfer-none-v1")
MASK_ID = _test_receipt("pr255-test-full-synthetic-mask-v1")
BASELINE_ID = _test_receipt("pr255-test-baseline-observable-v1")
MORPHOLOGY_ID = _test_receipt("pr255-test-morphology-observable-v1")


def _normalizer(dimension: int) -> NormalizerSpec:
    labels = tuple(f"u{index}" for index in range(dimension))
    return NormalizerSpec(
        normalizer_id=f"pr255-test-normalizer-{dimension}",
        kind=NormalizerKind.MES_ANCHORED,
        purposes=(NormalizerPurpose.RESPONSE_CONDITIONING,),
        coordinate_labels=labels,
        coordinate_map=tuple(
            tuple(1.0 if row == column else 0.0 for column in range(dimension))
            for row in range(dimension)
        ),
        source_identity="PR255-TEST-SYNTHETIC-NORMALIZER",
    )


def _schur_1d() -> tuple[SchurMorphologyInformationReport, NormalizerSpec]:
    normalizer = _normalizer(1)
    joint_covariance = np.eye(2)
    report = measure_schur_morphology_information(
        baseline_response=((1.0,),),
        morphology_response=((1.0,),),
        joint_covariance=joint_covariance,
        normalizer=normalizer,
        parameter_labels=("u0",),
        transfer_id=TRANSFER_ID,
        transfer_source=TransferSource.NONE,
        mask_id=MASK_ID,
        joint_covariance_id=anchored_numeric_content_id(joint_covariance),
        baseline_observable_id=BASELINE_ID,
        morphology_observable_id=MORPHOLOGY_ID,
    )
    return report, normalizer


def test_spec_binds_supported_quotient_schur_and_claim_boundary() -> None:
    spec = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    assert spec["work_unit_id"] == "PR-255"
    assert spec["target_sha"] == "090525951cc30ad29da7fa8ae0a11bd4553f5b4f"
    assert spec["change_set_id"] == "CS-PR255-RESPONSE-GEOMETRY"
    assert set(spec["phase_diagram"]["required_cells"]) == {
        kind.value for kind in NonlinearityDGPKind
    }
    assert spec["benchmark"] == {
        "data_source": "synthetic_only",
        "transfer_source": "none",
        "response_role": "hypothesis_only_analytic_synthetic",
        "pr151_data_used": False,
        "master_seed": 20260728,
        "minimum_replicates_per_cell": 20000,
        "maximum_replicates_per_cell": 400000,
        "maximum_mcse": 0.0025,
        "train_validation_held_out_split": [0.6, 0.2, 0.2],
        "precision_failure_status": "INCONCLUSIVE_MC_PRECISION",
    }
    assert "FLRW departure detection" in spec["claim_boundary"]["forbidden"]
    assert "Bianchi family identification" in spec["claim_boundary"]["forbidden"]
    assert "native-solver validation" in spec["claim_boundary"]["forbidden"]
    assert (
        spec["legacy_policy"]["active_replacement"]
        == "build_mes_information_gain_compatibility_view"
    )


def test_common_contracts_are_the_same_public_objects_in_htt() -> None:
    assert HttAnchoredResponseGeometryReport is AnchoredResponseGeometryReport
    assert (
        HttSchurMorphologyInformationReport
        is SchurMorphologyInformationReport
    )


def test_publication_policy_binds_portable_matrix_and_history_gates() -> None:
    policy = json.loads(PUBLICATION_POLICY.read_text(encoding="utf-8"))
    assert policy["policy_id"] == "PR255-PUBLICATION-POLICY"
    assert policy["max_open_prs"] == policy["max_prs_per_change_set"] == 1
    commands = policy["required_commands"]
    assert {command["id"] for command in commands} == {
        "pr255-focused",
        "pr255-synthetic-benchmark",
        "pr255-direct-fisher-oracle",
        "pr255-adjacent-contracts",
        "pr255-common-contracts",
        "pr255-claim-and-history",
        "dag-and-status",
    }
    assert all(command["argv"][0] == "{python}" for command in commands)
    assert {
        command["argv"][-1]
        for command in commands
        if command["id"].startswith("pr255-")
        and command["id"] != "pr255-direct-fisher-oracle"
    } == {"focused", "benchmark", "adjacent", "common", "claim"}
    oracle = next(
        command
        for command in commands
        if command["id"] == "pr255-direct-fisher-oracle"
    )
    assert oracle["argv"][-1].endswith(
        "run_pr255_response_geometry_oracle.py"
    )


def test_frozen_synthetic_benchmark_replays_exactly() -> None:
    frozen = json.loads(RECEIPT.read_text(encoding="utf-8"))
    assert frozen == build_payload()
    assert frozen["status"] == "PASS"
    assert frozen["owner"] == "HTT"
    assert frozen["scope"] == "pre_solver_synthetic_methodology"
    assert frozen["claim_tier"] == "diagnostic_only"
    assert frozen["scientific_artifact_mode"] == "diagnostic_only"
    assert frozen["data_source"] == "synthetic_only"
    assert frozen["pr151_data_used"] is False
    assert frozen["native_solver_used"] is False
    assert frozen["observational_validation"] is False
    assert frozen["transfer_source"] == "none"
    assert frozen["response_role"] == "hypothesis_only_analytic_synthetic"
    assert frozen["provenance"]["target_sha"] == (
        "090525951cc30ad29da7fa8ae0a11bd4553f5b4f"
    )
    assert frozen["provenance"]["generating_procedure"].endswith(
        "run_pr255_response_geometry_benchmark.py"
    )
    assert frozen["caveats"]
    assert frozen["configuration"]["master_seed"] == 20260728
    assert frozen["configuration"]["replicates_per_cell"] >= 20_000
    assert frozen["configuration"]["replicates_per_cell"] <= 400_000
    assert frozen["configuration"]["train_validation_held_out_split"] == [
        0.6,
        0.2,
        0.2,
    ]
    assert frozen["diagnostics"]["all_cell_mcse_pass"] is True
    assert frozen["diagnostics"]["all_phase_statuses_pass"] is True
    assert frozen["diagnostics"]["all_applicable_coverage_pass"] is True
    assert frozen["diagnostics"]["nominal_size_pass"] is True
    assert all(
        row["registered_decision_mcse"] <= MAX_MCSE
        and row["status"] == "PASS"
        for row in frozen["diagnostics"]["cells"]
    )


@pytest.mark.parametrize("mode", ("focused", "benchmark"))
def test_integration_runner_is_portable_outside_repo_cwd(
    tmp_path: Path,
    mode: str,
) -> None:
    # The focused runner executes this card.  Its child invocation owns the
    # scientific tests but must not recursively launch another runner.
    if os.environ.get("PR255_INTEGRATION_ACTIVE") == "1":
        return
    environment = os.environ.copy()
    environment["PYTHONPATH"] = ""
    completed = subprocess.run(
        [sys.executable, str(INTEGRATION_RUNNER), mode],
        cwd=tmp_path,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_direct_fisher_oracle_is_portable_outside_repo_cwd(
    tmp_path: Path,
) -> None:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = ""
    completed = subprocess.run(
        [sys.executable, str(DIRECT_FISHER_ORACLE)],
        cwd=tmp_path,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "PASS PR-255 direct-Fisher oracle cases=300" in completed.stdout


def test_benchmark_covers_all_phase_cells_and_mandatory_abstention() -> None:
    frozen = json.loads(RECEIPT.read_text(encoding="utf-8"))
    rows = {
        row["dgp_kind"]: row for row in frozen["diagnostics"]["cells"]
    }
    phase_cells = {
        row["dgp_kind"]: row for row in frozen["phase_diagram"]["cells"]
    }
    assert set(rows) == {kind.value for kind in NonlinearityDGPKind}
    assert rows["LINEAR_ANCHOR_COMPATIBLE"]["observed_status"] == (
        NonlinearityPhaseStatus.LINEAR_PREMISE_COMPATIBLE.value
    )
    assert rows["LINEAR_PREMISE_MISMATCH"]["observed_status"] == (
        NonlinearityPhaseStatus.LINEAR_PREMISE_MISMATCH.value
    )
    assert rows["NONLINEAR_ANCHOR_COMPATIBLE"]["observed_status"] == (
        NonlinearityPhaseStatus.NONLINEAR_WITHIN_ANCHOR.value
    )
    assert rows["NONLINEAR_PLUS_EXCEEDANCE"]["observed_status"] == (
        NonlinearityPhaseStatus.NONLINEAR_AND_EXCEEDANCE.value
    )
    for name in (
        "OBSERVER_FRAME_MISMATCH",
        "DERIVATIVE_CONTROL_FAILURE",
        "SYSTEMATICS_MIMIC",
        "UNKNOWN_SOURCE",
    ):
        assert rows[name]["mandatory_abstention"] is True
        assert rows[name]["observed_status"] == (
            NonlinearityPhaseStatus.UNATTRIBUTED_OFF_MANIFOLD.value
        )
        if name != "UNKNOWN_SOURCE":
            assert (
                rows[name]["source_competition_evaluation_count_per_split"]
                == 4000
            )
        assert rows[name]["source_competition_replicated"] is False
    for row in rows.values():
        assert row["stress_interval"][0] == row["stress_interval"][1]
        assert row["t_parallel"] is not None
        assert row["t_perp"] is not None
        assert row["delta_nl"] is None
        assert row["delta_nl_status"] == (
            "NOT_COMPUTED_NO_NONLINEAR_MANIFOLD_DISTANCE"
        )
        assert row["coverage"]["status"] in {
            "PASS",
            "NOT_APPLICABLE_NONLINEAR_DGP",
        }
        receipts = row["partition_receipts"]
        assert receipts["validation_role"] == (
            "matched_injection_evaluation"
        )
        assert len(
            {
                receipts["training"],
                receipts["validation"],
                receipts["held_out"],
            }
        ) == 3
        phase = phase_cells[row["dgp_kind"]]
        if phase["candidate_evaluation_ids"]:
            assert phase["held_out_receipt"] == receipts["held_out"]
            assert phase["matched_injection_receipt"] == receipts["validation"]
            gains = row["nonlinear_candidate_gains"]
            assert len(gains) == 1
            assert gains[0]["clears_both_registered_margins"] is (
                row["observed_status"]
                in {
                    NonlinearityPhaseStatus.NONLINEAR_WITHIN_ANCHOR.value,
                    NonlinearityPhaseStatus.NONLINEAR_AND_EXCEEDANCE.value,
                }
            )
        else:
            assert phase["held_out_receipt"] is None
            assert phase["matched_injection_receipt"] is None
            assert row["nonlinear_candidate_gains"] == []
    assert frozen["phase_diagram"]["transfer_source"] == "none"
    assert frozen["phase_diagram"]["transfer_id"] == (
        frozen["input_receipts"]["transfer"]["id"]
    )
    assert frozen["phase_diagram"]["transfer_metadata"] is None


def test_frozen_receipts_bind_numeric_content_and_named_semantics() -> None:
    frozen = json.loads(RECEIPT.read_text(encoding="utf-8"))
    receipts = frozen["input_receipts"]
    geometry = frozen["anchored_response_geometry"]
    schur = frozen["schur_morphology_information"]

    assert receipts["transfer"]["descriptor"]["source"] == "none"
    assert receipts["mask"]["descriptor"]["kind"] == "synthetic_full_support"
    assert receipts["baseline_observable"]["descriptor"]["role"] == "baseline"
    assert receipts["morphology_observable"]["descriptor"]["role"] == (
        "morphology_increment"
    )
    for label, role, descriptor in (
        ("transfer", "transfer", TRANSFER_DESCRIPTOR),
        ("mask", "mask", MASK_DESCRIPTOR),
        (
            "baseline_observable",
            "baseline_observable",
            BASELINE_OBSERVABLE_DESCRIPTOR,
        ),
        (
            "morphology_observable",
            "morphology_observable",
            MORPHOLOGY_OBSERVABLE_DESCRIPTOR,
        ),
    ):
        assert receipts[label] == {
            "id": _benchmark_semantic_receipt(
                role=role,
                descriptor=descriptor,
            ),
            "descriptor": descriptor,
        }
    assert receipts["covariance_ids"] == {
        "anchored_geometry": geometry["covariance_content_id"],
        "phase_nonlinearity": PHASE_COVARIANCE_ID,
        "schur_joint": schur["joint_covariance_content_id"],
    }
    assert geometry["covariance_id"] == geometry["covariance_content_id"]
    assert schur["joint_covariance_id"] == schur[
        "joint_covariance_content_id"
    ]
    for label in (
        "transfer",
        "mask",
        "baseline_observable",
        "morphology_observable",
    ):
        value = receipts[label]["id"]
        assert value.startswith("sha256:")
        assert len(set(value.removeprefix("sha256:"))) > 1


def test_benchmark_geometry_keeps_covariance_null_response_explicit() -> None:
    frozen = json.loads(RECEIPT.read_text(encoding="utf-8"))
    geometry = frozen["anchored_response_geometry"]
    assert geometry["status"] == AnchoredResponseStatus.EXPLICIT_NULL_RESPONSE.value
    assert geometry["supported_data_dimension"] == 2
    assert geometry["data_dimension"] == 3
    assert geometry["covariance_null_response_norm_sq"] > 0.0
    assert geometry["nuisance_rank"] == 1
    assert geometry["rank"] == geometry["original_rank"] == 1
    assert geometry["principal_angles"]["status"] == "DEFINED"


def test_schur_receipt_is_matrix_valued_and_has_finite_full_rank_contraction() -> None:
    frozen = json.loads(RECEIPT.read_text(encoding="utf-8"))
    schur = frozen["schur_morphology_information"]
    assert schur["status"] == "MEASURED"
    assert len(schur["baseline_information"]) == 2
    assert len(schur["incremental_information"]) == 2
    assert len(schur["joint_information"]) == 2
    assert schur["contraction"]["status"] == (
        IdentifiedSetContractionStatus.DEFINED_FULL_DIMENSION.value
    )
    assert 0.0 < (
        schur["contraction"]["confidence_ellipsoid_volume_ratio"]
    ) <= 1.0
    assert schur["contraction"]["contraction_kind"] == (
        "LOCAL_GAUSSIAN_SUPPORTED_ELLIPSOID"
    )
    assert schur["contraction"]["global_feasible_set_status"] == (
        "NOT_COMPUTED_NO_FEASIBLE_SET_INPUT"
    )
    assert schur["contraction"]["global_feasible_set_contraction"] is None


def test_exact_1d_matrix_report_builds_only_scalar_compatibility_view() -> None:
    matrix_report, normalizer = _schur_1d()
    result = build_mes_information_gain_compatibility_view(
        matrix_report=matrix_report,
        normalizer=normalizer,
        config_hash="sha256:" + "a" * 64,
        input_hashes=("sha256:" + "b" * 64,),
        generating_command=(
            "python -m pytest "
            "tests/pr_cards/test_pr_255_anchored_response_geometry.py -q"
        ),
        worktree_state="PR-255-test-worktree",
    )
    assert matrix_report.exact_one_dimensional_reduction is True
    assert result.diagonal_bound == pytest.approx(1.0)
    assert result.morphology_final_bound == pytest.approx(1.0 / math.sqrt(2.0))
    assert result.i_morph == pytest.approx(math.sqrt(2.0))
    assert result.manifest.production_status == "diagnostic_only"
    definitions = result.manifest.statistics_definitions
    assert definitions["compatibility_mode"] == (
        "exact_1d_schur_matrix_reduction"
    )
    assert definitions["anchor_scaling_information_gain"] is False
    assert result.branches[2].branch_role == (
        "exact_1d_schur_matrix_reduction"
    )


def test_scalar_compatibility_rejects_rank_gain_and_multidimensional_reports() -> None:
    normalizer = _normalizer(2)
    joint_covariance = np.eye(2)
    report = measure_schur_morphology_information(
        baseline_response=((1.0, 0.0),),
        morphology_response=((0.0, 1.0),),
        joint_covariance=joint_covariance,
        normalizer=normalizer,
        parameter_labels=("u0", "u1"),
        transfer_id=TRANSFER_ID,
        transfer_source=TransferSource.NONE,
        mask_id=MASK_ID,
        joint_covariance_id=anchored_numeric_content_id(joint_covariance),
        baseline_observable_id=BASELINE_ID,
        morphology_observable_id=MORPHOLOGY_ID,
    )
    assert report.contraction.status is (
        IdentifiedSetContractionStatus.RANK_GAIN_NO_FINITE_RATIO
    )
    assert report.exact_one_dimensional_reduction is False
    with pytest.raises(ValueError, match="exact one-dimensional"):
        build_mes_information_gain_compatibility_view(
            matrix_report=report,
            normalizer=normalizer,
            config_hash="sha256:" + "a" * 64,
            input_hashes=("sha256:" + "b" * 64,),
            generating_command="pytest",
            worktree_state="PR-255-test-worktree",
        )


def test_scalar_compatibility_rejects_covariance_null_response() -> None:
    normalizer = _normalizer(1)
    joint_covariance = np.asarray(((1.0, 1.0), (1.0, 1.0)))
    report = measure_schur_morphology_information(
        baseline_response=((1.0,),),
        morphology_response=((0.0,),),
        joint_covariance=joint_covariance,
        normalizer=normalizer,
        parameter_labels=("u0",),
        transfer_id=TRANSFER_ID,
        transfer_source=TransferSource.NONE,
        mask_id=MASK_ID,
        joint_covariance_id=anchored_numeric_content_id(joint_covariance),
        baseline_observable_id=BASELINE_ID,
        morphology_observable_id=MORPHOLOGY_ID,
    )
    assert report.status.value == "OUTSIDE_SUPPORTED_QUOTIENT"
    assert report.exact_one_dimensional_reduction is False
    with pytest.raises(ValueError, match="exact one-dimensional"):
        build_mes_information_gain_compatibility_view(
            matrix_report=report,
            normalizer=normalizer,
            config_hash="sha256:" + "a" * 64,
            input_hashes=("sha256:" + "b" * 64,),
            generating_command="pytest",
            worktree_state="PR-255-test-worktree",
        )


def test_scalar_compatibility_rejects_near_singular_joint_support_leak() -> None:
    normalizer = _normalizer(1)
    joint_covariance = np.asarray(
        ((1.0, 1.0 - 1.0e-13), (1.0 - 1.0e-13, 1.0))
    )
    report = measure_schur_morphology_information(
        baseline_response=((1.0,),),
        morphology_response=((0.0,),),
        joint_covariance=joint_covariance,
        normalizer=normalizer,
        parameter_labels=("u0",),
        transfer_id=TRANSFER_ID,
        transfer_source=TransferSource.NONE,
        mask_id=MASK_ID,
        joint_covariance_id=anchored_numeric_content_id(joint_covariance),
        baseline_observable_id=BASELINE_ID,
        morphology_observable_id=MORPHOLOGY_ID,
        rtol=1.0e-12,
    )
    assert report.status.value == "OUTSIDE_SUPPORTED_QUOTIENT"
    assert report.exact_one_dimensional_reduction is False
    with pytest.raises(ValueError, match="exact one-dimensional"):
        build_mes_information_gain_compatibility_view(
            matrix_report=report,
            normalizer=normalizer,
            config_hash="sha256:" + "a" * 64,
            input_hashes=("sha256:" + "b" * 64,),
            generating_command="pytest",
            worktree_state="PR-255-test-worktree",
        )


def test_missing_and_rank_mutation_paths_fail_closed() -> None:
    covariance = np.eye(2)
    missing = measure_anchored_response_geometry(
        response=None,
        covariance=covariance,
        normalizer=_normalizer(2),
        parameter_labels=("u0", "u1"),
        transfer_id=TRANSFER_ID,
        transfer_source=TransferSource.NONE,
        mask_id=MASK_ID,
        covariance_id=anchored_numeric_content_id(covariance),
    )
    assert missing.status is AnchoredResponseStatus.MISSING_INPUT
    assert missing.rank is None
    assert missing.response_replay_matrix is None

    unstable = NormalizerSpec(
        normalizer_id="pr255-rank-mutation",
        kind=NormalizerKind.MES_ANCHORED,
        purposes=(NormalizerPurpose.RESPONSE_CONDITIONING,),
        coordinate_labels=("u0", "u1"),
        coordinate_map=((1.0e-8, 0.0), (0.0, 1.0)),
        source_identity="PR255-RANK-MUTATION",
    )
    with pytest.raises(
        AnchoredResponseGeometryError,
        match="anchor scaling changed",
    ):
        measure_anchored_response_geometry(
            response=np.eye(2),
            covariance=covariance,
            normalizer=unstable,
            parameter_labels=("u0", "u1"),
            transfer_id=TRANSFER_ID,
            transfer_source=TransferSource.NONE,
            mask_id=MASK_ID,
            covariance_id=anchored_numeric_content_id(covariance),
            rtol=1.0e-6,
        )


def test_active_sources_do_not_import_pr151_or_native_solver_paths() -> None:
    sources = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            ROOT / "htt/src/common/anchored_response_geometry.py",
            ROOT / "htt/htt/htt/statistics/anchored_response_geometry.py",
            ROOT
            / "scripts/codex_harness/"
            "run_pr255_response_geometry_benchmark.py",
        )
    )
    assert "pr151_progress" not in sources
    assert "PR151_PATH" not in sources
    assert "PR151_RECEIPT" not in sources
    assert "read_pr151" not in sources
    assert "native_solver_adapter" not in sources
    assert "family_classifier" not in sources
    assert "stress_used_for_attribution=True" not in sources
