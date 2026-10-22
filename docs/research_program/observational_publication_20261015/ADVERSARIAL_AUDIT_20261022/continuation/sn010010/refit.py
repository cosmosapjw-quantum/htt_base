"""One public PS1MD light curve, conditional released-SALT2 spectral transport."""
from pathlib import Path
import hashlib
import json
import sys

import numpy as np
from astropy.io import fits
from scipy.optimize import least_squares

TOOLS=Path('/mnt/extdrive/workdir/htt_open_data/a22_20261023/tools')
sys.path.insert(0,str(TOOLS))
import sncosmo
import extinction

HERE=Path(__file__).resolve().parent
RAW=Path('/mnt/extdrive/workdir/htt_open_data/a22_20261023/sn010010')
CFG=json.loads((HERE/'CONFIG.json').read_text())


def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def read_inputs():
    identities=json.loads((HERE/'SOURCE_IDENTITIES.json').read_text())
    for e in identities['files']:
        p=Path(e['path'])
        if p.stat().st_size!=e['bytes'] or digest(p)!=e['sha256']:raise ValueError('immutable source identity drift')
        if p.suffix=='.gz':
            import gzip
            if p.with_suffix('').read_bytes()!=gzip.decompress(p.read_bytes()):raise ValueError('decoded model drift')
    f=RAW/'1_DATA/photometry/Pantheon_PS1MD/PS1_PSc010010.txt'
    meta={};rows=[]
    for line in f.read_text().splitlines():
        if line.startswith('OBS:'):
            x=line.split();rows.append(dict(row=len(rows),mjd=float(x[1]),band=x[2],flux=float(x[4]),error=float(x[5])))
        elif ':' in line:
            k,v=line.split(':',1);fields=v.strip().split();meta[k]=fields[0] if fields else ''
    if meta['SNID']!='010010' or meta['SURVEY']!='PS1MD' or len(rows)!=59 or int(meta['NOBS'])!=59:raise ValueError('same SN identity/count')
    if float(meta['MWEBV'])!=.0204 or float(meta['REDSHIFT_HELIO'])!=CFG['zHEL']:raise ValueError('observer metadata')
    published=Path('/mnt/extdrive/workdir/htt_open_data/pantheonplus/c447f0f/Pantheon_SH0ES.dat')
    if digest(published)!='1cb0fc379ef066afdc2ffd1857681cc478024570d8a3eba284fb645775198cf8':raise ValueError('published summary drift')
    lines=published.read_text().splitlines();header=lines[0].split();matches=[]
    for line in lines[1:]:
        r=dict(zip(header,line.split()))
        if r['CID']=='010010' and int(r['IDSURVEY'])==15:matches.append(r)
    if len(matches)!=1:raise ValueError('CID plus survey crosswalk')
    overrides={}
    for p in sorted((RAW/'1_DATA/header_overrides').glob('*.txt')):
        hits=[l.split()[2] for l in p.read_text().splitlines() if len(l.split())==3 and l.split()[:2]==['SN:','010010']]
        if len(hits)!=1:raise ValueError('unique header override')
        overrides[p.stem]=float(hits[0])
    if overrides['HOSTGAL_LOGMASS']!=float(matches[0]['HOST_LOGMASS']):raise ValueError('host override/release inconsistency')
    return rows,meta,matches[0],overrides


