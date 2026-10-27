"""Read-only independent R36-02 numerical checks; writes only review evidence."""
import csv
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import time

import numpy as np
import scipy
from scipy.integrate import quad
from scipy.linalg import qr, solve_triangular
from scipy.special import hyp2f1, spherical_jn, roots_legendre
from scipy.stats import beta

START = time.monotonic()
REPO = Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
ROOT = REPO/'docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027'
PRODUCT = ROOT/'products/R36-02-CF4-CORRELATED'
EXT = Path('/mnt/extdrive/workdir/htt_open_data/r36_cf4_correlated_actual')
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(PRODUCT))
import run_correlated as r
import run_sensitivity as sens

checks = {}
def emit(name, value):
    checks[name] = value
    print(name, json.dumps(value, sort_keys=True), flush=True)
def rel(a,b):
    return float(np.linalg.norm(a-b)/np.linalg.norm(b))

with np.load(r.SOURCE) as f:
    s={k:f[k] for k in f.files}
with np.load(r.OPERATOR) as f:
    op={k:f[k] for k in f.files}
with np.load(EXT/'RESULT_MATRICES.npz') as f:
    result={k:f[k] for k in f.files}
A=op['A_raw']; n=s['n_J2000']; z=s['z_CMB']; d=10**((s['dmzp']-25)/5)
assert A.shape==(36,35970)
assert np.array_equal(op['group_id'],s['group_id'])
assert r.sha(r.SOURCE)==r.SHA_SOURCE and r.sha(r.OPERATOR)==r.SHA_OPERATOR
emit('environment', {'python':sys.version,'executable':sys.executable,'numpy':np.__version__,
    'scipy':scipy.__version__,'finufft':r.finufft.__version__,
    'imported_science_sha256':r.sha(Path(r.old.__file__))})

# Independent closed form of the growing mode in matter+Lambda, and adaptive chi.
chi,g,_,D,f=r.old.background(z,64)
idx=np.unique(np.linspace(0,len(z)-1,9,dtype=int)); a=1/(1+z[idx]); x=-r.old.OL/r.old.OM*a**3
hyper=hyp2f1(1/3,1,11/6,x)
Dh=a*hyper/hyp2f1(1/3,1,11/6,-r.old.OL/r.old.OM)
fh=1+6*x/11*hyp2f1(4/3,2,17/6,x)/hyper
gh=a*r.old.H0*np.sqrt(r.old.OM/a**3+r.old.OL)*fh*Dh
chih=np.array([r.old.C/r.old.H0*quad(lambda t:1/np.sqrt(r.old.OM*(1+t)**3+r.old.OL),0,zz,epsabs=1e-12)[0] for zz in z[idx]])
growth={'D_relative_max':float(np.max(abs(D[idx]/Dh-1))), 'f_relative_max':float(np.max(abs(f[idx]/fh-1))),
        'g_relative_max':float(np.max(abs(g[idx]/gh-1))), 'chi_relative_max':float(np.max(abs(chi[idx]/chih-1)))}
assert max(growth.values())<1e-11
emit('independent_growth_and_distance',growth)

# Independent oscillatory ten-row pair kernel, including coincident rows.
rng=np.random.default_rng(27003602)
ni=rng.normal(size=(10,3));ni/=np.linalg.norm(ni,axis=1)[:,None]
xi=ni*rng.uniform(5,175,size=(10,1));xi[9]=xi[0];ni[9]=ni[0]
gi=rng.uniform(45,70,size=10); Ai=rng.normal(size=(5,10))/100
_,_,u,wa=r.old.angular_rule(53)
rad,wr=roots_legendre(48)
fixture=[]
for lo,hi in r.old.BANDS:
    k=lo+(rad+1)*(hi-lo)/2; wk=wr*(hi-lo)/2
    p0=r.old.power(k,json.loads((PRODUCT/'RESULT.json').read_text())['amplitude'])
    c=np.zeros((5,5)); cmut=np.zeros((5,5))
    for kv,wv,pv in zip(k,wk,p0):
        latent=gi[:,None]*(ni@u.T)*np.exp(1j*kv*(xi@u.T))
        projected=Ai@latent
        weights=wa*wv*pv/(2*np.pi)**3*np.exp(-(kv*5/r.old.H)**2)
        c+=np.einsum('at,bt,t->ab',projected,projected.conj(),weights).real
        no_phase=Ai@(gi[:,None]*(ni@u.T))
        cmut+=np.einsum('at,bt,t->ab',no_phase,no_phase,weights)
    pair=np.empty((10,10))
    for i in range(10):
        for j in range(10):
            delta=xi[i]-xi[j]; sep=np.linalg.norm(delta); dot=float(ni[i]@ni[j])
            longitudinal=float((ni[i]@delta)*(ni[j]@delta)/sep**2) if sep else 0
            pair[i,j]=gi[i]*gi[j]*quad(lambda kv:r.old.power(kv,json.loads((PRODUCT/'RESULT.json').read_text())['amplitude'])*np.exp(-(kv*5/r.old.H)**2)*((spherical_jn(0,kv*sep)+spherical_jn(2,kv*sep))*dot/3-spherical_jn(2,kv*sep)*longitudinal)/(2*np.pi**2),lo,hi,epsabs=1e-9,epsrel=1e-11)[0]
    expected=Ai@pair@Ai.T
    item={'relative_frobenius':rel(c,expected),'max_normalized_entry':float(np.max(abs(c-expected)/np.sqrt(np.outer(np.diag(expected),np.diag(expected))))),
          'phase_omission_mutant_relative':rel(cmut,expected),'one_over_2pi_mutant_relative':rel(c/(2*np.pi),expected)}
    assert item['relative_frobenius']<=1e-5 and item['max_normalized_entry']<=1e-6
    assert item['phase_omission_mutant_relative']>.1
    fixture.append(item)
