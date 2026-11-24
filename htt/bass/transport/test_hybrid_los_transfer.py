"""Tests for the hybrid line-of-sight transfer (native low-ell source x exact Bianchi characteristics)."""

from __future__ import annotations

import numpy as np
import pytest
from scipy.integrate import quad

from bass.transport.general_bianchi_transfer import gl_sphere_grid, map_from_scalar_alm, qu_from_spin2_alm
from bass.transport.general_lie_stokes import (
    GeneralLieStokesOperator,
    LieGeometry,
    stokes_maps_to_vector,
    vector_to_alm_dict,
)
from bass.transport.hybrid_los_transfer import (
    LosSourceHistory,
    healpix_directions,
    history_from_native_states,
    history_window,
    los_alm_healpix,
    los_sky,
    native_alm_to_healpix,
    pack_geometry14,
    trace_rays,
)
from bass.transport.moving_collision_stage import initial_radiation_stokes

ZERO14 = pack_geometry14(np.zeros((3, 3)), np.zeros(3), np.zeros((3, 3)))
SIGMA = np.array([[1.0e-3, 0.4e-3, 0.7e-3], [0.4e-3, -0.3e-3, 0.2e-3], [0.7e-3, 0.2e-3, -0.7e-3]])


def _real_random_state(op, rng, channels, scale=1e-5):
    """Reality-respecting random native vector on the requested (channel, ell_min, ell_max) blocks."""
    x = np.zeros(op.dim, dtype=complex)
    for ch, lo, hi in channels:
        for (ell, m), i in op.idx[ch].items():
            if lo <= ell <= hi and m >= 0:
                x[i] = complex(rng.normal(), rng.normal()) if m else complex(rng.normal(), 0.0)
        for (ell, m), i in op.idx[ch].items():
            if lo <= ell <= hi and m < 0:
                x[i] = (-1) ** m * np.conj(x[op.idx[ch][(ell, -m)]])
    return scale * x


def _shell_history(op, emission_at_shell, geometry14=ZERO14, n_shell=-6.9):
    """Optically thick thin shell at n_shell: the observer sees the shell source function."""
    N = np.array([-7.5, n_shell - 1e-3, n_shell, 0.0])
    em = np.zeros((4, op.dim), dtype=complex)
    em[1] = em[2] = emission_at_shell
    return LosSourceHistory(N=N, delta_tau=np.array([0.0, 1e6, 0.0]), emission=em,
                            initial_state=np.zeros(op.dim, dtype=complex), geometry_N=np.array([-8.0, 0.0]),
                            geometry14=np.stack([geometry14, geometry14]), ell_max_native=op.L)


def _native_run(L, sigma, a, n, n_cells=150, substeps=4):
    """Native hierarchy through a tanh recombination; returns (op, history, final native state)."""
    op = GeneralLieStokesOperator(L)
    geom = LieGeometry(sigma, a, n)
    N = np.linspace(-9.0, 0.0, n_cells + 1)

    def kappa(v):
        return 5e-2 * np.exp(-2.0 * v) * (0.5 * (1.0 + np.tanh((-7.0 - v) / 0.05)) + 2e-4)

    dtau = np.array([quad(kappa, N[k], N[k + 1], limit=200)[0] for k in range(n_cells)])
    S = np.zeros(op.dim, dtype=complex)
    states = [S.copy()]
    for k in range(n_cells):
        dN = N[k + 1] - N[k]
        S = op.advance_cell(S, dN, geom, dtau[k], source_increment=op.shear_source_vector(sigma, amplitude=dN),
                            substeps=substeps, bolometric_redshift=True)
        states.append(S.copy())
    g = geom.pack_14()
    hist = history_from_native_states(op, N, np.array(states), dtau, np.array([N[0], 0.0]), np.stack([g, g]))
    return op, hist, S


