"""HEALPix-enabled contracts for WU-011 processed boost response.

The pinned optional-dependency workflow exercises source-transfer ordering and
the actual weighted joint ``ell=0..5`` estimator.  New behavior is introduced
through RED tests before production code.
"""

from __future__ import annotations

import numpy as np
import pytest


hp = pytest.importorskip(
    "healpy",
    reason=(
        "optional dependency 'healpy' not installed; install pinned healpy "
        "to activate WU-011 processed source-transfer tests"
    ),
)

from obsstat.planck_pr3_operator import (  # noqa: E402
    build_joint_cutsky_operator,
    fit_joint_cutsky_alm,
)
from obsstat.processed_boost_response import (  # noqa: E402
    PositiveAbsoluteSkySpec,
    ProcessedBoostOperator,
    evaluate_processed_boost,
    healpix_sky_directions,
    source_convolved_finite_map,
)


pytestmark = pytest.mark.requires_healpy


def _source_sky() -> PositiveAbsoluteSkySpec:
    coefficients = np.zeros(48, dtype=float)
    # ell=1 occupies indices 0..2; ell=2 starts at index 3.
    coefficients[3:8] = (0.018, -0.011, 0.007, 0.013, -0.009)
    # Add an ell=5 component so transfer/boost order probes a wider band.
    ell5_start = sum(2 * ell + 1 for ell in range(1, 5))
    coefficients[ell5_start] = 0.006
    coefficients[ell5_start + 5] = -0.004
    return PositiveAbsoluteSkySpec(2.7255, coefficients, 6, "K_CMB")


def _transfer(processing_lmax: int) -> tuple[np.ndarray, np.ndarray]:
    ell = np.arange(processing_lmax + 1, dtype=float)
    source_beam = np.exp(-0.5 * ell * (ell + 1.0) * 0.075**2)
    source_pixel_window = np.exp(-0.5 * ell * (ell + 1.0) * 0.025**2)
    return source_beam, source_pixel_window


def _mask(nside: int) -> np.ndarray:
    z = healpix_sky_directions(nside)[:, 2]
    # A deterministic apodized north-heavy cut with exact weights in [0,1].
    return np.clip((z + 0.45) / 0.9, 0.0, 1.0)


def _processed_operator() -> tuple[np.ndarray, object, ProcessedBoostOperator]:
    nside = 16
    processing_lmax = 12
    mask = _mask(nside)
    joint = build_joint_cutsky_operator(
        mask,
        lmin=0,
        lmax=5,
        retained_lmin=2,
    )
    source_beam, source_pixel = _transfer(processing_lmax)
    ell = np.arange(processing_lmax + 1, dtype=float)
    target_beam = np.exp(-0.5 * ell * (ell + 1.0) * 0.11**2)
    target_pixel = np.exp(-0.5 * ell * (ell + 1.0) * 0.04**2)
    operator = ProcessedBoostOperator.from_components(
        mask=mask,
        joint_operator=joint,
        processing_lmax=processing_lmax,
        source_beam=source_beam,
        source_pixel_window=source_pixel,
        target_beam=target_beam,
        target_pixel_window=target_pixel,
    )
    return mask, joint, operator


def test_wu011_healpix_direction_registry_is_unit_and_deterministic() -> None:
    directions = healpix_sky_directions(16)
    assert directions.shape == (hp.nside2npix(16), 3)
    np.testing.assert_allclose(
        np.linalg.norm(directions, axis=1), 1.0, rtol=0.0, atol=2.0e-15
    )
    np.testing.assert_array_equal(directions, healpix_sky_directions(16))


def test_wu011_zero_boost_identity_transfer_replays_the_positive_sky() -> None:
    spec = _source_sky()
    nside = 16
    processing_lmax = 12
    ones = np.ones(processing_lmax + 1)
    result = source_convolved_finite_map(
        spec,
        np.zeros(3),
        nside=nside,
        processing_lmax=processing_lmax,
        source_beam=ones,
        source_pixel_window=ones,
    )
    expected = spec.evaluate(healpix_sky_directions(nside))
    np.testing.assert_allclose(
        result.pixel_map, expected, rtol=0.0, atol=3.0e-10
    )
    assert result.mutation is None
    assert result.processing_lmax == processing_lmax