class Experiment:
    def __init__(self,step=.5):
        self.step=step
        model=RAW/'3_SALT2/SALT2_B21trained_withsys/SALT2.MODEL000'
        self.source=sncosmo.SALT2Source(modeldir=str(model),name='release-c447-MODEL000')
        self.bands={};self.ab_comparison={};self.centers={}
        with fits.open(RAW/'2_CALIBRATION/SNANA_kcor/kcor_PS1_v6_1.fits') as f:
            filters=f[5].data;primary=f[6].data;zps=f[1].data
            wl=np.array(filters['wavelength (A)'],float);aw=np.array(primary['wavelength (A)'],float);ab=np.array(primary['AB'],float)
            for band in CFG['bands']:
                original=np.array(filters['PS1-'+band],float)
                if not np.isfinite(original).all() or np.any(original<0) or not np.any(original>0):raise ValueError('filter transmission')
                self.centers[band]=float(np.sum(wl*original)/np.sum(original))
                live=np.flatnonzero(original>0);lo=wl[max(live[0]-1,0)];hi=wl[min(live[-1]+1,len(wl)-1)]
                wave=np.linspace(lo,hi,int(round((hi-lo)/step))+1);trans=np.interp(wave,wl,original)
                dx=(hi-lo)/(len(wave)-1);weight=np.full(len(wave),dx);weight[[0,-1]]*=.5
                kernel=wave*trans*weight
                p=[r for r in zps if r['Filter Name']=='PS1-'+band]
                if len(p)!=1 or p[0]['Primary Name']!='AB':raise ValueError('compiled calibration identity')
                mag=float(p[0]['Primary Mag']);primary_flux=float(kernel@np.interp(wave,aw,ab))
                theoretical=3.631e-20*2.99792458e18/wave**2
                comparison=float((kernel@theoretical)/primary_flux-1)
                self.ab_comparison[band]=comparison
                # Use the actual compiled primary regardless of tiny reference mismatch.
                scale=10**(.4*(27.5-mag))/primary_flux
                self.bands[band]=dict(wave=wave,kernel=kernel,primary_flux=primary_flux,primary_mag=mag,scale=scale)
        if any(not 3000<=v/(1+CFG['zHEL'])<=7000 for v in self.centers.values()):raise ValueError('frozen filter-center domain')

    def primary_probe(self,band):
        b=self.bands[band]
        return b['primary_flux']*b['scale']

    def predict(self,theta,times,bands,z,mw_lambda=1.,spectral_lambda=1.,boost=1.):
        dt0,lnx0,x1,c=theta;source=self.source
        source.set(x0=np.exp(lnx0),x1=x1,c=c)
        values=[];atten={}
        for band in set(bands):
            wave=self.bands[band]['wave']*mw_lambda
            atten[band]=10**(-.4*extinction.fitzpatrick99(wave,CFG['MW']['Rv']*CFG['MW']['raw_EBV']*CFG['MW']['scale'],CFG['MW']['Rv']))
        for time,band in zip(times,bands):
            b=self.bands[band];rest=b['wave']*spectral_lambda/(1+z);phase=(time-dt0)/(1+z)
            if phase<source.minphase() or phase>source.maxphase() or rest[0]<source.minwave() or rest[-1]>source.maxwave():raise ValueError('SALT2 spectral/phase extrapolation forbidden')
            f=source.flux(float(phase),rest)/(1+z)*atten[band]*boost*10**(-.4*CFG['SALT_MAG_OFFSET'])
            values.append(float((f*b['kernel']).sum()*b['scale']))
        if not np.isfinite(values).all():raise ArithmeticError('nonfinite predicted photon flux')
        return np.array(values)


def fit(exp,initial,times,bands,y,errors,z,mw_lambda=1.):
    lower=np.array([-5,-30,-3,-.3]);upper=np.array([5,0,3,.3])
    def residual(theta):return (exp.predict(theta,times,bands,z,mw_lambda=mw_lambda)-y)/errors
    before=float(residual(initial)@residual(initial))
    sol=least_squares(residual,initial,bounds=(lower,upper),xtol=1e-12,ftol=1e-12,gtol=1e-10,max_nfev=1000,x_scale='jac')
    scaled=sol.jac/np.linalg.norm(sol.jac,axis=0);singular=np.linalg.svd(scaled,compute_uv=False)
    valid=bool(sol.success and np.isfinite(sol.fun).all() and np.all(sol.x>lower+1e-7) and np.all(sol.x<upper-1e-7) and singular[-1]>singular[0]*1e-10 and sol.fun@sol.fun<=before+1e-8*max(before,1))
    if not valid:raise ArithmeticError('conditional fit convergence/interior/rank/objective failed')
    return sol.x,dict(theta=sol.x.tolist(),chi2=float(sol.fun@sol.fun),initial_chi2=before,nfev=sol.nfev,scaled_jacobian_singular_values=singular.tolist(),weighted_residuals=sol.fun.tolist())


