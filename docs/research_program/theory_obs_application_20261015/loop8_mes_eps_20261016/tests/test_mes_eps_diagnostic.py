"""Small deterministic verification, plus exact source replay of C8-OBS-MES-EPS."""
from __future__ import annotations

import math
import os
from pathlib import Path

import numpy as np
import pytest

from mes_eps_diagnostic import (
    MesEpsAuditError, SLICES, SAME_SKY_NINE, T0_MICROK,
    power_and_epsilon, paired_spread, registered_geodesic_proxy_anchors,
    finite_shell_bound_per_microK, validate_sources, build_result,
)

INPUTS = Path(__file__).resolve().parents[1] / 'inputs'


def test_full_real_harmonic_basis_offsets_and_known_values():
    assert [SLICES[i] for i in range(2,6)] == [(0,5),(5,12),(12,21),(21,32)]
    a = np.zeros(32)
    a[0] = 5.
    cl2,eps2=power_and_epsilon(a,2)
    assert cl2 == 5.
    assert eps2 == pytest.approx(math.sqrt(5)/T0_MICROK)
    assert power_and_epsilon(a,3)[1] == 0.


def test_normalization_scales_with_amplitude():
    x=np.zeros((6,300,32)); x[:,:,5:12]=2.
    cl,e=power_and_epsilon(x,3)
    assert cl.shape==(6,300)
    np.testing.assert_allclose(cl,4,rtol=0,atol=1e-15)
    np.testing.assert_allclose(e,2/T0_MICROK,rtol=0,atol=1e-17)


def test_invalid_harmonic_inputs_fail_closed():
    with pytest.raises(MesEpsAuditError): power_and_epsilon(np.zeros(31),2)
    with pytest.raises(MesEpsAuditError): power_and_epsilon(np.zeros(32),1)
    with pytest.raises(MesEpsAuditError): power_and_epsilon(np.ones(32,dtype=complex),2)
    bad=np.zeros(32);bad[0]=np.nan
    with pytest.raises(MesEpsAuditError): power_and_epsilon(bad,2)
    with pytest.raises(MesEpsAuditError): power_and_epsilon(np.zeros(32),2,0)


def test_integer_harmonics_do_not_overflow_before_power():
    a=np.zeros(32,dtype=np.int64);a[0]=2**32
    cl,_=power_and_epsilon(a,2)
    assert cl==pytest.approx(float(2**64)/5)
    half=np.full(32,300,dtype=np.float16)
    assert power_and_epsilon(half,2)[0]==pytest.approx(90000)
    huge=np.zeros(32);huge[0]=1e200
    with pytest.raises(MesEpsAuditError): power_and_epsilon(huge,2)


def test_geodesic_e1crit_boundary_strict_not_inclusive():
    eps2,eps3=6.2e-6,7.0e-6
    crit=(43/25)*eps2+(9/35)*eps3
    assert registered_geodesic_proxy_anchors(0,eps2,eps3)['strict_hierarchy']
    assert registered_geodesic_proxy_anchors(0,eps2,eps3)['e1crit_strict_hierarchy']==pytest.approx(crit)
    assert registered_geodesic_proxy_anchors(crit*1.1,eps2,eps3)['strict_hierarchy'] is False
    assert registered_geodesic_proxy_anchors(crit*0.9,eps2,eps3)['strict_hierarchy'] is True
    # These finite decimals are exactly on the registered rational boundary.
    assert registered_geodesic_proxy_anchors(0.052,0.025,0.035)['strict_hierarchy'] is False


def test_geodesic_omega_is_epsilon3_independent_and_sigma_positive():
    a=registered_geodesic_proxy_anchors(0,6e-6,7e-6)
    b=registered_geodesic_proxy_anchors(0,6e-6,14e-6)
    assert a['W2_geodesic_algebraic_ceil']==pytest.approx(b['W2_geodesic_algebraic_ceil'])
    assert a['Sigma2_geodesic_algebraic_ceil'] < b['Sigma2_geodesic_algebraic_ceil']
    assert a['W2_geodesic_algebraic_ceil'] > 0


def test_negative_or_nan_eps_rejected():
    for e1,e2,e3 in [(0,-1e-7,2e-7),(0,np.nan,1e-7),(np.inf,0,1e-6)]:
        with pytest.raises(MesEpsAuditError): registered_geodesic_proxy_anchors(e1,e2,e3)


