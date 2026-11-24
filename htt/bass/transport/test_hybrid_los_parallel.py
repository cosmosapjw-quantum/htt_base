"""R108 S7: process-chunked line of sight reproduces the single-process maps."""

from __future__ import annotations

import numpy as np

from bass.transport.general_lie_stokes import GeneralLieStokesOperator, LieGeometry
from bass.transport.hybrid_los_parallel import los_sky_parallel
from bass.transport.hybrid_los_transfer import history_from_native_states, los_sky


def _history():
    sigma = np.array([[1.0e-3, 0.4e-3, 0.7e-3], [0.4e-3, -0.3e-3, 0.2e-3], [0.7e-3, 0.2e-3, -0.7e-3]])
    op = GeneralLieStokesOperator(4)
    geom = LieGeometry(sigma, np.array([0.05, 0.0, 0.0]), np.diag([0.0, 0.3, 0.3]))
    N = np.linspace(-9.0, 0.0, 41)
    kappa = 5e-2 * np.exp(-2.0 * N[:-1]) * (0.5 * (1.0 + np.tanh((-7.0 - N[:-1]) / 0.3)) + 2e-4)
    dtau = kappa * np.diff(N)
    S = np.zeros(op.dim, dtype=complex)
    states = [S.copy()]
    for k in range(N.size - 1):
        dN = N[k + 1] - N[k]
        S = op.advance_cell(S, dN, geom, dtau[k], source_increment=op.shear_source_vector(sigma, amplitude=dN),
                            substeps=2, bolometric_redshift=True)
        states.append(S.copy())
    g = geom.pack_14()
    return history_from_native_states(op, N, np.array(states), dtau, np.array([N[0], 0.0]), np.stack([g, g]))


def test_parallel_chunks_reproduce_single_process_maps():
    hist = _history()
    rng = np.random.default_rng(4)
    d = rng.normal(size=(240, 3))
    d /= np.linalg.norm(d, axis=1, keepdims=True)
    ref = los_sky(hist, d, max_step=0.05)
    par = los_sky_parallel(hist, d, workers=2, chunks=5, max_step=0.05)
    assert par.diagnostics["chunks"] == 5 and par.diagnostics["n_directions"] == 240
    scale = max(np.max(np.abs(ref.T)), np.max(np.abs(ref.Q)))
    for a, b in ((ref.T, par.T), (ref.Q, par.Q), (ref.U, par.U), (ref.V, par.V)):
        assert np.max(np.abs(a - b)) <= 1e-12 * scale
    assert abs(par.diagnostics["min_total_depth"] - ref.diagnostics["min_total_depth"]) <= 1e-12
