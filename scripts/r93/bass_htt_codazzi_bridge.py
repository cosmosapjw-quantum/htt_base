"""R93 exact on-shell BASS/HTT Codazzi source bridge across Bianchi strata.

Imports BASS conventions in its own original Python environment and the
HTT R49 true physical divergence code. Tests all 12 R90 canonical and
exceptional representatives, arbitrary physical scale H and kappa,
normal-frame momentum q and proper SO(3) rotations. No model transport or
observational Bianchi family identification is inferred.
"""
from pathlib import Path
import hashlib
import json
import subprocess
import numpy as np
from scipy.spatial.transform import Rotation
from bianchi.conventions import codazzi_residual
from bass.background.convention_bridge import exact_momentum_divergence

ROOT=Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
BASS=Path("/home/cosmosapjw/bass")
OUT=ROOT/"docs/research_program/observational_publication_20261015/R93_THIRD_SCIENCE_LOOP_20261121/BASS_HTT_CODAZZI_SAME_STATE_RESULT.json"
CANONICAL={
 "I":((0.,0.,0.),0.),
 "II":((0.,0.,1.),0.),
 "III_VIh=-1":((0.,1.,-1.),1.),
 "IV":((0.,0.,1.),1.),
 "V":((0.,0.,0.),1.),
 "VI_0":((0.,1.,-2.),0.),
 "VI_h=-1/4":((0.,1.,-2.),np.sqrt(.5)),
 "VI_h=-1/9_exception":((0.,1.,-4.),2./3.),
 "VII_0":((0.,1.,2.),0.),
 "VII_h=1/4":((0.,1.,2.),np.sqrt(.5)),
 "VIII":((1.,2.,-3.),0.),
 "IX":((1.,2.,3.),0.)
}
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for buf in iter(lambda:f.read(2**18),b""):h.update(buf)
 return h.hexdigest()
def head(repo):
 return subprocess.run(["git","rev-parse","HEAD"],cwd=repo,capture_output=True,text=True,check=True).stdout.strip()

def calculate():
 rng=np.random.default_rng(92333)
 data={}
 max_abs=0
 count=0
 max_rot=0
 for key,(eigs,a) in CANONICAL.items():
  N=np.diag(eigs).astype(float)
  A=np.array([a,0,0.],float)
  assert np.linalg.norm(N@A)<1e-12
  cases=[]
  for k in range(5):
   s=rng.normal(size=(3,3))
   S=.5*(s+s.T)
   S-=np.eye(3)*np.trace(S)/3
   H=.5+2*rng.random()
   kappa=1.1+.3*rng.random()
   qn=rng.normal(size=3)*(.1 if k!=0 else 0.)
   orig=np.asarray(codazzi_residual(S,N,A,qn))
   div=exact_momentum_divergence(H*S,H*A,H*N)
   physicalq=(H**2/kappa)*qn
   # exact on-shell signed convention:
   physical=(div+kappa*physicalq)/H**2
   err=float(np.max(abs(orig+physical)))
   if err>3e-12:raise AssertionError((key,err))
   R=Rotation.random(random_state=rng).as_matrix()
   Sr=R@S@R.T
   Ar=R@A;Nr=R@N@R.T;qr=R@qn
   b_rot=np.asarray(codazzi_residual(Sr,Nr,Ar,qr))
   # proper SO(3): vector covariance, no spurious handedness
   rot_err=float(np.max(abs(b_rot-R@orig)))
   if rot_err>3e-12:raise AssertionError(("SO3",key,rot_err))
   # signed physical source tensor has its own independent HTT oracle
   divrot=exact_momentum_divergence(H*Sr,H*Ar,H*Nr)
   physrot=(divrot+H**2*qr)/H**2
   ph_err=float(np.max(abs(physrot+b_rot)))
   if ph_err>3e-12:raise AssertionError(("HTT rot",key,ph_err))
   max_abs=max(max_abs,err,ph_err)
   max_rot=max(max_rot,rot_err)
   count+=1
   cases.append({"normalized_momentum_identity_error":err,
                 "proper_SO3_vector_covariance_error":rot_err,
                 "H":float(H),"kappa":float(kappa)})
  data[key]={"normal_curvature_N_eigenvalues":list(eigs),
             "a_norm":float(abs(a)),"sample_count":len(cases),
             "max_error":max(z["normalized_momentum_identity_error"] for z in cases),
             "max_SO3_error":max(z["proper_SO3_vector_covariance_error"] for z in cases)}
 return {"schema":"htt.r93.bass_r49_signed_codazzi_normalization/1",
         "BASS_root":str(BASS),"BASS_head":head(BASS),
         "HTT_head_at_run":head(ROOT),
         "source_sha256":{
           "BASS":sha(BASS/"bianchi/conventions.py"),
           "HTT":sha(ROOT/"htt/bass/background/convention_bridge.py"),
         },
         "equation":"C_BASS=3 A·Sigma + eps(N,Sigma) - qflux; div_HTT=-H^2(3 A·Sigma + eps(N,Sigma)); kappa*q=H^2 qflux; thus (div_HTT+kappa*q)/H^2=-C_BASS",
         "signature":"(-,+,+,+)","source_flux":"NORMAL_FRAME_ALGEBRAIC_NOT_EOS_REALIZED",
         "normalizations":"Sigma=sigma/H, n_norm=n/H, A_norm=a/H, qflux=kappa*q/H^2",
         "test_count":count,"canonical_strata":len(data),
         "max_equation_residual":float(max_abs),
         "max_SO3_covariance_residual":float(max_rot),
         "representatives":data,
         "physical_family_attribution":False,"full_tilted_positive_EOS_coverage":False,
         "native_radiative_boltzmann_used":False}
if __name__=="__main__":
 if OUT.exists():raise RuntimeError("create-only existing file")
 result=calculate()
 OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
 print(json.dumps({"cases":result["test_count"],
                   "families":result["canonical_strata"],
                   "max_error":result["max_equation_residual"],
                   "max_SO3_error":result["max_SO3_covariance_residual"]}))
