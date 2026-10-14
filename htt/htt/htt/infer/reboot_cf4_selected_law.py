"""RB07 declared selected CF4 SNIa scenario; heliocentric endpoint coefficients.

The population, Gaussian widths, common calibration and finite-distance term are
supplied scenarios. This module does not supply a CF4 completeness law, an H0
measurement, or a global-tilt response. Selection acts on observed modulus only.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import math
from pathlib import Path

import numpy as np
from numpy.polynomial.hermite import hermgauss
from numpy.polynomial.legendre import leggauss
from scipy.optimize import minimize
from scipy.special import log_ndtr, logsumexp

C = 299792.458
A = 5 / math.log(10)
K = 2 * A / C
X_MIN, X_MAX = math.log(5), math.log(250)
BOUNDS = [(40., 110.), (-15., 15.), (-15., 15.), (-15., 15.)]  # B/100 optimizer coordinates
SEMANTICS = ('PRESELECTION_SHARED_PRIOR', 'SELECTED_SLOT_PRIOR')


def log_cdf_interval(lo, hi):
    """log(Phi(hi)-Phi(lo)) with a complementary-CDF positive-tail branch."""
    if np.iscomplexobj(lo) or np.iscomplexobj(hi):raise ValueError('real CDF limits required')
    lo, hi = np.broadcast_arrays(np.asarray(lo, float), np.asarray(hi, float))
    if np.any(lo >= hi):
        raise ValueError('ordered CDF limits required')
    top = np.where(lo > 0, log_ndtr(-lo), log_ndtr(hi))
    bottom = np.where(lo > 0, log_ndtr(-hi), log_ndtr(lo))
    with np.errstate(divide='ignore', invalid='ignore'):
        return top + np.log(-np.expm1(bottom - top))


@dataclass(frozen=True)
class Scenario:
    alpha: float = 2.
    s_u_km_s: float = 250.
    s_spec_km_s: float = 30.
    s_eta_mag: float = .05
    kappa: float = .725
    selection_semantics: str = SEMANTICS[0]

    def __post_init__(self):
        vals = (self.alpha, self.s_u_km_s, self.s_spec_km_s, self.s_eta_mag, self.kappa)
        if not all(math.isfinite(v) for v in vals) or min(vals[1:4]) <= 0:
            raise ValueError('finite scenario and positive widths required')
        if self.selection_semantics not in SEMANTICS:
            raise ValueError('unrecognized selection semantics')


@dataclass(frozen=True)
class Sample:
    group_id: np.ndarray
    mu: np.ndarray
    sigma_mu: np.ndarray
    raw_vh: np.ndarray
    direction: np.ndarray

    def __post_init__(self):
        n = len(self.group_id)
        if n == 0 or len(set(map(int, self.group_id))) != n:
            raise ValueError('unique nonempty group IDs required')
        for arr in (self.mu, self.sigma_mu, self.raw_vh):
            if np.iscomplexobj(arr) or np.shape(arr) != (n,) or not np.isfinite(arr).all():
                raise ValueError('finite aligned samples required')
        if np.shape(self.direction) != (n, 3) or not np.isfinite(self.direction).all():
            raise ValueError('finite directions required')
        if np.any(self.sigma_mu <= 0) or np.any(self.raw_vh <= -C):
            raise ValueError('modulus uncertainty/redshift domain')
        if np.any((self.mu<31)|(self.mu>35)):raise ValueError('observation outside selected modulus support')
        if not np.allclose(np.linalg.norm(self.direction, axis=1), 1, atol=1e-10):
            raise ValueError('unit J2000 sourceward direction required')

    def without(self, index):
        keep = np.arange(len(self.group_id)) != index
        return Sample(*(np.asarray(getattr(self, field))[keep] for field in
                        ('group_id', 'mu', 'sigma_mu', 'raw_vh', 'direction')))


def selected_sample(catalog, packet):
    required = packet['subset']['group_ids']
    if len(required) != 24 or len(set(required)) != 24:
        raise ValueError('frozen 24-group list required')
    if catalog.provenance.get('frame') != 'heliocentric Vh; J2000 equatorial':
        raise ValueError('raw heliocentric J2000 source contract changed')
    # SNIa is the second method-presence column. No presence is a weight.
    eligible = (catalog.method_presence[:, 1] &
                ~np.any(catalog.method_presence[:, [0, 2, 3, 4, 5, 6]], axis=1) &
                (catalog.modulus >= 31) & (catalog.modulus <= 35) &
                (catalog.modulus_error <= .35))
    indices = np.flatnonzero(eligible)
    order = sorted(indices, key=lambda j: hashlib.sha256(
        f'RB07-SNIA-SCENARIO-v1:{int(catalog.group_id[j])}'.encode()).digest())[:24]
    ids = [int(catalog.group_id[j]) for j in order]
    if ids != required:
        raise ValueError('frozen selected group IDs differ from current raw source')
    return Sample(catalog.group_id[order], catalog.modulus[order],
                  catalog.modulus_error[order], catalog.vh_km_s[order],
                  catalog.direction[order])


class SelectedLaw:
    def __init__(self, sample: Sample, scenario: Scenario = Scenario(), distance_order=192, eta_order=40):
        if distance_order not in (128, 192, 256, 384, 512) or eta_order not in (24, 40, 64, 96, 128):
            raise ValueError('frozen quadrature orders required')
        self.sample, self.scenario = sample, scenario
        self.distance_order, self.eta_order = distance_order, eta_order
        z, w = leggauss(distance_order)
        self.x = (X_MAX + X_MIN)/2 + z*(X_MAX-X_MIN)/2
        logg = (scenario.alpha+1)*self.x - np.exp(self.x)/100
        self.log_gw = np.log(w) + logg - logsumexp(np.log(w)+logg)
        eh, ew = hermgauss(eta_order)
        self.eta = math.sqrt(2)*scenario.s_eta_mag*eh
        self.log_eta_w = np.log(ew) - .5*math.log(math.pi)
        self.y = C*np.log1p(sample.raw_vh/C)
        self.log_jac = -np.log1p(sample.raw_vh/C)

    @staticmethod
    def _theta(theta):
        if np.iscomplexobj(theta):raise ValueError('real endpoint coefficients required')
        theta = np.asarray(theta, float)
        if theta.shape != (4,) or not np.isfinite(theta).all():
            raise ValueError('finite H,Bx,By,Bz required')
        if not (40 <= theta[0] <= 110) or np.any(np.abs(theta[1:]) > 1500):
            raise ValueError('frozen H/B bounds exceeded')
        return theta

    def row_terms(self, theta):
        """Return log f_i(eta), log Z_i(eta); t is marginalized analytically."""
        H, *B = self._theta(theta)
        s = self.scenario; sample = self.sample
        distance = np.exp(self.x)[None, :]
        m = H*distance + (sample.direction @ np.array(B))[:, None] + \
            s.kappa*(75*distance)**2/C
        sy2 = s.s_u_km_s**2 + s.s_spec_km_s**2
        y = self.y[:, None]
        log_y = -.5*((y-m)**2/sy2 + math.log(2*math.pi*sy2))
        t_cond = m + s.s_u_km_s**2/sy2*(y-m)
        t_cond_var = s.s_u_km_s**2*s.s_spec_km_s**2/sy2
        cond_var = sample.sigma_mu[:, None]**2 + K*K*t_cond_var
        mu_cond = 25 + A*self.x[None, :] + K*t_cond
        mean_mu = 25 + A*self.x[None, :] + K*m
        marginal_sd = np.sqrt(sample.sigma_mu[:, None]**2 + K*K*s.s_u_km_s**2)
        # N x distance x eta, with one common eta grid for all rows.
        eta = self.eta[None, None, :]
        mu_diff = sample.mu[:, None, None] - mu_cond[:, :, None] - eta
        log_mu = -.5*(mu_diff**2/cond_var[:, :, None] +
                      np.log(2*math.pi*cond_var)[:, :, None])
        log_f = logsumexp(self.log_gw[None, :, None] + log_y[:, :, None] +
                          log_mu, axis=1) + self.log_jac[:, None]
        lower = (31 - mean_mu[:, :, None] - eta)/marginal_sd[:, :, None]
        upper = (35 - mean_mu[:, :, None] - eta)/marginal_sd[:, :, None]
        log_z = logsumexp(self.log_gw[None, :, None] +
                          log_cdf_interval(lower, upper), axis=1)
        if not np.isfinite(log_f).all() or not np.isfinite(log_z).all():
            raise FloatingPointError('unresolved selected density or normalizer')
        return log_f, log_z

    def log_likelihood(self, theta, *, held_index=None):
        f, z = self.row_terms(theta)
        if self.scenario.selection_semantics == SEMANTICS[0]:
            numerator = f.sum(axis=0)
            denominator = z.sum(axis=0)
            if held_index is not None:
                # Known selected slot remains: its f is replaced by Z.
                numerator = numerator - f[held_index] + z[held_index]
            return float(logsumexp(self.log_eta_w + numerator) -
                         logsumexp(self.log_eta_w + denominator))
        if held_index is not None:
            raise ValueError('LOO contract is preselection shared-prior only')
        return float(logsumexp(self.log_eta_w + (f-z).sum(axis=0)))

    def fit(self, starts=None, maxiter=400):
        if starts is None:
            starts = [(73., 0., 0., 0.), (73., .6, -2.8, -1.0)]
        attempts = []
        for start in starts:
            def objective(q):
                return -self.log_likelihood([q[0], *(100*q[1:])])
            result = minimize(objective, np.asarray(start), method='L-BFGS-B',
                              bounds=BOUNDS, options={'maxiter': maxiter, 'ftol': 2e-12,
                                                       'gtol': 1e-6, 'maxls': 30})
            theta = [float(result.x[0]), *(100*result.x[1:])]
            attempts.append({'theta':theta, 'logL':float(-result.fun),
                             'success':bool(result.success), 'message':str(result.message),
                             'nit':int(result.nit), 'nfev':int(result.nfev)})
        best = max(attempts, key=lambda r: r['logL'])
        if not best['success']:
            raise RuntimeError('fit did not converge: '+str(attempts))
        return {'best':best, 'attempts':attempts}

    def predictive(self, theta, draws=128, seed=7007):
        """Draw from fitted selected population, conditioned on fixed slots."""
        if not 1 <= draws <= 4096:
            raise ValueError('bounded predictive draw count required')
        f, z = self.row_terms(theta)
        del f
        rng = np.random.default_rng(seed)
        # One shared eta for each catalogue draw, from p(eta | selected slots).
        eta_logw = self.log_eta_w + z.sum(axis=0) if self.scenario.selection_semantics==SEMANTICS[0] else self.log_eta_w
        eta_probs = np.exp(eta_logw-logsumexp(eta_logw))
        eta_idx = rng.choice(len(self.eta), size=draws, p=eta_probs)
        H, *B = self._theta(theta)
        out_mu = np.empty((draws, len(self.sample.group_id)))
        out_vh = np.empty_like(out_mu)
        s = self.scenario
        sy2 = s.s_u_km_s**2+s.s_spec_km_s**2
        for row in range(len(self.sample.group_id)):
            dist = np.exp(self.x)
            m = H*dist + self.sample.direction[row] @ B + s.kappa*(75*dist)**2/C
            marginal_mean = 25+A*self.x+K*m
            marginal_var = self.sample.sigma_mu[row]**2+K*K*s.s_u_km_s**2
            sd = math.sqrt(marginal_var)
            for j, e_idx in enumerate(eta_idx):
                eta = self.eta[e_idx]
                lo, hi = (31-marginal_mean-eta)/sd, (35-marginal_mean-eta)/sd
                lx = self.log_gw + log_cdf_interval(lo,hi)
                xi = rng.choice(len(self.x),p=np.exp(lx-logsumexp(lx)))
                from scipy.stats import truncnorm
                mu = truncnorm.rvs(lo[xi],hi[xi],loc=marginal_mean[xi]+eta,
                                   scale=sd,random_state=rng)
                y_mean = m[xi]+K*s.s_u_km_s**2/marginal_var*(mu-marginal_mean[xi]-eta)
                y_var = sy2-(K*s.s_u_km_s**2)**2/marginal_var
                y = rng.normal(y_mean, math.sqrt(y_var))
                out_mu[j,row] = mu
                out_vh[j,row] = C*np.expm1(y/C)
        return {'seed':seed,'draws':draws,'generator_scope':'FRESH_SELECTED_CATALOGUE',
                'eta_draw_index':eta_idx.tolist(),
                'mu_quantiles':np.quantile(out_mu,[.05,.5,.95],axis=0).tolist(),
                'vh_quantiles':np.quantile(out_vh,[.05,.5,.95],axis=0).tolist(),
                'mu_interval_fraction':float(np.mean((out_mu>=31)&(out_mu<=35))),
                'selection_semantics':self.scenario.selection_semantics,
                'generating_law':'preselection eta|all selected slots OR declared postselection eta prior; x|selected slot,eta; truncated marginal mu; conditional y|mu; raw Vh=c*expm1(y/c)'}


def importance_posterior(law: SelectedLaw, fit_theta, *, seed=707, min_ess_fraction=.1,
                         max_normalized_weight=.05):
    """Optional proper uniform-bound posterior quadrature by Student-t importance.

    Admission thresholds are numerical Monte Carlo diagnostics, reported with
    values; the routine never calculates evidence or a physical claim.
    """
    from scipy.stats import multivariate_t
    if law.scenario.selection_semantics != SEMANTICS[0]:
        return {'status':'HOLD_POSTSELECTION_IMPORTANCE_NOT_IMPLEMENTED'}
    q0 = np.array([fit_theta[0], *(np.array(fit_theta[1:])/100)],float)
    steps = np.array([.02,.02,.02,.02])
    def nll(q):
        return -law.log_likelihood([q[0], *(100*q[1:])])
    center = nll(q0)
    h = np.zeros((4,4))
    for i in range(4):
        ei = np.eye(4)[i]*steps[i]
        h[i,i] = (nll(q0+ei)-2*center+nll(q0-ei))/steps[i]**2
        for j in range(i):
            ej = np.eye(4)[j]*steps[j]
            h[i,j] = h[j,i] = (nll(q0+ei+ej)-nll(q0+ei-ej)-
                              nll(q0-ei+ej)+nll(q0-ei-ej))/(4*steps[i]*steps[j])
    eigen = np.linalg.eigvalsh(h)
    if eigen.min() <= 0 or not np.isfinite(eigen).all():
        return {'status':'HOLD_HESSIAN_NOT_POSITIVE_DEFINITE','eigenvalues':eigen.tolist()}
    proposal = multivariate_t(loc=q0, shape=2*np.linalg.inv(h), df=5)
    rng = np.random.default_rng(seed)
    results = []
    accepted = []
    for n in (1024,2048):
        q = proposal.rvs(size=n if n==1024 else 1024,random_state=rng)
        accepted.extend(q)
        samples = np.array(accepted)
        inside = np.all((samples>=np.array(BOUNDS)[:,0]) &
                        (samples<=np.array(BOUNDS)[:,1]),axis=1)
        lp = np.full(len(samples),-np.inf)
        for i in np.flatnonzero(inside):
            lp[i] = law.log_likelihood([samples[i,0],*(100*samples[i,1:])])
        logw = lp-proposal.logpdf(samples)
        if not np.isfinite(logw).any():
            return {'status':'HOLD_IMPORTANCE_ALL_OUT_OF_BOUNDS','hessian_eigenvalues':eigen.tolist()}
        weight = np.exp(logw-logsumexp(logw))
        ess = float(1/np.sum(weight**2))
        theta = samples*np.array([1,100,100,100])
        mean = np.sum(weight[:,None]*theta,axis=0)
        variance = np.sum(weight[:,None]*(theta-mean)**2,axis=0)
        results.append({'draws':len(samples),'inside_bounds':int(inside.sum()),
                        'ess':ess,'ess_fraction':ess/len(samples),
                        'max_normalized_weight':float(weight.max()),
                        'mean':mean.tolist(),'mean_mcse_proxy':np.sqrt(variance/ess).tolist()})
    first, second = results
    difference = np.abs(np.array(first['mean'])-np.array(second['mean']))
    tolerance = 3*np.sqrt(np.array(first['mean_mcse_proxy'])**2+
                          np.array(second['mean_mcse_proxy'])**2)
    ok = (all(r['ess_fraction']>=min_ess_fraction and
              r['max_normalized_weight']<=max_normalized_weight for r in results)
          and np.all(difference<=tolerance))
    result = {'status':'NUMERICAL_POSTERIOR_DIAGNOSTIC_ONLY' if ok else 'HOLD_IMPORTANCE_DIAGNOSTICS',
              'prior':'proper independent uniform H[40,110], B_each[-1500,1500]',
              'proposal':'Student-t df5, fit-centered, twice inverse scaled Hessian',
              'seed':seed,'thresholds':{'min_ess_fraction':min_ess_fraction,
                                       'max_normalized_weight':max_normalized_weight,
                                       'mean_difference_mcse_factor':3},
              'hessian_eigenvalues':eigen.tolist(),'runs':results,
              'mean_difference':difference.tolist(),'difference_tolerance':tolerance.tolist(),
              'draw_ids':[f'RB07-importance-{seed}-{i:05d}' for i in range(len(theta))],
              'parameter_draws_H_B':theta.tolist(),'normalized_weights':weight.tolist(),
              'posterior_measure_scope':'proper finite-box conditional scenario posterior; no physical global-sector map',
              'refinement_scope':'nested importance cohort mean stability proxy, not independent convergence proof',
              'evidence_claim':False}
    if ok:
        # Integrate a small predictive check over weighted posterior draws.
        indices = rng.choice(len(samples),size=128,p=weight)
        mu, vh = [], []
        for j, i in enumerate(indices):
            draw = law.predictive(theta[i],draws=1,seed=seed+1000+j)
            mu.append(np.array(draw['mu_quantiles'])[1])
            vh.append(np.array(draw['vh_quantiles'])[1])
        result['posterior_predictive'] = {'draws':128,
            'mu_quantiles':np.quantile(mu,[.05,.5,.95],axis=0).tolist(),
            'vh_quantiles':np.quantile(vh,[.05,.5,.95],axis=0).tolist(),
            'status':'CONDITIONAL_SCENARIO_PPC_NO_NULL_ADMISSION'}
    return result


def conditional_t_parameters(m, x, eta, mu, y, sigma_mu, scenario):
    """Gaussian t | x,eta,observed mu,y under the frozen preselection law."""
    su2=scenario.s_u_km_s**2
    spec2=scenario.s_spec_km_s**2
    mu2=np.asarray(sigma_mu)**2
    precision=1/su2+1/spec2+K*K/mu2
    variance=1/precision
    mean=variance*(np.asarray(m)/su2+np.asarray(y)/spec2+
                   K*(np.asarray(mu)-25-A*np.asarray(x)-np.asarray(eta))/mu2)
    if not np.isfinite(mean).all() or not np.isfinite(variance).all() or np.any(variance<=0):
        raise FloatingPointError('latent redshift conditional unresolved')
    return mean,variance


def _weighted_quantiles(values,weights,quantiles=(.05,.5,.95)):
    values=np.asarray(values,float);weights=np.asarray(weights,float)
    if values.ndim!=2 or weights.shape!=(len(values),):
        raise ValueError('same-state weighted quantile dimensions')
    result=np.empty((len(quantiles),values.shape[1]))
    for column in range(values.shape[1]):
        order=np.argsort(values[:,column])
        cumulative=np.cumsum(weights[order]);cumulative[-1]=1.
        result[:,column]=values[order,column][np.searchsorted(cumulative,quantiles,side='left')]
    return result


def posterior_latent_bridge(law: SelectedLaw, posterior: dict, *, seed=7107):
    """One observed-data latent state and repeated measurement per theta draw.

    Every positive-weight theta retains its original draw ID and weight. A zero
    weight remains present with typed status and NaN latent arrays. No theta
    resampling or additional weight multiplication takes place.
    """
    if law.scenario.selection_semantics!=SEMANTICS[0]:
        raise ValueError('latent bridge requires PRESELECTION_SHARED_PRIOR')
    if posterior.get('status')!='NUMERICAL_POSTERIOR_DIAGNOSTIC_ONLY':
        raise ValueError('accepted finite-box importance posterior required')
    theta=np.asarray(posterior['parameter_draws_H_B'],float)
    weights=np.asarray(posterior['normalized_weights'],float)
    ids=np.asarray(posterior['draw_ids'],dtype=str)
    n=len(theta);rows=len(law.sample.group_id)
    if theta.shape!=(n,4) or weights.shape!=(n,) or ids.shape!=(n,) or \
            len(set(ids))!=n or not np.isfinite(weights).all() or np.any(weights<0) or \
            not np.isclose(weights.sum(),1,rtol=0,atol=1e-12):
        raise ValueError('posterior draw identity/weight contract failed')
    rng=np.random.default_rng(seed)
    shape=(n,rows)
    eta=np.full(n,np.nan);eta_index=np.full(n,-1,dtype=int)
    x=np.full(shape,np.nan);t=np.full(shape,np.nan)
    dA=np.full(shape,np.nan);ztrue=np.full(shape,np.nan);dL=np.full(shape,np.nan)
    rep_mu=np.full(shape,np.nan);rep_y=np.full(shape,np.nan);rep_vh=np.full(shape,np.nan)
    observed_chi2=np.full(n,np.nan);replicated_chi2=np.full(n,np.nan)
    status=np.full(n,'ZERO_WEIGHT',dtype='U24')
    sample=law.sample;s=law.scenario
    distance=np.exp(law.x)
    sy2=s.s_u_km_s**2+s.s_spec_km_s**2
    t_cond_var=s.s_u_km_s**2*s.s_spec_km_s**2/sy2
    for j in np.flatnonzero(weights>0):
        parameters=law._theta(theta[j])
        # Preselection posterior eta has the observed f numerator; Z belongs
        # only to the catalogue-selection denominator and never enters here.
        log_f,_=law.row_terms(parameters)
        eta_log=law.log_eta_w+log_f.sum(axis=0)
        if not np.isfinite(eta_log).any():
            raise FloatingPointError('shared eta conditional unresolved')
        eta_index[j]=int(rng.choice(len(law.eta),p=np.exp(eta_log-logsumexp(eta_log))))
        eta[j]=law.eta[eta_index[j]]
        H=parameters[0];B=parameters[1:]
        m=H*distance[None,:]+(sample.direction@B)[:,None]+s.kappa*(75*distance[None,:])**2/C
        y=law.y[:,None]
        tbar=m+s.s_u_km_s**2/sy2*(y-m)
        condvar=sample.sigma_mu[:,None]**2+K*K*t_cond_var
        mu_mean=25+A*law.x[None,:]+K*tbar+eta[j]
        log_y=-.5*((y-m)**2/sy2+math.log(2*math.pi*sy2))
        log_mu=-.5*((sample.mu[:,None]-mu_mean)**2/condvar+
                     np.log(2*math.pi*condvar))
        log_x=law.log_gw[None,:]+log_y+log_mu
        probabilities=np.exp(log_x-logsumexp(log_x,axis=1)[:,None])
        for row in range(rows):
            xi=int(rng.choice(len(law.x),p=probabilities[row]))
            x[j,row]=law.x[xi]
            mt=m[row,xi]
            tm,tv=conditional_t_parameters(mt,x[j,row],eta[j],sample.mu[row],law.y[row],
                                           sample.sigma_mu[row],s)
            t[j,row]=rng.normal(float(tm),math.sqrt(float(tv)))
        dA[j]=np.exp(x[j]);ztrue[j]=np.expm1(t[j]/C)
        dL[j]=np.exp(x[j]+2*t[j]/C)
        # Same latent state; only the two measurement errors are redrawn.
        model_mu=25+A*x[j]+K*t[j]+eta[j]
        rep_mu[j]=model_mu+rng.normal(0,sample.sigma_mu)
        rep_y[j]=t[j]+rng.normal(0,s.s_spec_km_s,size=rows)
        rep_vh[j]=C*np.expm1(rep_y[j]/C)
        observed_chi2[j]=float(np.sum(((sample.mu-model_mu)/sample.sigma_mu)**2+
                                      ((law.y-t[j])/s.s_spec_km_s)**2))
        replicated_chi2[j]=float(np.sum(((rep_mu[j]-model_mu)/sample.sigma_mu)**2+
                                        ((rep_y[j]-t[j])/s.s_spec_km_s)**2))
        status[j]='POSITIVE_WEIGHT'
    positive=weights>0
    if not positive.any():
        raise ValueError('no positive-weight posterior draws')
    w=weights[positive]  # unchanged, already normalized to one
    exceed=float(np.sum(w*(replicated_chi2[positive]>=observed_chi2[positive])))
    arrays={'draw_id':ids,'theta_H_B':theta,'normalized_weight':weights,
            'status':status,'eta_mag':eta,'eta_quadrature_index':eta_index,
            'x_log_dA_Mpc':x,'t_km_s':t,'dA_Mpc':dA,'z_true':ztrue,'dL_Mpc':dL,
            'mu_replicated_mag':rep_mu,'y_replicated_km_s':rep_y,
            'raw_Vh_replicated_km_s':rep_vh,
            'chi_square_48_observed_conditional':observed_chi2,
            'chi_square_48_replicated_conditional':replicated_chi2,
            'group_id':np.asarray(sample.group_id)}
    summary={'status':'CONDITIONAL_POSTERIOR_LATENT_BRIDGE',
             'seed':seed,'draws':n,'positive_weight_draws':int(positive.sum()),
             'zero_weight_draws':int((~positive).sum()),
             'weight_sum_unchanged':float(weights.sum()),
             'eta_conditioning':'log_eta_w + sum_i log f_i(eta); no Z_i',
             'x_conditioning':'log g_i(x) + log bivariate observed mu,y density',
             't_conditioning':'Gaussian precision su^-2 + sspec^-2 + K^2/smu^2',
             'same_state_distance_pushforward':{
                 'dA_Mpc_weighted_quantiles':_weighted_quantiles(dA[positive],w).tolist(),
                 'z_true_weighted_quantiles':_weighted_quantiles(ztrue[positive],w).tolist(),
                 'dL_Mpc_weighted_quantiles':_weighted_quantiles(dL[positive],w).tolist(),
                 'identity':'dL=dA*(1+z_true)^2 for each group/draw'},
             'repeated_measurement_ppc':{
                 'discrepancy':'sum 24 modulus and 24 y Gaussian standardized squared residuals, chi-square 48 conditional check',
                 'weighted_exceedance_descriptive':exceed,
                 'uniform_p_value_claim':False,
                 'latent_state_reused':True,'selection_reapplied':False,
                 'observed_chi2_weighted_mean':float(np.sum(w*observed_chi2[positive])),
                 'replicated_chi2_weighted_mean':float(np.sum(w*replicated_chi2[positive]))},
             'fresh_selected_catalogue_generator':'separate SelectedLaw.predictive; not this repeated-measurement PPC',
             'physical_MES':{'status':'UNKNOWN_PHYSICAL_SECTOR','unknown_mass':1.0,
                             'reason':'no physical map from heliocentric endpoint H/B to MES state'},
             'claim_tier':'CONDITIONAL_DIAGNOSTIC','scientific_admission':'NOT_EVALUATED'}
    return arrays,summary