def _los_low_ell(hist, n_gl=32, L_out=4):
    _, _, d, _ = gl_sphere_grid(n_gl)
    sky = los_sky(hist, d.reshape(-1, 3), max_step=0.02)
    opo = GeneralLieStokesOperator(L_out)
    vec = stokes_maps_to_vector(np.stack([sky.T, sky.Q, sky.U, sky.V], -1), opo.idx, opo.dim, L=L_out, n_gl_theta=n_gl)
    return opo, vec


def _max_rel(op, S, opo, vec, ch, ell):
    nat = np.array([S[op.idx[ch][(ell, m)]] for m in range(-ell, ell + 1)])
    los = np.array([vec[opo.idx[ch][(ell, m)]] for m in range(-ell, ell + 1)])
    return float(np.max(np.abs(los - nat)) / np.max(np.abs(nat)))


def test_pack_geometry14_matches_lie_geometry():
    sig = np.array([[1e-3, 2e-4, 3e-4], [2e-4, -4e-4, 1e-4], [3e-4, 1e-4, -6e-4]])
    a, n = np.array([0.1, 0.0, 0.0]), np.diag([0.0, 0.4, 0.4])
    # LieGeometry removes the floating-point trace of sigma; the order of the 14 slots must agree
    assert np.allclose(pack_geometry14(sig, a, n), LieGeometry(sig, a, n).pack_14(), rtol=0.0, atol=1e-15)


def test_flrw_static_source_is_reproduced_exactly():
    op = GeneralLieStokesOperator(4)
    x = _real_random_state(op, np.random.default_rng(3), (("T", 0, 2), ("E", 2, 2), ("B", 2, 2), ("V", 1, 1)))
    _, _, d, _ = gl_sphere_grid(12)
    dirs = d.reshape(-1, 3)
    sky = los_sky(_shell_history(op, x), dirs, max_step=0.05)
    al = vector_to_alm_dict(x, op.idx)
    th, ph = np.arccos(np.clip(dirs[:, 2], -1, 1)), np.arctan2(dirs[:, 1], dirs[:, 0])
    Q, U = qu_from_spin2_alm(al["E"], al["B"], th, ph, ell_max=4)
    assert np.max(np.abs(sky.T - map_from_scalar_alm(al["T"], th, ph, ell_max=4))) < 1e-12
    assert np.max(np.abs(sky.Q - Q)) < 1e-15 and np.max(np.abs(sky.U - U)) < 1e-15
    assert np.max(np.abs(sky.V - map_from_scalar_alm(al["V"], th, ph, ell_max=4))) < 1e-15


def test_bianchi_i_redshift_and_direction_match_closed_form():
    # constant H-normalised shear: a_i = exp(N + s_i N) and conserved covariant momenta
    s = np.array([2e-3, -0.5e-3, -1.5e-3])
    g = pack_geometry14(np.diag(s), np.zeros(3), np.zeros((3, 3)))
    op = GeneralLieStokesOperator(2)
    _, _, d, _ = gl_sphere_grid(12)
    dirs = d.reshape(-1, 3)
    n_shell = -6.9
    sky = los_sky(_shell_history(op, np.zeros(op.dim, dtype=complex), g, n_shell), dirs, max_step=0.01)
    delta = 0.5 * np.log(np.sum(dirs ** 2 * np.exp(-2 * s * n_shell), axis=1))
    assert np.max(np.abs(sky.T - 0.25 * np.expm1(-4.0 * delta))) < 1e-10
    for k, n_k, delta_k, _ in trace_rays(dirs, np.array([n_shell, 0.0]), np.array([-8.0, 0.0]),
                                         np.stack([g, g]), max_step=0.01):
        if k == 0:
            exact = dirs * np.exp(-s * n_shell)
            exact /= np.linalg.norm(exact, axis=1, keepdims=True)
            assert np.max(np.abs(n_k - exact)) < 1e-10 and np.max(np.abs(delta_k - delta)) < 1e-10


