"""R97 Unit C (G07_BIANCHI / P5): Non-axisymmetric coupled-m spin-2 Bianchi transport via R49 Gamma4 connection.

Bridges:
  - R49 12-family 4D synchronous-tetrad connection Gamma4 & tilted Einstein-Euler
    trajectories (H, sigma_ab, a_i, n_ij, v_photon, v_cdm)
  - R95 source-qualified HyRec-2 + Planck 2018 tanh reionization conformal timeline
    and BASS exact basis-free rank-9 Thomson eigenvalues (-1, -0.3 on T2/E2; -1 on B)
  - R96 exact spin-s cos(theta) streaming recurrence and sparse LU integration across
    m in {-2, -1, 0, 1, 2} up to L=60 (plus full all-|m|<=L verification at L=8, 12)

Physics formulation:
  Projects R49's exact 4D connection geodesic drift dn/dN (via pole-free spin-1 eth
  covariant operators) and Sachs screen twist dpsi/dN onto spin-0 (T) and spin-+/-2
  (P_+- = -(Q +- i U), converting to E and B) spherical harmonics, generating explicit
  m <-> m' azimuthal mode scattering and non-zero curved/helical E <-> B mixing in
  general non-axisymmetric Bianchi geometries (I, V, VI_{-1/9}, VII_0, VII_h, IX).

Strictly preserves:
  - Uniform (a_v, n_m) scaling preserving Class-B group parameter h = a^2/(n_2 n_3)
  - Physical claim boundary: source-conditional HyRec-2+tanh optics coupled with
    constructed/R49-rescaled geometric amplitudes; full_all_m_boltzmann_closure = False
    and SQ-NATIVE / B02-B05 remain non-promoted.
"""
from __future__ import annotations

import json
import math
import time
from pathlib import Path
import sys

import numpy as np
from scipy.sparse import csc_matrix, eye, lil_matrix
from scipy.sparse.linalg import splu
from scipy.spatial.transform import Rotation

ROOT = Path(__file__).resolve().parents[2]
for p in (str(ROOT), str(ROOT / "htt"), str(ROOT / "htt/src")):
    if p not in sys.path:
        sys.path.insert(0, p)

from bass.background.general_tilted_evolution import (
    TiltedEvolutionConfig,
    _build_default_admissible_state_for_family,
    evolve_general_tilted_bianchi,
)
from bass.background.geometry import pstf_rank2
from bass.transport.general_bianchi_transfer import (
    _spherical_screen_basis,
    gl_sphere_grid,
    spin_weighted_spherical_harmonic_grid,
)
from scripts.r95.bianchi_bg_audit import _build_vi_minus_1_9_state
from scripts.r95.bianchi_polarized_hierarchy import (
    _geodesic_aberration_and_twist_on_grid,
    _prepare_physical_visibility_timeline,
)
from scripts.r96.spin2_mblock_extension import c_spin, stf_source_harmonics

OUT_JSON = ROOT / "docs/research_program/observational_publication_20261015/R97_SCIENCE_EXECUTION_20261122/BIANCHI_COUPLED_M_TRANSPORT.json"
SIGNATURE = "(-,+,+,+)"


def _mode_index_table(L: int, m_values: tuple[int, ...]) -> tuple[dict, int]:
    """Unified state ordering across active m_values: block per (channel, m, ell).

    Stores offsets for T (ell=0..L), E (ell=2..L), B (ell=2..L) restricted to |m|<=ell.
    """
    idx_map = {"T": {}, "E": {}, "B": {}}
    cur = 0
    for m in m_values:
        for ell in range(abs(m), L + 1):
            idx_map["T"][(ell, m)] = cur
            cur += 1
    for m in m_values:
        for ell in range(max(2, abs(m)), L + 1):
            idx_map["E"][(ell, m)] = cur
            cur += 1
    for m in m_values:
        for ell in range(max(2, abs(m)), L + 1):
            idx_map["B"][(ell, m)] = cur
            cur += 1
    return idx_map, cur


def _build_spin_basis_theta(L: int, m_values: tuple[int, ...], th_1d: np.ndarray) -> dict[tuple[int, int, int], np.ndarray]:
    """Compute _sY_{ell, m}(theta, phi=0) vectors for s in {-3..+3} via exact 3-term recurrence (pole/overflow-free to L>=60)."""
    basis = {}
    ph0 = np.zeros_like(th_1d)
    costh = np.cos(th_1d)
    for s in (-3, -2, -1, 0, 1, 2, 3):
        for m in m_values:
            lmin = max(abs(s), abs(m))
            if lmin > L:
                continue
            y_prev = np.zeros_like(th_1d, dtype=np.complex128)
            # Seed strictly at minimal degree lmin (max 16 here, zero factorial overflow)
            y_curr = spin_weighted_spherical_harmonic_grid(s, lmin, m, th_1d, ph0)
            basis[(s, lmin, m)] = y_curr
            for ell in range(lmin, L):
                cp = c_spin(ell + 1, s, m)
                cm = c_spin(ell, s, m) if ell > lmin else 0.0
                diag_term = -(s * m) / (ell * (ell + 1.0)) if ell > 0 else 0.0
                y_next = ((costh - diag_term) * y_curr - cm * y_prev) / cp
                basis[(s, ell + 1, m)] = y_next
                y_prev, y_curr = y_curr, y_next
    return basis


