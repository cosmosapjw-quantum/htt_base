from __future__ import annotations

import numpy as np
import pytest

from bass.background import (
    MatterNormalFrameState,
    background_constraint_residuals,
    background_rhs,
    build_bianchi_algebra,
    build_geometry,
    build_orthogonal_initial_conditions,
    evaluate_background_constraints,
    raychaudhuri_rhs,
    shear_rhs,
    solve_background_evolution,
    summarize_background_residuals,
)
from bass.background.evolution import BackgroundEvolutionConfig
from bass.background.rhs import assemble_background_rhs


def test_background_constraint_residuals_alias_matches_canonical_evaluator() -> None:
    algebra = build_bianchi_algebra("V")
    geometry = build_geometry(algebra)
    matter = MatterNormalFrameState(rho=1.0, p=0.0)
    sigma = np.zeros((3, 3), dtype=np.float64)
    residuals = background_constraint_residuals(
        algebra=algebra,
        geometry=geometry,
        H=1.0,
        sigma_ab=sigma,
        matter=matter,
        lambda_value=0.0,
    )
    canonical = evaluate_background_constraints(
        algebra=algebra,
        geometry=geometry,
        H=1.0,
        sigma_ab=sigma,
        matter=matter,
        lambda_value=0.0,
    )
    assert residuals.gauss == pytest.approx(canonical.gauss)
    np.testing.assert_allclose(residuals.codazzi, canonical.codazzi)
    np.testing.assert_allclose(residuals.jacobi, canonical.jacobi)


def test_background_rhs_alias_matches_existing_assembly() -> None:
    algebra = build_bianchi_algebra("I")
    geometry = build_geometry(algebra)
    sigma = np.diag([2.0e-3, -1.0e-3, -1.0e-3])
    matter = MatterNormalFrameState(rho=3.0, p=0.0)
    lhs = background_rhs(
        H=2.0,
        sigma_ab=sigma,
        matter=matter,
        geometry=geometry,
        lambda_value=0.0,
    )
    rhs = assemble_background_rhs(
        H=2.0,
        sigma_ab=sigma,
        matter=matter,
        geometry=geometry,
        lambda_value=0.0,
    )
    assert lhs.H_dot == pytest.approx(rhs.H_dot)
    np.testing.assert_allclose(lhs.sigma_dot, rhs.sigma_dot)
    assert lhs.rho_dot == pytest.approx(rhs.rho_dot)


def test_raychaudhuri_and_shear_helpers_match_background_rhs_components() -> None:
    algebra = build_bianchi_algebra("V")
    geometry = build_geometry(algebra)
    sigma = np.diag([3.0e-3, -1.5e-3, -1.5e-3])
    matter = MatterNormalFrameState(rho=2.0, p=0.2, pi=np.diag([1.0e-4, -5.0e-5, -5.0e-5]))
    assembly = background_rhs(
        H=1.5,
        sigma_ab=sigma,
        matter=matter,
        geometry=geometry,
        lambda_value=0.0,
    )
    assert assembly.H_dot == pytest.approx(
        raychaudhuri_rhs(
            H=1.5,
            sigma_ab=sigma,
            matter=matter,
            lambda_value=0.0,
        )
    )
    np.testing.assert_allclose(
        assembly.sigma_dot,
        shear_rhs(
            H=1.5,
            sigma_ab=sigma,
            S_ab=geometry.S_AB,
            pi_ab=matter.pi,
        ),
    )


def test_named_branch_background_residual_summary_is_finite_and_dimensionless() -> None:
    ic = build_orthogonal_initial_conditions(
        algebra=build_bianchi_algebra("V"),
        rho=1.0,
        p=0.0,
        sigma_ab=np.zeros((3, 3)),
    )
    result = solve_background_evolution(
        ic,
        config=BackgroundEvolutionConfig(a_start=1.0e-3, a_end=2.0e-3, n_steps=32),
    )
    summary = summarize_background_residuals(result)
    assert summary.samples == 32
    assert np.isfinite(summary.gauss_max_over_H2_ref)
    assert np.isfinite(summary.codazzi_max_over_H2_ref)
    assert np.isfinite(summary.jacobi_max_over_structure_ref)
    assert summary.gauss_max_over_H2_ref < 1.0e-3
    assert summary.codazzi_max_over_H2_ref < 1.0e-4
