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


@dataclass(frozen=True)
class PosteriorDrawSource:
    """A supplied finite posterior representation, bound to inference inputs.

    This record does not establish that the likelihood, prior or sampler was
    scientifically adequate; that obligation belongs to the producing OA09 fit.
    """
    posterior_id: str
    conditioning_source_id: str
    likelihood_id: str
    prior_id: str
    draw_ids: tuple[str, ...]
    weights: tuple[float, ...]
    congruence: str
    comparator_id: str
    units: str = 'dimensionless'
    branch: str = 'SIGNED'
    distance_state_sha256: str | None = None

    def __post_init__(self):
        required=(self.posterior_id,self.conditioning_source_id,self.likelihood_id,
                  self.prior_id,self.congruence,self.comparator_id)
        if any(not isinstance(x,str) or not x.strip() for x in required):
            raise ValueError('posterior source, likelihood, prior and physical convention IDs required')
        if (not self.draw_ids or len(set(self.draw_ids))!=len(self.draw_ids)
                or any(not isinstance(x,str) or not x.strip() for x in self.draw_ids)):
            raise ValueError('unique ordered posterior draw IDs required')
        w=np.asarray(self.weights,dtype=float)
        if (w.shape!=(len(self.draw_ids),) or not np.isfinite(w).all() or np.any(w<0)
                or abs(float(w.sum())-1.)>64*np.finfo(float).eps):
            raise ValueError('proper supplied normalized posterior draw weights required')
        if self.units!='dimensionless' or self.branch!='SIGNED':
            raise ValueError('legacy signed dimensionless sector contract required')


def conditional_legacy_image(draws, adapter, *, source_id, joint_id, weights,
                             law_kind, q_thresholds=(0.1,), depth_representation=None,
                             covariance=None, covariance_blocks=None):
    """The original scenario-only interface; POSTERIOR remains refused here."""
    if law_kind not in {'SAMPLING','FINITE_SET'}:
        raise ValueError('conditional diagnostic requires SAMPLING or FINITE_SET')
    return _legacy_image(draws,adapter,source_id=source_id,joint_id=joint_id,
        weights=weights,law_kind=law_kind,q_thresholds=q_thresholds,
        depth_representation=depth_representation,covariance=covariance,
        covariance_blocks=covariance_blocks)


def posterior_legacy_image(draws, adapter, posterior_source: PosteriorDrawSource, *,
                           q_thresholds=(0.1,), depth_representation=None,
                           covariance=None, covariance_blocks=None):
    """Push forward supplied OA09 posterior atoms without changing ID or mass."""
    if not isinstance(posterior_source,PosteriorDrawSource):
        raise TypeError('typed source-bound posterior required')
    draws=tuple(draws)
    if tuple(d.latent_id for d in draws)!=posterior_source.draw_ids:
        raise ValueError('posterior draw order/identity mismatch')
    if (adapter.contract.congruence!=posterior_source.congruence
            or adapter.contract.comparator_id!=posterior_source.comparator_id):
        raise ValueError('posterior and legacy physical contract mismatch')
    result=_legacy_image(draws,adapter,source_id=posterior_source.conditioning_source_id,
        joint_id=posterior_source.posterior_id,weights=posterior_source.weights,
        law_kind='POSTERIOR',q_thresholds=q_thresholds,
        depth_representation=depth_representation,covariance=covariance,
        covariance_blocks=covariance_blocks)
    return dict(result,posterior_source=posterior_source,
                claim_status='CONDITIONAL_IMAGE_OF_SUPPLIED_POSTERIOR_SCIENTIFIC_ADMISSION_HOLD')


def _legacy_image(draws, adapter, *, source_id, joint_id, weights,
                  law_kind, q_thresholds, depth_representation,
                  covariance, covariance_blocks):
    """Preserve IDs, original measure, signed x and samplewise Q denominators.

    SAMPLING weights describe a caller-specified finite scenario sampling law.
    FINITE_SET carries no probability mass. An actual posterior must use a
    separately justified inference interface. Missing sectors remain undefined.
    Depth is a same-draw feature contrast, never an empirical H(d) or q(d).
    """
    if law_kind not in {'SAMPLING', 'FINITE_SET', 'POSTERIOR'}:
        raise ValueError('unsupported finite draw law')
    if not isinstance(source_id, str) or not source_id.strip():
        raise ValueError('source identity required')
    draws = tuple(draws)
    if not draws or any(not isinstance(d, ConditionalDraw) for d in draws):
        raise ValueError('nonempty typed draws required')
    if law_kind == 'FINITE_SET' and weights is not None:
        raise ValueError('finite set has no probability weights')
    if law_kind in {'SAMPLING','POSTERIOR'} and weights is None:
        raise ValueError('explicit finite probability weights required')
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


