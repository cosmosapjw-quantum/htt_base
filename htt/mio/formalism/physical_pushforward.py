"""Explicit legacy pushforward from multicomponent states to scalar projections.

The module does not infer missing physical components and does not reinterpret
legacy variables.  Inputs named ``Sigma_standard`` etc. must already follow the
legacy report's registered convention. It is not part of the active
``mio.formalism`` namespace.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Mapping, Optional, Sequence
import hashlib
import json
import warnings
import numpy as np

from common.statistical_foundations import (
    BC1_LEGACY_PROJECTION,
    BC2_NO_REPRESENTATION_PROMOTION,
    BudgetRadiusResult,
    BudgetRadiusStatus,
    ScalarRange,
)

LEGACY_REPRODUCTION_ONLY = True

warnings.warn(
    "mio.formalism.physical_pushforward is a legacy reproduction adapter; "
    "use typed state and identified-set contracts for active analysis",
    DeprecationWarning,
    stacklevel=2,
)

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
    classification: str = BC1_LEGACY_PROJECTION
    representation_policy: str = BC2_NO_REPRESENTATION_PROMOTION
    allowed_use: tuple[str, ...] = ("historical reproduction",)
    forbidden_use: tuple[str, ...] = (
        "departure distance",
        "occupancy",
        "probability",
        "evidence",
        "family identification",
    )

    def as_dict(self) -> dict:
        return {
            'name': self.name, 'status': self.status,
            'definition_id': self.definition_id, 'summary': dict(self.summary),
            'assumptions': list(self.assumptions),
            'missing_components': list(self.missing_components),
            'identified_components': list(self.identified_components),
            'claim_tier': self.claim_tier, 'source_hash': self.source_hash,
            'message': self.message,
            'classification': self.classification,
            'representation_policy': self.representation_policy,
            'allowed_use': list(self.allowed_use),
            'forbidden_use': list(self.forbidden_use),
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
                                      claim_tier: str = 'diagnostic_legacy_reproduction',
                                      *,
                                      legacy_reproduction: bool = False
                                      ) -> dict[str, PushforwardResult]:
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
    if claim_tier != 'diagnostic_legacy_reproduction':
        warnings.warn(
            "legacy pushforward claim_tier is fixed to diagnostic reproduction",
            DeprecationWarning,
            stacklevel=2,
        )
    xr = PushforwardResult(
        'x_C',
        'OK',
        'legacy_signed_defect_v1',
        _summary(x),
        tuple(assumptions),
        (),
        required,
        'diagnostic_legacy_reproduction',
        source,
    )
    out = {'x_C': xr}
    if x_max is not None:
        if not legacy_reproduction:
            out['Q'] = PushforwardResult(
                'Q',
                'BLOCKED_UNTYPED_DENOMINATOR',
                'legacy_Q_v1',
                assumptions=tuple(assumptions),
                source_hash=source,
                message=(
                    'A bare x_max cannot create an active ratio; set '
                    'legacy_reproduction=True only for frozen compatibility.'
                ),
            )
        elif not np.isfinite(x_max) or x_max <= 0:
            out['Q'] = PushforwardResult('Q', 'BLOCKED_INVALID_DENOMINATOR', 'legacy_Q_v1',
                                         assumptions=tuple(assumptions), source_hash=source)
        else:
            out['Q'] = PushforwardResult('Q', 'OK', 'legacy_Q_v1', _summary(x/x_max),
                                         tuple(assumptions), (), required,
                                         'diagnostic_legacy_reproduction', source)
    return out


def registered_callable_pushforward(name: str, samples: Mapping[str, np.ndarray],
                                    required: Sequence[str], function: Callable[..., np.ndarray],
                                    definition_id: str, assumptions: Sequence[str] = (),
                                    claim_tier: str = 'diagnostic') -> PushforwardResult:
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


def ratio_pushforward(
    name: str,
    numerator: np.ndarray,
    denominator: np.ndarray,
    definition_id: str,
    *,
    denominator_interval: ScalarRange | None = None,
    atol: float | None = None,
    rtol: float | None = None,
    assumptions: Sequence[str] = (),
    legacy_reproduction: bool = False,
) -> PushforwardResult:
    n, d = np.broadcast_arrays(np.asarray(numerator, dtype=float), np.asarray(denominator, dtype=float))
    source = _source_hash({'numerator': n, 'denominator': d})
    if not legacy_reproduction:
        return PushforwardResult(
            name,
            'BLOCKED_UNTYPED_DENOMINATOR',
            definition_id,
            assumptions=tuple(assumptions),
            source_hash=source,
            message='Raw-array ratios are legacy reproduction only.',
        )
    if denominator_interval is None or atol is None or rtol is None:
        return PushforwardResult(
            name,
            'RATIO_UNIDENTIFIED',
            definition_id,
            assumptions=tuple(assumptions),
            source_hash=source,
            message='An identified denominator interval and atol/rtol are required.',
        )
    if not denominator_interval.separated_from_zero(atol=atol, rtol=rtol):
        return PushforwardResult(
            name,
            'RATIO_UNIDENTIFIED',
            definition_id,
            assumptions=tuple(assumptions),
            source_hash=source,
            message='Denominator identified interval intersects the zero tolerance.',
        )
    tolerance = float(atol) + float(rtol) * max(
        float(np.max(np.abs(d))),
        1.0,
    )
    if np.any(np.abs(d) <= tolerance):
        return PushforwardResult(name, 'RATIO_UNIDENTIFIED', definition_id,
                                 assumptions=tuple(assumptions), source_hash=source,
                                 message='Point denominator enters the zero-tolerance branch.')
    return PushforwardResult(name, 'OK', definition_id, _summary(n/d), tuple(assumptions),
                             identified_components=('numerator','denominator'),
                             claim_tier='diagnostic_legacy_reproduction',
                             source_hash=source)


def matrix_budget_radius_report(
    samples: np.ndarray, budget: np.ndarray, rcond: float = 1e-12
) -> BudgetRadiusResult:
    """Return supported quotient radius and explicit null-space residual.

    A singular PSD budget defines a quotient geometry, not a free zero-cost
    direction.  The supported component receives ``x^T U^+ x`` while the
    Euclidean norm of the orthogonal null component is reported separately.
    """
    raw_x = np.asarray(samples, dtype=object)
    raw_u = np.asarray(budget, dtype=object)
    if any(isinstance(value, (bool, np.bool_)) for value in raw_x.flat):
        raise ValueError("samples must not contain boolean coordinates")
    if any(isinstance(value, (bool, np.bool_)) for value in raw_u.flat):
        raise ValueError("budget must not contain boolean entries")
    x = np.asarray(samples, dtype=float)
    u = np.asarray(budget, dtype=float)
    if x.ndim == 1:
        x = x[None, :]
    if x.ndim != 2 or x.shape[0] == 0 or not np.all(np.isfinite(x)):
        raise ValueError("samples must be a non-empty finite vector/matrix")
    if isinstance(rcond, (bool, np.bool_)) or not np.isfinite(rcond) or rcond <= 0:
        raise ValueError("rcond must be a finite positive real")
    if u.shape != (x.shape[1], x.shape[1]):
        raise ValueError('budget must be a symmetric square matrix matching sample dimension')
    if not np.all(np.isfinite(u)):
        raise ValueError("budget must be finite")
    matrix_scale = float(np.max(np.abs(u)))
    symmetry_atol = rcond * matrix_scale
    if not np.allclose(u, u.T, atol=symmetry_atol, rtol=rcond):
        raise ValueError('budget must be a symmetric square matrix matching sample dimension')
    values, vectors = np.linalg.eigh(u)
    spectral_scale = float(np.max(np.abs(values)))
    if spectral_scale == 0.0:
        supported = np.zeros_like(values, dtype=bool)
    else:
        if float(np.min(values)) < -rcond * spectral_scale:
            raise ValueError('budget matrix is not positive semidefinite')
        supported = values > rcond * spectral_scale
    if spectral_scale == 0.0 and float(np.min(values)) < 0.0:
        raise ValueError('budget matrix is not positive semidefinite')
    inv = np.zeros_like(values)
    np.divide(1.0, values, out=inv, where=supported)
    pinv = (vectors * inv) @ vectors.T
    radius = np.einsum('ni,ij,nj->n', x, pinv, x)
    null_basis = vectors[:, ~supported]
    if null_basis.size:
        null_residual = np.linalg.norm(x @ null_basis, axis=1)
    else:
        null_residual = np.zeros(x.shape[0], dtype=float)
    threshold = rcond * max(1.0, float(np.linalg.norm(x, ord=2)))
    status = (
        BudgetRadiusStatus.NULL_RESIDUAL_PRESENT
        if np.any(null_residual > threshold)
        else BudgetRadiusStatus.DEFINED
    )
    return BudgetRadiusResult(
        radius_sq=tuple(float(value) for value in radius),
        rank=int(np.count_nonzero(supported)),
        null_residual=tuple(float(value) for value in null_residual),
        status=status,
    )


def matrix_budget_radius(
    samples: np.ndarray, budget: np.ndarray, rcond: float = 1e-12
) -> np.ndarray:
    """Legacy float-array wrapper; use :func:`matrix_budget_radius_report`."""
    warnings.warn(
        "matrix_budget_radius hides rank/null metadata; use "
        "matrix_budget_radius_report",
        DeprecationWarning,
        stacklevel=2,
    )
    return np.asarray(
        matrix_budget_radius_report(samples, budget, rcond).radius_sq,
        dtype=float,
    )
