"""R104 regression: opaque photon cells follow the baryon frame at SDIRK stage times."""
import numpy as np

from bass.transport.coupled_einstein_boltzmann import _advance_moving_photon_cell, sky_energy_momentum_ratios
from bass.transport.general_lie_stokes import GeneralLieStokesOperator, LieGeometry
from bass.transport.moving_collision_stage import MovingCollisionStage, initial_radiation_stokes


def _geometry():
    shear = np.array([[2e-3, 1e-3, 0.], [1e-3, -1e-3, 5e-4], [0., 5e-4, -1e-3]])
    return LieGeometry(shear, np.zeros(3), np.zeros((3, 3)))


def test_constant_velocity_matches_cell_integrator():
    op = GeneralLieStokesOperator(4)
    v = np.array([1.2e-4, -0.7e-4, 0.4e-4])
    geom = _geometry()
    state = initial_radiation_stokes(op, 1.5 * v)
    src = op.shear_source_vector(_geometry_shear(), amplitude=0.3)
    moving = MovingCollisionStage(op, v)
    expected = op.advance_cell(state, 0.3, geom, 5.0, source_increment=src + 5.0 * moving.emission,
                               substeps=4, moving_collision=moving, bolometric_redshift=True)
    got = _advance_moving_photon_cell(op, state, 0.3, geom, src, np.full(4, 5.0 / 4), lambda u: v)
    assert np.linalg.norm(got - expected) <= 1e-12 * np.linalg.norm(expected)


def _geometry_shear():
    return np.array([[2e-3, 1e-3, 0.], [1e-3, -1e-3, 5e-4], [0., 5e-4, -1e-3]])


def test_opaque_cell_relaxes_to_end_of_cell_baryon_frame():
    op = GeneralLieStokesOperator(4)
    zero = LieGeometry(np.zeros((3, 3)), np.zeros(3), np.zeros((3, 3)))
    v0, v1 = np.array([2e-4, 0., 0.]), np.array([1e-4, 5e-5, 0.])
    state = initial_radiation_stokes(op, v0)
    out = _advance_moving_photon_cell(op, state, 0.4, zero, np.zeros(op.dim, complex), np.full(2, 5e3),
                                      lambda u: v0 + u * (v1 - v0))
    q = sky_energy_momentum_ratios(out, op)[0, 1:]
    target = 4 * v1 / (3 + v1 @ v1)
    frozen_mid = 4 * (0.5 * (v0 + v1)) / (3 + (0.5 * (v0 + v1)) @ (0.5 * (v0 + v1)))
    assert np.linalg.norm(q - target) <= 1e-3 * np.linalg.norm(target)
    assert np.linalg.norm(frozen_mid - target) > 0.3 * np.linalg.norm(target)
