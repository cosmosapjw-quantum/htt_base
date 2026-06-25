"""Fail-closed pushforward from identified multicomponent states to legacy scalars.

The module does not infer missing physical components and does not reinterpret
legacy variables.  Inputs named ``Sigma_standard`` etc. must already follow the
legacy report's registered convention.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Mapping, Optional, Sequence
import hashlib
import json
import numpy as np


@dataclass(frozen=True)
class PushforwardResult:
    name: str
    status: str
    definition_id: str
    summary: Mapping[str, float] = field(default_factory=dict)
    assumptions: tuple[str, ...] = ()
    missing_components: tuple[str, ...] = ()
    identified_components: tuple[str, ...] = ()
    claim_tier: str = 'diagnostic'
    source_hash: str = ''
    message: str = ''

    def as_dict(self) -> dict:
        return {
            'name': self.name, 'status': self.status,
            'definition_id': self.definition_id, 'summary': dict(self.summary),
            'assumptions': list(self.assumptions),
            'missing_components': list(self.missing_components),
            'identified_components': list(self.identified_components),
            'claim_tier': self.claim_tier, 'source_hash': self.source_hash,
            'message': self.message,
        }


def _source_hash(samples: Mapping[str, np.ndarray]) -> str:
    h = hashlib.sha256()
    for key in sorted(samples):
        h.update(key.encode())
        h.update(np.asarray(samples[key], dtype=float).tobytes())
    return h.hexdigest()


def _summary(x: np.ndarray) -> dict:
    q = np.quantile(np.asarray(x, dtype=float), [0.025, 0.16, 0.5, 0.84, 0.975])
    return {'q025': float(q[0]), 'q16': float(q[1]), 'median': float(q[2]),
            'q84': float(q[3]), 'q975': float(q[4]), 'mean': float(np.mean(x)),
            'std': float(np.std(x, ddof=1)) if np.size(x) > 1 else 0.0}


def legacy_signed_defect_pushforward(samples: Mapping[str, np.ndarray],
                                      x_max: Optional[float] = None,
                                      assumptions: Sequence[str] = (),
                                      claim_tier: str = 'conditional_inference') -> dict[str, PushforwardResult]:
    """Registered legacy relation

    ``x_C = Sigma_standard - W_standard + Omega_tilt + Omega_k_aniso``.

    Each named input is the *already normalized legacy component*.  This
    function deliberately performs no hidden square, unit conversion, or
    sector substitution.
    """
    required = ('Sigma_standard', 'W_standard', 'Omega_tilt', 'Omega_k_aniso')
    missing = tuple(k for k in required if k not in samples)
    source = _source_hash(samples)
    if missing:
        blocked = PushforwardResult(
            name='x_C', status='BLOCKED_UNIDENTIFIED_COMPONENTS',
            definition_id='legacy_signed_defect_v1', assumptions=tuple(assumptions),
            missing_components=missing,
            identified_components=tuple(k for k in required if k in samples),
            source_hash=source, message='No missing component was imputed or set to zero.',
        )
        return {'x_C': blocked}
    arrays = [np.asarray(samples[k], dtype=float) for k in required]
    arrays = np.broadcast_arrays(*arrays)
    x = arrays[0] - arrays[1] + arrays[2] + arrays[3]
    xr = PushforwardResult('x_C', 'OK', 'legacy_signed_defect_v1', _summary(x),
                           tuple(assumptions), (), required, claim_tier, source)
    out = {'x_C': xr}
    if x_max is not None:
        if not np.isfinite(x_max) or x_max <= 0:
            out['Q'] = PushforwardResult('Q', 'BLOCKED_INVALID_DENOMINATOR', 'legacy_Q_v1',
                                         assumptions=tuple(assumptions), source_hash=source)
        else:
            out['Q'] = PushforwardResult('Q', 'OK', 'legacy_Q_v1', _summary(x/x_max),
                                         tuple(assumptions), (), required, claim_tier, source)
    return out


def registered_callable_pushforward(name: str, samples: Mapping[str, np.ndarray],
                                    required: Sequence[str], function: Callable[..., np.ndarray],
                                    definition_id: str, assumptions: Sequence[str] = (),
                                    claim_tier: str = 'conditional_inference') -> PushforwardResult:
    missing = tuple(k for k in required if k not in samples)
    source = _source_hash(samples)
    if missing:
        return PushforwardResult(name, 'BLOCKED_UNIDENTIFIED_COMPONENTS', definition_id,
                                 assumptions=tuple(assumptions), missing_components=missing,
                                 identified_components=tuple(k for k in required if k in samples),
                                 source_hash=source)
    values = np.asarray(function(**{k: np.asarray(samples[k], dtype=float) for k in required}), dtype=float)
    if not np.all(np.isfinite(values)):
        return PushforwardResult(name, 'BLOCKED_NONFINITE_TRANSFORM', definition_id,
                                 assumptions=tuple(assumptions), source_hash=source)
    return PushforwardResult(name, 'OK', definition_id, _summary(values), tuple(assumptions),
                             (), tuple(required), claim_tier, source)


def ratio_pushforward(name: str, numerator: np.ndarray, denominator: np.ndarray,
                      definition_id: str, zero_guard: float = 1e-12,
                      assumptions: Sequence[str] = ()) -> PushforwardResult:
    n, d = np.broadcast_arrays(np.asarray(numerator, dtype=float), np.asarray(denominator, dtype=float))
    source = _source_hash({'numerator': n, 'denominator': d})
    if np.any(np.abs(d) <= zero_guard):
        return PushforwardResult(name, 'BLOCKED_ZERO_DENOMINATOR_BRANCH', definition_id,
                                 assumptions=tuple(assumptions), source_hash=source,
                                 message='Use a reference-free contrast on this branch.')
    return PushforwardResult(name, 'OK', definition_id, _summary(n/d), tuple(assumptions),
                             identified_components=('numerator','denominator'), source_hash=source)


def matrix_budget_radius(samples: np.ndarray, budget: np.ndarray, rcond: float = 1e-12) -> np.ndarray:
    """Return x^T U^+ x for vector/tensor samples and a PSD budget matrix U."""
    x = np.asarray(samples, dtype=float)
    u = np.asarray(budget, dtype=float)
    if x.ndim == 1:
        x = x[None, :]
    if u.shape != (x.shape[1], x.shape[1]) or not np.allclose(u, u.T, atol=1e-12, rtol=0):
        raise ValueError('budget must be a symmetric square matrix matching sample dimension')
    values, vectors = np.linalg.eigh(u)
    scale = max(1.0, float(np.max(np.abs(values))))
    if float(np.min(values)) < -rcond*scale:
        raise ValueError('budget matrix is not positive semidefinite')
    inv = np.where(values > rcond*scale, 1.0/values, 0.0)
    pinv = (vectors * inv) @ vectors.T
    return np.einsum('ni,ij,nj->n', x, pinv, x)
