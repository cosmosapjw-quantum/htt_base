"""PR-256 global-tilt versus local-boost response-geometry gates."""

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
from common.anchored_response_geometry import anchored_numeric_content_id
from common.revival_bulk_bridge import W as PR222_WINDOW_OPERATOR
from common.statistical_foundations import DepartureState
from common.transfer_registry import TransferSource
from htt.departure import (
    SourceResponseGeometryReport as ExportedSourceResponseGeometryReport,
)
from htt.departure import (
    VelocityFrameDecomposition as ExportedVelocityFrameDecomposition,
)
from htt.departure.velocity_frame_decomposition import (
    ResponseProviderAvailability,
    ResponseProviderKind,
    SourceHypothesis,
    SourceResponseGeometryReport,
    SourceResponseGeometryStatus,
    VelocityComponent,
    VelocityFrameDecomposition,
    VelocityFrameError,
    build_velocity_frame_decomposition,
    measure_source_response_geometry,
    register_source_response_provider,
)
from scripts.codex_harness.run_pr256_velocity_frame_benchmark import (
    CELL_THETA,
    FIRST_ORDER_BETA_CEILING,
    GENERATOR_SOURCE_ID,
    HELD_OUT_REPLICATES,
    MASK_ID,
    MAX_MCSE,
    OUTPUT,
    PR222_WINDOW_ID,
    SYNTHETIC_RESPONSE_PER_BETA_SCALE,
    TARGET_SHA,
    TRANSFER_ID,
    build_payload,
)
from scripts.codex_harness import run_pr256_velocity_frame_benchmark as benchmark


ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "docs/research_program/premise_anchor/pr256_spec.yaml"
POLICY = (
    ROOT
    / "docs/research_program/premise_anchor/"
    "pr256_publication_policy.json"
)
RUNNER = ROOT / "scripts/codex_harness/run_pr256_integration.py"
ORACLE = (
    ROOT
    / "scripts/codex_harness/"
    "run_pr256_response_geometry_oracle.py"
)
MODULE = (
    ROOT
    / "htt/htt/htt/departure/"
    "velocity_frame_decomposition.py"
)


