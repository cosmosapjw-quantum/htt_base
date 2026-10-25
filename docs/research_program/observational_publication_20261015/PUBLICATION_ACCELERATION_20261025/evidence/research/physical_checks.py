"""Finite physical interpretations of retained HTT estimates; no catalogue/ODE run."""
from pathlib import Path
import json, hashlib
import numpy as np
from scipy.stats import chi2
from scipy.optimize import brentq
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output'; FIG=ROOT/'figures'
OUT.mkdir(exist_ok=True); FIG.mkdir(exist_ok=True)
src=ROOT/'sources/H03_SOURCE_TOMOGRAPHY.json'
j=json.loads(src.read_text()); wins=j['monopole_dipole_STF2_windows']
C36=np.array(j['joint_covariance_36x36'])
idx=np.array([9*k+i for k in range(4) for i in (1,2,3)])
C=C36[np.ix_(idx,idx)]
y=np.concatenate([w['dipole_cartesian_km_s_Mpc'] for w in wins])
R=np.vstack([np.array(w['bulk_velocity_design_response_9x3_per_Mpc'])[1:4] for w in wins])
G=np.tile(np.eye(3),(4,1))
def fit(y,X,C):
    L=np.linalg.cholesky(C); A=np.linalg.solve(L,X); z=np.linalg.solve(L,y)
    b=np.linalg.lstsq(A,z,rcond=None)[0]; res=z-A@b
    return {'coef':b,'prediction':X@b,'residual_whitened':res,'T':float(res@res),
            'rank':int(np.linalg.matrix_rank(A)), 'coef_cov':np.linalg.inv(A.T@A),
            'condition_whitened_raw_coordinates':float(np.linalg.cond(A))}
designs={'bulk':R,'constant_rate_dipole':G,'bulk_plus_constant_rate':np.column_stack([R,G])}
fits={}; Cblock=np.zeros_like(C)
for k in range(4):Cblock[3*k:3*k+3,3*k:3*k+3]=C[3*k:3*k+3,3*k:3*k+3]
for name,X in designs.items():
    r=fit(y,X,C);df=len(y)-r['rank'];cut=chi2.ppf(.95,df)
    r.update(df=df,chi2_tail_if_working_Gaussian=float(chi2.sf(r['T'],df)),
             threshold95=float(cut),minimum_whitened_mean_budget95=max(0.,np.sqrt(r['T'])-np.sqrt(cut)),
             summary_covariance_tau95_km_s_Mpc=float(brentq(lambda t:fit(y,X,C+t*t*np.eye(12))['T']-cut,0.,10.)),
             block_diagonal_covariance_T=fit(y,X,Cblock)['T'])
    fits[name]=r
rate=[]
for w in wins:
    H=w['H0_working_km_s_Mpc'];Q=np.array(w['STF2_matrix_km_s_Mpc']);D=np.array(w['dipole_cartesian_km_s_Mpc'])
    ev,vec=np.linalg.eigh(Q)
    rate.append({'z':w['z_center'],'H_km_s_Mpc':H,'Q_km_s_Mpc':Q,'eigenvalues_km_s_Mpc':ev,
                 'relative_principal_rates_percent':100*ev/H,
                 'Sigma_if_same_local_physical_response':np.linalg.norm(Q)/(np.sqrt(6)*H),
                 'directional_quadrupole_rms_fraction':np.sqrt(2/15)*np.linalg.norm(Q)/H,
                 'full_dipole_quadrupole_rms_fraction':np.sqrt(D@D/3+2*np.trace(Q@Q)/15)/H})

