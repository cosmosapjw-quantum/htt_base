"""OBS03-SYNTH-v1 manufactured grouped latent-modulus likelihood.

This is not a calibrated real-CF4 likelihood. A fixed slot conditions on direction,
method and shell; integration is over independent uniform log-distance and source
motion, with the shared calibration anchor included once per catalogue.
"""
from dataclasses import dataclass
import itertools
import time
import numpy as np
from numpy.polynomial.legendre import leggauss
from scipy.optimize import minimize
from scipy.special import logsumexp, log_ndtr

C = 299792.458
A_MAG = 5 / np.log(10)
TRUTH = np.array([120., 1.2, .04])
SCALE = np.array([100., 1., .05])
BOUNDS = np.array([[-3000., 3000.], [-30., 30.], [-.5, .5]])
SIGMA_MU = np.array([.15, .20])
METHOD_OFFSET = np.array([0., .03])
THRESHOLD = np.array([35.10, 35.25])
ORDERS = ((32, 24), (64, 48), (96, 72))
SEED = 2026101303


def directions():
    phi = (1 + np.sqrt(5)) / 2
    vertices = []
    for p, q in itertools.product((-1., 1.), repeat=2):
        vertices.extend(((0., p, q*phi), (p, q*phi, 0.), (q*phi, 0., p)))
    n = np.array(sorted(vertices))
    return n / np.linalg.norm(n, axis=1)[:, None]


@dataclass(frozen=True)
class SyntheticCatalogue:
    slot_id: np.ndarray
    direction: np.ndarray
    shell: np.ndarray
    method: np.ndarray
    mu: np.ndarray
    vh: np.ndarray
    anchor: float
    selected: bool
    proposals: np.ndarray

    def __post_init__(self):
        n = len(self.slot_id)
        if not n or len(np.unique(self.slot_id)) != n:
            raise ValueError('nonempty unique synthetic slot IDs required')
        for x in (self.shell, self.method, self.mu, self.vh, self.proposals):
            if np.shape(x) != (n,) or not np.isfinite(x).all():
                raise ValueError('invalid catalogue shape/numeric fields')
        if np.shape(self.direction) != (n, 3) or not np.isfinite(self.direction).all() or not np.allclose(np.linalg.norm(self.direction,axis=1),1):
            raise ValueError('invalid directions')
        if not np.isfinite(self.anchor) or not np.isin(self.shell, [0,1]).all() or not np.isin(self.method,[0,1]).all():
            raise ValueError('invalid anchor/shell/method')
        if self.selected and np.any(self.mu > THRESHOLD[self.method]):
            raise ValueError('selected catalogue contains rejected row')

    def subset(self, mask):
        mask = np.asarray(mask)
        if mask.dtype != bool or mask.shape != self.slot_id.shape:
            raise ValueError('boolean slot mask required')
        return SyntheticCatalogue(*(getattr(self,k)[mask] for k in ('slot_id','direction','shell','method','mu','vh')),
                                  self.anchor,self.selected,self.proposals[mask])


def generate_catalogue(rng, *, selected=True, truth=TRUTH, method1_bias=0., max_proposals=3000):
    """Independent rejection draws per fixed slot; the anchor is one global draw."""
    theta = np.asarray(truth,float)
    if theta.shape != (3,) or not np.isfinite(theta).all() or np.any((theta<BOUNDS[:,0])|(theta>BOUNDS[:,1])):
        raise ValueError('truth outside frozen synthetic parameter box')
    if not np.isfinite(method1_bias):
        raise ValueError('finite injected bias required')
    n = np.repeat(directions(),2,axis=0)
    shell = np.tile([0,1],12); method = np.repeat(np.arange(12)%2,2)
    mu=[]; vh=[]; proposals=[]
    anchor=float(rng.normal(theta[2],.03))
    for i in range(24):
        for attempt in range(1,max_proposals+1):
            ell=rng.uniform(np.log([40.,100.][shell[i]])-.1,np.log([40.,100.][shell[i]])+.1)
            r=np.exp(ell); u=rng.uniform(-150.,150.)
            v=70*r+n[i,0]*(theta[0]+r*theta[1])+u
            mean=25+A_MAG*ell+2*A_MAG*np.log1p(v/C)+theta[2]+METHOD_OFFSET[method[i]]+(method1_bias if method[i]==1 else 0.)
            # Draw both observations on every proposal, including rejected ones.
            mm=rng.normal(mean,SIGMA_MU[method[i]]);vv=rng.normal(v,100.)
            if not selected or mm<=THRESHOLD[method[i]]:
                mu.append(mm);vh.append(vv);proposals.append(attempt);break
        else:
            raise RuntimeError('NUMERICAL_HOLD: proposal cap reached; slot not dropped')
    return SyntheticCatalogue(np.arange(24),n,shell,method,np.array(mu),np.array(vh),anchor,bool(selected),np.array(proposals))


