"""CF4 grouped-product adapters and supplied conditional sensitivity laws.

Public group summaries do not calibrate the all-method selection/covariance law.
The latent slot law below is usable only under supplied source, selection,
velocity and calibration assumptions; no catalogue weights are probabilities.
"""
from dataclasses import dataclass, replace
import copy
from enum import Enum
import math
import numpy as np
from numpy.polynomial.legendre import leggauss
from scipy.special import ndtr, log_ndtr, logsumexp
from scipy.optimize import minimize_scalar
from scipy.integrate import quad, IntegrationWarning
import warnings
from .cf4_information import angular_design, A_MAG, C
from .r7_cf4_law import SelectedLatentBlock
from common.r7_contracts import NumericalUnresolved


class ResponseFamily(str, Enum):
    AFFINE9 = 'affine9'
    WEAK12 = 'weak12'
    ENDPOINT13 = 'endpoint13'


class ProviderUnavailable(ValueError):
    pass


def _array(value, shape=None):
    x = np.asarray(value, dtype=float)
    if (shape is not None and x.shape != shape) or not np.isfinite(x).all():
        raise ValueError('finite array with declared shape required')
    return x


def _source(value):
    if not isinstance(value, str) or value.strip().lower() in ('', 'unknown', 'none', 'unavailable'):
        raise ProviderUnavailable('explicit assumption/source identity required')
    return value


def luminosity_to_area_distance(distance_mpc, redshift):
    """Etherington reciprocity, supplied redshift and luminosity distance."""
    d, z = np.broadcast_arrays(_array(distance_mpc), _array(redshift))
    if np.any(d <= 0) or np.any(z <= -1):
        raise ValueError('positive distance and z > -1 required')
    out = d / (1+z)**2
    if not np.isfinite(out).all() or np.any(out <= 0):
        raise ArithmeticError('distance conversion exceeds numerical domain')
    return out


def area_distance_to_modulus(distance_mpc, redshift, calibration_mag=0.):
    r, z, eta = np.broadcast_arrays(_array(distance_mpc), _array(redshift), _array(calibration_mag))
    if np.any(r <= 0) or np.any(z <= -1):
        raise ValueError('positive distance and z > -1 required')
    out = 25 + A_MAG*np.log(r) + 2*A_MAG*np.log1p(z) + eta
    if not np.isfinite(out).all():
        raise ArithmeticError('modulus conversion exceeds numerical domain')
    return out


