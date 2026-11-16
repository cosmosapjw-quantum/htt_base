"""Identifiability tools: executable companions of THEOREMS.md (node R54-THM).

Nothing here reads data. Every function is a finite-dimensional check or a design-only quantity.

T5  wishart_gls_factors          exact second-moment factors of GLS with a simulated covariance
T6  rep_matrix, equivariant_response_rank, block_identification
                                 numerical dimension of the space of O(3)- or SO(3)-equivariant linear responses from a
                                 kinematic irrep to a field on the sky, and rank bookkeeping per irreducible block
T7  zero_point_gauge             rank and null space of the multi-indicator dipole design
T7  depth_law_noncentrality      design-only separability of a 1/d law from a constant law
T8  rho_ratio, history_gram, minimal_norm_history, count_sign_changes
                                 two-kernel moment problem of the shear history

Conventions: n is the unit vector from the observer to the source. O(3) acts on a polar vector by g, on an axial
vector by det(g) g and on a symmetric trace-free tensor S by g S g^T (components in STF5_BASIS); the pseudo tensor
carries an extra det(g). A scalar field transforms as f(g^-1 n), a pseudo-scalar field with an extra det(g), a
tangent vector field (proper motion) as g V(g^-1 n).
"""
from __future__ import annotations

import math
from typing import Callable, Mapping, Sequence

import numpy as np

from .r54_tensor_five_view import STF5_BASIS

SQRT6 = math.sqrt(6.0)
KIN_KINDS = ("polar", "axial", "stf2", "pseudo_stf2")
OBS_KINDS = ("scalar", "pseudoscalar", "vector")


# --------------------------------------------------------------------------- T5
def wishart_gls_factors(n: int, p: int, k: int) -> dict:
    """Exact factors of T5 for S ~ W_p(n, Sigma)/n independent of y ~ N(J theta, Sigma), V = (J^T Sigma^-1 J)^-1:
    Cov(theta_hat) = cov_factor * V and E[(J^T S^-1 J)^-1] = plugin_factor * V."""
    if not 1 <= k <= p or n - p + k - 1 <= 0:
        raise ValueError("need 1 <= k <= p and n > p - k + 1")
    cov_factor, plugin_factor = (n - 1.0) / (n - p + k - 1.0), (n - p + k) / float(n)
    return {"cov_factor": cov_factor, "plugin_factor": plugin_factor, "variance_ratio": cov_factor / plugin_factor}


# --------------------------------------------------------------------------- T6
def rep_matrix(kind: str, g: np.ndarray) -> np.ndarray:
    """Matrix of the O(3) element g on the kinematic irrep ``kind``."""
    g = np.asarray(g, float)
    if g.shape != (3, 3) or np.abs(g @ g.T - np.eye(3)).max() > 1e-9:
        raise ValueError("g must be a 3x3 orthogonal matrix")
    det = float(np.sign(np.linalg.det(g)))
    if kind == "polar":
        return g.copy()
    if kind == "axial":
        return det * g
    if kind in ("stf2", "pseudo_stf2"):
        m = np.einsum("kij,lij->kl", STF5_BASIS, np.einsum("ia,lab,jb->lij", g, STF5_BASIS, g))
        return m if kind == "stf2" else det * m
    raise ValueError(f"unknown kinematic irrep: {kind}")


def _unit(v: np.ndarray) -> np.ndarray:
    return v / np.linalg.norm(v, axis=1, keepdims=True)


def _group_element(rng: np.random.Generator, proper: bool) -> np.ndarray:
    q, r = np.linalg.qr(rng.standard_normal((3, 3)))
    q = q * np.sign(np.diag(r))[None, :]
    if (np.linalg.det(q) > 0) != proper:
        q[:, 0] = -q[:, 0]
    return q


def _monomials(points: np.ndarray, degree: int) -> np.ndarray:
    x, y, z = points.T
    return np.stack([x**i * y**j * z**(d - i - j) for d in range(degree + 1) for i in range(d + 1) for j in range(d - i + 1)], axis=1)