def test_finite_shell_operator_bound_scaling():
    k=1.7542745035333505
    assert finite_shell_bound_per_microK(k,2)==pytest.approx(k/math.sqrt(5)/T0_MICROK)
    assert finite_shell_bound_per_microK(0,2)==0
    with pytest.raises(MesEpsAuditError): finite_shell_bound_per_microK(-1,2)


def test_paired_unit_is_sky_and_not_processing_image():
    obs=np.zeros((3,32));obs[1,0]=1;obs[2,0]=2
    skies=np.broadcast_to(obs[:,None,:],(3,300,32)).copy()
    out=paired_spread(obs,skies,2)
    assert out['n_processing_options_one_observed_sky']==3
    assert out['n_paired_simulation_skies']==300
    assert out['heldout_pairs_conditional']==240
    assert out['paired_heldout_spread_exceedances']==240
    assert out['exploratory_rank_fraction']==1
    assert 'NOT_PHYSICAL' in out['rank_interpretation']


def test_processing_permutation_leaves_same_sky_spread_unchanged():
    rng=np.random.default_rng(42)
    obs=rng.normal(size=(6,32)); skies=rng.normal(size=(6,300,32))
    a=paired_spread(obs,skies,3)
    order=[3,5,1,4,0,2]
    b=paired_spread(obs[order],skies[order],3)
    assert a['observed_eps_spread']==pytest.approx(b['observed_eps_spread'],abs=1e-20)
    assert a['exploratory_rank_fraction']==b['exploratory_rank_fraction']


def test_zero_power_has_undefined_relative_spread_not_nan():
    out=paired_spread(np.zeros((6,32)),np.zeros((6,300,32)),2)
    assert out['observed_eps_spread']==0
    assert out['observed_eps_spread_over_mean'] is None


def test_misaligned_pairing_and_nonfinite_inputs_fail_closed():
    with pytest.raises(MesEpsAuditError): paired_spread(np.zeros((6,32)),np.zeros((5,300,32)),2)
    bad=np.zeros((6,32));bad[0,0]=np.inf
    with pytest.raises(MesEpsAuditError): paired_spread(bad,np.zeros((6,300,32)),2)
    with pytest.raises(MesEpsAuditError): paired_spread(np.zeros((6,32)),np.zeros((6,60,32)),2)


def test_exact_input_hashes_and_wrong_bytes_guard(tmp_path):
    expected=validate_sources(INPUTS)
    assert expected['ffp_response/processing_coefficients.npz']=='0c104e41b2cbd979bbb92b61a43744fb0e17376d26dd8a534cc90ab79ca23b08'
    fake=tmp_path/'loop5';fake.mkdir()
    (fake/'result.json').write_text('{}')
    with pytest.raises(MesEpsAuditError): validate_sources(tmp_path)


@pytest.fixture(scope='module')
def result():
    return build_result(INPUTS)


def test_nine_live_same_sky_power_and_PR124_registry_replay(result):
    nine=result['loop5_nine_same_sky_same_mask']['rows']
    assert tuple(nine)==SAME_SKY_NINE
    assert len(nine)==9
    for v in nine.values():
        assert v['eps2_proxy']>0 and v['eps3_proxy']>0
        assert v['e1crit_for_strict_geodesic_hierarchy']>0
        assert 0<v['W2_geodesic_algebraic_ceil_e1_0']<v['Sigma2_geodesic_algebraic_ceil_e1_0']
    assert result['mes_theory']['actual_residual_cosmological_e1']=='UNIDENTIFIED_NOT_ZERO'


def test_ffp6_real_sky_300_paired_processing_replay(result):
    ffp=result['ffp10_six_pipeline_one_sky']
    assert len(ffp['pipelines'])==6
    for ell in [2,3]:
        out=ffp['paired_calibration'][f'ell{ell}']
        assert out['n_paired_simulation_skies']==300
        assert out['heldout_pairs_conditional']==240
        assert out['observed_eps_spread']>0
        assert out['exploratory_rank_fraction']>=1/241
    assert ffp['comparison_to_loop5']=='FORBIDDEN_DIFFERENT_MASK_PIPELINES'


def test_source_qualification_not_promoted(result):
    assert result['mes_theory']['physical_sigma_or_omega_ceil']=='NOT_ADMITTED'
    assert result['mes_theory']['derivative_copernican_C1_C2']=='UNIDENTIFIED_NOT_ZERO'
    assert result['released_smica_full_INT_BEAM']['l0']==0
    assert result['released_smica_full_INT_BEAM']['l1']==0
    assert result['validation_gate']['physical_EGS_qualifications']=='HOLD'