def _build_diag_stream_and_thomson(L: int, m_values: tuple[int, ...], idx_map: dict, dim: int, k: float) -> tuple[csc_matrix, csc_matrix]:
    """Exact diagonal-in-m spin-s cos(theta) streaming A and BASS rank-9 Thomson K."""
    A = lil_matrix((dim, dim), dtype=np.complex128)
    K = lil_matrix((dim, dim), dtype=np.complex128)
    for m in m_values:
        # Scalar T streaming & Thomson
        for ell in range(abs(m), L):
            i0 = idx_map["T"].get((ell, m))
            i1 = idx_map["T"].get((ell + 1, m))
            if i0 is not None and i1 is not None:
                c = c_spin(ell + 1, 0, m)
                A[i0, i1] = -1j * k * c
                A[i1, i0] = -1j * k * c
        # Spin-2 E/B streaming + m-helicity coupling
        for ell in range(max(2, abs(m)), L):
            e0 = idx_map["E"].get((ell, m))
            e1 = idx_map["E"].get((ell + 1, m))
            b0 = idx_map["B"].get((ell, m))
            b1 = idx_map["B"].get((ell + 1, m))
            if e0 is not None and e1 is not None:
                c2 = c_spin(ell + 1, 2, m)
                A[e0, e1] = -1j * k * c2
                A[e1, e0] = -1j * k * c2
                A[b0, b1] = -1j * k * c2
                A[b1, b0] = -1j * k * c2
        for ell in range(max(2, abs(m)), L + 1):
            ei = idx_map["E"][(ell, m)]
            bi = idx_map["B"][(ell, m)]
            d = -2.0 * m / (ell * (ell + 1.0))
            A[ei, bi] = k * d
            A[bi, ei] = -k * d
        # Thomson collision
        for ell in range(max(1, abs(m)), L + 1):
            ti = idx_map["T"].get((ell, m))
            if ti is not None:
                K[ti, ti] = -1.0
        for ell in range(max(2, abs(m)), L + 1):
            ei = idx_map["E"][(ell, m)]
            bi = idx_map["B"][(ell, m)]
            K[ei, ei] = -1.0
            K[bi, bi] = -1.0
        if abs(m) <= 2 and L >= 2:
            t2 = idx_map["T"][(2, m)]
            e2 = idx_map["E"][(2, m)]
            K[t2, t2] = -0.9
            K[t2, e2] = -math.sqrt(6.0) / 10.0
            K[e2, t2] = -3.0 / (5.0 * math.sqrt(6.0))
            K[e2, e2] = -0.4
    return A.tocsc(), K.tocsc()


