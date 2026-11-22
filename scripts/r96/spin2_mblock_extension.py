"""R96 physically typed spin-2 / all-azimuthal-m transport kernel research prototype.

Extends the older legacy PR13AG and R95 m=0 T+E tridiagonal skeleton to
explicit *general m* T/E/B with the exact spin-weighted cos(theta) recurrence

cos θ * _sY(l,m)= a(l+1,s,m) _sY(l+1,m)
                +a(l,s,m) _sY(l-1,m)
                -s*m/[l(l+1)] _sY(l,m).

P±=-(E±iB), with free streaming -i*k*cosθ, hence E'=-i*k offdiag E
     + k*d B, B'=-i*k offdiag B - k*d E, d=-2*m/[l(l+1)].
m=0 has *no* B production from this axisymmetric stream; |m|>0 can
convert E to B. Thomson T2/E2 submatrix directly reused from R95 and B
damped by -tau_dot. Uses true HyRec2/Planck tanh *reference visibility*
from R95 but a CONSTRUCTED quadrupolar STF shear source. Not an entire
general tilted Bianchi all-m Einstein-Boltzmann solution: inhomogeneous
k orientations, curved Bianchi m couplings and source-dependent collision
history are not implemented. Do not conflate code mode support with
physical family attribution.

Sparse LU Backward Euler is O(L) fill and O(N_ell) per time-step for
the banded free streaming blocks, rather than dense O(L^3) inversion.
"""
from __future__ import annotations
from pathlib import Path
import hashlib,json,math,time
import numpy as np
from scipy.sparse import csc_matrix,eye,lil_matrix
from scipy.sparse.linalg import splu
from scipy.special import sph_harm_y
from sympy.physics.wigner import wigner_3j
from scripts.r95.bianchi_polarized_hierarchy import _prepare_physical_visibility_timeline
from bass.transport.general_bianchi_transfer import gl_sphere_grid

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"docs/research_program/observational_publication_20261015/R96_THREE_THEORY_LOOPS_20261122/SPIN2_MBLOCK_HIERARCHY.json"

def c_spin(l,s,m):
 """Coefficient multiplying _sY_(l-1,m) in mu*_sY(l,m)."""
 if l<=max(abs(s),abs(m)):return 0.
 return math.sqrt((l*l-m*m)*(l*l-s*s))/(l*math.sqrt((2*l-1)*(2*l+1)))

def mblock_matrices(L,m,k=0.002):
 """For x=(T_l0..L, E_l2..L, B_l2..L), return A streaming and K Thomson."""
 if L<4 or abs(m)>L:raise ValueError("invalid mode")
 nT=L+1;np_=L-1;n=nT+2*np_
 A=lil_matrix((n,n),dtype=np.complex128)
 K=lil_matrix((n,n),dtype=np.complex128)
 for ell in range(abs(m),L):
  x=c_spin(ell+1,0,m)
  A[ell,ell+1]=-1j*k*x
  A[ell+1,ell]=-1j*k*x
 for ell in range(2,L):
  x=c_spin(ell+1,2,m)
  e=nT+ell-2
  b=nT+np_+ell-2
  A[e,e+1]=-1j*k*x
  A[e+1,e]=-1j*k*x
  A[b,b+1]=-1j*k*x
  A[b+1,b]=-1j*k*x
 for ell in range(max(2,abs(m)),L+1):
  E=nT+ell-2;B=E+np_
  d=-2*m/(ell*(ell+1))
  A[E,B]=k*d
  A[B,E]=-k*d
 # Keep m-mismatched modes zero by leaving all inactive rows unforced.
 for ell in range(max(1,abs(m)),L+1):
  K[ell,ell]=-1.
 for ell in range(max(2,abs(m)),L+1):
  i=ell-2
  K[nT+i,nT+i]=-1.
  K[nT+np_+i,nT+np_+i]=-1.
 if abs(m)<=2:
  K[2,2]=-.9
  K[2,nT]=-math.sqrt(6)/10
  K[nT,2]=-3/(5*math.sqrt(6))
  K[nT,nT]=-.4
 return A.tocsc(),K.tocsc()

