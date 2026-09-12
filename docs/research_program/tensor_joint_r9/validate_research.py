#!/usr/bin/env python3
"""Bounded R9 method experiments; no observational likelihood admission."""
from pathlib import Path
import json, math, platform, sys, hashlib
import numpy as np
import scipy
from scipy.integrate import quad
from scipy.stats import chi2, beta, norm
from fractions import Fraction as F

HERE = Path(__file__).resolve().parent
OUT = HERE / 'evidence'
OUT.mkdir(exist_ok=True)
SEED, DRAWS, ALPHA = 20260912, 20000, .05
rng = np.random.default_rng(SEED)

def interval(k, n):
    return [float(beta.ppf(.025,k,n-k+1)) if k else 0.,
            float(beta.ppf(.975,k+1,n-k)) if k<n else 1.]

def summary(ok):
    k=int(np.count_nonzero(ok)); n=len(ok)
    return {'covered':k,'draws':n,'coverage':k/n,'binomial_95_percent':interval(k,n)}

def kernels(z, kind):
    if kind=='constant': h=lambda x:1.
    elif kind=='linear': h=lambda x:1+.45*x
    elif kind=='lcdm': h=lambda x:math.sqrt(.3*(1+x)**3+.7)
    else: raise ValueError(kind)
    integrals=np.array([quad(lambda u:1/h(u),0,float(x),epsabs=1e-13,epsrel=1e-12)[0] for x in z])
    fo=(1+z)/(np.array([h(x) for x in z])*integrals)
    fs=(1+z)*(1-fo)
    return fo,fs

def response(depths, kind):
    # Fixed six opposed Cartesian directions per depth; not actual survey geometry.
    dirs=np.vstack((np.eye(3),-np.eye(3)))
    n=np.tile(dirs,(len(depths),1)); z=np.repeat(depths,len(dirs))
    fo,fs=kernels(z,kind)
    return (5/np.log(10))*np.column_stack((n*fo[:,None],n*fs[:,None])),z,n

def geometry(A,N):
    q=np.linalg.qr(N,mode='complete')[0]
    rn=np.linalg.matrix_rank(N); u=q[:,rn:]; d=u.T@A
    v,s,wt=np.linalg.svd(d,full_matrices=False)
    tol=max(d.shape)*np.finfo(float).eps*(s[0] if len(s) else 0.)
    r=int(np.sum(s>tol)); p=v[:,:r]@v[:,:r].T
    return u,d,p,r,s

results={'scope':'R9_RESEARCH_MOCKS_ONLY','seed':SEED,'draws_per_cell':DRAWS,
 'alpha':ALPHA,'runtime':{'python':sys.version.split()[0],'numpy':np.__version__,
 'scipy':scipy.__version__,'symbolic_local':'stdlib fractions; SymPy unavailable','platform':platform.platform()},
 'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
 'interpretation':'Finite design checks, not product law validation or proof by Monte Carlo.'}

# Exact arithmetic oracle independent of NumPy factorization; Wolfram evaluates the symbolic series separately.
P=[[F(4,5),F(-2,5)],[F(-2,5),F(1,5)]]
assert [[sum(P[i][k]*P[k][j] for k in range(2)) for j in range(2)] for i in range(2)]==P
assert [sum(P[i][k]*[1,2][k] for k in range(2)) for i in range(2)]==[0,0]
D=[sum(row) for row in P]; t=[v/sum(x*x for x in D) for v in D]
assert t==[2,-1]
results['exact_rational']={'projector':str(P),'identified_map':str(t),'status':'PASS_EXACT_LOW_DIMENSIONAL_IDENTITIES','four_axis_CAS':'NOT_EXECUTED'}

cases=[('constant_two_depths','constant',[.02,.15]),
       ('lcdm_same_depth','lcdm',[.05,.05]),
       ('lcdm_shallow','lcdm',[.005,.02]),
       ('lcdm_spread','lcdm',[.02,.15]),
       ('lcdm_deeper','lcdm',[.1,.5])]
rows=[]
for name,kind,depths in cases:
    A,zs,dirs=response(np.array(depths),kind)
    N=np.ones((len(zs),1));u,d,p,r,s=geometry(A,N)
    if kind=='constant':
        assert np.max(np.abs(A[:,:3]+A[:,3:]))<1e-10 and r==3
    if name=='lcdm_same_depth': assert r==3
    elif kind=='lcdm': assert r==6
    theta=np.array([.5,-.2,.1,-.1,.3,.2])*1e-7
    # Unit Gaussian errors in declared whitened coordinates. Deliberately not observational magnitudes.
    noise=rng.normal(size=(DRAWS,len(zs)))@u
    c=float(np.sqrt(chi2.ppf(1-ALPHA,r)))
    # Bias lies in the response space and has known radius; worst boundary direction is used.
    direction=np.linalg.svd(d,full_matrices=False)[0][:,0];rho=1.5
    b=rho*direction
    residual=(noise+b)@p
    stat=np.linalg.norm(residual,axis=1)
    robust=stat<=c+rho; naive=stat<=c
    row={'name':name,'H_family':kind,'depths':depths,'rank':r,
         'singular_values':s.tolist(),'condition_identified':float(s[0]/s[r-1]),
         'full_six_parameter_identified':r==6,'bias_radius':rho,'chi_radius':c,
         'robust_ball_confidence':summary(robust),'ignored_bias_control':summary(naive),
         'rank_threshold':'max(shape)*eps*smax; fixture diagnostic only',
         'parameter_units':'dimensionless v/c; noise is a dimensionless whitened fixture'}
    rows.append(row)