# Targeted numerical checks of the new algebra and data transformations.
rng=np.random.default_rng(20261025)
checks={}
checks['covariance_min_eigenvalue']=float(np.linalg.eigvalsh(C)[0]); assert checks['covariance_min_eigenvalue']>0
exact_fit=max(np.linalg.norm(fit(X@rng.normal(size=X.shape[1]),X,C)['residual_whitened']) for X in designs.values())
assert exact_fit<1e-10; checks['synthetic_exact_fit_max_residual']=float(exact_fit)
O,_=np.linalg.qr(rng.normal(size=(3,3)));O[:,0]*=np.linalg.det(O); U=np.kron(np.eye(4),O)
rotmax=0.
for name,X in designs.items():
    r=fits[name];rotmax=max(rotmax,abs(fit(U@y,U@X,U@C@U.T)['T']-r['T']))
    eta=r['minimum_whitened_mean_budget95'];eW=eta*r['residual_whitened']/np.sqrt(r['T'])
    yp=y-np.linalg.cholesky(C)@eW
    assert abs(fit(yp,X,C)['T']-r['threshold95'])<2e-10
checks['rotation_invariance_T_max_error']=float(rotmax);assert rotmax<1e-10
bound_n=0
for _ in range(200):
    q=rng.normal(size=(3,3));q=(q+q.T)/2;q-=np.trace(q)*np.eye(3)/3
    e=rng.normal(size=(3,3));e=(e+e.T)/2;e-=np.trace(e)*np.eye(3)/3;e*=rng.uniform(0,.4)/np.linalg.norm(e)
    h=2.;rh=.2;ht=h+rng.uniform(-rh,rh);rQ=.4
    actual=np.linalg.norm(q-e)/(np.sqrt(6)*ht)
    lo=max(0,np.linalg.norm(q)-rQ)/(np.sqrt(6)*(h+rh));hi=(np.linalg.norm(q)+rQ)/(np.sqrt(6)*(h-rh))
    assert lo-1e-14<=actual<=hi+1e-14
    assert np.max(np.abs(np.linalg.eigvalsh(q-e)-np.linalg.eigvalsh(q)))<=rQ+1e-14
    bound_n+=1
checks['response_bound_cases']=bound_n
mu,wm=np.polynomial.legendre.leggauss(24);ph=2*np.pi*np.arange(48)/48
n=np.stack([np.sqrt(1-mu[:,None]**2)*np.cos(ph),np.sqrt(1-mu[:,None]**2)*np.sin(ph),np.broadcast_to(mu[:,None],(24,48))],axis=-1)
quaderr=[]
for w in wins:
    q=np.array(w['STF2_matrix_km_s_Mpc']);v=np.einsum('...i,ij,...j->...',n,q,n)
    quaderr.append(abs(np.sum(wm[:,None]*v*v)/(2*48)-2*np.trace(q@q)/15))
checks['sphere_quadrupole_moment_max_error']=float(max(quaderr));assert max(quaderr)<1e-12

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
def save(fig,name):
    for ext in ['png','pdf']:fig.savefig(FIG/(name+'.'+ext),dpi=220,bbox_inches='tight')
    plt.close(fig)
z=np.array([w['z_center'] for w in wins])
fig,ax=plt.subplots(1,2,figsize=(10,3.8),layout='constrained')
ep=np.array([r['relative_principal_rates_percent'] for r in rate])
for i in range(3):ax[0].plot(z,ep[:,i],'o-',label=f'principal mode {i+1}')
ax[0].axhline(0,color='.5',lw=.8);ax[0].set(xlabel='window centre z',ylabel='relative quadrupole rate [%]',title='Measured rate-tensor eigenvalues');ax[0].legend(frameon=False)
for w in wins:
    h=w['H0_working_km_s_Mpc'];q=w['STF2_frobenius_km_s_Mpc'];r=np.linspace(0,4,120)
    ax[1].plot(r,np.maximum(0,q-r)/(np.sqrt(6)*h),label=f"z={w['z_center']:.3f}")
ax[1].set(xlabel=r'total tensor response-error radius [km s$^{-1}$ Mpc$^{-1}$]',ylabel=r'conditional lower bound on $\Sigma$',title='What a physical response must resolve');ax[1].legend(frameon=False)
save(fig,'physical_rate_eigenvalues')