@dataclass(frozen=True)
class CF4ResponseProvider:
    family: ResponseFamily
    observer_frame: str
    redshift_frame: str
    direction_frame: str
    remainder_source: str
    remainder_bound_km_s: float | None
    provider_id: str = 'CF4_SUPPLIED_ENDPOINT_RESPONSE'

    def __post_init__(self):
        if not isinstance(self.family, ResponseFamily):
            raise TypeError('explicit ResponseFamily required')
        for name in ('observer_frame', 'redshift_frame', 'direction_frame', 'provider_id'):
            _source(getattr(self, name))
        if self.observer_frame != self.redshift_frame:
            raise ProviderUnavailable('observer/redshift frame mismatch; supply explicit corrected product')
        if self.direction_frame != 'J2000_EQUATORIAL_SOURCEWARD':
            raise ProviderUnavailable('directions require explicit J2000 sourceward basis')
        if self.remainder_bound_km_s is not None:
            _source(self.remainder_source)
            if not math.isfinite(self.remainder_bound_km_s) or self.remainder_bound_km_s < 0:
                raise ValueError('finite nonnegative remainder bound required')

    @property
    def names(self):
        stf = tuple('STF'+str(j) for j in range(1,6))
        if self.family is ResponseFamily.AFFINE9:
            return ('Bx','By','Bz','H') + stf
        if self.family is ResponseFamily.WEAK12:
            return ('Bx','By','Bz','H','Ax','Ay','Az') + stf
        return ('b0','Bx','By','Bz','H','Ax','Ay','Az') + stf

    @property
    def units(self):
        return tuple('km/s' if x in ('b0','Bx','By','Bz') else 'km/s/Mpc' for x in self.names)

    def design(self, direction, area_distance_mpc):
        n = _array(direction)
        r = _array(area_distance_mpc)
        if n.ndim != 2 or n.shape[1] != 3 or r.shape != (len(n),) or np.any(r <= 0):
            raise ValueError('N source directions and positive N area distances required')
        ang = angular_design(n)
        if self.family is ResponseFamily.AFFINE9:
            return np.column_stack((n, r[:,None]*ang[:,[0,4,5,6,7,8]]))
        x = np.column_stack((n, r[:,None]*ang))
        return np.column_stack((np.ones(len(r)),x)) if self.family is ResponseFamily.ENDPOINT13 else x

    def velocity(self, direction, area_distance_mpc, coefficients, *, remainder_km_s=None):
        """cz response; endpoint13 b0=c(zeta0-1), B=c*zeta_vector.

        This is a free endpoint coefficient representation, not an inferred
        geometric normal. weak12 fixes b0=0; affine9 also fixes A=0.
        """
        if self.remainder_bound_km_s is None:
            raise ProviderUnavailable('finite-distance remainder UNKNOWN')
        r = _array(area_distance_mpc)
        theta = _array(coefficients, (len(self.names),))
        if remainder_km_s is None:
            if self.remainder_bound_km_s != 0:
                raise ProviderUnavailable('bounded deterministic remainder must be supplied explicitly')
            remainder = np.zeros(len(r))
        else:
            remainder = _array(remainder_km_s, r.shape)
        if np.any(np.abs(remainder) > self.remainder_bound_km_s):
            raise ValueError('remainder exceeds bound')
        v = self.design(direction,r) @ theta + remainder
        if not np.isfinite(v).all() or np.any(v <= -C):
            raise ValueError('response outside finite redshift domain')
        return v

    def capabilities(self):
        """R7 prediction-slot interface; unknown remainder cannot bind."""
        return ("distance",) if self.remainder_bound_km_s is not None else ()

    def capability(self):
        return dict(family=self.family.value, names=self.names, units=self.units,
                    expansion_dipole=self.family is not ResponseFamily.AFFINE9,
                    free_scalar_intercept=self.family is ResponseFamily.ENDPOINT13,
                    basis='Frobenius orthonormal STF; n^T E_j n; J2000 sourceward',
                    response='cz=b0+n.B+dA*(H+n.A+STF(n).s)+R',
                    endpoint_crosswalk='b0=c*(zeta0-1); B=c*zeta_vector',
                    remainder_status='UNKNOWN' if self.remainder_bound_km_s is None else 'SUPPLIED',
                    interpretation='conditional endpoint coefficients; no geometric normal or tilt inference')


def calibration_templates(catalog, *, global_mode=True, method_modes=False, angular=None):
    """Separate magnitude templates. Method PRESENCE is an assumed template,
    never a published mixing weight or calibrated individual-method modulus.
    """
    templates, names = [], []
    if global_mode:
        templates.append(np.ones(len(catalog.group_id))); names.append('global_zero_point')
    if method_modes:
        from obsstat.catalogs.cf4_grouped_observations import METHODS
        templates.extend(catalog.method_presence.T.astype(float)); names.extend('presence_'+x for x in METHODS)
    if angular is not None:
        t = _array(angular)
        if t.ndim != 2 or t.shape[0] != len(catalog.group_id):
            raise ValueError('angular calibration template shape')
        templates.extend(t.T); names.extend('angular_'+str(j) for j in range(t.shape[1]))
    return (np.column_stack(templates) if templates else np.empty((len(catalog.group_id),0))), tuple(names)


