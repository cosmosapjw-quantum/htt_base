"""Gaia-INFO-01: saved-law compression validation, no catalogue fit or physical detection.

Run from any cwd: python gaia_info.py [--draws 100000].
Requires the pinned R24 RESULT.json retained under ../sources/gaia/.
"""
from pathlib import Path
import argparse, hashlib, json, platform
import numpy as np
import scipy
from scipy.linalg import block_diag, null_space
from scipy.integrate import quad
from scipy.stats import chi2, ncx2, norm, beta
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

W=Path(__file__).resolve().parents[1]
SOURCE=W/'sources/gaia/METHOD_EXECUTION_20261023__k03_depth_moments__RESULT.json'
PIN='7f3f49a6b6d95b6ae0323d5bebd3afce0067b1a7'
EXPECTED_GIT_BLOB='e45d91abca9108e41136cea00ab1d641328e9537'

def gls(y,J,C,N=None):
    L=np.linalg.cholesky(C)
    WJ=np.linalg.solve(L,J)
    Wy=np.linalg.solve(L,y)
    Q=np.eye(len(C))
    if N is not None:
        WN=np.linalg.solve(L,N)
        U,s,_=np.linalg.svd(WN,full_matrices=False)
        rank=np.count_nonzero(s>1e-11*s[0])
        Q-=U[:,:rank]@U[:,:rank].T
    B=Q@WJ
    F=B.T@B
    cov=np.linalg.inv(F)
    A=np.linalg.solve(F,B.T)@np.linalg.solve(L,np.eye(len(C)))
    return A@y,cov,A,F,Q,L

def rate(mask):
    n=len(mask);k=int(np.count_nonzero(mask));p=k/n
    ci=[float(beta.ppf(.025,k,n-k+1)) if k else 0.,float(beta.ppf(.975,k+1,n-k)) if k<n else 1.]
    return {'rate':p,'MCSE':float(np.sqrt(p*(1-p)/n)), 'successes':k,'trials':n,'binomial_95_interval':ci}

def energy_fisher(delta,df=6):
    if delta==0:return 0.
    upper=ncx2.ppf(1-1e-12,df,delta*delta)
    def integrand(t):
        p=ncx2.pdf(t,df,delta*delta)
        if p<1e-250:return 0.
        ratio=np.exp(ncx2.logpdf(t,df+2,delta*delta)-np.log(p))
        return delta*delta*(ratio-1)**2*p
    return float(quad(integrand,0,upper,epsabs=2e-9,epsrel=2e-9,limit=200)[0])

