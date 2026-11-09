"""Geometry-only Bianchi type and tilted-state similarity diagnostics.

Consumes the Ellis--MacCallum (a,n) split and the orthonormal-frame
structure tensor C^k_ij. Deliberately independent of Boltzmann, LOS,
likelihood and sampler modules.

C[k,i,j] represents [e_i,e_j] = C[k,i,j] e_k in a right-handed
orthonormal invariant triad. Similarity quotients use SO(3) and one
common positive homothety; parity-reflected tilt orbits remain distinct.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import numpy as np

__all__ = [
    "BianchiTypeSignature", "GeometryFingerprint", "TiltOrbitFingerprint",
    "classify_bianchi_type", "structure_tensor_from_an",
    "spatial_ricci_from_structure_tensor", "geometry_fingerprint",
    "tilt_orbit_fingerprint", "recover_tilt_squared_components",
]

@dataclass(frozen=True)
class BianchiTypeSignature:
    label: str
    class_label: str
    rank_n: int
    inertia_n: tuple[int, int, int]
    h_parameter: Optional[float]

@dataclass(frozen=True)
class GeometryFingerprint:
    type_signature: BianchiTypeSignature
    normalized_a_norm: float
    normalized_n_eigenvalues: tuple[float, float, float]
    normalized_ricci_eigenvalues: tuple[float, float, float]
    scalar_curvature_sign: int
    flat_intrinsic_geometry: bool
    isotropic_intrinsic_curvature: bool
    structure_scale_kappa: float

@dataclass(frozen=True)
class TiltOrbitFingerprint:
    speed_squared: float
    p1: float
    p2: float
    class_b_a_dot_v: Optional[float]
    class_b_a_dot_v_cross_nv: Optional[float]
    class_a_v_nv_n2v_determinant: Optional[float]
    moment_rank: int
    moment_jacobian_rank: int
    moment_condition_number: float
    continuous_azimuth_degeneracy_dof: int
    orientation_quotient: str

def _as_vector3(x: np.ndarray, name: str) -> np.ndarray:
    arr = np.asarray(x, dtype=np.float64)
    if arr.shape != (3,) or not np.all(np.isfinite(arr)):
        raise ValueError(f"{name} must be a finite vector of shape (3,)")
    return arr

def _as_matrix3(x: np.ndarray, name: str) -> np.ndarray:
    arr = np.asarray(x, dtype=np.float64)
    if arr.shape != (3, 3) or not np.all(np.isfinite(arr)):
        raise ValueError(f"{name} must be a finite matrix of shape (3,3)")
    return arr

def _rank_and_inertia(eigenvalues: np.ndarray, atol: float) -> tuple[int, tuple[int, int, int]]:
    scale = float(np.max(np.abs(eigenvalues))) if eigenvalues.size else 0.0
    tol = atol * max(scale, np.finfo(float).tiny)
    pos = int(np.count_nonzero(eigenvalues > tol))
    neg = int(np.count_nonzero(eigenvalues < -tol))
    zero = 3 - pos - neg
    return pos + neg, (pos, neg, zero)

def classify_bianchi_type(a: np.ndarray, n: np.ndarray, *, atol: float = 1e-10) -> BianchiTypeSignature:
    """Classify the eleven Bianchi algebra strata from (a,n), not from curvature."""
    avec = _as_vector3(a, "a")
    nmat = _as_matrix3(n, "n")
    n_scale = max(float(np.linalg.norm(nmat)), np.finfo(float).tiny)
    if not np.allclose(nmat, nmat.T, rtol=0.0, atol=atol * n_scale):
        raise ValueError("n must be symmetric")
    scale = max(float(np.linalg.norm(avec)), float(np.linalg.norm(nmat)))
    if scale == 0.0:
        return BianchiTypeSignature("I", "A", 0, (0, 0, 3), None)
    jacobi = float(np.linalg.norm(nmat @ avec))
    if jacobi > atol * scale * scale:
        raise ValueError(f"Jacobi constraint n@a=0 failed: residual={jacobi:.3e}")
    eig = np.linalg.eigvalsh(nmat)
    rank, inertia = _rank_and_inertia(eig, atol)
    class_b = float(np.linalg.norm(avec)) > atol * scale
    if not class_b:
        if rank == 0: label = "I"
        elif rank == 1: label = "II"
        elif rank == 2: label = "VI_0" if inertia[0] and inertia[1] else "VII_0"
        elif rank == 3: label = "IX" if (inertia[0] == 3 or inertia[1] == 3) else "VIII"
        else: raise ValueError(f"unsupported Class-A rank/inertia: {rank}, {inertia}")
        return BianchiTypeSignature(label, "A", rank, inertia, None)
    if rank == 0:
        label, h = "V", None
    elif rank == 1:
        label, h = "IV", None
    elif rank == 2:
        tol = atol * max(float(np.max(np.abs(eig))), np.finfo(float).tiny)
        nonzero = eig[np.abs(eig) > tol]
        if nonzero.size != 2:
            raise ValueError("Class-B rank-two eigenvalue extraction failed")
        h = float(np.dot(avec, avec) / float(nonzero[0] * nonzero[1]))
        if h < 0.0:
            label = "III" if abs(h + 1.0) <= 10.0 * atol else "VI_h"
        else:
            label = "VII_h"
    else:
        raise ValueError(f"Class-B rank {rank} is incompatible with n@a=0")
    return BianchiTypeSignature(label, "B", rank, inertia, h)

def structure_tensor_from_an(a: np.ndarray, n: np.ndarray) -> np.ndarray:
    """Build C^k_ij=a_i delta^k_j-a_j delta^k_i+epsilon_ijm n^mk."""
    avec = _as_vector3(a, "a")
    nmat = _as_matrix3(n, "n")
    n_scale = max(float(np.linalg.norm(nmat)), np.finfo(float).tiny)
    if not np.allclose(nmat, nmat.T, rtol=0.0, atol=1e-10 * n_scale):
        raise ValueError("n must be symmetric")
    # C is a Lie bracket only when the Ellis--MacCallum Jacobi constraint holds.
    classify_bianchi_type(avec, nmat)
    eps = np.zeros((3, 3, 3), dtype=np.float64)
    eps[0, 1, 2] = eps[1, 2, 0] = eps[2, 0, 1] = 1.0
    eps[0, 2, 1] = eps[2, 1, 0] = eps[1, 0, 2] = -1.0
    C = np.zeros((3, 3, 3), dtype=np.float64)
    for k in range(3):
        for i in range(3):
            for j in range(3):
                C[k, i, j] = (
                    avec[i] * (1.0 if j == k else 0.0)
                    - avec[j] * (1.0 if i == k else 0.0)
                    + sum(eps[i, j, m] * nmat[m, k] for m in range(3))
                )
    return C

def spatial_ricci_from_structure_tensor(C: np.ndarray, *, atol: float = 1e-9) -> np.ndarray:
    """Compute the 3D left-invariant Ricci tensor using Koszul's formula."""
    c = np.asarray(C, dtype=np.float64)
    if c.shape != (3, 3, 3) or not np.all(np.isfinite(c)):
        raise ValueError("C must be a finite array of shape (3,3,3)")
    c_scale = max(float(np.linalg.norm(c)), np.finfo(float).tiny)
    if not np.allclose(c + np.swapaxes(c, 1, 2), 0.0, rtol=0.0, atol=atol * c_scale):
        raise ValueError("C must be antisymmetric in its lower indices")
    # A skew bilinear map need not be a Lie bracket. Verify Jacobi before
    # interpreting the Koszul contractions as homogeneous-manifold curvature.
    jacobi = np.zeros((3, 3, 3, 3), dtype=np.float64)
    for k in range(3):
        for i in range(3):
            for j in range(3):
                for ell in range(3):
                    for m in range(3):
                        jacobi[k, i, j, ell] += (
                            c[m, j, ell] * c[k, i, m]
                            + c[m, ell, i] * c[k, j, m]
                            + c[m, i, j] * c[k, ell, m]
                        )
    jacobi_residual = float(np.linalg.norm(jacobi))
    jacobi_scale = max(c_scale * c_scale, np.finfo(float).tiny)
    jacobi_tol = max(100.0 * atol, 100.0 * np.finfo(float).eps) * jacobi_scale
    if jacobi_residual > jacobi_tol:
        raise ValueError(
            "C violates the Jacobi identity: "
            f"residual={jacobi_residual:.3e}, tolerance={jacobi_tol:.3e}"
        )
    gamma = np.zeros((3, 3, 3), dtype=np.float64)
    for i in range(3):
        for j in range(3):
            for k in range(3):
                gamma[i, j, k] = 0.5 * (c[k, i, j] - c[i, j, k] + c[j, k, i])
    ric = np.zeros((3, 3), dtype=np.float64)
    for j in range(3):
        for k in range(3):
            for i in range(3):
                for m in range(3):
                    ric[j, k] += (
                        gamma[j, k, m] * gamma[i, m, i]
                        - gamma[i, k, m] * gamma[j, m, i]
                        - c[m, i, j] * gamma[m, k, i]
                    )
    curvature_scale = max(float(np.linalg.norm(c)) ** 2, np.finfo(float).tiny)
    antisym = float(np.linalg.norm(ric - ric.T))
    sym_tol = max(100.0 * atol * curvature_scale,
                  100.0 * np.finfo(float).eps * curvature_scale)
    if antisym > sym_tol:
        raise ArithmeticError(f"Ricci symmetry residual too large: {antisym:.3e}")
    return 0.5 * (ric + ric.T)