@dataclass(frozen=True)
class SlotAssumptions:
    """Uniform log dA and uniform source velocity, conditional on fixed slot.

    Selection is the supplied observed-mu interval; velocity observations have
    full support. Independence is conditional on shared calibration and velocity
    field. Bounds describe source intensity, not posterior bounds from DMzp.
    """
    log_distance_bounds: tuple
    source_velocity_bounds_km_s: tuple
    observed_mu_bounds: tuple
    sigma_mu_mag: float
    sigma_velocity_km_s: float
    source_id: str
    selection_id: str
    cross_covariance_id: str
    velocity_id: str

    def __post_init__(self):
        for name in ('source_id','selection_id','cross_covariance_id','velocity_id'):
            _source(getattr(self,name))
        for bounds in (self.log_distance_bounds,self.source_velocity_bounds_km_s):
            if len(bounds) != 2 or not np.isfinite(bounds).all() or bounds[0] >= bounds[1]:
                raise ValueError('ordered finite latent bounds required')
        b = self.observed_mu_bounds
        if len(b) != 2 or np.isnan(b).any() or b[0] >= b[1]:
            raise ValueError('ordered measurement selection bounds required')
        if not np.isfinite([self.sigma_mu_mag,self.sigma_velocity_km_s]).all() or min(self.sigma_mu_mag,self.sigma_velocity_km_s) <= 0:
            raise ValueError('positive finite measurement sigmas required')


def _log_interval(lo,hi):
    """Stable log[Phi(hi)-Phi(lo)] including either Gaussian tail."""
    lo,hi = np.broadcast_arrays(lo,hi)
    a = np.where(lo>0, log_ndtr(-lo),log_ndtr(hi))
    b = np.where(lo>0, log_ndtr(-hi),log_ndtr(lo))
    with np.errstate(divide='ignore', invalid='ignore'):
        return a+np.log(-np.expm1(b-a))


class CF4SelectedBlock(SelectedLatentBlock):
    """Reuse R7 block interface; integrate selection analytically over y.

    Avoid four-dimensional nested quadrature when the supplied independent
    Gaussian mu/velocity law and hard mu interval admit a Gaussian CDF. The
    inherited absolute-error contract remains operative (epsrel is zero).
    """
    def loglik(self,y,theta,eta,provider):
        y = _array(y,(2,))
        if not self.selection(y):
            return -math.inf
        value,error = self.intensity_at(y,theta,eta,provider)
        norm,ne = self._integral(lambda *xi: self.intensity(np.array(xi),theta,eta,provider)*self.selection_mass(np.array(xi),theta,eta,provider),self.latent_bounds)
        if value <= error or norm <= ne or norm <= 0:
            raise NumericalUnresolved('selected density/normalizer unresolved')
        return math.log(value)-math.log(norm)


def selected_slot_block(provider, direction, assumptions, *, remainder_km_s=None, absolute_error=1e-8):
    """Small two-latent block, compatible with build_cf4_law's raw branch."""
    if remainder_km_s is None:
        if provider.remainder_bound_km_s != 0:
            raise ProviderUnavailable("explicit finite-distance remainder required")
        # Keep None until evaluation: a later provider may have a positive
        # bound and must refuse omission rather than inherit assumed zero.
    n = _array(direction,(3,)); a = assumptions
    if not isinstance(a,SlotAssumptions):
        raise TypeError('SlotAssumptions required')
    def means(xi,theta,eta,p):
        r = np.exp(xi[0]); v = p.velocity(n[None,:],np.array([r]),theta,remainder_km_s=None if remainder_km_s is None else np.array([remainder_km_s]))[0]+xi[1]
        return area_distance_to_modulus(r,v/C,eta),v
    def density(y,xi,t,e,p):
        m,v = means(xi,t,e,p)
        return np.exp(-.5*((y[0]-m)/a.sigma_mu_mag)**2-.5*((y[1]-v)/a.sigma_velocity_km_s)**2)/(2*np.pi*a.sigma_mu_mag*a.sigma_velocity_km_s)
    lo,hi = a.observed_mu_bounds
    volume = (a.log_distance_bounds[1]-a.log_distance_bounds[0])*(a.source_velocity_bounds_km_s[1]-a.source_velocity_bounds_km_s[0])
    block = CF4SelectedBlock((a.log_distance_bounds,a.source_velocity_bounds_km_s),((lo,hi),(-np.inf,np.inf)),lambda x,t,e,p:1/volume,density,lambda y:float(lo<=y[0]<=hi),a.source_id,absolute_error=absolute_error)
    block.selection_mass = lambda x,t,e,p: float(np.exp(_log_interval((lo-means(x,t,e,p)[0])/a.sigma_mu_mag,(hi-means(x,t,e,p)[0])/a.sigma_mu_mag)))
    return block



