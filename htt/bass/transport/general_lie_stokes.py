"""Native all-m general-Lie polarized I/Q/U/V Boltzmann transport (N1).

Combines:
- 4D synchronous-tetrad Bianchi geodesic advection and Sachs screen twist for any
  Jacobi-admissible Lie algebra (a, N) across Bianchi Class A/B (including VI_{-1/9}
  and IX), spin-0 (T, V) and spin-+/-2 (E, B) signed spherical harmonics.
- General 3D comoving wavevector streaming (-i k . n) across all m in {-L..L}.
- Exact rank-9 Thomson collision operator (trace b=1, quadrupole STF b=7/10 coupling
  T_{2m} <-> E_{2m} with +sqrt(6)/10 under -(Q +- iU) = sum (E +- iB)_{+-2}Y_{lm},
  circular dipole b=1/2 on V_{1m}).
- L-stable SDIRK(2,2) stiff stage solver factoring the full sparse Lie/streaming
  base operator (never a diagonal approximation) combined with a cancellation-free
  9x9 Woodbury/Schur capacity solve preserving the conserved monopole through s=1e100.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from numbers import Integral
from typing import Mapping, Sequence

import numpy as np
from scipy.linalg import lu_factor, lu_solve
from scipy.sparse import csc_matrix, eye, lil_matrix
from scipy.sparse.linalg import splu
from scipy.special import sph_harm_y

from bass.background.convention_bridge import LEVI_CIVITA_3D, build_structure_tensor_with_sign
from bass.background.tilted_bianchi_state import build_4d_bianchi_connection
from bass.transport.general_bianchi_transfer import (
    _spherical_screen_basis,
    gl_sphere_grid,
    spin_weighted_spherical_harmonic_grid,
)

__all__ = [
    "GeneralLieStokesOperator",
    "LieGeometry",
    "alm_dict_to_vector",
    "c_spin",
    "max_stokes_reality_error",
    "stokes_maps_to_vector",
    "thomson_rank9_basis",
    "validate_lie_algebra",
    "vector_to_alm_dict",
    "vector_to_stokes_maps",
]


@dataclass(frozen=True)
class LieGeometry:
    """Dimensionless H-normalized Bianchi geometry tuple (sigma/H, a/H, n/H)."""

    sigma_N: np.ndarray
    a_N: np.ndarray
    n_N: np.ndarray

    def __post_init__(self) -> None:
        sig = np.asarray(self.sigma_N, dtype=np.float64)
        a = np.asarray(self.a_N, dtype=np.float64)
        n = np.asarray(self.n_N, dtype=np.float64)
        if sig.shape != (3, 3) or not np.all(np.isfinite(sig)):
            raise ValueError("sigma_N must be a finite (3, 3) array")
        if np.max(np.abs(sig - sig.T)) > 1e-11 * max(1.0, float(np.max(np.abs(sig)))):
            raise ValueError("sigma_N must be symmetric")
        sig = 0.5 * (sig + sig.T)
        tr = float(np.trace(sig))
        sig_scale = float(np.linalg.norm(sig))
        if abs(tr) > 1e-11 * max(1.0, sig_scale):
            raise ValueError(f"sigma_N must be trace-free, got trace={tr}")
        sig = sig - (tr / 3.0) * np.eye(3, dtype=np.float64)
        validate_lie_algebra(a, n)
        object.__setattr__(self, "sigma_N", sig)
        object.__setattr__(self, "a_N", a.copy())
        object.__setattr__(self, "n_N", 0.5 * (n + n.T))

    def pack_14(self) -> np.ndarray:
        """Pack (sigma_xx, yy, xy, xz, yz, a_0..2, n_xx, yy, zz, xy, xz, yz)."""
        s = self.sigma_N
        a = self.a_N
        n = self.n_N
        return np.array(
            [
                s[0, 0],
                s[1, 1],
                s[0, 1],
                s[0, 2],
                s[1, 2],
                a[0],
                a[1],
                a[2],
                n[0, 0],
                n[1, 1],
                n[2, 2],
                n[0, 1],
                n[0, 2],
                n[1, 2],
            ],
            dtype=np.float64,
        )

    @staticmethod
    def unpack_14(vec: Sequence[float] | np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        v = np.asarray(vec, dtype=np.float64)
        if v.shape != (14,):
            raise ValueError(f"expected length-14 geometry vector, got {v.shape}")
        xx, yy, xy, xz, yz, ax, ay, az, nxx, nyy, nzz, nxy, nxz, nyz = v
        sig = np.array([[xx, xy, xz], [xy, yy, yz], [xz, yz, -(xx + yy)]], dtype=np.float64)
        a = np.array([ax, ay, az], dtype=np.float64)
        n = np.array([[nxx, nxy, nxz], [nxy, nyy, nyz], [nxz, nyz, nzz]], dtype=np.float64)
        return sig, a, n


def validate_lie_algebra(a_vec: Sequence[float] | np.ndarray, n_mat: Sequence[Sequence[float]] | np.ndarray, *, rtol: float = 1e-11) -> None:
    """Enforce real finite symmetry of N and component-wise Jacobi identity N a == 0."""
    a = np.asarray(a_vec, dtype=np.float64)
    n = np.asarray(n_mat, dtype=np.float64)
    if a.shape != (3,) or n.shape != (3, 3) or not (np.all(np.isfinite(a)) and np.all(np.isfinite(n))):
        raise ValueError("Lie algebra requires finite real a_vec (3,) and n_mat (3,3)")
    n_scale = float(np.max(np.abs(n)))
    if float(np.max(np.abs(n - n.T))) > rtol * n_scale:
        raise ValueError("structure matrix n_mat must be symmetric")
    n_sym = 0.5 * (n + n.T)
    jac = n_sym @ a
    scale = float(a @ a + np.sum(n_sym * n_sym))
    jac_inf = float(np.max(np.abs(jac)))
    if scale == 0.0:
        if jac_inf != 0.0:
            raise ValueError("Jacobi identity violated at zero structure scale")
        return
    if jac_inf > rtol * scale:
        raise ValueError(
            f"Bianchi Jacobi identity N @ a == 0 violated: |N a|_inf={jac_inf:.3e}, scale={scale:.3e}"
        )


def c_spin(ell: int, s: int, m: int) -> float:
    """Spin-s cos(theta) ladder coefficient multiplying _sY_{ell-1,m}."""
    if ell <= max(abs(s), abs(m)):
        return 0.0
    return math.sqrt((ell * ell - m * m) * (ell * ell - s * s)) / (
        ell * math.sqrt((2 * ell - 1) * (2 * ell + 1))
    )


def _mode_index_table(L: int, m_values: tuple[int, ...]) -> tuple[dict[str, dict[tuple[int, int], int]], int]:
    idx: dict[str, dict[tuple[int, int], int]] = {"T": {}, "E": {}, "B": {}, "V": {}}
    cur = 0
    for ch, lmin in (("T", 0), ("E", 2), ("B", 2), ("V", 0)):
        for m in m_values:
            for ell in range(max(lmin, abs(m)), L + 1):
                idx[ch][(ell, m)] = cur
                cur += 1
    return idx, cur


def _build_spin_basis_theta(L: int, m_values: tuple[int, ...], th_1d: np.ndarray) -> dict[tuple[int, int, int], np.ndarray]:
    basis: dict[tuple[int, int, int], np.ndarray] = {}
    ph0 = np.zeros_like(th_1d)
    costh = np.cos(th_1d)
    for s in (-3, -2, -1, 0, 1, 2, 3):
        for m in m_values:
            lmin = max(abs(s), abs(m))
            if lmin > L:
                continue
            y_prev = np.zeros_like(th_1d, dtype=np.complex128)
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


def _geodesic_aberration_and_twist(
    n_hat_grid: np.ndarray,
    sig_N: np.ndarray,
    a_N: np.ndarray,
    n_N: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Return dimensionless H-normalized dn/dN and screen twist dpsi/dN on grid."""
    C_sp = build_structure_tensor_with_sign(a_N, n_N, a_sign=1)
    G4 = build_4d_bianchi_connection(1.0, sig_N, C_sp)
    n_flat = n_hat_grid.reshape(-1, 3)
    e_th, e_ph = _spherical_screen_basis(n_hat_grid)
    s1 = e_th.reshape(-1, 3)
    s2 = e_ph.reshape(-1, 3)
    p = -n_flat

    n_rays = p.shape[0]
    u = np.concatenate([np.ones((n_rays, 1)), p], axis=1)
    z1 = np.concatenate([np.zeros((n_rays, 1)), s1], axis=1)
    guu = np.einsum("dba,rb,ra->rd", G4, u, u)
    gz1u = np.einsum("dba,rb,ra->rd", G4, z1, u)
    dp_dN = -(guu[:, 1:] - p * guu[:, 0:1])
    dn_dN = -dp_dN
    ds1_dN = -(gz1u[:, 1:] - p * gz1u[:, 0:1])
    dpsi_dN = np.einsum("ri,ri->r", ds1_dN, s2)
    return dn_dN.reshape(n_hat_grid.shape), dpsi_dN.reshape(n_hat_grid.shape[:-1])


