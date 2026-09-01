"""RED/GREEN contracts for WU-011 processed boost linearization.

The retained-output convergence test uses the authoritative joint ell=0..5
solver.  The omitted-ell=1 mutation is checked in two different spaces:
its pixel-space error must remain O(beta), while the retained ell=2..5
response must be unchanged to numerical tolerance because the simultaneous
joint solve profiles ell=0,1 as nuisance modes.  Conflating those statements
would incorrectly demand nuisance leakage from an exact weighted solve.
"""

from __future__ import annotations

import numpy as np
import pytest


hp = pytest.importorskip(
    "healpy",
    reason="healpy is required by the WU-011 processed linearization contract",
)

from obsstat.lorentz_sky_pullback import (  # noqa: E402
    pullback_thermodynamic_temperature_field,
)
from obsstat.planck_pr3_operator import build_joint_cutsky_operator  # noqa: E402
from obsstat.processed_boost_operator import (  # noqa: E402
    ProcessedBoostOperator,
)
from obsstat.processed_boost_response import (  # noqa: E402
    PositiveAbsoluteSkySpec,
    healpix_sky_directions,
)


pytestmark = pytest.mark.requires_healpy


def _api():
    try:
        from obsstat import processed_boost_linearization as api
    except ImportError as exc:
        pytest.fail(f"WU-011 linearization API missing: {exc}", pytrace=False)
    return api


def _source_sky() -> PositiveAbsoluteSkySpec:
    coefficients = np.zeros(48, dtype=float)
    # ell=2 starts after the ell=1 block.
    coefficients[3:8] = (0.018, -0.011, 0.007, 0.013, -0.009)
    # Keep a wider source band active so processed linearization sees aliasing.
    ell5_start = sum(2 * ell + 1 for ell in range(1, 5))
    coefficients[ell5_start] = 0.006
    coefficients[ell5_start + 5] = -0.004
    ell6_start = sum(2 * ell + 1 for ell in range(1, 6))
    coefficients[ell6_start + 2] = 0.002
    return PositiveAbsoluteSkySpec(2.7255, coefficients, 6, "K_CMB")


def _operator() -> ProcessedBoostOperator:
    nside = 16
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


def _beta_direction() -> np.ndarray:
    direction = np.array([0.4, -0.2, 0.3], dtype=float)
    return direction / np.linalg.norm(direction)


def test_wu011_intrinsic_generator_matches_central_finite_pullback() -> None:
    api = _api()
    source = _source_sky()
    operator = _operator()
    direction = _beta_direction()
    sky_directions = healpix_sky_directions(operator.nside)
    epsilon = 2.0e-6
    plus = pullback_thermodynamic_temperature_field(
        sky_directions,
        epsilon * direction,
        source.evaluate,
    )
    minus = pullback_thermodynamic_temperature_field(
        sky_directions,
        -epsilon * direction,
        source.evaluate,
    )
    central = (plus - minus) / (2.0 * epsilon)
    analytic = api.intrinsic_scalar_generator_map(
        source,
        direction,
        nside=operator.nside,
        processing_lmax=operator.processing_lmax,
    )
    relative = np.linalg.norm(analytic - central) / np.linalg.norm(central)
    assert relative < 2.0e-8


def test_wu011_processed_finite_minus_linear_is_quadratic() -> None:
    api = _api()
    diagnostic = api.finite_to_linear_diagnostic(
        _source_sky(),
        _operator(),
        beta_direction=_beta_direction(),
        amplitudes=(8.0e-4, 4.0e-4, 2.0e-4, 1.0e-4),
    )
    assert diagnostic.amplitudes == (8.0e-4, 4.0e-4, 2.0e-4, 1.0e-4)
    assert 1.8 <= diagnostic.residual_slope <= 2.2
    assert diagnostic.scaled_plateau_relative_spread <= 0.35
    assert all(
        left > right
        for left, right in zip(diagnostic.residual_norms, diagnostic.residual_norms[1:])
    )


def test_wu011_mutations_are_typed_in_pixel_and_retained_spaces() -> None:
    api = _api()
    report = api.mutation_order_diagnostic(
        _source_sky(),
        _operator(),
        beta_direction=_beta_direction(),
        amplitudes=(8.0e-4, 4.0e-4, 2.0e-4, 1.0e-4),
    )
    assert 0.8 <= report.wrong_sign_retained_slope <= 1.2
    assert 0.8 <= report.omitted_l1_pixel_slope <= 1.2
    # The exact weighted joint solve profiles ell=0,1; it must not create a
    # retained signal merely because the diagnostic linear map omits ell=1.
    assert report.omitted_l1_retained_relative_norm <= 2.0e-8


def test_wu011_linearization_refuses_nonunit_direction_and_bad_amplitudes() -> None:
    api = _api()
    source = _source_sky()
    operator = _operator()
    with pytest.raises((TypeError, ValueError), match="unit|direction"):
        api.finite_to_linear_diagnostic(
            source,
            operator,
            beta_direction=np.array([1.0, 1.0, 1.0]),
            amplitudes=(8.0e-4, 4.0e-4, 2.0e-4),
        )
    with pytest.raises((TypeError, ValueError), match="amplitude|positive|finite"):
        api.finite_to_linear_diagnostic(
            source,
            operator,
            beta_direction=_beta_direction(),
            amplitudes=(8.0e-4, 0.0, 2.0e-4),
        )