def geometry_fingerprint(a: np.ndarray, n: np.ndarray, C: Optional[np.ndarray] = None,
                         *, atol: float = 1e-10) -> GeometryFingerprint:
    """Return SO(3) and common-positive-homothety invariant structure and curvature data."""
    avec = _as_vector3(a, "a")
    nmat = _as_matrix3(n, "n")
    signature = classify_bianchi_type(avec, nmat, atol=atol)
    kappa = float(np.sqrt(np.dot(avec, avec) + np.sum(nmat * nmat)))
    if kappa == 0.0:
        ahat, nhat = np.zeros(3), np.zeros((3, 3))
    else:
        ahat, nhat = avec / kappa, nmat / kappa
    eig_n = np.linalg.eigvalsh(nhat)
    c_expected = structure_tensor_from_an(avec, nmat)
    cmat = c_expected if C is None else np.asarray(C, dtype=np.float64)
    if cmat.shape != (3, 3, 3) or not np.all(np.isfinite(cmat)):
        raise ValueError("C must be a finite array of shape (3,3,3)")
    c_scale = max(float(np.linalg.norm(c_expected)), np.finfo(float).tiny)
    if not np.allclose(cmat, c_expected, rtol=0.0, atol=100.0 * atol * c_scale):
        raise ValueError("supplied C is inconsistent with the supplied (a,n) split")
    ric = spatial_ricci_from_structure_tensor(cmat)
    eig_r = np.linalg.eigvalsh(ric)
    rnorm = float(np.linalg.norm(eig_r))
    curvature_scale = max(float(np.linalg.norm(cmat)) ** 2, np.finfo(float).tiny)
    if rnorm <= atol * curvature_scale:
        eig_shape, scalar_sign, flat, isotropic = np.zeros(3), 0, True, True
    else:
        eig_shape = eig_r / rnorm
        scalar_sign = int(np.sign(np.trace(ric)))
        flat = False
        isotropic = bool(np.max(eig_r) - np.min(eig_r) <= 100.0 * atol * rnorm)
    return GeometryFingerprint(
        type_signature=signature,
        normalized_a_norm=float(np.linalg.norm(ahat)),
        normalized_n_eigenvalues=tuple(float(x) for x in eig_n),
        normalized_ricci_eigenvalues=tuple(float(x) for x in eig_shape),
        scalar_curvature_sign=scalar_sign,
        flat_intrinsic_geometry=flat,
        isotropic_intrinsic_curvature=isotropic,
        structure_scale_kappa=kappa,
    )

