from pathlib import Path
import json,hashlib
import numpy as np
from scipy import linalg,optimize,stats
from htt.htt.infer.r60_covariance_calibration import linear_budget_distance
base=Path('docs/research_program/observational_publication_20261015')
r58=base/'R58_MIXED_TENSOR_CONVERGENCE_20261117/RESULTS';r60=base/'R60_COVARIANCE_CALIBRATION_20261117/RESULTS/RADIAL'
z=np.load(r58/'OWNED_TENSOR_CARRIERS.npz',allow_pickle=False);r=np.load(r60/'RADIAL_RESPONSE_CARRIERS.npz',allow_pickle=False);d=json.loads((r60/'RADIAL_VELOCITY_RESULT.json').read_text())
scale=np.array(d['design']['parameter_scale']);A=np.array(d['design']['A_physical_to_chart']);T=np.array(d['design']['T_chart_to_physical'])
def fit(y,C,X,sc):
 L=linalg.cholesky(C,lower=True);Y=linalg.solve_triangular(L,y,lower=True);Z=linalg.solve_triangular(L,X*sc,lower=True)
 Q,R=linalg.qr(Z,mode='economic');beta=linalg.solve_triangular(R,Q.T@Y);Ri=linalg.solve_triangular(R,np.eye(R.shape[0]));CV=Ri@Ri.T
 return beta*sc,sc[:,None]*CV*sc[None,:],float(np.sum((Y-Z@beta)**2)),(L,Q,R)
errors={k:0. for k in ['physical_response_identity','estimate_scaled','covariance_scaled_relative','wald_lr','bias_map','budget_relative_excess','budget_distance','budget_kkt_relative','critical_threshold','endpoint_speed']}
summary={};ratios=[];budgets_count=0;critical_count=0
for name,v in d['variants'].items():
 y=z[name+'__y32'];C=z[name+'__cov32'];X=z[name+'__response32x11'];Xp=r[name+'__response32x14_physical'];Xc=r[name+'__response32x14_chart']
 errors['physical_response_identity']=max(errors['physical_response_identity'],float(np.max(abs((Xc@A-Xp)*scale))))
 h,cv,res,_=fit(y,C,Xc,scale);h=T@h;cv=T@cv@T.T;oh=np.array(v['physical_estimate14']);oc=np.array(v['physical_covariance14'])
 errors['estimate_scaled']=max(errors['estimate_scaled'],float(np.max(abs((h-oh)/scale))))
 errors['covariance_scaled_relative']=max(errors['covariance_scaled_relative'],float(np.max(abs((cv-oc)/scale[:,None]/scale[None,:]))/np.max(abs(oc/scale[:,None]/scale[None,:]))))
 bh,bc,bres,(L,Q,R)=fit(y,C,X,scale[:11]);Zw=linalg.solve_triangular(L,Xp[:,11:],lower=True);H=scale[:11,None]*linalg.solve_triangular(R,Q.T@Zw)
 errors['bias_map']=max(errors['bias_map'],float(np.max(abs(H-v['constant_estimator_bias_map14slope_to11']))))
 for key,ix in {'all14':np.arange(14),'physical_angular8':np.arange(3,11),'quadrupole5':np.arange(6,11),'physical_dipole3':np.arange(3,6),'velocity0_3':np.arange(3),'velocity_slope3':np.arange(11,14)}.items():
  free=np.setdiff1d(np.arange(14),ix)
  reduced=fit(y,C,Xp[:,free],scale[free])[2] if free.size else float(y@linalg.solve(C,y,assume_a='pos'))
  errors['wald_lr']=max(errors['wald_lr'],abs(reduced-res-v['tests'][key]['wald']))
 for key,ix in {'physical_angular8':np.arange(3,11),'quadrupole5':np.arange(6,11),'physical_dipole3':np.arange(3,6)}.items():
  h0=bh[ix];c0=bc[np.ix_(ix,ix)];H0=H[ix];LC=linalg.cholesky(c0,lower=True);M=linalg.solve_triangular(LC,H0,lower=True);yy=linalg.solve_triangular(LC,h0,lower=True);sv=linalg.svdvals(M);ratios.append(float(sv[-1]/sv[0]))
  body=v['bounded_velocity_slope'][key]
  for radius_s,b in body['budgets'].items():
   radius=float(radius_s);w=np.array(b['nuisance_witness']);residual=yy-M@w;value=float(residual@residual);norm=np.linalg.norm(w);budgets_count+=1
   errors['budget_relative_excess']=max(errors['budget_relative_excess'],float(norm-radius)/max(radius,1.))
   errors['budget_distance']=max(errors['budget_distance'],abs(value-b['distance2']))
   if radius>0:
    g=M.T@(M@w-yy);eta=max(0.,-float(g@w)/(w@w)) if norm>0 and norm>radius*(1-1e-9) else 0.
    kr=np.linalg.norm(g+eta*w)/max(np.linalg.norm(M.T@yy),1e-20);errors['budget_kkt_relative']=max(errors['budget_kkt_relative'],float(kr))
  cr=body['critical_V1_norm_km_s']
  if cr is not None and cr>0:
   critical_count+=1;Mh=M*cr
   opt=optimize.minimize(lambda q:float(np.sum((yy-Mh@q)**2)),np.zeros(3),jac=lambda q:2*Mh.T@(Mh@q-yy),method='SLSQP',constraints={'type':'ineq','fun':lambda q:1-q@q,'jac':lambda q:-2*q},options={'ftol':1e-12,'maxiter':500})
   if not opt.success: raise RuntimeError('independent SLSQP failed '+name+' '+key+': '+opt.message)
   errors['critical_threshold']=max(errors['critical_threshold'],abs(opt.fun-body['threshold']))
 speed=max(np.linalg.norm(h[:3]+h[11:]*q/d['design']['zstar']) for q in [d['design']['z_min'],d['design']['z_max']])/d['design']['c_km_s']
 errors['endpoint_speed']=max(errors['endpoint_speed'],abs(speed-v['bestfit_max_speed_over_c']))
 summary[name]={'nested_lr_independent':bres-res,'nested_p_independent':float(stats.chi2.sf(bres-res,3)),'speed_over_c':float(speed),'dH_sd_inflation_minmax':[min(v['dH_sd_inflation']),max(v['dH_sd_inflation'])],'quadrupole_D_b3000':v['bounded_velocity_slope']['quadrupole5']['budgets']['3000.0']['distance2']}
print(json.dumps({'source_sha256':hashlib.sha256((r60/'RADIAL_VELOCITY_RESULT.json').read_bytes()).hexdigest(),'carrier_sha256':hashlib.sha256((r60/'RADIAL_RESPONSE_CARRIERS.npz').read_bytes()).hexdigest(),'max_errors':errors,'bounded_witness_count':budgets_count,'positive_critical_count':critical_count,'image_singular_ratio_minmax':[min(ratios),max(ratios)],'summary':summary},indent=2))
