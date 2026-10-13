"""Sampling-covariance operators for the shared bulk-flow helpers.

The operator deliberately supports only positive-definite covariance models.
It avoids materialising catalogue-scale dense matrices while retaining the
``solve``, ``matmat``, log-determinant, and row-subsetting operations required
by GLS estimators and normalized Gaussian likelihoods.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property

import numpy as np

__all__ = ["SamplingCovariance", "as_sampling_covariance"]


def _small_longdouble_solve(matrix: np.ndarray, rhs: np.ndarray) -> np.ndarray:
    """Pivoted solve for the small Woodbury capacitance in extended precision."""
    a = np.array(matrix, dtype=np.longdouble, copy=True)
    b = np.array(rhs, dtype=np.longdouble, copy=True)
    vector_rhs = b.ndim == 1
    if vector_rhs:
        b = b[:, None]
    for column in range(a.shape[0]):
        pivot = column + int(np.argmax(np.abs(a[column:, column])))
        if a[pivot, column] == 0.0:
            raise ValueError("low-rank covariance capacitance is singular")
        if pivot != column:
            a[[column, pivot]] = a[[pivot, column]]
            b[[column, pivot]] = b[[pivot, column]]
        factor = a[column + 1:, column] / a[column, column]
        a[column + 1:, column:] -= factor[:, None] * a[column, column:]
        b[column + 1:] -= factor[:, None] * b[column]
    x = np.empty_like(b)
    for row in range(a.shape[0] - 1, -1, -1):
        x[row] = (b[row] - a[row, row + 1:] @ x[row + 1:]) / a[row, row]
    return x[:, 0] if vector_rhs else x


@dataclass(frozen=True)
class SamplingCovariance:
    """An SPD covariance represented as dense, diagonal, or ``D + U U.T``.

    ``low_rank`` is a factor, so its columns already include any desired
    eigenvalue square roots.  This representation has ``O(N K)`` storage and
    never constructs the corresponding ``N x N`` catalogue covariance.
    """

    diagonal: np.ndarray | None = None
    low_rank: np.ndarray | None = None
    dense: np.ndarray | None = None

    def __post_init__(self) -> None:
        supplied = sum(x is not None for x in (self.diagonal, self.dense))
        if supplied != 1:
            raise ValueError("provide exactly one of diagonal or dense covariance")
        if self.dense is not None:
            dense = np.asarray(self.dense, dtype=float)
            if dense.ndim != 2 or dense.shape[0] != dense.shape[1]:
                raise ValueError("dense covariance must be square")
            scale = float(np.max(np.abs(dense)))
            symmetry_tolerance = 64.0 * np.finfo(float).eps * scale
            if not np.all(np.isfinite(dense)) or np.max(np.abs(dense - dense.T)) > symmetry_tolerance:
                raise ValueError("dense covariance must be finite and symmetric")
            dense = 0.5 * (dense + dense.T)
            try:
                np.linalg.cholesky(dense)
            except np.linalg.LinAlgError as exc:
                raise ValueError("sampling covariance must be positive definite") from exc
            if self.low_rank is not None:
                raise ValueError("dense covariance cannot also have low_rank")
            object.__setattr__(self, "dense", dense)
            return
        diagonal = np.asarray(self.diagonal, dtype=float).reshape(-1)
        if diagonal.size == 0 or not np.all(np.isfinite(diagonal)) or np.any(diagonal <= 0.0):
            raise ValueError("covariance diagonal must be finite and > 0")
        low_rank = np.empty((diagonal.size, 0), dtype=float) if self.low_rank is None else np.asarray(self.low_rank, dtype=float)
        if low_rank.ndim != 2 or low_rank.shape[0] != diagonal.size or not np.all(np.isfinite(low_rank)):
            raise ValueError("low_rank must be finite with shape (N, K)")
        object.__setattr__(self, "diagonal", diagonal)
        object.__setattr__(self, "low_rank", low_rank)

    @property
    def size(self) -> int:
        return int(self.dense.shape[0] if self.dense is not None else self.diagonal.size)

    @cached_property
    def _whitening_factors(self):
        if self.dense is not None:
            return np.linalg.cholesky(self.dense)
        with np.errstate(over="ignore", invalid="ignore"):
            z = self.low_rank / np.sqrt(self.diagonal)[:, None]
        eps = np.finfo(float).eps
        limit = 1.0 / (max(self.size, 1) * np.sqrt(eps))
        # Frobenius norm upper-bounds spectral amplification and is invariant
        # under row permutation. Check before QR to avoid nonfinite transforms.
        if (not np.all(np.isfinite(z)) or
                (z.size and np.max(np.abs(z)) > limit) or np.linalg.norm(z) > limit):
            raise ArithmeticError(
                "whitening exceeds finite numerical domain: D-scaled low-rank "
                "dynamic range is unresolved; rescale or supply a stable dense covariance"
            )
        width = min(z.shape)
        reflectors = np.zeros((self.size, width))
        # Thin QR stored as Householder vectors. Applying Q and Q.T retains
        # small off-diagonal rotations that a rounded I-Q Q.T loses.
        for j in range(width):
            v = z[j:, j].copy()
            magnitude = float(np.linalg.norm(v))
            if magnitude == 0:
                continue
            v[0] += np.copysign(magnitude, v[0])
            v /= np.linalg.norm(v)
            reflectors[j:, j] = v
            z[j:, j:] -= 2 * v[:, None] * (v @ z[j:, j:])[None, :]
        rotation, singular, _ = np.linalg.svd(z[:width], full_matrices=False)
        # The D-scaled representation can be ill conditioned even when C
        # itself is benign. Orthogonal-transform roundoff is then amplified
        # by D^-1/2. Reject a conservative range where n*eps*||D^-1/2 U||
        # exceeds sqrt(eps); this is a numerical-domain restriction, not
        # a condition estimate of C or a scientific covariance criterion.
        amplification = float(singular[0]) if singular.size else 0.0
        if not np.isfinite(amplification) or amplification > limit:
            raise ArithmeticError(
                "whitening exceeds finite numerical domain: D-scaled low-rank "
                "dynamic range is unresolved; rescale or supply a stable dense covariance"
            )
        return reflectors, rotation, 1.0 / np.hypot(1.0, singular)

    def whiten(self, rhs: np.ndarray) -> np.ndarray:
        """Apply W with W C W.T = I; thin factors for D+UU.T.

        Covariance arrays must stay fixed after whitening factors are cached.
        StructuredLinearModel owns a read-only snapshot for this reason.
        """
        return self._whiten(rhs, transpose=False)

    def whiten_transpose(self, rhs: np.ndarray) -> np.ndarray:
        """Apply W.T, the adjoint of ``whiten``."""
        return self._whiten(rhs, transpose=True)

    def _whiten(self, rhs, transpose):
        rhs = np.asarray(rhs, dtype=float)
        if rhs.ndim not in (1, 2) or rhs.shape[0] != self.size or not np.all(np.isfinite(rhs)):
            raise ValueError("rhs must be a finite N-vector or N-by-small matrix")
        if self.dense is not None:
            root = self._whitening_factors
            return np.linalg.solve(root.T if transpose else root, rhs)
        scale = 1.0 / np.sqrt(self.diagonal)
        scale = scale[:, None] if rhs.ndim == 2 else scale
        reflectors, rotation, inverse_root = self._whitening_factors
        value = np.array(rhs if transpose else scale * rhs, copy=True)
        width = reflectors.shape[1]
        # Q.T value, attenuation in the small modal span, then Q value.
        for j in range(width):
            v = reflectors[j:, j]
            coeff = v @ value[j:]
            value[j:] -= 2 * (v[:, None] * coeff if rhs.ndim == 2 else v * coeff)
        coeff = rotation.T @ value[:width]
        value[:width] = rotation @ (inverse_root[:, None] * coeff if rhs.ndim == 2 else inverse_root * coeff)
        for j in range(width - 1, -1, -1):
            v = reflectors[j:, j]
            coeff = v @ value[j:]
            value[j:] -= 2 * (v[:, None] * coeff if rhs.ndim == 2 else v * coeff)
        return scale * value if transpose else value

    @property
    def storage_bytes(self) -> int:
        arrays = [x for x in (self.diagonal, self.low_rank, self.dense) if x is not None]
        factors = self.__dict__.get("_whitening_factors")
        if factors is not None:
            arrays.extend(factors if isinstance(factors, tuple) else (factors,))
        return sum(x.nbytes for x in arrays)

    def solve(self, rhs: np.ndarray) -> np.ndarray:
        """Return ``C^-1 rhs`` without materialising a low-rank covariance."""
        rhs = np.asarray(rhs, dtype=float)
        if rhs.shape[0] != self.size:
            raise ValueError("rhs leading dimension is incompatible with covariance")
        if self.dense is not None:
            return np.linalg.solve(self.dense, rhs)
        if self.low_rank.shape[1] == 0:
            return rhs / self.diagonal[:, None] if rhs.ndim == 2 else rhs / self.diagonal
        # Split b into a component in col(U) and its residual. For b = U a,
        # C^-1 b = D^-1 U (I + U.T D^-1 U)^-1 a, which avoids the catastrophic
        # b - U z subtraction in the usual Woodbury expression.
        d = self.diagonal.astype(np.longdouble)
        u = self.low_rank.astype(np.longdouble)
        b = rhs.astype(np.longdouble)
        capacitance = np.eye(u.shape[1], dtype=np.longdouble) + u.T @ (u / d[:, None])
        alpha = np.linalg.lstsq(self.low_rank, rhs, rcond=None)[0].astype(np.longdouble)
        modal = (u / d[:, None]) @ _small_longdouble_solve(capacitance, alpha)
        residual = b - u @ alpha
        inv_d_residual = residual / d[:, None] if residual.ndim == 2 else residual / d
        z = _small_longdouble_solve(capacitance, u.T @ inv_d_residual)
        residual_solution = (residual - u @ z) / d[:, None] if residual.ndim == 2 else (residual - u @ z) / d
        return np.asarray(modal + residual_solution, dtype=float)

    def matmat(self, rhs: np.ndarray) -> np.ndarray:
        """Return ``C rhs``."""
        rhs = np.asarray(rhs, dtype=float)
        if rhs.shape[0] != self.size:
            raise ValueError("rhs leading dimension is incompatible with covariance")
        if self.dense is not None:
            return self.dense @ rhs
        result = self.diagonal[:, None] * rhs if rhs.ndim == 2 else self.diagonal * rhs
        if self.low_rank.shape[1]:
            result = result + self.low_rank @ (self.low_rank.T @ rhs)
        return result

    def logdet(self) -> float:
        if self.dense is not None:
            return float(2.0 * np.log(np.diag(np.linalg.cholesky(self.dense))).sum())
        value = float(np.log(self.diagonal).sum())
        if self.low_rank.shape[1]:
            # log|I + B.T B| = sum_j log(1 + s_j^2).  This SVD form remains
            # stable for redundant columns in U, where a rounded capacitance
            # matrix can lose positive-definiteness despite C being SPD.
            singular_values = np.linalg.svd(
                self.low_rank / np.sqrt(self.diagonal)[:, None],
                compute_uv=False,
            )
            value += float(np.log1p(singular_values ** 2).sum())
        return value

    def marginal_variance(self) -> np.ndarray:
        """Return ``diag(C)`` without constructing a dense low-rank matrix."""
        if self.dense is not None:
            return np.diag(self.dense).copy()
        return self.diagonal + np.einsum("ij,ij->i", self.low_rank, self.low_rank)

    def subset(self, mask: np.ndarray) -> "SamplingCovariance":
        mask = np.asarray(mask)
        if mask.dtype != bool or mask.shape != (self.size,):
            raise ValueError("covariance subset mask must be boolean with shape (N,)")
        if self.dense is not None:
            return SamplingCovariance(dense=self.dense[np.ix_(mask, mask)])
        return SamplingCovariance(diagonal=self.diagonal[mask], low_rank=self.low_rank[mask])


def as_sampling_covariance(value: SamplingCovariance | np.ndarray) -> SamplingCovariance:
    """Normalize an explicit diagonal/dense covariance or existing operator."""
    if isinstance(value, SamplingCovariance):
        return value
    array = np.asarray(value, dtype=float)
    return SamplingCovariance(diagonal=array) if array.ndim == 1 else SamplingCovariance(dense=array)