def _receipt(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _provider(
    hypothesis: SourceHypothesis,
    response: object | None,
    *,
    availability: ResponseProviderAvailability = (
        ResponseProviderAvailability.AVAILABLE
    ),
    observables: tuple[str, ...] = ("dipole", "depth", "morphology"),
):
    local = hypothesis is SourceHypothesis.LOCAL_BOOST
    return register_source_response_provider(
        provider_id=_receipt(
            f"pr256-card-{hypothesis.value}-{availability.value}"
        ),
        hypothesis=hypothesis,
        velocity_component=(
            VelocityComponent.BETA_MO
            if local
            else VelocityComponent.BETA_RM
        ),
        provider_kind=ResponseProviderKind.ANALYTIC,
        availability=availability,
        observable_labels=observables,
        parameter_labels=(
            ("beta_MO_amplitude",)
            if local
            else ("beta_RM_amplitude",)
        ),
        response=response,
        transfer_id=TRANSFER_ID,
        transfer_source=TransferSource.NONE,
        basis="registered common synthetic basis",
        epoch_window="registered common synthetic window",
        assumptions=("first-order analytic response",),
        caveats=("hypothesis-only response",),
        missing_reason=(
            None
            if availability is ResponseProviderAvailability.AVAILABLE
            else "registered response provider unavailable"
        ),
    )


def _normalizer(
    matrix: tuple[tuple[float, ...], ...] = (
        (1.0, 0.0),
        (0.0, 1.0),
    ),
) -> NormalizerSpec:
    return NormalizerSpec(
        normalizer_id="pr256-card-block-normalizer",
        kind=NormalizerKind.MES_ANCHORED,
        purposes=(NormalizerPurpose.RESPONSE_CONDITIONING,),
        coordinate_labels=("beta_MO_amplitude", "beta_RM_amplitude"),
        coordinate_map=matrix,
        source_identity="PR256-CARD-TYPED-COORDINATES",
        assumptions=("block-preserving map",),
    )


def _measure(
    local_response: object,
    global_response: object,
    *,
    covariance: object | None = None,
    nuisance: object | None = None,
    threshold: float = 0.2,
    normalizer: NormalizerSpec | None = None,
) -> SourceResponseGeometryReport:
    covariance_value = np.eye(3) if covariance is None else covariance
    return measure_source_response_geometry(
        local_provider=_provider(
            SourceHypothesis.LOCAL_BOOST,
            local_response,
        ),
        global_provider=_provider(
            SourceHypothesis.GLOBAL_TILT,
            global_response,
        ),
        covariance=covariance_value,
        normalizer=_normalizer() if normalizer is None else normalizer,
        covariance_id=anchored_numeric_content_id(covariance_value),
        mask_id=MASK_ID,
        nuisance_response=nuisance,
        separation_threshold_radians=threshold,
    )


def test_spec_binds_frames_provider_abstention_and_claim_boundary() -> None:
    spec = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    assert spec["work_unit_id"] == "PR-256"
    assert spec["target_sha"] == TARGET_SHA
    assert spec["change_set_id"] == "CS-PR256-VELOCITY-FRAMES"
    assert spec["velocity_frame_contract"]["relation"] == (
        "beta_RO = beta_RM + beta_MO + O(beta^2)"
    )
    assert spec["velocity_frame_contract"]["parity"] == "polar_vector"
    assert set(spec["source_response_contract"]["statuses"]) == {
        status.value for status in SourceResponseGeometryStatus
    }
    assert spec["benchmark"]["data_source"] == "synthetic_only"
    assert spec["benchmark"]["pr151_data_used"] is False
    assert spec["benchmark"]["finite_window_source"] == (
        "common.revival_bulk_bridge.W"
    )
    assert spec["benchmark"]["train_validation_held_out_split"] == [
        0.6,
        0.2,
        0.2,
    ]
    assert "observed global-tilt detection" in spec["claim_boundary"]["forbidden"]
    assert "Bianchi family identification" in spec["claim_boundary"]["forbidden"]


def test_publication_policy_is_one_change_set_one_pr() -> None:
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    assert policy["policy_id"] == "PR256-PUBLICATION-POLICY"
    assert policy["target_sha"] == TARGET_SHA
    assert policy["max_open_prs"] == policy["max_prs_per_change_set"] == 1
    assert policy["publication_requires_external_publisher"] is True
    assert policy["ordinary_agent_push_forbidden"] is True
    assert {item["id"] for item in policy["required_commands"]} == {
        "pr256-focused",
        "pr256-synthetic-benchmark",
        "pr256-independent-oracle",
        "pr256-adjacent-contracts",
        "pr256-claim-and-history",
        "dag-and-status",
    }


def test_departure_state_remains_unchanged_and_separate() -> None:
    state = DepartureState(
        sigma_ab=(0.0,) * 5,
        omega_a=(0.0,) * 3,
        beta_a=(1.0e-3, 2.0e-3, 3.0e-3),
        delta_omega_k=0.0,
        frame="registered departure frame",
        congruence="registered congruence",
        epoch_window="registered window",
        averaging_scale="registered scale",
        basis="registered basis",
        units="registered units",
        parity="polar beta",
        perturbative_order="registered order",
    )
    decomposition = build_velocity_frame_decomposition(
        beta_RO=state.beta_a,
        beta_RM=None,
        beta_MO=None,
        basis="registered basis",
        epoch_window="registered window",
        first_order_beta_ceiling=1.0e-2,
    )
    assert state.beta_a == (1.0e-3, 2.0e-3, 3.0e-3)
    assert decomposition.status.value == "SUM_ONLY"
    source = MODULE.read_text(encoding="utf-8")
    assert "from common.statistical_foundations import DepartureState" not in source
    assert "DepartureState.beta_a =" not in source


def test_public_exports_share_exact_contract_identity() -> None:
    assert ExportedVelocityFrameDecomposition is VelocityFrameDecomposition
    assert ExportedSourceResponseGeometryReport is SourceResponseGeometryReport


def test_pr222_window_operator_is_bound_as_synthetic_only() -> None:
    assert PR222_WINDOW_OPERATOR.shape == (4, 3)
    assert PR222_WINDOW_ID == anchored_numeric_content_id(
        PR222_WINDOW_OPERATOR
    )
    frozen = json.loads(OUTPUT.read_text(encoding="utf-8"))
    assert frozen["provenance"]["pr222_window_operator_id"] == PR222_WINDOW_ID
    assert frozen["provenance"]["pr222_window_role"] == (
        "registered synthetic finite-window design input only"
    )


def test_frozen_benchmark_replays_and_controls_pass() -> None:
    frozen = json.loads(OUTPUT.read_text(encoding="utf-8"))
    assert frozen == build_payload()
    assert frozen["status"] == "PASS"
    assert frozen["owner"] == "HTT"
    assert frozen["scope"] == "pre_solver_synthetic_methodology"
    assert frozen["claim_tier"] == "diagnostic_only"
    assert frozen["data_source"] == "synthetic_only"
    assert frozen["response_role"] == "hypothesis_only"
    assert frozen["transfer_source"] == "none"
    assert frozen["sky_support_status"] == (
        "synthetic_directional_feature_space_not_observed_sky"
    )
    assert frozen["null_mock_status"] == (
        "preregistered_synthetic_dgp_only_no_observational_null"
    )
    assert frozen["covariance_status"] == (
        "registered_synthetic_covariance_supported_quotient_only"
    )
    assert frozen["pr151_data_used"] is False
    assert frozen["old_rust_science_output_used"] is False
    assert frozen["native_solver_used"] is False
    assert frozen["observational_validation"] is False
    assert frozen["configuration"]["held_out_replicates"] == (
        HELD_OUT_REPLICATES
    )
    assert frozen["configuration"]["partition_use"] == {
        "train": "sealed_unused_partition",
        "validation": "sealed_unused_partition",
        "held_out": "decision_scoring_only",
    }
    assert frozen["configuration"]["theta_units"] == (
        "dimensionless_beta_c_equals_1"
    )
    assert frozen["configuration"]["first_order_beta_ceiling"] == (
        FIRST_ORDER_BETA_CEILING
    )
    assert frozen["configuration"]["maximum_theta_source_norm_sum"] == (
        0.008
    )
    assert frozen["configuration"]["synthetic_response_per_beta_scale"] == (
        SYNTHETIC_RESPONSE_PER_BETA_SCALE
    )
    assert frozen["provenance"]["prediction_rule_id"].startswith("sha256:")
    assert frozen["provenance"]["scoring_rule_id"].startswith("sha256:")
    assert frozen["provenance"]["generating_procedure_sha256"] == (
        GENERATOR_SOURCE_ID
    )
    assert all(
        cell["target_identity"].startswith("sha256:")
        for cell in frozen["cells"]
    )
    assert frozen["controls"]["maximum_observed_mcse"] <= MAX_MCSE
    assert frozen["controls"]["confusable_mandatory_abstention"] is True
    assert frozen["controls"]["pure_local_false_global_pass"] is True
    assert frozen["controls"]["mixed_source_single_global_pass"] is True
    assert frozen["controls"]["added_observable_rank_or_angle_gain"] is True
    assert frozen["controls"]["full_minimum_angle_radians"] > (
        frozen["controls"]["baseline_minimum_angle_radians"]
    )


def test_benchmark_beta_coordinates_fail_closed_outside_first_order_domain(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert all(
        sum(abs(value) for value in theta)
        <= FIRST_ORDER_BETA_CEILING
        for theta in CELL_THETA.values()
    )
    frozen = json.loads(OUTPUT.read_text(encoding="utf-8"))
    assert all(
        cell["theta_units"] == "dimensionless_beta_c_equals_1"
        and cell["theta_source_norm_sum"] <= FIRST_ORDER_BETA_CEILING
        for cell in frozen["cells"]
    )
    monkeypatch.setitem(benchmark.CELL_THETA, "pure_local", (4.0, 0.0))
    with pytest.raises(ValueError, match="first-order domain"):
        benchmark.build_payload()


def test_all_six_methods_and_four_cells_are_predeclared() -> None:
    frozen = json.loads(OUTPUT.read_text(encoding="utf-8"))
    cells = {cell["cell_id"]: cell for cell in frozen["cells"]}
    assert set(cells) == {
        "pure_local",
        "pure_global",
        "mixed_source",
        "confusable_sum_only",
    }
    expected_methods = {
        "dipole_amplitude",
        "diagonal_Cl",
        "morphology_only",
        "anchor_stress_only",
        "anchored_response_geometry",
        "full_held_out_source_competition",
    }
    assert all(set(cell["methods"]) == expected_methods for cell in cells.values())
    assert all(
        method["geometry"]["status"] == "SUM_ONLY"
        and method["decisions"]["rates"]["ABSTAIN"] == 1.0
        for method in cells["confusable_sum_only"]["methods"].values()
    )
    assert (
        cells["mixed_source"]["methods"][
            "full_held_out_source_competition"
        ]["decisions"]["rates"]["MIXED_CANDIDATE"]
        == 1.0
    )


def test_angle_threshold_boundary_abstains() -> None:
    angle = 0.2
    local = np.array((1.0, 0.0, 0.0))
    global_value = np.array((math.cos(angle), math.sin(angle), 0.0))
    report = _measure(
        local[:, None],
        global_value[:, None],
        threshold=angle,
    )
    assert report.minimum_principal_angle_radians == pytest.approx(angle)
    assert report.status is SourceResponseGeometryStatus.SUM_ONLY


def test_block_scaling_preserves_rank_and_cannot_create_separation() -> None:
    local = ((1.0,), (0.0,), (0.0,))
    global_value = ((2.0,), (0.0,), (0.0,))
    baseline = _measure(local, global_value)
    scaled = _measure(
        local,
        global_value,
        normalizer=_normalizer(((2.0, 0.0), (0.0, 0.5))),
    )
    assert baseline.joint_rank == scaled.joint_rank == 1
    assert baseline.status is scaled.status is SourceResponseGeometryStatus.SUM_ONLY


def test_nuisance_projection_and_covariance_null_fail_closed() -> None:
    nuisance = ((1.0,), (0.0,), (0.0,))
    nuisance_report = _measure(
        ((1.0,), (0.0,), (0.0,)),
        ((0.0,), (1.0,), (0.0,)),
        nuisance=nuisance,
    )
    assert nuisance_report.status is SourceResponseGeometryStatus.NON_IDENTIFIED
    assert nuisance_report.local_rank == 0

    covariance = np.diag((1.0, 1.0, 0.0))
    null_report = _measure(
        ((1.0,), (0.0,), (0.0,)),
        ((0.0,), (0.0,), (1.0,)),
        covariance=covariance,
    )
    assert null_report.status is SourceResponseGeometryStatus.NON_IDENTIFIED
    assert null_report.covariance_null_response_norm_sq == pytest.approx(1.0)


def test_missing_observable_provider_is_not_zero_response() -> None:
    local = _provider(
        SourceHypothesis.LOCAL_BOOST,
        ((1.0,), (0.0,), (0.0,)),
    )
    missing = _provider(
        SourceHypothesis.GLOBAL_TILT,
        None,
        availability=ResponseProviderAvailability.MISSING,
    )
    covariance = np.eye(3)
    report = measure_source_response_geometry(
        local_provider=local,
        global_provider=missing,
        covariance=covariance,
        normalizer=_normalizer(),
        covariance_id=anchored_numeric_content_id(covariance),
        mask_id=MASK_ID,
    )
    assert (
        report.status
        is SourceResponseGeometryStatus.MISSING_RESPONSE_PROVIDER
    )
    assert report.common_geometry is None
    assert missing.response_id is None
    assert missing.response_replay_matrix is None


@pytest.mark.parametrize(
    "local,global_value,covariance",
    (
        (
            ((True,), (0.0,), (0.0,)),
            ((0.0,), (1.0,), (0.0,)),
            np.eye(3),
        ),
        (
            ((1.0,), (0.0,), (0.0,)),
            ((np.nan,), (1.0,), (0.0,)),
            np.eye(3),
        ),
        (
            ((1.0,), (0.0,), (0.0,)),
            ((0.0,), (1.0,), (0.0,)),
            ((1.0, 0.0), (0.0, 1.0)),
        ),
    ),
)
def test_malformed_response_and_covariance_inputs_fail(
    local: object,
    global_value: object,
    covariance: object,
) -> None:
    with pytest.raises(VelocityFrameError):
        _measure(local, global_value, covariance=covariance)


@pytest.mark.parametrize("mode", ("focused", "benchmark"))
def test_integration_runner_is_portable_outside_repo_cwd(
    tmp_path: Path,
    mode: str,
) -> None:
    if os.environ.get("PR256_INTEGRATION_ACTIVE") == "1":
        return
    environment = os.environ.copy()
    environment["PYTHONPATH"] = ""
    completed = subprocess.run(
        [sys.executable, str(RUNNER), mode],
        cwd=tmp_path,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_independent_cholesky_oracle_is_portable_outside_repo_cwd(
    tmp_path: Path,
) -> None:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = ""
    completed = subprocess.run(
        [sys.executable, str(ORACLE)],
        cwd=tmp_path,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "PASS PR-256 independent Cholesky oracle cases=300" in (
        completed.stdout
    )


def test_active_sources_do_not_import_pr151_or_native_solver() -> None:
    import_lines = "\n".join(
        line
        for path in (
            MODULE,
            ROOT
            / "scripts/codex_harness/"
            "run_pr256_velocity_frame_benchmark.py",
            ORACLE,
        )
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.startswith(("import ", "from "))
    )
    banned_imports = (
        "pr151_progress",
        "astropy.io",
        "native_adapter",
        "BASS_native",
        "rust",
    )
    assert not any(term in import_lines for term in banned_imports)
