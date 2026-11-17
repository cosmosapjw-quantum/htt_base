from pathlib import Path
import hashlib,json,sys,platform
import numpy as np
import scipy
from scipy import linalg,stats
base=Path('docs/research_program/observational_publication_20261015')
r58=base/'R58_MIXED_TENSOR_CONVERGENCE_20261117/RESULTS'
r60=base/'R60_COVARIANCE_CALIBRATION_20261117/RESULTS'
z=np.load(r58/'OWNED_TENSOR_CARRIERS.npz',allow_pickle=False)
a=json.loads((r60/'SENSITIVITY/SENSITIVITY_RESULT.json').read_text())
raw=json.loads((r58/'OWNED_TENSOR_RESULT.json').read_text())
native=json.loads((r58/'NATIVE_REPLAY/OWNED_TENSOR_RESULT.json').read_text())
ax=json.loads((r60/'AXISYMMETRIC_WITNESSES.json').read_text())
rows=z['row_indices32']; scale=z['parameter_scale']; names=sorted(a['baseline_results'])
def gls(y,c,x):
 L=linalg.cholesky(c,lower=True)
 yw=linalg.solve_triangular(L,y,lower=True)
 xw=linalg.solve_triangular(L,x,lower=True)
 beta,_,rank,_=linalg.lstsq(xw,yw,lapack_driver='gelsy')
 cov=linalg.solve(xw.T@xw,np.eye(x.shape[1]),assume_a='pos')
 res=yw-xw@beta
 return beta,cov,float(res@res),rank
out={'environment':{'python':platform.python_version(),'executable':sys.executable,'numpy':np.__version__,'scipy':scipy.__version__},'carrier_sha256':hashlib.sha256((r58/'OWNED_TENSOR_CARRIERS.npz').read_bytes()).hexdigest(),'variants':{},'frontier':{},'axis':{}}
cache={};errs={'fit_estimate_scaled_max':0.,'fit_cov_scaled_relative_max':0.,'block_wald_lr_max':0.,'gain_direct_max':0.,'contrast_reml_gain_identity_max':0.,'contrast_annihilation_max':0.,'native_raw_estimate_scaled_max':0.,'native_raw_cov_scaled_max':0.}
for name in names:
 y=z[name+'__y32'];x=z[name+'__response32x11'];n=z[name+'__white36'][np.ix_(rows,rows)];s=z[name+'__body36'][np.ix_(rows,rows)];c=n+s;xs=x*scale
 est,cov,res,rank=gls(y,c,xs);est=est*scale;cov=cov*scale[:,None]*scale[None,:]
 rec=a['baseline_results'][name];h=np.asarray(rec['estimate11']);v=np.asarray(rec['covariance11'])
 errs['fit_estimate_scaled_max']=max(errs['fit_estimate_scaled_max'],float(np.max(abs((est-h)/scale))))
 errs['fit_cov_scaled_relative_max']=max(errs['fit_cov_scaled_relative_max'],float(np.max(abs((cov-v)/scale[:,None]/scale[None,:]))/np.max(abs(v/scale[:,None]/scale[None,:]))))
 idxs={'all11':np.arange(11),'angular8':np.arange(3,11),'quadrupole5':np.arange(6,11),'dipole3':np.arange(3,6),'velocity3':np.arange(3)}
 for key,ix in idxs.items():
  free=np.setdiff1d(np.arange(11),ix)
  rr=gls(y,c,xs[:,free])[2] if len(free) else float(y@linalg.solve(c,y,assume_a='pos'))
  errs['block_wald_lr_max']=max(errs['block_wald_lr_max'],abs(rr-res-rec['tests'][key]['wald']))
 zz=linalg.null_space(xs.T)
 errs['contrast_annihilation_max']=max(errs['contrast_annihilation_max'],float(np.max(abs(zz.T@xs))))
 for kind,yc,nc,sc in [('zero_mean',y,n,s),('residual_contrast',zz.T@y,zz.T@n@zz,zz.T@s@zz)]:
  amp=a['amplitude_likelihoods'][name][kind]['amplitude'];C=nc+amp*sc
  gain=-.5*(np.linalg.slogdet(C)[1]-np.linalg.slogdet(nc)[1]+yc@linalg.solve(C,yc,assume_a='pos')-yc@linalg.solve(nc,yc,assume_a='pos'))
  errs['gain_direct_max']=max(errs['gain_direct_max'],abs(float(gain)-a['amplitude_likelihoods'][name][kind]['loglike_gain']))
  if kind=='residual_contrast':
   def rl(q):
    cc=n+q*s;ci=linalg.solve(cc,np.column_stack((y,xs)),assume_a='pos');j=xs.T@ci[:,1:]
    rr=gls(y,cc,xs)[2]
    return -.5*(np.linalg.slogdet(cc)[1]+np.linalg.slogdet(j)[1]+rr)
   errs['contrast_reml_gain_identity_max']=max(errs['contrast_reml_gain_identity_max'],abs(float(gain)-(rl(amp)-rl(0.))))
 oldh=np.array(raw['variants'][name]['fit']['estimate']);newh=np.array(native['variants'][name]['fit']['estimate'])
 oldv=np.array(raw['variants'][name]['fit']['covariance']);newv=np.array(native['variants'][name]['fit']['covariance'])
 errs['native_raw_estimate_scaled_max']=max(errs['native_raw_estimate_scaled_max'],float(np.max(abs((oldh-newh)/scale))))
 errs['native_raw_cov_scaled_max']=max(errs['native_raw_cov_scaled_max'],float(np.max(abs((oldv-newv)/scale[:,None]/scale[None,:]))))
 out['variants'][name]={'noise_eig_min':float(linalg.eigvalsh(n).min()),'signal_eig_min':float(linalg.eigvalsh(s).min()),'cov_condition':float(np.linalg.cond(c)),'scaled_information_condition':float(np.linalg.cond(xs.T@linalg.solve(c,xs,assume_a='pos'))),'angular_cov_condition':float(np.linalg.cond(v[3:,3:])), 'rank':int(rank)}
 cache[name]=(y,n,s,xs)
