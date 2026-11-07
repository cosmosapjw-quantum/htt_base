"""STF Metric Bridge: Coordinate chart conversions and Gram metric for STF rank-2 tensors.

Implements bidirectional mappings between:
1. Cartesian 5-vector chart:
     v_cart = (S_xx, S_yy, S_xy, S_xz, S_yz)
   with S_zz = -S_xx - S_yy.
2. Frobenius-orthonormal 5-vector chart:
     v_on = (1/sqrt(2)*(S_xx - S_yy),
             c1_sign/sqrt(6)*(S_xx + S_yy - 2*S_zz),
             sqrt(2)*S_xy,
             sqrt(2)*S_xz,
             sqrt(2)*S_yz)
   where c1_sign = +1 in the canonical 'kinematic_response' basis (matching
   STF_BASIS in kinematic_response.py and CANONICAL_STF_BASIS in stf_canonical.py),
   or c1_sign = -1 in the 'explicit_szz' / astrophysical convention where the
   second element is 1/sqrt(6)*(2*S_zz - S_xx - S_yy).

Provides:
- Exact Gram metric matrix G_STF5 such that:
    v_cart.T @ G_STF5 @ v_cart == v_on.T @ v_on == Tr(S @ S)
- Inverse Gram metric G_STF5_INV.
- Exact O(3) and SO(3) rotation equivariance operators and invariance validators.
- Fully typed, vectorized where applicable, with comprehensive docstrings.
"""

from __future__ import annotations

import math
from typing import Literal

import numpy as np

# Basis / chart conventions
Convention = Literal["kinematic_response", "explicit_szz", "astrophysical"]
Chart = Literal["cartesian", "orthonormal"]

_SQRT2: float = math.sqrt(2.0)
_SQRT6: float = math.sqrt(6.0)
_SQRT3_2: float = math.sqrt(1.5)  # sqrt(3/2)

# ---------------------------------------------------------------------------
# Gram Metric Matrix
# ---------------------------------------------------------------------------
# For v_cart = (S_xx, S_yy, S_xy, S_xz, S_yz) with S_zz = -S_xx - S_yy:
# Tr(S @ S) = S_xx^2 + S_yy^2 + (-S_xx - S_yy)^2 + 2*S_xy^2 + 2*S_xz^2 + 2*S_yz^2
#           = 2*S_xx^2 + 2*S_yy^2 + 2*S_xx*S_yy + 2*S_xy^2 + 2*S_xz^2 + 2*S_yz^2
# Hence G_STF5[0,0] = 2, G_STF5[1,1] = 2, G_STF5[0,1] = G_STF5[1,0] = 1,
# and diagonal 2 for the off-diagonal shear components.
G_STF5: np.ndarray = np.array([
    [2.0, 1.0, 0.0, 0.0, 0.0],
    [1.0, 2.0, 0.0, 0.0, 0.0],
    [0.0, 0.0, 2.0, 0.0, 0.0],
    [0.0, 0.0, 0.0, 2.0, 0.0],
    [0.0, 0.0, 0.0, 0.0, 2.0],
], dtype=np.float64)
G_STF5.setflags(write=False)

# Inverse Gram metric:
# Inverse of [[2, 1], [1, 2]] is [[2/3, -1/3], [-1/3, 2/3]].
G_STF5_INV: np.ndarray = np.array([
    [2.0 / 3.0, -1.0 / 3.0, 0.0, 0.0, 0.0],
    [-1.0 / 3.0, 2.0 / 3.0, 0.0, 0.0, 0.0],
    [0.0, 0.0, 0.5, 0.0, 0.0],
    [0.0, 0.0, 0.0, 0.5, 0.0],
    [0.0, 0.0, 0.0, 0.0, 0.5],
], dtype=np.float64)
G_STF5_INV.setflags(write=False)


