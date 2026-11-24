"""Hybrid line-of-sight transfer for homogeneous Bianchi skies (native low-ell source x exact characteristics).

Purpose
-------
The native all-m Stokes hierarchy (``GeneralLieStokesOperator`` driven by
``solve_coupled_einstein_boltzmann``) is qualified only at low multipoles (L <= 8 in
the R105/R106 runs).  The observed sky of a homogeneous Bianchi model needs all
multipoles: free streaming through the anisotropic background maps the low-ell
Thomson source of every past epoch onto a direction-dependent, possibly focused,
pattern.  Because the background is spatially homogeneous, the transport equation
of the native state

    dX/dN = M_Lie(N) X - 4 sigma_ij n^i n^j (1/4 + X) + kappa (1 + n.beta) [S_f(X) - (1/4 + X)]

(n = outward sky direction, X = quarter-intensity Stokes increment, T channel
(I/Ibar - 1)/4, Q/U in the screen basis (e_theta, e_phi) of n, N = ln a, rates per
e-fold) has exact characteristics: the backward null geodesics of the homogeneous
normal tetrad.  Its formal solution is therefore

    1 + 4 T_obs(n) = sum_k w_k (1 + 4 J_T(N_k, n_k)) exp(-4 Delta_k) + exp(-tau_0) (1 + 4 X_T(N_0, n_0)) exp(-4 Delta_0)
    (Q + iU)_obs(n) = sum_k w_k exp(-4 Delta_k - 2 i chi_k) J_P(N_k, n_k) + boundary term

with n_k the sky direction of the ray at node N_k, Delta_k = ln(E_k / E_obs) + N_k the
anisotropic part of the photon energy shift, chi_k the angle between the
parallel-transported Sachs vector s1 and e_theta(n_k), J the Thomson source function
per unit directional optical depth and w_k the exact exponential weights of a source
that is linear in optical depth between nodes.  Only the low-ell source J (ell <= 3)
is needed from the native hierarchy; the high-ell pattern comes from the
characteristics.  This is the Seljak-Zaldarriaga line-of-sight idea applied to a
homogeneous anisotropic background.

Conventions are those of ``general_lie_stokes``: signature (-+++), normal Fermi
tetrad, H-normalised geometry (sigma/H, a/H, n/H) packed as LieGeometry.pack_14,
photon momentum p = -n, Q/U defined by -(Q +- iU) = sum (E +- iB) _{+-2}Y_lm on the
outward sphere.  ``los_alm_healpix`` converts to HEALPix arrays; the convention map
is fixed by tests.

Scope and failure semantics
---------------------------
* First-order source (the native state) and exact geodesic redshift factor.
* The emission is truncated at ``source_ell_max``; the discarded norm is measured on
  every node and the run fails closed above ``max_source_truncation``.
* Geometry is interpolated linearly in N between recorded nodes.  The geodesic
  integration is RK4 with a bounded step; ``max_step`` controls convergence.
* No family attribution, likelihood or null is made here.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Mapping, Sequence

import numpy as np

from bass.background.convention_bridge import build_structure_tensor_with_sign
from bass.background.tilted_bianchi_state import build_4d_bianchi_connection
from bass.transport.general_bianchi_transfer import (
    _spherical_screen_basis,
    map_from_scalar_alm,
    qu_from_spin2_alm,
)
from bass.transport.general_lie_stokes import GeneralLieStokesOperator, LieGeometry, vector_to_alm_dict

__all__ = [
    "SCHEMA",
    "LosSourceHistory",
    "LosSky",
    "pack_geometry14",
    "thomson_emission",
    "history_from_native_states",
    "history_from_coupled_result",
    "history_window",
    "trace_rays",
    "los_sky",
    "healpix_directions",
    "los_alm_healpix",
    "native_alm_to_healpix",
]

SCHEMA = "htt.bass.hybrid_los/1"
_CHANNELS = ("T", "E", "B", "V")


def pack_geometry14(sigma_N: np.ndarray, a_N: np.ndarray, n_N: np.ndarray) -> np.ndarray:
    """Pack H-normalised (sigma, a, n) in the LieGeometry.pack_14 order without validation."""
    s = np.asarray(sigma_N, dtype=np.float64)
    a = np.asarray(a_N, dtype=np.float64)
    n = np.asarray(n_N, dtype=np.float64)
    if s.shape != (3, 3) or a.shape != (3,) or n.shape != (3, 3):
        raise ValueError("sigma_N and n_N must be 3x3 and a_N a 3-vector")
    return np.array([s[0, 0], s[1, 1], s[0, 1], s[0, 2], s[1, 2], a[0], a[1], a[2],
                     n[0, 0], n[1, 1], n[2, 2], n[0, 1], n[0, 2], n[1, 2]], dtype=np.float64)


@dataclass(frozen=True)
class LosSourceHistory:
    """Native source history on nodes N_0 < ... < N_K = 0 (observer).

    ``delta_tau[k]`` is the isotropic (conserved-anchor) Thomson depth of [N_k, N_{k+1}];
    ``emission[k]`` the native-layout harmonic Thomson gain per unit isotropic depth at
    N_k (``thomson_emission``); ``beta[k]`` the electron velocity at N_k (loss factor
    1 + n.beta).  ``geometry_N``/``geometry14`` tabulate the background for the rays
    and must cover [N_0, 0].
    """

    N: np.ndarray
    delta_tau: np.ndarray
    emission: np.ndarray
    initial_state: np.ndarray
    geometry_N: np.ndarray
    geometry14: np.ndarray
    ell_max_native: int
    beta: np.ndarray | None = None
    provenance: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        N = np.asarray(self.N, dtype=np.float64)
        K = N.size - 1
        if N.ndim != 1 or K < 1 or not np.all(np.isfinite(N)) or not np.all(np.diff(N) > 0.0):
            raise ValueError("N must be a finite strictly increasing array with at least two nodes")
        if abs(float(N[-1])) > 1e-9:
            raise ValueError("the last node must be the observer at N = 0")
        dt = np.asarray(self.delta_tau, dtype=np.float64)
        if dt.shape != (K,) or not np.all(np.isfinite(dt)) or np.any(dt < 0.0):
            raise ValueError("delta_tau must be finite, nonnegative and have one entry per interval")
        op_dim = _layout(int(self.ell_max_native))[1]
        em = np.asarray(self.emission)
        if em.shape != (K + 1, op_dim) or not np.all(np.isfinite(em)):
            raise ValueError(f"emission must have shape {(K + 1, op_dim)} and be finite")
        x0 = np.asarray(self.initial_state)
        if x0.shape != (op_dim,) or not np.all(np.isfinite(x0)):
            raise ValueError("initial_state must match the native layout and be finite")
        gN = np.asarray(self.geometry_N, dtype=np.float64)
        g14 = np.asarray(self.geometry14, dtype=np.float64)
        if gN.ndim != 1 or gN.size < 2 or not np.all(np.diff(gN) > 0.0) or g14.shape != (gN.size, 14):
            raise ValueError("geometry_N must be increasing and geometry14 must have shape (len(geometry_N), 14)")
        if not np.all(np.isfinite(g14)):
            raise ValueError("geometry14 must be finite")
        if gN[0] > N[0] + 1e-9 or gN[-1] < -1e-9:
            raise ValueError("geometry must cover [N_0, 0]")
        if self.beta is not None:
            b = np.asarray(self.beta, dtype=np.float64)
            if b.shape != (K + 1, 3) or not np.all(np.isfinite(b)) or np.any(np.sum(b * b, axis=1) >= 1.0):
                raise ValueError("beta must be finite, subluminal and have shape (K + 1, 3)")


@dataclass(frozen=True)
class LosSky:
    """Observed quarter-intensity Stokes increments on ``directions`` (outward sky unit vectors)."""

    directions: np.ndarray
    T: np.ndarray
    Q: np.ndarray
    U: np.ndarray
    V: np.ndarray
    diagnostics: Mapping[str, object]


_LAYOUT_CACHE: dict[int, tuple[dict, int]] = {}


def _layout(L: int) -> tuple[dict, int]:
    if L not in _LAYOUT_CACHE:
        op = GeneralLieStokesOperator(L)
        _LAYOUT_CACHE[L] = (op.idx, op.dim)
    return _LAYOUT_CACHE[L]


def thomson_emission(op: GeneralLieStokesOperator, state: np.ndarray, beta: Sequence[float] | None = None) -> np.ndarray:
    """Native Thomson gain per unit isotropic depth: G X (rest electrons) or the moving-stage gain.

    For moving electrons the returned vector is ``left @ right_h @ X + emission`` of
    ``MovingCollisionStage``; the background scatter-in that the stage nets against its
    own loss is restored in ``los_sky`` through the 1/4 offset of the source function.
    """
    x = np.asarray(state, dtype=np.complex128)
    if x.shape != (op.dim,):
        raise ValueError("state does not match the operator layout")
    b = np.zeros(3) if beta is None else np.asarray(beta, dtype=np.float64)
    if not np.any(b):
        return x + op._build_sparse_thomson() @ x
    from bass.transport.moving_collision_stage import MovingCollisionStage

    stage = MovingCollisionStage(op, b)
    return stage.left @ (stage.right_h @ x) + stage.emission


def history_from_native_states(
    op: GeneralLieStokesOperator,
    N: Sequence[float],
    states: np.ndarray,
    delta_tau: Sequence[float],
    geometry_N: Sequence[float],
    geometry14: np.ndarray,
    *,
    beta: np.ndarray | None = None,
    provenance: Mapping[str, object] | None = None,
) -> LosSourceHistory:
    """Build a history from native states recorded at every node (states[0] is the initial state)."""
    S = np.asarray(states, dtype=np.complex128)
    Nn = np.asarray(N, dtype=np.float64)
    if S.shape != (Nn.size, op.dim):
        raise ValueError("states must have one native vector per node")
    b = None if beta is None else np.asarray(beta, dtype=np.float64)
    em = np.stack([thomson_emission(op, S[k], None if b is None else b[k]) for k in range(Nn.size)])
    return LosSourceHistory(N=Nn, delta_tau=np.asarray(delta_tau, dtype=np.float64), emission=em,
                            initial_state=S[0], geometry_N=np.asarray(geometry_N, dtype=np.float64),
                            geometry14=np.asarray(geometry14, dtype=np.float64), ell_max_native=op.L,
                            beta=b, provenance=dict(provenance or {}))


def history_from_coupled_result(result, *, op: GeneralLieStokesOperator | None = None) -> LosSourceHistory:
    """Build the history from ``solve_coupled_einstein_boltzmann(..., record_history=True)``.

    Requires the LoS keys written by the coupled solver (``stokes_initial``,
    ``stokes_state``, ``baryon_velocity``, ``N_start``, ``geometry_N``, ``geometry14``) in
    the last (converged) Picard record.  Fails closed when they are absent.
    """
    hist = getattr(result, "history", None)
    if not hist or "iterations" not in hist:
        raise ValueError("coupled result has no recorded history; run with record_history=True")
    rec = hist["iterations"][-1]
    needed = ("stokes_initial", "stokes_state", "baryon_velocity", "N_start", "geometry_N", "geometry14", "N_end", "delta_tau")
    missing = [k for k in needed if k not in rec]
    if missing:
        raise ValueError(f"coupled history lacks line-of-sight keys {missing}")
    op = GeneralLieStokesOperator(int(result.ell_max)) if op is None else op
    N = np.concatenate([[float(rec["N_start"])], np.asarray(rec["N_end"], dtype=np.float64)])
    states = np.concatenate([np.asarray(rec["stokes_initial"])[None, :], np.asarray(rec["stokes_state"])], axis=0)
    beta = np.asarray(rec["baryon_velocity"], dtype=np.float64)
    prov = {"source": "solve_coupled_einstein_boltzmann", "family": getattr(result, "family", None),
            "ell_max_native": int(result.ell_max), "n_cells": int(result.n_cells),
            "picard_iterations_used": int(getattr(result, "picard_iterations_used", 0))}
    return history_from_native_states(op, N, states, rec["delta_tau"], rec["geometry_N"], rec["geometry14"],
                                      beta=beta, provenance=prov)


def history_window(history: LosSourceHistory, node: int) -> LosSourceHistory:
    """History seen by a normal observer at node ``node`` (all quantities shifted so that node is N = 0).

    Rates are per e-fold and the geometry is H-normalised, so a shift of N changes only
    the reference of the photon energy: Delta = ln(E/E_obs) + (N - N_obs).  Used to
    obtain independent line-of-sight photon moments at matched solver times.
    """
    N = np.asarray(history.N, dtype=np.float64)
    if not (1 <= int(node) < N.size):
        raise ValueError("node must select an interior or final node with at least one earlier node")
    k = int(node)
    n_obs = float(N[k])
    gN = np.asarray(history.geometry_N, dtype=np.float64)
    g14 = np.asarray(history.geometry14, dtype=np.float64)
    keep = gN < n_obs
    g_end = _geometry_at(gN, g14, n_obs)
    new_gN = np.concatenate([gN[keep], [n_obs]]) - n_obs
    new_g14 = np.vstack([g14[keep], g_end[None, :]])
    beta = None if history.beta is None else np.asarray(history.beta)[:k + 1]
    prov = dict(history.provenance)
    prov["window"] = {"node": k, "N_obs_original": n_obs}
    return LosSourceHistory(N=N[:k + 1] - n_obs, delta_tau=np.asarray(history.delta_tau)[:k],
                            emission=np.asarray(history.emission)[:k + 1], initial_state=history.initial_state,
                            geometry_N=new_gN, geometry14=new_g14, ell_max_native=history.ell_max_native,
                            beta=beta, provenance=prov)


# ---------------------------------------------------------------- characteristics
def _geometry_at(geometry_N: np.ndarray, geometry14: np.ndarray, N_val: float) -> np.ndarray:
    return np.array([np.interp(N_val, geometry_N, geometry14[:, j]) for j in range(14)])


def _connection_terms(g14: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    sig, a, n = LieGeometry.unpack_14(g14)
    G = build_4d_bianchi_connection(1.0, sig, build_structure_tensor_with_sign(a, n, a_sign=1))
    c0 = G[:, 0, 0]
    c1 = G[:, 0, 1:] + G[:, 1:, 0]
    d1 = G[:, 1:, 0]
    C2 = np.ascontiguousarray(np.transpose(G[:, 1:, 1:], (1, 0, 2)).reshape(3, 12))  # [b, d*3 + a]
    return c0, c1, d1, C2


def _ray_rhs(p: np.ndarray, s1: np.ndarray, terms) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """dlnE/dN, dp/dN and ds1/dN of k^a nabla_a k^d = 0 with H-normalised rates (H = 1)."""
    c0, c1, d1, C2 = terms
    r = p.shape[0]
    Tp = (p @ C2).reshape(r, 4, 3)
    guu = c0[None, :] + p @ c1.T + np.einsum("rda,ra->rd", Tp, p)
    Ts = (s1 @ C2).reshape(r, 4, 3)
    gzu = s1 @ d1.T + np.einsum("rda,ra->rd", Ts, p)
    dlnE = -guu[:, 0]
    dp = -(guu[:, 1:] - p * guu[:, :1])
    ds1 = -(gzu[:, 1:] - p * gzu[:, :1])
    return dlnE, dp, ds1


def _renormalise(p: np.ndarray, s1: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    p = p / np.linalg.norm(p, axis=1, keepdims=True)
    s1 = s1 - np.sum(s1 * p, axis=1, keepdims=True) * p
    s1 = s1 / np.linalg.norm(s1, axis=1, keepdims=True)
    return p, s1


def _rk4_segment(state, N_from: float, N_to: float, geometry_N, geometry14, max_step: float):
    """Advance (lnE, p, s1) from N_from to N_to (any sign) with uniform RK4 sub-steps."""
    lnE, p, s1 = state
    span = N_to - N_from
    n_sub = max(1, int(math.ceil(abs(span) / max_step)))
    h = span / n_sub
    N_cur = N_from
    for _ in range(n_sub):
        t1 = _connection_terms(_geometry_at(geometry_N, geometry14, N_cur))
        tm = _connection_terms(_geometry_at(geometry_N, geometry14, N_cur + 0.5 * h))
        t2 = _connection_terms(_geometry_at(geometry_N, geometry14, N_cur + h))
        k1 = _ray_rhs(p, s1, t1)
        k2 = _ray_rhs(p + 0.5 * h * k1[1], s1 + 0.5 * h * k1[2], tm)
        k3 = _ray_rhs(p + 0.5 * h * k2[1], s1 + 0.5 * h * k2[2], tm)
        k4 = _ray_rhs(p + h * k3[1], s1 + h * k3[2], t2)
        lnE = lnE + (h / 6.0) * (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0])
        p = p + (h / 6.0) * (k1[1] + 2 * k2[1] + 2 * k3[1] + k4[1])
        s1 = s1 + (h / 6.0) * (k1[2] + 2 * k2[2] + 2 * k3[2] + k4[2])
        p, s1 = _renormalise(p, s1)
        N_cur += h
    return lnE, p, s1


def trace_rays(directions: np.ndarray, N_nodes: Sequence[float], geometry_N: Sequence[float], geometry14: np.ndarray,
               *, max_step: float = 0.02):
    """Yield (k, n_k, Delta_k, chi_k) backward from the observer node to node 0.

    ``directions`` are outward observer sky vectors; n_k = -p is the sky direction of the
    ray at N_k; Delta_k = ln(E_k/E_obs) + N_k; chi_k rotates e_theta(n_k) into s1.
    """
    n_obs = np.asarray(directions, dtype=np.float64)
    n_obs = n_obs / np.linalg.norm(n_obs, axis=1, keepdims=True)
    gN = np.asarray(geometry_N, dtype=np.float64)
    g14 = np.asarray(geometry14, dtype=np.float64)
    Nn = np.asarray(N_nodes, dtype=np.float64)
    e_th, _ = _spherical_screen_basis(n_obs)
    state = (np.zeros(n_obs.shape[0]), -n_obs.copy(), e_th.copy())
    K = Nn.size - 1
    for k in range(K, -1, -1):
        if k < K:
            state = _rk4_segment(state, float(Nn[k + 1]), float(Nn[k]), gN, g14, max_step)
        lnE, p, s1 = state
        n_k = -p
        et, ep = _spherical_screen_basis(n_k)
        chi = np.arctan2(np.sum(s1 * ep, axis=1), np.sum(s1 * et, axis=1))
        yield k, n_k, lnE + float(Nn[k]), chi


# ---------------------------------------------------------------- formal solution
def _evaluate_native(vec: np.ndarray, idx: Mapping, directions: np.ndarray, ell_max: int, need_v: bool):
    alms = vector_to_alm_dict(vec, idx)
    th = np.arccos(np.clip(directions[:, 2], -1.0, 1.0))
    ph = np.arctan2(directions[:, 1], directions[:, 0])
    T = map_from_scalar_alm({k: v for k, v in alms["T"].items() if k[0] <= ell_max}, th, ph, ell_max=ell_max)
    E = {k: v for k, v in alms["E"].items() if k[0] <= ell_max}
    B = {k: v for k, v in alms["B"].items() if k[0] <= ell_max}
    if ell_max >= 2 and (E or B):
        Q, U = qu_from_spin2_alm(E, B, th, ph, ell_max=ell_max)
    else:
        Q = U = np.zeros(directions.shape[0])
    V = (map_from_scalar_alm({k: v for k, v in alms["V"].items() if k[0] <= ell_max}, th, ph, ell_max=ell_max)
         if need_v else np.zeros(directions.shape[0]))
    return T, Q + 1j * U, V


def _ell_norms(vec: np.ndarray, idx: Mapping) -> dict[int, float]:
    out: dict[int, float] = {}
    for ch in _CHANNELS:
        for (ell, _m), pos in idx[ch].items():
            out[ell] = out.get(ell, 0.0) + float(abs(vec[pos]) ** 2)
    return out


def _linear_depth_weights(dtau: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Weights (a, b) with int_0^dtau e^-x F dx = a F(0) + b F(dtau) for F linear in x."""
    one_minus = -np.expm1(-dtau)
    small = dtau < 1e-3
    safe = np.where(small, 1.0, dtau)
    ramp = np.where(small,
                    dtau / 2.0 - dtau ** 2 / 3.0 + dtau ** 3 / 8.0 - dtau ** 4 / 30.0,
                    (one_minus - dtau * np.exp(-dtau)) / safe)
    return one_minus - ramp, ramp


