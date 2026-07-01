"""Feasible correlated peculiar-velocity covariance at CF4 scale (Woodbury).

A dense N x N peculiar-velocity covariance is infeasible for the ~38k CF4 groups
(N^2 ~ 1.4e9, O(N^3) inversion). The velocity field at CF4 depth is dominated by a
few large-scale coherent modes, so the covariance is well modelled as

    C_PV = diag(sigma_v^2)  +  U Lambda U^T ,   U in R^{N x K},  K << N,

a diagonal per-group measurement term plus a low-rank coherent-field term. This is
exactly the audited Woodbury form already used by `bulkflow_mle._hier_covariance`
(`diag + Z T Z^T`); here the low-rank block is built from the leading large-scale
VELOCITY MODES (bulk + shear moments, the analytic leading correlation), so the
off-diagonal spatial velocity-velocity correlation `xi_ij` enters WITHOUT a fabricated
velocity power spectrum and WITHOUT an N x N inversion.

Inversion is Sherman-Morrison-Woodbury, O(N K^2):

    C^{-1} = D^{-1} - D^{-1} U (Lambda^{-1} + U^T D^{-1} U)^{-1} U^T D^{-1} ,
    log|C| = log|D| + log|Lambda| + log|Lambda^{-1} + U^T D^{-1} U|   (matrix determinant lemma),

reusing `scipy.linalg.cho_factor`/`cho_solve` on the K x K capacitance.

Diagnostic-only, model-independent kinematics: the bulk-flow / tilt (`Omega_tilt`)
amplitude and precision are model-independent descriptors; no Bianchi family,
geometry, frame-violation, or native-solver claim. A full `xi_ij` from a real
velocity power spectrum / WF-field ensemble is `BLOCKED_MISSING_FIELD_REALIZATIONS`;
the leading bulk+shear mode basis here is the honest, in-scope feasible form.
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np
from scipy.linalg import cho_factor, cho_solve

__all__ = [
    "traceless_symmetric_basis",
    "velocity_field_modes",
    "woodbury_solve",
    "woodbury_logdet",
    "TiltFit",
    "pv_tilt_gls",
    "omega_tilt_precision",
]


def traceless_symmetric_basis() -> np.ndarray:
    """The 5 orthonormal (Frobenius) traceless-symmetric 3x3 basis matrices E_a."""
    s = 1.0 / np.sqrt(2.0)
    E = np.zeros((5, 3, 3))
    # off-diagonal shears (symmetric)
    E[0, 0, 1] = E[0, 1, 0] = s     # xy
    E[1, 0, 2] = E[1, 2, 0] = s     # xz
    E[2, 1, 2] = E[2, 2, 1] = s     # yz
    # diagonal traceless combinations
    E[3, 0, 0], E[3, 1, 1] = s, -s                       # (xx - yy)/sqrt(2)
    d = 1.0 / np.sqrt(6.0)
    E[4, 0, 0], E[4, 1, 1], E[4, 2, 2] = d, d, -2.0 * d  # (xx + yy - 2zz)/sqrt(6)
    return E


def velocity_field_modes(positions: np.ndarray, *, sigma_bulk_kms: float = 150.0,
                         sigma_shear_kms_per_mpc: float = 1.5) -> dict:
    """Leading large-scale velocity modes (bulk + shear) sampled at galaxy positions.

    Returns the design `U` (N, 8) whose columns are the radial-velocity response to
    the 3 bulk-flow and 5 traceless-shear moments, and the prior variances `Lambda`
    (8,) of those moments. `U Lambda U^T` is the coherent-field (off-diagonal)
    velocity covariance; positions are in Mpc (supergalactic Cartesian).

    kinds: ("bulk","bulk","bulk","shear","shear","shear","shear","shear").
    """
    pos = np.asarray(positions, dtype=float)
    r = np.linalg.norm(pos, axis=1)
    n_hat = pos / np.where(r[:, None] > 0.0, r[:, None], 1.0)
    N = pos.shape[0]
    E = traceless_symmetric_basis()
    U = np.empty((N, 8))
    U[:, :3] = n_hat                                        # bulk: v_r = n . B
    for a in range(5):                                     # shear: v_r = n^T (E_a) x
        U[:, 3 + a] = np.einsum("ij,ai,aj->a", E[a], n_hat, pos)
    lam = np.empty(8)
    lam[:3] = sigma_bulk_kms ** 2
    lam[3:] = sigma_shear_kms_per_mpc ** 2
    kinds = ("bulk",) * 3 + ("shear",) * 5
    return {"U": U, "Lambda": lam, "kinds": kinds, "n_hat": n_hat, "r": r}


def _capacitance(diag: np.ndarray, U: np.ndarray, Lambda: np.ndarray):
    d = np.asarray(diag, dtype=float).reshape(-1)
    U = np.asarray(U, dtype=float)
    lam = np.asarray(Lambda, dtype=float).reshape(-1)
    Dinv_U = U / d[:, None]                                 # D^{-1} U  (N, K)
    M = np.diag(1.0 / lam) + U.T @ Dinv_U                  # Lambda^{-1} + U^T D^{-1} U
    return d, Dinv_U, lam, cho_factor(M, lower=True, check_finite=True)


def woodbury_solve(diag: np.ndarray, U: np.ndarray, Lambda: np.ndarray,
                   rhs: np.ndarray) -> np.ndarray:
    """(D + U Lambda U^T)^{-1} rhs via Sherman-Morrison-Woodbury, O(N K^2)."""
    d, Dinv_U, lam, cf = _capacitance(diag, U, Lambda)
    b = np.asarray(rhs, dtype=float)
    Dinv_b = b / d[:, None] if b.ndim == 2 else b / d
    UtDinv_b = U.T @ Dinv_b
    corr = Dinv_U @ cho_solve(cf, UtDinv_b)
    return Dinv_b - corr


def woodbury_logdet(diag: np.ndarray, U: np.ndarray, Lambda: np.ndarray) -> float:
    """log|D + U Lambda U^T| via the matrix determinant lemma."""
    d, _, lam, cf = _capacitance(diag, U, Lambda)
    logdet_D = float(np.sum(np.log(d)))
    logdet_Lambda = float(np.sum(np.log(lam)))
    logdet_M = 2.0 * float(np.sum(np.log(np.diag(cf[0]))))
    return logdet_D + logdet_Lambda + logdet_M


@dataclass(frozen=True)
class TiltFit:
    vector: np.ndarray        # bulk/tilt B (km/s), 3-vector
    covariance: np.ndarray    # 3x3 Cov(B) (km/s)^2, correlated-covariance GLS
    amplitude: float          # |B| (km/s)
    amplitude_error: float    # 1-sigma on |B|
    n_groups: int
    n_modes: int              # rank of the coherent-field block

    def as_dict(self) -> dict:
        return {"vector_kms": self.vector.tolist(), "covariance": self.covariance.tolist(),
                "amplitude_kms": self.amplitude, "amplitude_error_kms": self.amplitude_error,
                "n_groups": self.n_groups, "n_modes": self.n_modes}


def pv_tilt_gls(n_hat: np.ndarray, vpec: np.ndarray, diag_sigma2: np.ndarray,
                U: np.ndarray | None = None, Lambda: np.ndarray | None = None) -> TiltFit:
    """Correlated-covariance bulk-flow / tilt GLS on the low-rank Woodbury covariance.

    A = N^T C^{-1} N (3x3), b = N^T C^{-1} v, B = A^{-1} b, Cov(B) = A^{-1}, with
    C = diag(diag_sigma2) + U Lambda U^T applied via `woodbury_solve` (feasible at
    CF4 scale). If U is None this reduces to the diagonal weighted-GLS estimator."""
    n = np.asarray(n_hat, dtype=float)
    v = np.asarray(vpec, dtype=float)
    d = np.asarray(diag_sigma2, dtype=float).reshape(-1)
    if U is None or Lambda is None:
        Cinv_n = n / d[:, None]
        Cinv_v = v / d
        n_modes = 0
    else:
        Cinv_n = woodbury_solve(d, U, Lambda, n)           # (N,3)
        Cinv_v = woodbury_solve(d, U, Lambda, v)           # (N,)
        n_modes = int(np.asarray(U).shape[1])
    A = n.T @ Cinv_n
    b = n.T @ Cinv_v
    cov = np.linalg.inv(A)
    B = cov @ b
    amp = float(np.linalg.norm(B))
    if amp > 0.0:
        u = B / amp
        amp_err = float(np.sqrt(u @ cov @ u))
    else:
        amp_err = float(np.sqrt(np.trace(cov) / 3.0))
    return TiltFit(B, cov, amp, amp_err, int(n.shape[0]), n_modes)


def omega_tilt_precision(cov3: np.ndarray) -> float:
    """Scalar Omega_tilt (bulk-amplitude) precision proxy = 3 / tr(Cov). Higher is
    tighter; used as the `f_omega_tilt` Fisher diagonal fed to the coupled Fisher."""
    tr = float(np.trace(np.asarray(cov3, dtype=float)))
    return 3.0 / tr if tr > 0.0 else np.inf