# ---------------------------------------------------------------------------
# Orthonormal Basis Tensors
# ---------------------------------------------------------------------------
# Basis for 'kinematic_response' convention (matches kinematic_response.STF_BASIS)
STF_BASIS_KINEMATIC_RESPONSE: np.ndarray = np.array([
    [[1.0 / _SQRT2, 0.0, 0.0],
     [0.0, -1.0 / _SQRT2, 0.0],
     [0.0, 0.0, 0.0]],
    [[1.0 / _SQRT6, 0.0, 0.0],
     [0.0, 1.0 / _SQRT6, 0.0],
     [0.0, 0.0, -2.0 / _SQRT6]],
    [[0.0, 1.0 / _SQRT2, 0.0],
     [1.0 / _SQRT2, 0.0, 0.0],
     [0.0, 0.0, 0.0]],
    [[0.0, 0.0, 1.0 / _SQRT2],
     [0.0, 0.0, 0.0],
     [1.0 / _SQRT2, 0.0, 0.0]],
    [[0.0, 0.0, 0.0],
     [0.0, 0.0, 1.0 / _SQRT2],
     [0.0, 1.0 / _SQRT2, 0.0]],
], dtype=np.float64)
STF_BASIS_KINEMATIC_RESPONSE.setflags(write=False)

# Basis for 'explicit_szz' / astrophysical convention:
# E_1 sign flipped so Tr(S @ E_1) = 1/sqrt(6)*(2*S_zz - S_xx - S_yy)
STF_BASIS_EXPLICIT_SZZ: np.ndarray = np.array([
    [[1.0 / _SQRT2, 0.0, 0.0],
     [0.0, -1.0 / _SQRT2, 0.0],
     [0.0, 0.0, 0.0]],
    [[-1.0 / _SQRT6, 0.0, 0.0],
     [0.0, -1.0 / _SQRT6, 0.0],
     [0.0, 0.0, 2.0 / _SQRT6]],
    [[0.0, 1.0 / _SQRT2, 0.0],
     [1.0 / _SQRT2, 0.0, 0.0],
     [0.0, 0.0, 0.0]],
    [[0.0, 0.0, 1.0 / _SQRT2],
     [0.0, 0.0, 0.0],
     [1.0 / _SQRT2, 0.0, 0.0]],
    [[0.0, 0.0, 0.0],
     [0.0, 0.0, 1.0 / _SQRT2],
     [0.0, 1.0 / _SQRT2, 0.0]],
], dtype=np.float64)
STF_BASIS_EXPLICIT_SZZ.setflags(write=False)


def stf_gram_metric() -> np.ndarray:
    """Return the constant 5x5 Gram metric matrix G_STF5."""
    return G_STF5.copy()


def get_stf_basis(convention: Convention = "kinematic_response") -> np.ndarray:
    """Return the 5x3x3 Frobenius-orthonormal STF basis for the given convention."""
    if convention in ("kinematic_response", "default"):
        return STF_BASIS_KINEMATIC_RESPONSE
    elif convention in ("explicit_szz", "astrophysical"):
        return STF_BASIS_EXPLICIT_SZZ
    else:
        raise ValueError(f"Unknown convention: {convention}")


# ---------------------------------------------------------------------------
# Matrix Transformation Helpers (M and M_inv)
# ---------------------------------------------------------------------------
def cartesian_to_orthonormal_matrix(convention: Convention = "kinematic_response") -> np.ndarray:
    """Return 5x5 matrix M such that v_on = M @ v_cart."""
    s_zz_sign = -1.0 if convention in ("explicit_szz", "astrophysical") else 1.0
    return np.array([
        [1.0 / _SQRT2, -1.0 / _SQRT2, 0.0, 0.0, 0.0],
        [s_zz_sign * _SQRT3_2, s_zz_sign * _SQRT3_2, 0.0, 0.0, 0.0],
        [0.0, 0.0, _SQRT2, 0.0, 0.0],
        [0.0, 0.0, 0.0, _SQRT2, 0.0],
        [0.0, 0.0, 0.0, 0.0, _SQRT2],
    ], dtype=np.float64)


