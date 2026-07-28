"""Covariance-aware multicomponent response identifiability audit."""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Dict, Iterable, Mapping, Optional, Sequence, Tuple
import numpy as np


@dataclass(frozen=True)
class ResponseAudit:
    rank: int
    dimension: int
    singular_values: np.ndarray
    nullspace: np.ndarray
    projected_response: np.ndarray
    nuisance_rank: int
    tolerance: float
    block_slices: Mapping[str, slice]

    def __post_init__(self) -> None:
        for name in ("rank", "dimension", "nuisance_rank"):
            value = getattr(self, name)
            if isinstance(value, (bool, np.bool_)) or not isinstance(value, int):
                raise ValueError(f"{name} must be an integer")
            if value < 0:
                raise ValueError(f"{name} must be non-negative")
        if self.rank > self.dimension:
            raise ValueError("rank must not exceed dimension")
        tolerance = _nonnegative_real(self.tolerance, "tolerance")
        object.__setattr__(self, "tolerance", tolerance)
        for name in (
            "singular_values",
            "nullspace",
            "projected_response",
        ):
            value = _float_array(getattr(self, name), name)
            value = np.array(value, copy=True)
            value.setflags(write=False)
            object.__setattr__(self, name, value)
        if self.singular_values.ndim != 1:
            raise ValueError("singular_values must be one-dimensional")
        if self.nullspace.ndim != 2 or self.nullspace.shape[0] != self.dimension:
            raise ValueError("nullspace must have one row per parameter")
        if self.nullspace.shape[1] != self.dimension - self.rank:
            raise ValueError("nullspace dimension must equal dimension-rank")
        if (
            self.projected_response.ndim != 2
            or self.projected_response.shape[1] != self.dimension
        ):
            raise ValueError(
                "projected_response must have one column per parameter"
            )
        slices = dict(self.block_slices)
        if any(
            not isinstance(name, str)
            or not name
            or not isinstance(value, slice)
            for name, value in slices.items()
        ):
            raise ValueError("block_slices must map names to slices")
        object.__setattr__(self, "block_slices", MappingProxyType(slices))

    @property
    def identifiable(self) -> bool:
        return self.rank == self.dimension

    def as_dict(self) -> dict:
        return {
            'rank': self.rank,
            'dimension': self.dimension,
            'singular_values': self.singular_values.tolist(),
            'nullspace': self.nullspace.tolist(),
            'nuisance_rank': self.nuisance_rank,
            'tolerance': self.tolerance,
            'identifiable': self.identifiable,
            'block_slices': {k: [v.start, v.stop] for k, v in self.block_slices.items()},
        }


def _contains_bool(value: object) -> bool:
    if isinstance(value, (bool, np.bool_)):
        return True
    if isinstance(value, np.ndarray):
        return value.dtype.kind == "b"
    if isinstance(value, (tuple, list)):
        return any(_contains_bool(item) for item in value)
    return False