def main(draws=100000):
    raw=SOURCE.read_bytes()
    blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
    assert blob==EXPECTED_GIT_BLOB,(blob,EXPECTED_GIT_BLOB)
    src=json.loads(raw);y=np.array(src['full24_state_uasyr']);C=np.array(src['full24_cov_uasyr2'])
    c=np.array(src['depth_c_reported_z_centers']);assert y.shape==(24,) and C.shape==(24,24)
    T=np.zeros((18,24))
    for i,ci in enumerate(c):T[6*i:6*i+6,6*i:6*i+6]=np.eye(6);T[6*i:6*i+6,18:]=ci*np.eye(6)
    K=np.zeros((12,18));K[:6,:6]=-np.eye(6);K[:6,6:12]=np.eye(6);K[6:,6:12]=-np.eye(6);K[6:,12:]=np.eye(6)
    Y=T@y;CY=T@C@T.T;delta=K@Y;Cd=K@CY@K.T
    np.testing.assert_allclose(Y,src['Y18_state_uasyr'],atol=2e-13)
    np.testing.assert_allclose(CY,src['Y18_cov_uasyr2'],atol=2e-13)
    np.testing.assert_allclose(delta,np.array(src['anchored_difference18_state_uasyr'])[6:],atol=2e-13)
    np.testing.assert_allclose(Cd,np.array(src['anchored_difference18_cov_uasyr2'])[6:,6:],atol=2e-13)

    # Experiment 1: original six within-bin slopes, other18 means are arbitrary nuisance.
    J=np.vstack([np.zeros((18,6)),np.eye(6)]);N=np.vstack([np.eye(18),np.zeros((6,18))])
    theta,V,A,F,Q,L=gls(y,J,C,N)
    np.testing.assert_allclose(theta,y[18:],atol=2e-12)
    np.testing.assert_allclose(V,C[18:,18:],atol=2e-12)
    np.testing.assert_allclose(F,src['F'],atol=2e-13)
    # A bin-value projection can be perfectly adequate for one estimand and destroy another.
    TN=T@N;TJ=T@J
    projection_defect=float(np.linalg.norm(TJ-TN@np.linalg.lstsq(TN,TJ,rcond=None)[0]))
    assert projection_defect<1e-13
    minimal_score=A@y
    # Fixed invertible tensor-coordinate/normalization change, propagated through every object.
    angle=.63;R=np.array([[np.cos(angle),-np.sin(angle),0],[np.sin(angle),np.cos(angle),0],[0,0,1]])
    U=block_diag(*([R]*8));reference=np.tile([2.,2.,2.,3.,3.,3.],4)
    B=U/reference[:,None]
    td,Vd,Ad,Fd,_,_=gls(B@y,B@J,B@C@B.T,B@N)
    equivalence_theta=float(np.max(np.abs(td-theta)));equivalence_info=float(np.max(np.abs(Fd-F)))
    assert equivalence_theta<1e-10 and equivalence_info<1e-12
    # Original slope inference also survives dropping cross-block covariance *after* this retained law.
    C24block=block_diag(C[:6,:6],C[6:12,6:12],C[12:18,12:18],C[18:,18:])
    tb,Vb,*_=gls(y,J,C24block,N)
    assert np.max(np.abs(tb-theta))<1e-10 and np.max(np.abs(Vb-V))<1e-10

    rng=np.random.default_rng(20261028)
    Z=rng.standard_normal((draws,6));alpha=.05;cut=chi2.isf(alpha,6);zcut=norm.isf(alpha)
    # Whitened efficient slope score: covariance is identity by construction.
    amplitudes=[0.,.5,1.,2.,2.5,3.,4.,5.]
    tests=[]
    for a in amplitudes:
        ZZ=Z.copy();ZZ[:,0]+=a
        q=np.sum(ZZ**2,axis=1)
        tests.append({'mahalanobis_amplitude':a,'signed_known_direction':rate(ZZ[:,0]>zcut),
          'signed_known_direction_exact':float(norm.sf(zcut-a)),
          'scalar_energy_omnibus':rate(q>cut),'scalar_energy_exact':float(ncx2.sf(cut,6,a*a)),
          'six_parameter_GLS_omnibus_equals_energy':True,
          'scalar_energy_fisher_fraction_for_signed_amplitude':energy_fisher(a)})
    pair_delta=2.5
    sign_accuracy=float(norm.cdf(pair_delta));orientation_accuracy=float(norm.cdf(pair_delta/np.sqrt(2)))
    # T(y)=T(-y) gives identical distributions at +/- theta for any zero-centred Gaussian covariance.
    sign_check=np.max(np.abs(np.sum((Z+pair_delta)**2,axis=1)-np.sum((-Z-pair_delta)**2,axis=1)))
    assert sign_check==0
    slope_coverage=rate(np.sum(Z**2,axis=1)<=cut)
    separate_marginals=rate(np.all(np.abs(Z)<=norm.ppf(.975),axis=1))
    robust=[]
    for infl in [1.,1.25,1.5,2.]:
        robust.append({'true_covariance_multiplier':infl,'using_uninflated_covariance':rate(infl*np.sum(Z**2,axis=1)<=cut),
                       'exact_uninflated_coverage':float(chi2.cdf(cut/infl,6)),'using_correct_inflation':slope_coverage})
    bias=[]
    for b in [0.,.5,1.,2.]:
        z=Z.copy();z[:,0]+=b
        bias.append({'unmodelled_bias_mahalanobis':b,'false_positive':rate(np.sum(z*z,axis=1)>cut),
                     'exact':float(ncx2.sf(cut,6,b*b))})

    # Experiment2: three bin-value means share a common6-vector and a declared g-depth6-vector.
    # This is a distinct constrained mean family, not the original free-bin within-bin slope target.
    N18=np.tile(np.eye(6),(3,1));J18=np.vstack([ci*np.eye(6)for ci in c]);J2=np.vstack([ci*ci*np.eye(6)for ci in c])
    th,Cth,A18,F18,Q18,L18=gls(Y,J18,CY,N18)
    thcontrast,Ccontrast,*_=gls(delta,K@J18,Cd)
    np.testing.assert_allclose(th,thcontrast,atol=1e-10);np.testing.assert_allclose(Cth,Ccontrast,atol=1e-10)
    Cind=block_diag(*[CY[6*i:6*i+6,6*i:6*i+6]for i in range(3)])
    thind,Cnom,Aind,*_=gls(Y,J18,Cind,N18)
    Cactual=Aind@CY@Aind.T
    vals=np.linalg.eigvalsh(np.linalg.solve(np.linalg.cholesky(Cnom),np.linalg.solve(np.linalg.cholesky(Cnom),Cactual).T).T)
    # Joint and deliberately independent-bin fits consume exactly the same true Gaussian draws.
    noise=rng.standard_normal((draws,18))@np.linalg.cholesky(CY).T
    ec=noise@A18.T;ei=noise@Aind.T
    qc=np.einsum('ni,ij,nj->n',ec,np.linalg.inv(Cth),ec)
    qi=np.einsum('ni,ij,nj->n',ei,np.linalg.inv(Cnom),ei)
    corrected_i=np.einsum('ni,ij,nj->n',ei,np.linalg.inv(Cactual),ei)
    covrates={'joint_GLS_and_tensorized':rate(qc<=cut),'independent_bin_nominal':rate(qi<=cut),
              'independent_point_estimator_with_correct_joint_sandwich':rate(corrected_i<=cut)}
    # Injection along the least-informative physical coefficient direction of this declared family.
    ev,vec=np.linalg.eigh(F18);v=vec[:,0]/np.sqrt(ev[0]);inj=2.5*v
    cp=np.einsum('ni,ij,nj->n',ec+inj,np.linalg.inv(Cth),ec+inj)
    ip=np.einsum('ni,ij,nj->n',ei+Aind@J18@inj,np.linalg.inv(Cnom),ei+Aind@J18@inj)
    isand=np.einsum('ni,ij,nj->n',ei+Aind@J18@inj,np.linalg.inv(Cactual),ei+Aind@J18@inj)
    powers={'joint_GLS_and_tensorized':rate(cp>cut),'independent_bin_nominal':rate(ip>cut),
             'independent_with_correct_sandwich':rate(isand>cut)}
    # Spin/glide is in the profiled common nuisance, hence exact invariance in this experiment.
    shift=N18@np.array([2.,-1.,3.,20.,-10.,5.])
    spin_error=float(np.max(np.abs(A18@(Y+shift)-A18@Y)))
    assert spin_error<1e-10
    # Minimal common carrier for two depth families; preserve all pairwise profile ratios.
    WJ1=Q18@np.linalg.solve(L18,J18);WJ2=Q18@np.linalg.solve(L18,J2)
    Ustar,s,_=np.linalg.svd(np.column_stack([WJ1,WJ2]),full_matrices=False)
    r=int(np.count_nonzero(s>1e-11*s[0]));Ustar=Ustar[:,:r]
    wy=Q18@np.linalg.solve(L18,Y);tstar=Ustar.T@wy
    def fit_res(v,M):return float(np.linalg.norm(v-M@np.linalg.lstsq(M,v,rcond=None)[0])**2)
    fullratio=fit_res(wy,WJ1)-fit_res(wy,WJ2)
    compratio=fit_res(tstar,Ustar.T@WJ1)-fit_res(tstar,Ustar.T@WJ2)
    ratio_error=abs(fullratio-compratio);assert r==12 and ratio_error<1e-9
    Uone=np.linalg.svd(WJ1,full_matrices=False)[0]
    tone=Uone.T@wy
    one_ratio=fit_res(tone,Uone.T@WJ1)-fit_res(tone,Uone.T@WJ2)
    one_ranks=[int(np.linalg.matrix_rank(Uone.T@Jx))for Jx in (WJ1,WJ2)]
    assert one_ranks==[6,6] and abs(one_ratio)<1e-9

    out={'schema':'htt.gaia_info_01/1','source_commit':PIN,'source_repo_path':'docs/research_program/observational_publication_20261015/METHOD_EXECUTION_20261023/k03_depth_moments/RESULT.json',
      'source_git_blob':blob,'source_sha256':hashlib.sha256(raw).hexdigest(),
      'scope':'New finite calculations using the saved Gaussian working law only; no raw catalogue fit, new observed data, solver or ODE.',
      'coordinates':src['coordinates'],'units':src['units'],'rows_in_inherited_source':src['rows'],
      'nuisance_columns_in_original_source':102,'new_original_slope_columns':6,
      'original_profile_trace_retention':src['information_trace_retained_fraction'],
      'original_profile_directionwise_generalized_retention':src['information_generalized_retention_eigenvalues'],
      'original_profile_statistic':src['score_chi2_6_scenario'],'original_profile_working_tail':src['score_chi2_6_working_tail_scenario'],
      'T_24_to_18':T.tolist(),'D_18_to_12':K.tolist(),'C24_eigen_extrema':np.linalg.eigvalsh(C)[[0,-1]].tolist(),
      'experiment1_original_free_bin_slopes':{'target':'six within-bin g(z) slopes; all18 bin intercepts free nuisance',
          'full_GLS_equals_retained_last6':True,'original_F_reproduced':True,'theta':theta.tolist(),'covariance':V.tolist(),
          'tensorized_coordinate_theta_max_difference':equivalence_theta,'tensorized_information_max_difference':equivalence_info,
          'T18_slope_information_with_free_bin_nuisance':'exactly zero; TJ lies in span(TN)',
          'T18_projection_defect':projection_defect,'scalar_even_compression_Fisher_at_null':0.,
          'correct_score_Fisher_fraction':1.,'C24_block_drop_does_not_change_this_profiled_target':True,
          'coverage95':slope_coverage,'power_and_information':tests,'sign_pair':{'delta':pair_delta,'signed_optimal_accuracy':sign_accuracy,'any_even_summary_accuracy':.5},
          'common_confidence_event':{'joint_ellipsoid_coverage':slope_coverage,'six_separate95_intersection':separate_marginals,'separate_intersection_exact':.95**6,'interpretation':'The joint event can be pushed through multiple nonlinear functionals. Correct joint GLS can do this too; no extra information is created by the five-factor bookkeeping.'},
          'orthogonal_direction_pair_whitened':{'delta':pair_delta,'signed_optimal_accuracy':orientation_accuracy,'radial_energy_accuracy':.5},
          'covariance_inflation':robust,'unmodelled_selection_bias_scenarios':bias},
      'experiment2_constrained_bin_depth_family':{'target':'bin mean alpha+c_b theta; independent test estimand, not original within-bin slope',
          'theta_joint':th.tolist(),'theta_independent':thind.tolist(),'trace_joint_covariance':float(np.trace(Cth)),
          'trace_independent_nominal_covariance':float(np.trace(Cnom)),'trace_independent_actual_covariance':float(np.trace(Cactual)),
          'nominal_relative_actual_covariance_eigenvalues':vals.tolist(),'coverage95':covrates,'power_at_mahalanobis_2p5':powers,
          'frame_spin_glide_profile_invariance_error':spin_error,'correct_12D_contrast_equals_18D_profile':True,
          'candidate_depth_functions':['g','g^2'],'union_carrier_rank':r,'single_family_rank':6,
          'observed_profile_deviance_difference_g_minus_g2':fullratio,'common_carrier_ratio_error':ratio_error,
          'single_g_score_projected_family_ranks':one_ranks,'single_g_score_profile_deviance_difference':one_ratio,
          'single_g_score_family_comparison':'Both compressed response matrices span all6 output coordinates, so profiled family discrimination is lost although g-parameter inference remains exact.'},
      'comparator_admission':'Independent-bin covariance is a deliberately misspecified control. Joint VSH/GLS is the optimal matched benchmark; tensorized coordinates do not add Fisher information.',
      'random_seed':20261028,'draws':draws,'runtime':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__}}
    (W/'lanes/GAIA_INFO.json').write_text(json.dumps(out,indent=2)+'\n')
    plot(out)
    print(json.dumps({'source_rows':src['rows'],'trace_retention':out['original_profile_trace_retention'],
      'C_D_theta_difference':equivalence_theta,'experiment2_coverage':covrates,'experiment2_power':powers,'common_carrier_rank':r,'profile_ratio_error':ratio_error},indent=2))