def orthonormal_to_cartesian_matrix(convention: Convention = "kinematic_response") -> np.ndarray:
    """Return 5x5 matrix M_inv such that v_cart = M_inv @ v_on."""
    s_zz_sign = -1.0 if convention in ("explicit_szz", "astrophysical") else 1.0
    return np.array([
        [1.0 / _SQRT2, s_zz_sign / _SQRT6, 0.0, 0.0, 0.0],
        [-1.0 / _SQRT2, s_zz_sign / _SQRT6, 0.0, 0.0, 0.0],
        [0.0, 0.0, 1.0 / _SQRT2, 0.0, 0.0],
        [0.0, 0.0, 0.0, 1.0 / _SQRT2, 0.0],
        [0.0, 0.0, 0.0, 0.0, 1.0 / _SQRT2],
    ], dtype=np.float64)


# ---------------------------------------------------------------------------
# Coordinate Chart Conversions
# ---------------------------------------------------------------------------
def cartesian_to_orthonormal(
    v_cart: np.ndarray,
    convention: Convention = "kinematic_response",
) -> np.ndarray:
    """Convert Cartesian 5-vector chart to Frobenius-orthonormal 5-vector chart.

    Parameters
    ----------
    v_cart : np.ndarray
        Array with trailing dimension 5: (..., 5), holding (S_xx, S_yy, S_xy, S_xz, S_yz).
    convention : Convention
        'kinematic_response' (default) or 'explicit_szz' / 'astrophysical'.

    Returns
    -------
    np.ndarray
        Array of same shape (..., 5) in orthonormal chart.
    """
    arr = np.asarray(v_cart, dtype=np.float64)
    if arr.shape[-1] != 5:
        raise ValueError(f"Expected trailing dimension 5, got shape {arr.shape}")
    M = cartesian_to_orthonormal_matrix(convention)
    return np.einsum("ab,...b->...a", M, arr)


def orthonormal_to_cartesian(
    v_on: np.ndarray,
    convention: Convention = "kinematic_response",
) -> np.ndarray:
    """Convert Frobenius-orthonormal 5-vector chart to Cartesian 5-vector chart.

    Parameters
    ----------
    v_on : np.ndarray
        Array with trailing dimension 5: (..., 5).
    convention : Convention
        'kinematic_response' (default) or 'explicit_szz' / 'astrophysical'.

    Returns
    -------
    np.ndarray
        Array of same shape (..., 5) in Cartesian chart (S_xx, S_yy, S_xy, S_xz, S_yz).
    """
    arr = np.asarray(v_on, dtype=np.float64)
    if arr.shape[-1] != 5:
        raise ValueError(f"Expected trailing dimension 5, got shape {arr.shape}")
    M_inv = orthonormal_to_cartesian_matrix(convention)
    return np.einsum("ab,...b->...a", M_inv, arr)


# ---------------------------------------------------------------------------
# 3x3 Matrix <-> 5-Vector Conversions
# ---------------------------------------------------------------------------
def cartesian_to_stf_matrix(v_cart: np.ndarray) -> np.ndarray:
    """Reconstruct 3x3 symmetric trace-free tensor from Cartesian 5-vector.

    v_cart = (S_xx, S_yy, S_xy, S_xz, S_yz)
    S_zz is reconstructed as -S_xx - S_yy.

    Parameters
    ----------
    v_cart : np.ndarray
        Array of shape (..., 5).

    Returns
    -------
    np.ndarray
        Array of shape (..., 3, 3).
    """
    arr = np.asarray(v_cart, dtype=np.float64)
    if arr.shape[-1] != 5:
        raise ValueError(f"Expected trailing dimension 5, got {arr.shape}")
    xx = arr[..., 0]
    yy = arr[..., 1]
    xy = arr[..., 2]
    xz = arr[..., 3]
    yz = arr[..., 4]
    zz = -xx - yy

    # Construct (..., 3, 3) matrix
    out_shape = arr.shape[:-1] + (3, 3)
    out = np.zeros(out_shape, dtype=np.float64)
    out[..., 0, 0] = xx
    out[..., 0, 1] = xy
    out[..., 0, 2] = xz
    out[..., 1, 0] = xy
    out[..., 1, 1] = yy
    out[..., 1, 2] = yz
    out[..., 2, 0] = xz
    out[..., 2, 1] = yz
    out[..., 2, 2] = zz
    return out


