"""A22-05 finite vector-spherical-harmonic conditional Gaussian model."""
from pathlib import Path
import hashlib
import io
import json
import time
import zipfile

import healpy as hp
import numpy as np
from scipy.linalg import cho_factor, cho_solve
from scipy.special import sph_harm_y, logsumexp
from scipy.stats import chi2, beta as beta_distribution, norm
from scipy.optimize import brentq

HERE=Path(__file__).resolve().parent
RAW=Path('/mnt/extdrive/workdir/htt_open_data')
OUT=RAW/'a22_20261023/astrometry'
CONFIG=json.loads((HERE/'CONFIG.json').read_text())
NG,NA,NT,NS=18,24,42,18
NF=NG+NA+NT


def digest(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024**2),b''):h.update(b)
    return h.hexdigest()


def dipole(ra,dec):
    a,d=np.deg2rad(ra),np.deg2rad(dec)
    east=np.stack([-np.sin(a),np.cos(a),np.zeros_like(a)],axis=-1)
    north=np.stack([-np.sin(d)*np.cos(a),-np.sin(d)*np.sin(a),np.cos(d)],axis=-1)
    # Physical B1 = omega cross n. Generic VSH B=n cross E has opposite l1 sign.
    return np.stack([np.concatenate([east,north],axis=-1),
                     np.concatenate([north,-east],axis=-1)],axis=1)


def vsh(ra,dec,ells):
    theta=np.deg2rad(90-np.asarray(dec));phi=np.deg2rad(ra)
    if np.any(np.sin(theta)==0):raise ValueError('coordinate pole requires another tangent chart')
    blocks=[]
    for ell in ells:
        fields=[]
        for m in range(-ell,ell+1):
            _,grad=sph_harm_y(ell,abs(m),theta,phi,diff_n=1)
            if m==0:g=grad.real
            elif m>0:g=np.sqrt(2)*(-1)**m*grad.real
            else:g=np.sqrt(2)*(-1)**abs(m)*grad.imag
            fields.append(np.stack([g[:,1]/np.sin(theta),-g[:,0]],axis=1)*np.sqrt(4*np.pi/(ell*(ell+1))))
        e=np.stack(fields,axis=-1)
        b=np.stack([-e[:,1,:],e[:,0,:]],axis=1)
        blocks.extend([e,b])
    return np.concatenate(blocks,axis=-1)


def template_reference():
    folder=RAW/'adversarial20261022/quaia'
    maps=[]
    with zipfile.ZipFile(folder/'selection_function_template_maps.zip') as z:
        for name in CONFIG['templates']:
            maps.append(np.load(io.BytesIO(z.read(f'selection_function_template_maps/map_{name}_NSIDE64.npy')),allow_pickle=False))
    maps=np.stack(maps,axis=1).astype(float)
    center=maps.mean(axis=0);scale=maps.std(axis=0)
    if np.any(scale<=0):raise ValueError('constant template')
    z=(maps-center)/scale
    ra,dec=hp.pix2ang(64,np.arange(49152),lonlat=True,nest=False)
    x=dipole(ra,dec)
    factors=np.sqrt(np.einsum('nt,nkp->tp',z*z,x*x)/len(ra))
    if not np.isfinite(factors).all() or np.any(factors<=0):raise ValueError('invalid vector template normalization')
    return center,scale,factors


def design(ra,dec,z,templates,reference):
    x=dipole(ra,dec)
    bins=np.searchsorted(CONFIG['z_edges'],z,side='right')-1
    if np.any((bins<0)|(bins>2)):raise ValueError('reported-z outside fixed cohorts')
    d=np.zeros((len(ra),2,NG))
    for b in range(3):
        keep=bins==b;d[keep,:,6*b:6*b+6]=x[keep]
    angular=vsh(ra,dec,[2,3])
    center,scale,factors=reference
    temp=(templates-center)/scale
    ht=np.einsum('nt,nkp->nktp',temp,x).reshape(len(ra),2,NT)/factors.ravel()
    stress=vsh(ra,dec,[4])
    return np.concatenate([d,angular,ht,stress],axis=-1),bins


def whiten(x,y,sa,sd,rho):
    if not all(np.isfinite(v).all() for v in (x,y,sa,sd,rho)) or np.any(sa<=0) or np.any(sd<=0) or np.any(abs(rho)>=1):
        raise ValueError('invalid marginal PM covariance/data')
    root=np.sqrt(1-rho*rho)
    wx=np.stack([x[:,0]/sa[:,None],(x[:,1]/sd[:,None]-rho[:,None]*x[:,0]/sa[:,None])/root[:,None]],axis=1)
    wy=np.stack([y[:,0]/sa,(y[:,1]/sd-rho*y[:,0]/sa)/root],axis=1)
    return wx.reshape(-1,x.shape[-1]),wy.ravel()