def stf_source_harmonics(S):
 S=np.asarray(S,float)
 if S.shape!=(3,3) or np.max(abs(S-S.T))>1e-12 or abs(np.trace(S))>1e-12:
  raise ValueError("expected physical normal-frame symmetric tracefree")
 TH,PH,d,w=gl_sphere_grid(8)
 y=np.einsum("...i,ij,...j->...",d,S,d)
 out={}
 for m in range(-2,3):
  out[m]=complex(np.sum(w*y*np.conj(sph_harm_y(2,m,TH,PH))))
 return out

def recurrence_oracle():
 # Verify Wigner-3j recurrence for scalar s=0 and existing
 # tested spin-2 angular quadrature, using actual synthetic known grid.
 from bass.transport.general_bianchi_transfer import spin_weighted_spherical_harmonic_grid
 theta=np.array([.37,.83,1.22,1.79,2.36],float)
 phi=np.array([.1,.5,1.2,2.2,2.7])
 errors={}
 for s in (0,2,-2):
  m=1 if s==0 else 2
  l=max(4,abs(s)+1)
  y0=spin_weighted_spherical_harmonic_grid(s,l,m,theta,phi)
  yp=spin_weighted_spherical_harmonic_grid(s,l+1,m,theta,phi)
  ym=spin_weighted_spherical_harmonic_grid(s,l-1,m,theta,phi)
  # exact angular recurrence for spin s with signed diagonal term
  rhs=c_spin(l+1,s,m)*yp+c_spin(l,s,m)*ym-(s*m/(l*(l+1)))*y0
  diff=float(np.max(abs(np.cos(theta)*y0-rhs)))
  errors[str(s)]=diff
  if diff>2e-12:raise RuntimeError(f"spin-weight recurrence sign fails s={s}: {diff}")
 return errors

def integrate_block(vis,L,m,k=0.002,sigma=1e-4,quad=1+0j):
 A,K=mblock_matrices(L,m,k)
 n=A.shape[0]
 y=np.zeros(n,dtype=np.complex128)
 I=eye(n,format="csc",dtype=np.complex128)
 zf=vis["z_fwd"];H=vis["H_fwd_Mpc"];tdot=vis["tdot_fwd_Mpc"];deta=vis["d_eta"]
 for j,dt in enumerate(deta):
  z=.5*(zf[j]+zf[j+1])
  H_mid=.5*(H[j]+H[j+1])
  tdot_mid=.5*(tdot[j]+tdot[j+1])
  s=np.zeros(n,complex)
  if abs(m)<=2:
   # Source amplitude and spectral angular ratio separate.
   s[2]=-sigma*(H_mid/(1+z))/(((1+z)/1100)**.25)*quad
  yy=y+dt*s
  mat=I-dt*(A+tdot_mid*K)
  y=splu(mat).solve(yy)
 if not np.isfinite(y).all():raise RuntimeError("nonfinite")
 nT=L+1;nP=L-1
 T=y[:nT];E=y[nT:nT+nP];B=y[nT+nP:]
 return {"L":L,"m":m,"k_Mpc_inv":k,"T2":complex(T[2]),
         "E2":complex(E[0]),"B2":complex(B[0]),
         "all_mode_norm":float(np.linalg.norm(y)),
         "mode_EB_power_proxy":float(np.vdot(B,B).real),
         "mode_T_power_proxy":float(np.vdot(T,T).real),
         "mode_B_over_E_proxy":float(np.linalg.norm(B)/max(np.linalg.norm(E),1e-30)),
         "stream_max_skew_hermitian_err":float(np.max(np.abs((A+A.getH()).toarray()))),
         "thomson_2x2_eigen":sorted(np.linalg.eigvals(K.toarray()[[2,nT],:][:,[2,nT]]).real.tolist())}

