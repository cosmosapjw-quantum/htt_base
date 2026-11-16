"""R52 joint linear identification of tilt/boost/shear/acceleration responses.

theta (17, common Galactic triad, first order):
  s_sig[0:5]  sigma_ab/H0 today, orthonormal STF5 (matter congruence, z=0)
  omega[5:8]  omega_a/H0 today
  A[8:11]     matter 4-acceleration A_a/(c H0), z=0
  bRM[11:14]  radiation relative to matter velocity / c at z=0 (local radiation frame)
  bMO[14:17]  observer (SSB) relative to matter / c, z=0

Each probe is a linear-Gaussian block y = J theta + N eta + e, e ~ N(0, C), with
explicit nuisance columns N (profiled with a flat measure). Responses are the
R51 SOURCE_BOUND / CONDITIONAL operators; no working-model coefficient enters.
The likelihood rank and null space are recorded before any proper prior.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
from scipy import integrate

from htt.htt.infer.r51_source_bound_response import _cholesky_spd

THETA_NAMES = (
    [f"sigma_over_H0_e{k}" for k in range(5)]
    + [f"omega_over_H0_{c}" for c in "xyz"]
    + [f"A_over_cH0_{c}" for c in "xyz"]
    + [f"beta_RM0_{c}" for c in "xyz"]
    + [f"beta_MO_{c}" for c in "xyz"]
)
SL = {"sigma": slice(0, 5), "omega": slice(5, 8), "A": slice(8, 11), "bRM": slice(11, 14), "bMO": slice(14, 17)}
C_KM_S = 299792.458
MPC_KM = 3.0856775814913673e19
UAS_PER_RAD = 180.0 / math.pi * 3600.0e6
JULIAN_YEAR_S = 365.25 * 86400.0

s2, s6 = 1 / math.sqrt(2), 1 / math.sqrt(6)
STF_BASIS = np.array([
    [[s2, 0, 0], [0, -s2, 0], [0, 0, 0]],
    [[s6, 0, 0], [0, s6, 0], [0, 0, -2 * s6]],
    [[0, s2, 0], [s2, 0, 0], [0, 0, 0]],
    [[0, 0, s2], [0, 0, 0], [s2, 0, 0]],
    [[0, 0, 0], [0, 0, s2], [0, s2, 0]],
])


def stf5_rotation(R: np.ndarray) -> np.ndarray:
    """M with s' = M s for the tensor T -> R T R^T in the orthonormal STF5 basis."""
    R = np.asarray(R, float)
    return np.array([[np.trace(STF_BASIS[a] @ R @ STF_BASIS[b] @ R.T) for b in range(5)] for a in range(5)])


def h0_uas_per_year(h0_km_s_mpc: float) -> float:
    return h0_km_s_mpc / MPC_KM * UAS_PER_RAD * JULIAN_YEAR_S


def _E(a: float, om: float, orad: float, ol: float) -> float:
    return math.sqrt(orad * a**-4 + om * a**-3 + ol)


def endpoint_history_factor(z: float, om: float, orad: float, ol: float) -> float:
    """K(z) = 2 J(z)/chi(z) - 1 for A_PM = 2c(B_o-B_s)/D - dot B_o under sigma a^3 = const.

    J = H0 int sigma/sigma0 dt = int_{a_s}^1 a^-4/E da, chi = H0 D/c = int_{a_s}^1 da/(a^2 E).
    Small-z limit K -> 1 (mu ~ P sigma_o n, R36-03 nearby limit). CONDITIONAL on the
    Bianchi-I no-anisotropic-stress history and comoving sources.
    """
    a_s = 1.0 / (1.0 + z)
    J = integrate.quad(lambda a: a**-4 / _E(a, om, orad, ol), a_s, 1.0, epsrel=1e-11, epsabs=0.0)[0]
    chi = integrate.quad(lambda a: 1.0 / (a * a * _E(a, om, orad, ol)), a_s, 1.0, epsrel=1e-11, epsabs=0.0)[0]
    return 2.0 * J / chi - 1.0


@dataclass
class LinearProbe:
    name: str
    y: np.ndarray
    C: np.ndarray
    J: np.ndarray                      # (n, 17)
    N: np.ndarray | None = None        # (n, k) flat-measure nuisance
    block_id: str = ""
    frame: str = ""
    notes: dict = field(default_factory=dict)

    def __post_init__(self):
        self.y = np.asarray(self.y, float)
        self.C = np.asarray(self.C, float)
        self.J = np.asarray(self.J, float)
        n = self.y.size
        if self.C.shape != (n, n) or self.J.shape != (n, 17):
            raise ValueError(f"{self.name}: shape mismatch")
        if self.N is None:
            self.N = np.zeros((n, 0))
        self.N = np.asarray(self.N, float)


def profiled_carrier(p: LinearProbe) -> dict:
    """Nuisance-profiled (F, t, Q0, dof) of one probe; exact Gaussian algebra."""
    L = _cholesky_spd(p.C, p.name)
    Jw, yw, Nw = (np.linalg.solve(L, a) for a in (p.J, p.y, p.N))
    if Nw.shape[1]:
        Q, R = np.linalg.qr(Nw)
        if np.min(np.abs(np.diag(R))) < 1e-12 * np.max(np.abs(np.diag(R))):
            raise ValueError(f"{p.name}: nuisance design rank deficient")
        Jw = Jw - Q @ (Q.T @ Jw)
        yw = yw - Q @ (Q.T @ yw)
    Jraw = np.linalg.solve(L, p.J)
    F = Jw.T @ Jw
    return {"F": 0.5 * (F + F.T), "t": Jw.T @ yw, "Q0": float(yw @ yw), "dof": int(p.y.size - p.N.shape[1]),
            "F_unprofiled": Jraw.T @ Jraw}