emit('independent_ten_source_pair_kernel',fixture)

# Reuse retained projected factors. Check selected complex full-catalogue modes
# directly, without starting the full Fourier transform or old bank.
amp=json.loads((PRODUCT/'RESULT.json').read_text())['amplitude']
target,maps=r.quadrature_inventory([('C',53,32)])
positions=chi[:,None]*n
modechecks=[];gramchecks=[]
with np.load(EXT/'PV_FACTORS.npz') as factors:
    for bi,band in enumerate(maps['C']):
        F=factors[f'band{bi+1}']; C=result[f'band{bi+1}']
        gramchecks.append({'band':bi+1,'shape':list(F.shape),'gram_relative':rel(F@F.T,C)})
        assert gramchecks[-1]['gram_relative']<1e-13
        nt=len(band['u'])
        for ik,iu in [(0,1),(7,101),(16,250),(28,375),(32,nt-1)]:
            kv=band['k'][ik]; direction=band['u'][iu]
            raw=gi if False else g*(n@direction)*np.exp(1j*kv*(positions@direction))
            direct=A@raw
            scale=np.sqrt(band['wk'][ik]*r.old.power(kv,amp)*band['wu'][iu]/(2*np.pi**2))
            stored=(F[:,2*ik*nt+iu]+1j*F[:,(2*ik+1)*nt+iu]).reshape(3,36)
            expected=np.exp(-.5*(kv*r.RADII)**2)[:,None]*direct[None,:]*scale
            err=rel(stored,expected)
            modechecks.append({'band':bi+1,'radial_index':ik,'angular_index':iu,'relative':err})
            assert err<1e-6
emit('retained_factor_gram',gramchecks)
emit('retained_modes_against_independent_direct_source_sum',modechecks)

# The conditional law reconstructed without the production transport helper.
K=A@np.column_stack([d*(s['method_family']==m) for m in ('FP','OTHER','SN','TF')])
CD=150**2*(A@A.T); CK=.4**2*(K@K.T)
C=CD+CK+result['pv_total'][:36,:36]
emit('conditional_source_ownership',{'K_relative':rel(K,result['method_K']),
    'total_relative':rel(C,result['conditional_R5']), 'noise_trace':float(np.trace(CD)),
    'calibration_trace':float(np.trace(CK)), 'PV_trace':float(np.trace(result['pv_total'][:36,:36])),
    'baseline_not_added_max_abs':float(np.max(abs(C-result['conditional_R5'])))})
assert rel(C,result['conditional_R5'])<1e-13
assert rel(K,result['method_K'])<1e-13

# Support-sensitive refinement checks include the whole 108x108 joint covariance.
stages={name:dict(np.load(EXT/f'STAGE_{name}.npz')) for name in ['A','B','C']}
refinements=[]
for early,late in [('A','B'),('B','C')]:
    for band in ['band1','band2','total']:
        a=stages[early][band];b=stages[late][band];e,U=np.linalg.eigh(b)
        row={'stage_pair':[early,late],'band':band,'frobenius':rel(a,b),'support':{}}
        for tol in [1e-12,1e-10,1e-8]:
            keep=e>tol*e[-1]; W=U[:,keep]/np.sqrt(e[keep])
            delta=W.T@(a-b)@W
            row['support'][str(tol)]={'rank':int(sum(keep)),'whitened_spectral':float(np.linalg.norm(delta,2))}
        refinements.append(row)
emit('joint_108_covariance_refinement',refinements)

