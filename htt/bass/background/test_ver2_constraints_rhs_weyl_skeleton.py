from __future__ import annotations

import numpy as np
import pytest

from bass.background.bianchi_types import ALL_BIANCHI_TYPES, build_bianchi_algebra
from bass.background.constraints import MatterNormalFrameState, evaluate_background_constraints
from bass.background.geometry import build_geometry
from bass.background.initial_conditions import (
    build_orthogonal_initial_conditions,
    build_tilted_initial_conditions,
    solve_expanding_H,
)
from bass.background.rhs import assemble_background_rhs
from bass.background.weyl import build_weyl_diagnostics, electric_weyl_from_shear_rhs
from bass.tilt.species_tilt import (
    TiltedSpeciesParams,
    assemble_tilted_matter_state,
    decompose_tilted_species,
)


ALL_LABELS = ["FLRW", *ALL_BIANCHI_TYPES]


@pytest.mark.parametrize("label", ALL_LABELS)
def test_solve_expanding_H_satisfies_gauss_constraint_for_zero_shear(label):
    algebra = build_bianchi_algebra(label)
    geometry = build_geometry(algebra)
    H = solve_expanding_H(
        rho=10.0,
        sigma_ab=np.zeros((3, 3)),
        ricci_scalar=geometry.ricci_scalar,
        lambda_value=0.0,
    )
    residuals = evaluate_background_constraints(
        algebra=algebra,
        geometry=geometry,
        H=H,
        sigma_ab=np.zeros((3, 3)),
        matter=MatterNormalFrameState(rho=10.0, p=0.0),
        lambda_value=0.0,
    )
    assert residuals.gauss == pytest.approx(0.0, abs=1e-12)


@pytest.mark.parametrize("label", ALL_LABELS)
def test_zero_shear_zero_flux_gives_zero_codazzi_residual(label):
    algebra = build_bianchi_algebra(label)
    geometry = build_geometry(algebra)
    residuals = evaluate_background_constraints(
        algebra=algebra,
        geometry=geometry,
        H=1.0,
        sigma_ab=np.zeros((3, 3)),
        matter=MatterNormalFrameState(rho=1.0, p=0.0),
        lambda_value=0.0,
    )
    assert np.allclose(residuals.codazzi, 0.0, atol=1e-12)


def test_orthogonal_ic_builder_returns_machine_readable_residuals():
    ic = build_orthogonal_initial_conditions(
        algebra=build_bianchi_algebra("V"),
        rho=10.0,
        p=0.0,
        sigma_ab=np.zeros((3, 3)),
        lambda_value=0.0,
    )
    assert ic.residuals.gauss == pytest.approx(0.0, abs=1e-12)
    assert np.allclose(ic.residuals.codazzi, 0.0, atol=1e-12)


def test_tilted_matter_assembly_sums_species_channels_componentwise():
    p1 = decompose_tilted_species(
        TiltedSpeciesParams(rho_hat=2.0, p_hat=0.0, v=np.array([0.1, 0.0, 0.0]), label="cdm")
    )
    p2 = decompose_tilted_species(
        TiltedSpeciesParams(rho_hat=1.0, p_hat=1.0 / 3.0, v=np.array([0.0, 0.1, 0.0]), label="photon")
    )
    total = assemble_tilted_matter_state([p1, p2])
    assert total.rho == pytest.approx(p1.mu + p2.mu)
    assert total.p == pytest.approx(p1.p + p2.p)
    assert np.allclose(total.q, p1.q + p2.q)
    assert np.allclose(total.pi, p1.pi + p2.pi)


def test_type_i_counterstreaming_tilt_can_satisfy_codazzi_zero():
    algebra = build_bianchi_algebra("I")
    left = decompose_tilted_species(
        TiltedSpeciesParams(rho_hat=1.0, p_hat=0.0, v=np.array([0.1, 0.0, 0.0]), label="left")
    )
    right = decompose_tilted_species(
        TiltedSpeciesParams(rho_hat=1.0, p_hat=0.0, v=np.array([-0.1, 0.0, 0.0]), label="right")
    )
    ic = build_tilted_initial_conditions(
        algebra=algebra,
        species=[left, right],
        sigma_ab=np.zeros((3, 3)),
    )
    assert np.allclose(ic.matter.q, 0.0, atol=1e-14)
    assert np.allclose(ic.residuals.codazzi, 0.0, atol=1e-12)


def test_type_i_single_tilted_species_leaves_codazzi_mismatch_visible():
    algebra = build_bianchi_algebra("I")
    one = decompose_tilted_species(
        TiltedSpeciesParams(rho_hat=1.0, p_hat=0.0, v=np.array([0.1, 0.0, 0.0]), label="solo")
    )
    ic = build_tilted_initial_conditions(
        algebra=algebra,
        species=[one],
        sigma_ab=np.zeros((3, 3)),
        H=1.0,
        closure="hold_H",
    )
    assert np.linalg.norm(ic.matter.q) > 0.0
    assert np.linalg.norm(ic.residuals.codazzi) > 0.0


def test_type_i_background_rhs_matches_shear_decay_limit():
    algebra = build_bianchi_algebra("I")
    geometry = build_geometry(algebra)
    sigma = np.diag([2.0e-3, -1.0e-3, -1.0e-3])
    matter = MatterNormalFrameState(rho=3.0, p=0.0)
    rhs = assemble_background_rhs(
        H=2.0,
        sigma_ab=sigma,
        matter=matter,
        geometry=geometry,
        lambda_value=0.0,
    )
    assert np.allclose(rhs.sigma_dot, -6.0 * sigma)


def test_flrw_weyl_diagnostics_vanish():
    algebra = build_bianchi_algebra("FLRW")
    geometry = build_geometry(algebra)
    matter = MatterNormalFrameState(rho=1.0, p=0.0)
    rhs = assemble_background_rhs(
        H=1.0,
        sigma_ab=np.zeros((3, 3)),
        matter=matter,
        geometry=geometry,
        lambda_value=0.0,
    )
    weyl = build_weyl_diagnostics(
        sigma_ab=np.zeros((3, 3)),
        sigma_dot_ab=rhs.sigma_dot,
        H=1.0,
        geometry=geometry,
        residuals=rhs.residuals,
        pi_ab=matter.pi,
    )
    assert np.allclose(weyl.electric, 0.0)
    assert np.allclose(weyl.magnetic, 0.0)


def test_electric_weyl_is_trace_free_by_construction():
    sigma = np.diag([1.0e-3, -5.0e-4, -5.0e-4])
    sigma_dot = -3.0 * sigma
    electric = electric_weyl_from_shear_rhs(
        sigma_ab=sigma,
        sigma_dot_ab=sigma_dot,
        H=1.0,
        pi_ab=np.zeros((3, 3)),
    )
    assert abs(np.trace(electric)) < 1e-14