def test_wu011_source_transfer_does_not_commute_with_the_finite_boost() -> None:
    spec = _source_sky()
    nside = 16
    processing_lmax = 12
    beam, pixel = _transfer(processing_lmax)
    beta = np.array([0.018, -0.011, 0.014])
    correct = source_convolved_finite_map(
        spec,
        beta,
        nside=nside,
        processing_lmax=processing_lmax,
        source_beam=beam,
        source_pixel_window=pixel,
    )
    wrong = source_convolved_finite_map(
        spec,
        beta,
        nside=nside,
        processing_lmax=processing_lmax,
        source_beam=beam,
        source_pixel_window=pixel,
        mutation="TRANSFER_BEFORE_BOOST",
    )
    difference = float(np.linalg.norm(correct.pixel_map - wrong.pixel_map))
    anisotropy = correct.pixel_map - np.mean(correct.pixel_map)
    assert difference > 1.0e-7 * float(np.linalg.norm(anisotropy))
    assert correct.content_id != wrong.content_id
    assert wrong.mutation == "TRANSFER_BEFORE_BOOST"


def test_wu011_processed_operator_refuses_a_mask_identity_mismatch() -> None:
    mask, joint, operator = _processed_operator()
    assert operator.joint_operator_id == joint.operator_sha256
    changed = mask.copy()
    changed[0] *= 0.5
    with pytest.raises(ValueError, match="mask|operator identity"):
        ProcessedBoostOperator.from_components(
            mask=changed,
            joint_operator=joint,
            processing_lmax=operator.processing_lmax,
            source_beam=operator.source_beam,
            source_pixel_window=operator.source_pixel_window,
            target_beam=operator.target_beam,
            target_pixel_window=operator.target_pixel_window,
        )


def test_wu011_zero_boost_processed_evaluation_matches_direct_joint_fit() -> None:
    spec = _source_sky()
    mask, joint, operator = _processed_operator()
    evaluated = evaluate_processed_boost(
        spec,
        operator,
        np.zeros(3),
        mode="FINITE",
    )
    source_map = source_convolved_finite_map(
        spec,
        np.zeros(3),
        nside=operator.nside,
        processing_lmax=operator.processing_lmax,
        source_beam=operator.source_beam,
        source_pixel_window=operator.source_pixel_window,
    )
    direct = fit_joint_cutsky_alm(
        source_map.pixel_map,
        mask=mask,
        operator=joint,
        source_beam=operator.source_beam,
        source_pixel_window=operator.source_pixel_window,
        target_beam=operator.target_beam,
        target_pixel_window=operator.target_pixel_window,
    )
    np.testing.assert_allclose(
        evaluated.retained_coefficients,
        direct.retained_coefficients,
        rtol=0.0,
        atol=2.0e-13,
    )
    assert evaluated.retained_coefficients.shape == (32,)
    assert evaluated.operator_id == operator.content_id
    assert evaluated.source_map_id == source_map.content_id


def test_wu011_source_transfer_refuses_unbound_or_invalid_inputs() -> None:
    spec = _source_sky()
    ones = np.ones(13)
    invalid_cases = (
        # RING ordering permits non-power-of-two nside values; zero is invalid.
        dict(nside=0, processing_lmax=12, source_beam=ones, source_pixel_window=ones),
        dict(nside=16, processing_lmax=5, source_beam=np.ones(6), source_pixel_window=np.ones(6)),
        dict(nside=16, processing_lmax=12, source_beam=np.ones(12), source_pixel_window=ones),
        dict(nside=16, processing_lmax=12, source_beam=np.full(13, np.nan), source_pixel_window=ones),
        dict(nside=16, processing_lmax=12, source_beam=ones, source_pixel_window=np.zeros(13)),
    )
    for kwargs in invalid_cases:
        with pytest.raises((TypeError, ValueError), match="nside|lmax|transfer|positive|finite|shape"):
            source_convolved_finite_map(spec, np.zeros(3), **kwargs)
    with pytest.raises(ValueError, match="mutation"):
        source_convolved_finite_map(
            spec,
            np.zeros(3),
            nside=16,
            processing_lmax=12,
            source_beam=ones,
            source_pixel_window=ones,
            mutation="UNKNOWN",
        )
