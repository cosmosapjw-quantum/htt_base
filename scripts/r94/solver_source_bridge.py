"""R94 reuse of REAL preexisting source operators:
  REC Bianchi-I positive proper clock (1024-cell verified source),
  REI Thomson constants / source-history difference envelope,
  BASS exact basis-free rank-nine scattering,
  HTT R49 Class A/B all-12 Bianchi exact-geodesic polarized screen.

This is a *physically typed solver bridge* with explicitly constructed
radiation source and assumed electron-density history, not native all-m
Einstein-Boltzmann reconstruction or released cosmological source evidence.
The original repos and installed native runtimes are never modified.

The program may be run with HTT .venv Python and:
 PYTHONPATH=.:htt:htt/src:/home/cosmosapjw/Dropbox/bianchi/rec_bianchi/src
"""
from __future__ import annotations
import hashlib
import importlib.util
import json
import math
from pathlib import Path
from time import perf_counter

import numpy as np
from scipy.integrate import quad

from bass.background.convention_bridge import ALL_TWELVE_FAMILIES
from bass.background.general_tilted_evolution import (
 _build_default_admissible_state_for_family,
 evolve_general_tilted_bianchi,
 TiltedEvolutionConfig,
)
from bass.transport.general_bianchi_transfer import (
    TiltedTransferParameters,compute_general_bianchi_transfer,
    TRANSFER_MODE_GEODESIC,TRANSFER_MODE_LINEARIZED,gl_sphere_grid,
    FAMILY_TRANSFER_METADATA,
)
from full_bianchi_hyrec.background.axisymmetric_bianchi_i import AxisymmetricBianchiIBackground

HTT=Path(__file__).resolve().parents[2]
BASS=Path("/home/cosmosapjw/bass")
REC=Path("/home/cosmosapjw/Dropbox/bianchi/rec_bianchi")
REI=Path("/home/cosmosapjw/Dropbox/bianchi/rei_bianchi")
ROOT_OUT=HTT/"docs/research_program/observational_publication_20261015/R94_SIX_PAPER_ACCEL_HANDOFF_20261122"
BASS_POL=BASS/"bianchi/q/polarization.py"
HTT_TRANSFER=HTT/"htt/bass/transport/general_bianchi_transfer.py"
REC_SRC=REC/"src/full_bianchi_hyrec/background/axisymmetric_bianchi_i.py"
REI_SOURCE=REI/"research/flrw_pair_observable_20261016/results/THOMSON_PAIR_RESULT.json"
SIGNATURE="(-,+,+,+)"
N_E0_CM3=2.0e-7 # explicitly CONSTRUCTED, not inferred from REI result

def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(2**18),b""):h.update(b)
 return h.hexdigest()

def load_basis_free_polarization():
 spec=importlib.util.spec_from_file_location("r94_bass_q_polarization_readonly",BASS_POL)
 mod=importlib.util.module_from_spec(spec)
 spec.loader.exec_module(mod)
 return mod

def conditional_optical_depth(q_ref=0.,a_start=1/21.,a_end=.2,x_e=1.):
 # Reuse the accepted REC positive finite physical clock; flat positive
 # electron fraction is a constructed control, not a real REI ionization model.
 if not (0<=x_e<=1):raise ValueError("electron fraction outside [0,1]")
 bg=AxisymmetricBianchiIBackground(q_ref=q_ref,cells=1024)
 point0=bg.point(a_start)
 point1=bg.point(a_end)
 interval=bg.interval(a_start,a_end)
 constants=json.loads(REI_SOURCE.read_text())["constants"]
 c=float(constants["c_cm_per_s"])
 sigma_t=float(constants["sigma_T_cm2"])
 if not (c>0 and sigma_t>0):raise RuntimeError("non-positive Thomson constants")
 def opacity_integrand(loga):
  a=math.exp(loga)
  # dt = d ln(a)/H(a); physical n_e(a)=n_e0*a^-3*x_e.
  return c*sigma_t*N_E0_CM3*x_e*a**(-3)/bg.point(a).H_s_inv
 val,err=quad(opacity_integrand,math.log(a_start),math.log(a_end),
              epsabs=5e-12,epsrel=1e-9,limit=160)
 if val<0 or not math.isfinite(val):
  raise RuntimeError("physical optical depth integration not positive")
 return {"q_ref":q_ref,"a_interval":[a_start,a_end],"z_interval":[1/a_start-1,1/a_end-1],
         "delta_t_s":interval.delta_t_s,"delta_b":interval.delta_b,
         "tau_with_fixed_xe":float(val),"quad_abs_err_estimate":float(err),
         "electron_density0_cm-3_ASSUMED":N_E0_CM3,"electron_fraction_ASSUMED":x_e,
         "rec_method":interval.method_identity,"rec_source_sha":bg.source_sha256,
         "rei_constant_sha":sha(REI_SOURCE),"units":{"c":"cm/s","sigma_T":"cm2",
                  "n_e":"cm-3","H":"s-1","tau":"dimensionless"},
         "REI_electron_history_qualified":False,
         "physical_Bianchi_ionization_accepted":False}