def los_sky(history: LosSourceHistory, directions: np.ndarray, *, source_ell_max: int | None = None,
            max_step: float = 0.02, max_source_truncation: float = 1e-8) -> LosSky:
    """Formal solution of the native transport along exact homogeneous characteristics."""
    t0 = time.perf_counter()
    idx, dim = _layout(history.ell_max_native)
    N = np.asarray(history.N, dtype=np.float64)
    K = N.size - 1
    em = np.asarray(history.emission, dtype=np.complex128)
    beta = None if history.beta is None else np.asarray(history.beta, dtype=np.float64)
    norms = [_ell_norms(em[k], idx) for k in range(K + 1)]
    total = max(max(sum(v.values()) for v in norms), 1e-300)
    if source_ell_max is None:
        source_ell_max = max([ell for v in norms for ell, val in v.items() if val > 1e-28 * total] + [0])
    source_ell_max = int(min(max(source_ell_max, 0), history.ell_max_native))
    trunc = max(math.sqrt(sum(val for ell, val in v.items() if ell > source_ell_max) / total) for v in norms)
    if trunc > max_source_truncation:
        raise ValueError(f"emission beyond ell={source_ell_max} has relative norm {trunc:.3e} > {max_source_truncation:.1e}")
    v_slots = list(idx["V"].values())
    need_v = bool(v_slots) and (float(np.abs(em[:, v_slots]).max()) > 0.0
                                or float(np.abs(np.asarray(history.initial_state)[v_slots]).max()) > 0.0)

    n_dir = np.asarray(directions, dtype=np.float64).shape[0]
    accT = np.zeros(n_dir)
    accP = np.zeros(n_dir, dtype=np.complex128)
    accV = np.zeros(n_dir)
    tau_acc = np.zeros(n_dir)
    prev = None
    min_tau_pre = None
    for k, n_k, delta_k, chi_k in trace_rays(directions, N, history.geometry_N, history.geometry14, max_step=max_step):
        mu_k = np.ones(n_dir) if beta is None else 1.0 + n_k @ beta[k]
        T_k, P_k, V_k = _evaluate_native(em[k], idx, n_k, source_ell_max, need_v)
        red = np.exp(-4.0 * delta_k)
        rot = np.exp(-2j * chi_k)
        F_T = (1.0 + 4.0 * T_k / mu_k) * red
        F_P = (P_k / mu_k) * red * rot
        F_V = (V_k / mu_k) * red
        if prev is not None:
            pT, pP, pV, pmu = prev
            dtau = history.delta_tau[k] * 0.5 * (mu_k + pmu)
            a_w, b_w = _linear_depth_weights(dtau)
            att = np.exp(-tau_acc)
            accT += att * (a_w * pT + b_w * F_T)
            accP += att * (a_w * pP + b_w * F_P)
            accV += att * (a_w * pV + b_w * F_V)
            tau_acc = tau_acc + dtau
        prev = (F_T, F_P, F_V, mu_k)
        if k == 0:
            x0T, x0P, x0V = _evaluate_native(np.asarray(history.initial_state), idx, n_k, history.ell_max_native, need_v)
            att = np.exp(-tau_acc)
            accT += att * (1.0 + 4.0 * x0T) * red
            accP += att * x0P * red * rot
            accV += att * x0V * red
            min_tau_pre = float(tau_acc.min())
    diag = {"schema": SCHEMA, "n_nodes": int(K + 1), "n_directions": int(n_dir), "source_ell_max": source_ell_max,
            "max_source_truncation": float(trunc), "min_total_depth": min_tau_pre,
            "initial_state_weight_max": float(math.exp(-min_tau_pre)) if min_tau_pre is not None else None,
            "max_step": float(max_step), "seconds": time.perf_counter() - t0,
            "provenance": dict(history.provenance)}
    return LosSky(directions=np.asarray(directions, dtype=np.float64), T=0.25 * (accT - 1.0),
                  Q=accP.real, U=accP.imag, V=accV, diagnostics=diag)


