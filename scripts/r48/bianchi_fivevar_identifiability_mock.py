#!/usr/bin/env python3
"""Solver-free Bianchi momentum/HTT observability mock; no physical transfer claim."""
from __future__ import annotations
import argparse,json,math,platform
from pathlib import Path
import numpy as np
SEED=20261109; COUNT_RESPONSE_MOCK=1.25; GAIA_E1_RESPONSE_MOCK=.80; KAPPA_ENTHALPY_MOCK=1.0

def stf(v):
 x=np.asarray(v,float)
 if x.shape!=(5,): raise ValueError("STF chart must have length 5")
 return np.array([[x[0],x[2],x[3]],[x[2],x[1],x[4]],[x[3],x[4],-x[0]-x[1]]])
def chart(S): return np.array([S[0,0],S[1,1],S[0,1],S[0,2],S[1,2]])
def momentum_A(n,S):
 n=np.asarray(n,float);return np.array([(n[1]-n[2])*S[1,2],(n[2]-n[0])*S[0,2],(n[0]-n[1])*S[0,1]])
def momentum_B(p,S):
 a,n2,n3=np.asarray(p,float);return np.array([3*a*S[0,0]+(n2-n3)*S[1,2],3*a*S[0,1]+n3*S[0,2],3*a*S[0,2]-n2*S[0,1]])
def JA(S): return np.array([[0,S[1,2],-S[1,2]],[-S[0,2],0,S[0,2]],[S[0,1],-S[0,1],0]])
def JB(S): return np.array([[3*S[0,0],S[1,2],-S[1,2]],[3*S[0,1],0,S[0,2]],[3*S[0,2],-S[0,1],0]])
def ricci_A(n):
 n1,n2,n3=np.asarray(n,float);return np.array([.5*(n1*n1-(n2-n3)**2),.5*(n2*n2-(n3-n1)**2),.5*(n3*n3-(n1-n2)**2)])
def ricci_B(a,n2,n3):
 d=np.array([-.5*(n2-n3)**2-2*a*a,.5*(n2*n2-n3*n3)-2*a*a,.5*(n3*n3-n2*n2)-2*a*a]);o=np.diag(d);o[1,2]=o[2,1]=a*(n2-n3);return o
def beta_from_M(M,w=KAPPA_ENTHALPY_MOCK):
 M=np.asarray(M,float);m=float(np.linalg.norm(M))
 if w<=0 or not np.isfinite(w): raise ValueError("positive finite enthalpy required")
 if m==0:return np.zeros(3)
 r=m/w;b=2*r/(1+math.sqrt(1+4*r*r));return M*(b/m)
def logpdf(y,means,C):
 L=np.linalg.cholesky(C);r=np.linalg.solve(L,(y[None,:]-means).T).T
 return -.5*(np.einsum('ij,ij->i',r,r)+len(y)*math.log(2*math.pi)+2*np.log(np.diag(L)).sum())
def weights(lw):
 x=np.exp(lw-np.max(lw));return x/x.sum()
def covariance(std,seed):
 r=np.random.default_rng(seed).normal(size=(len(std),len(std)));a=r@r.T;d=np.sqrt(np.diag(a));corr=a/np.outer(d,d);corr=.55*np.eye(len(std))+.45*corr
 return std[:,None]*corr*std[None,:]
def build(seed=SEED):
 S=stf([.2,-.05,.1,.08,.06]);ns={'II':np.array([1.,0.,0.]),'IX':np.array([2.,1.,1.])};M={k:momentum_A(v,S) for k,v in ns.items()}
 assert np.allclose(M['II'],M['IX'],atol=1e-14,rtol=0)
 b=beta_from_M(M['II']);R={k:np.sort(ricci_A(v)) for k,v in ns.items()}
 C=covariance(np.array([.075]*3+[.065]*3+[.05]*15),seed+1);Cr=np.eye(3)*.375;g=np.linspace(0,1.75,701);p=np.exp(-.5*((g-1)/.25)**2);p/=p.sum()
 means=[]
 for lam in g:
  bt=beta_from_M(lam*M['II']);means.append(np.r_[-COUNT_RESPONSE_MOCK*bt,-GAIA_E1_RESPONSE_MOCK*bt,np.tile(lam*chart(S),3)])
 return S,ns,M,b,R,C,Cr,g,p,np.asarray(means)