def stf_matrix_to_cartesian(S: np.ndarray) -> np.ndarray:
    """Extract Cartesian 5-vector chart from 3x3 symmetric trace-free tensor.

    Returns (S_xx, S_yy, S_xy, S_xz, S_yz). Validates symmetry and trace-freeness.

    Parameters
    ----------
    S : np.ndarray
        Array of shape (..., 3, 3).

    Returns
    -------
    np.ndarray
        Array of shape (..., 5).
    """
    arr = np.asarray(S, dtype=np.float64)
    if arr.shape[-2:] != (3, 3):
        raise ValueError(f"Expected trailing dimensions (3, 3), got {arr.shape}")
    
    validate_stf_matrix(arr)

    xx = arr[..., 0, 0]
    yy = arr[..., 1, 1]
    xy = 0.5 * (arr[..., 0, 1] + arr[..., 1, 0])
    xz = 0.5 * (arr[..., 0, 2] + arr[..., 2, 0])
    yz = 0.5 * (arr[..., 1, 2] + arr[..., 2, 1])

    return np.stack([xx, yy, xy, xz, yz], axis=-1)


def orthonormal_to_stf_matrix(
    v_on: np.ndarray,
    convention: Convention = "kinematic_response",
) -> np.ndarray:
    """Reconstruct 3x3 STF tensor from Frobenius-orthonormal 5-vector.

    Parameters
    ----------
    v_on : np.ndarray
        Array of shape (..., 5).
    convention : Convention
        'kinematic_response' (default) or 'explicit_szz' / 'astrophysical'.

    Returns
    -------
    np.ndarray
        Array of shape (..., 3, 3).
    """
    arr = np.asarray(v_on, dtype=np.float64)
    if arr.shape[-1] != 5:
        raise ValueError(f"Expected trailing dimension 5, got {arr.shape}")
    basis = get_stf_basis(convention)
    return np.einsum("...a,aij->...ij", arr, basis)


def stf_matrix_to_orthonormal(
    S: np.ndarray,
    convention: Convention = "kinematic_response",
) -> np.ndarray:
    """Project 3x3 STF tensor onto Frobenius-orthonormal 5-vector chart.

    Parameters
    ----------
    S : np.ndarray
        Array of shape (..., 3, 3).
    convention : Convention
        'kinematic_response' (default) or 'explicit_szz' / 'astrophysical'.

    Returns
    -------
    np.ndarray
        Array of shape (..., 5).
    """
    arr = np.asarray(S, dtype=np.float64)
    if arr.shape[-2:] != (3, 3):
        raise ValueError(f"Expected trailing dimensions (3, 3), got {arr.shape}")
    validate_stf_matrix(arr)
    basis = get_stf_basis(convention)
    return np.einsum("...ij,aij->...a", arr, basis)


# ---------------------------------------------------------------------------
# Projection and Validation
# ---------------------------------------------------------------------------
def stf_project(tensor: np.ndarray) -> np.ndarray:
    """Return the Euclidean symmetric trace-free projection of a 3x3 tensor.

    S = 1/2*(T + T.T) - 1/3*Tr(T)*I_3.
    """
    t = np.asarray(tensor, dtype=np.float64)
    if t.shape[-2:] != (3, 3):
        raise ValueError(f"Expected trailing dimensions (3, 3), got {t.shape}")
    sym = 0.5 * (t + np.swapaxes(t, -1, -2))
    tr = np.trace(sym, axis1=-2, axis2=-1)[..., np.newaxis, np.newaxis]
    return sym - (1.0 / 3.0) * tr * np.eye(3)


