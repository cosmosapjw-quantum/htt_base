"""PA-6 tests for the runtime constraint-residual reporter."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from bass.background.bianchi_types import build_bianchi_algebra
from bass.background.evolution import (
    BackgroundEvolutionConfig,
    solve_background_evolution,
)
from bass.background.initial_conditions import build_orthogonal_initial_conditions
from bass.background.runtime_constraint_reporter import (
    DEFAULT_CONSTRAINT_THRESHOLDS,
    ConstraintCheckpointRecord,
    ConstraintResidualReport,
    build_constraint_residual_report,
    write_constraint_residual_report,
)


@pytest.fixture(scope="module")
def flrw_run() -> object:
    ic = build_orthogonal_initial_conditions(
        algebra=build_bianchi_algebra("FLRW"),
        rho=1.0,
        p=0.0,
        sigma_ab=np.zeros((3, 3)),
    )
    return solve_background_evolution(
        ic,
        config=BackgroundEvolutionConfig(a_start=1.0e-3, a_end=2.0e-3, n_steps=64),
    )


@pytest.fixture(scope="module")
def bianchi_i_run() -> object:
    sigma0 = np.diag([2.0e-4, -1.0e-4, -1.0e-4])
    ic = build_orthogonal_initial_conditions(
        algebra=build_bianchi_algebra("I"),
        rho=1.0,
        p=0.0,
        sigma_ab=sigma0,
    )
    return solve_background_evolution(
        ic,
        config=BackgroundEvolutionConfig(a_start=1.0e-3, a_end=2.0e-3, n_steps=64),
    )


class TestReportShape:
    def test_report_returns_dataclass(self, flrw_run) -> None:
        report = build_constraint_residual_report(flrw_run, family="FLRW")
        assert isinstance(report, ConstraintResidualReport)

    def test_checkpoints_subsampled_at_max_records(self, flrw_run) -> None:
        report = build_constraint_residual_report(
            flrw_run, family="FLRW", max_records=8
        )
        assert len(report.checkpoints) == 8
        assert all(
            isinstance(cp, ConstraintCheckpointRecord) for cp in report.checkpoints
        )

    def test_max_records_zero_disables_checkpoints(self, flrw_run) -> None:
        report = build_constraint_residual_report(
            flrw_run, family="FLRW", max_records=0
        )
        assert report.checkpoints == ()
        # The report itself must remain valid even with zero checkpoints.
        assert report.samples == len(flrw_run.residuals)

    def test_branch_inferred_from_result_when_not_overridden(self, flrw_run) -> None:
        report = build_constraint_residual_report(flrw_run, family="FLRW")
        assert report.branch == flrw_run.branch


class TestThresholdEnforcement:
    def test_flrw_run_passes_default_thresholds(self, flrw_run) -> None:
        report = build_constraint_residual_report(flrw_run, family="FLRW")
        # FLRW orthogonal trajectory must hold all four constraint
        # families below the default threshold.
        for k, v in report.threshold_breaches.items():
            assert v == 0, f"FLRW threshold breach in {k}: {v} samples > threshold"
        assert report.passed is True

    def test_bianchi_i_run_passes_default_thresholds(self, bianchi_i_run) -> None:
        report = build_constraint_residual_report(bianchi_i_run, family="I")
        # Bianchi-I orthogonal trajectory must also hold all four
        # constraint families below threshold.
        assert report.passed is True
        assert report.summary.codazzi_max_over_H2_ref < 1.0e-6

    def test_synthetic_breach_is_detected(self, flrw_run) -> None:
        """A pathologically tight threshold must surface as a breach.

        This is the *load-bearing* test: it proves the reporter actually
        checks the threshold rather than blindly passing.
        """
        report = build_constraint_residual_report(
            flrw_run,
            family="FLRW",
            thresholds={
                # tight enough to ensure at least one sample fails
                "gauss_over_H2_ref": 1.0e-30,
                "codazzi_over_H2_ref": 1.0e-30,
                "jacobi_over_structure_ref": 1.0e-30,
                "bianchi_over_H2_ref": 1.0e-30,
            },
        )
        # At these thresholds, every sample is a breach
        assert report.passed is False
        # Each breach count must be ≤ samples (count is honest)
        for k, v in report.threshold_breaches.items():
            assert 0 <= v <= report.samples


class TestWorstEtaIndex:
    def test_worst_index_is_in_range(self, flrw_run) -> None:
        report = build_constraint_residual_report(flrw_run, family="FLRW")
        for k, idx in report.worst_eta_index.items():
            assert 0 <= idx < report.samples, (
                f"worst_eta_index for {k} out of range: {idx} not in [0, {report.samples})"
            )


class TestSidecarWriter:
    def test_write_produces_valid_json(self, flrw_run, tmp_path: Path) -> None:
        report = build_constraint_residual_report(flrw_run, family="FLRW")
        path = write_constraint_residual_report(report, tmp_path)
        # File exists and parses as JSON
        assert Path(path).is_file()
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        assert payload["family"] == "FLRW"
        assert payload["passed"] is True
        assert "summary" in payload
        assert "threshold_breaches" in payload
        assert "checkpoints" in payload

    def test_write_payload_round_trip(self, bianchi_i_run, tmp_path: Path) -> None:
        report = build_constraint_residual_report(bianchi_i_run, family="I")
        path = write_constraint_residual_report(report, tmp_path)
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        # All threshold keys round-trip with finite numerical values
        assert sorted(payload["thresholds"]) == sorted(DEFAULT_CONSTRAINT_THRESHOLDS)
        for v in payload["thresholds"].values():
            assert np.isfinite(v) and v > 0.0


class TestNonDestructiveContract:
    def test_reporter_does_not_modify_result(self, flrw_run) -> None:
        """The reporter must observe — not mutate — the integration result."""
        eta_before = np.array(flrw_run.eta, copy=True)
        H_before = np.array(flrw_run.H, copy=True)
        n_residuals_before = len(flrw_run.residuals)
        _ = build_constraint_residual_report(flrw_run, family="FLRW")
        np.testing.assert_array_equal(flrw_run.eta, eta_before)
        np.testing.assert_array_equal(flrw_run.H, H_before)
        assert len(flrw_run.residuals) == n_residuals_before
