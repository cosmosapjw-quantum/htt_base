from __future__ import annotations

import healpy as hp
import numpy as np
import pytest

from htt.obsstat.owned_lowell_analysis import analyze_nside16_map


def test_temperature_carrier_has_complete_ell2_to5_layout() -> None:
    nside = 16
    alm = np.zeros(hp.Alm.getsize(5), dtype=complex)
    alm[hp.Alm.getidx(5, 2, 1)] = 2 + 3j
    sky = hp.alm2map(alm, nside, lmax=5)
    result = analyze_nside16_map(sky, np.ones_like(sky), dataset_id="commander", units="uK_CMB", ordering="RING", frame="GALACTIC")
    assert result["carrier_dimension"] == sum(2 * ell + 1 for ell in range(2, 6)) == 32
    assert result["polarization_status"] == "UNAVAILABLE_NO_Q_U"
    assert result["p_value"] is None


def test_mask_and_convention_mutations_are_detected() -> None:
    sky = np.zeros(hp.nside2npix(16))
    mask = np.ones_like(sky)
    with pytest.raises(ValueError, match="RING"):
        analyze_nside16_map(sky, mask, dataset_id="x", units="uK_CMB", ordering="NESTED", frame="GALACTIC")
    mask[0] = 2
    with pytest.raises(ValueError, match="mask-valued"):
        analyze_nside16_map(sky, mask, dataset_id="x", units="uK_CMB", ordering="RING", frame="GALACTIC")