def thomson_source(optical_depth:float,pol,n_theta=14):
 th,ph,d,w=gl_sphere_grid(n_theta)
 direction=d.reshape(-1,3)
 weights=w.reshape(-1)
 # Source: real parity-even STF quadrupole with a fixed offdiagonal entry.
 S=np.array([[.70,.18,0.],[.18,-.35,.08],[0.,.08,-.35]],float)
 S-=np.eye(3)*np.trace(S)/3
 angular=1+.08*np.einsum("ni,ij,nj->n",direction,S,direction)
 J=pol.unpolarized(direction,angular)
 before=float(np.dot(weights,pol.intensity(J)))
 Jout=pol.collide(direction,weights,J,float(optical_depth))
 after=float(np.dot(weights,pol.intensity(Jout)))
 if abs(before-after)/before>3e-12:
  raise RuntimeError("BASS exact Thomson energy normalization failed")
 leak=pol.screen_leak(direction,Jout)
 if leak>1e-11:raise RuntimeError("BASS photon polarization lost screen")
 eig=np.linalg.eigvalsh(Jout)
 if eig.min()<-2e-12:raise RuntimeError("unphysical negative polarized eigenvalue")
 intensity=pol.intensity(Jout)
 E=np.einsum("n,n,ni,nj->ij",weights,intensity,direction,direction)/after
 pi=E-np.eye(3)/3.
 if abs(np.trace(pi))>2e-13:raise RuntimeError("emission PSTF source not tracefree")
 return {
  "source_quad":pi,"tau":float(optical_depth),
  "massless_photon_source_model":"constructed anisotropic unpolarized I(n)=1+0.08 n_i S_ij n_j",
  "input_energy":before,"output_energy":after,
  "fractional_energy_error":abs(after-before)/before,
  "screen_leak":leak,"lowest_polarized_J_eigenvalue":float(eig.min()),
  "source_pi_frobenius":float(np.linalg.norm(pi)),
  "stokes_basis_note":"BASS unpolarized J, exact rank-9 collision; pi is *intensity quadrupole normal moment*, conditional interpretation when supplied to HTT",
 }

