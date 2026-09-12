"""Fixed-law set composition and same-state outer images, without optimizers."""
from dataclasses import dataclass,replace
from fractions import Fraction as F
import math
import numpy as np
from common.r8_jet_set import TensorImage,support,array,rational,sqrt_bounds
from common.r7_contracts import NumericalUnresolved
from .r7_confidence import PhysicalRegion,PhysicalDomain,BoundCertificate,combine_regions
from .r7_mes_region import AffineRatioFunctional,affine_box_gf_bound

FIXED_INTEGRATED_ALLOCATION={'CMB':F(1,80),'CF4':F(1,80),'distance_calibration':F(1,80),'DESI':F(1,80)}


@dataclass(frozen=True)
class CompatibleTuple:
    tuple_id:str
    domain:PhysicalDomain
    measurement_keys:dict


@dataclass(frozen=True)
class JointPhysicalRegion(PhysicalRegion):
    model_tuples:tuple=()
    def outer_contains(self,theta,eta=None):
        v=self.evaluate(theta,eta)
        return v.accepted or v.numeric_status=='NUMERICALLY_UNRESOLVED'


@dataclass(frozen=True)
class LinearTarget:
    functional_id:str
    coefficients:object
    constant:object=F(0)
    def __post_init__(self):
        c=array(self.coefficients)
        if c.ndim!=1 or not self.functional_id:raise ValueError('named ordered linear target required')
        c.setflags(write=False);object.__setattr__(self,'coefficients',c);object.__setattr__(self,'constant',rational(self.constant))
    def __call__(self,x):return self.constant+sum(self.coefficients*array(x))


def outer_region(measurements,admitted_tuples,allocation):
    tuples=tuple(admitted_tuples)
    if not tuples or not allocation or any(not isinstance(a,F) or not 0<a<1 for a in allocation.values()) or sum(allocation.values())>F(1,20):
        raise ValueError('nonempty compatible tuples and fixed exact total alpha<=.05 required')
    if len({t.tuple_id for t in tuples})!=len(tuples):raise ValueError('unique tuple IDs required')
    names=tuples[0].domain.parameter_names;parts=[]
    for t in tuples:
        if t.domain.parameter_names!=names or set(t.measurement_keys)-set(allocation):raise ValueError('same ordered estimand and fixed allocation required')
        keys=list(t.measurement_keys.values())
        if len(set(keys))!=len(keys):raise ValueError('one measurement cannot be counted under two scopes')
        regions=[measurements.get(t.measurement_keys.get(scope)) for scope in allocation]
        if any(r is not None and not isinstance(r,PhysicalRegion) for r in regions):raise TypeError('actual scoped acceptance regions required; factories have no coverage')
        parts.append(combine_regions(regions,t.domain,mode='MARGINAL_UNION_BOUND',fixed_alphas=list(allocation.values())))
    domains=[t.domain for t in tuples]
    bounds=None if any(d.bounds is None for d in domains) else tuple((min(d.bounds[i][0] for d in domains),max(d.bounds[i][1] for d in domains)) for i in range(len(names)))
    union_domain=PhysicalDomain('R8_UNION:'+':'.join(t.tuple_id for t in tuples),names,
        lambda x,e:any(d.includes(x,e) for d in domains),bounds,tuple(w for d in domains for w in d.witnesses),
        ('same maintained state/estimand; fixed allocations within a law tuple; union across alternative tuples',))
    combined=combine_regions(parts,union_domain,mode='ALTERNATIVE_MODEL_UNION')
    # R7 PhysicalRegion exposes a float coverage_lower. Allocations and their
    # arithmetic remain exact; this conversion is only the compatibility view.
    combined=replace(combined,coverage_lower=float(combined.coverage_lower))
    return JointPhysicalRegion(**vars(combined),model_tuples=tuples)


def _certificate(bounds,status,procedure,domain_id,target_id,scope_ids=()):
    return BoundCertificate(bounds,status,0. if bounds is not None else None,procedure,tuple(scope_ids),target_id,domain_id)


def project(region,target):
    if isinstance(region,TensorImage):
        did=region.domain.domain_id
        if isinstance(target,LinearTarget):
            if target.coefficients.shape!=(8,):raise ValueError('target dimension')
            plus=support(region,target.coefficients);minus=support(region,-target.coefficients)
            if plus.certificate['status']=='OUTER_RANGE_UNRESOLVED':return _certificate(None,'OUTER_RANGE_UNRESOLVED',region.status,did,target.functional_id)
            return _certificate((-minus.hi+target.constant,plus.hi+target.constant),'EXACT_IMAGE_OUTER_ENCLOSURE',
                'signed supports of one convex joint image; outward rational root brackets',did,target.functional_id)
        if target in ('s2','w2') and region.status=='EXACT_DECLARED_MINKOWSKI_IMAGE':
            sl=slice(0,5) if target=='s2' else slice(5,8);index=0 if target=='s2' else 1
            c=region.central_prediction[sl];l=region.factor[sl]
            if region.rho==math.inf and any(v!=0 for v in l.flat):return _certificate((0,math.inf),'UNBOUNDED_LOCAL_DOMAIN','nonzero unrestricted linear image direction',did,target)
            center=sqrt_bounds(sum(c*c));factor=sqrt_bounds(sum(v*v for v in l.flat))
            spread=(region.rho if region.rho!=math.inf else 0)*factor[1]+region.remainder_rate_radii[index]/region.theta
            return _certificate((max(F(0),center[0]-spread)**2/2,(center[1]+spread)**2/2),'CERTIFIED_OUTER_BOUND',
                'S:S/2 or W:W/2; triangle/reverse triangle and Frobenius bound on one joint image',did,target)
        return _certificate(None,'OUTER_RANGE_UNRESOLVED','registered nonlinear/global provider or positive denominator domain unavailable',did,str(target))
    if not isinstance(region,PhysicalRegion):raise TypeError('TensorImage or bound PhysicalRegion required')
    if isinstance(target,AffineRatioFunctional):
        cert=affine_box_gf_bound(region,target)
        if cert is not None:return cert
    if isinstance(target,LinearTarget) and region.domain.bounds is not None:
        if len(target.coefficients)!=len(region.domain.bounds):raise ValueError('target dimension')
        lo=hi=target.constant
        for c,(a,b) in zip(target.coefficients,region.domain.bounds):
            if not math.isfinite(a) or not math.isfinite(b):break
            values=(c*rational(a),c*rational(b));lo+=min(values);hi+=max(values)
        else:return _certificate((lo,hi),'CERTIFIED_OUTER_BOUND','exact affine box relaxation retains every unresolved candidate',region.domain.domain_id,target.functional_id,region.scope_ids)
    return _certificate(None,'OUTER_RANGE_UNRESOLVED','no certified nonlinear/global bound; local witnesses cannot define outer range',region.domain.domain_id,getattr(target,'functional_id',str(target)),region.scope_ids)