def test_line_of_sight_reproduces_native_hierarchy_in_class_b_geometry():
    # VII_h-like Lie algebra (a = (A,0,0), n = diag(0, n2, n2), n a = 0) with a finite recombination
    op, hist, S_final = _native_run(10, SIGMA, np.array([0.05, 0.0, 0.0]), np.diag([0.0, 0.3, 0.3]))
    opo, vec = _los_low_ell(hist)
    for ch, ell, tol in (("T", 1, 2e-5), ("T", 2, 2e-5), ("T", 3, 2e-5), ("E", 2, 4e-4), ("B", 2, 4e-4), ("B", 3, 4e-4)):
        assert _max_rel(op, S_final, opo, vec, ch, ell) < tol, (ch, ell)


def test_native_truncation_is_exposed_by_the_line_of_sight_in_a_focusing_geometry():
    a, n = np.array([0.3, 0.0, 0.0]), np.diag([0.0, 0.6, 0.6])
    errs = {}
    for L in (8, 16):
        op, hist, S_final = _native_run(L, SIGMA, a, n)
        opo, vec = _los_low_ell(hist)
        errs[L] = _max_rel(op, S_final, opo, vec, "T", 4)
    assert errs[8] > 1e-2 and errs[16] < 1e-3, errs


def test_boosted_blackbody_behind_a_thick_shell_is_reproduced_with_moving_electrons():
    op = GeneralLieStokesOperator(6)
    beta = np.array([2e-3, -1e-3, 5e-4])
    S = initial_radiation_stokes(op, beta)
    N = np.array([-7.5, -7.0, -6.99, 0.0])
    states = np.stack([S, S, S, np.zeros(op.dim, dtype=complex)])
    hist = history_from_native_states(op, N, states, np.array([0.0, 1e7, 0.0]), np.array([-8.0, 0.0]),
                                      np.stack([ZERO14, ZERO14]), beta=np.stack([beta] * 3 + [np.zeros(3)]))
    _, _, d, _ = gl_sphere_grid(24)
    sky = los_sky(hist, d.reshape(-1, 3), max_step=0.05, max_source_truncation=1e-6)
    vec = stokes_maps_to_vector(np.stack([sky.T, sky.Q, sky.U, sky.V], -1), op.idx, op.dim, L=6, n_gl_theta=24)
    assert np.max(np.abs(vec - S)) < 1e-12
    assert np.max(np.abs(sky.T + d.reshape(-1, 3) @ beta)) < 2.0 * float(beta @ beta)


def test_native_polarization_convention_matches_healpix():
    pytest.importorskip("healpy")
    lmax, nside = 8, 16
    op = GeneralLieStokesOperator(lmax)
    x = _real_random_state(op, np.random.default_rng(5), (("T", 1, 2), ("E", 2, 2), ("B", 2, 2)))
    sky = los_sky(_shell_history(op, x), healpix_directions(nside), max_step=0.05)
    alm = los_alm_healpix(sky, nside, lmax, iterations=8)
    ref = vector_to_alm_dict(x, op.idx)
    for ch in ("T", "E", "B"):
        r = native_alm_to_healpix(ref[ch], lmax)
        assert np.max(np.abs(alm[ch] - r)) < 1e-7 * np.max(np.abs(r)), ch


def test_history_and_truncation_fail_closed():
    op = GeneralLieStokesOperator(2)
    em = np.zeros((3, op.dim), dtype=complex)
    good = dict(N=np.array([-2.0, -1.0, 0.0]), delta_tau=np.array([1.0, 0.0]), emission=em,
                initial_state=np.zeros(op.dim, dtype=complex), geometry_N=np.array([-2.0, 0.0]),
                geometry14=np.stack([ZERO14, ZERO14]), ell_max_native=2)
    LosSourceHistory(**good)
    for key, bad in (("N", np.array([-2.0, -1.0, -0.5])), ("N", np.array([-1.0, -2.0, 0.0])),
                     ("delta_tau", np.array([1.0, -1.0])), ("geometry_N", np.array([-1.0, 0.0])),
                     ("emission", np.zeros((2, op.dim), dtype=complex))):
        with pytest.raises(ValueError):
            LosSourceHistory(**{**good, key: bad})
    op4 = GeneralLieStokesOperator(4)
    em4 = np.zeros((3, op4.dim), dtype=complex)
    em4[:, op4.idx["T"][(4, 0)]] = 1.0
    hist = LosSourceHistory(**{**good, "emission": em4, "initial_state": np.zeros(op4.dim, dtype=complex),
                               "ell_max_native": 4})
    with pytest.raises(ValueError, match="beyond ell"):
        los_sky(hist, np.array([[0.0, 0.0, 1.0]]), source_ell_max=2)