def dynamic_einstein_euler_transfer(pi_emit):
 """Run the actual R49 Einstein-Euler background coupled to exact geodesics.

 Uses admissible two-fluid initial conditions from R49 (photon/cdm EOS),
 fixed N=0..0.5, and constructed electron-radiation pi_emit from BASS.
 Not an observational full photon Boltzmann hierarchy or physical CMB null.
 """
 result={}
 for fam in ALL_TWELVE_FAMILIES:
  t=perf_counter()
  st=_build_default_admissible_state_for_family(fam)
  traj=evolve_general_tilted_bianchi(
   st,eos_by_species={"photon":1./3.,"cdm":0.},
   config=TiltedEvolutionConfig(
    N_start=0.,N_end=.5,n_eval=17,method="DOP853",
    rtol=1e-9,atol=1e-11))
  if (traj.max_jacobi_residual>1e-9 or
      traj.max_hamiltonian_residual_rel>1e-8 or
      traj.max_codazzi_residual_rel>1e-8 or
      traj.max_speed_over_trajectory>=1.):
   raise RuntimeError("R49 Einstein-Euler source constraints failed for "+fam)
  params=TiltedTransferParameters(
   family=fam,trajectory=traj,pi_gamma_emit=pi_emit,
   sigma_N=traj.sigma_ab_grid[-1]/traj.H_grid[-1],
   ell_max=6,n_gl_theta=14,transfer_mode=TRANSFER_MODE_GEODESIC,
   n_geodesic_steps=32)
  out=compute_general_bianchi_transfer(params)
  if out.max_screen_ortho_err>1e-8 or out.max_null_err>1e-8:
   raise RuntimeError("R49 geodesic screen invalid for "+fam)
  result[fam]={
   "class":traj.class_label,
   "two_fluid_eos":{"photon":1./3.,"cdm":0.},
   "N_span":[0.,.5],"N_eval":17,
   "max_jacobi":float(traj.max_jacobi_residual),
   "max_hamiltonian":float(traj.max_hamiltonian_residual_rel),
   "max_codazzi":float(traj.max_codazzi_residual_rel),
   "max_shear_trace_error":float(traj.max_shear_trace_error),
   "max_speed":float(traj.max_speed_over_trajectory),
   "final_H":float(traj.H_grid[-1]),
   "TT_ell2":float(out.cl_TT[2]),
   "EE_ell2":float(out.cl_EE[2]),
   "BB_ell2":float(out.cl_BB[2]),
   "max_null_err":float(out.max_null_err),
   "max_screen_ortho_err":float(out.max_screen_ortho_err),
   "runtime_s":round(perf_counter()-t,5),
   "source_claim":"physical Einstein-Euler two-fluid on R49 chosen initial state, *constructed* emission pi; neither Planck-likelihood nor free high-ell photon hierarchy"}
 return result


