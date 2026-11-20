"""C7 real-source conditional PHY 01..07 evidence, immutable anchors E0/E1.

Reproduces actual source-geometry/working-covariance claims, not a cosmological
same-frame joint likelihood, photon normal flux, physical shear or native solver.
"""
import hashlib,json,platform,sys
from pathlib import Path

import numpy as np
from scipy.special import roots_legendre
from astropy.coordinates import SkyCoord
from astropy import units as u
from scripts.r68.fiveview_geometry import stf_matrix
from scripts.r81.bench_baseline import axes
from htt.obsstat.pre_dag_fast import codazzi_map, radial_design
from htt.obsstat import phy_fast as fast

P=Path("docs/research_program/observational_publication_20261015")
SELECTED=Path("docs/research_program/cf4_schur_loop8_20261015/inputs/selected_source_observables.npz")
TABLE4=Path("/mnt/extdrive/workdir/raw/cf4_full/table4.dat")
R80=P/"R80_SQ_CF4_SOURCE_BINDING_20261120/RESULT.json"
R77=P/"R77_SEVEN_PHY_CROSSVIEW_20261119/RESULTS.json"
R76=P/"R76_P6_COVARIANT_DRIFT_FIVEVIEW_20261119/RESULTS.json"
R69=P/"R69_PHYSICAL_OBSERVABLE_BRIDGES_20261118/RESULTS/GAIA_E1B1E2B2.json"
R66=P/"R66_LOWELL_PHYSICAL_OBSERVABLES_20261117/RESULTS/OBSERVABLES.json"
OUT=P/"R81_PRE_DAG_NODES11_20_20261120/C7_PHYSICAL_SOURCE_REPLAY.json"

