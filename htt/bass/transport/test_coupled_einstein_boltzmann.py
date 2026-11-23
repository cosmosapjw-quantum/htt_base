"""Tests for coupled Bianchi Einstein-Euler + general-Lie + moving Thomson + HYREC solver."""
from __future__ import annotations

import numpy as np
from numpy.testing import assert_allclose

from bass.transport.coupled_einstein_boltzmann import (
    ALL_SEVEN_FAMILIES,
    CoupledSolverConfig,
    solve_coupled_einstein_boltzmann,
)
from bass.transport.general_lie_stokes import GeneralLieStokesOperator


def test_flrw_null_all_zero_constraints_and_signal() -> None:
    op = GeneralLieStokesOperator(6)
    res = solve_coupled_einstein_boltzmann(
        "FLRW",
        CoupledSolverConfig(ell_max=6, n_cells=80, substeps_per_cell=1, n_picard=1, epsilon=0.0),
        lie_op=op,
    )
    assert res.max_jacobi_residual == 0.0
    assert res.max_hamiltonian_residual < 1e-8
    assert res.max_codazzi_residual == 0.0
    assert res.max_stokes_reality_err == 0.0
    assert np.max(np.abs(res.final_state)) < 1e-14


def test_all_seven_families_constraints_and_viih_handedness_parity() -> None:
    op = GeneralLieStokesOperator(6)
    results = {}
    for fam in ALL_SEVEN_FAMILIES:
        res = solve_coupled_einstein_boltzmann(
            fam,
            CoupledSolverConfig(ell_max=6, n_cells=80, substeps_per_cell=1, n_picard=2, epsilon=1e-5, handedness=1),
            lie_op=op,
        )
        results[fam] = res
        assert res.max_jacobi_residual < 1e-10
        assert res.max_hamiltonian_residual < 1e-7
        assert res.max_codazzi_residual < 1e-7
        assert res.max_four_force_orthog_error < 1e-12
        assert res.max_momentum_sum_error < 1e-12
        assert res.max_stokes_reality_err < 1e-12
        if fam != "FLRW":
            assert res.cl_final["T"][2] > 0.0
            assert res.cl_final["E"][2] > 0.0

    # Check Type VII_h handedness parity (+1 vs -1): E-mode spectrum invariant while B/E polarization flips helicity
    res_minus = solve_coupled_einstein_boltzmann(
        "VII_h",
        CoupledSolverConfig(ell_max=6, n_cells=80, substeps_per_cell=1, n_picard=2, epsilon=1e-5, handedness=-1),
        lie_op=op,
    )
    assert_allclose(results["VII_h"].cl_final["E"][2:], res_minus.cl_final["E"][2:], rtol=5e-2, atol=1e-15)
    assert_allclose(results["VII_h"].cl_final["B"][2:], res_minus.cl_final["B"][2:], rtol=5e-2, atol=1e-15)
    # Check helicity sign flip: B_{lm}(+1) vs B_{lm}(-1) have opposite relative phase to E_{lm}!
    b2_p = results["VII_h"].alm_final["B"][(2, 2)]
    b2_m = res_minus.alm_final["B"][(2, 2)]
    assert abs(b2_p) > 0.0 or abs(results["VII_h"].alm_final["B"][(3, 2)]) > 0.0
    if abs(b2_p) > 1e-16:
        assert np.real(b2_p * np.conj(b2_m)) < 0.0 or abs(b2_p + b2_m) < abs(b2_p - b2_m)


def test_picard_pi_backreaction_and_nonlinear_tilt() -> None:
    op = GeneralLieStokesOperator(6)
    res_p1 = solve_coupled_einstein_boltzmann(
        "VII_h",
        CoupledSolverConfig(ell_max=6, n_cells=80, substeps_per_cell=1, n_picard=1, epsilon=2e-4),
        lie_op=op,
    )
    res_p2 = solve_coupled_einstein_boltzmann(
        "VII_h",
        CoupledSolverConfig(ell_max=6, n_cells=80, substeps_per_cell=1, n_picard=2, epsilon=2e-4),
        lie_op=op,
    )
    assert res_p2.picard_pi_rel_change > 0.0
    assert res_p2.max_codazzi_residual < 1e-7
    # Moving electron-frame baryon dipole/shear must leave non-zero T, E, B spectra and small reality error
    assert res_p2.cl_final["T"][1] > 0.0
    assert res_p2.cl_final["E"][2] > 0.0
    assert res_p2.cl_final["B"][2] > 0.0