def spd_inverse(a):
    if not np.isfinite(a).all() or not np.allclose(a,a.T,rtol=1e-11,atol=1e-13):raise ArithmeticError('nonfinite/asymmetric normal matrix')
    return cho_solve(cho_factor((a+a.T)/2,lower=True),np.eye(len(a)))


def lowrank_posterior(gram,p):
    # p is a nonnegative diagonal coefficient prior; zero is represented exactly.
    if np.any(p<0) or not np.isfinite(p).all():raise ValueError('finite PSD prior required')
    return factor_posterior(gram,np.diag(np.sqrt(p)))


def factor_posterior(gram,l):
    if not np.isfinite(gram).all() or not np.isfinite(l).all():raise ValueError('finite Gaussian operator required')
    matrix=np.eye(l.shape[1])+l.T@gram@l
    cf=cho_factor((matrix+matrix.T)/2,lower=True)
    r=l@cho_solve(cf,l.T)
    logdet=2*np.log(np.diag(cf[0])).sum()
    return (r+r.T)/2,float(logdet)


def radial_cut_failure_bound(radius,mean_bound,largest_variance):
    r,b,v=np.broadcast_arrays(radius,mean_bound,largest_variance)
    if not all(np.isfinite(x).all() for x in (r,b,v)) or np.any(r<=0) or np.any(b<0) or np.any(v<=0):
        raise ValueError('positive finite cut/covariance and nonnegative mean bound required')
    return np.exp(-np.maximum(r-b,0)**2/(2*v))


def family(gram):
    g=gram[:NF,:NF]
    models=[]
    for lmax in CONFIG['angular_lmax']:
        qa=10 if lmax==2 else 24
        for ta in CONFIG['angular_and_template_RMS_grid_uasyr']:
            for tt in CONFIG['angular_and_template_RMS_grid_uasyr']:
                p=np.zeros(NF);p[:NG]=CONFIG['signal_prior_sigma_uasyr']**2
                p[NG:NG+qa]=ta*ta/qa;p[NG+NA:NF]=tt*tt/NT
                r,ld=lowrank_posterior(g,p)
                rh,_=lowrank_posterior(g[NG:,NG:],p[NG:])
                k=np.concatenate([np.eye(NG),-g[:NG,NG:]@rh],axis=1)
                f=k@g[:,:NG];f=(f+f.T)/2
                cov=spd_inverse(f)
                scaled=f/np.sqrt(np.diag(f)[:,None]*np.diag(f)[None,:])
                condition=float(np.linalg.cond(scaled))
                if condition>1e10:raise ArithmeticError('conditional signal information numerically unresolved')
                models.append(dict(lmax=lmax,tau_angular=ta,tau_template=tt,p=p,R=r,logdet=ld,
                                   gls_map=cov@k,gls_cov=cov,posterior_cov=r[:NG,:NG],condition=condition))
    return models


def mixture(models,b):
    means=np.array([m['R'][:NG]@b for m in models])
    logz=np.array([-.5*(m['logdet']-b@m['R']@b) for m in models])
    w=np.exp(logz-logsumexp(logz))
    mean=w@means
    cov=sum(wj*(m['posterior_cov']+np.outer(mj-mean,mj-mean)) for wj,m,mj in zip(w,models,means))
    return mean,cov,w,means


def coordinate_interval(models,weights,means,j,level=.95):
    sd=np.sqrt([m['posterior_cov'][j,j] for m in models]);mu=means[:,j]
    low=float(np.min(mu-12*sd));high=float(np.max(mu+12*sd))
    def q(prob):return brentq(lambda x:weights@norm.cdf((x-mu)/sd)-prob,low,high,xtol=1e-9)
    return [q((1-level)/2),q((1+level)/2)]


def rank_diagnostic(gram):
    diagonal=np.diag(gram)
    live=diagonal>0
    g=gram[np.ix_(live,live)]/np.sqrt(diagonal[live,None]*diagonal[None,live])
    ev=np.linalg.eigvalsh((g+g.T)/2)
    return dict(columns=len(gram),zero_columns=int((~live).sum()),scaled_gram_eigenvalues=ev.tolist(),
                numerical_rank=int(np.sum(ev>max(ev[-1],1)*1e-10)),
                rank_convention='scaled Gram eigenvalue relative1e-10; normal-equation precision ceiling explicit')


