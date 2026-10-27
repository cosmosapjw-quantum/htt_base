"""R36-07 continuing research: source statistics, analytic-envelope witnesses.

No producer import; no original source/candidate mutation; no native map rerun.
All source-derived numbers below are map statistics or explicitly conditional
calculations. The script does not manufacture a physical confidence set.
"""
from pathlib import Path
import datetime, hashlib, json, math, platform, resource, time
import numpy as np
from astropy.io import fits
from scipy.special import logsumexp
import healpy as hp

ROOT=Path(__file__).resolve().parent
SRC=ROOT/'source'
BASE=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
ACT=Path('/mnt/extdrive/workdir/htt_open_data/r36_foreground_budget_actual')
START=time.monotonic()
C=299792458.; H=6.62607015e-34; KB=1.380649e-23; TCMB=2.7255
NU0=30e9; NUD=353e9; NUC=C/(240e-6)
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dbdt(nu):
    x=H*nu/(KB*TCMB)
    return 2*KB*nu**2/C**2*x**2*np.exp(x)/np.expm1(x)**2

def source_stats():
    out={}
    for name,scale in [('haslam408_ds_Remazeilles2014.fits',1.),('lambda_haslam408_nofilt.fits',.001)]:
        with fits.open(SRC/name,memmap=True) as f:
            z=np.asarray(f[1].data['TEMPERATURE'],dtype=np.float64).ravel()*scale
            assert z.size==12*512**2 and np.all(np.isfinite(z))
            out[name]={'pixels':int(z.size),'unit':'K_RJ','minimum':float(z.min()),'median':float(np.median(z)),
                'mean':float(z.mean()),'maximum':float(z.max()),'equal_area_integral_K_RJ_sr':float(z.mean()*4*np.pi),
                'nside':f[1].header.get('NSIDE'),'ordering':f[1].header.get('ORDERING'),
                'interpretation':'DELIVERED_MAP_STATISTIC; not a calibrated upper bound on arbitrary positive emitter mass'}
    with fits.open(SRC/'DIRBE_BAND10_AAM_P3B.FITS',memmap=True) as f:
        d=f[1].data; y=d['Photomet'].astype(float); s=d['StdDev'].astype(float)
        counts=d['WtNumObs']; pixels=d['Pixel_no']; n=y.size
        assert n==393216 and np.array_equal(np.sort(pixels),np.arange(n))
        assert np.all(counts>0) and np.all(np.isfinite(y)) and np.all(s>0)
        q=4*np.pi/n
        out['DIRBE_BAND10_AAM_P3B.FITS']={'pixels':n,'all_native_pixel_ids_once':True,'all_positive_observation_counts':True,
            'zodiacal_light_removed':bool(f[0].header['ZLREMOV']),'unit':'MJy/sr','negative_pixels':int((y<0).sum()),
            'minimum':float(y.min()),'median':float(np.median(y)),'mean':float(y.mean()),'maximum':float(y.max()),
            'sum_with_uniform_nominal_pixel_areas_MJy':float(q*y.sum()),
            'sigma_sum_worst_unknown_crosspixel_PSD_MJy':float(q*s.sum()),
            'Cantelli_95_percent_noise_margin_MJy_IF_released_marginals_are_valid':float(math.sqrt(19)*q*s.sum()),
            'stddev_definition':'standard deviation of weighted mean, per supplement Table 5.7-14; no second count division',
            'pixel_area_status':'CSC only approximately equal-area; uniform q is a chosen functional, not an exact sphere quadrature',
            'gain_systematic_fraction_Hauser1998_Table2':.116,
            'offset_systematic_nW_m2_sr_Hauser1998_Table2':2.,
            'offset_systematic_MJy_sr':2e-9/NUC/1e-20,
            'error_interpretation':'Published error estimates; neither deterministic envelopes nor a new joint confidence claim'}
    return out