def digest(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for z in iter(lambda:f.read(1<<20),b""):h.update(z)
 return h.hexdigest()

def load_selected():
 with np.load(SELECTED,allow_pickle=False) as z:
  return (z["group_id"].copy(),z["n_J2000"].copy(),z["e_dmzp"].copy())
def cf4_source():
 ids,n,e=load_selected()
 assert len(ids)==35970
 lines={int(x[:7]):x for x in TABLE4.read_text().splitlines() if x.strip()}
 assert len(lines)==38053
 rr=np.array([float(lines[int(g)][21:26]) for g in ids])
 assert np.all(rr>0)
 return ids,n,e,rr

def sky_quadrature():
 mu,wt=roots_legendre(100);phi=np.arange(200)*np.pi/100
 mm,pp=np.meshgrid(mu,phi,indexing="ij")
 n=np.column_stack([np.sqrt(1-mm.ravel()**2)*np.cos(pp.ravel()),
                    np.sqrt(1-mm.ravel()**2)*np.sin(pp.ravel()),mm.ravel()])
 weights=np.repeat(wt/(2*200),200)
 return n,weights

def main():
 source=json.loads(R80.read_text())
 previous=json.loads(R77.read_text())["results"]
 ids,n,e,r=cf4_source()
 weights=1/(e*e)
 A=axes(96)
 mask=fast.multi_axis_hemisphere(n,A,weights=weights)
 receipt=fast.last_phy_receipt()
 assert receipt["used"]=="fortran_batch" and receipt["source_certified"]
 assert mask["weights"].shape==(96,2)
 assert np.all(mask["counts"]>0)
 # True selected-source mask leakage: conditional model amplitude s=.03.
 dif=mask["second"][:,1,:,:]-mask["second"][:,0,:,:]
 eig=np.linalg.eigvalsh(dif)
 leakage=.03*(eig[:,2]-eig[:,0])
 assert np.all(np.isfinite(leakage))
 # Prior R80 only for the same CMB axis and same unweighted subset.
 cmb=SkyCoord(l=264.021*u.deg,b=48.253*u.deg,frame="galactic").icrs
 p=np.array([np.cos(cmb.dec.rad)*np.cos(cmb.ra.rad),np.cos(cmb.dec.rad)*np.sin(cmb.ra.rad),np.sin(cmb.dec.rad)])
 sel=(r>=40)&(r<400)
 only=fast.multi_axis_hemisphere(n[sel],p[None,:],native_lib=None)
 m2=only["second"][0,1]-only["second"][0,0]
 ev=np.linalg.eigvalsh(m2)
 cmp=.03*(ev[-1]-ev[0])
 ref=source["angular_mask_diagnostics"]["selected_40_400"]["sharp_even_shear_to_hemispherical_mean_bound"]
 assert abs(cmp-ref)<5e-14,(cmp,ref)
 phy01={"n_source":len(n),"n_40_400":int(sel.sum()),
        "n_mask_axes":len(A),"weighted_source_A96_sharp_minmax":[float(leakage.min()),float(leakage.max())],
        "original_R80_unweighted_CMB_axis_sharp":cmp,
        "R80_unweighted_replay_error":abs(cmp-ref),
        "Fortran_backend_receipt":receipt,"source_covariance_PV_selection":"UNAVAILABLE"}
 # Photon pressure actual PR3/PR4, no f.
 r66=json.loads(R66.read_text())
 phy02={}
 M=codazzi_map(np.array([1.,0.,0.]),np.diag([0.,3.,-3.]))
 for release in ("PR3","PR4"):
  s=stf_matrix(r66["nonlinear"][release]["radiation_moment_bundle"]["pi5_over_rho"])
  x=fast.photon_codazzi_feasibility(s,np.zeros(5),LieM=M,Omega=.3,eta=.2)
  assert x["photon_flux_missing"] and x["physical_Pi"] is None
  eig_expected=previous["PHY-02"]["R66_same_sky_finiteband_photon_pressure"][release]["P_eigenvalues"]
  np.testing.assert_allclose(x["P_eigen"],eig_expected,atol=2e-15,rtol=2e-15)
  phy02[release]={"actual_R66_P_min_eigen":min(x["P_eigen"]),"photon_flux_source":"UNAVAILABLE"}
 # Synthetic shared-beta closure only.
 beta=np.array([369.82/299792.458,0.,0.])
 ans=fast.shared_beta_radio_photon(beta,k=previous["PHY-03"]["radio_first_order_k"],kappa=0.)
 np.testing.assert_allclose(ans["count_STF"],ans["ratio"]*ans["photon_STF"],atol=2e-19)
 phy03={"synthetic_assumed_common_beta":beta.tolist(),"source_k":previous["PHY-03"]["radio_first_order_k"],
        "photon_chi":ans["photon_chi"],
        "physical_common_rest_frame":"NOT_ESTABLISHED",
        "R66_signed_chi_PR3":previous["PHY-03"]["actual_R66_finiteband_stress"]["PR3"]["R66_signed_chi_finiteband"]}
 # Normal Lie B2 ideal full sphere and actual Gaia source Fisher alias.
 sky,wts=sky_quadrature()
 Nb=np.diag([.013,-.017,.004]); S=np.diag([-.02,0.,.02])
 E2,B2=fast.local_E2_and_Lie_B2(sky,S,Nb)
 norm=float(wts@np.sum(B2*B2,axis=1))
 dot=float(wts@np.einsum("ni,ni->n",E2,B2))
 target=float(np.trace(Nb@Nb)/5)
 assert abs(norm-target)<2e-15 and abs(dot)<2e-15
 gaia=json.loads(R69.read_text())
 r76=json.loads(R76.read_text())["R69_Gaia_VSH_actual_source"]["results"]
 cases={}
 for maskkey in ("quality","quality_north","quality_south"):
  C=np.array(gaia["results"][maskkey]["formal_cov_microasyr2"])
  x=fast.gaia_eb_mask_alias(C)
  ref=r76[maskkey]["E2_B2_profiled_design_maxcanonical"]
  assert abs(x["maxcanonical"]-ref)<3e-12
  cases[maskkey]={"maxcanonical":x["maxcanonical"],"source_working_fisher_not_coupling":True}
 phy04={"normal_Lie_B2_spherical_norm":norm,"exact_STF_prediction":target,
        "E2_B2_full_sky_cross":dot,"gaia_masked_design":cases,
        "physical_Gaia_transfer":"UNAVAILABLE"}
 # Independent physical same-frame flux missing, synthetic C as direct test.
 M=codazzi_map(np.array([1.,0.,0]),np.diag([0.,3.,-3.]))
 assert np.linalg.matrix_rank(M)==2
 x5=np.array([-.2,.1,.03,.04,.02]);u_vec=np.array([.01,0.,-.01]);C8=np.diag([.04**2]*5+[.03**2]*3)
 r5=fast.normal_flux_residual(x5,u_vec,M,Omega=.4,C_joint=C8,independent_source=False)
 assert r5["physical_Pi"] is None and r5["rank_covariance"]==3
 phy05={"Lie_rank":2,"independent_measurement_residual_cov_rank":r5["rank_covariance"],
        "actual_independent_normal_flux":"UNAVAILABLE"}
 # Noncommuting shear eigenframe and higher angular moments.
 D=np.zeros((3,3));D[0,1]=D[1,0]=.01
 sh=fast.shear_shape_rate(np.diag([-.03,-.01,.04]),D,H=.1)
 assert abs(sh["dchi"])<3e-12 and sh["commutator_norm"]>0
 p0=fast.photon_l4_family(0.,threshold=.9,shear_s=.07)
 p1=fast.photon_l4_family(1.,threshold=.9,shear_s=.07)
 assert abs(p1["cap_F"]-p0["cap_F"]-.05707125)<1e-11
 phy06={"chi_time_derivative_exact":sh["dchi"],
        "noncommutator_norm":sh["commutator_norm"],
        "same_first_two_photon_moments_but_cap_F":[p0["cap_F"],p1["cap_F"]],
        "photon_actual_time_GF":"UNAVAILABLE"}
 # Actual CF4 12D spatial and radial source information (diagonal weights are
 # NOT actual correlated PV or zero-point source covariance).
 X=radial_design(r,n)
 synthetic_y=np.log10(r)-np.mean(np.log10(r))
 G,b,c=fast.weighted_radial_stats(X,weights,synthetic_y,native_lib=None)
 assert np.linalg.matrix_rank(X)==12
 assert np.linalg.eigvalsh(G)[0]>0
 source_single=radial_design(np.full_like(r,150.),n)
 assert np.linalg.matrix_rank(source_single)==9
 phy07={"n_selected":len(n),"radial12_design_rank":12,
        "fixed_distance_design_rank":9,"weighted_Gram_condition":float(np.linalg.cond(G)),
        "working_weight_source":"marginal e_dmzp^-2; correlated PV/calibration/selection C still missing",
        "response":"synthetic detrended log r; NOT new cosmological fit"}
 # Original science E0/E1 remains frozen.
 old=fast.historical_common_anchors()
 assert old["E0"]["state"]=="completed_scoped" and old["E1"]["state"]=="completed_scoped"
 phy19_20={"E0":{"state":old["E0"]["state"],"source_evidence":old["E0"]["existing_evidence"]},
           "E1":{"state":old["E1"]["state"],"source_evidence":old["E1"]["existing_evidence"]},
           "R78_science_sha":old["R78_science_nodes_42_sha"],
           "unchanged":True}
 manifest={
  "schema":"htt.r81.c7_original_source_phy_math_preflight/1",
  "input_sha256":{str(q):digest(q) for q in (SELECTED,TABLE4,R77,R80,R76,R69,R66)},
  "scientific_status":"SOURCE_CONDITIONAL_GEOMETRY_AND_TENSOR_MATH_NUMERICALLY_CHECKED",
  "nodes":{"11_SQ_NATIVE":{"input_status":"EXTERNAL_NATIVE_TRANSFER_NOT_SUPPLIED_NO_SOLVER_CREATED"},
      "12_PHY01":phy01,"13_PHY02":phy02,"14_PHY03":phy03,"15_PHY04":phy04,
      "16_PHY05":phy05,"17_PHY06":phy06,"18_PHY07":phy07,
      "19_20_original_E0_E1":phy19_20},
  "software":{"python":sys.version.split()[0],"numpy":np.__version__,"platform":platform.platform()},
  "no_R78_state_mutation":True,
  "no_cosmological_joint_source_likelihood":True
 }
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps({"selected_n":len(n),"axes":len(A),
   "leakage_range":phy01["weighted_source_A96_sharp_minmax"],
   "R80_error":phy01["R80_unweighted_replay_error"],
   "E2_B2_ideal_cross":dot,"Gaia_quality_design_alias":cases["quality"]["maxcanonical"],
   "radial_cond":phy07["weighted_Gram_condition"]},ensure_ascii=False))
if __name__=="__main__":
 main()