def accumulate():
    join=HERE.parent/'quaia_join/SUPPLEMENT_RESULT.json';meta=json.loads(join.read_text())
    cache=Path(meta['artifact']['path'])
    if digest(cache)!=meta['artifact']['sha256']:raise ValueError('qualified join drift')
    with np.load(cache,allow_pickle=False) as f:a={k:f[k] for k in f.files}
    n=len(a['source_id']);ref=template_reference()
    sums=[]
    for _ in range(2):sums.append(dict(G=np.zeros((NF+NS,NF+NS)),b=np.zeros(NF+NS),ywy=0.,logdetN=0.,n=0,zcounts=np.zeros(3,int),cut_Q=0.))
    qfull=0.;qmargin=0.;marginmask=np.zeros(n,bool)
    for start in range(0,n,4096):
        sl=slice(start,min(start+4096,n));ra=a['ra'][sl];dec=a['dec'][sl]
        temp=np.column_stack([a['template_'+name][sl] for name in CONFIG['templates']])
        x,bins=design(ra,dec,a['redshift_quaia'][sl],temp,ref)
        y=np.column_stack([a['pmra_uasyr'][sl],a['pmdec_uasyr'][sl]])
        sa=a['pmra_error_uasyr'][sl];sd=a['pmdec_error_uasyr'][sl];rho=a['gaia_pmra_pmdec_corr'][sl]
        h=x[:,:,NG:NF]
        # Complete angular l2/l3 E+B sets both give total-RMS100 covariance5000I.
        cov=100**2/NT*np.einsum('nik,njk->nij',h[:,:,NA:],h[:,:,NA:])
        cov[:,0,0]+=sa*sa+5000;cov[:,1,1]+=sd*sd+5000
        cov[:,0,1]+=rho*sa*sd;cov[:,1,0]+=rho*sa*sd
        largest=.5*(cov[:,0,0]+cov[:,1,1]+np.sqrt((cov[:,0,0]-cov[:,1,1])**2+4*cov[:,0,1]**2))
        radius=1000*10**(.4*(a['phot_g_mean_mag'][sl].astype(float)-18.25))
        gap=np.maximum(radius-100*np.sqrt(2),0)
        qi=radial_cut_failure_bound(radius,100*np.sqrt(2),largest)
        keep=gap>=np.sqrt(2*largest*np.log(n/.01))
        marginmask[sl]=keep;qfull+=float(qi.sum());qmargin+=float(qi[keep].sum())
        for item,sel in zip(sums,[np.ones(len(ra),bool),keep]):
            if not sel.any():continue
            wx,wy=whiten(x[sel],y[sel],sa[sel],sd[sel],rho[sel])
            item['G']+=wx.T@wx;item['b']+=wx.T@wy;item['ywy']+=wy@wy
            item['logdetN']+=np.sum(2*np.log(sa[sel])+2*np.log(sd[sel])+np.log1p(-rho[sel]**2))
            item['n']+=int(sel.sum());item['zcounts']+=np.bincount(bins[sel],minlength=3)
    sums[0]['cut_Q']=qfull;sums[1]['cut_Q']=qmargin
    if qmargin>.01000000001:raise ArithmeticError('predeclared known-cut union bound failed')
    OUT.mkdir(parents=True,exist_ok=True)
    for name,item in zip(['full','margin'],sums):np.savez_compressed(OUT/(name+'_stats.npz'),**item)
    provenance=dict(join_result_sha256=digest(join),row_cache_sha256=digest(cache),n=n,
                    reference_center=ref[0].tolist(),reference_scale=ref[1].tolist(),vector_column_RMS=ref[2].tolist(),
                    margin_rows=int(marginmask.sum()),config_sha256=digest(HERE/'CONFIG.json'),
                    full_stats_sha256=digest(OUT/'full_stats.npz'),margin_stats_sha256=digest(OUT/'margin_stats.npz'))
    (OUT/'stats_receipt.json').write_text(json.dumps(provenance,indent=2)+'\n')
    return sums,provenance


def binomial_interval(k,n):
    return [0. if k==0 else float(beta_distribution.ppf(.025,k,n-k+1)),
            1. if k==n else float(beta_distribution.ppf(.975,k+1,n-k))]


