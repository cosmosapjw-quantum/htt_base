from __future__ import annotations

import importlib

import numpy as np
import pytest

from bass.background import (
    CodazziProjectionError,
    build_bianchi_algebra,
    build_orthogonal_initial_conditions,
    build_tilted_initial_conditions,
    project_shear_to_codazzi,
    rescale_bianchi_algebra,
    solve_background_evolution,
)
from bass.background.constraints import MatterNormalFrameState, codazzi_constraint_residual
from bass.background.evolution import BackgroundEvolutionConfig
from bass.background.geometry import build_geometry
from bass.species.barotropic_closures import OrthogonalSpeciesRegistryClosure
from bass.species.registry import SpeciesBackgroundRegistry
from bass.tilt.species_tilt import TiltedSpeciesParams, decompose_tilted_species


ALL_LABELS = ["FLRW", "I", "II", "III", "IV", "V", "VI_0", "VI_h", "VII_0", "VII_h", "VIII", "IX"]


def test_importing_bass_background_package_is_cycle_safe() -> None:
    module = importlib.import_module("bass.background")
    assert hasattr(module, "solve_background_evolution")
    assert hasattr(module, "build_tilted_initial_conditions")


def test_rescale_bianchi_algebra_preserves_group_parameter_and_jacobi() -> None:
    algebra = build_bianchi_algebra("VII_h")
    scaled = rescale_bianchi_algebra(algebra, 3.5)
    assert scaled.h_parameter == pytest.approx(algebra.h_parameter)
    assert scaled.jacobi_residual_norm < 1.0e-12
    assert np.allclose(scaled.C, 3.5 * algebra.C)


@pytest.mark.parametrize("label", ALL_LABELS)
def test_all_types_orthogonal_ic_are_constructed_on_constraint_surface(label: str) -> None:
    sigma_guess = np.diag([2.0e-3, -1.0e-3, -1.0e-3])
    ic = build_orthogonal_initial_conditions(
        algebra=build_bianchi_algebra(label),
        rho=10.0,
        p=0.0,
        sigma_ab=sigma_guess,
        lambda_value=0.0,
        closure="solve_H",
    )
    assert abs(ic.residuals.gauss) < 1.0e-10
    assert np.linalg.norm(ic.residuals.codazzi) < 1.0e-10
    assert ic.metadata.codazzi_satisfied is True


def test_curvature_scale_closure_rescales_algebra_instead_of_matter() -> None:
    algebra = build_bianchi_algebra("V")
    ic = build_orthogonal_initial_conditions(
        algebra=algebra,
        rho=2.0,
        p=0.0,
        sigma_ab=np.zeros((3, 3)),
        H=1.0,
        closure="solve_curvature_scale",
    )
    assert ic.metadata.algebra_scale_factor > 0.0
    assert abs(ic.residuals.gauss) < 1.0e-10
    assert not np.allclose(ic.algebra.C, algebra.C)


def test_project_shear_amplitude_closure_hits_requested_hubble_branch() -> None:
    algebra = build_bianchi_algebra("I")
    sigma_guess = np.diag([2.0e-3, -1.0e-3, -1.0e-3])
    ic = build_orthogonal_initial_conditions(
        algebra=algebra,
        rho=1.0,
        p=0.0,
        sigma_ab=sigma_guess,
        H=0.8,
        closure="project_shear_amplitude",
    )
    assert ic.H == pytest.approx(0.8)
    assert ic.metadata.shear_amplitude_scale > 0.0
    assert abs(ic.residuals.gauss) < 1.0e-10


def test_type_i_single_tilted_species_is_rejected_by_codazzi() -> None:
    algebra = build_bianchi_algebra("I")
    solo = decompose_tilted_species(
        TiltedSpeciesParams(rho_hat=1.0, p_hat=0.0, v=np.array([0.1, 0.0, 0.0]), label="solo")
    )
    with pytest.raises(CodazziProjectionError, match="Codazzi projection failed"):
        build_tilted_initial_conditions(
            algebra=algebra,
            species=[solo],
            sigma_ab=np.zeros((3, 3)),
            H=1.0,
            closure="hold_H",
        )


@pytest.mark.parametrize("label", ALL_LABELS)
def test_all_types_counterstreaming_tilted_ic_smoke(label: str) -> None:
    algebra = build_bianchi_algebra(label)
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
        closure="solve_H",
    )
    assert abs(ic.residuals.gauss) < 1.0e-10
    assert np.linalg.norm(ic.residuals.codazzi) < 1.0e-10
    assert ic.metadata.codazzi_satisfied is True