metric={'angular8':(np.arange(3,11),np.array([3.]*3+[7.5]*5)),'quadrupole5':(np.arange(6,11),np.array([7.5]*5)),'dipole3':(np.arange(3,6),np.array([3.]*3))}
feas=dist=kt=rad=0.;count=0;positive=0
for q in a['calibration_frontier']:
 y,n,s,xs=cache[q['model']];mu,V,_,_=gls(y,n+q['cosmic_variance_amplitude']*s,xs);mu=scale*mu;V=V*scale[:,None]*scale[None,:]
 ix,B=metric[q['target']];h=mu[ix];C=V[np.ix_(ix,ix)];b=np.asarray(q['witness']);r=q['critical_rms_log_distance'];dn=h-b;D=float(dn@linalg.solve(C,dn,assume_a='pos'))
 budget=float(np.sqrt(np.sum(b*b/B)));feas=max(feas,budget-r);dist=max(dist,abs(D-q['distance2']));rad=max(rad,abs(q['critical_rms_magnitude']-5/np.log(10)*r));count+=1
 if r>0:
  positive+=1;g=linalg.solve(C,b-h,assume_a='pos');w=b/B;eta=-float(g@w)/(w@w);residual=np.linalg.norm(g+eta*w)/max(np.linalg.norm(g),1.)
  kt=max(kt,residual,abs(D-q['threshold'])/q['threshold']);assert eta>0
 else: assert D<=q['threshold']*(1+1e-10)
out['frontier']={'count':count,'positive_budgets':positive,'max_budget_excess':feas,'max_distance_error':dist,'max_relative_kkt_or_threshold_error':kt,'max_magnitude_conversion_error':rad}
for name,v in ax['variants'].items():
 cov=np.asarray(native['variants'][name]['fit']['covariance']);mu=np.asarray(native['variants'][name]['fit']['estimate']);k=mu[6:];candidate=np.asarray(v['candidate_kappa5']);n=np.asarray(v['candidate_axis_icrs_unit']);amp=v['candidate_signed_frobenius_amplitude'];K=amp*np.sqrt(1.5)*(np.outer(n,n)-np.eye(3)/3);D=float((k-candidate)@linalg.solve(cov[6:,6:],k-candidate,assume_a='pos'));f=np.asarray(v['full_11d_profile_lift']);fd=float((f-mu)@linalg.solve(cov,f-mu,assume_a='pos'))
 out['axis'][name]={'distance_error':abs(D-v['candidate_delta_chi2']),'full_distance_error':abs(fd-D),'matrix_error':float(np.max(abs(K-v['candidate_matrix']))),'degeneracy_eigen_gap':float(np.min(abs(np.diff(linalg.eigvalsh(K))))),'margin':float(stats.chi2.ppf(.95,5)-D)}
out['max_errors']=errs
print(json.dumps(out,indent=2,allow_nan=False))
