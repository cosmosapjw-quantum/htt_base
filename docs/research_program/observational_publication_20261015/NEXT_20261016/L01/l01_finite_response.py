"""L01 source-locked actual Planck temperature mask operator envelope.

No optical beam, polarization high-ell mask, foreground or E2E null law inferred.
"""
from pathlib import Path
import hashlib, json
import numpy as np
SHA_T_6_16='a9aaeb393deba03c97ecf45bf4e1ab74e98e3a8747de7c4bc7a96bff27014007'
SHA_T_17_32='91f496ca7cd1cbaed65153c64d83cf7abf84b21c141d8955d0cd8e07ed480a35'
SHA_LOW='900e6c6fa04a6313f63753747d89e7059486bdeb88d51c91d895fcc8b4e09459'

def response(path_early,path_late,path_low):
  for p,digest in ((path_early,SHA_T_6_16),(path_late,SHA_T_17_32),(path_low,SHA_LOW)):
    if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=digest:raise ValueError('Planck exact source mismatch')
  with np.load(path_early,allow_pickle=False) as p:K1=p['K_ell2to5_32x253'].copy()
  with np.load(path_late,allow_pickle=False) as p:K2=p['K_ell2to5_32x800'].copy()
  with np.load(path_low,allow_pickle=False) as p:
    t=p['coeff_T'].copy();Tnames=p['names_T'].tolist();eb=p['coeff_EB'].copy();ENames=p['names_EB'].tolist()
  if K1.shape!=(32,253) or K2.shape!=(32,800) or t.shape!=(9,32) or eb.shape!=(8,64):raise ValueError('Planck source shapes changed')
  return np.column_stack([K1,K2]),t,Tnames,eb,ENames

def diagnostics(paths):
  K,t,names,eb,en=response(*paths)
  u,s,vh=np.linalg.svd(K,full_matrices=False)
  rank=int(np.sum(s>s[0]*1e-12));R=np.random.default_rng(1234).normal(size=1053);R/=np.linalg.norm(R)
  normK=float(s[0]);normF=float(np.linalg.norm(K));
  # One projection onto rowspace and residual null; constructed nonzero h in null(K)
  null=(R-vh.T@(vh@R));nullnorm=float(np.linalg.norm(null));
  if nullnorm<1e-12:raise ValueError('no finite null vector')
  residual=float(np.linalg.norm(K@(null/nullnorm)))
  if residual>1e-12:raise ValueError('high-ell null residual too large')
  # Source-only processing norms, one physical CMB sky
  return dict(schema='htt.L01_T_finite_operator_power_envelope/1',source_sha256={'early':SHA_T_6_16,'late':SHA_T_17_32,'low':SHA_LOW},
     shape=list(K.shape),rank=rank,nullity=K.shape[1]-rank,spectral_norm=normK,frobenius_norm=normF,
     singular_values=s.tolist(),example_null_high_coefficients=1053,normalized_null_residual=residual,
     norm_low_bound_per_high2_norm_1=normK,nontrivial_null_high=bool(nullnorm>0),
     temperature_one_sky_treatments=names,polarization_one_sky_treatments=en,
     source_Smicas_T_norm=float(np.linalg.norm(t[names.index('SMICA_FULL')])),
     missing_spin2_high_ell_mask='NOT_IN_SOURCE_ZIP',missing_effective_beam='NOT_ADMITTED',missing_E2E_systematics='NOT_ADMITTED',
     claim='ACTUAL_FINITE_T_HIGH_ELL_LEAKAGE_GEOMETRY_ONLY; NO_PRIMORDIAL_B_OR_ANOMALY_P')