def _catalog_frames(catalog):
    provenance = catalog.provenance
    if provenance.get('frame') == 'heliocentric Vh; J2000 equatorial':
        return 'HELIOCENTRIC','J2000_EQUATORIAL_SOURCEWARD'
    return _source(provenance.get('redshift_frame')), _source(provenance.get('direction_frame'))

class ConditionalCF4CatalogueLaw:
    """Supplied selected slot laws with one shared Gaussian zero point.

    The prior is explicitly conditional on the fixed selected-slot/count scheme;
    it is not a population count law. Shared velocity fields and other calibration
    coefficients must be conditioned externally; correlated residual errors need
    a joint block and are refused by this independent-slot implementation.
    Quadrature refinement is an empirical numerical check, not a certificate.
    """
    def __init__(self, catalog, provider, assumptions, *, shared_zero_point_sigma_mag,
                 calibration_source, cross_covariance_mode, remainder_km_s, order=32, calibration_order=32,
                 conditioned_field_convention=None):
        if conditioned_field_convention not in ("ZERO_METHOD_ANGULAR_VELOCITY_FIELDS_ASSUMED_FOR_SCENARIO","SUPPLIED_FIELDS_REQUIRED"):
            raise ProviderUnavailable("explicit conditioned field convention required")
        self.conditioned_field_convention = conditioned_field_convention
        redshift_frame,direction_frame = _catalog_frames(catalog)
        if not isinstance(provider,CF4ResponseProvider) or provider.redshift_frame != redshift_frame or provider.direction_frame != direction_frame:
            raise ProviderUnavailable('catalogue/provider frame mismatch')
        if cross_covariance_mode != 'INDEPENDENT_GIVEN_SHARED_LATENTS':
            raise ProviderUnavailable('correlated errors require supplied joint block')
        if len(assumptions) != len(catalog.group_id) or not all(isinstance(x,SlotAssumptions) for x in assumptions):
            raise ValueError('one supplied source law per unique group required')
        if len(np.unique(catalog.group_id)) != len(catalog.group_id):
            raise ValueError('duplicate group IDs')
        _source(calibration_source)
        if not math.isfinite(shared_zero_point_sigma_mag) or shared_zero_point_sigma_mag <= 0:
            raise ValueError('one proper shared Gaussian calibration required')
        if not isinstance(order,int) or not 4 <= order <= 128 or not isinstance(calibration_order,int) or not 4 <= calibration_order <= 128:
            raise ValueError('bounded integer quadrature orders 4..128 required')
        # Snapshot the bound grouped product so unrelated callers cannot alter
        # this supplied law by editing catalogue arrays in place.
        fields = {}
        for key in ("group_id","modulus","modulus_error","vh_km_s","direction","method_presence"):
            value = np.array(getattr(catalog,key),copy=True); value.flags.writeable=False
            fields[key] = value
        self.catalog = replace(catalog,**fields,provenance=copy.deepcopy(catalog.provenance))
        self.provider,self.assumptions = provider,tuple(assumptions)
        self.remainder = _array(remainder_km_s,(len(catalog.group_id),)).copy()
        self.sigma = shared_zero_point_sigma_mag
        x,w = leggauss(order)
        self.log_weights = np.log(w[:,None]*w[None,:]/4)
        bounds = np.array([a.log_distance_bounds for a in assumptions])
        vb = np.array([a.source_velocity_bounds_km_s for a in assumptions])
        self.r = np.exp(bounds.mean(axis=1)[:,None,None]+np.diff(bounds,axis=1)[:,0,None,None]*x[None,:,None]/2)*np.ones((1,1,order))
        self.u = vb.mean(axis=1)[:,None,None]+np.diff(vb,axis=1)[:,0,None,None]*x[None,None,:]/2
        self.order,self.calibration_order = order,calibration_order
        self.calibration_source = calibration_source

    def row_loglik(self,theta,eta, *, method_offsets_mag=None, angular_offsets_mag=None, velocity_field_km_s=None):
        nrows = len(self.assumptions)
        if np.ndim(eta) != 0 or not np.isfinite(eta):
            raise ValueError("one finite shared zero point required")
        if self.conditioned_field_convention == "SUPPLIED_FIELDS_REQUIRED" and any(v is None for v in (method_offsets_mag,angular_offsets_mag,velocity_field_km_s)):
            raise ProviderUnavailable("conditioned method/angular/velocity fields must be supplied")
        # Explicit conditioned offsets, never fitted per-row inflation.
        def supplied(value):
            return np.zeros(nrows) if value is None else _array(value,(nrows,))
        offsets = eta+supplied(method_offsets_mag)+supplied(angular_offsets_mag)
        field = supplied(velocity_field_km_s)
        n = np.repeat(self.catalog.direction,self.order*self.order,axis=0)
        rem = np.repeat(self.remainder,self.order*self.order)
        v = self.provider.velocity(n,self.r.ravel(),theta,remainder_km_s=rem).reshape(self.r.shape)+self.u+field[:,None,None]
        mu = area_distance_to_modulus(self.r,v/C,offsets[:,None,None])
        sm = np.array([a.sigma_mu_mag for a in self.assumptions])[:,None,None]
        sv = np.array([a.sigma_velocity_km_s for a in self.assumptions])[:,None,None]
        lp = -.5*((self.catalog.modulus[:,None,None]-mu)/sm)**2-.5*((self.catalog.vh_km_s[:,None,None]-v)/sv)**2-np.log(2*np.pi*sm*sv)
        bounds = np.array([a.observed_mu_bounds for a in self.assumptions])
        ln = _log_interval((bounds[:,0,None,None]-mu)/sm,(bounds[:,1,None,None]-mu)/sm)
        out = logsumexp(lp+self.log_weights,axis=(1,2))-logsumexp(ln+self.log_weights,axis=(1,2))
        keep = (self.catalog.modulus>=bounds[:,0])&(self.catalog.modulus<=bounds[:,1])
        return np.where(keep,out,-np.inf)

    def log_likelihood(self,theta,**conditioned):
        """Posterior-centred adaptive eta integral, with numerical HOLD.

        Prior-centred Hermite nodes cannot resolve a narrow displaced posterior.
        Locate and scale the joint integrand, integrate split finite domains,
        refine tolerance and expand the tails. These convergence/error estimates
        are operational numerical checks, not a rigorous global certificate.
        ``calibration_order`` is retained for API compatibility and is not used
        as evidence that shared-calibration integration converged.
        """
        calls = 0
        def log_joint(eta):
            nonlocal calls
            calls += 1
            if calls > 4000:
                raise NumericalUnresolved('shared eta integration evaluation cap')
            return float(np.sum(self.row_loglik(theta,float(eta),**conditioned)))-.5*(eta/self.sigma)**2-math.log(self.sigma*math.sqrt(2*math.pi))
        lo,hi = -12*self.sigma,12*self.sigma
        for _ in range(8):
            result = minimize_scalar(lambda e:-log_joint(e),bounds=(lo,hi),method='bounded',options={'xatol':1e-11,'maxiter':120})
            center = float(result.x); peak = log_joint(center)
            if peak == -math.inf:
                return -math.inf
            if not result.success or not math.isfinite(peak):
                raise NumericalUnresolved('shared eta posterior mode unresolved')
            if min(center-lo,hi-center)>.05*(hi-lo) and max(log_joint(lo),log_joint(hi))<peak-50:
                break
            lo *= 2; hi *= 2
        else:
            raise NumericalUnresolved('shared eta tail/mode bracket unresolved')
        step = (self.sigma**-2+sum(a.sigma_mu_mag**-2 for a in self.assumptions))**-.5/5
        curvature = (2*peak-log_joint(center-step)-log_joint(center+step))/step**2
        if not math.isfinite(curvature) or curvature <= 0:
            raise NumericalUnresolved('shared eta posterior scale unresolved')
        width = 1/math.sqrt(curvature)
        def integrand(x):
            delta = log_joint(center+width*x)-peak
            if not math.isfinite(delta) or delta > 500:
                raise NumericalUnresolved('shared eta scaled integrand unresolved')
            return math.exp(delta)
        def integrate(lower,upper,absolute,relative):
            bounds = sorted(set([lower,upper]+[x for x in (-8.,0.,8.) if lower<x<upper]))
            total,error = 0.,0.
            with warnings.catch_warnings():
                warnings.simplefilter('error',IntegrationWarning)
                try:
                    for left,right in zip(bounds[:-1],bounds[1:]):
                        value,err = quad(integrand,left,right,epsabs=absolute,epsrel=relative,limit=200)
                        total += value; error += err
                except IntegrationWarning as exc:
                    raise NumericalUnresolved('shared eta adaptive quadrature unresolved') from exc
            if total <= 0 or not np.isfinite([total,error]).all() or error > 1e-8*total:
                raise NumericalUnresolved('shared eta quadrature error unresolved')
            return peak+math.log(width*total),error/total
        lower,upper = (lo-center)/width,(hi-center)/width
        coarse,_ = integrate(lower,upper,1e-10,1e-8)
        fine,error = integrate(2*lower,2*upper,1e-12,1e-10)
        if abs(coarse-fine)>1e-7:
            raise NumericalUnresolved('shared eta quadrature refinement/tails unresolved')
        self.last_eta_integration = {'center_mag':center,'scale_mag':width,'evaluations':calls,
            'loglik_refinement_difference':abs(coarse-fine),'relative_error_estimate':error,
            'method':'POSTERIOR_CENTRED_ADAPTIVE_QUADRATURE','certificate':False}
        return fine


