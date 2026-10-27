"""Independent R36-05 review: saved-array recount and bounded deterministic checks.

No new Monte Carlo draws, no producer main(), no fits, no repository writes.
Candidate implementation is imported only for explicitly labelled regression and
guard probes. Primary numerical checks below do not import its formulas.
"""
import os
os.environ.setdefault('PYTHONDONTWRITEBYTECODE', '1')
import sys
sys.dont_write_bytecode = True
import contextlib
import hashlib
import importlib
import io
import json
import math
from pathlib import Path
import platform
import subprocess
import time
import warnings

import mpmath as mp
import numpy as np
import scipy
from scipy.special import roots_legendre
from scipy.stats import beta, betabinom

REPO = Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
BASE = REPO / 'docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027'
PRODUCT = BASE / 'products/R36-05-RADIATION-RESPONSE'
RAW = Path('/mnt/extdrive/workdir/htt_open_data/r36_radiation_response_actual')
OUT = Path('/mnt/extdrive/workdir/htt_open_data/r36_radiation_fresh_review')
CONTRACT = Path('/mnt/extdrive/workdir/htt_open_data/r36_radiation_contract_preparation/IMPLEMENTATION_CONTRACT.json')
CLARIFICATION = CONTRACT.parent / 'PREPRODUCTION_RESOURCE_CLARIFICATION.json'
E = np.array([np.diag([1., -1., 0.])/np.sqrt(2), np.diag([1.,1.,-2.])/np.sqrt(6),
              [[0,1/np.sqrt(2),0],[1/np.sqrt(2),0,0],[0,0,0]],
              [[0,0,1/np.sqrt(2)],[0,0,0],[1/np.sqrt(2),0,0]],
              [[0,0,0],[0,0,1/np.sqrt(2)],[0,1/np.sqrt(2),0]]])
METRIC = np.diag([-1.,1.,1.,1.])
checks = []


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def near(name, x, y, tol=2e-12):
    err = float(np.max(np.abs(np.asarray(x)-np.asarray(y))))
    checks.append({'check': name, 'max_abs_error': err, 'tolerance': tol, 'pass': bool(err <= tol)})
    return err


def sphere(nmu, nphi):
    # Different quadrature implementation from the candidate's leggauss.
    z, wz = roots_legendre(nmu)
    phi = 2*np.pi*(np.arange(nphi)+.137)/nphi
    a, p = np.meshgrid(z, phi, indexing='ij')
    n = np.column_stack([(np.sqrt(1-a*a)*np.cos(p)).ravel(),
                         (np.sqrt(1-a*a)*np.sin(p)).ravel(), a.ravel()])
    return n, np.repeat(wz/(2*nphi), nphi)


def lorentz(v):
    v = np.asarray(v)
    b2 = v@v
    g = 1/math.sqrt(1-b2)
    out = np.eye(4)
    out[0,0] = g
    out[0,1:] = out[1:,0] = g*v
    if b2:
        out[1:,1:] += g*g/(g+1)*np.outer(v,v)
    return out


def sky(n, a, b):
    v = b*np.array([.6,0,.8])
    p = np.column_stack([np.ones(len(n)), -n]) @ lorentz(-v).T
    mu_rest = -p[:,3]/p[:,0]
    return (1+a*(3*mu_rest**2-1)/2)**.25/p[:,0]


def tensor(n, w, t):
    null = np.column_stack([np.ones(len(n)), -n])
    return np.einsum('n,na,nb->ab', w*t**4, null, null)


def d_from_tensor(t):
    rho = t[...,0,0]
    f = t[...,0,1:]/rho[...,None]
    pp = np.einsum('aij,...ij->...a',E,t[...,1:,1:])/rho[...,None]
    ff = np.einsum('aij,...i,...j->...a', E, f, f)
    return pp-3*ff/(2+np.sqrt(4-3*np.sum(f*f,axis=-1)))[...,None]


