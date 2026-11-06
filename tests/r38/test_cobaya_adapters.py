"""Unit tests for Cobaya Theory and Likelihood adapters.

Phase C of HTT-R38 Observational Convergence.
Tests Theory calculation, derived parameters, and likelihood evaluation across all probe channels.
"""
from __future__ import annotations

import math
import numpy as np
import pytest

from common.cobaya_adapters.theory import KinematicResponseTheory
from common.cobaya_adapters.likelihoods import (
    PlanckLowEllLikelihood,
    RadioCountLikelihood,
    QuaiaLikelihood,
    CF4Likelihood,
    PantheonLikelihood,
    GaiaVSHLikelihood,
    DESIBAOLikelihood,
    HTTJointMultiProbeLikelihood,
)

class MockProvider:
    """Mock Cobaya provider supplying theory results to likelihoods."""
    def __init__(self, theory: KinematicResponseTheory, params: dict):
        self.theory = theory
        self.state = {}
        self.theory.calculate(self.state, want_derived=True, **params)

    def get_result(self, name: str):
        return self.state[name]


def test_theory_calculation_and_derived():
    theory = KinematicResponseTheory()
    theory.initialize()
    
    state = {}
    params = {
        "beta_RO_x_milli": 1.23,
        "beta_RO_y_milli": 0.0,
        "beta_RO_z_milli": 0.0,
        "beta_RM_x_milli": 0.20,
        "beta_RM_y_milli": 0.0,
        "beta_RM_z_milli": 0.0,
        "d_int_x_milli": 0.05,
        "d_int_y_milli": 0.0,
        "d_int_z_milli": 0.0,
        "sigma_1_micro": 5.0,
        "sigma_2_micro": -2.0,
        "sigma_3_micro": 0.0,
        "sigma_4_micro": 0.0,
        "sigma_5_micro": 0.0,
    }
    theory.calculate(state, want_derived=True, **params)
    
    assert "kinematic_model" in state
    assert "derived" in state
    derived = state["derived"]
    
    # beta_RO amplitude ~ 1.23e-3
    assert math.isclose(derived["beta_RO_amp"], 0.00123, rel_tol=1e-6)
    # beta_MO amplitude = 1.23e-3 - 0.20e-3 = 1.03e-3
    assert math.isclose(derived["beta_MO_amp"], 0.00103, rel_tol=1e-6)
    # d_CMB amplitude = 1.23e-3 + 0.05e-3 = 1.28e-3
    assert math.isclose(derived["d_CMB_amp"], 0.00128, rel_tol=1e-6)


def test_individual_likelihoods():
    theory = KinematicResponseTheory()
    theory.initialize()
    params = {
        "beta_RO_x": 0.00123,
        "beta_RO_y": 0.0,
        "beta_RO_z": 0.0,
        "beta_RM_x": 0.00020,
        "beta_RM_y": 0.0,
        "beta_RM_z": 0.0,
        "sigma_1": 1e-5,
    }
    provider = MockProvider(theory, params)

    # 1. Planck
    planck = PlanckLowEllLikelihood()
    planck.initialize()
    planck.provider = provider
    lp_planck = planck.logp()
    assert np.isfinite(lp_planck)

    # 2. Radio
    radio = RadioCountLikelihood()
    radio.initialize()
    radio.provider = provider
    lp_radio = radio.logp()
    assert np.isfinite(lp_radio)

    # 3. Quaia
    quaia = QuaiaLikelihood()
    quaia.initialize()
    quaia.provider = provider
    lp_quaia = quaia.logp()
    assert np.isfinite(lp_quaia)

    # 4. CF4
    cf4 = CF4Likelihood()
    cf4.initialize()
    cf4.provider = provider
    lp_cf4 = cf4.logp()
    assert np.isfinite(lp_cf4)

    # 5. Pantheon+
    pantheon = PantheonLikelihood()
    pantheon.initialize()
    pantheon.provider = provider
    lp_pantheon = pantheon.logp()
    assert np.isfinite(lp_pantheon)

    # 6. Gaia VSH
    gaia = GaiaVSHLikelihood()
    gaia.initialize()
    gaia.provider = provider
    lp_gaia = gaia.logp()
    assert np.isfinite(lp_gaia)

    # 7. DESI BAO
    desi = DESIBAOLikelihood()
    desi.initialize()
    desi.provider = provider
    lp_desi = desi.logp()
    assert np.isfinite(lp_desi)


def test_joint_multi_probe_likelihood():
    theory = KinematicResponseTheory()
    theory.initialize()
    params = {"beta_RO_x": 0.00123, "beta_RM_x": 0.00020}
    provider = MockProvider(theory, params)

    joint = HTTJointMultiProbeLikelihood()
    joint.initialize()
    joint.provider = provider
    lp_joint = joint.logp()
    assert np.isfinite(lp_joint)
    # Check that individual logp sums to joint logp
    sum_individual = 0.0
    for name, p in joint.probes.items():
        p.provider = provider
        sum_individual += p.logp()
    assert math.isclose(lp_joint, sum_individual, rel_tol=1e-10)
