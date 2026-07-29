/-
  PR-257 orbit-catalogue v2 — independent Lean axis.

  This source formalizes exactly the bounded claims in
  CAS-PR257-ORBIT-CATALOGUE-V2-001:

  * the O(3) scalar/pseudoscalar transformation law of the twelve registered
    polynomials for an STF-even sigma, polar beta, and axial omega;
  * the trace-free 3x3 Cayley-Hamilton identity and its three registered
    vector contractions;
  * the squared beta-Krylov determinant/Gram-determinant identity;
  * all exact integer fixture values;
  * the beta=0, omega and negative-omega catalogue-collision witness; and
  * explicit UNPROVEN states for generic separation and completeness.

  The proof uses only the repository-pinned Lean 4 core/Std toolchain.  It
  does not import or assume a sibling CAS result.  `grind` is used as a
  kernel-checked polynomial normalizer; fixed rational claims use
  `native_decide`.
-/

import Std

namespace PR257Orbit

structure Vec3 where
  x : Rat
  y : Rat
  z : Rat
deriving DecidableEq, Repr

structure Mat3 where
  m00 : Rat
  m01 : Rat
  m02 : Rat
  m10 : Rat
  m11 : Rat
  m12 : Rat
  m20 : Rat
  m21 : Rat
  m22 : Rat
deriving DecidableEq, Repr

theorem Vec3.extensionality {u v : Vec3}
    (hx : u.x = v.x) (hy : u.y = v.y) (hz : u.z = v.z) : u = v := by
  cases u
  cases v
  grind

theorem Mat3.extensionality {A B : Mat3}
    (h00 : A.m00 = B.m00) (h01 : A.m01 = B.m01)
    (h02 : A.m02 = B.m02) (h10 : A.m10 = B.m10)
    (h11 : A.m11 = B.m11) (h12 : A.m12 = B.m12)
    (h20 : A.m20 = B.m20) (h21 : A.m21 = B.m21)
    (h22 : A.m22 = B.m22) : A = B := by
  cases A
  cases B
  grind

def dot (u v : Vec3) : Rat :=
  u.x * v.x + u.y * v.y + u.z * v.z

def vscale (a : Rat) (u : Vec3) : Vec3 :=
  ⟨a * u.x, a * u.y, a * u.z⟩

def vadd (u v : Vec3) : Vec3 :=
  ⟨u.x + v.x, u.y + v.y, u.z + v.z⟩

def mv (A : Mat3) (u : Vec3) : Vec3 :=
  ⟨A.m00 * u.x + A.m01 * u.y + A.m02 * u.z,
   A.m10 * u.x + A.m11 * u.y + A.m12 * u.z,
   A.m20 * u.x + A.m21 * u.y + A.m22 * u.z⟩

def mm (A B : Mat3) : Mat3 :=
  ⟨A.m00*B.m00 + A.m01*B.m10 + A.m02*B.m20,
   A.m00*B.m01 + A.m01*B.m11 + A.m02*B.m21,
   A.m00*B.m02 + A.m01*B.m12 + A.m02*B.m22,
   A.m10*B.m00 + A.m11*B.m10 + A.m12*B.m20,
   A.m10*B.m01 + A.m11*B.m11 + A.m12*B.m21,
   A.m10*B.m02 + A.m11*B.m12 + A.m12*B.m22,
   A.m20*B.m00 + A.m21*B.m10 + A.m22*B.m20,
   A.m20*B.m01 + A.m21*B.m11 + A.m22*B.m21,
   A.m20*B.m02 + A.m21*B.m12 + A.m22*B.m22⟩

def transpose (A : Mat3) : Mat3 :=
  ⟨A.m00, A.m10, A.m20,
   A.m01, A.m11, A.m21,
   A.m02, A.m12, A.m22⟩

def ident : Mat3 :=
  ⟨1, 0, 0, 0, 1, 0, 0, 0, 1⟩

def madd (A B : Mat3) : Mat3 :=
  ⟨A.m00+B.m00, A.m01+B.m01, A.m02+B.m02,
   A.m10+B.m10, A.m11+B.m11, A.m12+B.m12,
   A.m20+B.m20, A.m21+B.m21, A.m22+B.m22⟩

