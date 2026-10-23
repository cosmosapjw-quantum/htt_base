import hashlib, importlib.util, json, sys
from pathlib import Path
import numpy as np
import mpmath as mp
import scipy
from scipy.linalg import solve, eigh
ROOT=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
P=ROOT/'docs/research_program/observational_publication_20261015/CONTINUOUS_RESEARCH_20261023/execution/K03_PM'
OUT=Path('/tmp/r23_k03_review_083f890c')
digest=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
r=json.loads((P/'RESULT.json').read_text()); manifest=json.loads((P/'CANDIDATE_MANIFEST.json').read_text())
checks={}; details={}
checks['candidate_identity']=digest(P/'CANDIDATE_MANIFEST.json')=='86942bbc9e3999b54579f8f119ae2f0d3537756c5f2deda57f5dffc096eff192'
checks['candidate_files']=all(digest(P/k)==v['sha256'] and (P/k).stat().st_size==v['bytes'] for k,v in manifest['files'].items())
checks['immutable_inputs']=all(digest(k)==v for k,v in r['source_hashes'].items())
checks['moments_identity']=digest(manifest['external_moments']['path'])==manifest['external_moments']['sha256']
checks['primary_pdf_identity']=digest('/mnt/extdrive/workdir/htt_open_data/r23_20261023/research/marcori_1805.12121v1/1805.12121v1.pdf')=='4aa208f5e54e7f6a871d83d3b8a6a892f2e11041e472fecf4a4feac4a1ef6be4'
with np.load(manifest['external_moments']['path']) as z: A=z['A']; K=z['K']; q=z['qH']; n=int(z['n'])
with np.load('/mnt/extdrive/workdir/htt_open_data/a22_20261023/astrometry/full_stats.npz') as z: G=z['G']; b=z['b']; old_n=int(z['n'])
T=np.zeros((102,96)); T[18:,:84]=np.eye(84)
T[np.array([3,4,5,9,10,11,15,16,17]),np.arange(84,93)]=1
for axis in range(3): T[np.array([0,6,12])+axis,93+axis]=1
N=T.T@G@T; J=K@T; bu=T.T@b
# Independent symmetric LDL solve of augmented 102-column system, no author solver.
M=np.block([[A,J],[J.T,N]]); rhs=np.r_[q,bu]
d=np.sqrt(np.diag(M)); Mn=M/np.outer(d,d)
sol=solve(Mn,rhs/d,assume_a='sym')/d
covcol=solve(Mn,np.eye(102)[:,:6]/d[:,None],assume_a='sym')/d[:,None]
cov=covcol[:6]; th=sol[:6]
nd=np.sqrt(np.diag(N)); Ns=N/np.outer(nd,nd)
NJ=solve(Ns,J.T/nd[:,None],assume_a='sym')/nd[:,None]
Nb=solve(Ns,bu/nd,assume_a='sym')/nd
F=A-J@NJ; s=q-J@Nb
rel=lambda a,b:float(np.linalg.norm(np.asarray(a)-np.asarray(b))/max(1.,np.linalg.norm(b)))
details['augmented_vs_candidate']={'theta_abs_max':float(np.max(np.abs(th-r['fit']['theta']))),'covariance_relative':rel(cov,r['fit']['covariance']),'F_relative':rel(F,r['fit']['F']),'score_relative':rel(s,r['fit']['score'])}
checks['augmented_estimates_covariance']=np.allclose(th,r['fit']['theta'],rtol=1e-9,atol=1e-10) and np.allclose(cov,r['fit']['covariance'],rtol=1e-9,atol=1e-10)
# Eigensystem square-root whitening instead of author's Cholesky basis.
F=(F+F.T)/2
vb,Qb=eigh(F[:3,:3]); vl,Ql=eigh(F[3:,3:]); Wb=(Qb/np.sqrt(vb))@Qb.T; Wl=(Ql/np.sqrt(vl))@Ql.T
sv=np.linalg.svd(Wb@F[:3,3:]@Wl,compute_uv=False)
angles=np.degrees(np.arccos(sv)); retention=1-sv*sv
checks['angles']=np.allclose(angles,r['principal_angles']['principal_angles_degrees'],rtol=1e-10,atol=1e-10)
fbar=F/np.sqrt(np.outer(np.diag(F),np.diag(F))); eig=eigh(fbar,eigvals_only=True)
checks['rank']=int(np.sum(eig>1e-10*eig[-1]))==6 and n==old_n==755850
R=np.column_stack((np.eye(6),-NJ.T)); covs=R@M@R.T
checks['score_identity']=rel(covs,F)<1e-10
checks['annihilation']=np.linalg.norm(R@np.vstack((J,N)))/(np.linalg.norm(R)*np.linalg.norm(np.vstack((J,N))))<1e-10
checks['estimator_covariance']=rel(cov@covs@cov,cov)<1e-10
# All 96 nuisance columns, and arbitrary signal injection, in the stored-score model.
inj=solve(F,J-J@solve(N,N,assume_a='sym'),assume_a='sym')
checks['all_nuisance_injections']=float(np.max(np.linalg.norm(inj,axis=0)))<1e-9*(1+np.linalg.norm(th))
details['all_nuisance_max_shift']=float(np.max(np.linalg.norm(inj,axis=0)))
details['retained_summary']={'theta':th.tolist(),'standard_deviations':np.sqrt(np.diag(cov)).tolist(),'rank':6,'F_condition':float(eig[-1]/eig[0]),'angles_degrees':angles.tolist(),'retention':retention.tolist()}
# New 256-source fixture: full old nuisance definitions and direct 2x2 covariance solve.
spec=importlib.util.spec_from_file_location('candidate',P/'profile.py'); p=importlib.util.module_from_spec(spec); spec.loader.exec_module(p)
model=p.old_model(); rng=np.random.default_rng(883601); nfix=256
ra=rng.uniform(0,360,nfix); dec=np.degrees(np.arcsin(rng.uniform(-.95,.95,nfix))); zz=rng.uniform(.15,4.4,nfix)
rr=json.loads(Path('/mnt/extdrive/workdir/htt_open_data/a22_20261023/astrometry/stats_receipt.json').read_text()); ref=tuple(np.array(rr[k]) for k in ['reference_center','reference_scale','vector_column_RMS'])
temp=ref[0]+ref[1]*rng.normal(size=(nfix,len(ref[0])))
X,_=model.design(ra,dec,zz,temp,ref); U=X@T
alpha=np.deg2rad(ra); delta=np.deg2rad(dec)
E=np.stack([np.column_stack([-np.sin(alpha),np.cos(alpha),np.zeros(nfix)]),np.column_stack([-np.sin(delta)*np.cos(alpha),-np.sin(delta)*np.sin(alpha),np.cos(delta)])],axis=1)
Q=np.sqrt((1+zz)*(1+.0001*zz)); II=2*zz/(1+zz+Q)
H=np.concatenate([(zz/II-1)[:,None,None]*E,(-1/II)[:,None,None]*E],axis=2)
checks['tangent_and_profile_design']=np.allclose(H,p.response(model.dipole(ra,dec)[:,:,:3],zz),rtol=1e-12,atol=1e-12)
sa=rng.uniform(1,3,nfix); sd=rng.uniform(1,3,nfix); rho=rng.uniform(-.8,.8,nfix)
C=np.zeros((nfix,2,2));C[:,0,0]=sa**2;C[:,1,1]=sd**2;C[:,0,1]=C[:,1,0]=rho*sa*sd
L=np.linalg.cholesky(C)
true=rng.normal(size=6); eta=rng.normal(size=96); y=H@true+U@eta+rng.normal(size=(nfix,2))*.02
WH=np.linalg.solve(L,H).reshape(-1,6); WU=np.linalg.solve(L,U).reshape(-1,96); wy=np.linalg.solve(L,y[...,None])[...,0].ravel()
WX,wy_old=model.whiten(X,y,sa,sd,rho)
checks['whitening']=np.allclose(wy,wy_old,rtol=1e-12,atol=1e-12) and np.allclose(WU,WX@T,rtol=1e-12,atol=1e-12)
Z=np.column_stack([WH,WU]); qr,qrR=np.linalg.qr(Z,mode='reduced'); dense=solve(qrR,qr.T@wy)[:6]
qc=solve(qrR,solve(qrR.T,np.eye(102)))[:6,:6]
Af=WH.T@WH;Jf=WH.T@WU;Nf=WU.T@WU;Ff=Af-Jf@solve(Nf,Jf.T,assume_a='sym');sf=WH.T@wy-Jf@solve(Nf,WU.T@wy,assume_a='sym')
stream=solve(Ff,sf,assume_a='sym');fc=solve(Ff,np.eye(6),assume_a='sym')
checks['full_nuisance_fixture']=np.allclose(dense,stream,rtol=1e-9,atol=1e-10) and np.allclose(qc,fc,rtol=1e-9,atol=1e-10)
details['fixture']={'n':nfix,'nuisance_columns':96,'theta_relative':rel(dense,stream),'covariance_relative':rel(qc,fc)}
# Numerical distance integral checks independently test the closed distance law.
mp.mp.dps=70; errs=[]
for z in [mp.mpf('0.08634503930807114'),mp.mpf('.2'),mp.mpf(1),mp.mpf(2),mp.mpf('4.627459688728043')]:
 integ=mp.quad(lambda u:1/((1+u)**mp.mpf('1.5')*mp.sqrt(1+mp.mpf('.0001')*u)),[0,z])
 closed=2*z/(1+z+mp.sqrt((1+z)*(1+mp.mpf('.0001')*z)))
 errs.append(abs(integ-closed))
checks['independent_distance_integral']=all(e<mp.mpf('1e-60') for e in errs)
details['distance_integral_max_error']=str(max(errs))
KH=70000/(1e6*648000/np.pi*149597870700)*31557600*(180/np.pi)*3600*1e6
physical=7499.25*np.linalg.norm(th[:3])/KH
checks['units_and_physical_domain']=abs(KH-p.KH)<1e-12 and np.isclose(physical,r['physical_domain']['R_norm_ab_over_KH'],rtol=1e-10) and physical>1
details['physical_R_norm']=float(physical)
result={'python':sys.version.split()[0],'numpy':np.__version__,'scipy':scipy.__version__,'mpmath':mp.__version__,'checks':{k:bool(v) for k,v in checks.items()},'all_pass':all(checks.values()),'details':details,'full_retained_row_passes':0,'repository_writes':False}
(OUT/'CHECKS.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2)); assert result['all_pass']
