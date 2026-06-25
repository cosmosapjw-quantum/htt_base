"""PAPER-A proof-closure helpers (PR07-004).

Independent matrix/kinematic fixtures backing the PAPER-A theorems whose
corollaries were previously held at ``BLOCKED_PROOF_REVIEW``:

* duplicate response block adds zero identifiable rank, with the null-space
  equality qualified by *full column rank*;
* radial-vorticity no-go ``n^a Omega_ab n^b = 0``;
* single-shell dipole degeneracy (rank 3) vs broad-depth recovery (rank 6);
* temporal STF tensor rank ``rank(T (x) I_5) = 5 rank(T)``;
* exact Lorentz boost composition / non-Euclidean velocity addition, kept
  *separate* from the first-jet no-go (no Wigner-rotation angle is claimed).

These are diagnostic theorem fixtures; they assert no observational detection.
"""
from __future__ import annotations

import numpy as np


def numerical_rank(matrix: np.ndarray, *, rtol: float = 1e-11, atol: float = 1e-12) -> int:
    m = np.asarray(matrix, dtype=float)
    s = np.linalg.svd(m, compute_uv=False)
    if s.size == 0:
        return 0
    threshold = max(float(atol), float(rtol) * float(s[0]))
    return int(np.sum(s > threshold))


def duplicate_block_audit(A: np.ndarray, *, rtol: float = 1e-11) -> dict[str, object]:
    """Check rank([A A])=rank(A) and characterize its null space.

    The null space always contains vectors ``(x,-x)``. It equals that subspace
    only when ``A`` has full column rank.
    """
    a = np.asarray(A, dtype=float)
    doubled = np.concatenate([a, a], axis=1)
    u, s, vh = np.linalg.svd(doubled, full_matrices=True)
    rank_a = numerical_rank(a, rtol=rtol)
    rank_d = numerical_rank(doubled, rtol=rtol)
    null = vh[rank_d:].T
    p = a.shape[1]
    test = np.concatenate([np.eye(p), -np.eye(p)], axis=0)
    residual = np.linalg.norm(doubled @ test)
    return {
        "rank_A": rank_a,
        "rank_AA": rank_d,
        "nullity_AA": int(doubled.shape[1] - rank_d),
        "x_minus_x_residual": float(residual),
        "nullspace_equals_x_minus_x": bool(rank_a == p and doubled.shape[1] - rank_d == p),
        "nullspace_basis": null.tolist(),
    }


def radial_vorticity_response(directions: np.ndarray, radii: np.ndarray) -> np.ndarray:
    """Return the radial response to the three antisymmetric affine modes.

    For ``r=d n`` and antisymmetric ``Omega``, ``n^T Omega r=0`` exactly.
    Columns correspond to rotations about x,y,z.
    """
    n = np.asarray(directions, dtype=float)
    d = np.asarray(radii, dtype=float).reshape(-1)
    if n.shape != (d.size, 3):
        raise ValueError("directions must have shape (N,3)")
    norms = np.linalg.norm(n, axis=1)
    if np.any(norms == 0.0):
        raise ValueError("directions must be nonzero")
    n = n / norms[:, None]
    r = d[:, None] * n
    generators = np.array(
        [
            [[0, 0, 0], [0, 0, -1], [0, 1, 0]],
            [[0, 0, 1], [0, 0, 0], [-1, 0, 0]],
            [[0, -1, 0], [1, 0, 0], [0, 0, 0]],
        ],
        dtype=float,
    )
    return np.column_stack([np.einsum("ni,ij,nj->n", n, g, r) for g in generators])


def single_shell_dipole_design(directions: np.ndarray, depth: np.ndarray) -> np.ndarray:
    """Joint acceleration-like and coherent-bulk dipole design.

    The acceleration-like block is ``n_i``. A coherent bulk enters as
    ``n_i/depth`` in the low-z log-distance linearization. On one exact shell
    the two blocks are proportional and the six-column design has rank three.
    """
    n = np.asarray(directions, dtype=float)
    z = np.asarray(depth, dtype=float).reshape(-1)
    n = n / np.linalg.norm(n, axis=1)[:, None]
    if np.any(z <= 0.0):
        raise ValueError("depth must be positive")
    return np.concatenate([n, n / z[:, None]], axis=1)


def temporal_tensor_design(temporal_kernel: np.ndarray) -> np.ndarray:
    """Return ``T kron I_5`` for STF tensor histories."""
    t = np.asarray(temporal_kernel, dtype=float)
    if t.ndim != 2:
        raise ValueError("temporal_kernel must be 2D")
    return np.kron(t, np.eye(5))


def lorentz_boost(beta: np.ndarray) -> np.ndarray:
    """Return a proper orthochronous boost for signature (-,+,+,+)."""
    b = np.asarray(beta, dtype=float).reshape(3)
    b2 = float(b @ b)
    if b2 >= 1.0:
        raise ValueError("|beta| must be <1")
    if b2 == 0.0:
        return np.eye(4)
    gamma = 1.0 / np.sqrt(1.0 - b2)
    spatial = np.eye(3) + (gamma - 1.0) * np.outer(b, b) / b2
    out = np.empty((4, 4), dtype=float)
    out[0, 0] = gamma
    out[0, 1:] = gamma * b
    out[1:, 0] = gamma * b
    out[1:, 1:] = spatial
    return out


def composed_velocity(L: np.ndarray) -> np.ndarray:
    """Velocity of the transformed rest four-vector under ``L``."""
    mat = np.asarray(L, dtype=float).reshape(4, 4)
    return mat[1:, 0] / mat[0, 0]


def boost_composition_audit(beta1: np.ndarray, beta2: np.ndarray) -> dict[str, object]:
    """Exact Lorentz composition + non-Euclidean velocity addition.

    This is *not* a Wigner-rotation theorem: no decomposition into a net boost
    and spatial rotation, and no rotation angle, is claimed here.
    """
    eta = np.diag([-1.0, 1.0, 1.0, 1.0])
    L = lorentz_boost(beta1) @ lorentz_boost(beta2)
    v = composed_velocity(L)
    return {
        "lorentz_error": float(np.max(np.abs(L.T @ eta @ L - eta))),
        "composed_velocity": v.tolist(),
        "euclidean_sum": (np.asarray(beta1) + np.asarray(beta2)).tolist(),
        "nonadditivity_norm": float(np.linalg.norm(v - np.asarray(beta1) - np.asarray(beta2))),
    }


def first_jet_counterexample(alpha: float = 0.2) -> dict[str, object]:
    """Two normalized congruences agree at a point but have different expansion.

    In Minkowski coordinates, field 1 is constant. Field 2 has local velocity
    ``v_x=alpha*x`` and ``u=gamma(1,v_x,0,0)``. At x=0 both equal
    ``(1,0,0,0)``, but the second field has divergence ``alpha`` there. Hence
    pointwise four-velocity does not determine the first jet (congruence
    kinematics).
    """
    return {
        "pointwise_u_field_1": [1.0, 0.0, 0.0, 0.0],
        "pointwise_u_field_2": [1.0, 0.0, 0.0, 0.0],
        "theta_field_1_at_origin": 0.0,
        "theta_field_2_at_origin": float(alpha),
        "same_pointwise_velocity": True,
        "different_first_jet": bool(alpha != 0.0),
    }