def mscale (a : Rat) (A : Mat3) : Mat3 :=
  ⟨a*A.m00, a*A.m01, a*A.m02,
   a*A.m10, a*A.m11, a*A.m12,
   a*A.m20, a*A.m21, a*A.m22⟩

def trace (A : Mat3) : Rat := A.m00 + A.m11 + A.m22
def tr2 (A : Mat3) : Rat := trace (mm A A)
def tr3 (A : Mat3) : Rat := trace (mm (mm A A) A)

def det (A : Mat3) : Rat :=
  A.m00 * (A.m11*A.m22 - A.m12*A.m21)
  - A.m01 * (A.m10*A.m22 - A.m12*A.m20)
  + A.m02 * (A.m10*A.m21 - A.m11*A.m20)

def fromCols (u v w : Vec3) : Mat3 :=
  ⟨u.x, v.x, w.x,
   u.y, v.y, w.y,
   u.z, v.z, w.z⟩

def gramMatrix (u v w : Vec3) : Mat3 :=
  ⟨dot u u, dot u v, dot u w,
   dot v u, dot v v, dot v w,
   dot w u, dot w v, dot w w⟩

def sigmaAction (R sigma : Mat3) : Mat3 :=
  mm (mm R sigma) (transpose R)

/-- The exact registered O(3) domain: RᵀR=I and det(R)=±1. -/
structure O3 (R : Mat3) : Prop where
  rt_mul_r : mm (transpose R) R = ident
  det_sign : det R = 1 ∨ det R = -1

theorem mm_assoc (A B C : Mat3) : mm (mm A B) C = mm A (mm B C) := by
  apply Mat3.extensionality <;> grind [mm]

theorem mm_ident_left (A : Mat3) : mm ident A = A := by
  apply Mat3.extensionality <;> grind [mm, ident]

theorem mm_ident_right (A : Mat3) : mm A ident = A := by
  apply Mat3.extensionality <;> grind [mm, ident]

theorem mv_assoc (A B : Mat3) (u : Vec3) :
    mv (mm A B) u = mv A (mv B u) := by
  apply Vec3.extensionality <;> grind [mv, mm]

theorem mv_ident (u : Vec3) : mv ident u = u := by
  apply Vec3.extensionality <;> grind [mv, ident]

theorem trace_cyclic (A B : Mat3) :
    trace (mm A B) = trace (mm B A) := by
  grind [trace, mm]

theorem det_mul (A B : Mat3) :
    det (mm A B) = det A * det B := by
  grind [det, mm]

theorem fromCols_mv (R : Mat3) (u v w : Vec3) :
    fromCols (mv R u) (mv R v) (mv R w) = mm R (fromCols u v w) := by
  apply Mat3.extensionality <;> grind [fromCols, mv, mm]

theorem det_sq_one {R : Mat3} (hR : O3 R) : det R * det R = 1 := by
  rcases hR.det_sign with h | h <;> grind

theorem dot_mv_adjoint (R : Mat3) (u v : Vec3) :
    dot (mv R u) v = dot u (mv (transpose R) v) := by
  grind [dot, mv, transpose]

theorem dot_mv {R : Mat3} (hR : O3 R) (u v : Vec3) :
    dot (mv R u) (mv R v) = dot u v := by
  calc
    dot (mv R u) (mv R v)
        = dot u (mv (transpose R) (mv R v)) := dot_mv_adjoint _ _ _
    _ = dot u (mv (mm (transpose R) R) v) := by
          rw [mv_assoc]
    _ = dot u (mv ident v) := by rw [hR.rt_mul_r]
    _ = dot u v := by rw [mv_ident]

theorem sigmaAction_mul_R {R : Mat3} (hR : O3 R) (sigma : Mat3) :
    mm (sigmaAction R sigma) R = mm R sigma := by
  calc
    mm (sigmaAction R sigma) R
        = mm (mm R sigma) (mm (transpose R) R) := by
            simp only [sigmaAction, mm_assoc]
    _ = mm (mm R sigma) ident := by rw [hR.rt_mul_r]
    _ = mm R sigma := mm_ident_right _

