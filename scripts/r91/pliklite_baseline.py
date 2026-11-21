"""R91 solver-free baseline likelihood from already present official Plik-lite v22.

Reuses Planck 2018 native Plik-lite dataset files and the published Planck
best-fit theory D_ell spectrum. Precisely reproduces the Cobaya/Planck
PlanckPlikLite class equations, with no external Boltzmann run, no full
PR4 downloads and no Bianchi family identification. Read-only input files.
"""
from __future__ import annotations
import hashlib, json, math
from pathlib import Path
import numpy as np
from scipy.io import FortranFile
from scipy.linalg import cho_factor, cho_solve

DATA=Path("/mnt/extdrive/workdir/cobaya_packages/data/planck_2018_pliklite_native")
THEORY=Path("/mnt/extdrive/workdir/raw/planck_data/COM_PowerSpect_CMB-base-plikHM-TTTEEE-lowl-lowE-lensing-minimum-theory_R3.01.txt")
FILE_NAMES=["plik_lite_v22.dataset","blmin.dat","blmax.dat","bweight.dat","cl_cmb_plik_v22.dat","c_matrix_plik_v22.dat"]

def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1<<20),b""):h.update(b)
 return h.hexdigest()

def compute(A_planck:float=1.0)->dict:
 if not 0.9<=A_planck<=1.1:raise ValueError("unreasonable uncalibrated A_planck")
 metadata=(DATA/"plik_lite_v22.dataset").read_text()
 if not all(token in metadata for token in ("nbintt=215","nbinte=199","nbinee=199","lmax=2508","bin_lmin_offset = 30","use_cl = TT TE EE")):
  raise RuntimeError("likelihood data source/header mismatch")
 bins=(215,199,199)
 bounds0=np.loadtxt(DATA/"blmin.dat").astype(int)+30
 bounds1=np.loadtxt(DATA/"blmax.dat").astype(int)+30
 weights=np.loadtxt(DATA/"bweight.dat")
 ell=np.arange(len(weights))+30
 weights=weights*2*np.pi/(ell*(ell+1))
 obs=np.loadtxt(DATA/"cl_cmb_plik_v22.dat")
 with FortranFile(DATA/"c_matrix_plik_v22.dat","r") as f:
  covariance=f.read_reals(dtype=np.float64).reshape(613,613)
 # Cobaya PlanckPlikLite Fortran lower triangular becomes symmetric.
 covariance=np.tril(covariance)+np.tril(covariance,-1).T
 spectrum=np.loadtxt(THEORY)
 if spectrum.shape[0]!=2507 or not (spectrum[0,0]==2 and spectrum[-1,0]==2508):
  raise RuntimeError("Planck best fit D_l source shape drift")
 cl_by_kind={"tt":spectrum[:,1],"te":spectrum[:,2],"ee":spectrum[:,3]}
 spectrum_start=2
 kinds=("tt","te","ee")
 modeled=[]; ranges=[]; bykind={}
 offset=0
 for label,nbin in zip(kinds,bins):
  x=cl_by_kind[label]
  vals=[]
  for j in range(nbin):
   lo,hi=int(bounds0[j]),int(bounds1[j])
   if lo<spectrum_start or hi>2508:
    raise RuntimeError("observed Planck bandpower out of bounds")
   vals.append(float(np.dot(x[lo-spectrum_start:hi+1-spectrum_start],weights[lo-30:hi+1-30])))
  vals=np.asarray(vals)
  ranges.append((offset,offset+nbin))
  modeled.extend(vals.tolist())
  bykind[label]={"n_bins":nbin,"ell_min":int(bounds0[0]),"ell_max":int(bounds1[nbin-1]),
                 "max_bin_width":int(np.max(bounds1[:nbin]-bounds0[:nbin]+1))}
  offset+=nbin
 predicted=np.asarray(modeled,dtype=float)/A_planck**2
 y=obs[:,1]-predicted
 if covariance.shape!=(613,613):
  raise RuntimeError("invalid Pliklite covariance")
 L=cho_factor(covariance,lower=True,check_finite=False)
 z=cho_solve(L,y,check_finite=False)
 chi2=float(y@z)
 if not np.isfinite(chi2) or chi2<=0:
  raise RuntimeError("invalid Pliklite chi2")
 # Dataset bins tt,te,ee share covariance. These below are *marginal* contributions
 # y_g C_gg^-1 y_g, not sum-to-full conditional contributions.
 for (start,end),label in zip(ranges,kinds):
  cg=covariance[start:end,start:end]
  yg=y[start:end]
  bykind[label]["marginal_block_chi2"]=float(yg@cho_solve(cho_factor(cg,lower=True,check_finite=False),yg))
 bykind["total"]={"chi2":chi2,"n_bins":len(y)}
 # Conditional analytic calibration-profile check with a fixed published
 # background theory: u=1/A_planck**2, d≈u*t. This profiles ONE scalar only.
 t=np.asarray(modeled,dtype=float)
 d=np.asarray(obs[:,1],dtype=float)
 Pt=cho_solve(L,t,check_finite=False)
 Pd=cho_solve(L,d,check_finite=False)
 Fu=float(t@Pt)
 score=float(t@Pd)
 uhat=score/Fu
 if uhat<=0:raise RuntimeError("non-positive conditional Planck calibration")
 ahat=float(uhat**(-.5))
 chi2_profile=float(d@Pd-score**2/Fu)
 chi2_opt_direct=float((d-uhat*t)@cho_solve(L,d-uhat*t,check_finite=False))
 if abs(chi2_opt_direct-chi2_profile)>1e-7:raise RuntimeError("likelihood calibration quadratic identity failed")
 chi2_A1=float((d-t)@cho_solve(L,d-t,check_finite=False))
 bykind["conditional_fixed_theory_calibration_profile"]={
     "u_equals_A_inverse2_MLE":float(uhat),
     "A_planck_MLE":ahat,
     "sigma_u_fixed_theory":float(Fu**(-.5)),
     "sigma_A_delta_method":float(.5*ahat*Fu**(-.5)/uhat),
     "chi2_profile_min":chi2_profile,
     "chi2_improvement_A1_to_MLE":chi2_A1-chi2_profile,
     "interpretation":"fixed published CMB background, Plik-lite likelihood only; not physical Bianchi evidence"
 }
 return {
  "schema":"htt.r91.native_pliklite_fixed_theory_baseline/1",
  "official_likelihood":"Planck 2018 nuisance-marginalized Plik-lite v22, source Cobaya class planck_pliklite.py",
  "published_bestfit_theory":"Planck R3.01 CMB base plikHM+lowE+lensing minimum theory D_l file",
  "links":["https://github.com/CobayaSampler/planck_native_data",
           "https://github.com/CobayaSampler/cobaya",
           "https://github.com/benabed/clik"],
  "file_sha256":{x:sha(DATA/x) for x in FILE_NAMES},
  "theory_file_sha256":sha(THEORY),
  "input_types":{"theory":"D_l=l(l+1) C_l/(2pi) in microK^2",
                "likelihood_data":"C_l, not D_l, in microK^2",
                "covariance":"Fortran record binary lower triangular 613x613",
                "calibration_param":"A_planck, divides predicted C_l by A_planck^2"},
  "A_planck":A_planck,
  "bands":bykind,
  "log_likelihood_up_to_constant":float(-0.5*chi2),
  "cmb_morphology_information":"ABSENT_C_ELL_MARGINAL_ONLY",
  "source_null_qualified":"NO_FOR_BIANCHI_ATTRIBUTION",
  "CAMB_boltzmann_executed":False,
  "clik_executable_loaded":False,
  "claim":"Observed high-l power baseline only; not Planck low-l morphology likelihood",
 }