def test_project_shear_to_codazzi_can_match_nonzero_class_b_momentum_target() -> None:
    algebra = build_bianchi_algebra("V")
    geometry = build_geometry(algebra)
    sigma, meta = project_shear_to_codazzi(
        sigma_ab=np.zeros((3, 3)),
        geometry=geometry,
        target_q=np.array([2.0e-3, 0.0, 0.0]),
        policy="least_squares_project",
    )
    assert meta.residual_norm_after < 1.0e-10
    assert np.linalg.norm(sigma) > 0.0


def _koszul_divergence(sigma, bracket):
    """Contract the Koszul identity directly in an orthonormal invariant frame."""
    axes = np.eye(3)

    def comm(x, y):
        return np.einsum("kij,i,j->k", bracket, x, y)

    def nabla(x, y):
        return np.array([
            (comm(x, y) @ z - comm(y, z) @ x + comm(z, x) @ y) / 2
            for z in axes
        ])

    return np.array([
        -sum(nabla(y, x) @ sigma @ y + x @ sigma @ nabla(y, y) for y in axes)
        for x in axes
    ])


@pytest.mark.parametrize("kappa", [0., 0.4, 2.5])
def test_generic_vi_h_projection_and_residual_against_koszul(kappa):
    algebra = build_bianchi_algebra("VI_h", a_twist=0.5, n1=1., n3=-2.)
    geom = build_geometry(algebra)
    seed = np.array([[0.2, 0.03, -0.11], [0.03, -0.05, 0.07], [-0.11, 0.07, -0.15]])
    flux = np.array([0.11, -0.07, 0.05])
    matter = MatterNormalFrameState(1., 0., q=flux)
    before = _koszul_divergence(seed, algebra.C) + kappa * flux
    np.testing.assert_allclose(codazzi_constraint_residual(seed, matter, geom, kappa=kappa),
                               before, rtol=1e-13, atol=1e-14)
    sigma, meta = project_shear_to_codazzi(sigma_ab=seed, geometry=geom, target_q=flux, kappa=kappa)
    assert meta.rank == 3
    np.testing.assert_array_equal(meta.target_q, flux)
    assert meta.residual_norm_before == pytest.approx(np.linalg.norm(before), abs=1e-14)
    np.testing.assert_allclose(_koszul_divergence(sigma, algebra.C), -kappa * flux, atol=4e-13)
    assert meta.residual_norm_after < 4e-13


def test_zero_flux_vi_h_projection_uses_divergence_kernel():
    algebra = build_bianchi_algebra("VI_h", a_twist=0.5, n1=1., n3=-2.)
    seed = np.diag([0.2, 0.1, -0.3])
    sigma, _ = project_shear_to_codazzi(sigma_ab=seed, geometry=build_geometry(algebra),
                                        target_q=np.zeros(3), kappa=2.5)
    np.testing.assert_allclose(_koszul_divergence(sigma, algebra.C), 0., atol=2e-14)


def test_exceptional_vi_h_rejects_exact_blind_flux_component():
    algebra = build_bianchi_algebra("VI_h", a_twist=2./3., n1=1., n3=-4.)
    # Left-null vector (0,sqrt(n_2),sqrt(-n_3)); no STF shear can source it.
    flux = 0.125 * np.array([0., 1., 2.]) / np.sqrt(5.)
    with pytest.raises(CodazziProjectionError, match="residual=3.125e-01"):
        project_shear_to_codazzi(sigma_ab=np.zeros((3, 3)), geometry=build_geometry(algebra),
                                 target_q=flux, kappa=2.5)


def test_near_exceptional_vi_h_resolves_attainable_flux_without_normal_equations():
    algebra = build_bianchi_algebra("VI_h", a_twist=(2./3.) * 1.00001, n1=1., n3=-4.)
    flux = np.array([0.04, 0.03, -0.008])
    sigma, meta = project_shear_to_codazzi(sigma_ab=np.zeros((3, 3)), geometry=build_geometry(algebra),
                                           target_q=flux)
    assert meta.rank == 3
    np.testing.assert_allclose(_koszul_divergence(sigma, algebra.C), -flux, rtol=0, atol=2e-12)


def test_projection_reports_the_effective_singular_value_rank():
    algebra = build_bianchi_algebra("VI_h", a_twist=(2./3.) * 1.0000001, n1=1., n3=-4.)
    flux = np.array([0.04, 0., 0.])
    sigma, meta = project_shear_to_codazzi(sigma_ab=np.zeros((3, 3)), geometry=build_geometry(algebra),
                                           target_q=flux)
    assert meta.rank == 2
    np.testing.assert_allclose(_koszul_divergence(sigma, algebra.C), -flux, rtol=0, atol=1e-13)