def _hyrec_tables_present() -> bool:
    from bass.recombination.tilted_hyrec import DEFAULT_ATOMIC_DIR

    return (DEFAULT_ATOMIC_DIR / "Alpha_inf.dat").is_file()


@pytest.mark.skipif(not _hyrec_tables_present(),
                    reason="needs HYREC-2 tables in data/external/r101_legacy_recovery/hyrec_atomic (local workstation)")
def test_coupled_solver_history_feeds_the_line_of_sight():
    """Coupled run -> history -> LoS must reproduce the native low-ell observer state.

    Tolerances are the first-pass bound for 48 cells; the R107 handoff records the measured
    differences for 48/96/192 cells and tightens this bound to 3x the 192-cell value.
    """
    from bass.transport.coupled_einstein_boltzmann import CoupledSolverConfig, solve_coupled_einstein_boltzmann
    from bass.transport.hybrid_los_transfer import history_from_coupled_result

    res = solve_coupled_einstein_boltzmann("VII_h", CoupledSolverConfig(n_cells=48, ell_max=6, epsilon=2e-4,
                                                                        record_history=True))
    hist = history_from_coupled_result(res)
    op = GeneralLieStokesOperator(int(res.ell_max))
    assert hist.emission.shape == (49, op.dim) and abs(hist.N[-1]) < 1e-12
    opo, vec = _los_low_ell(hist, n_gl=24, L_out=3)
    for ch, ell in (("T", 2), ("E", 2)):
        nat = np.array([res.final_state[op.idx[ch][(ell, m)]] for m in range(-ell, ell + 1)])
        if np.max(np.abs(nat)) > 0.0:
            los = np.array([vec[opo.idx[ch][(ell, m)]] for m in range(-ell, ell + 1)])
            assert np.max(np.abs(los - nat)) <= 2e-2 * np.max(np.abs(nat)), ch


def test_windowed_history_reproduces_the_native_state_at_an_intermediate_time():
    """Independent line-of-sight photon moments at a matched solver time (SQ-PHOTON-FLUX route)."""
    sigma = SIGMA
    op, hist, _ = _native_run(10, sigma, np.array([0.05, 0.0, 0.0]), np.diag([0.0, 0.3, 0.3]))
    # recompute the native state at node k by replaying the run (emission = G S keeps S recoverable only through the run)
    k = 100
    N = hist.N
    geom = LieGeometry(sigma, np.array([0.05, 0.0, 0.0]), np.diag([0.0, 0.3, 0.3]))
    S = np.zeros(op.dim, dtype=complex)
    for j in range(k):
        dN = N[j + 1] - N[j]
        S = op.advance_cell(S, dN, geom, hist.delta_tau[j], source_increment=op.shear_source_vector(sigma, amplitude=dN),
                            substeps=4, bolometric_redshift=True)
    win = history_window(hist, k)
    assert abs(win.N[-1]) == 0.0 and win.provenance["window"]["node"] == k
    opo, vec = _los_low_ell(win)
    for ch, ell, tol in (("T", 1, 1e-4), ("T", 2, 1e-4), ("E", 2, 1e-3)):
        assert _max_rel(op, S, opo, vec, ch, ell) < tol, (ch, ell)
    with pytest.raises(ValueError):
        history_window(hist, 0)