theorem sigmaAction_mv {R : Mat3} (hR : O3 R) (sigma : Mat3) (u : Vec3) :
    mv (sigmaAction R sigma) (mv R u) = mv R (mv sigma u) := by
  calc
    mv (sigmaAction R sigma) (mv R u)
        = mv (mm (sigmaAction R sigma) R) u := (mv_assoc _ _ _).symm
    _ = mv (mm R sigma) u := by rw [sigmaAction_mul_R hR sigma]
    _ = mv R (mv sigma u) := mv_assoc _ _ _

theorem sigmaAction_mul {R : Mat3} (hR : O3 R) (A B : Mat3) :
    mm (sigmaAction R A) (sigmaAction R B) = sigmaAction R (mm A B) := by
  calc
    mm (sigmaAction R A) (sigmaAction R B)
        = mm (mm (sigmaAction R A) R) (mm B (transpose R)) := by
            simp only [sigmaAction, mm_assoc]
    _ = mm (mm R A) (mm B (transpose R)) := by
            rw [sigmaAction_mul_R hR A]
    _ = sigmaAction R (mm A B) := by
            simp only [sigmaAction, mm_assoc]

theorem trace_sigmaAction {R : Mat3} (hR : O3 R) (A : Mat3) :
    trace (sigmaAction R A) = trace A := by
  calc
    trace (sigmaAction R A)
        = trace (mm (transpose R) (mm R A)) := trace_cyclic _ _
    _ = trace (mm (mm (transpose R) R) A) := by rw [mm_assoc]
    _ = trace (mm ident A) := by rw [hR.rt_mul_r]
    _ = trace A := by rw [mm_ident_left]

theorem tr2_sigmaAction {R : Mat3} (hR : O3 R) (A : Mat3) :
    tr2 (sigmaAction R A) = tr2 A := by
  unfold tr2
  rw [sigmaAction_mul hR A A, trace_sigmaAction hR]

theorem tr3_sigmaAction {R : Mat3} (hR : O3 R) (A : Mat3) :
    tr3 (sigmaAction R A) = tr3 A := by
  unfold tr3
  rw [sigmaAction_mul hR A A]
  rw [sigmaAction_mul hR (mm A A) A]
  exact trace_sigmaAction hR _

def beta2 (beta : Vec3) : Rat := dot beta beta
def betaSigmaBeta (sigma : Mat3) (beta : Vec3) : Rat :=
  dot beta (mv sigma beta)
def betaSigma2Beta (sigma : Mat3) (beta : Vec3) : Rat :=
  dot beta (mv sigma (mv sigma beta))
def betaKrylovDet (sigma : Mat3) (beta : Vec3) : Rat :=
  det (fromCols beta (mv sigma beta) (mv sigma (mv sigma beta)))

def omega2 (omega : Vec3) : Rat := dot omega omega
def omegaSigmaOmega (sigma : Mat3) (omega : Vec3) : Rat :=
  dot omega (mv sigma omega)
def omegaSigma2Omega (sigma : Mat3) (omega : Vec3) : Rat :=
  dot omega (mv sigma (mv sigma omega))

def betaDotOmega (beta omega : Vec3) : Rat := dot beta omega
def betaSigmaOmega (sigma : Mat3) (beta omega : Vec3) : Rat :=
  dot beta (mv sigma omega)
def betaSigma2Omega (sigma : Mat3) (beta omega : Vec3) : Rat :=
  dot beta (mv sigma (mv sigma omega))

theorem beta2_scalar {R : Mat3} (hR : O3 R) (beta : Vec3) :
    beta2 (mv R beta) = beta2 beta := by
  exact dot_mv hR beta beta

theorem betaSigmaBeta_scalar {R : Mat3} (hR : O3 R)
    (sigma : Mat3) (beta : Vec3) :
    betaSigmaBeta (sigmaAction R sigma) (mv R beta)
      = betaSigmaBeta sigma beta := by
  unfold betaSigmaBeta
  rw [sigmaAction_mv hR, dot_mv hR]

theorem betaSigma2Beta_scalar {R : Mat3} (hR : O3 R)
    (sigma : Mat3) (beta : Vec3) :
    betaSigma2Beta (sigmaAction R sigma) (mv R beta)
      = betaSigma2Beta sigma beta := by
  unfold betaSigma2Beta
  rw [sigmaAction_mv hR, sigmaAction_mv hR, dot_mv hR]