def score_root(g):
    ev,v=np.linalg.eigh((g+g.T)/2)
    if ev[0]<-1e-10*max(ev[-1],1):raise ArithmeticError('non-PSD sufficient-statistic Gram')
    root=v*np.sqrt(np.maximum(ev,0))[None,:]
    if np.linalg.norm(root@root.T-g)/max(np.linalg.norm(g),1)>1e-10:raise ArithmeticError('score covariance reconstruction')
    return root


def mocks(item,models):
    rng=np.random.default_rng(CONFIG['mock_seed']);g=item['G'];gf=g[:NF,:NF]
    root=score_root(gf);rows=[];nmock=CONFIG['known_covariance_mock_count_per_case']
    signals=[]
    for kind in ['zero','common_E1','differential_bin_E1']:
        truth=np.zeros(NG)
        if kind=='common_E1':
            for b in range(3):truth[6*b:6*b+3]=[5,-2,3]
        if kind=='differential_bin_E1':truth[[0,6,12]]=[10,0,-10]
        signals.append((kind,truth))
    for ta in (0,10,30,100):
        model=next(m for m in models if m['lmax']==3 and m['tau_angular']==ta and m['tau_template']==ta)
        for kind,truth in signals:
            latent=rng.normal(size=(nmock,NF))*np.sqrt(model['p'])
            latent[:,:NG]=truth
            b=latent@gf+(rng.normal(size=(nmock,NF))@root.T)
            estimates=b@model['gls_map'].T;error=estimates-truth
            stat=np.einsum('ni,ij,nj->n',error,spd_inverse(model['gls_cov']),error)
            k=int(np.sum(stat<=chi2.ppf(.95,NG)))
            rows.append(dict(tau_angular=ta,tau_template=ta,signal=kind,n=nmock,covered=k,coverage=k/nmock,exact_binomial95=binomial_interval(k,nmock)))
    model=next(m for m in models if m['lmax']==3 and m['tau_angular']==30 and m['tau_template']==30)
    stress=[]
    for kind in ['omitted_E4_B4','unequal_E_B','template_correlated_mean']:
        latent=np.zeros((nmock,NF+NS));latent[:,:NF]=rng.normal(size=(nmock,NF))*np.sqrt(model['p']);latent[:,:NG]=0
        if kind=='omitted_E4_B4':latent[:,NF:]=rng.normal(size=(nmock,NS))*12/np.sqrt(NS)
        if kind=='unequal_E_B':
            e=np.r_[np.arange(NG,NG+5),np.arange(NG+10,NG+17)]
            bidx=np.r_[np.arange(NG+5,NG+10),np.arange(NG+17,NG+24)]
            latent[:,e]*=np.sqrt(2);latent[:,bidx]=0
        if kind=='template_correlated_mean':latent[:,NG+NA]+=100
        scores=latent@g[:,:NF]+rng.normal(size=(nmock,NF))@root.T
        estimates=scores@model['gls_map'].T
        stat=np.einsum('ni,ij,nj->n',estimates,spd_inverse(model['gls_cov']),estimates)
        k=int(np.sum(stat<=chi2.ppf(.95,NG)))
        stress.append(dict(kind=kind,n=nmock,coverage=k/nmock,covered=k,exact_binomial95=binomial_interval(k,nmock),mean_bias_uasyr=estimates.mean(axis=0).tolist()))
    # Prior-predictive calibration of the actual finite hyperparameter mixture.
    total=CONFIG['prior_predictive_mixture_mock_count'];indices=[0,6,12];covered=np.zeros(3,int)
    for _ in range(total):
        true=models[rng.integers(len(models))]
        latent=rng.normal(size=NF)*np.sqrt(true['p'])
        score=gf@latent+root@rng.normal(size=NF)
        _,_,weights,means=mixture(models,score)
        for j,coord in enumerate(indices):
            low,high=coordinate_interval(models,weights,means,coord)
            covered[j]+=low<=latent[coord]<=high
    prior=[dict(coordinate=j,n=total,covered=int(k),coverage=float(k/total),exact_binomial95=binomial_interval(int(k),total)) for j,k in zip(indices,covered)]
    return dict(known_covariance_joint18=rows,misspecification_controls=stress,
                mixture_prior_predictive_marginal=prior,
                interpretation='Whole-field Gaussian score-space draws, not iid source bootstrap or empirical Gaia selection coverage')