def posterior_lambda(y,g,p,m,C):return weights(logpdf(y,m,C)+np.log(p))
def gamma_q_9half(x):
 a,z=4.5,x/2;gl=math.lgamma(a);ap=a;term=sm=1/a
 for _ in range(10000):
  ap+=1;term*=z/ap;sm+=term
  if abs(term)<abs(sm)*1e-15:break
 return max(0.,min(1.,1-sm*math.exp(-z+a*math.log(z)-gl)))
def run_experiment(seed=SEED,n_rep=30000,n_post=12000,n_null=512):
 S,ns,M,beta0,R,C,Cr,g,p,means=build(seed);rng=np.random.default_rng(seed+2);h=rng.integers(0,2,n_rep);lam=np.clip(rng.normal(1,.25,n_rep),.25,1.75)
 mu=np.stack([np.interp(lam,g,means[:,j]) for j in range(means.shape[1])],axis=1);yk=mu+rng.multivariate_normal(np.zeros(21),C,size=n_rep)
 yr=R['II'][None,:]+(R['IX']-R['II'])[None,:]*h[:,None]+rng.multivariate_normal(np.zeros(3),Cr,size=n_rep)
 delta=R['IX']-R['II'];mahal=float(delta@np.linalg.solve(Cr,delta));llr=np.einsum('i,ni->n',delta,np.linalg.solve(Cr,(yr-(R['II']+R['IX'])/2).T).T)
 p1=1/(1+np.exp(-np.clip(llr,-700,700)));acc=float(np.mean((p1>=.5)==(h==1)));brier=float(np.mean((p1-h)**2))
 ent=-(p1*np.log(np.maximum(p1,1e-300))+(1-p1)*np.log(np.maximum(1-p1,1e-300)));mi=float(math.log(2)-ent.mean())
 u=rng.random(n_rep);ranks=np.where(h==0,u*(1-p1),(1-p1)+u*p1);counts=np.histogram(ranks,np.linspace(0,1,11))[0];chi2=float(np.sum((counts-n_rep/10)**2/(n_rep/10)))
 nrng=np.random.default_rng(seed+5);nullnorm=[]
 for _ in range(n_null):
  yn=means[0]+nrng.multivariate_normal(np.zeros(21),C);w=posterior_lambda(yn,g,p,means,C);ids=nrng.choice(len(g),32,p=w)
  nullnorm.extend(np.linalg.norm([beta_from_M(g[i]*M['II']) for i in ids],axis=1))
 nullnorm=np.asarray(nullnorm);drng=np.random.default_rng(seed+3);ykd=means[np.argmin(abs(g-1))]+drng.multivariate_normal(np.zeros(21),C)
 yrd=R['II']+drng.multivariate_normal(np.zeros(3),Cr);wl=posterior_lambda(ykd,g,p,means,C);pl=weights(logpdf(yrd,np.stack([R['II'],R['IX']]),Cr)+math.log(.5))
 prng=np.random.default_rng(seed+4);ids=prng.choice(len(g),n_post,p=wl);labels=prng.choice(2,n_post,p=pl);ls=g[ids]
 Ms=ls[:,None]*M['II'];betas=np.stack([beta_from_M(x) for x in Ms]);S5=ls[:,None]*chart(S);mixed=np.einsum('ni,ij,nj->n',betas,S,betas)*ls
 demo_lp=logpdf(yrd,np.stack([R['II'],R['IX']]),Cr);demo_llr=float(demo_lp[1]-demo_lp[0])
 t=np.arange(64)+.5;z=1-2*t/64;phi=math.pi*(3-math.sqrt(5))*t;rr=np.sqrt(1-z*z);dirs=np.c_[rr*np.cos(phi),rr*np.sin(phi),z]
 bmo=-betas;bc=bmo.mean(axis=0);bs=np.max(dirs@(bmo-bc).T,axis=1);SM=np.stack([stf(x) for x in S5]);Sc=SM.mean(axis=0)
 ss=np.max(np.einsum('di,nij,dj->dn',dirs,SM-Sc,dirs),axis=1);sh=np.hstack([S5,S5,S5]);Cpost=np.cov(sh,rowvar=False);Cdata=C[6:21,6:21]
 th=np.linspace(0,.25,101);bn=np.linalg.norm(bmo,axis=1);pip=np.array([np.mean(bn>=x) for x in th]);pin=np.array([np.mean(nullnorm>=x) for x in th])
 jw=np.linalg.solve(np.linalg.cholesky(Cr),delta);nn=jw[:,None];P=nn@np.linalg.pinv(nn.T@nn)@nn.T;je=(np.eye(3)-P)@jw
 flatI=ricci_A([0,0,0]);flatVII=ricci_A([0,2,2]);openV=ricci_B(1,0,0);openVII=ricci_B(1,2,2)
 return {'schema':'htt.r48_bianchi_fivevar_identifiability_mock/1','status':'SYNTHETIC_ORACLE_ONLY_NOT_OBSERVATIONAL_EVIDENCE',
 'seed':seed,'replications':n_rep,'posterior_draws':n_post,'null_data_realizations':n_null,'null_posterior_draws':len(nullnorm),
 'mock_response_calibration':{'count_dipole_scale':COUNT_RESPONSE_MOCK,'gaia_E1_like_scale':GAIA_E1_RESPONSE_MOCK,'kappa_enthalpy':KAPPA_ENTHALPY_MOCK,'status':'DECLARED_SYNTHETIC_ONLY_NOT_SURVEY_CALIBRATION'},
 'algebra':{'n_II':ns['II'].tolist(),'n_IX':ns['IX'].tolist(),'difference':(ns['IX']-ns['II']).tolist(),'shear_STF5':chart(S).tolist(),'momentum_kappa_q':M['II'].tolist(),
 'beta_NM':beta0.tolist(),'beta_norm':float(np.linalg.norm(beta0)),'ricci_eigenvalues':{k:v.tolist() for k,v in R.items()},'momentum_residual':float(np.linalg.norm(M['II']-M['IX'])),
 'class_A_flux_jacobian_rank':int(np.linalg.matrix_rank(JA(S))),'class_A_trace_kernel_residual':float(np.linalg.norm(JA(S)@np.ones(3))),
 'class_B_flux_jacobian_rank':int(np.linalg.matrix_rank(JB(S))),'class_B_flux_jacobian_det':float(np.linalg.det(JB(S))),'frame_closure':'beta_RM=beta_NM; beta_MO=-beta_NM; beta_RO=0'},
 'likelihood':{'kinematic_dimension':21,'curvature_dimension':3,'kinematic_covariance_min_eigenvalue':float(np.linalg.eigvalsh(C)[0]),'kinematic_cross_covariance_frobenius':float(np.linalg.norm(C-np.diag(np.diag(C)))),
 'curvature_noise_sigma':math.sqrt(.375),'curvature_mahalanobis_separation':mahal,'kinematic_only_label_information_nats':0.,'curvature_oracle_label_information_nats':mi,
 'expected_target_posterior_kl_full_data_nats':mi,'target_kl_loss_full_HTT_with_x_geometry_score_nats':0.,'target_kl_loss_ablation_no_geometry_carrier_nats':mi,'map_accuracy':acc,'brier_score':brier,
 'randomized_rank_SBC':{'chi_square':chi2,'dof':9,'p_value':gamma_q_9half(chi2),'bin_counts':counts.tolist()},
 'nuisance_projection':{'label_rank_before':1,'label_rank_after_parallel_unbounded_calibration_nuisance':int(np.linalg.norm(je)>1e-10),'residual_norm':float(np.linalg.norm(je))}},
 'HTT_five_views':{'shared_sample_ids':n_post,'sample_id_first_last':[0,n_post-1],
 'x':{'samplewise_fields':['lambda','sigma_STF5','beta_NM','beta_RM','beta_MO','beta_RO','sigma:beta_RM beta_RM/H_ref','count_dipole','Gaia_E1_like','three shear windows'],
 'curvature_carrier':'IDEALIZED_ORACLE_ONLY','curvature_observed_eigenvalues':yrd.tolist(),'curvature_log_likelihood_ratio':demo_llr,'posterior_P_IX_demo':float(pl[1]),
 'mixed_sigma_beta_beta_mean':float(mixed.mean()),'mixed_sigma_beta_beta_sd':float(mixed.std(ddof=1))},
 'Q':{'instantaneous_momentum_constraint':'ADMITTED','frame_closure':'EXACT_COLLINEAR','kinematic_response':'MOCK_CALIBRATED','curvature_sensor':'IDEALIZED_ORACLE_ONLY','real_catalogue_anchor':'UNAVAILABLE','dynamical_transport':'UNAVAILABLE'},
 'Pi':{'thresholds':th.tolist(),'posterior_beta_norm_exceedance':pip.tolist(),'null_law':'MATCHED_ZERO_TILT_INJECTION_FULL_POSTERIOR_PUSHFORWARD','null_beta_norm_exceedance':pin.tolist(),
 'null_mcse_max':float(np.max(np.sqrt(pin*(1-pin)/len(nullnorm))))},
 'F':{'directions':dirs.tolist(),'beta_center':bc.tolist(),'beta_support':bs.tolist(),'beta_anchor_radius':.05,'beta_occupancy':(bs/.05).tolist(),
 'shear_center_STF5':chart(Sc).tolist(),'shear_support':ss.tolist(),'shear_anchor_radius':.1,'shear_occupancy':(ss/.1).tolist(),'basis':'centered posterior deviation hull'},
 'G_F':{'windows':['W0','W1','W2'],'transport':'IDENTITY_MOCK_NO_EVOLUTION','posterior_cross_window_covariance_shape':list(Cpost.shape),
 'posterior_cross_window_covariance_trace':float(np.trace(Cpost)),'data_cross_window_covariance_shape':list(Cdata.shape),'data_cross_window_crossblock_norm':float(np.linalg.norm(Cdata[:5,5:10]))}},
 'presentation_equivalence_controls':{'I_vs_special_VII0':{'Ricci_I':flatI.tolist(),'Ricci_VII0':flatVII.tolist()},
 'V_vs_special_VIIh':{'h':.25,'Ricci_V':openV.tolist(),'Ricci_VIIh':openVII.tolist(),'sectional_curvature':-1.}},
 'claim_ceiling':['Class-A momentum map has an exact common-trace kernel.','Class-B map is generically rank 3 at fixed shear, outside det(J_B)=0.',
 'Selected II/IX pair has equal instantaneous normal-frame flux/tilt but different intrinsic 3-Ricci spectra.','Only an idealized curvature oracle separates the selected pair in this mock.',
 'No real data, Bianchi transfer, evolution solver, or global HTT sufficiency is established.'],
 'verification':{'python':platform.python_version(),'numpy':np.__version__,'local_pytest':'NOT_RUN_BY_SCRIPT','exact_repo_checkout':'NOT_RECORDED_BY_SCRIPT','github_actions':'NOT_RECORDED_BY_SCRIPT'}}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--seed',type=int,default=SEED);ap.add_argument('--replications',type=int,default=30000)
 ap.add_argument('--posterior-draws',type=int,default=12000);ap.add_argument('--null-draws',type=int,default=512)
 ap.add_argument('--output',type=Path,default=Path('R48_BIANCHI_FIVEVAR_MOCK_REPORT.json'));a=ap.parse_args()
 out=run_experiment(a.seed,a.replications,a.posterior_draws,a.null_draws);a.output.parent.mkdir(parents=True,exist_ok=True)
 a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n',encoding='utf-8')
 print(json.dumps({'report':str(a.output),'MI_nats':out['likelihood']['curvature_oracle_label_information_nats'],'MAP_accuracy':out['likelihood']['map_accuracy'],
 'SBC_chi2':out['likelihood']['randomized_rank_SBC']['chi_square']},indent=2))
if __name__=='__main__':main()