def build_group_law_factory(catalog, index, assumptions, *, calibration_source, remainder_km_s):
    """Bind one actual 1PGC mu,Vh pair to existing R7 selected-law factory.

    Multiple factories must be composed conditional on the same eta/field and
    integrated once. Treating their calibration marginals as independent is
    invalid. A one-row factory cannot calibrate the all-method catalogue law.
    """
    from scipy.integrate import nquad
    from common.r7_contracts import content_id
    from .r7_cf4_law import build_cf4_law
    if not isinstance(index,(int,np.integer)) or not 0 <= index < len(catalog.group_id):
        raise ValueError('valid group row index required')
    _source(calibration_source)
    if _catalog_frames(catalog) != ('HELIOCENTRIC','J2000_EQUATORIAL_SOURCEWARD'):
        raise ProviderUnavailable('group factory catalogue frame mismatch')
    a = assumptions
    n = catalog.direction[index].copy()
    # Provider is supplied at bind time; closures use its actual frame contract.
    p0 = CF4ResponseProvider(ResponseFamily.ENDPOINT13,'HELIOCENTRIC','HELIOCENTRIC',
                             'J2000_EQUATORIAL_SOURCEWARD','factory dispatch only',0.)
    block = selected_slot_block(p0,n,a,remainder_km_s=remainder_km_s)
    group = int(catalog.group_id[index])
    observed = np.array([catalog.modulus[index],catalog.vh_km_s[index]])
    source = content_id({'catalog':catalog.provenance,'group':group,'observed':observed,'direction':n})
    def mean(t,e,p):
        # Conditional selected mean under the supplied source model, not the
        # observed values and not the midpoint latent plug-in prediction.
        lo,hi=a.observed_mu_bounds
        volume=math.prod(b-a for a,b in block.latent_bounds)
        def moments(ell,u):
            r=np.exp(ell);v=p.velocity(n[None,:],[r],t,remainder_km_s=None if remainder_km_s is None else [remainder_km_s])[0]+u
            m=float(area_distance_to_modulus(r,v/C,e));zl,zh=(lo-m)/a.sigma_mu_mag,(hi-m)/a.sigma_mu_mag
            mass=float(np.exp(_log_interval(zl,zh)))
            shift=a.sigma_mu_mag*(np.exp(-.5*zl*zl)-np.exp(-.5*zh*zh))/np.sqrt(2*np.pi)
            return np.array([mass,m*mass+shift,v*mass])/volume
        result=[]
        for j in range(3):
            value,error=nquad(lambda ell,u:moments(ell,u)[j],block.latent_bounds,opts={'epsabs':1e-8,'epsrel':0})
            if not np.isfinite([value,error]).all() or error>1e-8:
                raise NumericalUnresolved('selected mean quadrature unresolved')
            result.append(value)
        if result[0]<=1e-8:raise NumericalUnresolved('selected mean normalization unresolved')
        return np.array(result[1:])/result[0]
    product={'product_id':f'CF4:1PGC:{group}','observed':observed,'measurement_ids':(f'CF4:{group}:mu_mag',f'CF4:{group}:Vh_km_s'),
       'parameter_names':p0.names,'parameter_units':p0.units,'mean':mean,'mean_id':'selected source-integrated mu,Vh conditional mean',
       'domain_id':'CF4_SUPPLIED_HELIOCENTRIC_ENDPOINT13',
       'domain_contains':lambda t,e:np.shape(t)==(13,) and np.isfinite(t).all() and np.ndim(e)==0 and np.isfinite(e),
       'source_id':source}
    original = build_cf4_law(product,{'latent_block':block,'selection_id':a.selection_id},{'source_id':calibration_source})
    from .r7_gaussian_law import ObservationLawFactory
    def bind(p):
        if not isinstance(p,CF4ResponseProvider) or p.family is not ResponseFamily.ENDPOINT13 or p.observer_frame != 'HELIOCENTRIC':
            raise ProviderUnavailable('group factory requires heliocentric endpoint13 provider')
        if remainder_km_s is None and p.remainder_bound_km_s != 0:
            raise ProviderUnavailable('explicit remainder required for the bound provider')
        law=original.builder(p)
        specification=dict(law.specification, supplied_slot_contract=contract)
        return replace(law,specification=specification,shared_latent_ids=('CF4:global_zero_point:'+calibration_source,'CF4:velocity_field:'+a.velocity_id))
    contract={'source_id':a.source_id,'selection_id':a.selection_id,'cross_covariance_id':a.cross_covariance_id,'velocity_id':a.velocity_id,
              'latent_measure':'uniform d(log dA) du','latent_bounds':block.latent_bounds,'mu_selection':a.observed_mu_bounds,
              'sigma_mu_mag':a.sigma_mu_mag,'sigma_velocity_km_s':a.sigma_velocity_km_s,'remainder_km_s':remainder_km_s,
              'observer_frame':'HELIOCENTRIC','direction_frame':'J2000_EQUATORIAL_SOURCEWARD','measurement_units':('mag','km/s')}
    spec=dict(original.specification,supplied_slot_contract=contract)
    return ObservationLawFactory(original.factory_id,original.measurement_ids,original.unfilled_prediction_slots,spec,bind)
