"""RED/GREEN contracts for WU-011 Task-7A deterministic evidence."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pytest


pytest.importorskip(
    "healpy",
    reason="healpy is required by the WU-011 Task-7A evidence contract",
)

pytestmark = pytest.mark.requires_healpy

_SOURCE_REVISION = "0" * 40


def _api():
    try:
        from obsstat import processed_boost_evidence as api
    except ImportError as exc:
        pytest.fail(f"WU-011 Task-7A evidence API missing: {exc}", pytrace=False)
    return api


@pytest.fixture(scope="module")
def report():
    return _api().build_task7a_evidence(
        source_revision=_SOURCE_REVISION,
        profile="CI_CORE",
    )


def test_wu011_task7a_exact_reference_and_case_registry(report) -> None:
    api = _api()
    assert report.terminal is api.Task7ATerminal.PASS_TASK7A_CORE_EVIDENCE
    assert report.source_revision == _SOURCE_REVISION
    assert report.profile == "CI_CORE"
    assert tuple(case.case_id for case in report.cases) == (
        "FULL_N8_L7_IDENTITY",
        "FULL_N8_L12_IDENTITY",
        "CUT_N8_L12_REFERENCE",
    )

    expected = api.full_sky_expected_singular_values()
    assert expected.shape == (49,)
    assert expected[-1] == 0.0
    assert np.sum(expected[:-1] ** 2) == pytest.approx(656.0)
    assert np.max(expected[:-1]) / np.min(expected[:-1]) == pytest.approx(
        math.sqrt(63.0 / 8.0)
    )


def test_wu011_task7a_fullsky_oracle_cutoff_and_alias_gates(report) -> None:
    cases = {case.case_id: case for case in report.cases}
    low = cases["FULL_N8_L7_IDENTITY"]
    high = cases["FULL_N8_L12_IDENTITY"]
    cut = cases["CUT_N8_L12_REFERENCE"]

    for case in (low, high):
        assert case.fullsky_spectrum_max_relative_error is not None
        assert case.fullsky_spectrum_max_relative_error <= 2.0e-5
        assert case.fullsky_trace_relative_error is not None
        assert case.fullsky_trace_relative_error <= 2.0e-5
        assert case.fullsky_null_relative <= 2.0e-8
        assert case.ell6_alias_to_neighbor <= 2.0e-6
        assert case.jacobian.metric_whitened_rank == 48
        assert math.isinf(case.jacobian.metric_whitened_condition_number)

    assert report.fullsky_cutoff_relative_drift <= 2.0e-5
    assert cut.ell6_alias_norm > max(low.ell6_alias_norm, high.ell6_alias_norm) * 10.0
    assert cut.ell6_alias_norm > 1.0e-10
    assert cut.monopole_relative_to_nonmonopole_max <= 5.0e-4


def test_wu011_task7a_diagnostics_and_mutations_are_load_bearing(report) -> None:
    assert 1.8 <= report.finite_to_linear.residual_slope <= 2.2
    assert report.finite_to_linear.scaled_plateau_relative_spread <= 0.35

    assert 0.8 <= report.mutations.wrong_sign_retained_slope <= 1.2
    assert 0.8 <= report.mutations.omitted_l1_pixel_slope <= 1.2
    assert report.mutations.omitted_l1_retained_relative_norm <= 2.0e-8

    assert report.fwl.full_solve_max_abs_residual <= 3.0e-12
    assert report.historical.relative_increment_residual <= 2.0e-3
    assert report.historical.sign_mutation_relative_residual >= 1.5
    assert report.transfer_order_relative_difference >= 1.0e-8


def test_wu011_task7a_artifacts_are_deterministic_and_verifiable(
    report,
    tmp_path: Path,
) -> None:
    api = _api()
    first = api.write_task7a_artifacts(report, tmp_path / "first")
    second = api.write_task7a_artifacts(report, tmp_path / "second")

    verified_first = api.verify_task7a_artifacts(first.output_dir)
    verified_second = api.verify_task7a_artifacts(second.output_dir)
    assert verified_first["terminal"] == api.Task7ATerminal.PASS_TASK7A_CORE_EVIDENCE.value
    assert verified_second == verified_first
    assert first.file_sha256 == second.file_sha256

    required = {
        "terminal.json",
        "summary.json",
        "cases.csv",
        "fullsky_singular_spectrum.csv",
        "finite_to_linear_scaling.csv",
        "gate_ratios.csv",
        "metric_spectrum_exact_vs_numerical.png",
        "finite_to_linear_scaling.png",
        "processed_channel_norms.png",
        "normalized_gate_margins.png",
        "FULL_N8_L7_IDENTITY_scientific_jacobian.npy",
        "FULL_N8_L12_IDENTITY_scientific_jacobian.npy",
        "CUT_N8_L12_REFERENCE_scientific_jacobian.npy",
        "CUT_N8_L12_REFERENCE_raw_replay_jacobian.npy",
        "CUT_N8_L12_REFERENCE_ell6_neighbor.npy",
        "CUT_N8_L12_REFERENCE_ell6_alias.npy",
        "CUT_N8_L12_REFERENCE_ell6_decomposition.npy",
        "SHA256SUMS",
    }
    assert required.issubset(set(first.file_sha256) | {"SHA256SUMS"})
