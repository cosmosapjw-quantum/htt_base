#!/usr/bin/env python3
"""Bounded independent physics/statistics oracle for frozen PR-290.

The exact-rank reference below is intentionally implemented without calling
the production helper's internal scoring functions.  The mutation probe works
in memory and never rewrites candidate or shared files.
"""

from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
from itertools import product
import json
import math
from pathlib import Path
import sys

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(ROOT), str(ROOT / "htt/src"), str(ROOT / "htt")]

from htt.obsstat.planck_post275_lane import (
    PlanckLaneContractError,
    biposh_feature_units,
    observation_inclusive_max_scan,
    validate_full_joint_covariance,
)
from htt.obsstat.boost_biposh_residual import (
    DIPOLE_B_DEG,
    DIPOLE_L_DEG,
    ExactBoostOperator,
)
from htt.src.common.observed_lane_activation import _validate_spec


SPEC = ROOT / "docs/research_program/post_pr275/pr290_spec.yaml"


def reference(rows: np.ndarray, directions: tuple[str, ...], observation: int):
    """Direct exact pooled-rank definition, independent of production code."""
    n_rows, n_statistics = rows.shape
    oriented: list[list[float]] = [[0.0] * n_statistics for _ in range(n_rows)]
    for i in range(n_rows):
        for j, direction in enumerate(directions):
            value = float(rows[i, j])
            if direction == "high":
                oriented[i][j] = value
            elif direction == "low":
                oriented[i][j] = -value
            else:
                held_out = sorted(float(rows[k, j]) for k in range(n_rows) if k != i)
                middle = len(held_out) // 2
                center = (
                    held_out[middle]
                    if len(held_out) % 2
                    else (held_out[middle - 1] + held_out[middle]) / 2.0
                )
                oriented[i][j] = abs(value - center)
    local = []
    for i in range(n_rows):
        local.append(
            tuple(
                Fraction(
                    sum(oriented[k][j] >= oriented[i][j] for k in range(n_rows)),
                    n_rows,
                )
                for j in range(n_statistics)
            )
        )
    minima = [min(row) for row in local]
    selected = minima[observation]
    global_p = Fraction(sum(value <= selected for value in minima), n_rows)
    return tuple(local), global_p


def check_rank() -> dict[str, int]:
    exhaustive = 0
    for n_rows, n_statistics in ((2, 1), (3, 1), (4, 1), (2, 2), (3, 2)):
        for flat in product((-1.0, 0.0, 1.0), repeat=n_rows * n_statistics):
            rows = np.asarray(flat, dtype=float).reshape(n_rows, n_statistics)
            for directions in product(("high", "low", "two-sided"), repeat=n_statistics):
                for observation in range(n_rows):
                    expected_local, expected_global = reference(
                        rows, directions, observation
                    )
                    actual = observation_inclusive_max_scan(
                        rows, directions, observation_index=observation
                    )
                    assert actual.local_p_all_rows == expected_local
                    assert actual.global_p == expected_global
                    assert actual.resolution_floor == Fraction(1, n_rows)
                    assert actual.global_p >= actual.resolution_floor
                    exhaustive += 1

    rng = np.random.default_rng(290)
    metamorphic = 0
    for _ in range(300):
        n_rows = int(rng.integers(2, 9))
        n_statistics = int(rng.integers(1, 5))
        rows = rng.normal(size=(n_rows, n_statistics))
        directions = tuple(
            ("high", "low", "two-sided")[int(value)]
            for value in rng.integers(0, 3, size=n_statistics)
        )
        observation = int(rng.integers(0, n_rows))
        actual = observation_inclusive_max_scan(
            rows, directions, observation_index=observation
        )
        expected_local, expected_global = reference(rows, directions, observation)
        assert actual.local_p_all_rows == expected_local
        assert actual.global_p == expected_global
        permutation = rng.permutation(n_rows)
        new_observation = int(np.flatnonzero(permutation == observation)[0])
        permuted = observation_inclusive_max_scan(
            rows[permutation], directions, observation_index=new_observation
        )
        assert permuted.global_p == actual.global_p
        assert math.isclose(
            permuted.observation_max_score,
            actual.observation_max_score,
            rel_tol=0.0,
            abs_tol=0.0,
        )
        metamorphic += 1
    return {"exhaustive_cases": exhaustive, "metamorphic_cases": metamorphic}