def compute():
 start=perf_counter()
 pol=load_basis_free_polarization()
 ion0=conditional_optical_depth(q_ref=0.0)
 ion1=conditional_optical_depth(q_ref=1e-6)
 src=thomson_source(ion1["tau_with_fixed_xe"],pol,n_theta=14)
 # For family-geodesic mode, geometrical shear is a CONSTRUCTED
 # constant normal-frame STF; no postulated beta_H or physical source H(z).
 sig=np.diag([0.002,-0.001,-0.001])
 fam_data={}
 for fam in ALL_TWELVE_FAMILIES:
  t=perf_counter()
  is_curved=fam not in {"FLRW","I","VII_0"}
  params=TiltedTransferParameters(family=fam,sigma_N=sig,
     pi_gamma_emit=src["source_quad"],omega_k=.02 if is_curved else 0.,
     ell_max=8,n_gl_theta=14,n_efolds_star=-.7,
     n_geodesic_steps=32,transfer_mode=TRANSFER_MODE_GEODESIC)
  q=compute_general_bianchi_transfer(params)
  if q.max_null_err>1e-8 or q.max_screen_ortho_err>1e-8:
   raise RuntimeError("geodesic physical state invalid: "+fam)
  fam_data[fam]={"family_class":FAMILY_TRANSFER_METADATA[fam].bianchi_class,
     "equivalence_class":q.equivalence_class,
     "TT_l2":float(q.cl_TT[2]),"EE_l2":float(q.cl_EE[2]),
     "BB_l2":float(q.cl_BB[2]),"TE_l2":float(q.cl_TE[2]),
     "max_BB":float(np.max(q.cl_BB[2:])),
     "max_null_err":float(q.max_null_err),
     "max_screen_ortho_err":float(q.max_screen_ortho_err),
     "rms_screen_twist":float(q.rms_delta_psi),
     "claim_tier":q.claim_tier,
     "source_provenance":q.channel_breakdown["response_provenance"],
     "elapsed_s":round(perf_counter()-t,5)}
 linear={}
 for fam in ALL_TWELVE_FAMILIES:
  if not FAMILY_TRANSFER_METADATA[fam].flrw_limit_admissible:
   linear[fam]={"status":"OUT_OF_SCOPE_NO_NEAR_FLRW_LIMIT"}
   continue
  p=TiltedTransferParameters(family=fam,sigma_N=sig,
     pi_gamma_emit=src["source_quad"],
     omega_k=.02 if fam not in {"FLRW","I","VII_0"} else 0.,
     ell_max=8,n_gl_theta=14,transfer_mode=TRANSFER_MODE_LINEARIZED)
  q=compute_general_bianchi_transfer(p)
  linear[fam]={"status":"SOURCE_CONDITIONAL_LINEARIZED_EXECUTED",
               "cl_TT_l2":float(q.cl_TT[2]),"cl_EE_l2":float(q.cl_EE[2]),
               "cl_BB_l2":float(q.cl_BB[2]),"claim_tier":q.claim_tier}
 convergence={}
 # Finite L only, not a true physical high-ell hierarchy.
 for fam in ("I","V","VII_h","IX"):
  arr=[]
  for L,nth in [(8,14),(16,20),(24,28)]:
   p=TiltedTransferParameters(family=fam,sigma_N=sig,
      pi_gamma_emit=src["source_quad"],
      omega_k=.02 if fam not in {"I","VII_0"} else 0.,
      ell_max=L,n_gl_theta=nth,n_geodesic_steps=32,
      n_efolds_star=-.7,transfer_mode=TRANSFER_MODE_GEODESIC)
   x=compute_general_bianchi_transfer(p)
   arr.append({"lmax":L,"n_gl_theta":nth,"l2_TT":float(x.cl_TT[2]),
               "l2_EE":float(x.cl_EE[2]),"l2_BB":float(x.cl_BB[2]),
               "max_null_error":x.max_null_err})
  convergence[fam]=arr
 dynamic=dynamic_einstein_euler_transfer(src["source_quad"])
 rei_bound=json.loads(REI_SOURCE.read_text())["optical_depth_envelope"]["q"]
 pi_plus=thomson_source(ion1["tau_with_fixed_xe"]+rei_bound,pol,n_theta=14)["source_quad"]
 pi_minus=thomson_source(max(0.,ion1["tau_with_fixed_xe"]-rei_bound),pol,n_theta=14)["source_quad"]
 bounded_pi=float(np.linalg.norm(pi_plus-pi_minus))
 # Source-local rule: this only solves deterministic directional geodesic
 # and constructed source radiative screening, not true CMB E/B high-ell.
 return {"schema":"htt.r94.rec_rei_bass_htt_conditional_polarized_transfer_bridge/1",
    "sources_sha256":{
      "BASS_polarization":sha(BASS_POL),"HTT_R49_transfer":sha(HTT_TRANSFER),
      "REC_background":sha(REC_SRC),"REI_conditional_envelope":sha(REI_SOURCE)},
    "optical_history_FLRW_constructed":ion0,
    "optical_history_BianchiI_constructed":ion1,
    "source":[{"source_pi_STF":src["source_quad"].tolist(),
               **{k:v for k,v in src.items() if k!="source_quad"}}],
    "full_12_bianchi_families_geodesic":fam_data,
    "near_FLRW_linearized_six_out_of_twelve":linear,
    "cutoff_studies_4_representatives":convergence,
    "dynamic_12_family_Einstein_Euler_and_geodesic":dynamic,
    "REI_pair_bound_construction":{"source_Ne_difference_envelope":float(rei_bound),
      "constructed_emission_pi_two_sided_change_frobenius":bounded_pi,
      "status":"SENSITIVITY_ONLY; REI pair envelope is NOT a physical Bianchi electron-history error bound"},
    "counts":{"exact_geodesic_family_count":len(fam_data),
              "linearized_executed":sum(z["status"].endswith("EXECUTED") for z in linear.values()),
              "linearized_rejected_correctly":sum(z["status"].startswith("OUT_OF_SCOPE") for z in linear.values()),
              "cutoff_case_count":sum(len(v) for v in convergence.values()),
              "dynamic_Einstein_Euler_families":len(dynamic)},
    "physics_claim_ceiling":{
      "source_closure":"CONSTRUCTED_XE_AND_DENSITY",
      "BASS_Thomson":"EXACT_BASIS_FREE_CONDITIONAL_COLLISION",
      "REC_clock":"REAL_PRESCRIBED_POSITIVE_BIANCHI_I_INTERVAL",
      "REI":"REAL_PAIR_DIFFERENCE_ENVELOPE_REUSED, NOT PHYSICAL ELECTRON_SOURCE",
      "HTT_transfer":"GEODESIC_AND_SCREEN_CONDITIONAL_WITH_R49_12_FAMILY_EINSTEIN_EULER_BACKGROUND_IN_SEPARATE_DYNAMIC_LANE",
      "native_all_m_CMB_EB_likelihood":False,
      "release_matched_Planck_MC_and_Bianchi_family_posterior":False,
      "source_congruence_and_transfer_calibration":None},
    "elapsed_s":float(perf_counter()-start)}