def high_precision_a(t):
    with mp.workdps(65):
        m = mp.matrix([[mp.mpf(float(v)) for v in row] for row in t])
        for i in range(4):
            m[i,0] = -m[i,0]
        ev = mp.eig(m,left=False,right=False)
        if max(abs(mp.im(x)) for x in ev)>mp.mpf('1e-55'):
            raise AssertionError('non-real high-precision eigenvalue')
        ev = sorted(mp.re(x) for x in ev)
        rho = -ev[0]
        return float(mp.sqrt(sum((x-rho/3)**2 for x in ev[1:]))/rho)


def cp(h,n):
    lo = 0. if h==0 else beta.ppf(.025,h,n-h+1)
    hi = 1. if h==n else beta.ppf(.975,h+1,n-h)
    return np.array([lo,hi])


def direct_operator(n,w,brightness):
    # Direct bilinear form, without candidate's STF4 or moment assembly.
    En = np.einsum('aij,nj->ani', E,n)
    nEn = np.einsum('ni,ani->an', n,En)
    out = np.empty((5,5))
    for a in range(5):
        for b in range(5):
            out[a,b] = np.dot(w*brightness,2*np.sum(En[a]*En[b],axis=1)-nEn[a]*nEn[b])
    return out


def main():
    begin = time.time()
    output = {'schema':'htt.r36_05.fresh_independent_review_evidence/1',
              'task_id':'R36-05-RADIATION-RESPONSE', 'reviewer':'/root/r36_radiation_fresh_review',
              'requested_runtime':'gpt-6-astra/xhigh', 'observed_runtime':'UNKNOWN',
              'formal_review_packet':None,'formal_review_ACK':None,'acceptance':False,
              'scope':'Review preparation only; no Monte Carlo producer rerun; read-only candidate.',
              'command':'env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python -B /mnt/extdrive/workdir/htt_open_data/r36_radiation_fresh_review/reproducer.py',
              'cwd':str(REPO), 'python':platform.python_version(), 'numpy':np.__version__,
              'scipy':scipy.__version__, 'mpmath':mp.__version__,
              'reproducer_sha256':sha(__file__), 'new_MC_draws':0, 'new_producer_invocations':0,
              'source_checkouts_created':0, 'repository_mutation':False}
    git = lambda *args: subprocess.check_output(['git',*args],cwd=REPO).decode().strip()
    output['git'] = {'branch':git('branch','--show-current'), 'HEAD':git('rev-parse','HEAD'),
                     'origin':git('remote','get-url','origin'),
                     'status_porcelain_sha256':hashlib.sha256(git('status','--porcelain=v1','-uall').encode()).hexdigest()}
    result = json.loads((PRODUCT/'RESULT.json').read_text())
    manifest = json.loads((PRODUCT/'MANIFEST.json').read_text())
    contract = json.loads(CONTRACT.read_text())
    identities = {'CANDIDATE.json':sha(PRODUCT/'CANDIDATE.json'),
                  'MANIFEST.json':sha(PRODUCT/'MANIFEST.json'),
                  'IMPLEMENTATION_CONTRACT.json':sha(CONTRACT),
                  'PREPRODUCTION_RESOURCE_CLARIFICATION.json':sha(CLARIFICATION)}
    assert identities == {'CANDIDATE.json':'91a3af176f7eabf3dba8d1af94616cd3a66a4e3ee374f731f45bb58236e6593d',
                          'MANIFEST.json':'5c033adc2bd9c6701c75587d58384857fb7803dc82ccbd2917d1df1429841323',
                          'IMPLEMENTATION_CONTRACT.json':'01e5cbafcc2ba5fefe242d04f4b49dd8727411cdbb1e5397e22c1ec30458637d',
                          'PREPRODUCTION_RESOURCE_CLARIFICATION.json':'b84a53e4aaf31a8563cf7916ed39ab41642ed95ed3973b8c32247b628a13db80'}
    manifest_checks = []
    for x in manifest['files']:
        p = Path(x['path'])
        observed = sha(p)
        manifest_checks.append({'path':str(p),'sha256':observed,'pass':observed==x['sha256'] and p.stat().st_size==x['bytes']})
    source_checks = []
    for key, x in contract['source_bindings'].items():
        actual = sha(REPO/x['path'])
        source_checks.append({'binding':key, 'sha256':actual,'pass':actual==x['sha256']})
    output['identities'] = identities
    output['manifest_checks'] = manifest_checks
    output['immutable_source_checks'] = source_checks
    arr = np.load(RAW/'sample_arrays.npz',allow_pickle=False)
    old = np.load(RAW/'raw/producer1_sample_arrays.npz',allow_pickle=False)
    parity = [key for key in old.files if not np.array_equal(old[key],arr[key],equal_nan=True)]
    output['first_producer_parity'] = {'first_keys':len(old.files),'current_keys':len(arr.files),'changed_old_keys':parity}
    assert not parity

    # Every saved realization; only recount/reconstruction, no sky generator rerun.
    rows = []
    selections = []
    extrema = []
    covariance_carrier = []
    for row in result['methods']:
        case, method = row['case'],row['method']
        stem = f'{case}_{method}'
        truth = result['truth'][case]
        d0,a0 = np.array(row['D_noiseless']),row['A_noiseless']
        dt,at = np.array(truth['physical_D']),truth['physical_A']
        calD,testD = arr[stem+'_cal_D'],arr[stem+'_test_D']
        calA,testA = arr[stem+'_cal_A'],arr[stem+'_test_A']
        cv,tv = arr[stem+'_cal_valid'],arr[stem+'_test_valid']
        assert len(cv)==8191 and len(tv)==4096 and cv.all() and tv.all()
        radii = np.linalg.norm(calD-d0,axis=1)
        errA = calA-a0
        r = np.partition(radii,7782)[7782]
        elo,ehi = np.partition(errA,[203,7987])[[203,7987]]
        near(stem+':radius',[r],row['D_radius'],1e-20)
        near(stem+':A_quantiles',[elo,ehi],row['A_error_quantiles'],1e-20)
        lower = np.maximum(testA-ehi,0.)
        upper = testA-elo
        nonempty = tv&(upper>=0)
        widths = np.where(nonempty,upper-lower,np.nan)
        hits = {'D_physical_target_coverage':tv&(np.linalg.norm(testD-dt,axis=1)<=r),
                'D_method_target_coverage':tv&(np.linalg.norm(testD-d0,axis=1)<=r),
                'A_physical_target_coverage':nonempty&(lower<=at)&(at<=upper),
                'A_method_target_coverage':nonempty&(lower<=a0)&(a0<=upper)}
        hitcounts = {}
        for key,mask in hits.items():
            h = int(mask.sum()); hitcounts[key] = h
            assert row[key]['hits']==h and row[key]['N']==4096
            near(stem+':'+key+':CP',cp(h,4096),[row[key]['lower'],row[key]['upper']],8e-13)
        assert np.array_equal(hits['D_physical_target_coverage'],arr[stem+'_test_D_physical_hit'])
        assert np.array_equal(hits['A_physical_target_coverage'],arr[stem+'_test_A_physical_hit'])
        assert np.array_equal(widths,arr[stem+'_test_A_width'],equal_nan=True)
        assert int(nonempty.sum())==row['A_nonempty_width']['count']
        near(stem+':nonempty_width_summaries',
             [np.nanmean(widths),np.nanmedian(widths),*np.nanquantile(widths,[.05,.95])],
             [row['A_nonempty_width'][k] for k in ('mean','median','p05','p95')],1e-20)
        near(stem+':D_content',beta.ppf([.025,.975],7783,409),row['calibration_content']['D_beta95'],1e-15)
        near(stem+':A_content',beta.ppf([.025,.975],7784,408),row['calibration_content']['A_equal_tail_beta95'],1e-15)
        assert len(np.unique(radii))==8191 and len(np.unique(errA))==8191
        fp = arr[stem+'_cal_fP']
        centered = fp-fp.mean(axis=0)
        cov = centered.T@centered/(len(fp)-1)
        near(stem+':full_fP_covariance',cov,row['fP_covariance'],2e-25)
        sd = np.sqrt(np.diag(cov))
        near(stem+':cross_block',cov[:3,3:]/sd[:3,None]/sd[None,3:],row['fP_standardized_cross_block_3x5'],5e-15)
        allcarrier = np.column_stack([arr[stem+'_cal_rho'],fp])
        c9 = np.cov(allcarrier,rowvar=False)
        covariance_carrier.append({'case':case,'method':method,'reconstructible_full_rho_fP_covariance_9x9':c9.tolist(),
                                   'fP_covariance_min_eigenvalue':float(np.linalg.eigvalsh(cov)[0]),
                                   'max_standardized_dQ_cross':float(np.max(np.abs(cov[:3,3:]/sd[:3,None]/sd[None,3:])))})
        for sample in ('cal','test'):
            tt = arr[f'{stem}_{sample}_stress']
            rr = arr[f'{stem}_{sample}_rho']
            fpall = arr[f'{stem}_{sample}_fP']
            rec = np.zeros_like(tt)
            rec[:,0,0] = rr
            rec[:,0,1:] = rec[:,1:,0] = rr[:,None]*fpall[:,:3]
            rec[:,1:,1:] = rr[:,None,None]*(np.eye(3)/3+np.einsum('na,aij->nij',fpall[:,3:],E))
            near(stem+':'+sample+':full_T_carrier',tt,rec,3e-16)
            near(stem+':'+sample+':D_independent',d_from_tensor(tt),arr[f'{stem}_{sample}_D'],3e-16)
            mincone = np.linalg.eigvalsh(tt/rr[:,None,None])[:,0]
            maxflux = np.max(np.linalg.norm(fpall[:,:3],axis=1))
            extrema.append({'case':case,'method':method,'sample':sample,'rho_range':[float(rr.min()),float(rr.max())],
                            'max_flux_norm':float(maxflux),'min_cone_eigenvalue':float(mincone.min())})
            eta = arr[f'{case}_eta_{sample}']
            ids = sorted(set([0,len(tt)-1,int(np.argmax(np.linalg.norm(eta,axis=1))),
                              int(np.argmax(arr[f'{stem}_{sample}_A'])),int(np.argmin(arr[f'{stem}_{sample}_A']))]))
            for index in ids:
                hp = high_precision_a(tt[index])
                er = near(stem+':'+sample+f':A_mp65:{index}',hp,arr[f'{stem}_{sample}_A'][index],2e-12)
                selections.append({'case':case,'method':method,'sample':sample,'index':index,'A_mp65':hp,'error':er})
        rows.append({'case':case,'method':method,'hit_counts':hitcounts,'empty_count':int((~nonempty).sum()),
                     'D_width':2*float(r),'A_nonempty_mean_width':float(np.nanmean(widths)),
                     'A_unconditional_width_empties_zero_labeled':float(np.nansum(widths)/len(widths))})
    output['saved_array_recount'] = rows
    output['full_covariance_carriers'] = covariance_carrier
    output['saved_domain_extrema'] = extrema
    output['high_precision_Landau_checks'] = selections
    for case in result['truth']:
        ex,li = [arr[f'{case}_{m}_test_A_width'] for m in ('exact','linear')]
        good = np.isfinite(ex)&np.isfinite(li)
        diff=ex[good]-li[good]
        r = next(x for x in result['methods'] if x['case']==case)
        near(case+':paired_width',[diff.mean(),diff.std(ddof=1)/np.sqrt(len(diff))],
             [r['paired_A_width_difference']['mean_exact_minus_linear'],r['paired_A_width_difference']['MC_SE']],1e-20)
        assert int(good.sum())==r['paired_A_width_difference']['count']

    # Refined direct temperature integration of zero and saved noise extremes.
    direct_checks=[]
    n,w=sphere(80,161)
    features=np.column_stack([n,np.einsum('aij,ni,nj->na',E,n,n)])
    for case,tr in result['truth'].items():
        a,b=tr['a'],tr['b']
        t=sky(n,a,b)
        tbar=w@t
        near(case+':refined_tbar',tbar,tr['tbar'])
        zero=tensor(n,w,t)
        near(case+':refined_analytic_T',zero,tr['analytic_T_over_rho_ref'])
        for sample in ('cal','test'):
            eta=arr[f'{case}_eta_{sample}']
            magnitude=np.linalg.norm(eta[:,:3],axis=1)+np.sqrt(2/3)*np.linalg.norm(eta[:,3:],axis=1)
            bound=(1-a/2)**.25*np.sqrt(1-b*b)/((1+b)*tbar)
            assert (magnitude<bound).all()
            assert arr[f'{case}_{sample}_temperature_positivity'].all()
            ids=sorted(set([0,len(eta)-1,int(np.argmax(magnitude)),int(np.argmax(np.abs(eta[:,0])))]))
            for i in ids:
                direct=tensor(n,w,t+tbar*(features@eta[i]))
                er=near(case+':'+sample+f':direct_T:{i}',direct,arr[f'{case}_exact_{sample}_stress'][i])
                direct_checks.append({'case':case,'sample':sample,'index':i,'max_abs_T_error':er,
                                      'global_positive_margin':float(bound-magnitude[i])})
    output['direct_sky_checks']=direct_checks

    # Frozen method law: independently check every linear carrier from saved eta.
    linear_errors=[]
    for case,tr in result['truth'].items():
        for sample in ('cal','test'):
            eta=arr[f'{case}_eta_{sample}']
            expected=np.column_stack([-4/3*(np.array(tr['d_true'])+eta[:,:3]),
                                      8/15*(np.array(tr['Q_true'])+eta[:,3:])])
            err=near(case+':'+sample+':linear_common_eta',expected,arr[f'{case}_linear_{sample}_fP'],2e-16)
            linear_errors.append(err)
    output['max_linear_common_input_error']=max(linear_errors)

    # No extra draws: remove d/Q cross block in a deterministic first-order
    # diagnostic of the same nonlinear D readout. This is a falsifier, not a
    # replacement law or reported confidence procedure.
    cov=np.array(result['temperature_law']['covariance'])
    diagonal_blocks=cov.copy(); diagonal_blocks[:3,3:]=0; diagonal_blocks[3:,:3]=0
    block_diagnostic=[]
    for case,tr in result['truth'].items():
        f=-4/3*np.array(tr['d_true'])
        s=f@f; kap=3/(2+np.sqrt(4-3*s))
        # derivative of kappa(s), exact analytic expression.
        kp=9/(2*np.sqrt(4-3*s)*(2+np.sqrt(4-3*s))**2)
        uff=np.einsum('aij,i,j->a',E,f,f)
        dg=2*kap*np.einsum('aij,j->ai',E,f)+2*kp*uff[:,None]*f
        J=np.column_stack([4/3*dg,8/15*np.eye(5)])
        full=J@cov@J.T
        cut=J@diagonal_blocks@J.T
        evals=np.linalg.eigvalsh(np.linalg.solve(np.linalg.cholesky(full),np.linalg.solve(np.linalg.cholesky(full),cut).T).T)
        # Symmetric whitened variance ratios; raw difference is also retained.
        block_diagnostic.append({'case':case,'full_trace':float(np.trace(full)),'cross_omitted_trace':float(np.trace(cut)),
                                 'trace_relative_difference':float(np.trace(cut)/np.trace(full)-1),
                                 'max_abs_covariance_difference':float(np.max(np.abs(cut-full))),
                                 'variance_ratio_eigenvalues':evals.tolist()})
    output['cross_block_omission_falsifier']={'method':'deterministic Jacobian of D under linear adapter; no MC or calibration replacement',
                                             'input_covariance_cross_block':cov[:3,3:].tolist(), 'rows':block_diagnostic}

    # Saved response coefficients, no nonlinear fit rerun. Full 5x5 direct matrix.
    saved=json.loads((BASE/'imports/v15/cas/entropic_shear_results.json').read_text())
    response_checks=[]
    for nr in (256,320):
        n,w=sphere(nr,12)
        mu=n[:,2]
        target=np.polynomial.legendre.legval(mu,saved['input_brightness_legendre_coefficients'])
        target_matrix=direct_operator(n,w,target)
        near(f'isotropic_response_{nr}',direct_operator(n,w,np.ones(len(n))),8/15*np.eye(5))
        for source in saved['rows']:
            br=np.polynomial.legendre.legval(mu,source['beta_legendre_coefficients'])**-4
            mat=direct_operator(n,w,br)
            er=float(np.linalg.norm(mat-target_matrix,2))
            ent=float(w@(br**.75-target**.75))
            rr=next(x for x in result['response_compression']['L2_L4'] if x['nmu']==nr and x['L']==source['L'])
            near(f'L{source["L"]}_{nr}_matrix',mat,rr['response_matrix_over_rho0'])
            near(f'L{source["L"]}_{nr}_error',er,rr['operator_error_over_rho0'])
            near(f'L{source["L"]}_{nr}_entropy',ent,rr['entropy_difference_over_Siso'])
            response_checks.append({'nmu':nr,'L':source['L'],'operator_error':er,'entropy_difference':ent,
                                    'minimum_inverse_temperature':float(np.min(np.polynomial.legendre.legval(mu,source['beta_legendre_coefficients'])))})
    fallback=[]
    for nr in (160,320):
        n,w=sphere(nr,32)
        brightness=np.exp(8*n[:,2]**2); brightness/=w@brightness
        mat=direct_operator(n,w,brightness)
        delta=float(1-w@brightness**.75)
        eig=np.linalg.eigvalsh(mat)
        near(f'entropy_fallback_{nr}',eig,result['response_compression'][f'entropy_fallback_{nr}']['actual_eigenvalues_over_rho'])
        fallback.append({'nmu':nr,'delta':delta,'lower_bound':float(8/15-np.sqrt(8*delta/3)),
                         'eigenvalues':eig.tolist()})
    output['independent_response_checks']=response_checks
    output['independent_entropy_fallback']=fallback

    # Candidate regressions and small probes, explicitly separate from independent
    # primary checks above. Test modules contain no main/production side effects.
    sys.path.insert(0,str(PRODUCT))
    log=io.StringIO()
    focused=[]
    with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log),warnings.catch_warnings(record=True) as ws:
        for name in ('test_radiation_core','test_run_comparison'):
            module=importlib.import_module(name)
            for fname in sorted(x for x in dir(module) if x.startswith('test_')):
                getattr(module,fname)(); focused.append(name+'.'+fname)
        core=importlib.import_module('radiation_core')
        run=importlib.import_module('run_comparison')
        # General non-axisymmetric response checks missing from scalar toy tables.
        n,w=sphere(40,83)
        br=1+.17*n[:,0]-.11*n[:,1]+.12*n[:,0]*n[:,2]+.2*n[:,0]**2*n[:,1]**2
        mm=core.moments(n,w,br,1)
        near('nonaxisymmetric_5x5_rank024',core.response_from_moments(mm),direct_operator(n,w,br))
        # Finiteness and invalid samples are not projected into the cone.
        bad=np.zeros((3,9)); bad[0,0]=1; bad[0,1]=2; bad[2,0]=np.nan
        got=run.analyze_moments(bad)
        assert not got['valid'].any()
        guard={'large_flux_zero_density_NaN_valid_flags':got['valid'].tolist()}
        # Scale extremes: same ordinary physical tensor represented in 10^-250
        # and 10^250 density units should preserve dimensionless observables.
        tr=np.array(result['truth']['a0.02_b0.3']['analytic_T_over_rho_ref'])
        vec=np.r_[tr[0,0],tr[0,1:],np.einsum('aij,ij->a',E,tr[1:,1:])]
        scaled=run.analyze_moments(np.stack([vec*1e-250,vec,vec*1e250]))
        near('scale_extremes_D',scaled['D'],np.tile(scaled['D'][1],(3,1)))
        near('scale_extremes_A',scaled['A'],np.repeat(scaled['A'][1],3))
        guard['scale_1e_minus250_1_1e250_valid_flags']=scaled['valid'].tolist()
        # Expose limits of the separately exported convenience helper. This helper
        # is not the producer's guarded readout; flag this as scoped API limitation.
        negpressure=np.diag([1.,4/3,-1/6,-1/6])
        malformed=core.Moments(1.,np.zeros(3),np.diag([1.,-.5,-.5]),np.zeros((3,)*4),negpressure)
        old_read=core.stress_readout(malformed)
        guard['convenience_helper_negative_pressure_fixture']={'stress':negpressure.tolist(),
                     'stress_readout_returns_finite_A':old_read['A_gamma'],
                     'production_analyze_moments_valid':bool(run.analyze_moments(np.r_[1.,0.,0.,0.,np.einsum('aij,ij->a',E,negpressure[1:,1:])][None,:])['valid'][0]),
                     'consumed_by_actual_MC':False}
    output['focused_candidate_test_calls']=focused
    output['focused_test_stdout_stderr']=log.getvalue()
    output['warnings']=[str(x.message) for x in ws]
    output['domain_probes']=guard
    # One exact D test coverage is high; retain a diagnostic under the frozen
    # continuous-order calibration design, rather than tune or force a 95% hit rate.
    high=next(r for r in rows if r['case']=='a0_b0.3' and r['method']=='exact')
    h=high['hit_counts']['D_physical_target_coverage']
    output['high_exact_coverage_diagnostic']={'case':'a0_b0.3','target':'D','hits':h,'N':4096,
                'one_sided_beta_binomial_predictive_tail':float(betabinom.sf(h-1,4096,7783,409)),
                'scope':'Unadjusted diagnostic for continuous method-target calibration law; one of multiple displayed estimates. No additional draws or tuning.'}
    output['checks']=checks
    output['failed_checks']=[x for x in checks if not x['pass']]
    output['elapsed_seconds']=time.time()-begin
    output['peak_rss_kib']=__import__('resource').getrusage(__import__('resource').RUSAGE_SELF).ru_maxrss
    output['exit_status']=0 if not output['failed_checks'] and all(x['pass'] for x in manifest_checks+source_checks) else 1
    output['candidate_identity_end']=sha(PRODUCT/'CANDIDATE.json')
    output['manifest_identity_end']=sha(PRODUCT/'MANIFEST.json')
    (OUT/'RAW_RECEIPT.json').write_text(json.dumps(output,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'checks':len(checks),'failed_checks':output['failed_checks'],
                      'manifest_pass':all(x['pass'] for x in manifest_checks),
                      'source_pass':all(x['pass'] for x in source_checks),
                      'saved_rows':len(rows),'high_precision_checks':len(selections),
                      'direct_sky_checks':len(direct_checks),'focused_tests':len(focused),
                      'elapsed_seconds':output['elapsed_seconds'],'guard':guard,
                      'high_exact_coverage_diagnostic':output['high_exact_coverage_diagnostic']}))
    raise SystemExit(output['exit_status'])


if __name__=='__main__':
    main()