class LatentModulusLikelihood:
    """Product quadrature over d ell du, with normalized weights summing to one."""
    def __init__(self,catalogue,order=(64,48),*,omit_selection_normalizer=False):
        if tuple(order) not in ORDERS:
            raise ValueError('quadrature order outside frozen ladder')
        self.catalogue=catalogue;self.order=tuple(order)
        self.omit_selection_normalizer=bool(omit_selection_normalizer)
        xl,wl=leggauss(order[0]);xu,wu=leggauss(order[1])
        centers=np.log(np.array([40.,100.]))[catalogue.shell]
        self.ell=(centers[:,None,None]+.1*xl[None,:,None])+np.zeros((1,1,order[1]))
        self.r=np.exp(self.ell);self.u=150*xu[None,None,:]
        self.log_weights=np.log(wl[:,None]*wu[None,:]/4.)
        self.nx=catalogue.direction[:,0,None,None]
        self.sm=SIGMA_MU[catalogue.method,None,None]
        self.delta=METHOD_OFFSET[catalogue.method,None,None]
        self.threshold=THRESHOLD[catalogue.method,None,None]
        self.calls=0
        self.call_limit=600

    def row_terms(self,theta,*,gradient=False):
        theta=np.asarray(theta,float)
        if theta.shape!=(3,) or not np.isfinite(theta).all() or np.any((theta<BOUNDS[:,0])|(theta>BOUNDS[:,1])):
            raise ValueError('parameter outside frozen box')
        v=70*self.r+self.nx*(theta[0]+self.r*theta[1])+self.u
        if np.any(v<=-C):
            raise ValueError('latent redshift domain')
        mean=25+A_MAG*self.ell+2*A_MAG*np.log1p(v/C)+theta[2]+self.delta
        rm=(self.catalogue.mu[:,None,None]-mean)/self.sm
        rv=(self.catalogue.vh[:,None,None]-v)/100.
        log_density=-.5*(rm*rm+rv*rv)-np.log(self.sm*100*2*np.pi)
        log_i=logsumexp(log_density+self.log_weights,axis=(1,2))
        selected=self.catalogue.selected and not self.omit_selection_normalizer
        if selected:
            t=(self.threshold-mean)/self.sm
            log_cdf=log_ndtr(t)
            log_alpha=logsumexp(log_cdf+self.log_weights,axis=(1,2))
        else:
            log_alpha=np.zeros(len(log_i))
        if not gradient:
            return log_i,log_alpha
        dv=np.stack(np.broadcast_arrays(self.nx+np.zeros_like(v),self.nx*self.r+np.zeros_like(v),np.zeros_like(v)),axis=-1)
        dm=(2*A_MAG/(C+v))[...,None]*dv;dm[...,2]=1.
        score=(rm/self.sm)[...,None]*dm+(rv/100.)[...,None]*dv
        ni=np.exp(log_density+self.log_weights-log_i[:,None,None])
        grad_i=np.sum(ni[...,None]*score,axis=(1,2))
        grad_alpha=np.zeros_like(grad_i)
        if selected:
            # d alpha = - integral phi(t)/sigma * dmean; avoids unstable phi/Phi.
            pdf_over_alpha=np.exp(-.5*t*t-.5*np.log(2*np.pi)+self.log_weights-log_alpha[:,None,None])/self.sm
            grad_alpha=-np.sum(pdf_over_alpha[...,None]*dm,axis=(1,2))
        return log_i,log_alpha,grad_i-grad_alpha

    def objective(self,scaled_theta):
        if self.calls>=self.call_limit:
            raise RuntimeError("NUMERICAL_HOLD: 600 objective evaluations exhausted")
        self.calls+=1
        theta=np.asarray(scaled_theta,float)*SCALE
        li,la,grad=self.row_terms(theta,gradient=True)
        anchor_res=(self.catalogue.anchor-theta[2])/.03
        value=-float(np.sum(li-la)-.5*anchor_res**2-np.log(.03*np.sqrt(2*np.pi)))
        score=np.sum(grad,axis=0);score[2]+=anchor_res/.03
        return value,-score*SCALE

    def anchor_free_hessian(self,scaled_theta,step):
        h=observed_hessian(self,scaled_theta,step)
        h[2,2]-=(SCALE[2]/.03)**2
        return h