def _float_array(value: object, name: str) -> np.ndarray:
    if _contains_bool(value):
        raise ValueError(f"{name} must not contain booleans")
    try:
        out = np.asarray(value, dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc
    if not np.isfinite(out).all():
        raise ValueError(f"{name} must be finite")
    return out


def _nonnegative_real(value: object, name: str) -> float:
    if isinstance(value, (bool, np.bool_)):
        raise ValueError(f"{name} must not be boolean")
    try:
        out = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a real number") from exc
    if not np.isfinite(out) or out < 0.0:
        raise ValueError(f"{name} must be finite and non-negative")
    return out


def _whitener(covariance: np.ndarray, rtol: float = 1e-12) -> np.ndarray:
    c = _float_array(covariance, "covariance")
    rtol = _nonnegative_real(rtol, "rtol")
    if c.ndim != 2 or c.shape[0] != c.shape[1]:
        raise ValueError('covariance must be square')
    if c.shape[0] == 0:
        raise ValueError('covariance must not be empty')
    entry_scale = float(np.max(np.abs(c), initial=0.0))
    symmetry_tolerance = 64.0 * np.finfo(float).eps * entry_scale
    if not np.allclose(c, c.T, atol=symmetry_tolerance, rtol=0):
        raise ValueError('covariance must be symmetric')
    values, vectors = np.linalg.eigh(c)
    scale = float(np.max(np.abs(values), initial=0.0))
    if scale == 0.0:
        raise ValueError('covariance must be positive definite for this audit')
    if float(np.min(values)) <= rtol * scale:
        raise ValueError('covariance must be positive definite for this audit')
    return (vectors / np.sqrt(values)) @ vectors.T


def _rank(a: np.ndarray, rtol: float | None = None) -> tuple[int, np.ndarray, float, np.ndarray]:
    a = _float_array(a, "response")
    if a.ndim != 2:
        raise ValueError("response must be a matrix")
    if rtol is not None:
        rtol = _nonnegative_real(rtol, "rtol")
    u, s, vt = np.linalg.svd(a, full_matrices=True)
    if s.size == 0:
        tol = 0.0
        rank = 0
    else:
        tol = (max(a.shape) * np.finfo(float).eps * s[0]) if rtol is None else rtol * s[0]
        rank = int(np.count_nonzero(s > tol))
    null = vt[rank:].T if vt.shape[0] > rank else np.empty((a.shape[1], 0))
    return rank, s, float(tol), null


def nuisance_projected_response(response: np.ndarray,
                                  covariance: np.ndarray,
                                  nuisance: Optional[np.ndarray] = None) -> tuple[np.ndarray, int]:
    r = _float_array(response, "response")
    if r.ndim != 2:
        raise ValueError('response must be a matrix')
    w = _whitener(covariance)
    rw = w @ r
    if nuisance is None or np.asarray(nuisance).size == 0:
        return rw, 0
    n = _float_array(nuisance, "nuisance")
    if n.ndim != 2 or n.shape[0] != r.shape[0]:
        raise ValueError('nuisance must have the same row count as response')
    nw = w @ n
    u, s, _ = np.linalg.svd(nw, full_matrices=False)
    tol = max(nw.shape) * np.finfo(float).eps * (s[0] if s.size else 1.0)
    nr = int(np.count_nonzero(s > tol))
    q = u[:, :nr]
    projected = rw - q @ (q.T @ rw)
    return projected, nr


def audit_response_blocks(blocks: Mapping[str, np.ndarray],
                          covariance: np.ndarray,
                          nuisance: Optional[np.ndarray] = None,
                          rtol: float | None = None) -> ResponseAudit:
    if not blocks:
        raise ValueError('at least one response block is required')
    slices: Dict[str, slice] = {}
    mats = []
    start = 0
    row_count: int | None = None
    for name, value in blocks.items():
        if not isinstance(name, str) or not name:
            raise ValueError("response block names must be non-empty strings")
        m = _float_array(value, name)
        if m.ndim != 2:
            raise ValueError(f'{name}: response block must be a matrix')
        if row_count is None:
            row_count = m.shape[0]
        elif m.shape[0] != row_count:
            raise ValueError('all response blocks must have the same row count')
        stop = start + m.shape[1]
        slices[name] = slice(start, stop)
        mats.append(m)
        start = stop
    r = np.column_stack(mats)
    rp, nr = nuisance_projected_response(r, covariance, nuisance)
    rank, singular, tol, null = _rank(rp, rtol)
    return ResponseAudit(rank, r.shape[1], singular, null, rp, nr, tol, slices)


def principal_angles(left: np.ndarray, right: np.ndarray,
                     covariance: np.ndarray, nuisance: Optional[np.ndarray] = None) -> np.ndarray:
    left = _float_array(left, "left")
    right = _float_array(right, "right")
    if left.ndim != 2 or right.ndim != 2:
        raise ValueError("left and right must be matrices")
    if left.shape[0] != right.shape[0]:
        raise ValueError("left and right must have the same row count")
    joined = np.column_stack([left, right])
    projected, _ = nuisance_projected_response(joined, covariance, nuisance)
    p = left.shape[1]
    a, b = projected[:, :p], projected[:, p:]
    ua, sa, _ = np.linalg.svd(a, full_matrices=False)
    ub, sb, _ = np.linalg.svd(b, full_matrices=False)
    ta = max(a.shape) * np.finfo(float).eps * (sa[0] if sa.size else 1.0)
    tb = max(b.shape) * np.finfo(float).eps * (sb[0] if sb.size else 1.0)
    qa = ua[:, :int(np.count_nonzero(sa > ta))]
    qb = ub[:, :int(np.count_nonzero(sb > tb))]
    if qa.shape[1] == 0 or qb.shape[1] == 0:
        return np.empty(0)
    cosines = np.linalg.svd(qa.T @ qb, compute_uv=False)
    return np.arccos(np.clip(cosines, -1.0, 1.0))


def rank_gain_ladder(blocks: Mapping[str, np.ndarray], covariance: np.ndarray,
                     nuisance: Optional[np.ndarray] = None) -> list[dict]:
    out = []
    active: Dict[str, np.ndarray] = {}
    for name, block in blocks.items():
        active[name] = block
        audit = audit_response_blocks(active, covariance, nuisance)
        minimum = (
            0.0
            if audit.rank < audit.dimension
            else (
                float(audit.singular_values[-1])
                if audit.singular_values.size
                else 0.0
            )
        )
        out.append({'added': name, 'rank': audit.rank, 'dimension': audit.dimension,
                    'min_singular': minimum})
    return out