def passband():
    rows=[]
    for line in (SRC/'DIRBE_SYSTEM_SPECTRAL_RESPONSE_TABLE.ASC').read_text().splitlines():
        try: a=[float(v) for v in line.split()]
        except ValueError: continue
        if len(a)==11: rows.append(a)
    tab=np.asarray(rows); nu=C/(tab[:,0]*1e-6); r=tab[:,10]; ix=np.argsort(nu);nu=nu[ix];r=r[ix]
    assert np.all(np.diff(nu)>0) and np.all(r>=0)
    # Exact integrals for the explicitly chosen piecewise-linear-in-frequency
    # interpolant of the rounded published table, using high-order Gauss nodes.
    from numpy.polynomial.legendre import leggauss
    gx,gw=leggauss(16)
    left,right=nu[:-1],nu[1:]; mid=(left+right)/2; half=(right-left)/2
    nq=(mid[:,None]+half[:,None]*gx).ravel()
    rq=((r[:-1,None]+r[1:,None])/2+(r[1:,None]-r[:-1,None])/2*gx).ravel()
    wq=(half[:,None]*np.broadcast_to(gw,(len(half),len(gw)))).ravel()
    keep=rq>0;nq=nq[keep];rq=rq[keep];wq=wq[keep]
    norm=float(np.sum(wq*rq*NUC/nq))
    m=float(dbdt(NU0)*np.sum(wq*rq*(nq/NU0)**-1)/norm)
    p=wq*rq*NUC/nq/norm
    t=np.log(nq/NU0); tbar=float(p@t)
    assert abs(m/(dbdt(NU0)*NU0/NUC)-1)<5e-15
    checks=[]
    for delta in [-100.,-20.,-5.,-1.,0.,1.,5.,20.,100.]:
        actual=float(logsumexp(np.log(p)+delta*t))
        lower=delta*tbar
        assert actual>=lower-2e-13
        checks.append({'delta_beta':delta,'log_H_over_m':actual,'Jensen_lower_log':lower})
    nz=np.where(r>0)[0]
    result={'release':'DIRBE Pass 3B November 1996','reference_wavelength_um':240.,
            'reference_frequency_GHz':NUC/1e9,'positive_tabulated_frequency_GHz':[float(nu[nz[0]]/1e9),float(nu[nz[-1]]/1e9)],
            'piecewise_linear_support_GHz':[float(nu[max(0,nz[0]-1)]/1e9),float(nu[min(len(nu)-1,nz[-1]+1)]/1e9)],
            'normalization_integral_Hz_for_nuIconstant':norm,
            'baseline_m_MJy_sr_per_K_CMB30':m/1e-20,'tbar_log_nu_over_30':tbar,
            'geometric_mean_frequency_GHz':NU0*np.exp(tbar)/1e9,
            'Jensen_checks':checks,
            'qualification':'Rounded response table and chosen interpolation; no empirical lower-response uncertainty certificate claimed'}
    return result,(nq,p,rq,wq,norm)

def envelopes(stats,pb):
    a=math.log(30/.408); b=pb['tbar_log_nu_over_30']
    # Sensitivity calculation ONLY: assume each delivered sum is exact true
    # positive full-sky flux, kappa=1, and Haslam is monochromatic at 408 MHz.
    below=stats['lambda_haslam408_nofilt.fits']['equal_area_integral_K_RJ_sr']
    low_i=below*(2*KB*(.408e9)**2/C**2)
    jminus=low_i/(dbdt(NU0)*(.408/30)**-1)
    jplus=stats['DIRBE_BAND10_AAM_P3B.FITS']['sum_with_uniform_nominal_pixel_areas_MJy']/pb['baseline_m_MJy_sr_per_K_CMB30']
    theta=b/(a+b)
    m0=jminus**theta*jplus**(1-theta)
    result=[]; moments=[m0]
    delta=np.linspace(-100,100,40001)
    for k in range(1,5):
        cm=(k/(math.e*a))**k; cp=(k/(math.e*b))**k
        assert np.all(abs(delta)**k<=cm*np.exp(-a*delta)+cp*np.exp(b*delta))
        bound=cm*jminus+cp*jplus
        moments.append(bound)
        result.append({'order':k,'coefficient_minus':cm,'coefficient_plus':cp,'conditional_absolute_moment_K_CMB_sr':bound})
    D=np.load(ACT/'ACTUAL_GEOMETRY.npz')['D']
    assert D.shape==(9,)
    lnorm=math.sqrt(3/math.pi)
    rho=lnorm*math.sqrt((D[0]*m0)**2+(D[1]*moments[1])**2+(D[5]*moments[2]/2)**2)
    rem=[]
    for freq in [30.,44.,70.,100.,143.,217.,353.]:
        t=math.log(freq/30)
        # Exponential interpolation is sharper than Jminus+Jplus.
        eta=(b-t)/(a+b)
        assert 0<=eta<=1
        expbound=jminus**eta*jplus**(1-eta)
        triangle=expbound+m0+abs(t)*moments[1]+t*t*moments[2]/2
        cubic=abs(t)**3/6*((3/(math.e*(a-max(-t,0))))**3*jminus+(3/(math.e*(b-max(t,0))))**3*jplus)
        bound=min(triangle,cubic)
        # Algebra witness for a mixture of positive atoms: not a coverage test.
        atoms=np.array([-8.,-2.,0.,.3,4.,7.]); masses=np.array([1.,2.,3.,4.,2.,1.])*1e-30
        jm=float(masses@np.exp(-a*atoms));jp=float(masses@np.exp(b*atoms))
        exact=float(masses@np.abs(np.expm1(t*atoms)-t*atoms-(t*atoms)**2/2))
        cc=abs(t)**3/6*((3/(math.e*(a-max(-t,0))))**3*jm+(3/(math.e*(b-max(t,0))))**3*jp)
        assert exact<=cc+1e-40
        rem.append({'nominal_frequency_GHz':freq,'conditional_TV_remainder_K_CMB30_sr':bound,
                    'after_nominal_thermodynamic_conversion_and_24_harmonic_norm_K_CMB':bound*dbdt(NU0)*(freq/30)**-1/dbdt(freq*1e9)*lnorm,
                    'warning':'Nominal-frequency illustration only; native target bands must integrate this bound'})
    return {'status':'CONDITIONAL_SENSITIVITY_ONLY_NOT_SOURCE_QUALIFIED_UPPER_BOUND',
            'unverified_assumptions':['Haslam monochromatic response','both positive global response lower constants kappa=1',
            'raw sums equal true total intensities with no calibration/noise/processing error','pure unabsorbed common power laws over entire bracket'],
            'a_minus':a,'b_plus':b,'Jminus_K_CMB30_sr':jminus,'Jplus_K_CMB30_sr':jplus,
            'Holder_M0_K_CMB30_sr':m0,'moments':result,'R32_D':D.tolist(),
            'conditional_synch_component_rho_bound_K_CMB':rho,
            'is_full_nine_moment_physical_rho':False,'nominal_remainder_examples':rem}