def _project_gamma4_to_coupled_m_operators(
    L: int,
    m_values: tuple[int, ...],
    idx_map: dict,
    dim: int,
    sig_N: np.ndarray,
    a_N: np.ndarray,
    n_N: np.ndarray,
    *,
    basis_theta: dict | None = None,
    n_gl_theta: int | None = None,
) -> dict:
    """Project R49 Gamma4(H=1, sig_N, a_N, n_N) geodesic advection & screen twist into coupled-m sparse operators.

    Exploits 1D FFT in phi + exact Gauss-Legendre theta inner products via pole-free spin-1
    eth ladder actions:
      D_v (_sY_{lm}) = +0.5 * (v_- * eth(_sY_{lm}) + v_+ * ethbar(_sY_{lm}))
    where eth(_sY_{lm}) = -sqrt((l-s)(l+s+1)) _{s+1}Y_{lm},
          ethbar(_sY_{lm}) = +sqrt((l+s)(l-s+1)) _{s-1}Y_{lm}.
    Retains the exact Liouville geodesic advection operator M_geo_exact (including S^2
    expansion/focusing divergence 0.5 * (D + D^dagger) plus exact skew-Hermitian screen twist)
    alongside its skew-Hermitian unitary component M_geo_unitary for norm diagnostics.
    """
    n_th = max(L + 8, 16) if n_gl_theta is None else int(n_gl_theta)
    TH, PH, n_hat_grid, weights = gl_sphere_grid(n_th)
    th_1d = TH[:, 0]
    n_ph = PH.shape[1]
    # Gauss-Legendre theta weights sum to 2.0 (integral over sin(theta)dtheta);
    # combined with 2*pi * [ (1/n_ph) sum_phi e^{-i dm phi} f(th, ph) ], inner product matches
    # int dOmega = int_{-1}^1 d(cos th) int_0^{2pi} dphi identically!
    w_th = weights.sum(axis=1)  # shape (n_th,)! Wait: sum(weights, axis=1) = (2*pi/n_ph)*n_ph*wx = 2*pi * wx!
    # Check: sum(W) = 4*pi => sum_phi weights = 2*pi * wx! If f_phi_hat = fft(f)/n_ph (average over phi),
    # then sum_theta (2*pi * wx) * f_phi_hat == sum_theta wx * sum_phi dphi * f == int dOmega f! EXACT!
    dn_dN, dpsi_dN, _, _ = _geodesic_aberration_and_twist_on_grid(
        n_hat_grid, 1.0, sig_N, a_N, n_N, 1.0
    )
    e_th, e_ph = _spherical_screen_basis(n_hat_grid)
    v_th = np.sum(dn_dN * e_th, axis=-1)
    v_ph = np.sum(dn_dN * e_ph, axis=-1)
    v_plus = v_th + 1j * v_ph
    v_minus = v_th - 1j * v_ph

    # Azimuthal Fourier modes: hat_f[dm_bin] = (1/n_ph) * sum_j f(th, phi_j) * e^{-i * dm * phi_j}
    fft_vp = np.fft.fft(v_plus, axis=1) / float(n_ph)
    fft_vm = np.fft.fft(v_minus, axis=1) / float(n_ph)
    fft_psi = np.fft.fft(dpsi_dN.astype(np.complex128), axis=1) / float(n_ph)

    if basis_theta is None:
        basis_theta = _build_spin_basis_theta(L, m_values, th_1d)

    def _compute_spin_adv_and_psi(s: int, ell_min: int) -> tuple[np.ndarray, np.ndarray]:
        """Compute dense per-m-set advection D^{(s)} and twist W^{(s)} indexed cleanly."""
        keys = [(ell, m) for m in m_values for ell in range(max(ell_min, abs(m)), L + 1)]
        n_s = len(keys)
        D_s = np.zeros((n_s, n_s), dtype=np.complex128)
        W_s = np.zeros((n_s, n_s), dtype=np.complex128)
        # Pre-slice per m column blocks
        by_m = {}
        for pos, (ell, m) in enumerate(keys):
            by_m.setdefault(m, []).append((pos, ell))

        # Matrix helper by (m', m) pair using BLAS matrix-matrix product across ell' x ell
        ls_by_m = {m: [e for _, e in pairs] for m, pairs in by_m.items()}
        pos_by_m = {m: np.array([p for p, _ in pairs], dtype=int) for m, pairs in by_m.items()}

        Y_s = {m: np.vstack([basis_theta[(s, ell, m)] for ell in ls_by_m[m]]) for m in by_m}
        Y_sp1 = {
            m: np.vstack([
                (-math.sqrt(max(0, (ell - s) * (ell + s + 1))) * basis_theta[(s + 1, ell, m)])
                if abs(s + 1) <= ell else np.zeros(n_th, dtype=np.complex128)
                for ell in ls_by_m[m]
            ])
            for m in by_m
        }
        Y_sm1 = {
            m: np.vstack([
                (+math.sqrt(max(0, (ell + s) * (ell - s + 1))) * basis_theta[(s - 1, ell, m)])
                if abs(s - 1) <= ell else np.zeros(n_th, dtype=np.complex128)
                for ell in ls_by_m[m]
            ])
            for m in by_m
        }

        for mp, p_mp in pos_by_m.items():
            Ym_conj = np.conj(Y_s[mp]) * w_th[None, :]
            for m, p_m in pos_by_m.items():
                dm = mp - m
                if abs(dm) > n_ph // 2:
                    continue
                bin_idx = dm % n_ph
                vp_dm = fft_vp[:, bin_idx]
                vm_dm = fft_vm[:, bin_idx]
                psi_dm = fft_psi[:, bin_idx]
                if np.max(np.abs(vp_dm)) > 1e-16 or np.max(np.abs(vm_dm)) > 1e-16:
                    # +0.5 * (v_- * eth + v_+ * ethbar) Y_{lm} = -(v_th d_th + v_ph/sin th d_ph + i s cot th v_ph)
                    # Note Goldberg eth = -(d_th - s cot th + i/sin th d_ph) already carries -1, so +0.5 gives partial_N = -(dn/dN . grad)!
                    adv_blk = +0.5 * (
                        (Ym_conj * vm_dm[None, :]) @ Y_sp1[m].T
                        + (Ym_conj * vp_dm[None, :]) @ Y_sm1[m].T
                    )
                    D_s[np.ix_(p_mp, p_m)] = adv_blk
                if s != 0 and np.max(np.abs(psi_dm)) > 1e-16:
                    w_blk = (Ym_conj * psi_dm[None, :]) @ Y_s[m].T
                    W_s[np.ix_(p_mp, p_m)] = w_blk
        return D_s, W_s

    D_0, _ = _compute_spin_adv_and_psi(0, 0)
    D_p2, W_p2 = _compute_spin_adv_and_psi(2, 2)
    D_m2, W_m2 = _compute_spin_adv_and_psi(-2, 2)

    # Split geodesic advection into exact skew-Hermitian unitary transport vs Hermitian divergence
    D_0_u = 0.5 * (D_0 - D_0.conj().T)
    D_p2_u = 0.5 * (D_p2 - D_p2.conj().T)
    D_m2_u = 0.5 * (D_m2 - D_m2.conj().T)
    D_0_div = 0.5 * (D_0 + D_0.conj().T)

    # Verify W_p2, W_m2 Hermiticity
    w_herm_err = max(
        float(np.max(np.abs(W_p2 - W_p2.conj().T))),
        float(np.max(np.abs(W_m2 - W_m2.conj().T))),
    )
    if w_herm_err > 1e-12:
        raise RuntimeError(f"Screen twist Hermitian matrix check failed: {w_herm_err}")

    # Convert spin (+2, -2) to (E, B): a^{(+2)} = E + i B, a^{(-2)} = E - i B
    # Advection unitary: E' = 0.5*(D+ + D-) E + 0.5i*(D+ - D-) B; B' = -0.5i*(D+ - D-) E + 0.5*(D+ + D-) B
    M_adv_EE_u = 0.5 * (D_p2_u + D_m2_u)
    M_adv_EB_u = 0.5j * (D_p2_u - D_m2_u)
    M_adv_BE_u = -0.5j * (D_p2_u - D_m2_u)
    M_adv_BB_u = M_adv_EE_u

    M_adv_EE = 0.5 * (D_p2 + D_m2)
    M_adv_EB = 0.5j * (D_p2 - D_m2)
    M_adv_BE = -0.5j * (D_p2 - D_m2)
    M_adv_BB = M_adv_EE

    # Twist unitary (+2i psi' P+ / -2i psi' P-):
    # E' = i*(W+ - W-) E - (W+ + W-) B; B' = +(W+ + W-) E + i*(W+ - W-) B
    M_tw_EE = 1j * (W_p2 - W_m2)
    M_tw_EB = -(W_p2 + W_m2)
    M_tw_BE = +(W_p2 + W_m2)
    M_tw_BB = M_tw_EE

    # Embed into unified global sparse matrix of shape (dim, dim)
    keys_T = [(ell, m) for m in m_values for ell in range(abs(m), L + 1)]
    keys_EB = [(ell, m) for m in m_values for ell in range(max(2, abs(m)), L + 1)]
    off_T = np.array([idx_map["T"][k] for k in keys_T], dtype=int)
    off_E = np.array([idx_map["E"][k] for k in keys_EB], dtype=int)
    off_B = np.array([idx_map["B"][k] for k in keys_EB], dtype=int)

    M_adv_u = lil_matrix((dim, dim), dtype=np.complex128)
    M_adv_full = lil_matrix((dim, dim), dtype=np.complex128)
    M_tw = lil_matrix((dim, dim), dtype=np.complex128)

    def _insert_sparse(M_lil, r_idx, c_idx, mat, tol=1e-15):
        rr, cc = np.where(np.abs(mat) > tol)
        for i, j in zip(rr, cc):
            M_lil[r_idx[i], c_idx[j]] = mat[i, j]

    _insert_sparse(M_adv_u, off_T, off_T, D_0_u)
    _insert_sparse(M_adv_u, off_E, off_E, M_adv_EE_u)
    _insert_sparse(M_adv_u, off_E, off_B, M_adv_EB_u)
    _insert_sparse(M_adv_u, off_B, off_E, M_adv_BE_u)
    _insert_sparse(M_adv_u, off_B, off_B, M_adv_BB_u)

    _insert_sparse(M_adv_full, off_T, off_T, D_0)
    _insert_sparse(M_adv_full, off_E, off_E, M_adv_EE)
    _insert_sparse(M_adv_full, off_E, off_B, M_adv_EB)
    _insert_sparse(M_adv_full, off_B, off_E, M_adv_BE)
    _insert_sparse(M_adv_full, off_B, off_B, M_adv_BB)

    _insert_sparse(M_tw, off_E, off_E, M_tw_EE)
    _insert_sparse(M_tw, off_E, off_B, M_tw_EB)
    _insert_sparse(M_tw, off_B, off_E, M_tw_BE)
    _insert_sparse(M_tw, off_B, off_B, M_tw_BB)

    M_adv_u_csc = M_adv_u.tocsc()
    M_adv_full_csc = M_adv_full.tocsc()
    M_tw_csc = M_tw.tocsc()
    M_tot_unitary = M_adv_u_csc + M_tw_csc
    M_geo_exact = M_adv_full_csc + M_tw_csc
    skew_err = float(np.max(np.abs((M_tot_unitary + M_tot_unitary.getH()).toarray())))
    if skew_err > 1e-12:
        raise RuntimeError(f"Coupled geodesic operator skew-Hermitian violation: {skew_err}")

    # Measure cross-m coupling Frobenius norm vs total Frobenius norm on exact Liouville operator
    m_col = np.zeros(dim, dtype=int)
    for k, i in idx_map["T"].items():
        m_col[i] = k[1]
    for k, i in idx_map["E"].items():
        m_col[i] = k[1]
    for k, i in idx_map["B"].items():
        m_col[i] = k[1]
    coo = M_geo_exact.tocoo()
    cross_mask = m_col[coo.row] != m_col[coo.col]
    cross_m_frob = float(np.linalg.norm(coo.data[cross_mask]))
    total_frob = float(np.linalg.norm(coo.data))

    return {
        "M_adv_unitary": M_adv_u_csc,
        "M_twist": M_tw_csc,
        "M_geo_unitary": M_tot_unitary,
        "M_geo_exact": M_geo_exact,
        "skew_hermitian_err": skew_err,
        "w_twist_hermitian_err": w_herm_err,
        "adv_divergence_frobenius": float(np.linalg.norm(D_0_div)),
        "cross_m_frobenius": cross_m_frob,
        "total_geo_frobenius": total_frob,
        "cross_m_coupling_fraction": float(cross_m_frob / max(total_frob, 1e-30)),
        "dn_dN": dn_dN,
        "dpsi_dN": dpsi_dN,
        "grid": (TH, PH, n_hat_grid, weights),
        "basis_theta": basis_theta,
    }