def equivariant_response_rank(kin: str, obs: str, parity: bool = True, degree: int = 3, seed: int = 20261116,
                              n_points: int = 40, n_group: int = 8, region: Callable[[np.ndarray], np.ndarray] | None = None,
                              rtol: float = 1e-9) -> int:
    """Dimension of the space of equivariant linear responses ``kin`` -> field of type ``obs``, counted as functions on S^2.

    Unknown: a matrix polynomial Phi(n) of degree <= ``degree`` with Phi(g n) rho_kin(g) = tau_obs(g) Phi(n) for sampled n
    and sampled group elements (rotations; with ``parity`` every second one is improper) and n.Phi(n) = 0 for vector
    fields. ``region`` optionally restricts the points on which the solutions are compared (mask independence, C6.5).
    The count does not use Schur's lemma, so it is an independent check of the selection rule T6.
    """
    if kin not in KIN_KINDS or obs not in OBS_KINDS:
        raise ValueError("unknown kinematic irrep or observable type")
    rng = np.random.default_rng(seed)
    dk, df = (3 if kin in ("polar", "axial") else 5), (3 if obs == "vector" else 1)
    pts = _unit(rng.standard_normal((n_points, 3)))
    mono = _monomials(pts, degree)
    n_unknown = mono.shape[1] * df * dk
    blocks = []
    for index in range(n_group):
        g = _group_element(rng, proper=not (parity and index % 2 == 1))
        det = float(np.sign(np.linalg.det(g)))
        tau = g if obs == "vector" else np.array([[det if obs == "pseudoscalar" else 1.0]])
        lhs = np.einsum("pa,fF,Dd->pfdaFD", _monomials(pts @ g.T, degree), np.eye(df), rep_matrix(kin, g))
        rhs = np.einsum("pa,fF,dD->pfdaFD", mono, tau, np.eye(dk))
        blocks.append((lhs - rhs).reshape(-1, n_unknown))
    if obs == "vector":                                           # tangency n.Phi(n) = 0
        blocks.append(np.einsum("pF,pa,dD->pdaFD", pts, mono, np.eye(dk)).reshape(-1, n_unknown))
    system = np.vstack(blocks)
    if system.shape[0] < n_unknown:
        raise ValueError("too few sampled constraints for the polynomial ansatz")
    _, s, vt = np.linalg.svd(system, full_matrices=False)          # rows >= unknowns, so vt spans the whole coefficient space
    null = vt[int(np.sum(s > rtol * s[0])):]
    if null.shape[0] == 0:
        return 0
    probe = _unit(rng.standard_normal((400, 3)))
    if region is not None:
        probe = probe[np.asarray(region(probe), bool)]
        if probe.shape[0] < 30:
            raise ValueError("the region keeps too few probe directions")
    values = np.einsum("pa,cafd->cpfd", _monomials(probe, degree), null.reshape(-1, mono.shape[1], df, dk)).reshape(null.shape[0], -1)
    sv = np.linalg.svd(values, compute_uv=False)
    return int(np.sum(sv > rtol * max(sv[0], 1.0)))


def block_identification(blocks: Mapping[tuple[int, str], np.ndarray], rtol: float = 1e-10) -> dict:
    """Rank bookkeeping of T6. ``blocks[(ell, parity)]`` is the multiplicity matrix M (observable slots x kinematic
    copies) of the irreducible block; the unidentified subspace has dimension sum (2 ell + 1) nullity(M)."""
    out, total = {}, 0
    for (ell, parity), matrix in blocks.items():
        m = np.asarray(matrix, float)
        if m.ndim != 2 or parity not in ("+", "-") or ell < 0:
            raise ValueError("each block needs a 2-D multiplicity matrix and a parity '+' or '-'")
        s = np.linalg.svd(m, compute_uv=False) if m.size else np.zeros(0)
        rank = int(np.sum(s > rtol * s[0])) if s.size and s[0] > 0 else 0
        nullity = m.shape[1] - rank
        out[f"{ell}{parity}"] = {"slots": int(m.shape[0]), "copies": int(m.shape[1]), "rank": rank, "nullity": nullity,
                                 "unidentified_dimension": (2 * ell + 1) * nullity}
        total += (2 * ell + 1) * nullity
    return {"blocks": out, "unidentified_dimension": total, "identified": total == 0}


# --------------------------------------------------------------------------- T7
def zero_point_gauge(directions: Sequence[np.ndarray], responses: Sequence[np.ndarray] | None = None, rtol: float = 1e-10) -> dict:
    """Dipole design of K distance-indicator samples: mean_i = (delta + d_p).n_i [+ g_i V.n_i] for object i of sample p.

    Parameter order: delta (3), d_1 .. d_K (3 each), then V (3) when ``responses`` (one array g per sample) is given.
    Returns the rank, the nullity and an orthonormal basis of the null space (the gauge orbit of T7a)."""
    k = len(directions)
    if k == 0 or (responses is not None and len(responses) != k):
        raise ValueError("need at least one sample and one response array per sample")
    n_par = 3 * (k + 1) + (3 if responses is not None else 0)
    rows = []
    for p, nhat in enumerate(directions):
        nhat = np.asarray(nhat, float)
        if nhat.ndim != 2 or nhat.shape[1] != 3:
            raise ValueError("directions must be (N, 3) arrays")
        block = np.zeros((nhat.shape[0], n_par))
        block[:, 0:3] = nhat
        block[:, 3 * (p + 1):3 * (p + 2)] = nhat
        if responses is not None:
            block[:, -3:] = np.asarray(responses[p], float)[:, None] * nhat
        rows.append(block)
    design = np.vstack(rows)
    _, s, vt = np.linalg.svd(design, full_matrices=True)
    rank = int(np.sum(s > rtol * s[0]))
    return {"n_parameters": n_par, "rank": rank, "nullity": n_par - rank, "null_basis": vt[rank:], "design": design}