theorem betaKrylovDet_pseudoscalar {R : Mat3} (hR : O3 R)
    (sigma : Mat3) (beta : Vec3) :
    betaKrylovDet (sigmaAction R sigma) (mv R beta)
      = det R * betaKrylovDet sigma beta := by
  unfold betaKrylovDet
  rw [sigmaAction_mv hR, sigmaAction_mv hR]
  rw [fromCols_mv, det_mul]

theorem dot_vscale_left (a : Rat) (u v : Vec3) :
    dot (vscale a u) v = a * dot u v := by
  grind [dot, vscale]

theorem dot_vscale_right (a : Rat) (u v : Vec3) :
    dot u (vscale a v) = a * dot u v := by
  grind [dot, vscale]

theorem mv_vscale (A : Mat3) (a : Rat) (u : Vec3) :
    mv A (vscale a u) = vscale a (mv A u) := by
  apply Vec3.extensionality <;> grind [mv, vscale]

theorem mv_madd (A B : Mat3) (u : Vec3) :
    mv (madd A B) u = vadd (mv A u) (mv B u) := by
  apply Vec3.extensionality <;> grind [mv, madd, vadd]

theorem mv_mscale (a : Rat) (A : Mat3) (u : Vec3) :
    mv (mscale a A) u = vscale a (mv A u) := by
  apply Vec3.extensionality <;> grind [mv, mscale, vscale]

theorem dot_vadd_right (u v w : Vec3) :
    dot u (vadd v w) = dot u v + dot u w := by
  grind [dot, vadd]

theorem omega2_scalar {R : Mat3} (hR : O3 R) (omega : Vec3) :
    omega2 (vscale (det R) (mv R omega)) = omega2 omega := by
  unfold omega2
  rw [dot_vscale_left, dot_vscale_right, dot_mv hR]
  have hd := det_sq_one hR
  grind

theorem omegaSigmaOmega_scalar {R : Mat3} (hR : O3 R)
    (sigma : Mat3) (omega : Vec3) :
    omegaSigmaOmega (sigmaAction R sigma) (vscale (det R) (mv R omega))
      = omegaSigmaOmega sigma omega := by
  unfold omegaSigmaOmega
  rw [mv_vscale, sigmaAction_mv hR]
  rw [dot_vscale_left, dot_vscale_right, dot_mv hR]
  have hd := det_sq_one hR
  grind

theorem omegaSigma2Omega_scalar {R : Mat3} (hR : O3 R)
    (sigma : Mat3) (omega : Vec3) :
    omegaSigma2Omega (sigmaAction R sigma) (vscale (det R) (mv R omega))
      = omegaSigma2Omega sigma omega := by
  unfold omegaSigma2Omega
  rw [mv_vscale, sigmaAction_mv hR]
  rw [mv_vscale, sigmaAction_mv hR]
  rw [dot_vscale_left, dot_vscale_right, dot_mv hR]
  have hd := det_sq_one hR
  grind

theorem betaDotOmega_pseudoscalar {R : Mat3} (hR : O3 R)
    (beta omega : Vec3) :
    betaDotOmega (mv R beta) (vscale (det R) (mv R omega))
      = det R * betaDotOmega beta omega := by
  unfold betaDotOmega
  rw [dot_vscale_right, dot_mv hR]

theorem betaSigmaOmega_pseudoscalar {R : Mat3} (hR : O3 R)
    (sigma : Mat3) (beta omega : Vec3) :
    betaSigmaOmega (sigmaAction R sigma) (mv R beta)
      (vscale (det R) (mv R omega))
      = det R * betaSigmaOmega sigma beta omega := by
  unfold betaSigmaOmega
  rw [mv_vscale, sigmaAction_mv hR]
  rw [dot_vscale_right, dot_mv hR]

theorem betaSigma2Omega_pseudoscalar {R : Mat3} (hR : O3 R)
    (sigma : Mat3) (beta omega : Vec3) :
    betaSigma2Omega (sigmaAction R sigma) (mv R beta)
      (vscale (det R) (mv R omega))
      = det R * betaSigma2Omega sigma beta omega := by
  unfold betaSigma2Omega
  rw [mv_vscale, sigmaAction_mv hR]
  rw [mv_vscale, sigmaAction_mv hR]
  rw [dot_vscale_right, dot_mv hR]

