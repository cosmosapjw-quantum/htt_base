"""R96 CF4 legacy-R36 covariance + R27 7-channel source reconciliation.

Exact linear-Gaussian conditional model. Uses all 35,970 CF4 selected source
groups, 4 weighted H03 windows x 9 coefficients; real physical low-k R36 PV,
R27 finite additive method support and legacy R36 4-method covariance.

C_A = C_PV + C_H03_noise + sigma^2 J7 J7^T   [new CONDITIONAL model]
C_B = C_PV + K4 Sigma4 K4^T + R36_resid      [inherited R36 model]

These have different working-noise/calibration provenance; MUST NOT be
added as independent covariances. Low-rank Cholesky Woodbury is checked
against direct dense GLS and against R95 stored numbers.

No pre-intercalibration MCMC posterior, selection covariance or independent
heldout is invented or reconstructed.
"""
from pathlib import Path
import json,hashlib,math,time,importlib.util
import numpy as np
from scipy.linalg import cho_factor, cho_solve
from scripts.r95 import sq_cf4_synthesis as r95

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"docs/research_program/observational_publication_20261015/R96_THREE_THEORY_LOOPS_20261122/CF4_COVARIANCE_RECONCILIATION.json"
R36=Path("/mnt/extdrive/workdir/htt_open_data/r36_cf4_correlated_actual/RESULT_MATRICES.npz")
R27=Path("/mnt/extdrive/workdir/htt_open_data/r27_cf4_exact_calibration_factor_numeric/actual_run/products/FACTOR.npz")
R95=ROOT/"docs/research_program/observational_publication_20261015/R95_LOCAL_EXECUTION_20261122/G02_SQ_CF4_SYNTHESIS.json"
SIGMA_CAL=(0.,.02,.05,.1,.2)
PV_RADIUS=(5,10,20)
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(2**20),b""):h.update(b)
 return h.hexdigest()

def woodbury_gls(C0,U,D,y):
 """C=C0+U U^T; profiled GLS theta, covariance, chi2, without C inverse."""
 C0=np.asarray(C0,float);U=np.asarray(U,float)
 cc=cho_factor(C0,lower=True,check_finite=False)
 m=U.shape[1]
 CinvD=cho_solve(cc,D,check_finite=False)
 Cinvy=cho_solve(cc,y,check_finite=False)
 if m:
  V=cho_solve(cc,U,check_finite=False)
  kk=cho_factor(np.eye(m)+U.T@V,lower=True,check_finite=False)
  CinvD-=V@cho_solve(kk,U.T@CinvD,check_finite=False)
  Cinvy-=V@cho_solve(kk,U.T@Cinvy,check_finite=False)
 fisher=D.T@CinvD
 cf=cho_factor(.5*(fisher+fisher.T),lower=True,check_finite=False)
 cov=cho_solve(cf,np.eye(D.shape[1]),check_finite=False)
 beta=cho_solve(cf,D.T@Cinvy,check_finite=False)
 res=y-D@beta
 cinv_res=cho_solve(cc,res,check_finite=False)
 if m:cinv_res-=V@cho_solve(kk,U.T@cinv_res,check_finite=False)
 chi=float(res@cinv_res)
 return beta,cov,chi

