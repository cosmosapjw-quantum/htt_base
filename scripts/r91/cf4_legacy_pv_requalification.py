"""R91: requalify EXISTING R36 CF4 low-k Fourier Gaussian PV factors against R90.

This is a real measured 35,970 source-operator conditional covariance under
an Eisenstein-Hu 1998 no-wiggle, finite-band source model. It is NOT a full
source-matched physical CF4 posterior, selection law or upstream MCMC
calibration. Read-only heavy factor files and frozen R36 results; no rerun.
"""
from __future__ import annotations
import hashlib,json
from pathlib import Path
import numpy as np
from scipy.linalg import cho_factor,cho_solve

ROOT=Path(__file__).resolve().parents[2]
DOC=ROOT/"docs/research_program/observational_publication_20261015"
R36=DOC/"OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-02-CF4-CORRELATED"
SOURCE=Path("/mnt/extdrive/workdir/htt_open_data/r36_cf4_correlated_actual")
R27=Path("/mnt/extdrive/workdir/htt_open_data/r27_cf4_exact_calibration_factor_numeric/actual_run/products")
R89=DOC/"R89_EIGHT_ANALYSIS_HANDOFF_20261121/runs/G02_CF4/SOLVER_FREE_RESEARCH_RESULT.json"
R89DEEP=DOC/"R89_EIGHT_ANALYSIS_HANDOFF_20261121/runs/G02_CF4/DEEP_MULTISURVEY_RESULT.json"

def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for buf in iter(lambda:f.read(2**20),b""):h.update(buf)
 return h.hexdigest()

