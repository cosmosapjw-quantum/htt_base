"""R94 exact closed-form quadrupolar Gaunt and optional C++17/OpenMP kernel.

Purpose: replace SymPy/Wigner3j per-coefficient calls and Python loops in R93.
Mathematical equivalence only to R93's declared L=2, ell -> ell+2
modulation statistic. The speed-up does NOT qualify cosmic anisotropy or
Bianchi family attribution; mask/beam/source covariance remain external.

G_{ell m,ell+2,m-M} = (-1)^M sqrt(5(2ell+1)(2ell+5)/(4pi))
  *[24/(product_{k=1}^5(2ell+k))]
  *((ell+1)(ell+2)/2)
  *sqrt( product_{k=1}^{2-M}(ell+m+k)
        product_{k=1}^{2+M}(ell-m+k) /[(2+M)!(2-M)!]).
Derived from unique Racah term j1+j2=j3, valid M=-2...+2.
"""
from __future__ import annotations
import ctypes
import hashlib
import math
import os
from dataclasses import dataclass
from pathlib import Path
import subprocess
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
CPP=Path(__file__).with_name("gaunt_core.cpp")
BIN=Path.home()/"Downloads/htt_r94_native_cache"
L2_BANDS=((2,8),(9,16),(17,32),(33,46))

def sha(p:Path)->str:
 h=hashlib.sha256()
 with p.open("rb") as f:
  for blk in iter(lambda:f.read(1<<20),b""): h.update(blk)
 return h.hexdigest()

def gaunt_l2_stepup(l:int,m:int,M:int)->float:
 if l<0 or abs(m)>l or abs(M)>2:
  raise ValueError("invalid ell,m,M")
 denom=1
 for k in range(1,6):denom*=2*l+k
 a=1
 for k in range(1,3-M):a*=l+m+k
 b=1
 for k in range(1,3+M):b*=l-m+k
 ratio=(a*b)/(math.factorial(2+M)*math.factorial(2-M))
 pref=math.sqrt(5.*(2*l+1)*(2*l+5)/(4*math.pi))
 return ((-1)**M)*pref*(24./denom)*(l+1)*(l+2)/2.*math.sqrt(ratio)

def alm_index(lmax:int,l:int,m:int)->int:
 # HEALPix RING triangular index, identical hp.Alm.getidx
 if l<0 or l>lmax or abs(m)>l:raise ValueError("invalid ALM coordinate")
 a=abs(m)
 return a*(2*lmax+1-a)//2 + l

@dataclass(frozen=True)
class Terms:
 band:tuple[int,int]
 M:int
 idx_a:np.ndarray
 idx_b:np.ndarray
 code_a:np.ndarray
 code_b:np.ndarray
 weight:np.ndarray
 norm:float
 def nterm(self)->int:return len(self.weight)

def build_terms(cl:np.ndarray,lmax:int,bands=L2_BANDS,ms=(0,1,2))->dict[tuple[int,int],Terms]:
 cl=np.asarray(cl,dtype=np.float64)
 if lmax<4 or len(cl)<lmax+1:raise ValueError("bad lmax or C_l")
 out={}
 for bi,band in enumerate(bands):
  low,high=band
  if low<2 or high+2>lmax:raise ValueError("ell+2 exceeds lmax")
  for M in ms:
   ia,ib,ca,cb,w=[],[],[],[],[]
   gn=0.
   for l in range(low,high+1):
    den=cl[l]+cl[l+2]
    if not np.isfinite(den) or den<=0:raise ValueError("C_l normalization is not positive")
    for m in range(-l,l+1):
     mp=m-M
     if abs(mp)>l+2:continue
     G=gaunt_l2_stepup(l,m,M)
     if abs(G)<1e-14:continue
     ia.append(alm_index(lmax,l,m))
     ib.append(alm_index(lmax,l+2,mp))
     ca.append(0 if m>=0 else (-1 if (-m)%2 else 1))
     cb.append(0 if mp>=0 else (-1 if (-mp)%2 else 1))
     w.append(G/den)
     gn+=G*G
   if not w or gn<=0:raise RuntimeError("no Gaunt weight")
   out[bi,M]=Terms(band,M,np.ascontiguousarray(ia,np.int32),
      np.ascontiguousarray(ib,np.int32),np.ascontiguousarray(ca,np.int8),
      np.ascontiguousarray(cb,np.int8),np.ascontiguousarray(w,np.float64),float(gn))
 return out

