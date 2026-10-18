import numpy as np
import pytest
from scipy.stats import norm
from obsstat.typed_xqpi_observation_bridge import (
    C_KM_S,TypedDefectBridgeError,analytic_conditional_tail,
    paired_velocity_quantile_atoms, conditionally_matter_tilt,
    nine_same_sky_geodesic_anchor_scenarios,get_legacy_ceiling,
    strict_known_pi)


def test_exact_gaussian_tail_matches_midpoint_quadrature():
    ids,v=paired_velocity_quantile_atoms(419.,36.,8192)
    om=.3153;cx=6.4743e-6
    x=conditionally_matter_tilt(v,om)
    assert len(set(ids))==len(ids)==8192
    for t in (.01,.05,.1,.5,1.):
        observed=strict_known_pi(x,np.ones(len(x)),cx,t)
        exact=analytic_conditional_tail(t,419.,36.,om,cx)
        assert observed==pytest.approx(exact,abs=1/8192+1e-13)


def test_strict_threshold_zero_atom_and_negative_signed_offset():
    x=analytic_conditional_tail(0.,0.,1.,.3153,1.)
    assert x==pytest.approx(.5)
    assert analytic_conditional_tail(-.1,0.,1.,.3153,1.)==1.
    assert analytic_conditional_tail(.1,419.,36.,.3153,.001,x_offset=-.1)<1.


def test_r204_different_denominators_do_not_commute_with_paired_images():
    _,v=paired_velocity_quantile_atoms(419.,36.,1024)
    x=conditionally_matter_tilt(v,.3153)
    c1=get_legacy_ceiling(.001233,5e-6,7e-6)
    c2=get_legacy_ceiling(.001233,8e-6,5e-6)
    t=.1
    assert strict_known_pi(x,np.ones(len(x)),c1,t)!=strict_known_pi(x,np.ones(len(x)),c2,t)


def test_typed_geodesic_anchor_does_not_supply_accel_curvature_occupancy():
    a=nine_same_sky_geodesic_anchor_scenarios({
        'one':{
        'epsilon2_explicit_sqrtCl_over_T0':6.2e-6,
        'epsilon3_explicit_sqrtCl_over_T0':7e-6}
    })['one']
    assert a['registered_geodesic_sigma_sector_anchor']>0
    assert a['geodesic_acceleration_sector_anchor_status']=='NO_MES_ANCHOR'
    assert a['anisotropic_curvature_anchor_status']=='NO_MES_ANCHOR'
    assert a['CF4_apparent_shear_proxy_to_geodesic_MES_stress_status']=='CHANNEL_MISMATCH'
    assert a['legacy_corrected_shear_anchor_status']=='WITHHELD'


def test_invalid_unnormalized_or_complex_inputs_fail_closed():
    with pytest.raises(TypedDefectBridgeError):
        analytic_conditional_tail(.1,419.,0.,.3153,.001)
    with pytest.raises(TypedDefectBridgeError):
        analytic_conditional_tail(.1,419.,36.,.3153,0.)
    with pytest.raises(TypedDefectBridgeError):
        conditionally_matter_tilt(np.ones(12,dtype=complex),.3153)
    with pytest.raises(TypedDefectBridgeError):
        paired_velocity_quantile_atoms(419.,36.,100)