def spin_norm():
    nside=4;lmax=3;npix=hp.nside2npix(nside)
    columns=[]
    for typ in ['E','B']:
        for ell in [2,3]:
            for mm in range(ell+1):
                phases=[1.] if mm==0 else [1/math.sqrt(2),-1j/math.sqrt(2)]
                for phase in phases:
                    ae=np.zeros(hp.Alm.getsize(lmax),complex);ab=ae.copy()
                    (ae if typ=='E' else ab)[hp.Alm.getidx(lmax,ell,mm)]=phase
                    columns.append(hp.alm2map_spin([ae,ab],nside,2,lmax=lmax))
    L=np.asarray(columns)
    gram=np.einsum('aip,ajp->pij',L,L)
    bgram=np.einsum('aip,ajp->pij',L[12:],L[12:])
    err=float(np.max(abs(gram-np.eye(2)*3/math.pi)))
    berr=float(np.max(abs(bgram-np.eye(2)*3/(2*math.pi))))
    assert err<5e-14 and berr<5e-14
    return {'all24_operator_norm':math.sqrt(3/math.pi),'B12_operator_norm':math.sqrt(3/(2*math.pi)),
            'all24_addition_theorem_max_error':err,'B12_addition_theorem_max_error':berr,
            'independent_library':'healpy alm2map_spin '+hp.__version__,'fixture_nside':nside,
            'applies_to':'common full-sky harmonic integration; a mask of magnitude <=1 preserves upper bound',
            'native_operator_caveat':'beam/mask/mapmaking mixing needs its own norm or direct pointwise retained-kernel bound'}