def check_units_and_covariance() -> dict[str, object]:
    assert biposh_feature_units("microK_CMB") == {
        "alm": "microK_CMB",
        "cl": "microK_CMB^2",
        "biposh_A": "microK_CMB^2",
        "biposh_D": "microK_CMB^4",
        "s_one_half": "microK_CMB^4",
        "power_tensor": "dimensionless",
        "parity_ratio": "dimensionless",
        "axis_score": "dimensionless",
    }
    accepted = validate_full_joint_covariance(
        [[2.0, 0.4], [0.4, 1.0]], ("C2", "A22")
    )
    assert accepted["rank"] == accepted["dimension"] == 2
    assert accepted["minimum_eigenvalue"] > 0.0
    rejected = 0
    for matrix in (
        np.eye(2),
        np.array([[1.0, 1.0], [1.0, 1.0]]),
        np.array([[1.0, 2.0], [2.0, 1.0]]),
    ):
        try:
            validate_full_joint_covariance(matrix, ("C2", "A22"))
        except PlanckLaneContractError:
            rejected += 1
    assert rejected == 3
    return {"accepted_spd_rank": accepted["rank"], "rejected_invalid": rejected}


def check_boost_sign_and_zero() -> dict[str, object]:
    import healpy as hp

    zero = ExactBoostOperator(nside=1, lmax=1, beta=0.0)
    theta, phi = hp.pix2ang(1, np.arange(hp.nside2npix(1)))
    assert np.array_equal(zero.doppler, np.ones_like(zero.doppler))
    assert np.allclose(zero._theta_ab, theta, rtol=0.0, atol=1e-15)
    assert np.allclose(zero._phi_ab, phi, rtol=0.0, atol=1e-15)

    beta = 1.23e-3
    positive = ExactBoostOperator(nside=2, lmax=1, beta=beta)
    theta2, phi2 = hp.pix2ang(2, np.arange(hp.nside2npix(2)))
    sky = np.stack(
        (
            np.sin(theta2) * np.cos(phi2),
            np.sin(theta2) * np.sin(phi2),
            np.cos(theta2),
        ),
        axis=1,
    )
    direction = np.asarray(
        hp.rotator.dir2vec(DIPOLE_L_DEG, DIPOLE_B_DEG, lonlat=True), dtype=float
    )
    mu = sky @ (direction / np.linalg.norm(direction))
    assert np.argmax(positive.doppler) == np.argmax(mu)
    assert np.argmin(positive.doppler) == np.argmin(mu)
    assert positive.doppler[np.argmax(mu)] > 1.0
    assert positive.doppler[np.argmin(mu)] < 1.0
    return {"zero_identity": True, "forward_hotter_sign": True}


def probe_spec_guard() -> dict[str, object]:
    spec = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    mutations = {
        "legacy_global_rank_estimator": (
            "pipeline_contract",
            "global_rank_contract",
            "estimator",
            "legacy_lowell_global_calibration_calibrate_max_scan",
        ),
        "anti_conservative_tie_policy": (
            "pipeline_contract",
            "global_rank_contract",
            "tie_policy",
            "strict_greater_than",
        ),
        "wrong_finite_resolution": (
            "pipeline_contract",
            "global_rank_contract",
            "finite_resolution",
            "one_over_null_count",
        ),
        "independent_component_pairing": (
            "pipeline_contract",
            "covariance_contract",
            "component_pairing",
            "independent_SMICA_Commander",
        ),
        "diagonal_covariance_allowed": (
            "pipeline_contract",
            "covariance_contract",
            "diagonal_shortcut_allowed",
            True,
        ),
        "linear_biposh_A_units": (
            "pipeline_contract",
            "harmonic_and_unit_contract",
            "biposh_A_units",
            "microK_CMB",
        ),
        "mask_deconvolution_relabelled_ready": (
            "pipeline_contract",
            "mask_beam_contract",
            "current_status",
            "READY",
        ),
        "multipole_vectors_relabelled_ready": (
            "pipeline_contract",
            "multipole_vector_contract",
            "current_status",
            "READY",
        ),
    }
    accepted_relaxations = []
    for name, (*keys, replacement) in mutations.items():
        candidate = deepcopy(spec)
        cursor = candidate
        for key in keys[:-1]:
            cursor = cursor[key]
        cursor[keys[-1]] = replacement
        try:
            _validate_spec(candidate)
        except Exception:
            continue
        accepted_relaxations.append(name)
    return {
        "mutation_count": len(mutations),
        "accepted_relaxations": accepted_relaxations,
        "candidate_semantic_verdict": (
            "FAIL" if accepted_relaxations else "PASS"
        ),
    }


def main() -> None:
    payload = {
        "schema": "htt.pr290.frozen_physstat_oracle.v1",
        "rank": check_rank(),
        "units_and_covariance": check_units_and_covariance(),
        "boost": check_boost_sign_and_zero(),
        "spec_guard": probe_spec_guard(),
    }
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