def main():
    start=time.perf_counter();items,receipt=accumulate();outputs=[];all_models=[]
    for name,item in zip(['full','known_cut_margin'],items):
        models=family(item['G']);b=item['b'][:NF];mean,cov,w,means=mixture(models,b)
        summaries=[]
        for i,m in enumerate(models):
            summaries.append(dict(lmax=m['lmax'],tau_angular=m['tau_angular'],tau_template=m['tau_template'],
                conditional_gls_mean_uasyr=(m['gls_map']@b).tolist(),conditional_gls_cov_uas2yr2=m['gls_cov'].tolist(),
                posterior_mean_uasyr=means[i].tolist(),posterior_cov_uas2yr2=m['posterior_cov'].tolist(),
                posterior_hyper_weight=float(w[i]),scaled_signal_condition=m['condition']))
        contrast=np.zeros((3,NG));contrast[:,0:3]=np.eye(3);contrast[:,12:15]=-np.eye(3)
        q=float(item['cut_Q'])
        outputs.append(dict(cohort=name,n=item['n'],zcounts=item['zcounts'].tolist(),rank=rank_diagnostic(item['G'][:NF,:NF]),
            known_PM_cut_union_Q=q,known_cut_log_normalizer_upper=None if q>=1 else float(-np.log1p(-q)),
            mixture_mean_uasyr=mean.tolist(),mixture_covariance_uas2yr2=cov.tolist(),
            marginal95_intervals=[coordinate_interval(models,w,means,j) for j in range(NG)],
            low_minus_high_E1=dict(mean_uasyr=(contrast@mean).tolist(),covariance_uas2yr2=(contrast@cov@contrast.T).tolist()),
            conditional_grid=summaries))
        all_models.append(models)
    simulation=mocks(items[0],all_models[0])
    result=dict(owner='htt',claim_tier='C0_CONDITIONAL_GAUSSIAN_EXPERIMENT',transfer_source='none',
                config=CONFIG,source_receipt=receipt,cohorts=outputs,validation_mocks=simulation,seconds=time.perf_counter()-start,
                local_cosmic_common_E1=dict(columns=6,rank=3,null='(delta,-delta); no qualified distinct physical depth law'),
                covariance_scope='per-source PM blocks + declared finite Gaussian common-field family; empirical spatial law UNKNOWN',
                selection_scope='Known radial PM-cut bound on compact signal domain only; Gaia classifier law UNKNOWN; posterior family remains untruncated working model',
                caveats=['Reported-z cohorts are not physical distance bins; catastrophic redshift error law absent.',
                         'B1 has frame-spin degeneracy; common E1 local/cosmic components are not identified.',
                         '32-model grid and signal prior are declared; source covariance scales do not certify the grid as an empirical bound.',
                         'Conditional/prior-predictive mock coverage does not calibrate full Gaia/Quaia selection or original K03/K05.'])
    (HERE/'RESULT.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib import pyplot as plt
    fig,ax=plt.subplots(1,3,figsize=(13,4))
    for k,c in enumerate(outputs):
        means=np.array(c['mixture_mean_uasyr']).reshape(3,6)
        sd=np.sqrt(np.diag(c['mixture_covariance_uas2yr2'])).reshape(3,6)
        for b in range(3):ax[k].errorbar(np.arange(6)+.15*b,means[b],yerr=1.96*sd[b],fmt='o',label=f'reported z bin{b+1}')
        ax[k].set(xticks=np.arange(6),xticklabels=['Ex','Ey','Ez','Bx','By','Bz'],ylabel='microas/yr; moment +/-1.96 sigma',title=c['cohort'])
    ax[0].legend(fontsize=7)
    vals=simulation['misspecification_controls']
    ax[2].bar(np.arange(len(vals)),[x['coverage'] for x in vals]);ax[2].axhline(.95,color='k',ls='--')
    ax[2].set(xticks=np.arange(3),xticklabels=['omitted l4','unequal E/B','template mean'],ylim=(0,1),ylabel='conditional joint18 coverage')
    ax[2].tick_params(axis='x',rotation=25)
    fig.suptitle('Declared Gaussian field experiment; spatial covariance / full selection UNKNOWN')
    fig.tight_layout()
    for ext in ('png','pdf'):fig.savefig(HERE/f'ASTROMETRY.{ext}',dpi=160)
    plt.close(fig)
    print(json.dumps(dict(full_rows=outputs[0]['n'],margin_rows=outputs[1]['n'],margin_Q=outputs[1]['known_PM_cut_union_Q'],seconds=result['seconds'])))


if __name__=='__main__':main()