def tilt_orbit_fingerprint(a: np.ndarray, n: np.ndarray, tilt_velocity: np.ndarray,
                           *, atol: float = 1e-10) -> TiltOrbitFingerprint:
    """Return SO(3)-orbit invariants and the specific-tilt identifiability stratum.

    v is a dimensionless matter 3-velocity relative to the homogeneous-slice
    normal congruence. It is not an observer boost or a solved fluid history.
    """
    avec, nmat, v = _as_vector3(a, "a"), _as_matrix3(n, "n"), _as_vector3(tilt_velocity, "tilt_velocity")
    speed2 = float(np.dot(v, v))
    if speed2 >= 1.0:
        raise ValueError(f"tilt speed must satisfy |v|<1; got |v|^2={speed2}")
    sig = classify_bianchi_type(avec, nmat, atol=atol)
    kappa = float(np.sqrt(np.dot(avec, avec) + np.sum(nmat * nmat)))
    nhat = nmat / kappa if kappa > 0.0 else np.zeros((3, 3))
    p1, p2 = float(v @ nhat @ v), float(v @ nhat @ nhat @ v)
    eig = np.linalg.eigvalsh(nhat)
    M = np.vstack((np.ones(3), eig, eig * eig))
    sv = np.linalg.svd(M, compute_uv=False)
    tol = atol * max(float(sv[0]), np.finfo(float).tiny)
    rank = int(np.count_nonzero(sv > tol))
    condition = float(sv[0] / sv[-1]) if rank == 3 else float("inf")

    if sig.class_label == "A":
        chi = float(np.linalg.det(np.column_stack((v, nhat @ v, nhat @ nhat @ v))))
        degeneracy = 0
        if speed2 > atol * atol:
            vals, vecs = np.linalg.eigh(nhat)
            i = 0
            while i < 3:
                j = i + 1
                while j < 3 and abs(vals[j] - vals[i]) <= 100.0 * atol * max(1.0, np.max(np.abs(vals))):
                    j += 1
                if j - i > 1 and np.linalg.norm(vecs[:, i:j].T @ v) > atol:
                    degeneracy = j - i - 1
                    break
                i = j
        return TiltOrbitFingerprint(
            speed2, p1, p2, None, None, chi, rank, rank, condition,
            degeneracy, "SO(3); parity-reflected orbits remain distinct"
        )

    ahat = avec / float(np.linalg.norm(avec))
    q0 = float(ahat @ v)
    q1 = float(ahat @ np.cross(v, nhat @ v))
    eig_tol = 100.0 * atol * max(1.0, np.max(np.abs(eig)))
    nonzero = eig[np.abs(eig) > eig_tol]
    if speed2 <= atol * atol:
        degeneracy = 0
    elif nonzero.size == 0:
        degeneracy = 1 if np.linalg.norm(v - q0 * ahat) > atol else 0
    elif nonzero.size == 1:
        degeneracy = 0
    elif nonzero.size == 2 and abs(nonzero[0] - nonzero[1]) <= eig_tol:
        degeneracy = 1 if np.linalg.norm(v - q0 * ahat) > atol else 0
    else:
        degeneracy = 0
    return TiltOrbitFingerprint(
        speed2, p1, p2, q0, q1, None, rank, rank, condition,
        degeneracy, "SO(3); parity-reflected orbits remain distinct"
    )

