"""FIBRE-INFO-01: finite positive 2x2 count experiment; no ODE/catalogue fit.
python code/fibre_info.py --draws 100000
"""
from pathlib import Path
import argparse,json,hashlib,platform
import numpy as np
from scipy.linalg import expm
from scipy.stats import chi2,beta,norm
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
W=Path(__file__).resolve().parents[1]
SEED=20261028
sig=np.array([[[0,1],[1,0]],[[0,-1j],[1j,0]],[[1,0],[0,-1]]],complex)
I=np.eye(2,dtype=complex)
axes=np.array([[1,0,0],[-1,0,0],[0,1,0],[0,-1,0],[0,0,1],[0,0,-1]],float)

def rate(a):
 n=len(a);k=int(np.sum(a));p=k/n
 return {"rate":p,"MCSE":float(np.sqrt(p*(1-p)/n)),"successes":k,"draws":n,"binomial95":[float(beta.ppf(.025,k,n-k+1)) if k else 0.,float(beta.ppf(.975,k+1,n-k)) if k<n else 1.]}

def profile_info(M,nuisance=False):
 if not len(M):return np.zeros((3,3))
 Q=np.eye(len(M))
 if nuisance:Q-=np.ones((len(M),len(M)))/len(M)
 return M.T@Q@M/len(M) # per expected informative photon, at t=0

def draw(rng,theta,delta,draws,N=1000):
 t=axes@theta+delta
 assert np.max(abs(t))<1
 n=rng.binomial(N,1/3,size=(draws,6))
 k=rng.binomial(n,(1+t)/2)
 th=2*k/n-1
 est=(th[:,::2]-th[:,1::2])/2
 var=((1-th[:,::2]**2)/n[:,::2]+(1-th[:,1::2]**2)/n[:,1::2])/4
 return n,k,th,est,var,t

def natural_span_check():
 r=np.random.default_rng(SEED+1); th=r.uniform(-.2,.2,size=(40,3)); dd=r.uniform(-.1,.1,size=40)
 fixed=th@axes.T; uncertain=fixed+dd[:,None]
 h=lambda t:np.log((1+t)/(1-t))
 sf=np.linalg.svd(h(fixed),compute_uv=False);su=np.linalg.svd(h(uncertain),compute_uv=False)
 return {"known_zero_calibration_natural_parameter_span_rank":int(np.sum(sf>1e-12)),"unknown_calibration_natural_parameter_span_rank":int(np.sum(su>1e-12)),"unknown_span_singular_values":su.tolist(),"consequence":"At delta=0, opposite-axis successes can be pooled into three sufficient binomial counts; unknown common delta requires the six count channels for exact likelihood preservation on the open parameter family."}

