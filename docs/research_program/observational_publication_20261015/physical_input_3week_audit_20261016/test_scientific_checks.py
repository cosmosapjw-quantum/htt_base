import numpy as np
from teff_optical_checks import thermal_mixture_witness, local_optical_rank, fisher_response_gap

def test_positive_weights():
    r=thermal_mixture_witness()
    assert np.min(r['weights_with_hot_endpoint'])>0
    assert np.min(r['weights_without_hot_endpoint'])==0

def test_equal_retained_moments():
    r=thermal_mixture_witness()
    assert all(abs(v[0]-v[1])<1e-12 for v in r['matched_moments'].values())

def test_rate_target_difference():
    r=thermal_mixture_witness()
    assert all(abs(v[0]-v[1])>0.05 for v in r['unidentified_rate_moments'].values())

def test_tail_relative_minimax():
    r=thermal_mixture_witness()
    assert r['pointwise_sharp_minimax_relative_error'][-1] > 0.999

def test_rank_135():
    assert local_optical_rank()['ranks']['optical_1_3_5']==9

def test_radial_rank_and_vorticity():
    r=local_optical_rank();assert r['ranks']['radial_scalar_1_5']==6 and r['vorticity_null_absmax']<1e-15

def test_nuisance_monopole_gauge():
    r=local_optical_rank();assert r['ranks']['optical_plus_4_method_offsets']==12


def test_fisher_response_kernel_outside_energy_number_span():
    r=fisher_response_gap()
    assert r["unidentified_Fisher_residual"]>0.1
    assert r["residual_after_E2_added"]<1e-11