/-- Every real symmetric trace-free matrix is represented by five rationals. -/
def stf (a b d e f : Rat) : Mat3 :=
  ⟨a, d, e,
   d, b, f,
   e, f, -a-b⟩

theorem stf_symmetric (a b d e f : Rat) :
    transpose (stf a b d e f) = stf a b d e f := by
  rfl

theorem stf_tracefree (a b d e f : Rat) :
    trace (stf a b d e f) = 0 := by
  grind [trace, stf]

def stfQ2 (a b d e f : Rat) : Rat :=
  a*a + b*b + a*b + d*d + e*e + f*f

def stfQ3 (a b d e f : Rat) : Rat :=
  -a*a*b - a*b*b - a*f*f + d*d*(a+b) + 2*d*e*f - b*e*e

theorem stf_tr2_half (a b d e f : Rat) :
    tr2 (stf a b d e f) / 2 = stfQ2 a b d e f := by
  grind (ringSteps := 500000) [tr2, trace, mm, stf, stfQ2]

theorem stf_tr3_third (a b d e f : Rat) :
    tr3 (stf a b d e f) / 3 = stfQ3 a b d e f := by
  grind (ringSteps := 1000000) [tr3, trace, mm, stf, stfQ3]

/-- Trace-free 3x3 Cayley-Hamilton identity in the registered normalization. -/
theorem cayleyHamiltonSTF (a b d e f : Rat) :
    mm (mm (stf a b d e f) (stf a b d e f)) (stf a b d e f)
      =
    madd
      (mscale (tr2 (stf a b d e f) / 2) (stf a b d e f))
      (mscale (tr3 (stf a b d e f) / 3) ident) := by
  rw [stf_tr2_half, stf_tr3_third]
  apply Mat3.extensionality <;>
    grind (ringSteps := 500000)
      [stf, mm, madd, mscale, stfQ2, stfQ3, ident]

theorem cayleyHamiltonBetaContraction
    (a b d e f : Rat) (beta : Vec3) :
    dot beta
      (mv (mm (mm (stf a b d e f) (stf a b d e f))
              (stf a b d e f)) beta)
      =
    (tr2 (stf a b d e f) / 2)
        * dot beta (mv (stf a b d e f) beta)
      + (tr3 (stf a b d e f) / 3) * dot beta beta := by
  rw [cayleyHamiltonSTF]
  rw [mv_madd, mv_mscale, mv_mscale, dot_vadd_right,
    dot_vscale_right, dot_vscale_right, mv_ident]

theorem cayleyHamiltonOmegaContraction
    (a b d e f : Rat) (omega : Vec3) :
    dot omega
      (mv (mm (mm (stf a b d e f) (stf a b d e f))
              (stf a b d e f)) omega)
      =
    (tr2 (stf a b d e f) / 2)
        * dot omega (mv (stf a b d e f) omega)
      + (tr3 (stf a b d e f) / 3) * dot omega omega := by
  rw [cayleyHamiltonSTF]
  rw [mv_madd, mv_mscale, mv_mscale, dot_vadd_right,
    dot_vscale_right, dot_vscale_right, mv_ident]

theorem cayleyHamiltonMixedContraction
    (a b d e f : Rat) (beta omega : Vec3) :
    dot beta
      (mv (mm (mm (stf a b d e f) (stf a b d e f))
              (stf a b d e f)) omega)
      =
    (tr2 (stf a b d e f) / 2)
        * dot beta (mv (stf a b d e f) omega)
      + (tr3 (stf a b d e f) / 3) * dot beta omega := by
  rw [cayleyHamiltonSTF]
  rw [mv_madd, mv_mscale, mv_mscale, dot_vadd_right,
    dot_vscale_right, dot_vscale_right, mv_ident]

/-- det[u,v,w]^2 = det of the Gram matrix, over exact rationals. -/
theorem detSquared_eq_gramDet (u v w : Vec3) :
    det (fromCols u v w) * det (fromCols u v w)
      = det (gramMatrix u v w) := by
  grind [det, fromCols, gramMatrix, dot]

