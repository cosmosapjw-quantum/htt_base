"""Acceptance test 6 for R49 GBI-03 general tilted Bianchi evolution & FMO2026 stability."""
from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import pytest

from bass.background.convention_bridge import ALL_TWELVE_FAMILIES
from bass.background.general_tilted_evolution import (
    TiltedEvolutionConfig,
    energy_momentum_ratio_from_primitive,
    evolve_general_tilted_bianchi,
    primitive_from_energy_momentum_ratio,
    run_fournodavlos_two_fluid_bianchi_i_benchmark,
    verify_all_families_evolution_convergence,
)


def test_conservative_primitive_roundtrip() -> None:
    """Logarithmic conserved-ratio conversion inverts cleanly across dust, radiation, and stiff EOS."""
    for K in (0.0, 1.0 / 3.0, 0.42, 0.68):
        v_in = np.array([0.25, -0.18, 0.11], dtype=np.float64)
        lE, r_v = energy_momentum_ratio_from_primitive(1.4, v_in, K)
        eps_out, p_out, v_out, _ = primitive_from_energy_momentum_ratio(lE, r_v, K)
        assert abs(eps_out - 1.4) < 1.0e-13
        assert abs(p_out - K * 1.4) < 1.0e-13
        assert np.max(np.abs(v_out - v_in)) < 1.0e-14


def test_acceptance_6_fournodavlos_two_fluid_bianchi_i_stability_and_all_families() -> None:
    """Acceptance Test 6: reproduce FMO2026 two-fluid Bianchi-I stability & Class A/B constraints."""
    fmo = run_fournodavlos_two_fluid_bianchi_i_benchmark(K_1=0.42, K_2=0.58, lambda_value=1.8, N_end=4.5)
    assert fmo.passed_theorem_regime is True
    assert fmo.shear_decay_ratio < 1.0e-3
    assert fmo.max_speed_along_orbit < 1.0
    assert fmo.max_hamiltonian_residual_rel < 1.0e-9
    assert fmo.max_codazzi_residual_rel < 1.0e-10

    conv = verify_all_families_evolution_convergence()
    assert conv["all_passed"] is True
    assert set(conv["families"].keys()) == set(ALL_TWELVE_FAMILIES)
    for fam, rec in conv["families"].items():
        assert rec["passed"] is True, f"Family {fam} failed convergence check"
        assert rec["max_jacobi_residual"] < 1.0e-13
        assert rec["max_hamiltonian_residual_rel"] < 1.0e-9
        assert rec["max_codazzi_residual_rel"] < 1.0e-9
        assert rec["refinement_diff_H"] < 1.0e-6
        assert rec["refinement_diff_sigma"] < 1.0e-6
        assert rec["refinement_diff_v_photon"] < 1.0e-6