def compute():
 t0=time.perf_counter()
 H=r95._load_h03()
 inp=H.source(r95.SELECT)
 assert len(inp.z)==35970
 dist=H.proxy_distance(inp.mu)
 sig=H.working_sigma(dist,inp.e_mu)
 X=H.velocity_design(dist,inp.n)
 theta=np.empty(36)
 influence=[]
 for j,zc in enumerate(H.CENTERS):
  w=H.window(inp.z,sig,zc)
  result=H.fit(X,H.C_KM_S*inp.z,w,influence=True)
  influence.append(result["A"])
  theta[j*9:(j+1)*9]=result["theta"]
 A=np.vstack(influence)
 Cnoise,_=H.joint_covariance(A,sig)
 with np.load(R27,allow_pickle=False) as f:
  ids=f["group_id"]; S7=np.asarray(f["selected_support_7"],float)
  assert np.array_equal(ids,inp.ids)
 assert S7.shape==(35970,7)
 dcz_dmu=-(math.log(10.)/5.)*70.*dist
 J=A@(S7*dcz_dmu[:,None])
 Jbulk=A@inp.n
 with np.load(R36,allow_pickle=False) as f:
  PVall=f["pv_total"];C_r36=f["conditional_R5"];theta_R36=f["theta"]
  K=f["method_K"];Sigma4=f["method_Sigma"]
  baseline=f["baseline"]
 residual=C_r36-PVall[:36,:36]-K@Sigma4@K.T
 delta=C_r36-(PVall[:36,:36]+Cnoise)
 ev_delta=np.linalg.eigvalsh((delta+delta.T)/2)
 ev_res=np.linalg.eigvalsh((residual+residual.T)/2)
 if not ev_res.min()>0:raise RuntimeError("R36 remainder not PSD")
 if np.max(abs(theta-theta_R36))>1e-10:raise RuntimeError("H03 source theta parity drift")
 D=np.tile(np.eye(9),(4,1))
 target=json.loads(R95.read_text())["joint_pv_plus_calibration_grid"]
 rows={}
 max_parity=0.
 for radius,jj in zip(PV_RADIUS,range(3)):
  c0=PVall[jj*36:(jj+1)*36,jj*36:(jj+1)*36]+Cnoise
  assert np.linalg.eigvalsh(c0).min()>0
  row={}
  for scal in SIGMA_CAL:
   U=J*scal
   beta,cov,chi=woodbury_gls(c0,U,D,theta)
   full=c0+U@U.T
   ck=cho_factor(full,lower=True,check_finite=False)
   CiD=cho_solve(ck,D,check_finite=False)
   beta_d=np.linalg.solve(D.T@CiD,D.T@cho_solve(ck,theta,check_finite=False))
   err=float(np.max(abs(beta-beta_d)))
   if err>2e-8:raise RuntimeError("Woodbury-dense mismatch")
   expected=target[f"R{radius}"][f"sig_cal_{scal:.2f}"]
   parity=abs(beta[0]-expected["H0_est"])
   max_parity=max(max_parity,parity)
   if parity>2e-7:raise RuntimeError(f"R95 source/method parity drift {radius} {scal}")
   row[f"{scal:.2f}"]={"H0":float(beta[0]),"H0_sd":float(np.sqrt(cov[0,0])),
            "dipole_amp":float(np.linalg.norm(beta[1:4])),"chi2_27dof":chi,
            "dense_gls_max_abs_beta_diff":err}
  rows[f"R{radius}"]=row
 # historical inherited model is NOT equal to any new R95 model.
 b_old,c_old,chi_old=woodbury_gls(C_r36,np.zeros((36,0)),D,theta)
 return {
  "schema":"htt.r96.R36_R27_CF4_two_non_equivalent_covariance_models/1",
  "source_id":{"selected_35970":sha(r95.SELECT),"r36":sha(R36),
               "r27":sha(R27),"r95":sha(R95)},
  "N_group":int(len(inp.z)),"H03_nwindows":4,"H03_ncoeff":9,
  "math":"d=X beta + Jcal delta + Jbulk b + eta; Cnew=CPV + CH03noise + Jcal Sigma Jcal^T",
  "model_A_R95_lowrank_grid":rows,
  "model_B_inherited_R36":{"legacy_conditional_R5_source_sha":sha(R36),
        "H0":float(b_old[0]),"sd":float(np.sqrt(c_old[0,0])),
        "chi2":chi_old,"method_K_shape":list(K.shape),
        "method_Sigma_trace":float(np.trace(Sigma4)),
        "positive_remainder_min_eigen":float(ev_res.min()),
        "positive_remainder_trace":float(np.trace(residual))},
  "cross_model_difference":{
      "max_abs_R36_conditional_vs_PV_plus_actual_H03noise":float(np.max(abs(delta))),
      "difference_eigen_min":float(ev_delta.min()),
      "difference_eigen_max":float(ev_delta.max()),
      "difference_is_psd":bool(ev_delta.min()>=-1e-11),
      "interpretation":"R36 legacy method-four plus low-rank and positive working residual differs from R95 independently constructed noise+seven-method model; cannot concatenate or identify upstream posterior"},
  "J_cal_36x7_rank":int(np.linalg.matrix_rank(J)),
  "J_bulk_36x3_rank":int(np.linalg.matrix_rank(Jbulk)),
  "source_support_overlap_groups":int(np.count_nonzero(S7.sum(axis=1)>1)),
  "theta_R36_max_abs_diff":float(np.max(abs(theta-theta_R36))),
  "max_H0_R95_parity":max_parity,
  "publication_ready":False,"full_S_PV_and_calibration":None,
  "epistemic_status":"derived linear Gaussian covariance identity and numerically checked actual CF4 35,970 source; physical zero point MCMC prior, selection and heldout unresolved",
  "elapsed_s":time.perf_counter()-t0,
 }
def main():
 if OUT.exists():raise FileExistsError("create-only result")
 j=compute()
 OUT.write_text(json.dumps(j,indent=2,ensure_ascii=False)+"\n")
 print(json.dumps({"n":j["N_group"],"R36_R95_max_difference":j["cross_model_difference"],
       "model_A_R5_H0":j["model_A_R95_lowrank_grid"]["R5"],
       "legacy":j["model_B_inherited_R36"],"J_rank":j["J_cal_36x7_rank"]}))
if __name__=="__main__":main()
