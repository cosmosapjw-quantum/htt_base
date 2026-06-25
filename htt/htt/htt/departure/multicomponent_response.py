"""Covariance-aware multicomponent response identifiability audit."""
from __future__ import annotations

from dataclasses import dataclass
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


def _whitener(covariance: np.ndarray, rtol: float = 1e-12) -> np.ndarray:
    c = np.asarray(covariance, dtype=float)
    if c.ndim != 2 or c.shape[0] != c.shape[1]:
        raise ValueError('covariance must be square')
    if not np.allclose(c, c.T, atol=1e-12, rtol=0):
        raise ValueError('covariance must be symmetric')
    values, vectors = np.linalg.eigh(c)
    scale = max(1.0, float(np.max(np.abs(values))))
    if float(np.min(values)) <= rtol * scale:
        raise ValueError('covariance must be positive definite for this audit')
    return (vectors / np.sqrt(values)) @ vectors.T


def _rank(a: np.ndarray, rtol: float | None = None) -> tuple[int, np.ndarray, float, np.ndarray]:
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
    r = np.asarray(response, dtype=float)
    if r.ndim != 2:
        raise ValueError('response must be a matrix')
    w = _whitener(covariance)
    rw = w @ r
    if nuisance is None or np.asarray(nuisance).size == 0:
        return rw, 0
    n = np.asarray(nuisance, dtype=float)
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
    row_counts = {np.asarray(v).shape[0] for v in blocks.values()}
    if len(row_counts) != 1:
        raise ValueError('all response blocks must have the same row count')
    slices: Dict[str, slice] = {}
    mats = []
    start = 0
    for name, value in blocks.items():
        m = np.asarray(value, dtype=float)
        if m.ndim != 2:
            raise ValueError(f'{name}: response block must be a matrix')
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
    joined = np.column_stack([left, right])
    projected, _ = nuisance_projected_response(joined, covariance, nuisance)
    p = np.asarray(left).shape[1]
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
        out.append({'added': name, 'rank': audit.rank, 'dimension': audit.dimension,
                    'min_singular': float(audit.singular_values[-1]) if audit.singular_values.size else 0.0})
    return out
