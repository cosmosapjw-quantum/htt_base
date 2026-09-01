"""RED/GREEN contracts for WU-011 nuisance and historical parity gates."""

from __future__ import annotations

import numpy as np
import pytest


hp = pytest.importorskip(
    "healpy",
    reason="healpy is required by the WU-011 parity contract",
)

from obsstat.planck_pr3_operator import (  # noqa: E402
    build_joint_cutsky_operator,
    real_vector_to_alm,
)
from obsstat.processed_boost_operator import (  # noqa: E402
    ProcessedBoostOperator,
    evaluate_processed_boost,
)
from obsstat.processed_boost_response import (  # noqa: E402
    PositiveAbsoluteSkySpec,
    healpix_sky_directions,
    source_convolved_finite_map,
)


pytestmark = pytest.mark.requires_healpy


def _api():
    try:
        from obsstat import processed_boost_parity as api
    except ImportError as exc:
        pytest.fail(f"WU-011 parity API missing: {exc}", pytrace=False)
    return api


def _operator(*, nside: int = 8, processing_lmax: int = 12) -> ProcessedBoostOperator:
    z = healpix_sky_directions(nside)[:, 2]
    mask = np.clip((z + 0.45) / 0.9, 0.0, 1.0)
    joint = build_joint_cutsky_operator(mask, lmin=0, lmax=5, retained_lmin=2)
    ell = np.arange(processing_lmax + 1, dtype=float)
    source_beam = np.exp(-0.5 * ell * (ell + 1.0) * 0.075**2)
    source_pixel = np.exp(-0.5 * ell * (ell + 1.0) * 0.025**2)
    target_beam = np.exp(-0.5 * ell * (ell + 1.0) * 0.11**2)
    target_pixel = np.exp(-0.5 * ell * (ell + 1.0) * 0.04**2)
    return ProcessedBoostOperator.from_components(
        mask=mask,
        joint_operator=joint,
        processing_lmax=processing_lmax,
        source_beam=source_beam,
        source_pixel_window=source_pixel,
        target_beam=target_beam,
        target_pixel_window=target_pixel,
    )


def _source_sky() -> PositiveAbsoluteSkySpec:
    coefficients = np.zeros(48, dtype=float)
    coefficients[0:3] = (0.004, -0.003, 0.002)
    coefficients[3:8] = (0.018, -0.011, 0.007, 0.013, -0.009)
    ell5_start = sum(2 * ell + 1 for ell in range(1, 5))
    coefficients[ell5_start] = 0.006
    coefficients[ell5_start + 5] = -0.004
    ell6_start = sum(2 * ell + 1 for ell in range(1, 6))
    coefficients[ell6_start + 2] = 0.002
    return PositiveAbsoluteSkySpec(2.7255, coefficients, 6, "K_CMB")


def test_weighted_fwl_matches_the_authoritative_simultaneous_joint_solve() -> None:
    api = _api()
    source = _source_sky()
    operator = _operator()
    beta = np.array([0.012, -0.007, 0.009], dtype=float)
    source_map = source_convolved_finite_map(
        source,
        beta,
        nside=operator.nside,
        processing_lmax=operator.processing_lmax,
        source_beam=operator.source_beam,
        source_pixel_window=operator.source_pixel_window,
    )
    fwl = api.weighted_fwl_retained_solution(source_map.pixel_map, operator)
    direct = evaluate_processed_boost(source, operator, beta, mode="FINITE")
    np.testing.assert_allclose(
        fwl.retained_scientific_coefficients,
        direct.retained_coefficients,
        atol=3.0e-12,
        rtol=0.0,
    )
    assert fwl.nuisance_rank == 4
    assert fwl.full_solve_max_abs_residual <= 3.0e-12


def test_weighted_fwl_annihilates_a_pure_fitted_nuisance_map() -> None:
    api = _api()
    operator = _operator()
    coefficients = np.zeros(36, dtype=float)
    coefficients[:4] = (2.1, -0.3, 0.2, 0.15)
    alm = real_vector_to_alm(coefficients, lmin=0, lmax=5)
    pixel_map = hp.alm2map(
        alm,
        nside=operator.nside,
        lmax=5,
        pol=False,
    )
    result = api.weighted_fwl_retained_solution(pixel_map, operator)
    assert np.linalg.norm(result.retained_scientific_coefficients) <= 3.0e-11
    assert result.profiled_rhs_norm <= 3.0e-11


def test_historical_fixed_axis_increment_parity_and_sign_kill() -> None:
    api = _api()
    report = api.historical_fixed_axis_parity(
        _source_sky(),
        nside=16,
        lmax=12,
        beta=0.02,
    )
    assert report.relative_increment_residual <= 2.0e-3
    assert report.sign_mutation_relative_residual >= 1.5
    assert report.generic_increment_norm > 0.0
    assert report.legacy_increment_norm > 0.0


def test_historical_parity_refuses_an_incomplete_band() -> None:
    api = _api()
    with pytest.raises(api.HistoricalParityDomainError):
        api.historical_fixed_axis_parity(
            _source_sky(),
            nside=8,
            lmax=5,
            beta=0.02,
        )