def recover_tilt_squared_components(a: np.ndarray, n: np.ndarray,
                                    speed_squared: float, p1: float, p2: float,
                                    *, atol: float = 1e-10) -> tuple[np.ndarray, int, float]:
    """Recover squared tilt components in an eigenframe; fail closed if rank<3."""
    avec, nmat = _as_vector3(a, "a"), _as_matrix3(n, "n")
    classify_bianchi_type(avec, nmat, atol=atol)
    speed_squared = float(speed_squared)
    if not np.isfinite(speed_squared) or speed_squared < 0.0 or speed_squared >= 1.0:
        raise ValueError("speed_squared must be finite and satisfy 0 <= speed_squared < 1")
    kappa = float(np.sqrt(np.dot(avec, avec) + np.sum(nmat * nmat)))
    nhat = nmat / kappa if kappa > 0.0 else np.zeros((3, 3))
    eig = np.linalg.eigvalsh(nhat)
    M = np.vstack((np.ones(3), eig, eig * eig))
    sv = np.linalg.svd(M, compute_uv=False)
    tol = atol * max(float(sv[0]), np.finfo(float).tiny)
    rank = int(np.count_nonzero(sv > tol))
    condition = float(sv[0] / sv[-1]) if rank == 3 else float("inf")
    if rank < 3:
        raise np.linalg.LinAlgError(f"tilt squared components not fully identifiable: rank={rank}/3")
    rhs = np.asarray([speed_squared, p1, p2], dtype=np.float64)
    if not np.all(np.isfinite(rhs)) or speed_squared < 0.0:
        raise ValueError("moments must be finite and speed_squared nonnegative")
    w = np.linalg.solve(M, rhs)
    if np.min(w) < -100.0 * atol:
        raise ValueError("moments imply a negative squared tilt component")
    return np.maximum(w, 0.0), rank, condition