def depth_law_noncentrality(g: np.ndarray, cov: np.ndarray) -> dict:
    """Testing V = 0 in y_w = A + g_w V + noise (w = 1..K, 3-vectors stacked depth-major) with A free.

    Returns the 3x3 matrix Lambda with noncentrality lambda = V^T Lambda V. For ``cov`` = c (K x K, same law per
    Cartesian component) also the scalar g^T c^-1 g sin^2(angle) and sin^2 of the angle between the two laws in the
    c^-1 metric; the laws are separable iff that angle is non-zero, i.e. iff g is not constant."""
    g = np.asarray(g, float)
    k, cov = g.size, np.asarray(cov, float)
    if cov.shape == (k, k):
        full = np.kron(cov, np.eye(3))
    elif cov.shape == (3 * k, 3 * k):
        full = cov
    else:
        raise ValueError("cov must be (K, K) or (3K, 3K)")
    xa, xv = np.kron(np.ones((k, 1)), np.eye(3)), np.kron(g[:, None], np.eye(3))
    ci = np.linalg.inv(full)
    gaa, gav, gvv = xa.T @ ci @ xa, xa.T @ ci @ xv, xv.T @ ci @ xv
    lam = gvv - gav.T @ np.linalg.solve(gaa, gav)
    out = {"Lambda": 0.5 * (lam + lam.T)}
    if cov.shape == (k, k):
        cinv, one = np.linalg.inv(cov), np.ones(k)
        gg, g1, oo = float(g @ cinv @ g), float(g @ cinv @ one), float(one @ cinv @ one)
        out.update({"scalar": gg - g1 * g1 / oo, "sin2_angle": 1.0 - g1 * g1 / (gg * oo)})
    return out


# --------------------------------------------------------------------------- T8
def rho_ratio(tau: np.ndarray | float) -> np.ndarray:
    """K_E/K_T = sqrt6 (x - 1)/(x + 6) with x = exp(7 tau/10): strictly increasing from 0 towards sqrt6 (T8-i)."""
    x = np.exp(0.7 * np.asarray(tau, float))
    return SQRT6 * (x - 1.0) / (x + 6.0)


def history_gram(kt: np.ndarray, ke: np.ndarray, weights: np.ndarray) -> np.ndarray:
    """Gram matrix of (K_T, K_E) in L2 with quadrature ``weights`` (positive, in N = ln a)."""
    kernels = np.vstack([np.asarray(kt, float), np.asarray(ke, float)])
    w = np.asarray(weights, float)
    if kernels.shape[1] != w.size or (w <= 0).any():
        raise ValueError("weights must be positive and match the kernels")
    return (kernels * w) @ kernels.T


def minimal_norm_history(kt: np.ndarray, ke: np.ndarray, weights: np.ndarray, sigma: Sequence[float]) -> dict:
    """Least-L2 history with prescribed (Sigma_T, Sigma_E): s* = c_T K_T + c_E K_E, c = G^-1 Sigma, norm^2 = Sigma^T G^-1 Sigma (T8-iv)."""
    gram, target = history_gram(kt, ke, weights), np.asarray(sigma, float)
    if np.linalg.cond(gram) > 1e14:
        raise ValueError("the kernels are linearly dependent on this support: only one functional is measured")
    coef = np.linalg.solve(gram, target)
    return {"history": coef[0] * np.asarray(kt, float) + coef[1] * np.asarray(ke, float), "norm": float(math.sqrt(target @ coef)),
            "coefficients": coef, "gram": gram}


def count_sign_changes(values: np.ndarray, atol: float = 0.0) -> int:
    """Number of sign changes of a sampled function, zeros (|v| <= atol) ignored."""
    v = np.asarray(values, float)
    v = v[np.abs(v) > atol]
    return int(np.sum(v[1:] * v[:-1] < 0.0))