def thomson_rank9_basis(
    idx_map: Mapping[str, Mapping[tuple[int, int], int]], dim: int
) -> tuple[np.ndarray, np.ndarray]:
    """Build orthonormal (dim, 9) basis U and eigenvalues b such that G = U diag(b) U^T, K = G - I."""
    U = np.zeros((dim, 9), dtype=np.float64)
    gains = np.array([1.0] + [0.7] * 5 + [0.5] * 3, dtype=np.float64)
    if (0, 0) in idx_map["T"]:
        U[idx_map["T"][(0, 0)], 0] = 1.0
    inv_rt7 = 1.0 / math.sqrt(7.0)
    rt6_ov_rt7 = math.sqrt(6.0 / 7.0)
    for col, m in enumerate((-2, -1, 0, 1, 2), start=1):
        t2 = idx_map["T"].get((2, m))
        e2 = idx_map["E"].get((2, m))
        if t2 is not None and e2 is not None:
            U[t2, col] = inv_rt7
            U[e2, col] = rt6_ov_rt7
    for col, m in enumerate((-1, 0, 1), start=6):
        v1 = idx_map["V"].get((1, m))
        if v1 is not None:
            U[v1, col] = 1.0
    return U, gains


def vector_to_alm_dict(
    state: np.ndarray, idx_map: Mapping[str, Mapping[tuple[int, int], int]]
) -> dict[str, dict[tuple[int, int], complex]]:
    return {
        ch: {lm: complex(state[pos]) for lm, pos in idx_map[ch].items()}
        for ch in ("T", "E", "B", "V")
    }


