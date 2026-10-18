"""Coverage/order and finite-band controls for the original-support bridge."""
import numpy as np
import pytest

import original_selected_support as original
from reuse_support_and_remainders import finite_bands, temperature_diagnostics


def test_native_and_must_precede_coarse_coverage_threshold():
    first = np.ones(48, bool); second = first.copy()
    first[0] = False; second[1] = False
    coverage = original.parent_coverage(first & second, 2, 1)
    assert coverage[0] == .5
    # Separate >=.75 thresholds would admit this parent and give a wrong support.
    assert (original.parent_coverage(first, 2, 1)[0] >= .75
            and original.parent_coverage(second, 2, 1)[0] >= .75)
    assert not coverage[0] >= .75


def test_original_threshold_has_exact_integer_child_boundary():
    window = np.ones(12*32**2, bool)
    window[:5] = False
    window[1024:1030] = False
    coverage = original.parent_coverage(window, 32, 1)
    assert coverage[0] >= .995 and coverage[1] < .995


def test_nested_ring_reordering_is_explicit():
    import healpy as hp
    nested = np.zeros(hp.nside2npix(2), bool)
    nested[[0, 7, 15, 33]] = True
    ring = hp.reorder(nested, n2r=True)
    np.testing.assert_array_equal(hp.reorder(ring, r2n=True), nested)
    assert not np.array_equal(ring, nested)


@pytest.mark.parametrize("bad", [np.ones(48), np.ones(47, bool)])
def test_bad_native_coverage_rejected(bad):
    with pytest.raises(ValueError): original.parent_coverage(bad, 2, 1)


def test_finite_bands_keep_large_cancelling_terms_and_reject_missing_remainder():
    low, mid, tail = np.zeros(64), np.ones(64)*1e-7, -np.ones(64)*.99e-7
    obj = {"total_K_CMB": low+mid+tail, "low_2_to_5_K_CMB": low,
           "mid_6_to_8_K_CMB": mid, "tail_9_to_L_K_CMB": tail}
    result = finite_bands(obj)
    assert result["all"]["mid_tail_interference_nK_CMB2"] < 0
    assert result["all"]["norms_nK_CMB"]["mid_6_8"] > result["all"]["norms_nK_CMB"]["total"]*90
    obj["tail_9_to_L_K_CMB"] = np.zeros(64)
    with pytest.raises(ValueError, match="CLOSURE"): finite_bands(obj)


def test_temperature_source_missing_product_not_zero_imputed():
    with pytest.raises(ValueError): temperature_diagnostics(np.ones((8, 32)), [str(i) for i in range(8)])