def distance_state_digest(source, omega_m, h0_rd, redshift, radial_integral, light_speed=299792.458):
    """Bind ordered numerical distance state AND supplied posterior measure.

    This identity does not validate the producing inference or physical sectors.
    """
    import hashlib,json
    h=hashlib.sha256()
    identity=[source.posterior_id,source.conditioning_source_id,source.likelihood_id,
              source.prior_id,source.congruence,source.comparator_id,source.units,source.branch]
    h.update(json.dumps(identity,separators=(',',':')).encode())
    for draw_id in source.draw_ids:
        payload=draw_id.encode();h.update(len(payload).to_bytes(8,'little'));h.update(payload)
    for value in (source.weights,omega_m,h0_rd,redshift,radial_integral,[light_speed]):
        if np.iscomplexobj(value):raise ValueError('real distance state required')
        array=np.ascontiguousarray(value,dtype='<f8')
        h.update(json.dumps(array.shape).encode());h.update(array.view(np.uint8))
    return h.hexdigest()


def posterior_distance_image(posterior_source: PosteriorDrawSource, omega_m, h0_rd, *,
                             redshift, radial_integral, light_speed=299792.458):
    """Distance-only image of one supplied finite posterior measure.

    Each row is the original posterior atom.  ``radial_integral`` contains
    integral_0^z dz/E(z) for that same row; callers must not permute rows or
    resample the measure.  No legacy physical sector is inferred from FLRW
    distance parameters.  This interface is separate from ``posterior_legacy_image``
    because no physical legacy adapter contract is available here.
    """
    if not isinstance(posterior_source, PosteriorDrawSource):
        raise TypeError('typed posterior source required')
    if posterior_source.congruence!='FLAT_LCDM_DISTANCE' or posterior_source.comparator_id!='DISTANCE_ONLY':
        raise ValueError('flat-LCDM distance model/comparator binding required')
    if any(np.iscomplexobj(v) for v in (omega_m,h0_rd,redshift,radial_integral,light_speed)):
        raise ValueError('real distance states required')
    expected=distance_state_digest(posterior_source,omega_m,h0_rd,redshift,radial_integral,light_speed)
    if not posterior_source.distance_state_sha256 or posterior_source.distance_state_sha256!=expected:
        raise ValueError('posterior numerical state/measure binding mismatch')
    n = len(posterior_source.draw_ids)
    omega = np.asarray(omega_m, dtype=float)
    ar = np.asarray(h0_rd, dtype=float)
    z = np.asarray(redshift, dtype=float)
    integral = np.asarray(radial_integral, dtype=float)
    if (omega.shape != (n,) or ar.shape != (n,) or z.ndim != 1
            or integral.shape != (n, len(z)) or not len(z)
            or not np.isfinite(omega).all() or not np.isfinite(ar).all()
            or not np.isfinite(z).all() or not np.isfinite(integral).all()
            or np.any(omega <= 0) or np.any(omega >= 1) or np.any(ar <= 0)
            or np.any(z <= 0) or np.any(integral <= 0)
            or not np.isfinite(light_speed) or light_speed <= 0):
        raise ValueError('aligned finite interior posterior distance states required')
    from numpy.polynomial.legendre import leggauss
    nodes,node_weights=leggauss(48)
    unique,index=np.unique(omega,return_inverse=True)
    t=z[:,None]*(nodes[None,:]+1)/2
    inverse_E=1/np.sqrt(unique[:,None,None]*(1+t[None,:,:])**3+1-unique[:,None,None])
    reference=np.sum(inverse_E*node_weights[None,None,:],axis=2)*z[None,:]/2
    if not np.allclose(integral,reference[index],rtol=1e-10,atol=1e-12):
        raise ValueError('radial integral/model row pairing mismatch')
    zp = 1 + z[None, :]
    e = np.sqrt(omega[:, None] * zp**3 + 1 - omega[:, None])
    h0_dl_c = zp * integral
    h0_da_c = integral / zp
    if not np.allclose(h0_dl_c, zp**2 * h0_da_c, rtol=2e-14, atol=0):
        raise ArithmeticError('distance reciprocity failed')
    with np.errstate(over='ignore',divide='ignore',invalid='ignore'):
        dm=light_speed*integral/ar[:,None]
        dh=light_speed/(ar[:,None]*e)
        decel=1.5*omega[:,None]*zp**3/e**2-1
    if not all(np.isfinite(v).all() for v in (e,h0_dl_c,h0_da_c,dm,dh,decel)):
        raise ValueError('nonfinite derived distance image')
    return {
        'posterior_source': posterior_source,
        'draw_ids': posterior_source.draw_ids,
        'weights': posterior_source.weights,
        'redshift': z,
        'E': e,
        'q_deceleration': decel,
        'H0_DL_over_c': h0_dl_c,
        'H0_DA_over_c': h0_da_c,
        'DM_over_rd': dm,
        'DH_over_rd': dh,
        'physical_sector': {
            name: {'status': 'UNAVAILABLE', 'unknown_mass': 1.0}
            for name in ('Sigma2', 'W2', 'Omega_tilt', 'curvature_delta',
                         'x_ceiling', 'x', 'Q', 'Pi', 'F', 'G')
        },
        'claim_status': 'CONDITIONAL_DISTANCE_IMAGE_PHYSICAL_MES_HOLD',
    }