def alm_dict_to_vector(
    alm_by_ch: Mapping[str, Mapping[tuple[int, int], complex]],
    idx_map: Mapping[str, Mapping[tuple[int, int], int]],
    dim: int,
) -> np.ndarray:
    vec = np.zeros(dim, dtype=np.complex128)
    for ch in ("T", "E", "B", "V"):
        src = alm_by_ch.get(ch, {})
        for lm, pos in idx_map[ch].items():
            if lm in src:
                vec[pos] = complex(src[lm])
    return vec


def stokes_maps_to_vector(
    stokes_iquv: np.ndarray,
    idx_map: Mapping[str, Mapping[tuple[int, int], int]],
    dim: int,
    *,
    L: int,
    n_gl_theta: int,
) -> np.ndarray:
    """Project (n_th, n_ph, 4) or (n_rays, 4) I/Q/U/V sky on gl_sphere_grid to (T,E,B,V) harmonics."""
    from bass.transport.general_bianchi_transfer import _fast_scalar_alm_from_gl, _fast_spin2_alm_from_gl

    TH, _, _, _ = gl_sphere_grid(n_gl_theta)
    sky = np.asarray(stokes_iquv)
    if sky.ndim == 2:
        sky = sky.reshape(*TH.shape, 4)
    if sky.shape != (*TH.shape, 4):
        raise ValueError(f"expected Stokes sky shape {(*TH.shape, 4)}, got {sky.shape}")

    def _proj_real(arr4: np.ndarray) -> np.ndarray:
        aT = _fast_scalar_alm_from_gl(arr4[..., 0], n_gl_theta, L)
        aE, aB = _fast_spin2_alm_from_gl(arr4[..., 1], arr4[..., 2], n_gl_theta, L)
        aV = _fast_scalar_alm_from_gl(arr4[..., 3], n_gl_theta, L)
        return alm_dict_to_vector({"T": aT, "E": aE, "B": aB, "V": aV}, idx_map, dim)

    if np.iscomplexobj(sky):
        return _proj_real(sky.real) + 1j * _proj_real(sky.imag)
    return _proj_real(sky.astype(np.float64))