def _native_so(compile_if_needed=True):
 digest=sha(CPP)[:20]
 so=BIN/("gaunt_"+digest+".so")
 if not so.exists():
  if not compile_if_needed:raise FileNotFoundError(so)
  BIN.mkdir(parents=True,exist_ok=True)
  cmd=["g++","-O3","-fPIC","-shared","-std=c++17","-fopenmp","-ffp-contract=off",
       str(CPP),"-o",str(so.with_suffix(".partial"))]
  p=subprocess.run(cmd,capture_output=True,text=True,check=False,timeout=50)
  if p.returncode:
   if so.with_suffix(".partial").exists():so.with_suffix(".partial").unlink()
   raise RuntimeError("native gaunt C++ compile failed: "+p.stderr[-1100:])
  os.replace(so.with_suffix(".partial"),so)
 lib=ctypes.CDLL(str(so))
 func=lib.htt_r94_gaunt_project
 P=ctypes.c_void_p
 I=ctypes.c_int64
 func.argtypes=[P,I,I,I,P,P,P,P,P,ctypes.c_double,P]
 func.restype=ctypes.c_int
 return func,so

def _apply_codes(z,c):
 return np.where(c[None,:]!=0,np.conj(z),z)*np.where(c[None,:]==-1,-1.,1.)

def project(alm,terms,backend="numpy",chunk_terms=512):
 a=np.ascontiguousarray(alm,dtype=np.complex128)
 if a.ndim==1:a=a[None,:]
 if a.ndim!=2:raise ValueError("ALM must be 1D or 2D")
 n,nalm=a.shape
 out=np.zeros((n,len({k[0] for k in terms}),5),dtype=np.float64)
 func=None
 if backend=="native":func,_=_native_so()
 elif backend!="numpy":raise ValueError("backend must be numpy or native")
 for (bi,M),t in sorted(terms.items()):
  if t.idx_a.max()>=nalm or t.idx_b.max()>=nalm:raise ValueError("ALM lmax insufficient")
  if backend=="native":
   tmp=np.empty((n,2),dtype=np.float64)
   err=func(ctypes.c_void_p(a.ctypes.data),n,nalm,t.nterm(),
       ctypes.c_void_p(t.idx_a.ctypes.data),ctypes.c_void_p(t.idx_b.ctypes.data),
       ctypes.c_void_p(t.code_a.ctypes.data),ctypes.c_void_p(t.code_b.ctypes.data),
       ctypes.c_void_p(t.weight.ctypes.data),t.norm,ctypes.c_void_p(tmp.ctypes.data))
   if err:raise RuntimeError(f"native kernel returned error {err}")
   z=tmp[:,0]+1j*tmp[:,1]
  else:
   z=np.zeros(n,dtype=np.complex128)
   for beg in range(0,t.nterm(),chunk_terms):
    sl=slice(beg,min(beg+chunk_terms,t.nterm()))
    x=_apply_codes(a[:,t.idx_a[sl]],t.code_a[sl])
    y=_apply_codes(a[:,t.idx_b[sl]],t.code_b[sl])
    z += np.sum(x*np.conj(y)*t.weight[None,sl],axis=1)
   z /= t.norm
  if M==0:
   out[:,bi,0]=z.real
   if np.max(abs(z.imag))>1e-7*max(1.,float(np.max(abs(z.real)))):
    raise RuntimeError("Gaunt M=0 violates reality")
  elif M==1:
   out[:,bi,1:3]=np.sqrt(2)*np.stack([z.real,z.imag],axis=1)
  elif M==2:
   out[:,bi,3:5]=np.sqrt(2)*np.stack([z.real,z.imag],axis=1)
 return out

def loo_diagonal_fast(x,obs):
 """O(Nd) exact leave-one-out mean & unbiased variance, replacing np.delete loop."""
 x=np.asarray(x,dtype=np.float64)
 obs=np.asarray(obs,dtype=np.float64)
 if x.ndim!=2 or len(x)<4 or obs.shape!=(x.shape[1],):raise ValueError("bad shapes")
 n=len(x)
 # Stable centered moment algebra, avoids loss of significance in E[x²]-E[x]².
 mu=x.mean(axis=0)
 delta=x-mu
 sse=np.sum(delta*delta,axis=0)
 var=sse/(n-1)
 if np.any(var<=1e-18):raise ValueError("bad variance")
 qobs=float(np.sum((obs-mu)**2/var))
 mean_minus=mu[None,:]-delta/(n-1)
 # Deleting observation i removes n/(n-1)*(x_i - mean)² from total SSE.
 var_minus=(sse[None,:]-(n/(n-1))*delta*delta)/(n-2)
 if np.any(var_minus<=1e-18):raise ValueError("bad LOO variance")
 loo=np.sum((x-mean_minus)**2/var_minus,axis=1)
 tail=int(np.count_nonzero(loo>=qobs))
 return {"observed_score":qobs,"MC_N":n,"null_tail_count":tail,"rank_p":(tail+1)/(n+1),
         "MC_median_score":float(np.median(loo)),
         "MC_p95_score":float(np.quantile(loo,.95)),
         "mean_all":mu,"std_all":np.sqrt(var),
         "test":"same source-conditional R93 statistic, algebraically exact O(Nd) LOO"}
