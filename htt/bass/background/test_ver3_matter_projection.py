from __future__ import annotations

import numpy as np
import pytest

from bass.background.constraints import MatterNormalFrameState
from bass.background.initial_conditions import build_tilted_initial_conditions
from bass.background.matter_projection import (
    SpeciesProjectedState,
    SpeciesRestFrameState,
    project_species_to_normal_frame,
    total_matter_projection,
)
from bass.background.bianchi_types import build_bianchi_algebra
from bass.tilt.species_tilt import TiltedSpeciesParams, decompose_tilted_species


def test_orthogonal_projection_is_identity_source_pack():
    rest = SpeciesRestFrameState(rho_hat=2.0, p_hat=0.5, label="orth")
    projected = project_species_to_normal_frame(rest, np.zeros(3))
    assert projected.rho == pytest.approx(2.0)
    assert projected.p == pytest.approx(0.5)
    assert np.allclose(projected.q, 0.0)
    assert np.allclose(projected.pi, 0.0)


def test_identity_metric_projection_matches_existing_tilted_species_decomposition():
    rest = SpeciesRestFrameState(rho_hat=1.0, p_hat=1.0 / 3.0, label="rad")
    tilt = np.array([0.1, 0.02, 0.0], dtype=np.float64)
    projected = project_species_to_normal_frame(rest, tilt)
    legacy = decompose_tilted_species(TiltedSpeciesParams(rho_hat=1.0, p_hat=1.0 / 3.0, v=tilt, label="rad"))
    assert projected.rho == pytest.approx(legacy.mu)
    assert projected.p == pytest.approx(legacy.p)
    np.testing.assert_allclose(projected.q, legacy.q)
    np.testing.assert_allclose(projected.pi, legacy.pi)


def test_nontrivial_gamma_metric_lowers_tilt_before_projection():
    gamma = np.diag([4.0, 1.0, 1.0]).astype(np.float64)
    rest = SpeciesRestFrameState(rho_hat=2.0, p_hat=0.0, label="dust")
    tilt_up = np.array([0.1, 0.0, 0.0], dtype=np.float64)
    projected = project_species_to_normal_frame(rest, tilt_up, gamma)
    assert projected.tilt_covariant[0] == pytest.approx(0.4)
    assert projected.gamma_lorentz == pytest.approx(1.0 / np.sqrt(1.0 - 0.04))
    assert projected.q[0] == pytest.approx(projected.gamma_lorentz**2 * 2.0 * 0.4)


def test_total_matter_projection_sums_species_componentwise():
    species = (
        project_species_to_normal_frame(SpeciesRestFrameState(rho_hat=1.0, p_hat=0.0, label="cdm"), np.array([0.1, 0.0, 0.0])),
        project_species_to_normal_frame(SpeciesRestFrameState(rho_hat=2.0, p_hat=2.0 / 3.0, label="rad"), np.array([0.0, 0.1, 0.0])),
    )
    total = total_matter_projection(species)
    assert isinstance(total, MatterNormalFrameState)
    assert total.rho == pytest.approx(sum(piece.rho for piece in species))
    assert total.p == pytest.approx(sum(piece.p for piece in species))
    np.testing.assert_allclose(total.q, sum((piece.q for piece in species), start=np.zeros(3)))


def test_total_projection_keeps_anisotropic_stress_trace_free():
    species = (
        project_species_to_normal_frame(SpeciesRestFrameState(rho_hat=1.0, p_hat=0.0, label="x"), np.array([0.1, 0.0, 0.0])),
        project_species_to_normal_frame(SpeciesRestFrameState(rho_hat=1.0, p_hat=0.0, label="y"), np.array([0.0, 0.1, 0.0])),
    )
    total = total_matter_projection(species)
    assert abs(np.trace(total.pi)) < 1.0e-12


def test_tilted_ic_builder_matches_projected_total_source_pack():
    left_rest = SpeciesRestFrameState(rho_hat=1.0, p_hat=0.0, label="left")
    right_rest = SpeciesRestFrameState(rho_hat=1.0, p_hat=0.0, label="right")
    left_projected = project_species_to_normal_frame(left_rest, np.array([0.1, 0.0, 0.0]))
    right_projected = project_species_to_normal_frame(right_rest, np.array([-0.1, 0.0, 0.0]))
    expected = total_matter_projection((left_projected, right_projected))
    ic = build_tilted_initial_conditions(
        algebra=build_bianchi_algebra("V"),
        species=(
            decompose_tilted_species(TiltedSpeciesParams(rho_hat=1.0, p_hat=0.0, v=np.array([0.1, 0.0, 0.0]), label="left")),
            decompose_tilted_species(TiltedSpeciesParams(rho_hat=1.0, p_hat=0.0, v=np.array([-0.1, 0.0, 0.0]), label="right")),
        ),
        sigma_ab=np.zeros((3, 3)),
    )
    assert ic.residuals.gauss == pytest.approx(ic.residuals.gauss)
    np.testing.assert_allclose(ic.matter.q, expected.q)
    np.testing.assert_allclose(ic.matter.pi, expected.pi)