def validate_stf_matrix(S: np.ndarray, atol: float = 1e-12) -> None:
    """Raise ValueError if S is not symmetric or trace-free within tolerance."""
    arr = np.asarray(S, dtype=np.float64)
    if arr.shape[-2:] != (3, 3):
        raise ValueError(f"Expected trailing dimensions (3, 3), got {arr.shape}")
    scale = float(np.max(np.abs(arr))) if arr.size > 0 else 1.0
    tol = max(atol, 64.0 * np.finfo(float).eps * scale)

    # Check symmetry
    asym = np.swapaxes(arr, -1, -2) - arr
    if np.any(np.abs(asym) > tol):
        raise ValueError("Tensor is not symmetric within tolerance")

    # Check trace
    tr = np.trace(arr, axis1=-2, axis2=-1)
    if np.any(np.abs(tr) > tol):
        raise ValueError("Tensor is not trace-free within tolerance")


# ---------------------------------------------------------------------------
# Inner Products and Frobenius Norms
# ---------------------------------------------------------------------------
def stf_cartesian_inner_product(u_cart: np.ndarray, v_cart: np.ndarray) -> float | np.ndarray:
    """Compute inner product of two Cartesian 5-vectors using Gram metric G_STF5.

    u_cart.T @ G_STF5 @ v_cart == Tr(S_u @ S_v).
    """
    u = np.asarray(u_cart, dtype=np.float64)
    v = np.asarray(v_cart, dtype=np.float64)
    return np.einsum("...a,ab,...b->...", u, G_STF5, v)


def stf_orthonormal_inner_product(u_on: np.ndarray, v_on: np.ndarray) -> float | np.ndarray:
    """Compute Euclidean inner product of two orthonormal 5-vectors.

    u_on.T @ v_on == Tr(S_u @ S_v).
    """
    u = np.asarray(u_on, dtype=np.float64)
    v = np.asarray(v_on, dtype=np.float64)
    return np.einsum("...a,...a->...", u, v)


def stf_matrix_inner_product(S1: np.ndarray, S2: np.ndarray) -> float | np.ndarray:
    """Compute Frobenius matrix inner product: Tr(S1 @ S2)."""
    s1 = np.asarray(S1, dtype=np.float64)
    s2 = np.asarray(S2, dtype=np.float64)
    return np.einsum("...ij,...ji->...", s1, s2)


def stf_frobenius_norm_sq(
    v: np.ndarray,
    chart: Chart = "cartesian",
    convention: Convention = "kinematic_response",
) -> float | np.ndarray:
    """Compute squared Frobenius norm Tr(S @ S).

    If chart == 'cartesian', evaluates v.T @ G_STF5 @ v.
    If chart == 'orthonormal', evaluates v.T @ v.
    """
    arr = np.asarray(v, dtype=np.float64)
    if chart == "cartesian":
        return stf_cartesian_inner_product(arr, arr)
    elif chart == "orthonormal":
        return stf_orthonormal_inner_product(arr, arr)
    else:
        raise ValueError(f"Unknown chart: {chart}")


def stf_frobenius_norm(
    v: np.ndarray,
    chart: Chart = "cartesian",
    convention: Convention = "kinematic_response",
) -> float | np.ndarray:
    """Compute Frobenius norm sqrt(Tr(S @ S))."""
    return np.sqrt(np.maximum(stf_frobenius_norm_sq(v, chart=chart, convention=convention), 0.0))


# ---------------------------------------------------------------------------
# O(3) and SO(3) Equivariance & Invariance
# ---------------------------------------------------------------------------
def rotate_stf_matrix(S: np.ndarray, R: np.ndarray) -> np.ndarray:
    """Apply spatial rotation/reflection R in O(3) to 3x3 STF tensor S.

    S' = R @ S @ R.T.
    """
    r = np.asarray(R, dtype=np.float64)
    if r.shape != (3, 3):
        raise ValueError(f"Expected rotation matrix shape (3, 3), got {r.shape}")
    s = np.asarray(S, dtype=np.float64)
    return np.einsum("ik,...kl,jl->...ij", r, s, r)


