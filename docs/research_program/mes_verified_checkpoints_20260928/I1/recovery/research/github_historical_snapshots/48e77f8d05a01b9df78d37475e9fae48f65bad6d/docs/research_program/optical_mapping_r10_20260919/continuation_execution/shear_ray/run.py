#!/usr/bin/env python3
"""Flat null characteristic oracle, independent of production T9 coefficients."""
from pathlib import Path
import argparse,json,hashlib,time,resource
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

CONFIG={'L_star':'arbitrary physical length','E_star':1.,'T0_K':2.7,'h_over_L':[.08,.04,.02,.01,.005,.0025,.00125], 'angular_grids':[8,16,32], 'energy_nodes':[32,64,128], 'pointwise_tolerance':2e-12,'fixed_h_quadrature_tolerance':2e-11,'odd_tolerance':2e-11,'last_derivative_relative_tolerance':.006,'richardson_relative_tolerance':5e-5,'h_limit':'right limit h->0; first-order forward quotient','resolution_limit':'fixed h=.08; angular and energy controls separate'}

def sphere(n):
 m,w=np.polynomial.legendre.leggauss(n);p=np.arange(2*n)*np.pi/n;z,phi=np.meshgrid(m,p,indexing='ij')
 e=np.stack([np.sqrt(1-z*z)*np.cos(phi),np.sqrt(1-z*z)*np.sin(phi),z],-1).reshape(-1,3)
 return e,np.repeat(w,2*n)*np.pi/n

def coefficients(e,w,field,normalize=False):
 if normalize:field=field/(w@field/(4*np.pi))-1
 q=15/(8*np.pi)*np.einsum('n,n,nij->ij',w,field,e[:,:,None]*e[:,None,:]-np.eye(3)/3)
 triple=np.einsum('ni,nj,nk->nijk',e,e,e)
 trace=np.einsum('ni,jk->nijk',e,np.eye(3))+np.einsum('nj,ik->nijk',e,np.eye(3))+np.einsum('nk,ij->nijk',e,np.eye(3))
 o=35/(8*np.pi)*np.einsum('n,n,nijk->ijk',w,field,triple-trace/5)
 dip=3/(4*np.pi)*np.einsum('n,n,ni->i',w,field,e)
 return q,o,dip

def propagate(e,S,h,energy_nodes):
 if h<=0 or h*np.linalg.norm(S,2)>=1:raise ValueError('Outside h>0 timelike full-sky domain')
 xsrc=-h*e
 v=xsrc@S.T;gam=1/np.sqrt(1-np.sum(v*v,axis=1))
 usrc=np.c_[gam,gam[:,None]*v]
 # p=(epsilon_obs/c)(1,e), c cancels in dimensionless energy ratio.
 punit=np.c_[np.ones(len(e)),e]
 metric=np.diag([-1.,1.,1.,1.])
 g=-np.einsum('ni,ij,nj->n',usrc,metric,punit)
 nodes,weights=np.polynomial.laguerre.laggauss(energy_nodes)
 # Integrate actual source occupation F(eps_src), not the g^-4 formula.
 intensity=np.sum((weights*nodes**3)[:,None]*np.exp(-(g[None,:]-1)*nodes[:,None]),axis=0)
 # Independent frequency-space temperature reconstruction from transported f.
 freq=np.array([1.,3.,7.]);occupation=1/np.expm1(freq[:,None]*g[None,:])
 temp=CONFIG['T0_K']*freq[:,None]/np.log1p(1/occupation)
 return g,intensity,temp,usrc,punit

def basis():
 out=[np.diag([1.,-1.,0.])/np.sqrt(2),np.diag([1.,1.,-2.])/np.sqrt(6)]
 for i,j in [(0,1),(0,2),(1,2)]:
  a=np.zeros((3,3));a[i,j]=a[j,i]=1/np.sqrt(2);out.append(a)
 out.append(sum(a*x for a,x in zip(out,[.2,-.3,.1,.4,-.2])))
 return out