def verify_angular_quadrature_oracle() -> dict:
    """Verify M_twist, M_geo_exact, and reality parity against 2D GL and live 4D R49 geodesics."""
    from scipy.linalg import expm
    from bass.transport.general_bianchi_transfer import _fast_spin2_alm_from_gl, integrate_polarized_geodesics, qu_from_spin2_alm

    L = 6
    n_gl = 18
    m_vals = tuple(range(-L, L + 1))  # exact full all-m at L=6
    idx_map, dim = _mode_index_table(L, m_vals)
    # Use a helical + curved VI_{-1/9}-like geometry with non-axisymmetric rotation
    alg_a = np.array([0.04, -0.02, 0.03], dtype=np.float64)
    alg_n = np.array([[0.05, 0.03, -0.01], [0.03, -0.02, 0.04], [-0.01, 0.04, 0.06]], dtype=np.float64)
    sig_gen = pstf_rank2(np.array([[0.02, 0.015, -0.01], [0.015, -0.01, 0.02], [-0.01, 0.02, -0.01]], dtype=np.float64))

    op = _project_gamma4_to_coupled_m_operators(L, m_vals, idx_map, dim, sig_gen, alg_a, alg_n, n_gl_theta=n_gl)
    TH, PH, n_hat_grid, _ = op["grid"]

    rng = np.random.default_rng(9703)
    alm_E = {}; alm_B = {}
    y_test = np.zeros(dim, dtype=np.complex128)
    for ell in range(2, L - 1):  # L-2 bandlimit so dpsi * Y_{l} fits inside L without truncation leakage
        for m in range(0, ell + 1):
            cE = (rng.normal() + (0.0 if m == 0 else 1j * rng.normal())) * 0.1
            cB = (rng.normal() + (0.0 if m == 0 else 1j * rng.normal())) * 0.07
            cT = (rng.normal() + (0.0 if m == 0 else 1j * rng.normal())) * 0.2
            alm_E[(ell, m)] = cE; alm_B[(ell, m)] = cB
            y_test[idx_map["E"][(ell, m)]] = cE
            y_test[idx_map["B"][(ell, m)]] = cB
            y_test[idx_map["T"][(ell, m)]] = cT
            if m > 0:
                alm_E[(ell, -m)] = ((-1) ** m) * np.conj(cE)
                alm_B[(ell, -m)] = ((-1) ** m) * np.conj(cB)
                y_test[idx_map["E"][(ell, -m)]] = alm_E[(ell, -m)]
                y_test[idx_map["B"][(ell, -m)]] = alm_B[(ell, -m)]
                y_test[idx_map["T"][(ell, -m)]] = ((-1) ** m) * np.conj(cT)

    # Check 1: Exact screen twist matrix action vs 2D GL (Q', U') = (-2 dpsi' U, +2 dpsi' Q)
    Q_g, U_g = qu_from_spin2_alm(alm_E, alm_B, TH, PH, ell_max=L)
    dpsi = op["dpsi_dN"]
    ae_tw_grid, ab_tw_grid = _fast_spin2_alm_from_gl(-2.0 * dpsi * U_g, +2.0 * dpsi * Q_g, TH.shape[0], L)
    y_tw_mat = op["M_twist"] @ y_test
    max_tw_err = 0.0
    for ell in range(2, L + 1):
        for m in range(-ell, ell + 1):
            max_tw_err = max(
                max_tw_err,
                abs(y_tw_mat[idx_map["E"][(ell, m)]] - ae_tw_grid[(ell, m)]),
                abs(y_tw_mat[idx_map["B"][(ell, m)]] - ab_tw_grid[(ell, m)]),
            )

    # Check 2: Live 4D R49 geodesic ray oracle exp(+dN * M_geo_exact) vs integrate_polarized_geodesics over dN=1e-5
    from bass.transport.general_bianchi_transfer import _fast_scalar_alm_from_gl
    dN_ray = 1e-5
    rays = integrate_polarized_geodesics(
        n_hat_grid,
        family="VII_h",
        H0=1.0,
        sigma_ab=sig_gen,
        a_vec=alg_a,
        n_mat=alg_n,
        n_efolds_star=-dN_ray,
        n_steps=32,
    )
    n_emit = -rays.p_emit / np.linalg.norm(rays.p_emit, axis=-1, keepdims=True)
    A_T = rng.normal(size=(3, 3))
    A_T = 0.5 * (A_T + A_T.T)
    Pi_em = pstf_rank2(rng.normal(size=(3, 3)))

    def _eval_T(n_arr):
        return np.einsum("...i,ij,...j->...", n_arr, A_T, n_arr) + 0.3 * n_arr[..., 0] * n_arr[..., 1] * n_arr[..., 2]

    def _eval_QU(s1, s2):
        q = 0.5 * (np.einsum("...i,ij,...j->...", s1, Pi_em, s1) - np.einsum("...i,ij,...j->...", s2, Pi_em, s2))
        u = np.einsum("...i,ij,...j->...", s1, Pi_em, s2)
        return q, u

    def _sky_to_vec(Tg, Qg, Ug):
        aT = _fast_scalar_alm_from_gl(Tg, n_gl, L)
        aE, aB = _fast_spin2_alm_from_gl(Qg, Ug, n_gl, L)
        v = np.zeros(dim, dtype=np.complex128)
        for key, val in aT.items():
            if key in idx_map["T"]:
                v[idx_map["T"][key]] = val
        for key, val in aE.items():
            if key in idx_map["E"]:
                v[idx_map["E"][key]] = val
        for key, val in aB.items():
            if key in idx_map["B"]:
                v[idx_map["B"][key]] = val
        return v

    y0_sky = _sky_to_vec(_eval_T(n_hat_grid), *_eval_QU(*_spherical_screen_basis(n_hat_grid)))
    y_ray = _sky_to_vec(_eval_T(n_emit), *_eval_QU(rays.s1_emit, rays.s2_emit))
    y_op = expm(dN_ray * op["M_geo_exact"].toarray()) @ y0_sky
    n_T = len(idx_map["T"])
    n_E = len(idx_map["E"])
    rel_T = float(np.linalg.norm(y_op[:n_T] - y_ray[:n_T]) / max(np.linalg.norm(y_ray[:n_T] - y0_sky[:n_T]), 1e-30))
    rel_E = float(np.linalg.norm(y_op[n_T : n_T + n_E] - y_ray[n_T : n_T + n_E]) / max(np.linalg.norm(y_ray[n_T : n_T + n_E] - y0_sky[n_T : n_T + n_E]), 1e-30))
    rel_B = float(np.linalg.norm(y_op[n_T + n_E :] - y_ray[n_T + n_E :]) / max(np.linalg.norm(y_ray[n_T + n_E :] - y0_sky[n_T + n_E :]), 1e-30))
    if max(rel_T, rel_E, rel_B) > 1e-8:
        raise RuntimeError(f"4D geodesic ray oracle mismatch: T={rel_T}, E={rel_E}, B={rel_B}")

    # Check 3: Reality conjugate parity on full M_geo_exact @ y_test
    y_adv = op["M_geo_exact"] @ y_test
    max_conj_parity_err = 0.0
    for ch in ("T", "E", "B"):
        lmin = 0 if ch == "T" else 2
        for ell in range(lmin, L + 1):
            for m in range(1, ell + 1):
                c_pos = y_adv[idx_map[ch][(ell, m)]]
                c_neg = y_adv[idx_map[ch][(ell, -m)]]
                max_conj_parity_err = max(max_conj_parity_err, abs(c_neg - ((-1) ** m) * np.conj(c_pos)))

    return {
        "twist_operator_vs_2d_gl_grid_max_abs_err": float(max_tw_err),
        "r49_4d_geodesic_oracle_rel_err_T": rel_T,
        "r49_4d_geodesic_oracle_rel_err_E": rel_E,
        "r49_4d_geodesic_oracle_rel_err_B": rel_B,
        "geo_operator_reality_conjugate_parity_err": float(max_conj_parity_err),
        "skew_hermitian_err": op["skew_hermitian_err"],
    }