def sign_check(draws):
 # Dedicated streams allow this finite correction to be rerun independently.
 srng=np.random.default_rng(SEED+2);trng=np.random.default_rng(SEED+3)
 eps=.08; true=np.array([0,0,eps]);correct=[];ties=0;strict=0
 for label in [-1,1]:
  n,k,_,_,_,_=draw(srng,label*true,0.,draws//2)
  # LLR=2*atanh(eps)*integer statistic: exact integer ties, no float ambiguity.
  stat=(2*k[:,4]-n[:,4])-(2*k[:,5]-n[:,5])
  tie=(stat==0);win=(label*stat>0)
  strict+=int(win.sum());ties+=int(tie.sum())
  tie_prediction=trng.choice([-1,1],size=len(stat))
  correct.extend((win | (tie & (tie_prediction==label))).tolist())
 out=rate(np.array(correct));out.update({"count_seed":SEED+2,"tie_seed":SEED+3,"tie_count":ties,"strict_successes":strict,"strict_success_fraction":strict/len(correct),"expected_accuracy_with_half_ties":(strict+.5*ties)/len(correct),"tie_rule":"Independent equal-probability class assignment for exact zero integer LLR statistic"})
 return out

def run(draws=100000):
 rng=np.random.default_rng(SEED)
 # Exact 6-point spherical quadrature: mean n=0 and mean nn=I/3.
 nvec=axes;theta=np.array([.2,-.3,.4]);f=np.array([I+n[2]*np.einsum("i,ijk->jk",theta,sig) for n in nvec])
 density=f.mean(axis=0);current=np.einsum("ni,nab->iab",nvec,f)/6
 expected=np.zeros((3,2,2),complex);expected[2]=np.einsum("i,ijk->jk",theta,sig)/3
 stress_trace=np.einsum("ni,nj,n->ij",nvec,nvec,np.trace(f,axis1=1,axis2=2))/6
 # Literal additive formula can fail positivity even for |eps|<1.
 additive_eigen=np.linalg.eigvalsh(.1*I+.2*sig[2])
 # State/effect/path all transform at their respective endpoints.
 Gs=expm(-.37j*(sig[0]+.4*sig[2]));Go=expm(.29j*(sig[1]-.2*sig[2]))
 rho=(I+np.einsum("i,ijk->jk",theta,sig))/2
 Us=[I,expm(.25j*np.pi*sig[1]),expm(-.25j*np.pi*sig[0])]
 R=(I+sig[2])/2
 before=[];after=[];effective=[]
 for U in Us:
  before.append(float(np.trace(R@U@rho@U.conj().T).real))
  fp=Gs@rho@Gs.conj().T;Up=Go@U@Gs.conj().T;Rp=Go@R@Go.conj().T
  after.append(float(np.trace(Rp@Up@fp@Up.conj().T).real))
  eff=U.conj().T@sig[2]@U
  effective.append([float(np.trace(s@eff).real/2) for s in sig])
 effective=np.array(effective)
 np.testing.assert_allclose(effective,[[0,0,1],[1,0,0],[0,1,0]],atol=1e-14)
 # Pure helicity U(1) connection cannot rotate a helicity detector into coherence.
 phases=[0.,.37,1.1];geom_z=[];geom_x=[]
 for phase in phases:
  Ug=expm(1j*phase*sig[2])
  geom_z.append([float(np.trace(s@Ug.conj().T@sig[2]@Ug).real/2) for s in sig])
  geom_x.append([float(np.trace(s@Ug.conj().T@sig[0]@Ug).real/2) for s in sig])
 geometric_connection={"helicity_detector_rank":int(np.linalg.matrix_rank(geom_z,tol=1e-12)),"linear_detector_rank":int(np.linalg.matrix_rank(geom_x,tol=1e-12)),"helicity_effect_axes":geom_z,"linear_effect_axes":geom_x,"assumption":"Only opposite helicity phases; generic SU2 converters require a separately supplied interaction/analyzer."}
 designs={"A_trace":np.zeros((0,3)),"B_helicity":np.array([[0,0,1.]]),"C_xyz_effects":np.eye(3),"D_two_calibrated_paths":effective[:2],"balanced_six_effects":axes}
 ranks={k:{"known_calibration_rank":int(np.linalg.matrix_rank(M)) if M.size else 0,"unknown_common_signed_dipole_rank":int(np.linalg.matrix_rank(profile_info(M,True),tol=1e-10)),"profile_information_per_informative_photon":profile_info(M,True).tolist()} for k,M in designs.items()}
 # Same acquired 6-analyzer count law; all views below are deterministic reductions.
 cases={}
 for name,th0 in [("null",np.zeros(3)),("x_signal",np.array([.1,0,0])),("z_signal",np.array([0,0,.1])),("mixed",np.array([.12,.08,.06]))]:
  n,k,t,est,var,true_t=draw(rng,th0,.025,draws)
  wald=np.sum((est-th0)**2/var,axis=1)
  nullstat=np.sum(est**2/var,axis=1)
  # Six simultaneous Clopper-Pearson intervals, union bound alpha=0.05.
  alpha=.05/6
  lo=beta.ppf(alpha/2,k,n-k+1);hi=beta.ppf(1-alpha/2,k+1,n-k)
  lo=np.where(k==0,0,lo);hi=np.where(k==n,1,hi)
  included=np.all((2*lo-1<=true_t)&(true_t<=2*hi-1),axis=1)
  low_t=2*lo-1;high_t=2*hi-1
  physical_mean=axes@th0
  image_included=np.max(low_t-physical_mean,axis=1)<=np.min(high_t-physical_mean,axis=1)
  image_rejects_zero=np.max(low_t,axis=1)>np.min(high_t,axis=1)
  cases[name]={"theta":th0.tolist(),"calibration_delta":.025,"wald_joint95_coverage":rate(wald<=chi2.ppf(.95,3)),"exact_common_event_coverage":rate(included),"projected_physical_image_coverage":rate(image_included),"projected_image_excludes_zero":rate(image_rejects_zero),"joint3_false_positive_or_power":rate(nullstat>chi2.ppf(.95,3)),"helicity_z_false_positive_or_power":rate(est[:,2]**2/var[:,2]>chi2.ppf(.95,1)),"trace_null_likelihood_ratio":1.0,"mean_estimate":est.mean(axis=0).tolist()}
 # Sign classification at equal prior using the same count law, with fair ties.
 sign_result=sign_check(draws)
 # CP dephasing and exact Fisher spectra at the unpolarized point.
 lambdas=np.linspace(0,1,21);spectra=[];cp_errors=[]
 for lam in lambdas:
  K0=np.sqrt((1+lam)/2)*I;K1=np.sqrt((1-lam)/2)*sig[2]
  channel=lambda X:K0@X@K0.conj().T+K1@X@K1.conj().T
  A=np.diag([lam,lam,1.])
  cp_errors.append(float(np.linalg.norm(channel(rho)-(I+np.einsum("i,ijk->jk",A@theta,sig))/2)))
  spectra.append([lam**2,lam**2,1.])
 summary={"schema":"htt.fibre_info_01/1","scope":"Finite positive count-law methods experiment, no observational detection or new spacetime congruence","skill_context_used":"WORK_PACKET.md; PhysMath1.3 R2/R3/R5/R7/R9","source":"MF02 PDF p17 section1.6.4 equations1.6.8-10 already contains correct multiplicative distribution; pasted proposal omits brackets/f0 factor","seed":SEED,"draws_per_case":draws,"photon_budget":6000,"settings":6,"per_setting_photons":1000,"directions":"six Cartesian sphere quadrature directions","signal":"f0(E)[I+(n.e)theta.sigma], e=z, norm(theta)<=1","n0":"integral f0(E) d^3p/(2pi hbar)^3 per internal channel","units":"theta and detector/calibration contrasts dimensionless; j/(c n0), v/c dimensionless","checks":{"density_max_error":float(np.max(abs(density-I))),"current_max_error":float(np.max(abs(current-expected))),"trace_stress_max_error":float(np.max(abs(stress_trace-2*np.eye(3)/3))),"minimum_occupation_eigenvalue":float(np.min(np.linalg.eigvalsh(f))),"literal_additive_counterexample_eigenvalues":additive_eigen.tolist(),"joint_basis_path_effect_covariance_error":float(np.max(abs(np.array(before)-after))),"effective_path_axes":effective.tolist(),"dephasing_max_error":max(cp_errors)},"design_ranks":ranks,"exact_binomial_natural_span":natural_span_check(),"geometric_U1_connection":geometric_connection,"count_law":"p(n,s|k)=(1+s(n.e)(m_k.theta+delta))/12 on six directions and s=+/-1; an identity angular-selection nuisance eta(n.e) can be added and cancels from the r=s(n.e) marginal conditional on |n.e|=1","statistics":"Conditionally n_k~Binomial(1000,1/3), k_k|n_k~Binomial(n_k,(1+m_k.theta+delta)/2); theta_hat_i=(t_hat_+i-t_hat_-i)/2; exact simultaneous event is six Bonferroni Clopper-Pearson intervals","cases":cases,"equal_prior_sign_accuracy":sign_result,"trace_or_sorted_state_spectrum_sign_accuracy":.5,"dephasing":{"lambda":lambdas.tolist(),"Fisher_retained_by_axis":spectra,"channel":"((1+lambda)/2)rho+((1-lambda)/2)sigma_z rho sigma_z","at_lambda_zero_rank":1},"runtime":{"python":platform.python_version(),"numpy":np.__version__},"push":False,"native_solver_or_ODE":False}
 assert summary['checks']['current_max_error']<1e-14 and summary['checks']['joint_basis_path_effect_covariance_error']<1e-14
 (W/'lanes/FIBRE_INFO.json').write_text(json.dumps(summary,indent=2)+"\n")
 fig,axs=plt.subplots(1,3,figsize=(14,4),layout='constrained')
 labels=['Trace','Helicity','x/y/z','Two paths','Balanced ±axes'];keys=list(designs)
 pos=np.arange(5);axs[0].bar(pos-.17,[ranks[k]['known_calibration_rank'] for k in keys],.34,label='Calibration known');axs[0].bar(pos+.17,[ranks[k]['unknown_common_signed_dipole_rank'] for k in keys],.34,label='Common dipole nuisance');axs[0].set(xticks=pos,xticklabels=labels,ylim=(0,3.5),ylabel='Identifiable internal directions',title='Actual effects determine rank');axs[0].tick_params(axis='x',rotation=25);axs[0].legend(fontsize=8)
 names=['null','x_signal','z_signal'];xx=np.arange(3)
 axs[1].bar(xx-.18,[cases[k]['joint3_false_positive_or_power']['rate'] for k in names],.36,label='Joint 3-component test');axs[1].bar(xx+.18,[cases[k]['helicity_z_false_positive_or_power']['rate'] for k in names],.36,label='Helicity-z only');axs[1].axhline(.05,color='black',ls=':',lw=1);axs[1].set(xticks=xx,xticklabels=['Null','x signal','z signal'],ylim=(0,1),ylabel='Rejection probability',title='Same acquired photon counts');axs[1].legend(fontsize=8)
 axs[2].plot(lambdas,np.array(spectra)[:,0],label='Coherence x/y');axs[2].plot(lambdas,np.array(spectra)[:,2],label='Helicity z');axs[2].set(xlabel='Dephasing transmission λ',ylabel='Fisher fraction at unpolarized null',ylim=(-.03,1.05),title='A specified CP loss channel');axs[2].legend(fontsize=8)
 fig.suptitle('FIBRE-INFO-01 — finite detector experiment; no cosmological detection')
 for suffix in ['png','pdf']:fig.savefig(W/('figures/fibre_info_comparison.'+suffix),dpi=180)
 print(json.dumps({'checks':summary['checks'],'ranks':{k:(v['known_calibration_rank'],v['unknown_common_signed_dipole_rank']) for k,v in ranks.items()},'coverage':{k:v['wald_joint95_coverage']['rate'] for k,v in cases.items()},'common_event':{k:v['exact_common_event_coverage']['rate'] for k,v in cases.items()},'image_coverage':{k:v['projected_physical_image_coverage']['rate'] for k,v in cases.items()},'image_power':{k:v['projected_image_excludes_zero']['rate'] for k,v in cases.items()},'geometric_U1':geometric_connection,'power':{k:[v['joint3_false_positive_or_power']['rate'],v['helicity_z_false_positive_or_power']['rate']] for k,v in cases.items()},'sign_accuracy':summary['equal_prior_sign_accuracy']},indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--draws',type=int,default=100000);run(p.parse_args().draws)