def compute():
 t0=time.perf_counter()
 rec=recurrence_oracle()
 vis=_prepare_physical_visibility_timeline()
 S=np.array([[.5,.2,-.05],[.2,-.3,.1],[-.05,.1,-.2]],float)
 quad=stf_source_harmonics(S)
 amp=max(abs(v) for v in quad.values())
 if amp<=0:raise RuntimeError("STF source projection zero")
 q={m:v/amp for m,v in quad.items()}
 output={}
 for L in (8,16,32,60):
  out=[]
  for m in (-2,-1,0,1,2):
   j=integrate_block(vis,L,m,k=.002,sigma=1e-4,quad=q[m])
   out.append({**{x:v for x,v in j.items() if x not in ("T2","E2","B2")},
              "T2":[j["T2"].real,j["T2"].imag],
              "E2":[j["E2"].real,j["E2"].imag],
              "B2":[j["B2"].real,j["B2"].imag]})
   if j["stream_max_skew_hermitian_err"]>1e-13:
    raise RuntimeError("free-streaming Hermitian norm not preserved")
   if np.max(abs(np.array(j["thomson_2x2_eigen"])-[-1.,-.3]))>1e-13:
    raise RuntimeError("Thomson source collision eigen drift")
  output[str(L)]=out
 zero=[]
 for m in (0,1,2):
  r=integrate_block(vis,8,m,k=0,sigma=1e-4,quad=1)
  zero.append({"m":m,"B2_abs":abs(r["B2"]),"Bnorm_proxy":r["mode_EB_power_proxy"]})
 if max(r["B2_abs"] for r in zero)>1e-14:
  raise RuntimeError("zero-k B from E violation")
 m0=[x for x in output["60"] if x["m"]==0][0]
 if abs(complex(*m0["B2"]))>1e-13:
  raise RuntimeError("m0 parity fail")
 # A finite-ell supported code is not an executed full-all-m Bianchi hierarchy.
 return {"schema":"htt.r96.general_m_spin2_finite_hierarchy_control/1",
         "source":"R95 HyRec2+tanh tau_dot and legacy PR13AG + R95 m0 T/E reused",
         "mathematical_model":"-ik cos(theta) spin s=0,+2,-2 with spin recurrence; T2/E2 BASS Thomson; constructed STF shear sigma=1e-4 and k=0.002 1/Mpc; axisymmetric homogeneous free-streaming blocks",
         "signature":"(-,+,+,+)","unit":"k, tau_dot,H_conf are 1/Mpc; d_eta in Mpc; sigma dimensionless H-normalized; T/E/B Fourier-modes dimensionless",
         "recurrence_oracle":rec,"stf_source_normalized_by_m":{str(m):[v.real,v.imag] for m,v in q.items()},
         "m_modes_executed":list(range(-2,3)),"ell_max_executed":[8,16,32,60],
         "mblock_results":output,"zero_k_null_B":zero,
         "m0_B60_abs":abs(complex(*m0["B2"])),
         "legacy_pr13ag_synthetic_source_promoted":False,
         "full_all_m_curved_tilted_bianchi_coupling_produced":False,
         "B_mode_sources":"m-dependent helicity free-streaming toy; no curved Bianchi connection precession/m-mode scattering",
         "physical_CMB_power_spectra_or_Bianchi_posterior":None,
         "elapsed_s":time.perf_counter()-t0}
def main():
 if OUT.exists():raise RuntimeError("create-only")
 j=compute()
 OUT.write_text(json.dumps(j,indent=2,ensure_ascii=False)+"\n")
 print(json.dumps({"spin_recurrence_max":max(j["recurrence_oracle"].values()),
  "modes":j["m_modes_executed"],"L":j["ell_max_executed"],
  "B_abs_m0_L60":j["m0_B60_abs"],"elapsed":j["elapsed_s"]}))
if __name__=="__main__":main()