def analyze(full_factor=True)->dict:
 pstat=json.loads((R36/"PUBLICATION_STATUS.json").read_text())
 old=json.loads((R36/"RESULT.json").read_text())
 if pstat["status"]!="FORMALLY_QUALIFIED_SCOPED_CONDITIONAL_PRODUCT":
  raise RuntimeError("R36 historical conditional evidence not qualified")
 if old["source_rows"]!=35970 or old["source_sha256"]!="86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c":
  raise RuntimeError("R36 selected source not same as R90")
 with np.load(SOURCE/"RESULT_MATRICES.npz",allow_pickle=False) as f:
  pv=np.asarray(f["pv_total"],float)
  total=np.asarray(f["conditional_R5"],float)
  baseline=np.asarray(f["baseline"],float)
  theta=np.asarray(f["theta"],float)
  method_K=np.asarray(f["method_K"],float)
  method_Sigma=np.asarray(f["method_Sigma"],float)
 with np.load(SOURCE/"STAGE_C.npz",allow_pickle=False) as f:
  band1=np.asarray(f["band1"],float)
  band2=np.asarray(f["band2"],float)
  stage=np.asarray(f["total"],float)
 with np.load(R27/"FACTOR.npz",allow_pickle=False) as f:
  groupids=np.asarray(f["group_id"],int)
  L=np.asarray(f["L_binary64"],float)
  cn=f["channel_names"].tolist()
  selected=f["selected_support_7"]
 if len(groupids)!=35970 or len(np.unique(groupids))!=35970:
  raise RuntimeError("R27 exact source supports not same universe")
 if L.shape!=(5,35019) or selected.shape!=(35970,7):
  raise RuntimeError("R27 calibration source transfer shape drift")
 if pv.shape!=(108,108) or total.shape!=(36,36):
  raise RuntimeError("R36 covariance expected 108x108 full, 36x36 R5")
 # exact original 36 observed coefficient cross-check
 r89=json.loads(R89.read_text())
 deep=json.loads(R89DEEP.read_text())
 t89=np.asarray(r89["part_a_cf4_flow_and_partial_id"]["joint_36d_raw_vs_flow"]["raw_theta_4x9"]).ravel()
 tdeep=np.asarray(deep["des_dovekie_5yr"]["fits_mag"]["valid_sky_all_z_9p_stat_sys"]["dipole_vec"])
 parity=np.max(abs(t89-theta))
 # The R36 total intentionally doesn't include inherited working baseline.
 assert np.linalg.norm(total-baseline[:36,:36])>1e-6
 sym=max(np.max(abs(a-a.T)) for a in (pv,total,band1,band2))
 eig_pv=np.linalg.eigvalsh(pv)
 eig_tot=np.linalg.eigvalsh(total)
 eig_cond=np.linalg.eigvalsh(pv[:36,:36])
 if eig_pv.min()<-1e-7 or eig_tot.min()<=0:
  raise RuntimeError("invalid PSD expected source covariance")
 trace_R5=float(np.trace(pv[:36,:36]))
 offdiag=pv[:36,:36].copy()
 for j in range(4):offdiag[9*j:9*(j+1),9*j:9*(j+1)]=0.
 cross_norm=float(np.linalg.norm(offdiag))
 diagonal_norm=float(np.linalg.norm(np.diag(np.diag(pv[:36,:36]))))
 # mean chi2 for shared nine-parameter Gaussian mean, source-conditioned
 design=np.tile(np.eye(9),(4,1))
 cc=cho_factor(total,lower=True,check_finite=False)
 cf=cho_solve(cc,design,check_finite=False)
 beta=np.linalg.solve(design.T@cf,design.T@cho_solve(cc,theta,check_finite=False))
 residual=theta-design@beta
 chi=float(residual@cho_solve(cc,residual,check_finite=False))
 factor_recon={}
 if full_factor:
  with np.load(SOURCE/"PV_FACTORS.npz",allow_pickle=False) as f:
   U1=np.asarray(f["band1"],float)
   U2=np.asarray(f["band2"],float)
  if U1.shape!=U2.shape or U1.shape[0]!=108:
   raise RuntimeError("R36 Fourier factor dimensions unexpected")
  for title,U,C in (("band1_R5",U1[:36],band1[:36,:36]),("band2_R5",U2[:36],band2[:36,:36])):
   grams=U@U.T
   diff=float(np.linalg.norm(grams-C)/np.linalg.norm(C))
   if diff>5e-8:raise RuntimeError("full R36 Fourier Gram failure: "+title)
   factor_recon[title]={"relative_frobenius_error":diff,"number_k_angular_modes":U.shape[1]}
 result={
 "schema":"htt.r91.cf4_existing_physical_pv_conditional_requalification/1",
 "historical_R36_product_status":pstat["status"],
 "historical_R36_scope":"VALIDATED_FINITE_GAUSSIAN_PV_SUBBANDS_NOT_ACTUAL_CF4_EMPIRICAL_COVERAGE",
 "sources":{"R36_result_sha256":sha(R36/"RESULT.json"),"R36_status_sha256":sha(R36/"PUBLICATION_STATUS.json"),
            "R36_matrix_sha256":sha(SOURCE/"RESULT_MATRICES.npz"),
            "R36_factors_sha256":sha(SOURCE/"PV_FACTORS.npz"),
            "R27_factor_sha256":sha(R27/"FACTOR.npz"),
            "R89_G02_sha256":sha(R89),"R89_DEEP_sha256":sha(R89DEEP)},
 "n_same_CF4_selected_groups":len(groupids),
 "PV_modes":{"k_h_per_Mpc":[0.005,0.05],"k_split":0.02,
             "four_H03_windows_times_nine_moments":36,
             "R_hinv_Mpc":[5,10,20],
             "pv_source_all_radii_shape":list(pv.shape),
             "R5_PV_trace_units_km_s_Mpc_squared":trace_R5,
             "R5_PV_min_eigen":float(eig_cond.min()),
             "all_radii_min_eigen":float(eig_pv.min()),
             "full_four_window_cross_block_frob_norm":cross_norm,
             "diagonal_frob_norm_R5":diagonal_norm,
             "cross_over_diagonal_frob_norm":cross_norm/diagonal_norm,
             "PV_factor_checks":factor_recon,
             "R36_C_total_R5_min_eigen":float(eig_tot.min()),
             "R36_C_total_R5_trace":float(np.trace(total)),
             "R36_original_working_trace":float(np.trace(baseline)),
             "uncertainty_model":"EH98 Gaussian k in 0.005..0.05 h/Mpc plus stipulated independent noise and mean-design calibration; omitted k, source response, calibration prior unresolved"},
 "R89_H03_raw_theta_max_abs_diff":float(parity),
 "R36_refitted_shared_nine_chi2":chi,
 "R36_historical_shared_nine_chi2":float(old["mean_comparison"]["observed_chi2"]["shared_nine_coordinate_mean"]),
 "R27_source_conditional_calibration_factor":{"channels":cn,"n_group_ids":len(groupids),
              "support_7_count":int(selected.sum()),"factor_rows":int(L.shape[1]),
              "identified":"fixed seven-channel source quotient additive calibration only, NOT upstream MCMC"},
 "physics_scope":{"partial_S_PV":"KNOWN_CONDITIONAL_SOURCE_MODELED",
                  "full_S_PV":"BLOCKED_OUTSIDE_BANDS_AND_NONLINEAR",
                  "upstream_JcalSigmaJ":"NOT_IDENTIFIED_FROM_POST_MCMC_MODULI",
                  "C_selection":"NOT_CALIBRATED",
                  "true_CF4_heldout":"NOT_AVAILABLE",
                  "original_SQ_CF4":"BLOCKED_INPUT"},
 }
 if parity>5e-9 or abs(chi-result["R36_historical_shared_nine_chi2"])>1e-6:
  raise RuntimeError("R36/R89 finite numerical identity diverged")
 return result