def plot(d):
    a=d['experiment1_original_free_bin_slopes'];b=d['experiment2_constrained_bin_depth_family'];rows=a['power_and_information']
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,ax=plt.subplots(1,3,figsize=(13,3.8))
    x=[r['mahalanobis_amplitude']for r in rows]
    ax[0].plot(x,[r['signed_known_direction_exact']for r in rows],'-o',label='Signed, specified direction')
    ax[0].plot(x,[r['scalar_energy_exact']for r in rows],'-s',label='Energy / joint GLS omnibus')
    ax[0].axhline(.05,color='grey',ls=':');ax[0].set(xlabel='Signal Mahalanobis amplitude',ylabel='Power, level 0.05',title='The question determines useful information');ax[0].legend(fontsize=8)
    ax[1].plot(x,[r['scalar_energy_fisher_fraction_for_signed_amplitude']for r in rows],'-o',label='Radial energy compression')
    ax[1].axhline(1,color='#b44430',ls='--',label='Efficient score / tensor coordinates')
    ax[1].set(xlabel='Signed-amplitude magnitude',ylabel='Retained Fisher fraction',ylim=(-.04,1.07),title='Correct scalar law; sign is still lost');ax[1].legend(fontsize=8)
    labels=['Joint GLS\n= tensorized','Independent\nbins','Independent +\njoint sandwich'];keys=list(b['coverage95'])
    vals=[b['coverage95'][k]['rate']for k in keys];errs=[1.96*b['coverage95'][k]['MCSE']for k in keys]
    ax[2].bar(range(3),vals,color=['#327ba8','#bd7458','#78a8a2']);ax[2].errorbar(range(3),vals,yerr=errs,fmt='none',color='black',capsize=3)
    ax[2].axhline(.95,color='black',ls='--');ax[2].set(xticks=range(3),xticklabels=labels,ylabel='Coverage of nominal 95% region',ylim=(.89,1.012),title='Cross-bin mean-family experiment')
    fig.suptitle('Gaia-INFO-01 — saved Gaussian-law validation, not a physical Gaia detection',fontsize=12)
    fig.tight_layout();fig.savefig(W/'figures/gaia_info_comparison.png',dpi=190);fig.savefig(W/'figures/gaia_info_comparison.pdf');plt.close(fig)
    fig,ax=plt.subplots(1,2,figsize=(9.5,3.6))
    ax[0].bar(['Before nuisance','After nuisance','Efficient score','Even power at null'],[1,d['original_profile_trace_retention'],d['original_profile_trace_retention'],0],color=['#aaa','#327ba8','#348b6c','#bd7458'])
    ax[0].set(ylabel='Information relative to unprofiled trace',ylim=(0,1.05),title='Distinct losses: profiling and compression');ax[0].tick_params(axis='x',rotation=17)
    a=d['experiment1_original_free_bin_slopes']['covariance_inflation'];xx=[r['true_covariance_multiplier']for r in a]
    ax[1].plot(xx,[r['exact_uninflated_coverage']for r in a],'-o',label='Covariance underestimate')
    ax[1].axhline(.95,color='#348b6c',ls='--',label='Correct covariance');ax[1].set(xlabel='True covariance / adopted covariance',ylabel='95% region coverage',ylim=(.5,1),title='Representation cannot repair a wrong law');ax[1].legend(fontsize=8)
    fig.tight_layout();fig.savefig(W/'figures/gaia_info_robustness.png',dpi=190);fig.savefig(W/'figures/gaia_info_robustness.pdf');plt.close(fig)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--draws',type=int,default=100000);args=parser.parse_args();main(args.draws)