theorem betaKrylovGramSyzygy (sigma : Mat3) (beta : Vec3) :
    betaKrylovDet sigma beta * betaKrylovDet sigma beta
      =
    det (gramMatrix beta (mv sigma beta) (mv sigma (mv sigma beta))) := by
  exact detSquared_eq_gramDet _ _ _

/-! Exact registered fixture values. -/

def fixedSigma : Mat3 :=
  ⟨1, 0, 0, 0, 2, 0, 0, 0, -3⟩
def fixedBeta : Vec3 := ⟨1, 1, 1⟩
def fixedOmega : Vec3 := ⟨1, 2, 3⟩

theorem fixed_tr_sigma2 : tr2 fixedSigma = 14 := by native_decide
theorem fixed_tr_sigma3 : tr3 fixedSigma = -18 := by native_decide
theorem fixed_beta2 : beta2 fixedBeta = 3 := by native_decide
theorem fixed_beta_sigma_beta :
    betaSigmaBeta fixedSigma fixedBeta = 0 := by native_decide
theorem fixed_beta_sigma2_beta :
    betaSigma2Beta fixedSigma fixedBeta = 14 := by native_decide
theorem fixed_beta_krylov_det :
    betaKrylovDet fixedSigma fixedBeta = 20 := by native_decide
theorem fixed_omega2 : omega2 fixedOmega = 14 := by native_decide
theorem fixed_omega_sigma_omega :
    omegaSigmaOmega fixedSigma fixedOmega = -18 := by native_decide
theorem fixed_omega_sigma2_omega :
    omegaSigma2Omega fixedSigma fixedOmega = 98 := by native_decide
theorem fixed_beta_dot_omega :
    betaDotOmega fixedBeta fixedOmega = 6 := by native_decide
theorem fixed_beta_sigma_omega :
    betaSigmaOmega fixedSigma fixedBeta fixedOmega = -4 := by native_decide
theorem fixed_beta_sigma2_omega :
    betaSigma2Omega fixedSigma fixedBeta fixedOmega = 36 := by native_decide

def betaSigma3Beta (sigma : Mat3) (beta : Vec3) : Rat :=
  dot beta (mv sigma (mv sigma (mv sigma beta)))
def omegaSigma3Omega (sigma : Mat3) (omega : Vec3) : Rat :=
  dot omega (mv sigma (mv sigma (mv sigma omega)))
def betaSigma3Omega (sigma : Mat3) (beta omega : Vec3) : Rat :=
  dot beta (mv sigma (mv sigma (mv sigma omega)))

theorem fixed_beta_sigma3_beta :
    betaSigma3Beta fixedSigma fixedBeta = -18 := by native_decide
theorem fixed_omega_sigma3_omega :
    omegaSigma3Omega fixedSigma fixedOmega = -210 := by native_decide
theorem fixed_beta_sigma3_omega :
    betaSigma3Omega fixedSigma fixedBeta fixedOmega = -64 := by native_decide
theorem fixed_beta_krylov_gram :
    det (gramMatrix fixedBeta (mv fixedSigma fixedBeta)
      (mv fixedSigma (mv fixedSigma fixedBeta))) = 400 := by native_decide

structure CatalogueValues where
  tr_sigma2 : Rat
  tr_sigma3 : Rat
  beta2_v : Rat
  beta_sigma_beta : Rat
  beta_sigma2_beta : Rat
  beta_krylov_det : Rat
  omega2_v : Rat
  omega_sigma_omega : Rat
  omega_sigma2_omega : Rat
  beta_dot_omega : Rat
  beta_sigma_omega : Rat
  beta_sigma2_omega : Rat
deriving DecidableEq, Repr

def catalogue (sigma : Mat3) (beta omega : Vec3) : CatalogueValues :=
  ⟨tr2 sigma, tr3 sigma,
   beta2 beta, betaSigmaBeta sigma beta, betaSigma2Beta sigma beta,
   betaKrylovDet sigma beta,
   omega2 omega, omegaSigmaOmega sigma omega, omegaSigma2Omega sigma omega,
   betaDotOmega beta omega, betaSigmaOmega sigma beta omega,
   betaSigma2Omega sigma beta omega⟩

