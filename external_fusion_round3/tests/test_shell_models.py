from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from htt_ext.lowell.discrimination import summarize_simulation
from htt_ext.lowell.shells import simulate_shell_poles
from htt_ext.remote.fields import simulate_remote_fields
from htt_ext.types import ShellGrid, SourceModel


def test_shell_simulation_shapes_and_reproducibility():
    grid = ShellGrid.from_redshifts([0.02, 0.1, 0.3, 0.8, 1.5])
    a = simulate_shell_poles(grid, model=SourceModel.GLOBAL_COHERENT, seed=10)
    b = simulate_shell_poles(grid, model=SourceModel.GLOBAL_COHERENT, seed=10)
    for ell in a.ells:
        assert a.shell_alms[ell].shape == (grid.size, 2 * ell + 1)
        assert np.array_equal(a.shell_alms[ell], b.shell_alms[ell])


def test_local_and_global_have_different_endpoint_remote_geometry():
    grid = ShellGrid.from_redshifts([0.02, 0.08, 0.2, 0.45, 0.8, 1.3, 2.0])
    local = summarize_simulation(simulate_shell_poles(grid, model=SourceModel.LOCAL_BOOST, seed=4)).as_dict()
    global_ = summarize_simulation(simulate_shell_poles(grid, model=SourceModel.GLOBAL_COHERENT, seed=4)).as_dict()
    assert local["ell1_endpoint_remote_angle_deg"] != global_["ell1_endpoint_remote_angle_deg"]


def test_remote_local_boost_not_inserted_into_remote_shells():
    grid = ShellGrid.from_redshifts([0.1, 0.3, 0.7, 1.2])
    iso = simulate_remote_fields(grid, model=SourceModel.ISOTROPIC, seed=11)
    local = simulate_remote_fields(grid, model=SourceModel.LOCAL_BOOST, seed=11)
    assert np.array_equal(iso.dipole_true, local.dipole_true)
    assert np.array_equal(iso.quadrupole_true, local.quadrupole_true)