fig,axs=plt.subplots(1,3,figsize=(11,3.6),layout='constrained')
styles={'bulk':('C1','--'),'constant_rate_dipole':('C2',':'),'bulk_plus_constant_rate':('C3','-')}
for k,ax in enumerate(axs):
    ax.errorbar(z,y.reshape(4,3)[:,k],yerr=np.sqrt(np.diag(C)).reshape(4,3)[:,k],fmt='ko',capsize=3,label='saved dipole; working SD')
    for name,r in fits.items():
        col,sty=styles[name];ax.plot(z,r['prediction'].reshape(4,3)[:,k],sty,c=col,label=name.replace('_',' '))
    ax.set(xlabel='window centre z',ylabel=r'$D_'+str(k+1)+r'$ [km s$^{-1}$ Mpc$^{-1}$]',title='ICRS '+['x','y','z'][k])
axs[0].legend(fontsize=7.5,frameon=False);save(fig,'physical_dipole_response')

fig,ax=plt.subplots(1,2,figsize=(10,3.8),layout='constrained')
for name,r in fits.items():
    eta=np.linspace(0,6,150);ax[0].plot(eta,np.maximum(0,np.sqrt(r['T'])-eta)**2/r['threshold95'],label=name.replace('_',' '))
ax[0].axhline(1,color='k',lw=.8);ax[0].set(xlabel='whitened mean-discrepancy budget',ylabel=r'$T_{\min}/\chi^2_{d,0.95}$',title='Exact response-error frontier');ax[0].legend(frameon=False,fontsize=8)
for K in [.001,.01,.1]:
    beta=np.geomspace(1e-5,.02,160);sig=.3*beta/(2*np.sqrt(K)*(1-beta**2));ax[1].loglog(beta,sig,label=f'K={K:g}')
ax[1].set(xlabel=r'normal-relative matter tilt $\beta$',ylabel=r'required LRS shear $\Sigma$',title=r'Bianchi V constraint: $w=0,\Omega_m=0.3$');ax[1].legend(frameon=False)
save(fig,'physical_error_and_geometry')

def plain(x):
    if isinstance(x,np.ndarray):return x.tolist()
    if isinstance(x,np.generic):return x.item()
    if isinstance(x,dict):return {k:plain(v) for k,v in x.items()}
    if isinstance(x,list):return [plain(v) for v in x]
    return x
result={'scope':'Derived finite interpretation of saved H03 carrier; no new catalogue fit or survey-null calibration',
        'source':{'path':str(src.relative_to(ROOT)),'sha256':hashlib.sha256(src.read_bytes()).hexdigest(),
                  'commit':'0d5ab96bdb55398076629099664c77517ec33bb4','git_blob':'538caae5212e576232b1c6b270cc084704504624'},
        'working_law':j['working_law'],'covariance_scope':j['full_joint_covariance_kind'],
        'data_dipoles':y,'data_covariance':C,'bulk_response':R,'fits':fits,'rate_tensors':rate,'checks':checks,
        'figure_metadata':{'owner':'MIO/obsstat exploratory physical interpretation','claim_tier':'SOURCE_WORKING_RESPONSE_ONLY',
                          'artifact_mode':'derived/replotted saved estimates','allowed_use':'compare finite response hypotheses; expose error budgets',
                          'transfer_source':'retained H03 window response; LRS Bianchi V algebraic constraint only',
                          'null_status':'working Gaussian conditional only','covariance_status':'inherited diagonal row-scatter law; shared-window covariance retained',
                          'forbidden_uses':'native Bianchi identification; physical global-tilt posterior; calibrated survey anomaly'}}
(OUT/'physical_results.json').write_text(json.dumps(plain(result),indent=2))
print(json.dumps(plain({'fits':{n:{k:v for k,v in r.items() if k in ['T','rank','df','chi2_tail_if_working_Gaussian','minimum_whitened_mean_budget95','summary_covariance_tau95_km_s_Mpc','block_diagonal_covariance_T']} for n,r in fits.items()},'checks':checks}),indent=2))