def zeroBeta : Vec3 := ⟨0, 0, 0⟩
def negativeFixedOmega : Vec3 := ⟨-1, -2, -3⟩

theorem nongeneric_catalogue_collision :
    catalogue fixedSigma zeroBeta fixedOmega
      = catalogue fixedSigma zeroBeta negativeFixedOmega := by native_decide

theorem nongeneric_witness_states_distinct :
    fixedOmega ≠ negativeFixedOmega := by native_decide

inductive PromotionStatus
  | UNPROVEN
deriving DecidableEq, Repr

def genericOrbitSeparationStatus : PromotionStatus := .UNPROVEN
def invariantRingCompletenessStatus : PromotionStatus := .UNPROVEN

theorem generic_separation_not_promoted :
    genericOrbitSeparationStatus = .UNPROVEN := rfl

theorem completeness_not_promoted :
    invariantRingCompletenessStatus = .UNPROVEN := rfl

/-!
  The eight contract-level checks are represented as propositions that are
  inhabited only because the load-bearing theorems above compiled.
-/

structure ScalarPseudoscalarO3Seal : Prop where
  tr2_even : ∀ {R}, O3 R → ∀ sigma, tr2 (sigmaAction R sigma) = tr2 sigma
  tr3_even : ∀ {R}, O3 R → ∀ sigma, tr3 (sigmaAction R sigma) = tr3 sigma
  beta2_even : ∀ {R}, O3 R → ∀ beta, beta2 (mv R beta) = beta2 beta
  betaSigmaBeta_even :
    ∀ {R}, O3 R → ∀ sigma beta,
      betaSigmaBeta (sigmaAction R sigma) (mv R beta)
        = betaSigmaBeta sigma beta
  betaSigma2Beta_even :
    ∀ {R}, O3 R → ∀ sigma beta,
      betaSigma2Beta (sigmaAction R sigma) (mv R beta)
        = betaSigma2Beta sigma beta
  betaKrylov_odd :
    ∀ {R}, O3 R → ∀ sigma beta,
      betaKrylovDet (sigmaAction R sigma) (mv R beta)
        = det R * betaKrylovDet sigma beta
  omega2_even :
    ∀ {R}, O3 R → ∀ omega,
      omega2 (vscale (det R) (mv R omega)) = omega2 omega
  omegaSigmaOmega_even :
    ∀ {R}, O3 R → ∀ sigma omega,
      omegaSigmaOmega (sigmaAction R sigma) (vscale (det R) (mv R omega))
        = omegaSigmaOmega sigma omega
  omegaSigma2Omega_even :
    ∀ {R}, O3 R → ∀ sigma omega,
      omegaSigma2Omega (sigmaAction R sigma) (vscale (det R) (mv R omega))
        = omegaSigma2Omega sigma omega
  betaDotOmega_odd :
    ∀ {R}, O3 R → ∀ beta omega,
      betaDotOmega (mv R beta) (vscale (det R) (mv R omega))
        = det R * betaDotOmega beta omega
  betaSigmaOmega_odd :
    ∀ {R}, O3 R → ∀ sigma beta omega,
      betaSigmaOmega (sigmaAction R sigma) (mv R beta)
        (vscale (det R) (mv R omega))
        = det R * betaSigmaOmega sigma beta omega
  betaSigma2Omega_odd :
    ∀ {R}, O3 R → ∀ sigma beta omega,
      betaSigma2Omega (sigmaAction R sigma) (mv R beta)
        (vscale (det R) (mv R omega))
        = det R * betaSigma2Omega sigma beta omega

theorem scalarPseudoscalarO3Seal : ScalarPseudoscalarO3Seal :=
  ⟨tr2_sigmaAction, tr3_sigmaAction,
   beta2_scalar, betaSigmaBeta_scalar, betaSigma2Beta_scalar,
   betaKrylovDet_pseudoscalar,
   omega2_scalar, omegaSigmaOmega_scalar, omegaSigma2Omega_scalar,
   betaDotOmega_pseudoscalar, betaSigmaOmega_pseudoscalar,
   betaSigma2Omega_pseudoscalar⟩

end PR257Orbit
