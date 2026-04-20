"""Tests for VER2 TSC chart-domain guard skeletons."""
from __future__ import annotations

import numpy as np
import pytest

from common.contracts import ArtifactManifest
from tsc.admissibility.domain import (
    build_domain_report,
    check_be_eta_nonpositive,
    check_jacobian_sigma_min,
    check_theta_positive,
    check_weight_simplex,
    guard_production_domain,
)


def _manifest() -> ArtifactManifest:
    return ArtifactManifest(
        artifact_id="tsc.domain",
        artifact_path="artifacts/tsc/domain.json",
        owner="TSC",
        implementation_scope="tsc",
        claim_tier="conditional",
        production_status="production_candidate",
        created_by="test-suite",
        git_commit="abc123",
        config_hash="cfg",
        input_hashes=["a"],
        code_version="0.0-test",
        schema_version="ver2-v1",
    )


def test_theta_positive_passes_for_positive_samples():
    flag = check_theta_positive([1.0, 1.2, 0.9])
    assert flag.ok
    assert flag.value == pytest.approx(0.9)


def test_theta_nonpositive_blocks():
    flag = check_theta_positive([1.0, 0.0, 0.5])
    assert not flag.ok
    assert flag.reason == "theta_nonpositive"


def test_be_eta_nonpositive_blocks_positive_eta():
    flag = check_be_eta_nonpositive([-0.3, 0.1, -0.2])
    assert not flag.ok
    assert flag.reason == "be_eta_positive"


def test_weight_simplex_requires_nonnegative_unit_sum():
    assert check_weight_simplex([0.25, 0.25, 0.5]).ok
    bad = check_weight_simplex([0.2, 0.2, 0.2])
    assert not bad.ok
    assert bad.reason == "weight_simplex_invalid"


def test_jacobian_sigma_min_guard():
    ok = check_jacobian_sigma_min([1.0, 1e-2, 1e-1], floor=1e-3)
    bad = check_jacobian_sigma_min([1.0, 1e-5], floor=1e-3)
    assert ok.ok
    assert not bad.ok
    assert bad.reason == "jacobian_near_singular"


def test_build_domain_report_invalid_domain_collects_reasons():
    report = build_domain_report(
        chart="one_field",
        theta_samples=[1.0, -0.1],
        eta_samples=[-0.2, 0.1],
        weights=[0.2, 0.2, 0.2],
        jacobian_singular_values=[1e-6, 2e-6],
        be_case=True,
        sigma_min_floor=1e-3,
        manifest=_manifest(),
    )
    assert report.status == "invalid_domain"
    assert "theta_nonpositive" in report.blocking_reasons
    assert "be_eta_positive" in report.blocking_reasons
    assert "weight_simplex_invalid" in report.blocking_reasons
    assert "jacobian_near_singular" in report.blocking_reasons


def test_guard_production_domain_raises_on_invalid_domain():
    report = build_domain_report(
        chart="one_field",
        theta_samples=np.array([1.0, -0.5]),
        manifest=_manifest(),
    )
    with pytest.raises(RuntimeError, match="invalid chart domain"):
        guard_production_domain(report)
