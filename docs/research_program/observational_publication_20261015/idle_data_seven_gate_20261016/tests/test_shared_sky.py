import numpy as np
import pytest
from htt_gate_precursors.shared_sky import simulate_same_sky,matched_scan,heldout_rank_p_values,observed_p


def test_correlated_product_sky_count_and_source_identification():
    M=simulate_same_sky(500,4,.3)
    corr=np.corrcoef(M,rowvar=False)
    assert np.mean(corr[np.triu_indices(4,1)])==pytest.approx(1/1.09,abs=.04)
    T=matched_scan(M,tuple('s%d'%i for i in range(500)))
    assert T.shape==(500,)


def test_exhaustive_heldout_uniform_rank_if_distinct():
    T=matched_scan(simulate_same_sky(101,4,.25))
    p=heldout_rank_p_values(T)
    assert np.allclose(np.sort(p),np.arange(1,102)/101)
    # Exact heldout type I error at alpha=0.05: floor(N*alpha)/N.
    assert np.mean(p<=.05)==pytest.approx(5/101)


def test_rank_exceedance_formula_and_minimum_resolution():
    null=np.array([[1.,2.],[2.,2.],[2.1,1.]])
    p=observed_p(np.array([4,0]),null)
    assert p==pytest.approx(.25)
    assert observed_p(np.array([0,0]),null)==pytest.approx(1)


def test_duplicate_sky_id_refused():
    M=simulate_same_sky(3,2,.2)
    with pytest.raises(ValueError):matched_scan(M,('same','same','other'))


def test_method_scan_must_match_null_processing():
    M=np.array([[.1,.2],[.3,.8],[.4,.2]])
    # The predeclared operator scans over both channels for every sky.
    assert np.array_equal(matched_scan(M),[.2,.8,.4])
    assert observed_p(np.array([1.,0.]),M)==.25


def test_wrong_unit_count_gives_fake_minimum_p_resolution():
    n_sky,n_methods=99,4
    valid_min=1/(n_sky+1)
    invalid_min=1/(n_sky*n_methods+1)
    assert valid_min>invalid_min