def test_tilted_species_generator_retains_physical_flux_in_both_constraints():
    algebra = build_bianchi_algebra("VI_h", a_twist=0.5, n1=1., n3=-2.)
    v = np.array([0.03, -0.02, 0.01])
    species = decompose_tilted_species(TiltedSpeciesParams(rho_hat=1., p_hat=0., v=v, label="dust"))
    kappa = 0.7
    ic = build_tilted_initial_conditions(algebra=algebra, species=(s for s in [species]), kappa=kappa)
    expected_flux = v / (1. - v @ v)
    np.testing.assert_allclose(ic.matter.q, expected_flux, atol=1e-15)
    np.testing.assert_allclose(_koszul_divergence(ic.sigma_ab, algebra.C), -kappa * expected_flux, atol=1e-13)
    assert ic.metadata.codazzi_satisfied and ic.metadata.gauss_admissible
    np.testing.assert_allclose(ic.residuals.codazzi, 0., atol=1e-13)


def test_short_flrw_background_run_preserves_isotropy() -> None:
    ic = build_orthogonal_initial_conditions(
        algebra=build_bianchi_algebra("FLRW"),
        rho=1.0,
        p=0.0,
        sigma_ab=np.zeros((3, 3)),
    )
    result = solve_background_evolution(
        ic,
        config=BackgroundEvolutionConfig(a_start=1.0e-3, a_end=2.0e-3, n_steps=32),
    )
    assert np.allclose(result.sigma_tensor, 0.0, atol=1.0e-12)
    assert np.max(np.abs(result.electric_weyl)) < 1.0e-12
    assert np.max(np.abs(result.magnetic_weyl)) < 1.0e-12
    assert max(abs(res.gauss) for res in result.residuals) < 5.0e-6


def test_short_bianchi_i_run_tracks_a_cubed_sigma_invariant() -> None:
    sigma0 = np.diag([2.0e-4, -1.0e-4, -1.0e-4])
    ic = build_orthogonal_initial_conditions(
        algebra=build_bianchi_algebra("I"),
        rho=1.0,
        p=0.0,
        sigma_ab=sigma0,
    )
    result = solve_background_evolution(
        ic,
        config=BackgroundEvolutionConfig(a_start=1.0e-3, a_end=2.5e-3, n_steps=48),
    )
    invariant = result.sigma_tensor[:, 0, 0] * result.a**3
    assert np.max(np.abs(invariant - invariant[0])) < 1.0e-6


def test_species_backed_background_run_reaches_reionization_window_with_physical_eta_mapping() -> None:
    species = SpeciesBackgroundRegistry.from_planck2018(recombination_warning_policy="ignore")
    eta_start = 0.5
    eta_end = species.bg_table.eta_at_a(1.0 / 9.0)
    a_start = float(species.bg_table.interp_a(eta_start))
    a_end = float(species.bg_table.interp_a(eta_end))
    rho = 0.0
    p = 0.0
    from bass.species.base import CANONICAL_ORDER, SpeciesLabel

    for label in CANONICAL_ORDER:
        if label is SpeciesLabel.LAMBDA:
            continue
        rho += float(species[label].rho_rest(eta_start))
        p += float(species[label].p_rest(eta_start))
    ic = build_orthogonal_initial_conditions(
        algebra=build_bianchi_algebra("I"),
        rho=rho,
        p=p,
        sigma_ab=np.zeros((3, 3)),
        lambda_value=float(species[SpeciesLabel.LAMBDA].rho_rest(eta_start)),
    )
    result = solve_background_evolution(
        ic,
        config=BackgroundEvolutionConfig(
            a_start=a_start,
            a_end=a_end,
            n_steps=96,
            rtol=1.0e-8,
            atol=1.0e-10,
            solver_method="BDF",
            matter_model_override=OrthogonalSpeciesRegistryClosure(species),
            eta_at_scale_factor=species.bg_table.eta_at_a,
            lambda_value=float(species[SpeciesLabel.LAMBDA].rho_rest(eta_start)),
        ),
    )
    assert result.eta[0] == pytest.approx(eta_start, abs=1.0e-8)
    assert result.eta[-1] == pytest.approx(eta_end, rel=5.0e-4)
    assert result.a[-1] == pytest.approx(1.0 / 9.0, rel=1.0e-6)