def main():
    rows,meta,summary,overrides=read_inputs();exp=Experiment();kept=[];excluded=[]
    for row in rows:
        reason=None
        if row['band'] not in CFG['bands']:reason='frozen rest-filter-center domain'
        elif not -15<=(row['mjd']-CFG['T_ref_MJD'])/(1+CFG['zHEL'])<=45:reason='frozen published-anchor rest-phase window'
        if reason:excluded.append(dict(row=row['row'],reason=reason));continue
        if not np.isfinite([row['flux'],row['error']]).all() or row['error']<=0:raise ValueError('measurement row invalid')
        kept.append(row)
    times=np.array([r['mjd']-CFG['T_ref_MJD'] for r in kept]);bands=np.array([r['band'] for r in kept]);y=np.array([r['flux'] for r in kept]);error=np.array([r['error'] for r in kept])
    published=np.array([float(summary['PKMJD'])-CFG['T_ref_MJD'],np.log(float(summary['x0'])),float(summary['x1']),float(summary['c'])])
    initial=published+np.array([.2,np.log(1.05),-.05,.01])
    theta,baseline=fit(exp,initial,times,bands,y,error,CFG['zHEL'])
    dof=len(y)-4;baseline.update(n=len(y),ndof=dof,reduced_chi2=baseline['chi2']/dof,
        working_adequacy='PASS_DECLARED_SCREEN' if baseline['chi2']/dof<=3 else 'BASELINE_ADEQUACY_HOLD',
        selected_rows=[r['row'] for r in kept],excluded_rows=excluded,
        published_summary={k:summary[k] for k in ['CID','IDSURVEY','x0','x1','c','PKMJD','mB','FITCHI2','NDOF']})
    defects=dict(x0_relative=float(np.exp(theta[1]-published[1])-1),x1=float(theta[2]-published[2]),c=float(theta[3]-published[3]),t0_day=float(theta[0]-published[0]))
    baseline['published_parity_defects']=defects
    baseline['published_parity']='PARITY_REPRODUCED_WITHIN_DECLARED_SCREEN' if all(abs(v)<=CFG['published_parity_tolerances'][k] for k,v in defects.items()) else 'PARITY_NOT_REPRODUCED'
    refined=Experiment(step=.25)
    p=exp.predict(theta,times,bands,CFG['zHEL']);pr=refined.predict(theta,times,bands,CFG['zHEL'])
    qerr=float(np.max(abs(p/pr-1)))
    if qerr>1e-6:raise ArithmeticError('photon quadrature refinement failed')
    paired=[]
    for delta in CFG['deltas']:
        tp=times/delta;zp=(1+CFG['zHEL'])/delta-1
        target=exp.predict(theta,delta*tp,bands,CFG['zHEL'],mw_lambda=delta,spectral_lambda=delta,boost=delta**3)
        expected=theta.copy();expected[0]/=delta;expected[1]+=2*np.log(delta)
        for label,mwf in [('covariant_MW',delta),('frozen_observer_MW',1.)]:
            start=expected+np.array([.1,np.log(.98),.03,-.005])
            fitted,info=fit(exp,start,tp,bands,target,error,zp,mw_lambda=mwf)
            diff=fitted-expected;kappa=float(-2.5/np.log(10)*diff[1])
            if label=='covariant_MW' and (abs(kappa)>1e-6 or max(abs(diff[2:]))>1e-5 or abs(diff[0])>1e-4):raise ArithmeticError('covariant paired fit tolerance failed')
            paired.append(dict(delta=delta,MW_experiment=label,fit=info,defect_from_covariant_parameters=diff.tolist(),kappa_amplitude_mag=kappa,
                response_scope='fitted attenuated MODEL000, not observed residual transport/global BBC/PV'))
    # Refit one frozen-MW cell at refined quadrature to resolve a nonidentity scale.
    delta=1.01;tp=times/delta;zp=(1+CFG['zHEL'])/delta-1
    target=refined.predict(theta,delta*tp,bands,CFG['zHEL'],mw_lambda=delta,spectral_lambda=delta,boost=delta**3)
    basecase=next(r for r in paired if r['delta']==delta and r['MW_experiment']=='frozen_observer_MW')
    fine,_=fit(refined,np.array(basecase['fit']['theta']),tp,bands,target,error,zp,mw_lambda=1.)
    uncertainty=np.abs(fine-np.array(basecase['fit']['theta']))
    result=dict(owner='htt',claim_tier=CFG['claim_tier'],transfer_source='none',config_sha256=digest(HERE/'CONFIG.json'),source_identities_sha256=digest(HERE/'SOURCE_IDENTITIES.json'),
        code_sha256=digest(Path(__file__)),versions=dict(sncosmo=sncosmo.__version__,extinction=extinction.__version__,numpy=np.__version__),
        baseline=baseline,header_overrides=overrides,compiled_rest_filter_centers_A={k:v/(1+CFG['zHEL']) for k,v in exp.centers.items()},
        compiled_AB_vs_3631Jy_relative=exp.ab_comparison,calibration_reference='compiled KCOR AB primary integral explicitly',
        quadrature_max_relative=qerr,paired=paired,frozen_MW_delta101_refinement_parameter_shift=uncertainty.tolist(),
        empirical_total_kappa='UNKNOWN',PV_group_eta='UNKNOWN',published_fit_configuration='PS1.nml and observed FITRES/private nominal model binding missing',
        caveats=['Working diagonal measurement likelihood omits producer model covariance/error floor and global calibration/BBC selection.',
                 'Fixed row membership, MW, calibration and global standardization; model-generated transported SED, not observed spectra.',
                 'Model directory B21 name and paper B22b name are not equated; exact MODEL000 files are binding.',
                 'No stochastic PV term or Pantheon total covariance added; no original-node promotion.'])
    (HERE/'RESULT.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib import pyplot as plt
    fig,ax=plt.subplots(1,3,figsize=(13,4))
    colors={'g':'tab:green','r':'tab:red','i':'tab:purple'}
    for band in CFG['bands']:
        sel=bands==band;order=np.argsort(times[sel]);ax[0].errorbar(times[sel],y[sel],yerr=error[sel],fmt='.',label=band,color=colors[band])
        ax[0].plot(times[sel][order],p[sel][order],color=colors[band])
    ax[0].set(xlabel='MJD - 55238.9 (days)',ylabel='released FLUXCAL');ax[0].legend()
    ax[1].plot(np.arange(len(y)),baseline['weighted_residuals'],'.');ax[1].set(xlabel='frozen measurement row',ylabel='working weighted residual')
    for label in ('covariant_MW','frozen_observer_MW'):
        rr=[r for r in paired if r['MW_experiment']==label];ax[2].plot([r['delta'] for r in rr],[r['kappa_amplitude_mag'] for r in rr],'o-',label=label)
    ax[2].set(xlabel='finite Doppler delta',ylabel='conditional amplitude defect (mag)');ax[2].legend(fontsize=7)
    fig.suptitle('SN010010 conditional fit; '+baseline['working_adequacy']+'; '+baseline['published_parity'],fontsize=10);fig.tight_layout()
    for ext in ('png','pdf'):fig.savefig(HERE/f'REFIT.{ext}',dpi=160)
    plt.close(fig)
    print(json.dumps(dict(n=len(y),reduced_chi2=baseline['reduced_chi2'],parity=baseline['published_parity'],defects=defects,quadrature=qerr,
        paired_kappa=[(r['delta'],r['MW_experiment'],r['kappa_amplitude_mag']) for r in paired],refinement=uncertainty.tolist())))


if __name__=='__main__':main()
