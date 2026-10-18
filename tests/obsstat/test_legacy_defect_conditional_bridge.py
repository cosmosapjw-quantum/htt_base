"""Legacy three-layer output must preserve source/likelihood and frame assumptions."""
import numpy as np
import pytest
from obsstat.legacy_defect_conditional_bridge import (
    mes_scenario_ceiling,scalar_proxy_from_Cl,matter_tilt_density,
    legacy_pushforward_of_external_bulk_proxy, LegacyDefectBridgeError
)


def test_legacy_defect_limiting_cases_and_tilt_density():
    assert matter_tilt_density(np.array([0]),omega_m=.3153,w=0)[0]==pytest.approx(0)
    beta=np.array([.001334,.002])
    dens=matter_tilt_density(beta,omega_m=.3153,w=0)
    np.testing.assert_allclose(dens,.3153*beta**2,rtol=3e-6)
    assert dens[0]>0 and dens[1]>dens[0]


def test_three_legacy_bounds_order_for_positive_multipoles():
    e2=6e-6;e3=7e-6
    c=mes_scenario_ceiling(.00123,e2,e3)
    assert 0<c['A2_max']<c['W2_max']<c['Sigma2_max']
    assert c['B_sigma']>c['B_omega']>c['B_accel']


def test_ceiling_zero_without_dipole_stays_finite_and_small():
    n=mes_scenario_ceiling(0,6e-6,7e-6)
    y=mes_scenario_ceiling(.0012336,6e-6,7e-6)
    assert 0<n['Sigma2_max']<y['Sigma2_max']
    assert n['Sigma2_max']<1e-8


def test_conditional_velocity_gaussian_pushforward_is_reparam_invariant():
    a=legacy_pushforward_of_external_bulk_proxy(400,80,6e-6,7e-6,
             eps1_ref=.0012336,draws=10000,seed=5)
    b=legacy_pushforward_of_external_bulk_proxy(400,80,6e-6,7e-6,
             eps1_ref=.001476,draws=10000,seed=5)
    np.testing.assert_allclose(a['Omega_tilt_quantiles'],b['Omega_tilt_quantiles'],atol=1e-16)
    assert a['MES_ceiling']<b['MES_ceiling']
    assert a['occupancy_quantiles'][2]>b['occupancy_quantiles'][2]


def test_negative_uncertainty_and_invalid_epsilon_fail_closed():
    with pytest.raises(LegacyDefectBridgeError):
        mes_scenario_ceiling(-1e-3,1e-6,1e-6)
    with pytest.raises(LegacyDefectBridgeError):
        legacy_pushforward_of_external_bulk_proxy(400,-80,6e-6,7e-6,
            eps1_ref=.00123)
    with pytest.raises(LegacyDefectBridgeError):
        scalar_proxy_from_Cl(np.array([-1]),2)
