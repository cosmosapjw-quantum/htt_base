#!/usr/bin/env python3
"""Independent read-only oracle for the frozen PR-290 physics/stat contract."""

from __future__ import annotations

import copy
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys
import tempfile

import numpy as np
import yaml


ROOT = Path(__file__).resolve().parents[4]
for path in (ROOT, ROOT / "htt/src", ROOT / "htt"):
    sys.path.insert(0, str(path))

from common.observed_lane_activation import build_planck_activation_decision
from htt.obsstat.boost_biposh_residual import ExactBoostOperator
from htt.obsstat.planck_post275_lane import (
    PlanckLaneContractError,
    biposh_feature_units,
    build_preactivation_capability_snapshot,
    observation_inclusive_max_scan,
    validate_full_joint_covariance,
)


SPEC = Path("docs/research_program/post_pr275/pr290_spec.yaml")
STATUS = Path("docs/codex_handoff/pr_status.yaml")
IDENTITY = Path("docs/generated/pr289_data_identity_v2_receipt.json")
PR288 = Path("docs/generated/pr288_bayesian_semantics_receipt.json")
RECEIPT = Path(
    "docs/research_program/post_pr275/data_runs/planck/PR290_NONEXECUTION_RECEIPT.json"
)
OBSERVED_RESULTS = Path("docs/research_program/post_pr275/data_runs/planck/results")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def copy_activation_inputs(destination: Path) -> None:
    identity = json.loads((ROOT / IDENTITY).read_text(encoding="utf-8"))
    sources = tuple(Path(value) for value in identity["source_bindings"])
    for relative in (SPEC, STATUS, IDENTITY, PR288, *sources):
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)


def mutate_spec(payload: dict[str, object], mutation: str) -> None:
    pipeline = payload["pipeline_contract"]
    assert isinstance(pipeline, dict)
    if mutation == "legacy_rank_estimator":
        pipeline["global_rank_contract"]["estimator"] = (
            "legacy_lowell_global_calibration_calibrate_max_scan"
        )
    elif mutation == "anti_conservative_ties":
        pipeline["global_rank_contract"]["tie_policy"] = "strict_greater"
    elif mutation == "wrong_finite_floor":
        pipeline["global_rank_contract"]["finite_resolution"] = "one_over_null_count"
    elif mutation == "independent_component_pairing":
        pipeline["covariance_contract"]["component_pairing"] = (
            "independent_SMICA_Commander_rows"
        )
    elif mutation == "diagonal_covariance":
        pipeline["covariance_contract"]["diagonal_shortcut_allowed"] = True
    elif mutation == "linear_biposh_units":
        pipeline["harmonic_and_unit_contract"]["biposh_A_units"] = "microK_CMB"
    elif mutation == "mask_ready":
        pipeline["mask_beam_contract"]["current_status"] = "READY_UNDECONVOLVED"
    elif mutation == "multipole_ready":
        pipeline["multipole_vector_contract"]["current_status"] = "READY_FAKE_POLE"
    elif mutation == "operator_order":
        pipeline["exact_common_operator_order"] = list(
            reversed(pipeline["exact_common_operator_order"])
        )
    elif mutation == "wrong_null_family":
        pipeline["null_family"] = "UNREGISTERED_NULLS"
    elif mutation == "mask_deconvolution_optional":
        pipeline["mask_deconvolution_required"] = False
    elif mutation == "diagonal_covariance_allowed":
        pipeline["diagonal_covariance_forbidden"] = False
    else:
        raise AssertionError(f"unknown mutation: {mutation}")


def independent_rank(
    rows: np.ndarray, directions: tuple[str, ...], observation_index: int
) -> tuple[tuple[Fraction, ...], Fraction]:
    matrix = np.asarray(rows, dtype=float)
    n_rows, n_columns = matrix.shape
    oriented = np.empty_like(matrix)
    for column, direction in enumerate(directions):
        if direction == "high":
            oriented[:, column] = matrix[:, column]
        elif direction == "low":
            oriented[:, column] = -matrix[:, column]
        elif direction == "two-sided":
            for row in range(n_rows):
                center = float(np.median(np.delete(matrix[:, column], row)))
                oriented[row, column] = abs(matrix[row, column] - center)
        else:
            raise AssertionError(direction)
    local = tuple(
        tuple(
            Fraction(
                sum(oriented[other, column] >= oriented[row, column] for other in range(n_rows)),
                n_rows,
            )
            for column in range(n_columns)
        )
        for row in range(n_rows)
    )
    minima = tuple(min(row) for row in local)
    observed_minimum = minima[observation_index]
    global_rank = Fraction(sum(value <= observed_minimum for value in minima), n_rows)
    return local[observation_index], global_rank