# ---------------------------------------------------------------- harmonic output
def healpix_directions(nside: int) -> np.ndarray:
    """RING-ordered HEALPix pixel centres as outward unit vectors."""
    import healpy as hp

    return np.stack(hp.pix2vec(int(nside), np.arange(12 * int(nside) ** 2)), axis=1)


def los_alm_healpix(sky: LosSky, nside: int, lmax: int, *, iterations: int = 3) -> dict[str, np.ndarray]:
    """HEALPix (T, E, B, V) alm of a sky computed on ``healpix_directions(nside)``.

    Native Q/U on e_theta/e_phi with -(Q +- iU) = sum (E +- iB) _{+-2}Y are passed to
    healpy unchanged; ``test_native_polarization_convention_matches_healpix`` fixes that
    this reproduces the native (E, B) coefficients.
    """
    import healpy as hp

    if sky.T.size != 12 * int(nside) ** 2:
        raise ValueError("sky was not computed on healpix_directions(nside)")
    t, e, b = hp.map2alm([sky.T, sky.Q, sky.U], lmax=int(lmax), iter=int(iterations), pol=True)
    v = hp.map2alm(sky.V, lmax=int(lmax), iter=int(iterations))
    return {"T": t, "E": e, "B": b, "V": v, "lmax": int(lmax)}


def native_alm_to_healpix(alm: Mapping[tuple[int, int], complex], lmax: int) -> np.ndarray:
    """Native (ell, m) dictionary to a healpy m >= 0 array."""
    import healpy as hp

    out = np.zeros(hp.Alm.getsize(int(lmax)), dtype=np.complex128)
    for (ell, m), v in alm.items():
        if ell <= lmax and m >= 0:
            out[hp.Alm.getidx(int(lmax), ell, m)] = v
    return out
