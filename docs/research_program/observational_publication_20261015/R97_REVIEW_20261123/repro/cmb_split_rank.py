import numpy as np, healpy as hp, json, time, sys
from scripts.r97 import cmb_injection_and_eb_leakage as B
from scripts.r96 import cmb_crossfit_null as C
from scripts.r94 import gaunt_fast as G
from scripts.r95.planck_fullres_teb_analysis import _all_six_spectra
from scipy.linalg import cho_solve
tm=time.monotonic()
ids,a,s,n,obs,man=C.load(); a=a[ids<300].copy(); mask=(ids[ids<300]%2==0); G._native_so(compile_if_needed=False)
with np.load(B.STREAM/"alm_basis_lmax48.npz") as f: basis=f['basis_T_alm'].astype(complex)
with np.load(B.STREAM/"observed_smica_commander_TEB_alm.npz") as f: obs64=f['smica_TEB_n64sub'].astype(complex)
I=[hp.Alm.getidx(48,l,m) for l,m in [(0,0),(1,0),(1,1)]]
def mom(x): return np.stack([x[...,I[0]].real,x[...,I[1]].real,x[...,I[2]].real,x[...,I[2]].imag],axis=-1)
normal=mom(basis); clean=a.copy(); clean[:,0]-=np.linalg.solve(normal.T,mom(a[:,0]).T).T@basis
test_j=json.load(open(B.OUT_JSON))
print('versions',sys.version.split()[0],np.__version__,hp.__version__,'precomputed and exact obs residual',np.max(abs(mom(obs64[0]))),np.max(abs(mom(obs[0]))),'corrected low moments',np.max(abs(mom(clean[:,0]))),'obs correction error',np.max(abs(obs[0]-(obs64[0]-np.linalg.solve(normal.T,mom(obs64[0]))@basis))),'IDs',np.array_equal(ids[ids<300],np.arange(300)),flush=True)
from hashlib import sha256
print('sha256',[(p.name,sha256(p.read_bytes()).hexdigest()) for p in (C.MANIFEST,B.STREAM/'alm_basis_lmax48.npz',B.STREAM/'observed_smica_commander_TEB_alm.npz',B.OUT_JSON)],flush=True)
for weights_all in (True,False):
  raw=_all_six_spectra(a if weights_all else a[mask],48)
  cw=np.array([B.r93.iso_theory_cl(),np.maximum(1e-12,raw['EE'].mean(axis=0)),np.maximum(1e-12,raw['BB'].mean(axis=0))])
  terms=[G.build_terms(x,48) for x in cw]
  def bip(arr):return np.column_stack([G.project(arr[:,i,:],terms[i],backend="native").reshape(len(arr),20) for i in range(3)])
  for A,o,tag in ((a,obs,'mixed'),(a,obs64,'matched64'),(clean,obs,'matched2048')):
    X=bip(A); y=bip(o[None])[0]; tr=X[mask];te=X[~mask]
    mx,sx=tr[:,:40].mean(0),tr[:,:40].std(0,ddof=1);my=tr[:,40:].mean(0)
    Z=(tr[:,:40]-mx)/sx
    W=np.linalg.solve(Z.T@Z+1500*np.eye(40),Z.T@(tr[:,40:]-my))
    def rem(d):return np.column_stack((d[:,:40], d[:,40:]-my-((d[:,:40]-mx)/sx)@W))
    varratio=rem(te)[:,40:].var(0,ddof=1).sum()/te[:,40:].var(0,ddof=1).sum()
    for label,xf,zf,yf in [('raw',tr,te,y),('ridge',rem(tr),rem(te),rem(y[None])[0])]:
      mu=xf.mean(0); sdev=xf.std(0,ddof=1); corr=np.corrcoef(xf.T)*.8+np.eye(60)*.2
      z=(zf-mu)/sdev; zy=(yf-mu)/sdev; zz=np.linalg.solve(corr,z.T).T
      score=np.einsum("ij,ij->i",z,zz); q=float(zy@np.linalg.solve(corr,zy)); k=int(sum(score>=q)); print(weights_all,tag,label,'score',q,'exceed',k,'p',(k+1)/151,'cond',np.linalg.cond(corr),'B var ratio',varratio,flush=True)
    if not weights_all and tag=='matched2048':
      rng=np.random.default_rng(112296);idx=rng.integers(0,len(te),size=(1500,len(te)))
      ratio=(rem(te)[idx,40:].var(1,ddof=1).sum(1) / te[idx,40:].var(1,ddof=1).sum(1));print("bootstrap holdout fixedfit ratio 95%",np.quantile(ratio,[.025,.975]))
print("seconds",time.monotonic()-tm)