results['response_cells']=rows

# Arbitrarily dependent marginal products with ONE common nuisance.
cal=[]; crit=float(norm.ppf(1-ALPHA/4))
for corr in [-.8,0.,.8]:
    cov=np.array([[1.,corr],[corr,1.]])
    e=rng.normal(size=(DRAWS,2))@np.linalg.cholesky(cov).T
    # theta=2 mu1-mu2; intersection of two marginal intervals has support radius 3*crit.
    error=2*e[:,0]-e[:,1]
    cal.append({'correlation':corr,'common_nuisance_join':summary(np.abs(error)<=3*crit),
      'per_product_alpha':ALPHA/2,'target_radius':3*crit,
      'independence_assumed_control':summary(np.abs(error)<=norm.ppf(.975)*np.sqrt(5)),
      'separate_nuisance_projection':'WHOLE_REAL_LINE_FOR_THETA'})
results['shared_calibration_cells']=cal

# Target-specific discrepancy support retains orientation, unlike a scalar max eigenvalue.
G=np.diag([.01,4.]);t=np.array([1.,0.]);dbar=.5
results['oriented_discrepancy']={'directional_support':float(np.sqrt(2*dbar*t@G@t)),
 'scalar_radius_support':float(np.sqrt(2*dbar*np.linalg.eigvalsh(G)[-1])*np.linalg.norm(t)),
 'interpretation':'Known fixture G only; no measured entropy, kernel or Teff consumer.'}
assert results['oriented_discrepancy']['directional_support']==.1

# Independent high-accuracy formula vs numerical quadrature for H=H0(1+.45z).
zs=np.array([.005,.02,.15,.5]);fo,fs=kernels(zs,'linear');rnum=fs/fo
rex=(1+.45*zs)*np.log1p(.45*zs)/.45-(1+zs)
err=float(np.max(np.abs(rnum-rex)));assert err<1e-10
results['depth_quadrature_oracle']={'max_abs_error':err,'tolerance':1e-10}

# Model diagnostic retained even if parameter projection discards its direction.
A=np.array([[1.],[0.]]);y=np.array([0.,8.]);p=A@np.linalg.pinv(A)
results['orthogonal_misspecification']={'parameter_residual':float(np.linalg.norm(p@y)),
 'model_residual':float(np.linalg.norm((np.eye(2)-p)@y)),
 'interpretation':'Perfect parameter-fit score does not establish model adequacy.'}

path=OUT/'research_checks.json';path.write_text(json.dumps(results,indent=2)+'\n')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,axes=plt.subplots(1,2,figsize=(10,4.4),layout='constrained')
for kind in ['constant','linear','lcdm']:
    zz=np.geomspace(.002,.5,150);oo,ss=kernels(zz,kind)
    axes[0].plot(zz,ss/oo+1,label=kind)
axes[0].set_xscale('log');axes[0].set_xlabel('redshift z (fixed-design model)');axes[0].set_ylabel('source/observer kernel ratio + 1');axes[0].legend()
x=np.arange(len(rows));axes[1].bar(x-.18,[r['robust_ball_confidence']['coverage'] for r in rows],.36,label='bounded bias retained')
axes[1].bar(x+.18,[r['ignored_bias_control']['coverage'] for r in rows],.36,label='bias ignored')
axes[1].axhline(.95,color='black',ls='--',lw=1);axes[1].set_ylim(.65,1.01)
axes[1].set_xticks(x,['constant H','same z','shallow','spread','deeper'],rotation=25,ha='right')
axes[1].set_ylabel('empirical true-parameter coverage');axes[1].legend(fontsize=8)
fig.suptitle('R9 research fixtures — not observational constraints',fontsize=12)
fig.savefig(OUT/'response_and_coverage.png',dpi=150);fig.savefig(OUT/'response_and_coverage.pdf');plt.close(fig)
(OUT/'figure_manifest.json').write_text(json.dumps({'figure':'response_and_coverage.png','source':'research_checks.json','generator':'../validate_research.py','owner':'HTT research','scope':'fixed synthetic design','claim_tier':'DIAGNOSTIC_ONLY','transfer_source':'none','sky_support_status':'six synthetic Cartesian directions','null_mock_status':'explicit selected Gaussian fixture; not an observed product law','caveats':['20,000 draws per cell; no empirical inference','Kernel curves use declared first-order flat-FLRW model']} ,indent=2)+'\n')
print(json.dumps({'response_cells':len(rows),'calibration_cells':len(cal),'draws_per_cell':DRAWS,'checks':'PASS_SCOPED','output':str(path)},indent=2))
