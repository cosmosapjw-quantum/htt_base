"""Source-bound finite sampling diagnostics; no physical posterior is constructed."""
from dataclasses import dataclass
import numpy as np
from common.typefree_functionals import (FunctionalSpec, FunctionalRecord,
    FiniteJointSource, UndefinedValue, finite_joint_pushforward)
from common.typefree_depth import signed_depth_transport


@dataclass(frozen=True)
class ConditionalDraw:
    latent_id: str
    Sigma2: float | None
    W2: float | None
    Omega_tilt: float | None
    curvature_delta: float | None
    x_ceiling: float | None
    identifiable: bool = True
    depth_records: tuple[FunctionalRecord, ...] = ()


def conditional_legacy_image(draws, adapter, *, source_id, joint_id, weights,
                             law_kind, q_thresholds=(0.1,), depth_representation=None,
                             covariance=None, covariance_blocks=None):
    """Preserve IDs, original measure, signed x and samplewise Q denominators.

    SAMPLING weights describe a caller-specified finite scenario sampling law.
    FINITE_SET carries no probability mass. An actual posterior must use a
    separately justified inference interface. Missing sectors remain undefined.
    Depth is a same-draw feature contrast, never an empirical H(d) or q(d).
    """
    if law_kind not in {'SAMPLING', 'FINITE_SET'}:
        raise ValueError('conditional diagnostic requires SAMPLING or FINITE_SET')
    if not isinstance(source_id, str) or not source_id.strip():
        raise ValueError('source identity required')
    draws = tuple(draws)
    if not draws or any(not isinstance(d, ConditionalDraw) for d in draws):
        raise ValueError('nonempty typed draws required')
    if law_kind == 'FINITE_SET' and weights is not None:
        raise ValueError('finite set has no probability weights')
    if law_kind == 'SAMPLING' and weights is None:
        raise ValueError('explicit scenario weights required')
    if any(type(d.identifiable) is not bool for d in draws):
        raise ValueError('explicit Boolean identifiability required')
    for d in draws:
        if not d.latent_id or d.latent_id != d.latent_id.strip():
            raise ValueError('draw ID required')
        if d.depth_records and any(r.latent_id != d.latent_id for r in d.depth_records):
            raise ValueError('depth records must retain draw ID')
    spec = FunctionalSpec('conditional-legacy-paired-v1', ('draw',), (1,), 0,
        'SIGNED', 'scalar', 'dimensionless', adapter.contract.congruence,
        'source-declared', source_id, 'VA-02', 'source-conditional', 'signed')
    records = tuple(FunctionalRecord(d.latent_id, spec, np.array([i]), np.array([0]))
                    for i, d in enumerate(draws))
    # Normalize safely before the existing finite source constructor.
    raw_weights = np.ones(len(draws)) if weights is None else np.asarray(weights, float)
    if (raw_weights.shape != (len(draws),) or not np.isfinite(raw_weights).all()
            or np.any(raw_weights < 0) or raw_weights.max() <= 0):
        raise ValueError('finite nonnegative weights with positive total required')
    scaled = raw_weights / raw_weights.max()
    source = FiniteJointSource(joint_id, records, law_kind, source_id,
        None if law_kind == 'FINITE_SET' else tuple(scaled))
    column = lambda name: [np.nan if getattr(d, name) is None else getattr(d, name) for d in draws]
    result = adapter.departure_pushforward(Sigma2=column('Sigma2'), W2=column('W2'),
        Omega_tilt=column('Omega_tilt'), curvature_delta=column('curvature_delta'),
        x_ceiling=column('x_ceiling'), weights=scaled,
        identifiable=[d.identifiable for d in draws], q_thresholds=q_thresholds)
    def image(name):
        return finite_joint_pushforward(source,
            lambda r: result[name][int(r.values[0])] if np.isfinite(result[name][int(r.values[0])])
            else UndefinedValue('MISSING_SECTOR_OR_INVALID_DOMAIN'),
            definition_id='legacy-signed-'+name, target_domain_id=source_id)
    depth = ()
    if depth_representation is not None:
        if any(not d.depth_records for d in draws):
            raise ValueError('explicit available/unavailable depth records required for every draw')
        baseline_specs = tuple(r.spec for r in draws[0].depth_records)
        if any(tuple(r.spec for r in d.depth_records) != baseline_specs for d in draws[1:]):
            raise ValueError('cross-draw depth specs must match at every corresponding block')
        depth = tuple(signed_depth_transport(d.depth_records, depth_representation,
            transport_definition_id=depth_representation.procedure_id,
            covariance=covariance, covariance_blocks=covariance_blocks) for d in draws)
    elif any(d.depth_records for d in draws):
        raise ValueError('depth representation required')
    depth_image = None
    if depth:
        depth_image = finite_joint_pushforward(source,
            lambda r: depth[int(r.values[0])].contrasts
            if depth[int(r.values[0])].contrasts is not None
            else UndefinedValue(depth[int(r.values[0])].status),
            definition_id='signed-depth-feature-contrast', target_domain_id=source_id)
    return {'source_id': source_id, 'joint_id': joint_id, 'law_kind': law_kind,
        'draw_ids': tuple(d.latent_id for d in draws), 'x': image('x'), 'Q': image('Q'),
        'Pi_intervals': None if law_kind == 'FINITE_SET' else result['Pi_intervals'],
        'depth': depth, 'depth_image': depth_image, 'contract': result['contract'], 'source_sha256': result['source_sha256'],
        'denominator_mode': 'SAMPLEWISE_CALLER_SUPPLIED_SHEAR_CEILING',
        'units': 'dimensionless', 'comparator': adapter.contract.comparator_id,
        'branch': 'SIGNED', 'event': 'Q > threshold', 'claim_status': 'HOLD_ACTUAL_FIT',
        'F4': None, 'filling_fraction': None, 'physical_H_d': None, 'physical_q_d': None}