def _family_rescaled_trajectory_history(family_label: str, z_fwd: np.ndarray, sigma_amp: float = 1e-4, omega_k: float = 0.04, handedness: int = 1):
    """Integrate actual R49 Einstein-Euler trajectory and construct bounded conformal history H(N), sig_N(N), a_N(N), n_N(N)."""
    if family_label == "FLRW":
        return {"sig": np.zeros((3, 3)), "a": np.zeros(3), "n": np.zeros((3, 3)), "r49_max_cod": 0.0, "h_param": None}
    if family_label == "VI_-1/9_exception":
        st = _build_vi_minus_1_9_state()
    else:
        st = _build_default_admissible_state_for_family(family_label)
    traj = evolve_general_tilted_bianchi(
        st,
        eos_by_species={"photon": 1.0 / 3.0, "cdm": 0.0},
        config=TiltedEvolutionConfig(N_start=0.0, N_end=2.0, n_eval=21, method="DOP853", rtol=1e-9, atol=1e-11),
    )
    # Extract exact dimensional ratios at R49 trajectory endpoint and normalize cleanly to bounded conformal amplitude
    sig_r49 = traj.sigma_ab_grid[-1] / traj.H_grid[-1]
    sig_norm = max(float(np.linalg.norm(sig_r49)), 1e-30)
    # Use general non-axisymmetric rotation R so sigma_ab excites all m in {-2,-1,0,1,2} EXCEPT for axisymmetric I control
    sig_N = (sig_r49 / sig_norm) * sigma_amp
    a_r49 = traj.a_grid[-1] / traj.H_grid[-1]
    n_r49 = traj.n_grid[-1] / traj.H_grid[-1]
    curv_scale = math.sqrt(max(abs(omega_k), 0.0))
    ref_curv = max(float(np.linalg.norm(a_r49)), float(np.linalg.norm(n_r49)), 1e-30)
    if family_label == "I":
        a_N = np.zeros(3, dtype=np.float64)
        n_N = np.zeros((3, 3), dtype=np.float64)
    elif family_label == "VII_0":
        a_N = np.zeros(3, dtype=np.float64)
        n_N = handedness * (n_r49 / ref_curv) * 0.08
    else:
        a_N = a_r49 * (curv_scale / ref_curv)
        n_N = handedness * n_r49 * (curv_scale / ref_curv)
    # Verify exact Class-B rotationally-invariant Casimir h = 2||a||^2 / [(tr n)^2 - tr(n^2)] == -1/9 under uniform scaling
    h_actual = None
    if family_label == "VI_-1/9_exception":
        tr_n = float(np.trace(n_N))
        prod23 = 0.5 * (tr_n * tr_n - float(np.trace(n_N @ n_N)))
        h_actual = float(np.dot(a_N, a_N) / prod23)
        if abs(h_actual - (-1.0 / 9.0)) > 1e-11:
            raise RuntimeError(f"VI_-1/9 h-parameter invariance violated: {h_actual}")
    return {
        "sig": pstf_rank2(sig_N),
        "a": a_N,
        "n": 0.5 * (n_N + n_N.T),
        "r49_max_cod": float(traj.max_codazzi_residual_rel),
        "r49_max_ham": float(traj.max_hamiltonian_residual_rel),
        "h_param": h_actual,
    }


