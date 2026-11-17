"""R62-F1: source-range and equation acceptance must survive a unit change."""
from dataclasses import replace

import numpy as np
import pytest

from bass.background.bianchi_types import build_bianchi_algebra
from bass.background.convention_bridge import build_structure_tensor_with_sign
from bass.background.initial_conditions import CodazziProjectionError
from bass.background.tilted_bianchi_state import (
    SpeciesFluidCongruence, construct_admissible_tilted_state, evaluate_tilted_constraints,
)


@pytest.mark.parametrize("kappa", [2.0766474428449717e-43, 1e30])
@pytest.mark.parametrize("family", ["I", "IX"])
@pytest.mark.parametrize("mode", ["strict", "project_shear_to_codazzi"])
def test_zero_range_rejects_single_tilt_independently_of_einstein_coupling(kappa, family, mode):
    dust = SpeciesFluidCongruence(species="cdm", eps_hat=1., p_hat=0., v_vec=[.1, 0., 0.])
    with pytest.raises(CodazziProjectionError, match="actual divergence range"):
        construct_admissible_tilted_state(family=family, species=[dust], kappa=kappa, codazzi_mode=mode)


@pytest.mark.parametrize("kappa", [2.0766474428449717e-43, 1., 1e30])
def test_compensating_flux_is_not_rejected_by_relative_range_check(kappa):
    sources = [SpeciesFluidCongruence(species="cdm", eps_hat=1., p_hat=0., v_vec=[.1, 0., 0.]),
               SpeciesFluidCongruence(species="baryon", eps_hat=1., p_hat=0., v_vec=[-.1, 0., 0.])]
    state = construct_admissible_tilted_state(family="I", species=sources, kappa=kappa)
    assert state.constraints.is_admissible
    np.testing.assert_array_equal(state.total_matter.q, np.zeros(3))
    assert max(state.constraints.normalized_residuals.values()) < 1e-13


@pytest.mark.parametrize("length_scale,energy_scale", [(1e-22, 1.), (1e12, 1e5)])
def test_ix_admissibility_and_violation_are_unit_covariant(length_scale, energy_scale):
    # Equivalent tuple: geometric inverse-length fields multiply by L,
    # energy density by E, coupling by L^2/E; beta is invariant.
    L, E = length_scale, energy_scale
    n = L*np.diag([1., 2., 3.]); a = np.zeros(3)
    alg = replace(build_bianchi_algebra("IX"), a=a, n=n, C=build_structure_tensor_with_sign(a, n))
    sigma = L*np.array([[0., .1, 0.], [.1, 0., 0.], [0., 0., 0.]])
    rho = 4.99*E
    beta = np.array([0., 0., -.1/4.99])
    dust = SpeciesFluidCongruence(species="cdm", eps_hat=rho*(1-beta@beta), p_hat=0., v_vec=beta)
    kwargs = dict(family="IX", algebra=alg, H=L, closure="hold_H", species=[dust], kappa=L*L/E)
    state = construct_admissible_tilted_state(sigma_ab=sigma, **kwargs)
    assert state.constraints.is_admissible
    assert max(state.constraints.normalized_residuals.values()) < 3e-14
    # A 10% shear perturbation cannot pass solely because all raw residuals
    # are far below a dimensionless absolute floor in a small unit chart.
    with pytest.raises(CodazziProjectionError, match="Constraints violated"):
        construct_admissible_tilted_state(sigma_ab=1.1*sigma, **kwargs)


def test_direct_evaluator_rejects_small_unit_hamiltonian_and_trace_errors():
    coupling = 2.0766474428449717e-43
    dust = SpeciesFluidCongruence(species="cdm", eps_hat=1., p_hat=0., v_vec=[0., 0., 0.])
    state = construct_admissible_tilted_state(family="I", species=[dust], kappa=coupling)
    args = dict(family="I", algebra=state.algebra, geometry=state.geometry,
                total_matter=state.total_matter, kappa=coupling)
    wrong_h = evaluate_tilted_constraints(H=2*state.H, sigma_ab=np.zeros((3, 3)), **args)
    assert abs(wrong_h.hamiltonian_residual) < wrong_h.tolerance
    assert wrong_h.normalized_residuals["hamiltonian"] == pytest.approx(.6)
    assert not wrong_h.is_admissible
    wrong_trace = evaluate_tilted_constraints(H=state.H, sigma_ab=1e-22*np.eye(3), **args)
    assert wrong_trace.shear_trace_error < wrong_trace.tolerance
    assert wrong_trace.normalized_residuals["shear_trace"] > 1.
    assert not wrong_trace.is_admissible
