from __future__ import annotations

from obsstat.lowell_likelihood_branches import classify_lowell_likelihood


def test_central_chi_square_not_allowed_for_deterministic_template():
    result = classify_lowell_likelihood(
        statistic="D2_D3_scalar",
        bianchi_role="deterministic_mean_template",
        orientation_status="not_marginalized",
        covariance_status="not_bound",
    )
    assert result["allowed"] is False
    assert "noncentral_or_harmonic_orientation_required" in result["blocked_reasons"]


def test_covariance_branch_requires_full_covariance():
    result = classify_lowell_likelihood(
        statistic="BiPoSH_or_covariance",
        bianchi_role="stochastic_covariance",
        orientation_status="not_applicable",
        covariance_status="diagonal_only",
    )
    assert result["allowed"] is False
    assert "full_covariance_not_bound" in result["blocked_reasons"]


def test_mean_template_branch_allows_harmonic_marginalized():
    result = classify_lowell_likelihood(
        statistic="harmonic_template_alm",
        bianchi_role="deterministic_mean_template",
        orientation_status="marginalized",
        covariance_status="not_applicable",
    )
    assert result["allowed"] is True
    assert result["blocked_reasons"] == []


def test_covariance_branch_allows_full_covariance():
    result = classify_lowell_likelihood(
        statistic="BiPoSH_or_covariance",
        bianchi_role="stochastic_covariance",
        orientation_status="not_applicable",
        covariance_status="full_anisotropic",
    )
    assert result["allowed"] is True
    assert result["blocked_reasons"] == []
