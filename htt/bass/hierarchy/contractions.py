"""bass/hierarchy/contractions.py (LB-2a) — PSTF algebra utilities.

Provides the symmetric-trace-free (STF) projector on rank-ℓ 3-tensors
and the packed ↔ full-tensor conversion used by ``PSTFTensor``.

Design
------
For each rank ``ℓ ∈ {0, 1, …, L_MAX_CACHED}`` we precompute an
orthonormal basis ``Q_ℓ ∈ R^{3^ℓ × (2ℓ+1)}`` whose columns span the
STF subspace of ``⊗^ℓ R^3``. Packed → full conversion is ``T_flat =
Q_ℓ · c``; the inverse is ``c = Q_ℓ^T · T_flat``. Because the columns
of ``Q_ℓ`` are flat-orthonormal, ``Q_ℓ^T · Q_ℓ = I`` and the round
trip is exact to machine precision. The STF projector on an arbitrary
rank-ℓ tensor is ``T → Q_ℓ · (Q_ℓ^T · T_flat)``.

Construction of ``Q_ℓ``:

1. Enumerate the symmetric-tensor basis in ``⊗^ℓ R^3`` by looping over
   all multi-exponents ``(a, b, c)`` with ``a + b + c = ℓ``. Each
   ``(a, b, c)`` produces one totally-symmetric basis tensor whose
   support is the distinct permutations of the string
   ``(0^a 1^b 2^c)``.
2. For each symmetric basis tensor compute its rank-``(ℓ-2)`` trace
   over the first two axes. By full symmetry the trace over any pair
   is equal, so tracing over one pair suffices.
3. Find the null space of the trace matrix; combine with the symmetric
   basis to obtain vectors that are simultaneously symmetric and
   trace-free. The null-space dimension equals ``2ℓ + 1`` exactly.
4. Orthonormalise via QR to form ``Q_ℓ``.

References
----------
- ``docs/lowell_bianchi/00_conventions.md §5`` — PSTF packing.
- Ellis, Maartens, MacCallum, *Relativistic Cosmology* §4.5 — moment
  expansion and STF projection.
- Ellis-Bruni-Ellis 1992 — explicit PSTF projector forms up to ℓ=8.
- Arfken-Weber-Harris, *Mathematical Methods for Physicists* Ch 16 —
  real spherical harmonics basis (the (2ℓ+1) count).
"""
from __future__ import annotations

from itertools import permutations
from typing import Dict

import numpy as np


# Maximum ℓ for which we pre-build the orthonormal STF basis. The spec
# constrains the hierarchy to ``L ≤ 8`` (00_conventions.md §10 and
# 02_multipole_hierarchy_spec.md §2.5).
L_MAX_CACHED: int = 8


# Cache populated at import time by ``_initialise_cache``.
_STF_BASIS_CACHE: Dict[int, np.ndarray] = {}


def _numeric_dtype(value: np.ndarray | object) -> np.dtype:
    """Return the canonical floating dtype for real/complex tensors.

    The STF basis itself is real-valued, but FB-5 evolves complex mode
    amplitudes. We therefore preserve complex128 whenever the input has
    a non-zero imaginary lane and otherwise keep the historical float64
    path byte-identical.
    """
    arr = np.asarray(value)
    return np.dtype(np.complex128 if np.iscomplexobj(arr) else np.float64)


def _symmetric_basis_flat(ell: int) -> np.ndarray:
    """Return the symmetric-tensor basis for rank ``ell`` as a flat matrix.

    Rows are the ``(ℓ+1)(ℓ+2)/2`` basis tensors, each flattened to a
    length-``3**ell`` vector. Each basis tensor has value 1 at every
    distinct permutation of the canonical multi-index ``(0^a 1^b 2^c)``
    and zero elsewhere.

    Reference: Ellis §4.5 uses the closure of symmetric tensors over
    these monomial-like basis elements.
    """
    dim = 3 ** ell if ell >= 1 else 1
    rows: list[np.ndarray] = []
    for a in range(ell + 1):
        for b in range(ell + 1 - a):
            c = ell - a - b
            canonical = tuple([0] * a + [1] * b + [2] * c)
            tensor = np.zeros((3,) * ell if ell > 0 else ()) if ell > 0 else np.array(1.0)
            if ell == 0:
                # Rank-0: single scalar basis tensor.
                rows.append(np.array([1.0]))
                return np.array(rows)
            seen: set[tuple[int, ...]] = set()
            for perm in permutations(canonical):
                if perm in seen:
                    continue
                seen.add(perm)
                tensor[perm] = 1.0
            rows.append(tensor.reshape(dim).copy())
    return np.array(rows)