def identification(F: np.ndarray, rel_tol: float = 1e-10) -> dict:
    """Rank/eigenvectors of the correlation-normalized Fisher (blocks differ by ~1e9 in scale).

    Parameters with zero Fisher diagonal are exact null directions. Eigenvectors are
    returned in the normalized basis u_k = sqrt(F_kk) theta_k (zero for null parameters).
    """
    F = 0.5 * (F + F.T)
    dg = np.diag(F).copy()
    live = dg > 0
    D = np.zeros_like(dg)
    D[live] = 1.0 / np.sqrt(dg[live])
    F = F * D[:, None] * D[None, :]
    w, V = np.linalg.eigh(F)
    order = np.argsort(w)[::-1]
    w, V = w[order], V[:, order]
    thr = rel_tol * max(w[0], 1e-300)
    rank = int(np.sum(w > thr))
    return {"eigenvalues": w, "eigenvectors": V, "rank": rank, "null_space": V[:, rank:]}


def block_ranks(F: np.ndarray, F_ref: np.ndarray | None = None, rel_tol: float = 1e-8) -> dict:
    """Rank of the (profiled) Fisher on each theta block.

    Threshold is relative to the largest eigenvalue of the same block of F_ref
    (the unprofiled information), so information removed by nuisance profiling is
    not counted as identified.
    """
    ref = F if F_ref is None else F_ref
    out = {}
    for k, s in SL.items():
        w = np.linalg.eigvalsh(0.5 * (F[s, s] + F[s, s].T))
        wr = np.linalg.eigvalsh(0.5 * (ref[s, s] + ref[s, s].T))
        out[k] = int(np.sum(w > rel_tol * wr.max())) if wr.max() > 0 else 0
    return out


def gaussian_posterior(F: np.ndarray, t: np.ndarray, prior_sd: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    P = F + np.diag(1.0 / np.asarray(prior_sd, float) ** 2)
    d = np.sqrt(np.diag(P))
    Ps = P / d[:, None] / d[None, :]
    L = _cholesky_spd(0.5 * (Ps + Ps.T), "posterior precision")
    cov_s = np.linalg.solve(L.T, np.linalg.solve(L, np.eye(len(t))))
    cov = cov_s / d[:, None] / d[None, :]
    return cov @ t, 0.5 * (cov + cov.T)


def joint(probes: list[LinearProbe]) -> dict:
    ids = [p.block_id for p in probes]
    if any(not i for i in ids) or len(set(ids)) != len(ids):
        raise ValueError(f"unique non-empty block ids required: {ids}")
    cars = {p.name: profiled_carrier(p) for p in probes}
    F = sum(c["F"] for c in cars.values())
    t = sum(c["t"] for c in cars.values())
    Fu = sum(c["F_unprofiled"] for c in cars.values())
    return {"carriers": cars, "F": F, "t": t, "F_unprofiled": Fu}


def chi2_at(p: LinearProbe, theta: np.ndarray) -> tuple[float, int]:
    c = profiled_carrier(p)
    return float(c["Q0"] - 2 * theta @ c["t"] + theta @ c["F"] @ theta), c["dof"]


# -----------------------------------------------------------------------------
# Frame-composition designs (first order). Velocities of frames in a common frame:
#   beta_RM = v_R - v_M (radiation rel. matter), beta_MO = v_O - v_M (observer rel. matter).
#   CMB dipole (observer rel. radiation)   = v_O - v_R = beta_MO - beta_RM
#   count dipole (observer rel. sources=M) = c_EB (v_O - v_M) = c_EB beta_MO
#   CF4 source bulk in z_CMB frame         = c (v_M - v_R) = -c beta_RM
# -----------------------------------------------------------------------------


def cmb_dipole_design() -> np.ndarray:
    J = np.zeros((3, 17))
    J[:, SL["bMO"]] = np.eye(3)
    J[:, SL["bRM"]] = -np.eye(3)
    return J


def count_dipole_design(c_eb: float, R_gal_to_probe: np.ndarray) -> np.ndarray:
    J = np.zeros((3, 17))
    J[:, SL["bMO"]] = c_eb * np.asarray(R_gal_to_probe, float)
    return J


def cf4_h03_design(AN: np.ndarray, h0_ref: float, R_gal_to_probe: np.ndarray) -> np.ndarray:
    """36 x 17 response of the R36 H03 coordinates (4 windows x [H, dipole3, STF5]).

    Anisotropic expansion H_n = H(1) + delta H_n with delta H_n = -n.a + sigma_nn (Heinesen 2021,
    n toward source); delta H is absolute, so in units of the declared reference H0:
    dipole rows -h0_ref A~, STF rows h0_ref sigma~. Source bulk V_s = -c beta_RM through AN.
    """
    R = np.asarray(R_gal_to_probe, float)
    M5 = stf5_rotation(R)
    J = np.zeros((36, 17))
    for w in range(4):
        J[9 * w + 1:9 * w + 4, SL["A"]] = -h0_ref * R
        J[9 * w + 4:9 * w + 9, SL["sigma"]] = h0_ref * M5
    J[:, SL["bRM"]] = np.asarray(AN, float) @ (-C_KM_S * R)
    return J


def effective_dof(p: "LinearProbe", post_cov: np.ndarray) -> float:
    """n - n_nuisance - tr(F_p Sigma_post): data dof left after the joint fit (hat-matrix trace)."""
    c = profiled_carrier(p)
    return float(p.y.size - p.N.shape[1] - np.trace(c["F"] @ post_cov))