def audit_mutations() -> dict[str, str]:
    mutations = (
        "legacy_rank_estimator",
        "anti_conservative_ties",
        "wrong_finite_floor",
        "independent_component_pairing",
        "diagonal_covariance",
        "linear_biposh_units",
        "mask_ready",
        "multipole_ready",
        "operator_order",
        "wrong_null_family",
        "mask_deconvolution_optional",
        "diagonal_covariance_allowed",
    )
    results: dict[str, str] = {}
    with tempfile.TemporaryDirectory(prefix="pr290-r2-physcode-") as raw:
        root = Path(raw)
        copy_activation_inputs(root)
        original = yaml.safe_load((root / SPEC).read_text(encoding="utf-8"))
        for mutation in mutations:
            payload = copy.deepcopy(original)
            mutate_spec(payload, mutation)
            (root / SPEC).write_text(
                yaml.safe_dump(payload, sort_keys=False), encoding="utf-8"
            )
            decision = build_planck_activation_decision(repository_root=root)
            require(
                decision.terminal == "BLOCKED_CONTRACT_INVALID",
                f"{mutation} escaped contract invalidation: {decision.terminal}",
            )
            require(
                decision.dependency_snapshot == (),
                f"{mutation} reached dependency evaluation",
            )
            require(
                "pipeline contract drifted" in decision.reasons[0],
                f"{mutation} failed through the wrong branch: {decision.reasons}",
            )
            results[mutation] = decision.terminal
        (root / SPEC).write_text(
            yaml.safe_dump(original, sort_keys=False), encoding="utf-8"
        )
    return results


def audit_rank() -> dict[str, object]:
    counterexample = np.array(
        [
            [0.7124909382, -0.4582932305],
            [-0.0194839346, 1.6279099650],
            [0.5488777725, 1.4096506226],
        ]
    )
    exact = tuple(
        observation_inclusive_max_scan(
            counterexample, ("high", "high"), observation_index=index
        ).global_p
        for index in range(3)
    )
    require(exact == (Fraction(2, 3), Fraction(2, 3), Fraction(1)), "exact rank drift")
    rng = np.random.default_rng(290)
    comparisons = 0
    for n_rows in (3, 4, 7):
        for _ in range(8):
            rows = rng.normal(size=(n_rows, 3))
            directions = ("high", "low", "two-sided")
            for observation_index in range(n_rows):
                expected_local, expected_global = independent_rank(
                    rows, directions, observation_index
                )
                observed = observation_inclusive_max_scan(
                    rows, directions, observation_index=observation_index
                )
                require(observed.local_p == expected_local, "local pooled rank mismatch")
                require(observed.global_p == expected_global, "global pooled rank mismatch")
                require(observed.resolution_floor == Fraction(1, n_rows), "wrong floor")
                comparisons += 1
    tied = observation_inclusive_max_scan(
        np.ones((5, 2)), ("high", "high"), observation_index=0
    )
    require(tied.global_p == Fraction(1), "ties are not conservative")
    return {
        "counterexample_global_ranks": [str(value) for value in exact],
        "differential_comparisons": comparisons,
        "tie_global_rank": str(tied.global_p),
        "finite_floor": str(tied.resolution_floor),
    }


def audit_units_covariance_and_boost() -> dict[str, object]:
    units = biposh_feature_units("microK_CMB")
    require(units["alm"] == "microK_CMB", "alm unit drift")
    require(units["cl"] == units["biposh_A"] == "microK_CMB^2", "quadratic unit drift")
    require(
        units["biposh_D"] == units["s_one_half"] == "microK_CMB^4",
        "quartic unit drift",
    )

    covariance = np.array([[2.0, 0.4], [0.4, 1.0]])
    accepted = validate_full_joint_covariance(covariance, ("C2", "A22"))
    require(accepted["rank"] == 2 and accepted["off_diagonal_present"] is True, "SPD rejection")
    refused: list[str] = []
    for name, matrix in (
        ("diagonal", np.eye(2)),
        ("indefinite", np.array([[1.0, 2.0], [2.0, 1.0]])),
        ("singular", np.ones((2, 2))),
    ):
        try:
            validate_full_joint_covariance(matrix, ("C2", "A22"))
        except PlanckLaneContractError:
            refused.append(name)
        else:
            raise AssertionError(f"{name} covariance was accepted")

    import healpy as hp

    zero = ExactBoostOperator(nside=1, lmax=1, beta=0.0)
    theta, phi = hp.pix2ang(1, np.arange(hp.nside2npix(1)))
    require(np.array_equal(zero.doppler, np.ones_like(zero.doppler)), "zero Doppler drift")
    require(np.allclose(zero._theta_ab, theta) and np.allclose(zero._phi_ab, phi), "zero aberration drift")

    epsilon = 1.0e-6
    plus = ExactBoostOperator(nside=1, lmax=1, beta=epsilon)
    minus = ExactBoostOperator(nside=1, lmax=1, beta=-epsilon)
    n_hat = np.stack(
        [np.sin(theta) * np.cos(phi), np.sin(theta) * np.sin(phi), np.cos(theta)], axis=1
    )
    b_hat = np.asarray(
        hp.rotator.dir2vec(264.021, 48.253, lonlat=True), dtype=float
    )
    b_hat /= np.linalg.norm(b_hat)
    mu = n_hat @ b_hat
    doppler_derivative = (plus.doppler - minus.doppler) / (2.0 * epsilon)
    require(np.allclose(doppler_derivative, mu, rtol=1e-8, atol=1e-9), "Doppler sign drift")

    def vectors(operator: ExactBoostOperator) -> np.ndarray:
        return np.stack(
            [
                np.sin(operator._theta_ab) * np.cos(operator._phi_ab),
                np.sin(operator._theta_ab) * np.sin(operator._phi_ab),
                np.cos(operator._theta_ab),
            ],
            axis=1,
        )

    aberration_derivative = (vectors(plus) - vectors(minus)) / (2.0 * epsilon)
    expected_derivative = mu[:, None] * n_hat - b_hat[None, :]
    require(
        np.allclose(aberration_derivative, expected_derivative, rtol=2e-6, atol=2e-8),
        "aberration sign drift",
    )
    return {
        "units": units,
        "covariance_condition_number": accepted["condition_number"],
        "covariance_refusals": refused,
        "zero_boost_finite_identity": True,
        "doppler_and_aberration_first_order_signs": "PASS",
    }