def vector_to_stokes_maps(
    vec: np.ndarray,
    idx_map: Mapping[str, Mapping[tuple[int, int], int]],
    *,
    L: int,
    n_gl_theta: int,
) -> np.ndarray:
    """Reconstruct (n_th, n_ph, 4) I/Q/U/V Stokes maps on gl_sphere_grid(n_gl_theta)."""
    from bass.transport.general_bianchi_transfer import map_from_scalar_alm, qu_from_spin2_alm

    TH, PH, _, _ = gl_sphere_grid(n_gl_theta)

    def _rec_real(v_re: np.ndarray) -> np.ndarray:
        # Careful: even when overall state represents real fields (with reality condition),
        # _rec_real handles complex real-space projections if split cleanly into real/imag sky parts.
        alms = vector_to_alm_dict(v_re, idx_map)
        I_m = map_from_scalar_alm(alms["T"], TH, PH, ell_max=L)
        Q_m, U_m = qu_from_spin2_alm(alms["E"], alms["B"], TH, PH, ell_max=L)
        V_m = map_from_scalar_alm(alms["V"], TH, PH, ell_max=L)
        return np.stack((I_m, Q_m, U_m, V_m), axis=-1)

    # Check if state obeys real-field parity; if k != 0 complex mode, reconstruct Re/Im parts faithfully:
    # For general complex harmonic vector y = y_R + i y_I where y_R is Hermitian part 0.5*(y + P y^*):
    if max_stokes_reality_error(vec, idx_map) <= 1e-10:
        return _rec_real(vec)
    # General complex sky: decompose into even/odd reality combinations y_R = 0.5*(y + y_tilde), y_I = -0.5j*(y - y_tilde)
    conj_partner = np.zeros_like(vec)
    for ch in ("T", "E", "B", "V"):
        mp = idx_map[ch]
        for (ell, m), pos in mp.items():
            if (ell, -m) in mp:
                conj_partner[pos] = ((-1.0) ** m) * np.conj(vec[mp[(ell, -m)]])
    y_re = 0.5 * (vec + conj_partner)
    y_im = -0.5j * (vec - conj_partner)
    return _rec_real(y_re) + 1j * _rec_real(y_im)


def max_stokes_reality_error(
    vec: np.ndarray, idx_map: Mapping[str, Mapping[tuple[int, int], int]]
) -> float:
    err = 0.0
    for ch in ("T", "E", "B", "V"):
        mp = idx_map[ch]
        for (ell, m), pos in mp.items():
            if m >= 0 and (ell, -m) in mp:
                err = max(err, float(abs(vec[mp[(ell, -m)]] - ((-1.0) ** m) * np.conj(vec[pos]))))
    return err


def _insert_sparse(M_lil: lil_matrix, r_idx: np.ndarray, c_idx: np.ndarray, mat: np.ndarray, tol: float = 1e-15) -> None:
    rr, cc = np.where(np.abs(mat) > tol)
    for i, j in zip(rr, cc):
        M_lil[r_idx[i], c_idx[j]] += mat[i, j]


