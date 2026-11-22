from scripts.r97 import cmb_injection_and_eb_leakage as B
import numpy as np, healpy as hp, time, json
start=time.monotonic();j=json.load(open(B.OUT_JSON));s=j['anisotropy_injection_recovery']['coherent_additive_L2_sweep_150_heldout'];A=np.array([x['A_injected'] for x in s.values()]);mean=np.array([x['recovered_amplitude_mean'] for x in s.values()]);var=np.array([x['recovered_amplitude_sd']**2 for x in s.values()]);m=np.linalg.lstsq(np.c_[np.ones(6),np.sqrt(A),A],mean,rcond=None)[0];v=np.linalg.lstsq(np.c_[np.ones(6),2*np.sqrt(A),A],var,rcond=None)[0];fac=np.polyfit(A,np.sqrt(A),1)[0];print('exact additive expansion: intercept,mean cross,signal',m,'variances (baseline,covariance,interference)',v,'slope_SE',fac*np.sqrt(v[2]/150),'residual',max(abs(mean-np.c_[np.ones(6),np.sqrt(A),A]@m)),flush=True)
mask=hp.read_map(str(B.MASK_P_FITS),dtype=np.float64);w=hp.map2alm(mask,lmax=96,iter=0,pol=False);del mask
print('mask L0,96 elapsed',w[0],time.monotonic()-start,flush=True)
th=np.zeros(49);ell=np.arange(2,49);th[2:]=.01*B.r93.iso_theory_cl()[2:]*(ell/10)**.5
ll,mm=hp.Alm.getlm(48);I=np.concatenate([hp.Alm.getidx(48,i,np.arange(i+1)) for i in ell]);assert len(I)==1222
def sim(nside,n):
  rng=np.random.default_rng(9703);W=hp.alm2map(w,nside,lmax=96,pol=False);EE=[];BB=[]
  for i in range(n):
    a=np.zeros(len(ll),dtype=complex)
    for l in ell:
      z=rng.normal(size=2*l+1);a[hp.Alm.getidx(48,l,0)]=np.sqrt(th[l])*z[0];a[hp.Alm.getidx(48,l,np.arange(1,l+1))]=np.sqrt(th[l]/2)*(z[1::2]+1j*z[2::2])
    q,u=hp.alm2map_spin([a,np.zeros_like(a)],nside,2,lmax=48)
    e,b=hp.map2alm_spin([q*W,u*W],2,lmax=48);EE.append(hp.alm2cl(e)[2:]);BB.append(hp.alm2cl(b)[2:])
  E,F=np.stack(EE),np.stack(BB);r=F/E
  print('nside,n mean-of-ratios8,ratio-of-averages8,mean-of-ratios-all,ratio-of-averages-all',nside,n,r[:8].mean(),(F[:8].mean(0)/E[:8].mean(0)).mean(),r.mean(),(F.mean(0)/E.mean(0)).mean(),'seconds',time.monotonic()-start,flush=True)
  if n>=200:
    targets=np.array([(f.mean(0)/e.mean(0)).mean() for f,e in zip(np.array_split(F,16),np.array_split(E,16))]);print('batch SE approx',targets.std(ddof=1)/4,flush=True)
sim(128,8)
sim(64,512)