def evolve_coupled_m_system(
    vis: dict,
    *,
    L: int,
    m_values: tuple[int, ...],
    sig_N: np.ndarray,
    a_N: np.ndarray,
    n_N: np.ndarray,
    k: float = 0.002,
    include_geo_coupling: bool = True,
) -> dict:
    """Evolve the complete coupled-(m, ell, T/E/B) sparse LU hierarchy over R95 HyRec-2+tanh timeline."""
    idx_map, dim = _mode_index_table(L, m_values)
    A, K = _build_diag_stream_and_thomson(L, m_values, idx_map, dim, k)
    if include_geo_coupling and (np.any(sig_N) or np.any(a_N) or np.any(n_N)):
        geo = _project_gamma4_to_coupled_m_operators(L, m_values, idx_map, dim, sig_N, a_N, n_N)
        M_geo = geo["M_geo_exact"]
        cross_m_frac = geo["cross_m_coupling_fraction"]
        skew_geo = geo["skew_hermitian_err"]
    else:
        M_geo = csc_matrix((dim, dim), dtype=np.complex128)
        cross_m_frac = 0.0
        skew_geo = 0.0

    # Pre-project normalized STF source harmonics S_2m for m in m_values intersect [-2..2]
    quad_m = stf_source_harmonics(sig_N)
    #Wait: stf_source_harmonics projects n^T S n on S^2, whose scale already carries ||sig_N||!
    # Check consistency with R96: R96 passed -sigma * (H/(1+z)) / ((1+z)/1100)^0.25 * q[m];
    # here quad_m = <Y_{2m} | n^T sig_N n> ALREADY includes the dimensionless shear tensor sig_N magnitude!
    zf = vis["z_fwd"]
    H = vis["H_fwd_Mpc"]
    tdot = vis["tdot_fwd_Mpc"]
    deta = vis["d_eta"]

    y = np.zeros(dim, dtype=np.complex128)
    I_sp = eye(dim, format="csc", dtype=np.complex128)
    active_m2 = [m for m in m_values if abs(m) <= 2]
    for j, dt in enumerate(deta):
        z_mid = 0.5 * (zf[j] + zf[j + 1])
        H_mid = 0.5 * (H[j] + H[j + 1])
        tdot_mid = 0.5 * (tdot[j] + tdot[j + 1])
        H_conf = H_mid / (1.0 + z_mid)
        decay = ((1.0 + z_mid) / 1100.0) ** (-0.25)

        s_vec = np.zeros(dim, dtype=np.complex128)
        for m in active_m2:
            s_vec[idx_map["T"][(2, m)]] = -H_conf * decay * quad_m[m]

        op_step = A + tdot_mid * K + H_conf * M_geo
        y = splu(I_sp - dt * op_step).solve(y + dt * s_vec)

    if not np.all(np.isfinite(y)):
        raise RuntimeError("Non-finite state in coupled-m solver")

    # Compute spectra C_ell^{TT, EE, BB, TE, TB, EB}, reality parity residual, and per-m power breakdown
    cl = {name: np.zeros(L + 1, dtype=np.float64) for name in ("TT", "EE", "BB", "TE", "TB", "EB")}
    pow_by_m = {str(m): 0.0 for m in m_values}
    conj_err = 0.0
    for ell in range(L + 1):
        denom = float(2 * ell + 1)
        tt = 0.0; ee = 0.0; bb = 0.0; te = 0.0; tb = 0.0; eb = 0.0
        for m in m_values:
            if abs(m) > ell:
                continue
            t_val = y[idx_map["T"][(ell, m)]]
            tt += abs(t_val) ** 2
            pow_by_m[str(m)] += abs(t_val) ** 2
            if ell >= 2:
                e_val = y[idx_map["E"][(ell, m)]]
                b_val = y[idx_map["B"][(ell, m)]]
                ee += abs(e_val) ** 2
                bb += abs(b_val) ** 2
                te += (t_val * np.conj(e_val)).real
                tb += (t_val * np.conj(b_val)).real
                eb += (e_val * np.conj(b_val)).real
                pow_by_m[str(m)] += abs(e_val) ** 2 + abs(b_val) ** 2
            if m > 0 and (-m in m_values):
                conj_err = max(conj_err, abs(y[idx_map["T"][(ell, -m)]] - ((-1) ** m) * np.conj(t_val)))
                if ell >= 2:
                    conj_err = max(
                        conj_err,
                        abs(y[idx_map["E"][(ell, -m)]] - ((-1) ** m) * np.conj(y[idx_map["E"][(ell, m)]])),
                        abs(y[idx_map["B"][(ell, -m)]] - ((-1) ** m) * np.conj(y[idx_map["B"][(ell, m)]])),
                    )
        cl["TT"][ell] = tt / denom
        if ell >= 2:
            cl["EE"][ell] = ee / denom; cl["BB"][ell] = bb / denom
            cl["TE"][ell] = te / denom; cl["TB"][ell] = tb / denom; cl["EB"][ell] = eb / denom

    tot_e = float(np.sum([abs(y[idx_map["E"][k]]) ** 2 for k in idx_map["E"]]))
    tot_b = float(np.sum([abs(y[idx_map["B"][k]]) ** 2 for k in idx_map["B"]]))
    m0_t = sum(abs(y[idx_map["T"][(ell, 0)]]) ** 2 for ell in range(L + 1)) if 0 in m_values else 0.0
    mn0_t = sum(abs(y[idx_map["T"][(ell, m)]]) ** 2 for m in m_values if m != 0 for ell in range(abs(m), L + 1))
    return {
        "L": L,
        "state_dim": dim,
        "cross_m_coupling_fraction": cross_m_frac,
        "geo_skew_hermitian_err": skew_geo,
        "reality_conjugate_parity_err": float(conj_err),
        "all_mode_norm": float(np.linalg.norm(y)),
        "total_E_power": tot_e,
        "total_B_power": tot_b,
        "B_over_E_norm_ratio": float(math.sqrt(tot_b) / max(math.sqrt(tot_e), 1e-30)),
        "m_nonzero_over_total_T_power": float(mn0_t / max(m0_t + mn0_t, 1e-30)),
        "power_by_m": pow_by_m,
        "cl_TT_2_to_5": cl["TT"][2:6].tolist(),
        "cl_EE_2_to_5": cl["EE"][2:6].tolist(),
        "cl_BB_2_to_5": cl["BB"][2:6].tolist(),
        "cl_TB_2_to_5": cl["TB"][2:6].tolist(),
        "cl_EB_2_to_5": cl["EB"][2:6].tolist(),
        "cl_full": {c: cl[c].tolist() for c in cl},
    }