def audit_live_boundary() -> dict[str, object]:
    receipt_before = hashlib.sha256((ROOT / RECEIPT).read_bytes()).hexdigest()
    observed_before = (ROOT / OBSERVED_RESULTS).exists()
    decision = build_planck_activation_decision(repository_root=ROOT)
    receipt_after = hashlib.sha256((ROOT / RECEIPT).read_bytes()).hexdigest()
    observed_after = (ROOT / OBSERVED_RESULTS).exists()
    require(decision.terminal == "BLOCKED_PREDECESSOR_FINAL_SUCCESS", "authentic terminal drift")
    require(decision.numeric_outputs_written == (), "numeric output recorded")
    require(decision.observed_data_executed is False, "observed execution recorded")
    require(decision.network_or_download_side_effect is False, "network side effect recorded")
    require(receipt_before == receipt_after, "frozen receipt mutated")
    require(observed_before == observed_after is False, "observed result directory exists")
    require(decision.data_identity_snapshot["canonical_record_replay"] is True, "native replay not canonical")
    require(decision.data_identity_snapshot["satisfied"] is False, "identity absence promoted")
    capabilities = build_preactivation_capability_snapshot()
    expected = {
        "local_boost": "synthetic_operator_contract_only",
        "global_tilt": "BLOCKED_UNBOUND_GLOBAL_RESPONSE",
        "local_global_rank": "NOT_MEASURED",
        "Q": "BLOCKED_NO_DEPARTURE_BUNDLE_BUDGET",
        "F": "BLOCKED_NO_SIGN_CLEAN_XC_AND_CEILING",
        "Pi": "BLOCKED_NO_Q_OR_F_MEASURE",
        "G_F": "NOT_APPLICABLE_NO_DEPTH_AXIS",
        "likelihood_prior_posterior_evidence": "NOT_APPLICABLE_DIAGNOSTIC_ONLY",
        "family_identification_gate": "BLOCKED_PRE_NATIVE_ATLAS",
    }
    require(all(capabilities.get(key) == value for key, value in expected.items()), "capability ceiling drift")
    require(all(not isinstance(value, (int, float)) for value in capabilities.values()), "numeric capability leaked")
    return {
        "terminal": decision.terminal,
        "canonical_native_record_replay": decision.data_identity_snapshot[
            "canonical_record_replay"
        ],
        "admission_status": decision.data_identity_snapshot["admission_status"],
        "numeric_outputs_written": list(decision.numeric_outputs_written),
        "observed_data_executed": decision.observed_data_executed,
        "network_or_download_side_effect": decision.network_or_download_side_effect,
        "observed_result_directory_absent": not observed_after,
        "receipt_unchanged": receipt_before == receipt_after,
        "capability_ceiling": expected,
    }


def main() -> int:
    result = {
        "schema": "A_PR290_R2_PHYSCODE_ORACLE_V1",
        "candidate_sha": "8da5ea88ab98aa42c8538198ea2d625f7d0f0555",
        "mutations": audit_mutations(),
        "rank": audit_rank(),
        "units_covariance_boost": audit_units_covariance_and_boost(),
        "live_boundary": audit_live_boundary(),
        "status": "PASS",
    }
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