def _build_stf_orthonormal_basis(ell: int) -> np.ndarray:
    """Orthonormal basis matrix ``Q_ℓ`` for the STF subspace of ``⊗^ℓ R^3``.

    Returns a ``(3**ell, 2ell+1)`` array whose columns are an orthonormal
    basis (under the flat-vector inner product) of the symmetric
    trace-free subspace.

    Reference: 02_multipole_hierarchy_spec.md §3; Ellis §4.5.
    """
    if ell == 0:
        return np.array([[1.0]], dtype=np.float64)
    if ell == 1:
        # Vectors are automatically STF: Q = I_3.
        return np.eye(3, dtype=np.float64)

    dim = 3 ** ell
    sym_basis_rows = _symmetric_basis_flat(ell)  # (N_sym, dim)

    # Compute rank-(ell-2) trace over axes 0,1 of each symmetric basis tensor.
    # For a FULLY symmetric tensor the trace over any pair is identical,
    # so tracing over one pair captures the entire trace content.
    n_sym = sym_basis_rows.shape[0]
    dim_tr = 3 ** (ell - 2)
    trace_mat = np.zeros((dim_tr, n_sym), dtype=np.float64)
    for i in range(n_sym):
        V = sym_basis_rows[i].reshape((3,) * ell)
        tr_V = np.trace(V, axis1=0, axis2=1)
        trace_mat[:, i] = tr_V.reshape(dim_tr)

    # Null space of trace_mat → symmetric basis combinations that are
    # additionally trace-free.
    _, sigma, Vt = np.linalg.svd(trace_mat, full_matrices=True)
    if sigma.size == 0:
        rank = 0
    else:
        tol = 1e-10 * max(sigma.max(), 1.0)
        rank = int(np.sum(sigma > tol))
    null_coefs = Vt[rank:].T  # (n_sym, n_null)

    # Lift to flat-tensor space and orthonormalise.
    stf_vectors = sym_basis_rows.T @ null_coefs  # (dim, n_null)
    Q, _ = np.linalg.qr(stf_vectors)

    expected = 2 * ell + 1
    if Q.shape[1] < expected:
        raise RuntimeError(
            f"STF basis construction failed for ell={ell}: "
            f"got {Q.shape[1]} orthonormal vectors, expected {expected}."
        )
    return np.ascontiguousarray(Q[:, :expected], dtype=np.float64)


def _initialise_cache() -> None:
    """Populate ``_STF_BASIS_CACHE`` at import time for ℓ ≤ L_MAX_CACHED."""
    for ell in range(L_MAX_CACHED + 1):
        _STF_BASIS_CACHE[ell] = _build_stf_orthonormal_basis(ell)


_initialise_cache()


def stf_basis(ell: int) -> np.ndarray:
    """Return the cached orthonormal STF basis ``Q_ℓ`` for rank ``ell``.

    Shape ``(3**ell, 2*ell + 1)`` with orthonormal columns.

    Reference: 02_multipole_hierarchy_spec.md §3.
    """
    if ell < 0:
        raise ValueError(f"ell must be non-negative, got {ell}")
    if ell > L_MAX_CACHED:
        raise NotImplementedError(
            f"ell={ell} exceeds precomputed cache L_MAX_CACHED={L_MAX_CACHED}. "
            f"Rebuild with higher L_MAX_CACHED if needed."
        )
    return _STF_BASIS_CACHE[ell]


