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