def observed_hessian(likelihood,scaled_theta,step=.02):
    """Central differences of analytic score in frozen scaled coordinates."""
    scaled_theta=np.asarray(scaled_theta,float)
    h=np.empty((3,3))
    for j in range(3):
        e=np.eye(3)[j]*step
        if np.any((scaled_theta+e)*SCALE>BOUNDS[:,1]) or np.any((scaled_theta-e)*SCALE<BOUNDS[:,0]):
            raise ValueError('Hessian stencil crosses parameter box')
        h[:,j]=(likelihood.objective(scaled_theta+e)[1]-likelihood.objective(scaled_theta-e)[1])/(2*step)
    return (h+h.T)/2


def covariance_from_hessian(hessian):
    """No pseudoinverse: a non-SPD observed Hessian is a numerical HOLD."""
    h=np.asarray(hessian,float)
    if h.shape!=(3,3) or not np.isfinite(h).all():
        raise ValueError('invalid observed Hessian')
    eig=np.linalg.eigvalsh(h)
    tol=8*np.finfo(float).eps*3*np.linalg.norm(h,2)
    if eig[0]<=tol:
        raise ValueError('NUMERICAL_HOLD: observed Hessian not stably SPD')
    np.linalg.cholesky(h)
    inv=np.linalg.solve(h,np.eye(3))
    return SCALE[:,None]*inv*SCALE[None,:]


def fit_catalogue(catalogue,order=(64,48),*,omit_selection_normalizer=False):
    start=time.monotonic();like=LatentModulusLikelihood(catalogue,order,omit_selection_normalizer=omit_selection_normalizer)
    try:
        opt=minimize(like.objective,np.array([0.,0.,catalogue.anchor])/SCALE,jac=True,method='L-BFGS-B',
                 bounds=(BOUNDS/SCALE[:,None]).tolist(),options={'ftol':1e-10,'gtol':1e-6,'maxiter':100,'maxfun':600})
    except RuntimeError as exc:
        return {'status':'NUMERICAL_HOLD','failure':str(exc),'order':list(order),
                'estimate':None,'standard_errors':None,'interval95':None,'converged':False,
                'boundary':False,'objective_evaluations':like.calls,'elapsed_seconds':time.monotonic()-start}
    theta=opt.x*SCALE
    boundary=bool(np.any(np.isclose(theta,BOUNDS[:,0],atol=1e-6,rtol=0)) or np.any(np.isclose(theta,BOUNDS[:,1],atol=1e-6,rtol=0)))
    report={'order':list(order),'estimate':theta.tolist(),'objective':float(opt.fun),'converged':bool(opt.success),
            'optimizer_status':int(opt.status),'optimizer_message':str(opt.message),'nfev':int(opt.nfev),'nit':int(opt.nit),
            'boundary':boundary,'standard_errors':None,'interval95':None,'status':'NUMERICAL_HOLD'}
    try:
        if not opt.success or boundary:
            raise ValueError('failed/boundary optimizer')
        h1=observed_hessian(like,opt.x,.02);h2=observed_hessian(like,opt.x,.01)
        v1=covariance_from_hessian(h1);v2=covariance_from_hessian(h2)
        se1=np.sqrt(np.diag(v1));se2=np.sqrt(np.diag(v2))
        relative=np.abs(se2[:2]/se1[:2]-1)
        if np.max(relative)>.01:
            raise ValueError('NUMERICAL_HOLD: Hessian step-halving SE unstable')
        report.update({'status':'FIT_NUMERICALLY_STABLE','covariance':v2.tolist(),'standard_errors':se2.tolist(),
            'interval95':np.column_stack((theta-1.959963984540054*se2,theta+1.959963984540054*se2)).tolist(),
            'hessian_scaled':h2.tolist(),'hessian_step_se_relative_change':relative.tolist()})
    except (ValueError,RuntimeError,np.linalg.LinAlgError) as exc:
        report['failure']=str(exc)
    report['objective_evaluations']=like.calls
    report['elapsed_seconds']=time.monotonic()-start
    return report