def witnesses(pdata):
    nu,p,r,w,norm=pdata
    dmin=min(abs(math.log(.408/30)),float(np.log(nu/NU0).min()))
    curved=[]
    for amp in [10.,1e3,1e6,1e12]:
        k=2*math.log(amp)/dmin**2
        low=amp*math.exp(-k*math.log(.408/30)**2)
        high=amp*float(p@np.exp(-k*np.log(nu/NU0)**2))
        assert low<=1/amp*(1+1e-12) and high<=1/amp*(1+1e-12)
        curved.append({'reference_amplitude':amp,'quadratic_log_curvature_k':k,
                       'low_endpoint_ratio_times_amplitude':low,'DIRBE_baseline_weighted_ratio_times_amplitude':high})
    def logexpm1(z):return z+np.log(-np.expm1(-z))
    hot=[]
    for temp in [20.,100.,1000.,1e6]:
        beta=1.5;xref=H*NUD/(KB*temp)
        ratio=np.exp((beta+3)*np.log(nu/NUD)+logexpm1(xref)-logexpm1(H*nu/(KB*temp)))
        hot.append({'T_K':temp,'DIRBE_Ical_per_I353':float(np.sum(w*r*ratio)/norm),
                    'R32_t_second_factorial_moment_per_reference_amplitude':((temp-20)/20)**2/2})
    cold=[]
    for temp in [1.,.1,.01,.001]:
        xref=H*NUD/(KB*temp);beta=xref-3; logamp=math.log(xref)
        ld=(beta+3)*np.log(nu/NUD)+logexpm1(xref)-logexpm1(H*nu/(KB*temp))
        low=(beta+3)*math.log(.408e9/NUD)+float(logexpm1(xref))-float(logexpm1(H*.408e9/(KB*temp)))
        ldir=float(logsumexp(np.log(w*r/norm)+ld))+logamp
        # A broad native-like positive band containing 353 GHz is unbounded too.
        # Analytic Laplace asymptotic: integral A*S_nu dnu ~ nu_ref*sqrt(2*pi*xref).
        cold.append({'T_K':temp,'beta':beta,'reference_amplitude':xref,
                     'log_Haslam_monochromatic_I_per_unit_reference':low+logamp,
                     'log_DIRBE_Ical_per_unit_reference':ldir,
                     'positive_broad_target_integral_asymptotic_Hz':NUD*math.sqrt(2*np.pi*xref)})
    # Unit-normalized positive observation beams need not preserve sky integral.
    spatial=[]
    for eps in [1e-1,1e-3,1e-6]:
        mat=np.array([[1-eps,eps],[1-2*eps,2*eps]])
        mu=np.array([0.,1/eps]);y=mat@mu
        assert np.all(mat>0) and np.allclose(mat.sum(axis=1),1)
        assert np.allclose(y,[1,2])
        spatial.append({'epsilon':eps,'positive_unit_row_beams':mat.tolist(),'sky_mass':float(mu.sum()),
                        'all_observations_positive':y.tolist(),'sum_y':float(y.sum()),'minimum_column_sum':float(mat.sum(axis=0).min())})
    return {'curvature_witness':curved,'curvature_scope':'positive smooth spectra without curvature restriction; not asserted a classical synchrotron electron-spectrum construction',
            'MBB_highT_witness':hot,'MBB_cold_beta_tail_witness':cold,
            'MBB_scope':'normalized mathematical modified-blackbody family on beta real,T>0; no claim these tails represent viable thermal dust',
            'positive_full_observation_spatial_witness':spatial,
            'spatial_scope':'counterexample to row normalization + populated outputs implying quantitative mass domination, not evidence DIRBE has a physical hole'}

def main():
    stats=source_stats();pb,pdata=passband()
    intake=json.loads((ROOT/'SOURCE_INTAKE.json').read_text())
    sources=[]
    for row in intake:
        assert row['status']=='ACQUIRED'
        actual=sha(row['path']);assert actual==row['sha256']
        sources.append({'name':Path(row['path']).name,'bytes':row['bytes'],'sha256':actual,'url':row['url']})
    sealed=BASE/'docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-07-FOREGROUND-BUDGET/RESULT.json'
    result={'task_id':'R36-07-FOREGROUND-BUDGET','same_issue_continuation':True,
            'status':'SOURCE_AND_ANALYTIC_RESEARCH_COMPLETED_PHYSICAL_BUDGET_UNQUALIFIED',
            'sealed_candidate_identity':'34ac36b0a774589c213d33943e4a4c25678d4e095e9b9f6062081118a2129cc9',
            'sealed_RESULT_sha256':sha(sealed),'source_stats':stats,'DIRBE_passband':pb,
            'conditional_envelope':envelopes(stats,pb),'spin_harmonic_norm':spin_norm(),'unbounded_sector_witnesses':witnesses(pdata),
            'source_hash_checks':sources,'acceptance_met':False,'qualified_products':[],
            'runtime':{'requested_model':'gpt-6-astra','requested_effort':'xhigh','observed':'UNKNOWN','role':'research contributor, not independent reviewer of this method'},
            'execution':{'python':platform.python_version(),'numpy':np.__version__,'elapsed_seconds':time.monotonic()-START,
                         'maxrss_KiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}}
    assert result['sealed_RESULT_sha256']=='2b125b9a98060f48324740848c3b09b3b23ac00185e1a53e241645274c0d71d4'
    (ROOT/'NUMERIC_RESEARCH.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'all_source_hashes_match':len(sources),'conditional_synch_rho_K':result['conditional_envelope']['conditional_synch_component_rho_bound_K_CMB'],
                      'spin_maxerr':result['spin_harmonic_norm']['all24_addition_theorem_max_error'],'elapsed_s':result['execution']['elapsed_seconds']}))
if __name__=='__main__':main()