def recession_certificate(R,K,v,*,domain_A,target,feasible_state=None,domain_b=None,observation=None):
    """For D={x:A x<=b}, prove a supplied feasible x+t v is unbounded.

    A=0 defaults to feasible x=0 in the unrestricted linear space. For a
    constrained domain the actual b and feasible state must be supplied.
    """
    r,k,vec,a,t=map(array,(R,K,v,domain_A,target))
    n=len(vec)
    if vec.shape!=(n,) or r.ndim!=2 or k.ndim!=2 or a.ndim!=2 or r.shape[1]!=n or k.shape[1]!=n or a.shape[1]!=n or t.shape!=(k.shape[0],):raise ValueError('ordered recession dimensions')
    if any(a@vec>0):return {'status':'NOT_A_RECESSION_WITNESS'}
    if any(r@vec!=0):return {'status':'OBSERVATION_CHANGED'}
    if sum(t*(k@vec))==0:return {'status':'TARGET_UNCHANGED'}
    if feasible_state is None:
        if len(a):return {'status':'FEASIBILITY_UNRESOLVED'}
        x=np.zeros(n,dtype=object)
    else:x=array(feasible_state)
    if x.shape!=(n,):raise ValueError('feasible state dimension')
    if len(a):
        if domain_b is None:return {'status':'FEASIBILITY_UNRESOLVED'}
        b=array(domain_b)
        if b.shape!=(len(a),):raise ValueError('constraint RHS dimension')
        if any(a@x>b):return {'status':'INFEASIBLE_BASE_STATE'}
    if observation is not None:
        y=array(observation)
        if y.shape!=(r.shape[0],):raise ValueError('observation dimension')
        if any(r@x!=y):return {'status':'BASE_STATE_OBSERVATION_MISMATCH'}
    return {'status':'UNBOUNDED_LOCAL_DOMAIN','direction':vec.tolist(),'base_state':x.tolist(),'target_slope':sum(t*(k@vec)),
            'scope':'specified feasible affine local-state ray only; not a global Einstein-Boltzmann extension'}


def closure_frontier(region_factory,target,value,rho_grid):
    grid=tuple(rational(x) for x in rho_grid);value=rational(value)
    if not grid or grid[0]<0 or tuple(sorted(set(grid)))!=grid:raise ValueError('ordered unique nonnegative closure grid required')
    lower=F(0);upper=math.inf;cells=[];first=None
    for rho in grid:
        region=region_factory(rho);bound=project(region,target);status='UNRESOLVED'
        # This implementation certifies nesting only for a fixed ellipsoid and
        # remainder set with changing rho. Arbitrary factories need a separate
        # nesting proof; observing nested endpoint bounds does not supply one.
        if not isinstance(region,TensorImage):
            return {'rho_lower':F(0),'rho_upper':math.inf,'status':'NESTING_UNRESOLVED',
                    'cells':[],'scope':'no fixed jet-image family certificate'}
        if region.rho!=rho:raise ValueError('image does not use the requested radius')
        if first is None:first=region
        elif (region.theta!=first.theta or region.remainder_rate_radii!=first.remainder_rate_radii
              or region.domain.domain_id!=first.domain.domain_id or region.domain.frame!=first.domain.frame
              or region.domain.assumptions!=first.domain.assumptions
              or any(not np.array_equal(a,b) for a,b in ((region.j0,first.j0),(region.L,first.L),(region.domain.K,first.domain.K)))):
            raise ValueError('frontier requires one fixed closure family')
        if bound.bounds is not None:
            lo,hi=bound.bounds
            if value<lo or value>hi:status='CERTIFIED_EXCLUDED';lower=rho
            elif isinstance(region,TensorImage) and isinstance(target,LinearTarget) and region.status=='EXACT_DECLARED_MINKOWSKI_IMAGE':
                plus=support(region,target.coefficients);minus=support(region,-target.coefficients)
                if -minus.lo+target.constant<=value<=plus.lo+target.constant:status='CERTIFIED_IN_EXACT_CONVEX_IMAGE';upper=min(upper,rho)
        cells.append({'rho':rho,'status':status,'bounds':bound.bounds})
    if upper<lower:raise ValueError('closure family contradicts nestedness at registered queries')
    return {'rho_lower':lower,'rho_upper':upper,'status':'CERTIFIED_GRID_BRACKET' if math.isfinite(upper) else 'UPPER_FRONTIER_UNRESOLVED',
            'cells':cells,'scope':'nested deterministic closure sensitivity, not a prior or fitted radius'}