def sym_trace_free(tensor: np.ndarray) -> np.ndarray:
    """Project a rank-ℓ tensor onto its symmetric-trace-free part.

    Input is a ``(3,) * ell`` ndarray. The output has the same shape
    and satisfies both full index symmetry and vanishing of every
    two-index trace.

    - ``ell = 0``: returns the input unchanged.
    - ``ell = 1``: returns the input unchanged (vectors are
      automatically PSTF on 3-space).
    - ``ell >= 2``: projects via the cached STF orthonormal basis.

    Reference: Ellis §4.5 (STF projection); Ellis-Bruni-Ellis 1992.
    """
    arr = np.asarray(tensor)
    dtype = _numeric_dtype(arr)
    arr = arr.astype(dtype, copy=False)
    if arr.ndim == 0:
        return np.asarray(arr, dtype=dtype).copy()
    if arr.ndim == 1:
        return arr.copy()

    ell = arr.ndim
    # Verify the tensor is on 3-space (each axis has length 3).
    if any(dim != 3 for dim in arr.shape):
        raise ValueError(
            f"sym_trace_free expects all axes of length 3, got shape {arr.shape}"
        )
    Q = stf_basis(ell)
    flat = arr.reshape(-1)
    components = Q.T @ flat
    projected = Q @ components
    return projected.reshape(arr.shape)


def pstf_pack(tensor: np.ndarray) -> np.ndarray:
    """Extract packed PSTF components ``c ∈ R^{2ℓ+1}`` from a full tensor.

    The input is a rank-ℓ ndarray on 3-space; the output gives its
    coordinates in the orthonormal STF basis. Any part of the input
    that is not symmetric-trace-free is silently projected away.

    Reference: 02_multipole_hierarchy_spec.md §2.3 (``pstf_from_tensor``).
    """
    arr = np.asarray(tensor)
    dtype = _numeric_dtype(arr)
    arr = arr.astype(dtype, copy=False)
    if arr.ndim == 0:
        return np.array([arr.item()], dtype=dtype)
    ell = arr.ndim
    if any(dim != 3 for dim in arr.shape):
        raise ValueError(
            f"pstf_pack expects all axes of length 3, got shape {arr.shape}"
        )
    Q = stf_basis(ell)
    return Q.T @ arr.reshape(-1)


def pstf_unpack(components: np.ndarray, ell: int) -> np.ndarray:
    """Inverse of ``pstf_pack``: reconstruct the full (3,)*ell tensor.

    Reference: 02_multipole_hierarchy_spec.md §2.3 (``pstf_to_tensor``).
    """
    c = np.asarray(components)
    dtype = _numeric_dtype(c)
    c = c.astype(dtype, copy=False)
    if c.shape != (2 * ell + 1,):
        raise ValueError(
            f"components shape {c.shape} != (2ell+1,) = ({2*ell+1},) for ell={ell}"
        )
    if ell == 0:
        return np.array(c[0].item(), dtype=dtype)
    Q = stf_basis(ell)
    return (Q @ c).reshape((3,) * ell)


def verify_pstf_invariants(
    tensor: np.ndarray, tol: float = 1e-12
) -> tuple[bool, str]:
    """Check that ``tensor`` is (1) symmetric under every axis swap and
    (2) trace-free over every axis pair.

    Returns ``(ok, message)`` — ``message`` is empty on success or a
    diagnostic describing the first violation.

    Reference: 00_conventions.md §5.1, invariant #6 of README §5.
    """
    arr = np.asarray(tensor)
    if arr.ndim < 2:
        return True, ""
    ell = arr.ndim
    # Symmetry: compare against any axis swap.
    from itertools import combinations
    for i, j in combinations(range(ell), 2):
        axes = list(range(ell))
        axes[i], axes[j] = axes[j], axes[i]
        swapped = np.transpose(arr, axes)
        diff = np.max(np.abs(arr - swapped))
        if diff > tol * max(np.max(np.abs(arr)), 1.0):
            return False, (
                f"asymmetric under swap of axes {i}<->{j} "
                f"(max diff = {diff:.3e})"
            )
    # Trace-free over every pair.
    for i, j in combinations(range(ell), 2):
        if i == j:
            continue
        axes_first = list(range(ell))
        axes_first.remove(j)
        axes_first.remove(i)
        # Put i, j at the front then trace
        perm = [i, j] + axes_first
        permuted = np.transpose(arr, perm)
        tr = np.trace(permuted, axis1=0, axis2=1)
        tr_norm = np.max(np.abs(tr)) if tr.size else 0.0
        if tr_norm > tol * max(np.max(np.abs(arr)), 1.0):
            return False, (
                f"trace non-zero over axes ({i},{j}) "
                f"(max |tr| = {tr_norm:.3e})"
            )
    return True, ""