def stf_rotation_operator_5d(
    R: np.ndarray,
    chart: Chart = "orthonormal",
    convention: Convention = "kinematic_response",
) -> np.ndarray:
    """Compute 5x5 transformation operator D_5(R) for rotation/reflection R in O(3).

    For the orthonormal chart:
      [D5_on(R)]_ab = Tr(E_a @ R @ E_b @ R.T).
      This operator is an exact 5x5 orthogonal matrix in O(5).

    For the Cartesian chart:
      D5_cart(R) = M_inv @ D5_on(R) @ M.
      This operator satisfies: D5_cart(R).T @ G_STF5 @ D5_cart(R) == G_STF5.

    Parameters
    ----------
    R : np.ndarray
        (3, 3) matrix in O(3) or SO(3).
    chart : Chart
        'orthonormal' or 'cartesian'.
    convention : Convention
        'kinematic_response' (default) or 'explicit_szz' / 'astrophysical'.

    Returns
    -------
    np.ndarray
        (5, 5) real operator matrix.
    """
    r = np.asarray(R, dtype=np.float64)
    if r.shape != (3, 3):
        raise ValueError(f"Expected rotation matrix shape (3, 3), got {r.shape}")
    
    basis = get_stf_basis(convention)  # (5, 3, 3)
    
    # Rotated basis elements: R @ E_b @ R.T
    rotated_basis = np.einsum("ik,bkl,jl->bij", r, basis, r)  # (5, 3, 3)
    
    # D5_on[a, b] = Tr(E_a @ rotated_basis[b])
    D5_on = np.einsum("aij,bji->ab", basis, rotated_basis)  # (5, 5)

    if chart == "orthonormal":
        return D5_on
    elif chart == "cartesian":
        M = cartesian_to_orthonormal_matrix(convention)
        M_inv = orthonormal_to_cartesian_matrix(convention)
        return M_inv @ D5_on @ M
    else:
        raise ValueError(f"Unknown chart: {chart}")


def rotate_stf_vector(
    v: np.ndarray,
    R: np.ndarray,
    chart: Chart = "orthonormal",
    convention: Convention = "kinematic_response",
) -> np.ndarray:
    """Rotate 5-vector representation under spatial rotation/reflection R in O(3).

    v' = D_5(R) @ v.

    Parameters
    ----------
    v : np.ndarray
        Array of shape (..., 5).
    R : np.ndarray
        (3, 3) rotation/reflection matrix in O(3).
    chart : Chart
        'orthonormal' or 'cartesian'.
    convention : Convention
        'kinematic_response' or 'explicit_szz'.

    Returns
    -------
    np.ndarray
        Rotated 5-vector array of shape (..., 5).
    """
    arr = np.asarray(v, dtype=np.float64)
    D = stf_rotation_operator_5d(R, chart=chart, convention=convention)
    return np.einsum("ab,...b->...a", D, arr)


def verify_o3_invariance(
    v: np.ndarray,
    R: np.ndarray,
    chart: Chart = "orthonormal",
    convention: Convention = "kinematic_response",
    atol: float = 1e-12,
) -> bool:
    """Verify exact O(3) norm preservation and rotation equivariance.

    Checks:
    1. |D_5(R) @ v|^2 == |v|^2 (via appropriate metric).
    2. Matrix equivariance: stf_to_matrix(rotate(v)) == rotate_matrix(stf_to_matrix(v)).
    """
    v_arr = np.asarray(v, dtype=np.float64)
    norm_sq_before = stf_frobenius_norm_sq(v_arr, chart=chart, convention=convention)
    v_rot = rotate_stf_vector(v_arr, R, chart=chart, convention=convention)
    norm_sq_after = stf_frobenius_norm_sq(v_rot, chart=chart, convention=convention)

    if not np.allclose(norm_sq_before, norm_sq_after, atol=atol):
        return False

    # Check matrix equivariance
    if chart == "cartesian":
        S = cartesian_to_stf_matrix(v_arr)
        S_rot_expected = rotate_stf_matrix(S, R)
        S_rot_actual = cartesian_to_stf_matrix(v_rot)
    else:
        S = orthonormal_to_stf_matrix(v_arr, convention=convention)
        S_rot_expected = rotate_stf_matrix(S, R)
        S_rot_actual = orthonormal_to_stf_matrix(v_rot, convention=convention)

    return bool(np.allclose(S_rot_expected, S_rot_actual, atol=atol))