def run(out):
 out.mkdir(parents=True,exist_ok=False);(out/'config.json').write_text(json.dumps(CONFIG,indent=2)+'\n')
 started=time.perf_counter();e,w=sphere(16);rows=[];roundoff=[];control=[]
 for idx,S in enumerate(basis()):
  qrows=[];trows=[]
  for h in CONFIG['h_over_L']:
   g,I,T,u,p=propagate(e,S,h,64)
   gref=(1+h*np.einsum('ni,ij,nj->n',e,S,e))/np.sqrt(1-h*h*np.einsum('ni,ij,nj->n',e,S@S,e))
   point=max(np.max(abs(g-gref)),np.max(abs(I-6*gref**-4))/6,np.max(abs(T-2.7/gref))/2.7)
   assert point<CONFIG['pointwise_tolerance']
   assert np.max(abs(np.einsum('ni,ij,nj->n',u,np.diag([-1,1,1,1]),u)+1))<2e-12
   q,o,d=coefficients(-e,w,I);tq,to,td=coefficients(-e,w,T[0],True)
   odd=max(np.max(abs(o)),np.max(abs(d)),np.max(abs(to)),np.max(abs(td)));assert odd<CONFIG['odd_tolerance']
   ref=-24*S;tref=-S;dq=q/h;dt=tq/h;qrows.append(dq);trows.append(dt)
   rows.append({'case':idx,'h':h,'domain_h_normS':float(h*np.linalg.norm(S,2)),'pointwise_residual':float(point),'odd_max':float(odd),'brightness_derivative_relative_error':float(np.linalg.norm(dq-ref)/np.linalg.norm(ref)),'temperature_derivative_relative_error':float(np.linalg.norm(dt-tref)/np.linalg.norm(tref)),'Pi2':q.tolist(),'Theta2':tq.tolist(),'S':S.tolist()})
  qr=2*qrows[-1]-qrows[-2];tr=2*trows[-1]-trows[-2]
  errors=[np.linalg.norm(qr+24*S)/np.linalg.norm(24*S),np.linalg.norm(tr+S)/np.linalg.norm(S)]
  assert max(errors)<CONFIG['richardson_relative_tolerance']
  assert max(rows[-1][k] for k in ['brightness_derivative_relative_error','temperature_derivative_relative_error'])<CONFIG['last_derivative_relative_tolerance']
  # Wrong source location/sign and wrong brightness power must fail the same derivative target.
  h=CONFIG['h_over_L'][-1];gwrong=propagate(e,-S,h,64)[1]
  wrong_sign=coefficients(-e,w,gwrong)[0]/h
  g=propagate(e,S,h,64)[0];wrong_power=coefficients(-e,w,6/g)[0]/h
  signerr=np.linalg.norm(wrong_sign+24*S)/np.linalg.norm(24*S);powererr=np.linalg.norm(wrong_power+24*S)/np.linalg.norm(24*S)
  assert signerr>1.9 and powererr>.7
  control.append({'case':idx,'richardson_errors':list(map(float,errors)),'wrong_sign_relative_error':float(signerr),'wrong_power_relative_error':float(powererr),'controls_rejected':True})
 # Hold h fixed while changing angular grid, then energy nodes separately.
 S=basis()[-1];h=.08;angular=[];energy=[]
 for grid in CONFIG['angular_grids']:
  ee,ww=sphere(grid);g,I,T,_,_=propagate(ee,S,h,64);angular.append(coefficients(-ee,ww,I)[0])
 for nodes in CONFIG['energy_nodes']:
  g,I,T,_,_=propagate(e,S,h,nodes);energy.append(coefficients(-e,w,I)[0])
 angular_errors=[float(np.linalg.norm(a-angular[-1])) for a in angular[:-1]];energy_errors=[float(np.linalg.norm(a-energy[-1])) for a in energy[:-1]]
 # A convergence sequence may start unresolved; admission uses the two finest
 # angular resolutions, retaining the coarse error and demanding improvement.
 assert angular_errors[-1]<CONFIG['fixed_h_quadrature_tolerance']
 assert angular_errors[-1]<angular_errors[0]/10
 assert max(energy_errors)<CONFIG['fixed_h_quadrature_tolerance']
 g,I,T,_,_=propagate(e,np.zeros((3,3)),h,64);assert np.max(abs(I-6))<2e-12
 assert np.max(abs(coefficients(-e,w,I)[0]))<2e-11
 # No derivative claim beyond the predeclared truncation/roundoff window.
 for hh in [1e-5,1e-7,1e-9]:
  _,ii,tt,_,_=propagate(e,S,hh,64)
  roundoff.append({'h':hh,'relative_error':float(np.linalg.norm(coefficients(-e,w,ii)[0]/hh+24*S)/np.linalg.norm(24*S))})
 fig,ax=plt.subplots(1,2,figsize=(10,4))
 for idx in range(6):
  rr=[r for r in rows if r['case']==idx];ax[0].loglog([r['h'] for r in rr],[r['brightness_derivative_relative_error'] for r in rr],'.-',label=f'S{idx}')
 ax[0].set(xlabel='h / L* (resolution fixed)',ylabel='relative brightness derivative error',title='Right-derivative limit');ax[0].legend(ncol=2)
 ax[1].semilogy([8,16],np.maximum(angular_errors,1e-16),'o-',label='angular: vs grid 32');ax[1].semilogy([32,64],np.maximum(energy_errors,1e-16),'s-',label='energy: vs 128 nodes');ax[1].set(xlabel='quadrature resolution (h/L*=0.08)',ylabel='absolute Pi2 difference',title='Fixed-h quadrature check');ax[1].legend();fig.suptitle('Flat shear characteristic: exploratory, no formal/observed admission');fig.tight_layout();fig.savefig(out/'convergence.png',dpi=170);plt.close(fig)
 result={'status':'PASS_EXPLORATORY_SHEAR_CHARACTERISTIC','scope':'right derivative at initially isotropic event, prescribed flat congruence and source x0=0','Pi0':6.,'rows':rows,'controls':control,'fixed_h':{'h':h,'angular_errors':angular_errors,'energy_errors':energy_errors},'roundoff_diagnostic_only':roundoff,'wall_seconds':time.perf_counter()-started,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'formal_eligible':False,'alpha_spent':0}
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['status','wall_seconds','peak_rss_kib']}))

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);args=ap.parse_args();run(args.output)