def check_quadrature(catalogue,low,high,low_fit,high_fit):
    """Frozen truth/start/optimum and interval-Hessian stencil point checks."""
    if low_fit.get('estimate') is None or high_fit.get('estimate') is None:
        return {'passed':False,'reason':'optimizer evaluation cap exhausted'}
    points=[TRUTH,np.array([0.,0.,catalogue.anchor]),np.array(high_fit['estimate'])]
    for step in (.02,.01):
        for j in range(3):
            for sign in (-1,1):
                p=np.array(high_fit['estimate'])+sign*step*SCALE*np.eye(3)[j]
                if np.any((p<BOUNDS[:,0])|(p>BOUNDS[:,1])):
                    return {'passed':False,'reason':'Hessian comparison stencil crosses box'}
                points.append(p)
    l=LatentModulusLikelihood(catalogue,low);h=LatentModulusLikelihood(catalogue,high)
    differences=[]
    for p in points:
        il,al=l.row_terms(p);ih,ah=h.row_terms(p)
        differences.append(float(np.max(np.abs((ih-ah)-(il-al)))))
    stable=low_fit['status']=='FIT_NUMERICALLY_STABLE' and high_fit['status']=='FIT_NUMERICALLY_STABLE'
    displacement=se_change=None
    if stable:
        sl=np.array(low_fit['standard_errors'])[:2];sh=np.array(high_fit['standard_errors'])[:2]
        displacement=np.abs(np.array(high_fit['estimate'])[:2]-np.array(low_fit['estimate'])[:2])/sh
        se_change=np.abs(sh/sl-1)
    passed=bool(stable and max(differences)<=1e-5 and np.max(displacement)<=.02 and np.max(se_change)<=.01)
    return {'passed':passed,'low_order':list(low),'high_order':list(high),'max_per_row_log_density_change':max(differences),
            'point_count':len(points),'estimate_change_in_SE':displacement.tolist() if stable else None,
            'SE_relative_change':se_change.tolist() if stable else None}


def refined_fit(catalogue):
    fits=[];checks=[]
    for order in ORDERS:
        fit=fit_catalogue(catalogue,order);fits.append(fit)
        if len(fits)>1:
            check=check_quadrature(catalogue,ORDERS[len(fits)-2],order,fits[-2],fits[-1]);checks.append(check)
            if check['passed']:
                return {'status':'QUADRATURE_ACCEPTED','accepted_order':list(order),'fits':fits,'checks':checks}
    return {'status':'NUMERICAL_HOLD','accepted_order':None,'fits':fits,'checks':checks}


def local_response_svd(catalogue,theta,*,anchor=False,zero_shell_width=False):
    """Conditional small response, with latent-distance/source-motion profiling.

    This SVD is a local response diagnostic, distinct from the marginal observed
    likelihood Hessian. It specializes OBS-02's 3x2 block to B,A,kappa.
    """
    theta=np.asarray(theta,float);r=np.array([40.,100.])[catalogue.shell]
    nx=catalogue.direction[:,0];h=70*r+nx*(theta[0]+r*theta[1]);z=h/C
    sigma=np.column_stack((SIGMA_MU[catalogue.method],np.full(len(r),100.),np.full(len(r),150/np.sqrt(3))))
    j=np.zeros((len(r),3,3));j[:,0,2]=1;j[:,2,0]=-nx;j[:,2,1]=-r*nx
    if zero_shell_width:
        # A known single radius has exactly proportional B and A responses.
        rows=np.column_stack((nx,r*nx,np.zeros(len(r))))/100.
        # Calibration information supplied by modulus and one anchor only.
        rows=np.vstack((rows,np.column_stack((np.zeros(len(r)),np.zeros(len(r)),1/SIGMA_MU[catalogue.method]))))
    else:
        from htt.infer.cf4_information import latent_jacobian
        e=latent_jacobian(r,z,70+nx*theta[1])/sigma[:,:,None]
        q=np.cross(e[:,:,0],e[:,:,1]);q/=np.linalg.norm(q,axis=1)[:,None]
        rows=np.einsum('ni,nij->nj',q,j/sigma[:,:,None])
    if anchor:
        rows=np.vstack((rows,[0.,0.,1/.03]))
    scaled=rows*SCALE
    _,s,vt=np.linalg.svd(scaled,full_matrices=False)
    tol=8*np.finfo(float).eps*max(scaled.shape)*s[0]
    return {'rank':int(np.sum(s>tol)),'singular_values':s.tolist(),'rank_tolerance':float(tol),
            'null_directions_scaled':vt[s<=tol].tolist(),'coefficient_scale':SCALE.tolist(),
            'anchor_augmented':bool(anchor),'zero_shell_width':bool(zero_shell_width),
            'source_motion_sd_proxy':'uniform[-150,150] RMS=150/sqrt(3); local Gaussian-noise SVD diagnostic only'}