# Independent Cholesky+QR GLS, all specified unit-column rank thresholds.
designs={'shared_monopole':np.tile(np.eye(9)[:,0],4)[:,None],
    'affine_monopole':np.column_stack([np.tile(np.eye(9)[:,0],4),np.repeat(np.array([.025,.04,.06,.08])-.05,9)*np.tile(np.eye(9)[:,0],4)]),
    'shared_nine_coordinate_mean':np.tile(np.eye(9),(4,1))}
L=np.linalg.cholesky(C); ywhite=solve_triangular(L,result['theta'],lower=True)
Qs={};fitchecks={}
saved=json.loads((PRODUCT/'RESULT.json').read_text())['mean_comparison']
for name,X in designs.items():
    W=solve_triangular(L,X,lower=True); sv=np.linalg.svd(W/np.linalg.norm(W,axis=0),compute_uv=False)
    Qs[name]=qr(W,mode='economic')[0]
    residual=ywhite-Qs[name]@(Qs[name].T@ywhite); stat=float(residual@residual)
    fitchecks[name]={'qr_chi2':stat,'saved_chi2':saved['observed_chi2'][name],
        'rank_sensitivity':{str(tol):int(sum(sv>tol*sv[0])) for tol in [1e-12,1e-10,1e-8]},
        'unit_column_singular_values':sv.tolist()}
    assert abs(stat-saved['observed_chi2'][name])<1e-8
rng=np.random.default_rng(3602);white_noise=rng.standard_normal((2000,36)); stats={}
for name,Q in Qs.items():
    residual=white_noise-(white_noise@Q)@Q.T
    stats[name]=np.einsum('ij,ij->i',residual,residual)
names=list(designs); score=np.column_stack([stats[name]+designs[name].shape[1]*np.log(36) for name in names])
choice=np.argmin(score,axis=1); selected=np.array([stats[names[j]][i] for i,j in enumerate(choice)])
exceed=int(np.sum(selected>=saved['observed_chi2'][saved['chosen']]))
mc={'exceedances':exceed,'draws':2000,'plus_one_tail':(1+exceed)/2001,
    'counts':{name:int(np.sum(choice==i)) for i,name in enumerate(names)},
    'binomial_95percent_upper_if_zero':float(beta.ppf(.95,1,2000)),
    'reference':'known stipulated Gaussian covariance and shared-monopole mean; no empirical source coverage'}
assert mc['counts']==saved['selection_counts_under_shared_monopole']
assert mc['plus_one_tail']==saved['known_covariance_gaussian_selected_tail']
emit('mean_model_QR_and_rank',fitchecks);emit('independent_selection_reference_reproduction',mc)

# Test relative-only source/observer rank on the actual conditional metric.
AN=A@n; combined=np.column_stack([AN,-AN]); Wh=solve_triangular(L,combined,lower=True)
sv=np.linalg.svd(Wh/np.linalg.norm(Wh,axis=0),compute_uv=False)
emit('actual_source_observer_rank',{'rank_sensitivity':{str(tol):int(sum(sv>tol*sv[0])) for tol in [1e-12,1e-10,1e-8]},
    'null_max_abs':float(np.max(abs(combined@np.r_[np.array([17.,-23.,31.]),np.array([17.,-23.,31.])]))),
    'AN_saved_max_abs':float(np.max(abs(AN-op['AN'])))})

# Summary falsifier: compare each saved subset covariance at matched smoothing R.
summary=json.loads((PRODUCT/'SENSITIVITY.json').read_text())
errors=[]
with np.load(EXT/'SENSITIVITY_MATRICES.npz') as subsets:
    for name in subsets.files:
        for ir,R in enumerate([5,10,20]):
            sl=slice(36*ir,36*(ir+1));block=subsets[name][sl,sl];base=result['pv_total'][sl,sl]
            row=summary['results'][name]['bands_sum_blocks'][ir]
            expected_trace=float(np.trace(block)/np.trace(base));expected_frob=rel(block,base)
            errors.append({'case':name,'R_hinv_Mpc':R,'subset_trace':float(np.trace(block)),
                'same_radius_full_trace':float(np.trace(base)),
                'reported_ratio':row['trace_ratio_to_full_sample'],'correct_same_radius_ratio':expected_trace,
                'reported_relative_frobenius':row['frobenius_relative_to_full_sample'],
                'correct_same_radius_relative_frobenius':expected_frob})
emit('sensitivity_summary_counterexamples',errors)

# The actual subset operators reproduce full-refit form and zero excluded columns.
refit,identity=sens.fit_operator(np.ones(len(z),bool),s,op['sigma'])
emit('full_subset_refit_parity',{'A_relative':rel(refit,A),'A_X_max_abs':identity})
assert rel(refit,A)<1e-10

checks['elapsed_seconds']=time.monotonic()-START
(OUT/'INDEPENDENT_CHECKS.json').write_text(json.dumps(checks,indent=2)+'\n')
print('CHECKS_COMPLETED',checks['elapsed_seconds'])
