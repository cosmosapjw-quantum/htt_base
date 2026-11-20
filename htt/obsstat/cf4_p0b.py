"""R87 SQ-CF4 P0-B: actual CF4 method-overlap contrasts and conditional PV law.

The published table3 per-method group distance moduli are *already* jointly
intercalibrated by Cosmicflows-4. They are not independent raw calibration
observations. All returned method coefficients describe **residual source
consistency**, not a new absolute zero-point posterior, cosmic significance, or
independent calibration validation. No original source/DAG is mutated.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import hashlib
import sys

import numpy as np
from scipy.linalg import cho_factor, cho_solve

from htt.obsstat.catalogs.cf4_grouped_observations import load_grouped_observations, METHODS

ROOT=Path("docs/research_program/observational_publication_20261015")
RAW=Path("/mnt/extdrive/workdir/raw/cf4_full")
SELECT=Path("docs/research_program/cf4_schur_loop8_20261015/inputs/selected_source_observables.npz")
HASHES={
 "table3.dat":"c2351c52de3e38a7fd80256b6f0818c550dd9f105b91e84fbcc1eb7234160b4d",
 "table4.dat":"b6edfec68bdfddeada8f3b8f11938f3bbda98a8e2894ff136a369c2ad6594e94",
 "ReadMe":"2cfed1418147d5a626dee1fa37c47252124477c9828490508d9bbe511d34edb4",
 "selected":"86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c"
}
METHOD_NAMES=("SNIA","FP","TF","SBFO","SBFI","SNII")
# Published CF4 CDS Table 3 positions are 1-based inclusive.
# CAL has no published e_DMcal, and is retained for lineage but cannot enter
# inverse-variance contrast fitting without importing an unquoted error law.
FIELDS={
 "CAL":((89,90),(92,97),None),
 "SNIA":((99,99),(101,106),(108,112)),
 "FP":((114,116),(118,123),(125,129)),
 "TF":((131,132),(134,139),(141,145)),
 "SBFO":((147,149),(151,156),(158,162)),
 "SBFI":((164,164),(166,171),(173,177)),
 "SNII":(None,(179,184),(186,190))
}
C_KMS=299792.458


def sha(path):
 h=hashlib.sha256()
 with Path(path).open("rb") as f:
  for block in iter(lambda:f.read(1<<20),b""):h.update(block)
 return h.hexdigest()


@dataclass(frozen=True)
class Cf4MethodSource:
 group_id:np.ndarray
 direction:np.ndarray
 distance_modulus:np.ndarray
 distance_modulus_error:np.ndarray
 z_CMB:np.ndarray
 method_presence:np.ndarray
 method_modulus:np.ndarray
 method_sigma:np.ndarray
 CAL_modulus:np.ndarray
 selected_family:np.ndarray
 selected_family_counts:dict
 raw_method_field_role:str
 method_names:tuple=METHOD_NAMES
 source_sha256:dict|None=None
 source_array_fingerprint:dict|None=None


def _array_digest(array):
    return hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest()


def validate_source_identity(src:Cf4MethodSource):
    if not isinstance(src,Cf4MethodSource) or src.source_array_fingerprint is None:
        raise ValueError("CF4 source identity fingerprint missing")
    for key,digest in src.source_array_fingerprint.items():
        if _array_digest(getattr(src,key))!=digest:
            raise ValueError(f"CF4 original source identity fingerprint mismatch: {key}")
    if len(src.group_id)!=35970 or len(np.unique(src.group_id))!=35970:
        raise ValueError("CF4 source ID cardinality invalid")
    return True


def profile_source_method_offsets(src:Cf4MethodSource):
    validate_source_identity(src)
    return profile_method_offsets(src.method_modulus,src.method_sigma)


def _field(line,span):
 if span is None:return ""
 return line[span[0]-1:span[1]].strip()


def load_cf4_method_source(table3=RAW/"table3.dat",table4=RAW/"table4.dat",
                          readme=RAW/"ReadMe",select=SELECT):
 paths=[Path(table3),Path(table4),Path(readme),Path(select)]
 pins=[HASHES[k] for k in ("table3.dat","table4.dat","ReadMe","selected")]
 for path,digest in zip(paths,pins):
  if not path.is_file():raise FileNotFoundError(path)
  if sha(path)!=digest:raise ValueError(f"original CF4 source SHA256 drift: {path}")
 grouped=load_grouped_observations(paths[0],paths[1],paths[2])
 with np.load(paths[3],allow_pickle=False) as selected:
  ids=selected["group_id"].copy()
  n=selected["n_J2000"].copy()
  dm=selected["dmzp"].copy()
  ed=selected["e_dmzp"].copy()
  zcmb=selected["z_CMB"].copy()
  families=selected["method_family"].copy()
 if len(ids)!=35970 or not np.all(np.diff(ids)>0):raise ValueError("selected group ID ordering")
 ix=np.searchsorted(grouped.group_id,ids)
 if np.any(ix>=len(grouped.group_id)) or not np.array_equal(grouped.group_id[ix],ids):
  raise ValueError("group ID table3/table4 missing or mismatched")
 if not np.array_equal(dm,grouped.modulus[ix]) or not np.array_equal(ed,grouped.modulus_error[ix]):
  raise ValueError("reported original group modulus/error not preserved")
 if np.max(abs(n-grouped.direction[ix]))>1e-10:
  raise ValueError("original J2000 source direction mismatch")
 # Single traversal of the original fixed-width table3, no extra synthetic
 # per-method "observations" are counted as additional independent groups.
 with paths[0].open(encoding="ascii") as f:
  lines={int(row[:7]):row for row in f if row.strip()}
 if len(lines)!=38053 or set(lines)!=set(grouped.group_id):
  raise ValueError("original grouped table3 source identity mismatch")
 method_mu=np.full((len(ids),len(METHOD_NAMES)),np.nan)
 method_err=np.full_like(method_mu,np.inf)
 cal=np.full(len(ids),np.nan)
 presence=np.zeros((len(ids),7),dtype=bool)
 for row,gid in enumerate(ids):
  line=lines[int(gid)]
  for j,key in enumerate(METHODS):
   count_span,dm_span,e_span=FIELDS[key]
   raw_dm=_field(line,dm_span)
   value=float(raw_dm) if raw_dm else np.nan
   if key=="SNII":
    has=np.isfinite(value) and value>0
   else:
    raw_count=_field(line,count_span)
    c=int(raw_count) if raw_count else 0
    has=c>0
   presence[row,j]=has
   if has and not np.isfinite(value):
    raise ValueError("method present without finite released modulus")
   if key=="CAL":
    if has:cal[row]=value
    continue
   k=METHOD_NAMES.index(key)
   if has:
    raw_err=_field(line,e_span)
    error=float(raw_err) if raw_err else np.nan
    if not np.isfinite(error) or error<=0:
     raise ValueError(f"method {key} measured but error missing/nonpositive")
    method_mu[row,k]=value
    method_err[row,k]=error
 if not np.array_equal(presence,grouped.method_presence[ix]):
  raise ValueError("seven CF4 presence flags differ from original grouped loader")
 if int((presence.sum(axis=1)==0).sum())!=185:
  raise ValueError("original R80 zero-method presence count changed")
 if int((presence.sum(axis=1)>1).sum())!=926:
  raise ValueError("original R80 multi-method groups changed")
 counts={str(k):int(np.sum(families==k)) for k in np.unique(families)}
 if counts!={"FP":26916,"OTHER":740,"SN":700,"TF":7614}:
  raise ValueError("source selected method categorical grouping changed")
 fields={"group_id":ids,"direction":n,"distance_modulus":dm,
         "distance_modulus_error":ed,"z_CMB":zcmb,
         "method_presence":presence,"method_modulus":method_mu,
         "method_sigma":method_err,"CAL_modulus":cal,
         "selected_family":families}
 return Cf4MethodSource(ids,n,dm,ed,zcmb,presence,method_mu,method_err,cal,
  families,counts,
  "ALREADY_INTERCALIBRATED_GROUPED_DISTANCE_ESTIMATES_NOT_RAW_ZERO_POINTS",
  source_sha256={str(p):sha(p) for p in paths},
  source_array_fingerprint={k:_array_digest(v) for k,v in fields.items()})


def method_information(modulus,sigma):
 mu=np.asarray(modulus,dtype=np.float64)
 err=np.asarray(sigma,dtype=np.float64)
 if mu.ndim!=2 or mu.shape[1]!=6 or err.shape!=mu.shape or len(mu)<1:
  raise ValueError("method source must be same size N×6")
 if np.isnan(err).any() or (err<=0).any() or not np.all(np.isfinite(err)|np.isinf(err)):
  raise ValueError("positive finite method sigma or +inf for absent method required")
 live=np.isfinite(err)
 if (not np.isfinite(mu[live]).all()) or np.any(live & (err<=0)):
  raise ValueError("observed method modulus not finite")
 w=np.zeros_like(err)
 w[live]=err[live]**-2
 total=w.sum(axis=1)
 y=np.where(live,mu,0.)
 mean=np.divide((w*y).sum(axis=1),total,out=np.zeros(len(mu)),where=total>0)
 # Never subtract huge one-method diagonal weights from equally huge
 # projected terms. Each one-method row has ZERO actual contrast information.
 # Pairwise offdiagonal edge weights reconstruct the Laplacian exactly, keeping
 # the method-gauge null F @ ones = 0 to close-to-machine accuracy.
 inv_total=np.divide(1.,total,out=np.zeros(len(mu)),where=total>0)
 F=np.zeros((6,6))
 for i in range(6):
  for j in range(i+1,6):
   edge=float(np.sum(w[:,i]*w[:,j]*inv_total))
   F[i,j]=-edge
   F[j,i]=-edge
 for i in range(6):
  F[i,i]=-float(np.sum(F[i,:]))
 b=(w*(y-mean[:,None])).sum(axis=0)
 # Groups with one source method contribute no projected evidence.
 N=np.count_nonzero(live,axis=1)
 fnull=float(np.max(abs(F@np.ones(6))))
 return {"F":F,"fisher_full":F,"b":b,"n_distinct_supported_groups":int(np.sum(N>=2)),
  "n_single_method":int(np.sum(N==1)),"n_no_method":int(np.sum(N==0)),
  "n_multimethod_observations":int(N.sum()),
  "fisher_null_one_max":fnull,"source_method_count":int(np.count_nonzero(np.any(live,axis=0)))}


def _components_from_overlap(err):
 valid=np.isfinite(err)
 adj=np.logical_or(valid.T@valid>0,np.eye(6,dtype=bool))
 # Boolean matmul in NumPy can be used but ignore numeric counts.
 adj=np.array([[(np.any(valid[:,i]&valid[:,j])) or i==j
     for j in range(6)] for i in range(6)],bool)
 reachable={0}
 while True:
  new=reachable|{int(j) for i in reachable for j in range(6) if adj[i,j]}
  if new==reachable:break
  reachable=new
 return sorted(reachable)


def profile_method_offsets(modulus,sigma,*,ref_index=0,rank_tol=1e-10):
 if ref_index!=0:raise ValueError("registered source method gauge reference SNIA only")
 info=method_information(modulus,sigma)
 err=np.asarray(sigma,float)
 active=_components_from_overlap(err)
 retained=[k for k in active if k!=0 and np.any(np.isfinite(err[:,k]))]
 F=info["F"];b=info["b"]
 fitted=np.full(6,np.nan);fitted[0]=0.
 cov=np.full((6,6),np.nan)
 if len(retained):
  f=F[np.ix_(retained,retained)]
  ev=np.linalg.eigvalsh(f)
  if ev[0]<=0 or ev[-1]/ev[0]>1/rank_tol:
   raise ValueError("source method-overlap graph SPD/rank condition invalid")
  fac=cho_factor(f,lower=True,check_finite=False)
  x=cho_solve(fac,b[retained],check_finite=False)
  fitted[retained]=x
  cov[np.ix_(retained,retained)]=cho_solve(fac,np.eye(len(retained)),check_finite=False)
 # Gauge δ_SNIA=0 is a coordinate choice, not measured zero point.
 out=dict(info)
 out.update({"delta_mag":fitted,"cov_working_mag2":cov,
  "rank_effective":len(retained),
  "effective_methods":[METHOD_NAMES[k] for k in [0]+retained],
  "method_reference":"SNIA=0 gauge, NOT physical SNIA anchor posterior",
  "method_overlap_graph_connected":len(retained)==5,
  "physical_absolute_zero_point_posterior":None,
  "per_method_noise_independence_qualified":False,
  "global_CF4_intercalibration_upstream_leakage":True})
 return out


def _contrast_loss(modulus,sigma,delta):
 mu=np.asarray(modulus,float);err=np.asarray(sigma,float)
 allowed=np.isfinite(err)&np.isfinite(np.asarray(delta))[None,:]
 w=np.zeros_like(err)
 w[allowed]=err[allowed]**-2
 y=np.where(allowed,mu,0.)
 shift=np.where(np.isfinite(delta),delta,0.)
 y=y-shift[None,:]*allowed
 total=w.sum(axis=1)
 mean=np.divide((w*y).sum(axis=1),total,out=np.zeros(len(mu)),where=total>0)
 resid=np.where(allowed,y-mean[:,None],0.)
 n=np.count_nonzero(allowed,axis=1)
 return {"loss":float(np.sum(w*resid**2)),
   "supported_groups":int(np.sum(n>=2)),
   "estimated_contrast_degrees":int(np.sum(np.maximum(n-1,0))),
   "weight_units":"inverse_squared_magnitudes; NOT a calibrated chi-square law"}


def spatial_group_heldout(source:Cf4MethodSource):
 validate_source_identity(source)
 n=source.direction
 ra=(np.arctan2(n[:,1],n[:,0])%(2*np.pi))
 skybin=np.minimum((ra/(np.pi/2)).astype(np.int8),3)
 if not np.all(np.bincount(skybin,minlength=4)>100):
  raise ValueError("original sky quadrants not populated")
 rows=[]
 for fold in range(4):
  test=(skybin==fold);train=~test
  assert not np.intersect1d(source.group_id[test],source.group_id[train]).size
  estimate=profile_method_offsets(source.method_modulus[train],
                                  source.method_sigma[train])
  data=source.method_modulus[test];sigma=source.method_sigma[test]
  predicted=_contrast_loss(data,sigma,estimate["delta_mag"])
  zero=_contrast_loss(data,sigma,np.zeros(6))
  rows.append({
    "fold":int(fold),"J2000_RA_sector_deg":[90*fold,90*(fold+1)],
    "train_groups":int(train.sum()),"test_groups":int(test.sum()),
    "unique_group_ID_train_vs_test_overlap":0,
    "method_network_rank_in_training":estimate["rank_effective"],
    "finite_working_loss":bool(np.isfinite(predicted["loss"])),
    "heldout_precalibrated_group_contrast_loss":predicted["loss"],
    "heldout_no_extra_offset_loss":zero["loss"],
    "heldout_predictive_loss_difference":predicted["loss"]-zero["loss"],
    "heldout_groups_with_at_least_two_usable_methods":predicted["supported_groups"],
    "heldout_contrast_degrees":predicted["estimated_contrast_degrees"],
    "training_fitted_delta_mag":estimate["delta_mag"].tolist(),
    "this_is_not_a_new_raw_method_calibration":True
  })
 return {
  "schema":"htt.r87.source_precalibrated_method_residual_spatial_CV/1",
  "folds":rows,
  "group_ID_partition":"Exact one original 1PGC group per fold, four fixed equatorial RA quadrants; no ID modulo resampling",
  "independent_upstream_zero_point_calibration":False,
  "qualified_selection_PV_coverage":False,
  "physical_calibration_p_value":None,
  "test_type":"source_product_spatial_predictive_consistency_only_not_independent_precalibration_or_cosmological_CV"}


def pv_sensitivity_scenario(source:Cf4MethodSource,*,bulk_sigma_kms=150.,
                            shear_sigma_kms_per_mpc=1.5):
 validate_source_identity(source)
 if bulk_sigma_kms<0 or shear_sigma_kms_per_mpc<0 or (
     bulk_sigma_kms==0 and shear_sigma_kms_per_mpc==0):
  raise ValueError("source PV scenario nonnegative prior scales, one positive")
 from htt.obsstat.pv_covariance import velocity_field_modes,woodbury_solve
 # Keep original optical apparent H03 parametrization. It is a source-selected
 # forward fitting basis, not a physically qualified Sachs/Jacobi normal map.
 sys.path.insert(0,str((ROOT/"H03_20261016/src").resolve()))
 import h03_tomography as H
 d=10.**((source.distance_modulus-25)/5)
 X=H.velocity_design(d,source.direction)
 y=C_KMS*source.z_CMB
 diag=(70*np.log(10)/5*d*source.distance_modulus_error)**2 +250.**2
 assert np.all(diag>0)
 mode=velocity_field_modes(d[:,None]*source.direction,
            sigma_bulk_kms=bulk_sigma_kms,
            sigma_shear_kms_per_mpc=shear_sigma_kms_per_mpc)
 valid=mode["Lambda"]>0
 U=mode["U"][:,valid]
 lam=mode["Lambda"][valid]
 # A low-rank source mode exactly contained in the mean-design X (e.g. STF
 # velocity shear) only inflates the conditional coefficient covariance.
 # A constant peculiar bulk velocity has n_i response, whereas this H03
 # apparent Hubble-dipole has d_i*n_i: they are NOT the same data column at
 # varying distance. Therefore bulk can move the conditional point estimate.
 projected=np.linalg.lstsq(X,U,rcond=None)[0]
 column_residual=np.linalg.norm(U-X@projected,axis=0)/np.linalg.norm(U,axis=0)
 DinvX=X/diag[:,None];DinvY=y/diag
 F0=X.T@DinvX;b0=X.T@DinvY
 CinvX=woodbury_solve(diag,U,lam,X)
 CinvY=woodbury_solve(diag,U,lam,y)
 F=X.T@CinvX;b=X.T@CinvY
 F=(F+F.T)/2
 cf=cho_factor(F,lower=True,check_finite=False)
 fitted=cho_solve(cf,b)
 cf0=cho_factor((F0+F0.T)/2,lower=True,check_finite=False)
 fitted0=cho_solve(cf0,b0)
 cov=cho_solve(cf,np.eye(9))
 cov0=cho_solve(cf0,np.eye(9))
 if not np.isfinite(cov).all() or np.linalg.eigvalsh(cov)[0]<=0:
  raise ValueError("PV sensitivity working covariance not SPD")
 # Exact identified-model theorem if all coherent U columns are already in X:
 # unchanged GLS mean, coefficient covariance plus A Lambda A^T.
 in_mean_span=bool(np.max(column_residual)<1e-12)
 predicted_cov=(cov0 + (projected*lam[None,:])@projected.T
                if in_mean_span else None)
 theorem_error=(float(np.linalg.norm(cov-predicted_cov)/np.linalg.norm(predicted_cov))
                if predicted_cov is not None else None)
 return {
   "source_N":int(len(X)),"F_conditioned":F,"F_diagonal":F0,
   "source_assumed_low_rank_modes":int(U.shape[1]),
   "source_modes_distance_to_H03_mean_span_relative":column_residual.tolist(),
   "source_modes_fully_in_mean_span":in_mean_span,
   "source_span_theorem_covariance_relative_error":theorem_error,
   "conditional_bulk_shift_vs_depth_dependent_dipole":"PV v_r=n.B while H03 apparent expansion dipole is d*n.D, distinct columns for nonconstant d",
   "working_gls_beta_with_assumed_PV":fitted,
   "working_gls_beta_only_diagonal":fitted0,
   "working_gls_beta_max_abs_difference":float(np.max(abs(fitted-fitted0))),
   "covariance_trace_ratio":float(np.trace(cov)/np.trace(cov0)),
   "conditional_sigma_bulk_kms":float(bulk_sigma_kms),
   "conditional_sigma_shear_kms_per_mpc":float(shear_sigma_kms_per_mpc),
   "source_matched_PV_field_ensemble_qualified":False,
   "source_selection_C_qualified":False,
   "observed_normal_shear":None,"physical_Pi":None,
   "conditional_source_note":"Low-rank bulk/shear scenario reused from pv_covariance; source-selected field ensemble, full nonlinear PV and selection law are not qualified"}


def p0b_claim_gate(source:Cf4MethodSource):
 validate_source_identity(source)
 return {"P0_B_physics_status":"BLOCKED_PHYSICAL_PV_CALIBRATION_SELECTION_AND_HELDOUT",
  "source_valid_raw_method_DM":bool(len(source.group_id)==35970),
  "actual_full_C_qualified":False,
  "actual_spatial_calibration_heldout_qualified":False,
  "physical_p_value":None,
  "source_zero_point_uncertainty":"NOT_IN_RELEASED_TABLE3_POST_INTERCALIBRATED_PRODUCTS",
  "physical_S_PV_source_ensemble":None,"physical_C_selection":None}
