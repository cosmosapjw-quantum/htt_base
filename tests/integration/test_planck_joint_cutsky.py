from __future__ import annotations

import healpy as hp
import numpy as np
import pytest

from obsstat.planck_joint_cutsky import fit_joint_cutsky_lowell
from obsstat.planck_post275_lane import PlanckLaneContractError
from obsstat.planck_pr3_operator import (
    LMAX,
    alm_to_real_vector,
    real_alm_layout,
    real_vector_to_alm,
)


def _mask(nside: int) -> np.ndarray:
    _, _, z = hp.pix2vec(nside, np.arange(hp.nside2npix(nside)))
    mask = (np.abs(z) > 0.20).astype(float)
    mask[(np.abs(z) > 0.20) & (np.abs(z) < 0.32)] = 0.5
    return mask


def _unit_transfers() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    ones = np.ones(LMAX + 1, dtype=float)
    return ones.copy(), ones.copy(), ones.copy(), ones.copy()


@pytest.mark.requires_healpy
@pytest.mark.parametrize("nuisance_scale", [0.0, 1.0, 1.0e3, -1.0e5])
def test_joint_cutsky_fit_recovers_known_lowell_with_arbitrary_monopole_dipole(
    nuisance_scale: float,
) -> None:
    nside = 8
    rng = np.random.default_rng(315)
    nuisance_dimension = len(real_alm_layout(lmin=0, lmax=1))
    retained_dimension = len(real_alm_layout(lmin=2, lmax=LMAX))
    nuisance = nuisance_scale * rng.normal(size=nuisance_dimension)
    retained = rng.normal(size=retained_dimension)
    full = np.concatenate((nuisance, retained))
    sky = hp.alm2map(
        real_vector_to_alm(full, lmin=0, lmax=LMAX),
        nside=nside,
        lmax=LMAX,
    )
    source_beam, source_pixel, target_beam, target_pixel = _unit_transfers()
    result = fit_joint_cutsky_lowell(
        sky,
        common_mask=_mask(nside),
        source_beam=source_beam,
        source_pixel_window=source_pixel,
        target_beam=target_beam,
        target_pixel_window=target_pixel,
    )
    recovered = alm_to_real_vector(
        result.retained_alm, lmin=2, lmax=LMAX
    )
    np.testing.assert_allclose(recovered, retained, rtol=2e-9, atol=2e-9)
    assert result.support_pixels == int(np.count_nonzero(_mask(nside)))
    assert result.weighted_residual_norm < 1e-8 * max(
        1.0, float(np.linalg.norm(full))
    )


@pytest.mark.requires_healpy
def test_masked_region_contamination_cannot_change_joint_cutsky_fit() -> None:
    nside = 8
    rng = np.random.default_rng(31_500)
    full = rng.normal(size=len(real_alm_layout(lmin=0, lmax=LMAX)))
    sky = hp.alm2map(
        real_vector_to_alm(full, lmin=0, lmax=LMAX),
        nside=nside,
        lmax=LMAX,
    )
    mask = _mask(nside)
    source_beam, source_pixel, target_beam, target_pixel = _unit_transfers()

    baseline = fit_joint_cutsky_lowell(
        sky,
        common_mask=mask,
        source_beam=source_beam,
        source_pixel_window=source_pixel,
        target_beam=target_beam,
        target_pixel_window=target_pixel,
    )
    contaminated_map = sky.copy()
    contaminated_map[mask == 0.0] += rng.normal(
        scale=1.0e8, size=np.count_nonzero(mask == 0.0)
    )
    contaminated = fit_joint_cutsky_lowell(
        contaminated_map,
        common_mask=mask,
        source_beam=source_beam,
        source_pixel_window=source_pixel,
        target_beam=target_beam,
        target_pixel_window=target_pixel,
    )
    np.testing.assert_array_equal(
        contaminated.fitted_real_coefficients,
        baseline.fitted_real_coefficients,
    )
    np.testing.assert_array_equal(
        contaminated.retained_alm,
        baseline.retained_alm,
    )


@pytest.mark.requires_healpy
def test_joint_cutsky_fit_abstains_on_rank_or_transfer_failure() -> None:
    nside = 8
    sky = np.ones(hp.nside2npix(nside), dtype=float)
    tiny = np.zeros_like(sky)
    tiny[:8] = 1.0
    source_beam, source_pixel, target_beam, target_pixel = _unit_transfers()
    with pytest.raises(PlanckLaneContractError, match="rank deficient|condition"):
        fit_joint_cutsky_lowell(
            sky,
            common_mask=tiny,
            source_beam=source_beam,
            source_pixel_window=source_pixel,
            target_beam=target_beam,
            target_pixel_window=target_pixel,
        )

    amplifying_target = np.ones(LMAX + 1, dtype=float)
    amplifying_target[2:] = 1.01
    with pytest.raises(PlanckLaneContractError, match="amplify"):
        fit_joint_cutsky_lowell(
            sky,
            common_mask=_mask(nside),
            source_beam=source_beam,
            source_pixel_window=source_pixel,
            target_beam=amplifying_target,
            target_pixel_window=target_pixel,
        )


@pytest.mark.requires_healpy
def test_observation_and_null_joint_operator_configuration_is_one_function() -> None:
    nside = 8
    mask = _mask(nside)
    source_beam, source_pixel, target_beam, target_pixel = _unit_transfers()
    maps = [
        np.zeros(hp.nside2npix(nside), dtype=float),
        np.ones(hp.nside2npix(nside), dtype=float),
    ]
    results = [
        fit_joint_cutsky_lowell(
            pixel_map,
            common_mask=mask,
            source_beam=source_beam,
            source_pixel_window=source_pixel,
            target_beam=target_beam,
            target_pixel_window=target_pixel,
        )
        for pixel_map in maps
    ]
    assert results[0].mask_sha256 == results[1].mask_sha256
    assert results[0].normal_matrix_sha256 == results[1].normal_matrix_sha256
    assert results[0].basis_order == results[1].basis_order