def compute() -> dict:
    t0 = time.perf_counter()
    oracle = verify_angular_quadrature_oracle()
    vis = _prepare_physical_visibility_timeline()
    m5 = (-2, -1, 0, 1, 2)

    # 1. Negative & axisymmetry controls at L=16
    ctrl_flrw = evolve_coupled_m_system(
        vis, L=16, m_values=m5, sig_N=np.zeros((3, 3)), a_N=np.zeros(3), n_N=np.zeros((3, 3)), k=0.002
    )
    sig_axi = pstf_rank2(np.diag([1.0, 1.0, -2.0])) * (5e-5 / math.sqrt(6.0))
    ctrl_axi_I = evolve_coupled_m_system(
        vis, L=16, m_values=m5, sig_N=sig_axi, a_N=np.zeros(3), n_N=np.zeros((3, 3)), k=0.002
    )
    # Pure axisymmetric m=0 shear in non-helical I must yield cross_m=0 and m_nonzero=0 and B=0!
    if ctrl_flrw["all_mode_norm"] > 1e-25:
        raise RuntimeError(f"FLRW coupled-m null control failed: {ctrl_flrw['all_mode_norm']}")
    if ctrl_axi_I["m_nonzero_over_total_T_power"] > 1e-22 or ctrl_axi_I["total_B_power"] > 1e-22:
        raise RuntimeError(f"Axisymmetric Bianchi-I control failed: {ctrl_axi_I}")

    # 2. Pure axisymmetric shear injected into HELICAL/CURVED Bianchi VI_{-1/9} and VII_h (proves m=0 -> m!=0 scattering strictly from Gamma4 coupling!)
    r_v = _family_rescaled_trajectory_history("V", vis["z_fwd"], sigma_amp=5e-5, omega_k=0.04)
    r_vi = _family_rescaled_trajectory_history("VI_-1/9_exception", vis["z_fwd"], sigma_amp=5e-5, omega_k=0.04)
    r_7h_pos = _family_rescaled_trajectory_history("VII_h", vis["z_fwd"], sigma_amp=5e-5, omega_k=0.04, handedness=1)
    r_70 = _family_rescaled_trajectory_history("VII_0", vis["z_fwd"], sigma_amp=5e-5, omega_k=0.0)
    r_ix = _family_rescaled_trajectory_history("IX", vis["z_fwd"], sigma_amp=5e-5, omega_k=0.04)

    # Inject PURE m=0 axisymmetric shear sig_axi into non-axisymmetric VI_{-1/9} & tilted-n IX to measure m=0 -> m!=0 scattering directly!
    R_tilt = Rotation.from_euler("zyx", [0.4, 0.7, -0.3]).as_matrix()
    scatter_vi = evolve_coupled_m_system(
        vis, L=16, m_values=m5, sig_N=sig_axi, a_N=r_vi["a"], n_N=r_vi["n"], k=0.002
    )
    scatter_ix_tilted = evolve_coupled_m_system(
        vis, L=16, m_values=m5, sig_N=sig_axi, a_N=np.zeros(3), n_N=R_tilt @ r_ix["n"] @ R_tilt.T, k=0.002
    )

    # 3. Full coupled evolution across L in {8, 16, 32, 60} for R49 trajectories (non-axisymmetric rotated R49 shear + curvature)
    families_L = {}
    for L in (8, 16, 32, 60):
        families_L[str(L)] = {}
        for fname, hist in (("I_rotated", {"sig": R_tilt @ sig_axi @ R_tilt.T, "a": np.zeros(3), "n": np.zeros((3, 3))}),
                            ("V", r_v), ("VI_-1/9", r_vi), ("VII_0", r_70), ("VII_h", r_7h_pos), ("IX", r_ix)):
            res = evolve_coupled_m_system(
                vis, L=L, m_values=m5, sig_N=hist["sig"], a_N=hist["a"], n_N=hist["n"], k=0.002
            )
            res.pop("cl_full")
            families_L[str(L)][fname] = res

    # Measure L=32 -> L=60 truncation convergence across all 6 geometries
    l32_vs_l60_be_rel = {}
    for fname in ("I_rotated", "V", "VI_-1/9", "VII_0", "VII_h", "IX"):
        b32 = families_L["32"][fname]["B_over_E_norm_ratio"]
        b60 = families_L["60"][fname]["B_over_E_norm_ratio"]
        l32_vs_l60_be_rel[fname] = float(abs(b60 - b32) / max(b60, 1e-30))

    # 4. Chirality/handedness parity flip check on VII_h under exact improper O(3) reflection (P sig P^T, P a, -P n P^T) at L=16
    P_refl = np.diag([1.0, -1.0, 1.0])
    c_p = evolve_coupled_m_system(vis, L=16, m_values=m5, sig_N=r_7h_pos["sig"], a_N=r_7h_pos["a"], n_N=r_7h_pos["n"], k=0.002)
    c_m = evolve_coupled_m_system(
        vis, L=16, m_values=m5,
        sig_N=P_refl @ r_7h_pos["sig"] @ P_refl.T,
        a_N=P_refl @ r_7h_pos["a"],
        n_N=-P_refl @ r_7h_pos["n"] @ P_refl.T,
        k=0.002,
    )
    chiral_tb_sum = float(np.max(np.abs(np.array(c_p["cl_full"]["TB"]) + np.array(c_m["cl_full"]["TB"]))))
    chiral_tb_scale = float(np.max(np.abs(c_p["cl_full"]["TB"])))
    chiral_eb_sum = float(np.max(np.abs(np.array(c_p["cl_full"]["EB"]) + np.array(c_m["cl_full"]["EB"]))))
    chiral_eb_scale = float(np.max(np.abs(c_p["cl_full"]["EB"])))
    chiral_tt_diff = float(np.max(np.abs(np.array(c_p["cl_full"]["TT"]) - np.array(c_m["cl_full"]["TT"]))) / max(np.max(c_p["cl_full"]["TT"]), 1e-30))

    # 5. Exact k=0 real-sky conjugate parity check (for k>0 plane-wave streaming -i*k introduces complex Fourier phase)
    ctrl_k0_real = evolve_coupled_m_system(
        vis, L=12, m_values=tuple(range(-12, 13)),
        sig_N=R_tilt @ sig_axi @ R_tilt.T, a_N=r_vi["a"], n_N=r_vi["n"], k=0.0,
    )
    if ctrl_k0_real["reality_conjugate_parity_err"] > 1e-12:
        raise RuntimeError(f"k=0 reality conjugate parity failed: {ctrl_k0_real['reality_conjugate_parity_err']}")

    # 6. Full all-|m|<=L (dim=231 at L=8, dim=499 at L=12) vs m_values=(-2..2) comparison on VI_{-1/9}
    res_allm_L8 = evolve_coupled_m_system(
        vis, L=8, m_values=tuple(range(-8, 9)), sig_N=sig_axi, a_N=r_vi["a"], n_N=r_vi["n"], k=0.002
    )
    res_m5_L8 = evolve_coupled_m_system(
        vis, L=8, m_values=m5, sig_N=sig_axi, a_N=r_vi["a"], n_N=r_vi["n"], k=0.002
    )
    m_gt2_pow_8 = sum(v for k, v in res_allm_L8["power_by_m"].items() if abs(int(k)) > 2)
    tot_allm_pow_8 = sum(res_allm_L8["power_by_m"].values())

    res_allm_L12 = evolve_coupled_m_system(
        vis, L=12, m_values=tuple(range(-12, 13)), sig_N=sig_axi, a_N=r_vi["a"], n_N=r_vi["n"], k=0.002
    )
    res_m5_L12 = evolve_coupled_m_system(
        vis, L=12, m_values=m5, sig_N=sig_axi, a_N=r_vi["a"], n_N=r_vi["n"], k=0.002
    )
    m_gt2_pow_12 = sum(v for k, v in res_allm_L12["power_by_m"].items() if abs(int(k)) > 2)
    tot_allm_pow_12 = sum(res_allm_L12["power_by_m"].values())

    out = {
        "schema": "htt.r97.bianchi_coupled_m_spin2_transport/1",
        "elapsed_seconds": time.perf_counter() - t0,
        "signature": SIGNATURE,
        "units": {"k_Mpc_inv": 0.002, "H_conf": "1/Mpc", "d_eta": "Mpc", "sigma_N_and_a_N_n_N": "H-normalized dimensionless"},
        "oracle_verification": oracle,
        "controls": {
            "FLRW_all_mode_norm": ctrl_flrw["all_mode_norm"],
            "Bianchi_I_axisym_m_nonzero_ratio": ctrl_axi_I["m_nonzero_over_total_T_power"],
            "Bianchi_I_axisym_total_B_power": ctrl_axi_I["total_B_power"],
            "k0_allm_L12_reality_conjugate_parity_err": ctrl_k0_real["reality_conjugate_parity_err"],
            "m0_seed_scattering_VI_minus_1_9": {
                "h_parameter_preserved": r_vi["h_param"],
                "cross_m_coupling_fraction": scatter_vi["cross_m_coupling_fraction"],
                "m_nonzero_over_total_T_power": scatter_vi["m_nonzero_over_total_T_power"],
                "B_over_E_norm_ratio": scatter_vi["B_over_E_norm_ratio"],
            },
            "m0_seed_scattering_IX_tilted": {
                "cross_m_coupling_fraction": scatter_ix_tilted["cross_m_coupling_fraction"],
                "m_nonzero_over_total_T_power": scatter_ix_tilted["m_nonzero_over_total_T_power"],
                "B_over_E_norm_ratio": scatter_ix_tilted["B_over_E_norm_ratio"],
            },
        },
        "chirality_VIIh_L16": {
            "TT_rel_diff": chiral_tt_diff,
            "TB_max_abs": chiral_tb_scale,
            "TB_flip_residual_rel": float(chiral_tb_sum / max(chiral_tb_scale, 1e-30)),
            "EB_max_abs": chiral_eb_scale,
            "EB_flip_residual_rel": float(chiral_eb_sum / max(chiral_eb_scale, 1e-30)),
        },
        "full_all_m_vs_m5_L8_VI_minus_1_9": {
            "all_m_dim": res_allm_L8["state_dim"],
            "m5_dim": res_m5_L8["state_dim"],
            "power_fraction_leaking_to_abs_m_gt_2": float(m_gt2_pow_8 / max(tot_allm_pow_8, 1e-30)),
            "B_over_E_allm": res_allm_L8["B_over_E_norm_ratio"],
            "B_over_E_m5": res_m5_L8["B_over_E_norm_ratio"],
        },
        "full_all_m_vs_m5_L12_VI_minus_1_9": {
            "all_m_dim": res_allm_L12["state_dim"],
            "m5_dim": res_m5_L12["state_dim"],
            "power_fraction_leaking_to_abs_m_gt_2": float(m_gt2_pow_12 / max(tot_allm_pow_12, 1e-30)),
            "B_over_E_allm": res_allm_L12["B_over_E_norm_ratio"],
            "B_over_E_m5": res_m5_L12["B_over_E_norm_ratio"],
        },
        "L32_vs_L60_B_over_E_rel_diff": l32_vs_l60_be_rel,
        "coupled_m5_by_L": families_L,
        "physics_gates": {
            "implementation_verified": True,
            "full_all_m_boltzmann_closure": False,
            "SQ_NATIVE_and_B02_to_B05_promoted": False,
            "source_separation_note": "HyRec-2+tanh optical visibility is Planck 2018 source-qualified; geometric shear/curvature magnitudes are normalized R49 trajectory endpoint/rescaled inputs, not cosmological MCMC posteriors.",
        },
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, indent=2) + "\n")
    return out


if __name__ == "__main__":
    res = compute()
    print(json.dumps({
        "oracle": res["oracle_verification"],
        "k0_parity": res["controls"]["k0_allm_L12_reality_conjugate_parity_err"],
        "scatter_vi": res["controls"]["m0_seed_scattering_VI_minus_1_9"],
        "scatter_ix": res["controls"]["m0_seed_scattering_IX_tilted"],
        "chiral_VIIh": res["chirality_VIIh_L16"],
        "allm_L8": res["full_all_m_vs_m5_L8_VI_minus_1_9"],
        "allm_L12": res["full_all_m_vs_m5_L12_VI_minus_1_9"],
        "L32_vs_L60_BE_rel": res["L32_vs_L60_B_over_E_rel_diff"],
        "L60_VI_dim": res["coupled_m5_by_L"]["60"]["VI_-1/9"]["state_dim"],
        "L60_VI_B_over_E": res["coupled_m5_by_L"]["60"]["VI_-1/9"]["B_over_E_norm_ratio"],
        "elapsed_s": res["elapsed_seconds"],
    }))