class GeneralLieStokesOperator:
    """All-m sparse general-Lie geodesic + 3D Fourier + rank-9 Thomson I/Q/U/V propagator."""

    def __init__(self, L: int, *, m_values: tuple[int, ...] | None = None, n_gl_theta: int | None = None):
        if isinstance(L, (bool, np.bool_)) or not isinstance(L, Integral) or not (2 <= int(L) <= 24):
            raise ValueError("L must be an integer in [2, 24]")
        self.L = int(L)
        self.m_values = tuple(range(-self.L, self.L + 1)) if m_values is None else tuple(m_values)
        self.idx, self.dim = _mode_index_table(self.L, self.m_values)
        self.n_gl_theta = max(self.L + 8, 16) if n_gl_theta is None else int(n_gl_theta)
        if self.n_gl_theta < self.L + 4:
            raise ValueError("n_gl_theta must be >= L + 4 for exact projection")

        TH, PH, n_hat_grid, weights = gl_sphere_grid(self.n_gl_theta)
        self._grid = (TH, PH, n_hat_grid, weights)
        th_1d = TH[:, 0]
        basis_theta = _build_spin_basis_theta(self.L, self.m_values, th_1d)
        self._basis_theta = basis_theta

        # Precompute 14 basis sparse Lie geometry operators + 3 Cartesian Fourier wavevector operators.
        basis_ops = []
        for row in np.eye(14, dtype=np.float64):
            sig, a, n = LieGeometry.unpack_14(row)
            basis_ops.append(self._project_lie_geometry(sig, a, n))
        for axis in range(3):
            basis_ops.append(self._project_cartesian_streaming(axis))

        # Union-of-slots CSC layout for O(nnz) matrix assembly at any step.
        indices = []
        for op in basis_ops:
            coo = op.tocoo()
            indices.append(coo.row.astype(np.int64) * self.dim + coo.col.astype(np.int64))
        slots = np.unique(np.concatenate(indices)) if indices else np.zeros(0, dtype=np.int64)
        coeff = np.zeros((len(slots), len(basis_ops)), dtype=np.complex128)
        for j, (keys, op) in enumerate(zip(indices, basis_ops)):
            coo = op.tocoo()
            coeff[np.searchsorted(slots, keys), j] = coo.data
        tpl = csc_matrix(
            (np.arange(1, len(slots) + 1, dtype=np.float64), (slots // self.dim, slots % self.dim)),
            shape=(self.dim, self.dim),
        )
        self._coeff = coeff[tpl.data.astype(int) - 1]
        self._template = tpl.astype(np.complex128)
        self._I_sp = eye(self.dim, format="csc", dtype=np.complex128)

        # Rank-9 Thomson collision factors G = U diag(gains) U^T, K = G - I.
        self.U_rank9, self.thomson_gains = thomson_rank9_basis(self.idx, self.dim)
        self.K_dense_matrix = self._build_sparse_thomson()

    def _keys_and_offsets(self, ell_min: int, channel: str) -> tuple[list[tuple[int, int]], np.ndarray]:
        keys = [(ell, m) for m in self.m_values for ell in range(max(ell_min, abs(m)), self.L + 1)]
        offs = np.array([self.idx[channel][k] for k in keys], dtype=np.int64)
        return keys, offs

    def _spin_blocks(
        self,
        vp_grid: np.ndarray | None,
        vm_grid: np.ndarray | None,
        scalar_mul_grid: np.ndarray | None,
        *,
        s: int,
        ell_min: int,
        use_advection: bool,
    ) -> tuple[np.ndarray, np.ndarray]:
        TH, PH, _, weights = self._grid
        n_th, n_ph = TH.shape
        w_th = weights.sum(axis=1)
        keys = [(ell, m) for m in self.m_values for ell in range(max(ell_min, abs(m)), self.L + 1)]
        n_s = len(keys)
        D_s = np.zeros((n_s, n_s), dtype=np.complex128)
        W_s = np.zeros((n_s, n_s), dtype=np.complex128)
        by_m: dict[int, list[tuple[int, int]]] = {}
        for pos, (ell, m) in enumerate(keys):
            by_m.setdefault(m, []).append((pos, ell))
        ls_by_m = {m: [e for _, e in pairs] for m, pairs in by_m.items()}
        pos_by_m = {m: np.array([p for p, _ in pairs], dtype=int) for m, pairs in by_m.items()}
        Y_s = {m: np.vstack([self._basis_theta[(s, ell, m)] for ell in ls_by_m[m]]) for m in by_m}

        if use_advection:
            fft_vp = np.fft.fft(vp_grid, axis=1) / float(n_ph)
            fft_vm = np.fft.fft(vm_grid, axis=1) / float(n_ph)
            Y_sp1 = {
                m: np.vstack([
                    (-math.sqrt(max(0, (ell - s) * (ell + s + 1))) * self._basis_theta[(s + 1, ell, m)])
                    if abs(s + 1) <= ell
                    else np.zeros(n_th, dtype=np.complex128)
                    for ell in ls_by_m[m]
                ])
                for m in by_m
            }
            Y_sm1 = {
                m: np.vstack([
                    (+math.sqrt(max(0, (ell + s) * (ell - s + 1))) * self._basis_theta[(s - 1, ell, m)])
                    if abs(s - 1) <= ell
                    else np.zeros(n_th, dtype=np.complex128)
                    for ell in ls_by_m[m]
                ])
                for m in by_m
            }
        else:
            fft_vp = fft_vm = Y_sp1 = Y_sm1 = None

        fft_mul = np.fft.fft(scalar_mul_grid.astype(np.complex128), axis=1) / float(n_ph) if scalar_mul_grid is not None else None

        for mp, p_mp in pos_by_m.items():
            Ym_conj = np.conj(Y_s[mp]) * w_th[None, :]
            for m, p_m in pos_by_m.items():
                dm = mp - m
                if abs(dm) > n_ph // 2:
                    continue
                bin_idx = dm % n_ph
                if use_advection:
                    vp_dm = fft_vp[:, bin_idx]
                    vm_dm = fft_vm[:, bin_idx]
                    if np.max(np.abs(vp_dm)) > 1e-16 or np.max(np.abs(vm_dm)) > 1e-16:
                        D_s[np.ix_(p_mp, p_m)] = 0.5 * (
                            (Ym_conj * vm_dm[None, :]) @ Y_sp1[m].T
                            + (Ym_conj * vp_dm[None, :]) @ Y_sm1[m].T
                        )
                if fft_mul is not None:
                    mul_dm = fft_mul[:, bin_idx]
                    if np.max(np.abs(mul_dm)) > 1e-16:
                        W_s[np.ix_(p_mp, p_m)] = (Ym_conj * mul_dm[None, :]) @ Y_s[m].T
        return D_s, W_s

    def _project_lie_geometry(self, sig_N: np.ndarray, a_N: np.ndarray, n_N: np.ndarray) -> csc_matrix:
        _, _, n_hat_grid, _ = self._grid
        dn_dN, dpsi_dN = _geodesic_aberration_and_twist(n_hat_grid, sig_N, a_N, n_N)
        e_th, e_ph = _spherical_screen_basis(n_hat_grid)
        v_th = np.sum(dn_dN * e_th, axis=-1)
        v_ph = np.sum(dn_dN * e_ph, axis=-1)
        vp = v_th + 1j * v_ph
        vm = v_th - 1j * v_ph

        D_0, _ = self._spin_blocks(vp, vm, None, s=0, ell_min=0, use_advection=True)
        D_p2, W_p2 = self._spin_blocks(vp, vm, dpsi_dN, s=2, ell_min=2, use_advection=True)
        D_m2, W_m2 = self._spin_blocks(vp, vm, dpsi_dN, s=-2, ell_min=2, use_advection=True)

        M = lil_matrix((self.dim, self.dim), dtype=np.complex128)
        _, off_T = self._keys_and_offsets(0, "T")
        _, off_E = self._keys_and_offsets(2, "E")
        _, off_B = self._keys_and_offsets(2, "B")
        _, off_V = self._keys_and_offsets(0, "V")

        _insert_sparse(M, off_T, off_T, D_0)
        _insert_sparse(M, off_V, off_V, D_0)

        M_EE = 0.5 * (D_p2 + D_m2) + 1j * (W_p2 - W_m2)
        M_EB = 0.5j * (D_p2 - D_m2) - (W_p2 + W_m2)
        M_BE = -0.5j * (D_p2 - D_m2) + (W_p2 + W_m2)
        M_BB = M_EE

        _insert_sparse(M, off_E, off_E, M_EE)
        _insert_sparse(M, off_E, off_B, M_EB)
        _insert_sparse(M, off_B, off_E, M_BE)
        _insert_sparse(M, off_B, off_B, M_BB)
        return M.tocsc()

    def _project_cartesian_streaming(self, axis: int) -> csc_matrix:
        """Exact GL projection of -1j * n_{axis} onto (T, E, B, V) signed harmonics."""
        return self._project_scalar_multiplier(-1j * self._grid[2][..., axis])

    def _project_scalar_multiplier(self, mul):
        """Harmonic representation of a common ray-dependent Stokes multiplier."""
        _, S_0 = self._spin_blocks(None, None, mul, s=0, ell_min=0, use_advection=False)
        _, S_p2 = self._spin_blocks(None, None, mul, s=2, ell_min=2, use_advection=False)
        _, S_m2 = self._spin_blocks(None, None, mul, s=-2, ell_min=2, use_advection=False)

        M = lil_matrix((self.dim, self.dim), dtype=np.complex128)
        _, off_T = self._keys_and_offsets(0, "T")
        _, off_E = self._keys_and_offsets(2, "E")
        _, off_B = self._keys_and_offsets(2, "B")
        _, off_V = self._keys_and_offsets(0, "V")

        _insert_sparse(M, off_T, off_T, S_0)
        _insert_sparse(M, off_V, off_V, S_0)
        M_EE = 0.5 * (S_p2 + S_m2)
        M_EB = 0.5j * (S_p2 - S_m2)
        _insert_sparse(M, off_E, off_E, M_EE)
        _insert_sparse(M, off_E, off_B, M_EB)
        _insert_sparse(M, off_B, off_E, -M_EB)
        _insert_sparse(M, off_B, off_B, M_EE)
        return M.tocsc()

    def bolometric_redshift_operator(self, geometry):
        """Projection of -4 sigma_ij n_i n_j multiplying existing brightness.

        This term evolves a^4 I or the normalized bolometric Stokes increment.
        Direction/screen-only geodesic tests can still use base_operator alone.
        """
        packed = geometry.pack_14() if isinstance(geometry, LieGeometry) else np.asarray(geometry)
        if not hasattr(self, "_bolometric_shear_basis"):
            n = self._grid[2]
            basis = []
            for row in np.eye(14)[:5]:
                shear, _, _ = LieGeometry.unpack_14(row)
                rate = -4.0 * np.einsum("...i,ij,...j->...", n, shear, n)
                basis.append(self._project_scalar_multiplier(rate))
            self._bolometric_shear_basis = tuple(basis)
        return sum((x * mat for x, mat in zip(packed[:5], self._bolometric_shear_basis)),
                   0.0 * self._I_sp)

    def _build_sparse_thomson(self) -> csc_matrix:
        """Return exact sparse rank-9 K = U diag(b) U^T - I for dense verification and source RHS."""
        K = lil_matrix((self.dim, self.dim), dtype=np.complex128)
        K.setdiag(-1.0)
        UG = (self.U_rank9 * self.thomson_gains) @ self.U_rank9.T
        nz_r, nz_c = np.where(np.abs(UG) > 1e-16)
        for r, c in zip(nz_r, nz_c):
            K[r, c] += UG[r, c]
        return K.tocsc()

    def base_operator(
        self,
        geometry: LieGeometry | np.ndarray,
        *,
        k_eff: Sequence[float] | np.ndarray = (0.0, 0.0, 0.0),
    ) -> csc_matrix:
        """Assemble sparse M_base = M_Lie(geometry) + M_stream(k_eff) in O(nnz) time."""
        g14 = geometry.pack_14() if isinstance(geometry, LieGeometry) else np.asarray(geometry, dtype=np.float64)
        if g14.shape != (14,):
            raise ValueError("geometry must be a LieGeometry or length-14 vector")
        sig, a, n = LieGeometry.unpack_14(g14)
        validate_lie_algebra(a, n)
        kv = np.asarray(k_eff, dtype=np.float64)
        if kv.shape != (3,) or not np.all(np.isfinite(kv)):
            raise ValueError("k_eff must be a finite real 3-vector")
        vals = self._coeff @ np.r_[g14, kv]
        return csc_matrix((vals, self._template.indices, self._template.indptr), shape=self._template.shape, copy=False)

    def shear_source_vector(self, sigma_N: np.ndarray, *, amplitude: float = 1.0) -> np.ndarray:
        """Project -amplitude * (n^T sigma_N n) onto T_{2m} harmonic source slots."""
        sig = np.asarray(sigma_N, dtype=np.float64)
        if sig.shape != (3, 3):
            raise ValueError("sigma_N must have shape (3, 3)")
        TH, PH, d, w = gl_sphere_grid(8)
        quad = np.einsum("...i,ij,...j->...", d, sig, d)
        out = np.zeros(self.dim, dtype=np.complex128)
        for m in range(-2, 3):
            if (2, m) in self.idx["T"]:
                coeff = complex(np.sum(w * quad * np.conj(sph_harm_y(2, m, TH, PH))))
                out[self.idx["T"][(2, m)]] = -float(amplitude) * coeff
        return out

    def dipole_source_vector(self, vec3: Sequence[float] | np.ndarray, *, channel: str = "T", amplitude: float = 1.0) -> np.ndarray:
        """Project amplitude * (n . vec3) onto ell=1 harmonic slots of channel ('T' or 'V')."""
        v = np.asarray(vec3, dtype=np.float64)
        if v.shape != (3,) or not np.all(np.isfinite(v)):
            raise ValueError("vec3 must be a finite 3-vector")
        TH, PH, d, w = gl_sphere_grid(8)
        dip = np.einsum("...i,i->...", d, v)
        out = np.zeros(self.dim, dtype=np.complex128)
        for m in (-1, 0, 1):
            if (1, m) in self.idx[channel]:
                coeff = complex(np.sum(w * dip * np.conj(sph_harm_y(1, m, TH, PH))))
                out[self.idx[channel][(1, m)]] = float(amplitude) * coeff
        return out

    def apply(
        self,
        state: np.ndarray,
        geometry: LieGeometry | np.ndarray,
        opacity_per_efold: float,
        *,
        k_eff: Sequence[float] | np.ndarray = (0.0, 0.0, 0.0),
    ) -> np.ndarray:
        """Apply continuous generator dS/du_time = M_base S + opacity * K_thomson S."""
        y = np.asarray(state, dtype=np.complex128)
        if y.shape != (self.dim,):
            raise ValueError(f"state must have shape ({self.dim},)")
        tau_r = float(opacity_per_efold)
        if not math.isfinite(tau_r) or tau_r < 0.0:
            raise ValueError("opacity_per_efold must be finite and nonnegative")
        M = self.base_operator(geometry, k_eff=k_eff)
        res = M @ y
        if tau_r > 0.0:
            res = res + tau_r * (self.U_rank9 @ (self.thomson_gains * (self.U_rank9.T @ y)) - y)
        return res

    def factor_sdirk_stage(
        self,
        M_base: csc_matrix,
        gamma_h: float,
        tau_step: float,
    ):
        """Factor (I - gamma_h M_base - s K_thomson) with s = gamma_h * tau_step >= 0.

        Uses sparse LU of A_base = (1 + s) I - gamma_h M_base combined with an exact
        cancellation-free 9x9 Woodbury/Schur capacity solve keeping the conserved
        monopole eigenvalue O(1/(1+s)) uncorrupted for all s >= 0.
        """
        s = float(gamma_h) * float(tau_step)
        if not math.isfinite(s) or s < 0.0:
            raise ValueError("stage optical depth s must be finite and nonnegative")
        gh = float(gamma_h)
        A_base = (1.0 + s) * self._I_sp - gh * M_base
        lu = splu(A_base.tocsc())
        if s == 0.0:
            def solve_collisionless(rhs: np.ndarray) -> np.ndarray:
                r = np.asarray(rhs, dtype=np.complex128)
                return lu.solve(r)
            return solve_collisionless

        # Solve A_base * W_corr = gh * M_base * U_rank9 (only 9 sparse solves)
        rhs_U = (gh * (M_base @ self.U_rank9)).astype(np.complex128)
        W_corr = np.column_stack([lu.solve(rhs_U[:, j]) for j in range(9)])
        # Exact identity: A_base^{-1} U = (U + W_corr) / (1 + s)
        # Capacitance matrix: I_9 - s/(1+s) diag(b) - s/(1+s) diag(b) (U^T W_corr)
        alpha = s / (1.0 + s)
        # Diagonal avoids cancellation when b[0] == 1: (1 + (1 - b)*s)/(1 + s)
        diag_cap = (1.0 + (1.0 - self.thomson_gains) * s) / (1.0 + s)
        C_cap = np.diag(diag_cap.astype(np.complex128)) - alpha * (
            self.thomson_gains[:, None] * (self.U_rank9.T @ W_corr)
        )
        # Scale conserved monopole row 0 before 9x9 LU so small O(1/(1+s)) pivot stays accurate
        pivot0 = C_cap[0, 0]
        if abs(pivot0) == 0.0:
            raise ArithmeticError("degenerate monopole capacitance pivot")
        C_cap[0, :] /= pivot0
        cap_lu = lu_factor(C_cap)
        UV_comb = self.U_rank9 + W_corr

        def solve(rhs: np.ndarray) -> np.ndarray:
            r = np.asarray(rhs, dtype=np.complex128)
            x0 = lu.solve(r)
            proj = self.thomson_gains * (self.U_rank9.T @ x0)
            proj[0] /= pivot0
            m = lu_solve(cap_lu, proj)
            return x0 + alpha * (UV_comb @ m)

        return solve

    def advance_cell(
        self,
        state: np.ndarray,
        delta_N: float,
        geometry: LieGeometry | np.ndarray,
        delta_tau: float,
        *,
        source_increment: np.ndarray | None = None,
        k_eff: Sequence[float] | np.ndarray = (0.0, 0.0, 0.0),
        substeps: int = 1,
        moving_collision=None,
        bolometric_redshift: bool = False,
    ) -> np.ndarray:
        """Evolve S' = M_base * rate_time * S + tau_rate * K S + src over one cell via L-stable SDIRK(2,2).

        Specifically solves on u in [0, 1]:
            dS/du = delta_N * M_base(geometry, k_eff) S + delta_tau * K_thomson S + source_increment
        where `M_base` collects H-normalized Lie advection + k_eff streaming (so k_eff = d_chi/dN * k_phys
        or H-normalized streaming parameter multiplying delta_N).
        """
        if isinstance(substeps, (bool, np.bool_)) or not isinstance(substeps, Integral) or substeps < 1:
            raise ValueError("substeps must be a positive integer")
        dN = float(delta_N)
        dtau = float(delta_tau)
        if not math.isfinite(dN) or dN < 0.0 or not math.isfinite(dtau) or dtau < 0.0:
            raise ValueError("delta_N and delta_tau must be finite and nonnegative")
        y = np.array(state, dtype=np.complex128, copy=True)
        if y.shape != (self.dim,) or not np.all(np.isfinite(y)):
            raise ValueError(f"state must be a finite length-{self.dim} array")
        if source_increment is None:
            src_step = None
        else:
            src = np.asarray(source_increment, dtype=np.complex128)
            if src.shape != (self.dim,) or not np.all(np.isfinite(src)):
                raise ValueError("source_increment must be finite and match state shape")
            src_step = src / float(substeps)

        M_base = self.base_operator(geometry, k_eff=k_eff)
        if bolometric_redshift:
            M_base = M_base + self.bolometric_redshift_operator(geometry)
        gamma = 1.0 - 1.0 / math.sqrt(2.0)
        h = 1.0 / float(substeps)
        # Factor with dN * M_base so step size in u is h and stage depth s = gamma * h * dtau
        factor = self.factor_sdirk_stage if moving_collision is None else moving_collision.factor_sdirk_stage
        solve = factor(dN * M_base, gamma * h, dtau)
        for _ in range(int(substeps)):
            if src_step is None:
                y1 = solve(y)
                y = solve(y + ((1.0 - gamma) / gamma) * (y1 - y))
            else:
                inc = gamma * src_step
                y1 = solve(y + inc)
                y = solve(y + ((1.0 - gamma) / gamma) * (y1 - y) + inc)
        if not np.all(np.isfinite(y)):
            raise FloatingPointError("GeneralLieStokesOperator produced non-finite state")
        return y
