"""RED/GREEN contracts for the WU-011 processed coefficient Jacobian.

The public tensor is ordered as ``(beta_axis, retained_output, source_mode)``.
Its source registry is the physical monopole temperature followed by the
scientific stored-real ``ell=1..6`` coefficients.  The retained registry is the
scientific stored-real ``ell=2..5`` carrier.

In the exact continuum response, the physical monopole maps only to the fitted
dipole and is profiled from the retained block.  The implemented HEALPix
linearization can leave a disclosed numerical monopole column.  The tests
therefore distinguish raw numerical rank from the rank of the 48 physically
non-monopole source coordinates instead of promoting replay leakage to a new
identifiable mode.
"""

from __future__ import annotations

import numpy as np
import pytest


hp = pytest.importorskip(
    "healpy",
    reason="healpy is required by the WU-011 Jacobian contract",
)

from obsstat.planck_pr3_operator import build_joint_cutsky_operator  # noqa: E402
from obsstat.processed_boost_linearization import (  # noqa: E402
    evaluate_processed_linear_response,
)
from obsstat.processed_boost_operator import (  # noqa: E402
    ProcessedBoostOperator,
    evaluate_processed_boost,
)
from obsstat.processed_boost_response import (  # noqa: E402
    PositiveAbsoluteSkySpec,
    healpix_sky_directions,
)


pytestmark = pytest.mark.requires_healpy


def _api():
    try:
        from obsstat import processed_boost_jacobian as api
    except ImportError as exc:
        pytest.fail(f"WU-011 Jacobian API missing: {exc}", pytrace=False)
    return api


def _operator() -> ProcessedBoostOperator:
    nside = 8
    processing_lmax = 12
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
    coefficients[3:8] = (0.018, -0.011, 0.007, 0.013, -0.009)
    ell5_start = sum(2 * ell + 1 for ell in range(1, 5))
    coefficients[ell5_start] = 0.006
    coefficients[ell5_start + 5] = -0.004
    ell6_start = sum(2 * ell + 1 for ell in range(1, 6))
    coefficients[ell6_start + 2] = 0.002
    return PositiveAbsoluteSkySpec(2.7255, coefficients, 6, "K_CMB")


@pytest.fixture(scope="module")
def jacobian():
    return _api().build_processed_boost_jacobian(_operator())


def test_wu011_jacobian_has_registered_dimensions_and_alias_slice(jacobian) -> None:
    api = _api()
    assert jacobian.tensor.shape == (3, 32, 49)
    assert len(jacobian.source_registry) == 49
    assert len(jacobian.output_registry) == 32
    assert jacobian.ell6_alias_block.shape == (3, 32, 13)
    assert jacobian.source_registry[0] == api.ScientificMode(0, 0, "REAL")
    assert jacobian.source_registry[36] == api.ScientificMode(6, 0, "REAL")
    assert jacobian.source_registry[-1] == api.ScientificMode(6, 6, "IMAG")
    assert jacobian.output_registry[0] == api.ScientificMode(2, 0, "REAL")
    assert jacobian.output_registry[-1] == api.ScientificMode(5, 5, "IMAG")


def test_wu011_jacobian_resolves_all_nonmonopole_source_coordinates(jacobian) -> None:
    assert jacobian.nonmonopole_rank == 48
    assert len(jacobian.nonmonopole_singular_values) == 48
    assert np.all(np.isfinite(jacobian.nonmonopole_singular_values))
    assert np.isfinite(jacobian.nonmonopole_condition_number)
    assert jacobian.nonmonopole_condition_number >= 1.0
    # The raw matrix can acquire one extra numerical direction from the
    # map2alm replay of the analytically nuisance-only monopole response.
    assert jacobian.combined_rank in {48, 49}
    assert len(jacobian.combined_singular_values) == 49
    assert jacobian.monopole_retained_norm <= 5.0e-4
    assert jacobian.monopole_relative_to_nonmonopole_max <= 5.0e-4
    assert np.linalg.norm(jacobian.ell6_alias_block) > 0.0


def test_wu011_jacobian_reconstructs_the_direct_linear_response(jacobian) -> None:
    api = _api()
    source = _source_sky()
    beta = np.array([1.7e-3, -9.0e-4, 1.2e-3], dtype=float)
    predicted = api.predict_processed_linear_response(jacobian, source, beta)
    direct = evaluate_processed_linear_response(source, _operator(), beta)
    scale = max(np.linalg.norm(direct.retained_coefficients), np.finfo(float).tiny)
    relative = np.linalg.norm(predicted - direct.retained_coefficients) / scale
    assert relative <= 2.0e-8


def test_wu011_jacobian_matches_a_centered_finite_boost_derivative(jacobian) -> None:
    api = _api()
    source = _source_sky()
    operator = _operator()
    direction = np.array([0.4, -0.2, 0.3], dtype=float)
    direction /= np.linalg.norm(direction)
    epsilon = 2.0e-3
    plus = evaluate_processed_boost(source, operator, epsilon * direction, mode="FINITE")
    minus = evaluate_processed_boost(source, operator, -epsilon * direction, mode="FINITE")
    centered = (plus.retained_coefficients - minus.retained_coefficients) / (2.0 * epsilon)
    predicted = api.predict_processed_linear_response(jacobian, source, direction)
    scale = max(np.linalg.norm(centered), np.finfo(float).tiny)
    relative = np.linalg.norm(centered - predicted) / scale
    assert relative <= 5.0e-4


def test_wu011_jacobian_arrays_are_content_bound_and_immutable(jacobian) -> None:
    assert jacobian.content_id.startswith("sha256:")
    assert not jacobian.tensor.flags.writeable
    assert not jacobian.ell6_alias_block.flags.writeable
    with pytest.raises(ValueError):
        jacobian.tensor[0, 0, 0] = 1.0
