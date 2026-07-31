/-
  PR-270 Pillar-T CAS axis — exact Lean 4 formalization.

  This file is intentionally self-contained and imports only `Std` under the
  repository-pinned `formal/lean-toolchain`.  It proves the exact algebraic
  core of CAS-PR270-VECTOR-TENSOR-ORBIT-001:

  * the trace-free shear discriminant and repeated-eigenvalue stratum;
  * the general symmetric trace-free 3x3 Cayley-Hamilton reduction;
  * the Krylov/Vandermonde and Gram determinant identities;
  * the registered 14-coordinate chart Jacobian factor, using its actual
    block-triangular decomposition into the invariant, self-moment, and three
    Krylov moment blocks;
  * the exact principal and boundary fixtures; and
  * the cleared-denominator quotient-rule core of VT-T13.

  The global-orbit and full 1+3 source statements are represented only by
  typed nonpromotion states.  This file therefore cannot promote global
  separation, a native geometry payload, or family identification.
-/

import Std

namespace PR270PillarT

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

def madd (A B : Mat3) : Mat3 :=
  ⟨A.m00+B.m00, A.m01+B.m01, A.m02+B.m02,
   A.m10+B.m10, A.m11+B.m11, A.m12+B.m12,
   A.m20+B.m20, A.m21+B.m21, A.m22+B.m22⟩

def mscale (a : Rat) (A : Mat3) : Mat3 :=
  ⟨a*A.m00, a*A.m01, a*A.m02,
   a*A.m10, a*A.m11, a*A.m12,
   a*A.m20, a*A.m21, a*A.m22⟩

def ident : Mat3 :=
  ⟨1, 0, 0, 0, 1, 0, 0, 0, 1⟩

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

def stf (a b d e f : Rat) : Mat3 :=
  ⟨a, d, e, d, b, f, e, f, -a-b⟩

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

/-- VT-T6: Cayley-Hamilton for a general symmetric trace-free 3x3 matrix. -/
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

/-- The power-four reduction follows by multiplying the exact CH identity. -/
theorem cayleyHamiltonPowerFour (a b d e f : Rat) :
    mm
      (mm (mm (stf a b d e f) (stf a b d e f)) (stf a b d e f))
      (stf a b d e f)
      =
    madd
      (mscale
        (tr2 (stf a b d e f) / 2)
        (mm (stf a b d e f) (stf a b d e f)))
      (mscale
        (tr3 (stf a b d e f) / 3)
        (stf a b d e f)) := by
  rw [cayleyHamiltonSTF]
  apply Mat3.extensionality <;>
    grind (ringSteps := 500000) [mm, madd, mscale, ident]

/-- det[u,v,w]^2 is the exact Gram determinant over the rationals. -/
theorem detSquared_eq_gramDet (u v w : Vec3) :
    det (fromCols u v w) * det (fromCols u v w)
      = det (gramMatrix u v w) := by
  grind [det, fromCols, gramMatrix, dot]

def lambda3 (l1 l2 : Rat) : Rat := -l1-l2

def gapPolynomial (l1 l2 : Rat) : Rat :=
  (l1-l2) * (l1+2*l2) * (2*l1+l2)

def shearI2 (l1 l2 : Rat) : Rat :=
  l1^2 + l2^2 + (lambda3 l1 l2)^2

def shearI3 (l1 l2 : Rat) : Rat :=
  l1^3 + l2^3 + (lambda3 l1 l2)^3

def shearDelta (l1 l2 : Rat) : Rat :=
  (shearI2 l1 l2)^3 / 2 - 3 * (shearI3 l1 l2)^2

/-- VT-T5: the characteristic discriminant is the squared Vandermonde. -/
theorem discriminantIdentity (l1 l2 : Rat) :
    shearDelta l1 l2 = (gapPolynomial l1 l2)^2 := by
  grind (ringSteps := 1000000)
    [shearDelta, shearI2, shearI3, lambda3, gapPolynomial]

theorem discriminantSquareForm (l1 l2 : Rat) :
    shearDelta l1 l2 =
      ((l1-l2) * (l1+2*l2) * (2*l1+l2))^2 := by
  exact discriminantIdentity l1 l2

theorem axisymmetricStratum :
    shearI2 2 (-1) = 6 ∧
    shearI3 2 (-1) = 6 ∧
    shearDelta 2 (-1) = 0 := by
  native_decide

theorem principalShapeFixture :
    shearI2 (-2) 0 = 8 ∧
    shearI3 (-2) 0 = 0 ∧
    shearDelta (-2) 0 = 256 := by
  native_decide

def diagAction (l1 l2 : Rat) (v : Vec3) : Vec3 :=
  ⟨l1*v.x, l2*v.y, (lambda3 l1 l2)*v.z⟩

def krylovDet (l1 l2 : Rat) (v : Vec3) : Rat :=
  det (fromCols v (diagAction l1 l2 v)
    (diagAction l1 l2 (diagAction l1 l2 v)))

/-- VT-T7: exact Krylov/Vandermonde factorization. -/
theorem krylovVandermonde (l1 l2 : Rat) (v : Vec3) :
    krylovDet l1 l2 v =
      -v.x*v.y*v.z*gapPolynomial l1 l2 := by
  cases v
  simp only [krylovDet, diagAction, lambda3, gapPolynomial, det, fromCols]
  grind (ringSteps := 1000000)

theorem krylovGram (l1 l2 : Rat) (v : Vec3) :
    krylovDet l1 l2 v * krylovDet l1 l2 v =
      det (gramMatrix v (diagAction l1 l2 v)
        (diagAction l1 l2 (diagAction l1 l2 v))) := by
  exact detSquared_eq_gramDet _ _ _

def principalVector : Vec3 := ⟨1, 1, 1⟩
def noncyclicVector : Vec3 := ⟨1, 0, 1⟩

theorem principalKrylovFixture :
    krylovDet (-2) 0 principalVector = 16 := by native_decide

theorem principalKrylovGramFixture :
    det (gramMatrix principalVector
      (diagAction (-2) 0 principalVector)
      (diagAction (-2) 0 (diagAction (-2) 0 principalVector))) = 256 := by
  native_decide

theorem repeatedSpectrumRefusal (v : Vec3) :
    krylovDet 2 (-1) v = 0 := by
  grind [krylovDet, diagAction, lambda3, det, fromCols]

theorem zeroComponentRefusal :
    krylovDet (-2) 0 noncyclicVector = 0 := by native_decide

/-!
The 14-coordinate Jacobian is block lower triangular after ordering its
variables as (lambda_1, lambda_2, v_0, v_1, v_2, v_3).  The upper block
splits again into:

* a 2x2 derivative block for (I2,I3), and
* a 3x3 derivative block for the v_0 self moments.

The remaining three diagonal blocks are the same Krylov moment matrix.  The
following definitions are those exact block determinants, not fitted values.
-/

def invariantDerivativeDet (l1 l2 : Rat) : Rat :=
  (4*l1 + 2*l2) * (3*l2^2 - 3*(lambda3 l1 l2)^2)
  - (2*l1 + 4*l2) * (3*l1^2 - 3*(lambda3 l1 l2)^2)

def selfMomentDerivativeDet (l1 l2 a b c : Rat) : Rat :=
  det
    ⟨2*a, 2*b, 2*c,
     2*l1*a, 2*l2*b, 2*(lambda3 l1 l2)*c,
     2*l1^2*a, 2*l2^2*b, 2*(lambda3 l1 l2)^2*c⟩

def momentKrylovBlockDet (l1 l2 a b c : Rat) : Rat :=
  det
    ⟨a, b, c,
     l1*a, l2*b, (lambda3 l1 l2)*c,
     l1^2*a, l2^2*b, (lambda3 l1 l2)^2*c⟩

theorem invariantDerivativeFactor (l1 l2 : Rat) :
    invariantDerivativeDet l1 l2 = -6 * gapPolynomial l1 l2 := by
  grind [invariantDerivativeDet, lambda3, gapPolynomial]

theorem selfMomentDerivativeFactor (l1 l2 a b c : Rat) :
    selfMomentDerivativeDet l1 l2 a b c =
      -8*a*b*c*gapPolynomial l1 l2 := by
  grind [selfMomentDerivativeDet, lambda3, gapPolynomial, det]

theorem momentKrylovBlockFactor (l1 l2 a b c : Rat) :
    momentKrylovBlockDet l1 l2 a b c =
      -a*b*c*gapPolynomial l1 l2 := by
  grind [momentKrylovBlockDet, lambda3, gapPolynomial, det]

def localChartJacobianDet (l1 l2 a b c : Rat) : Rat :=
  invariantDerivativeDet l1 l2
  * selfMomentDerivativeDet l1 l2 a b c
  * (momentKrylovBlockDet l1 l2 a b c)^3

/-- VT-T8: exact determinant factor of the registered local chart. -/
theorem localChartJacobianFactor (l1 l2 a b c : Rat) :
    localChartJacobianDet l1 l2 a b c =
      -48*a^4*b^4*c^4
        *(l1-l2)^5*(l1+2*l2)^5*(2*l1+l2)^5 := by
  rw [localChartJacobianDet, invariantDerivativeFactor,
    selfMomentDerivativeFactor, momentKrylovBlockFactor]
  grind [gapPolynomial]

theorem principalLocalChartJacobian :
    localChartJacobianDet (-2) 0 1 1 1 = 50331648 := by
  native_decide

theorem repeatedSpectrumLocalChartRefusal (a b c : Rat) :
    localChartJacobianDet 2 (-1) a b c = 0 := by
  rw [localChartJacobianFactor]
  grind

theorem noncyclicLocalChartRefusal (l1 l2 b c : Rat) :
    localChartJacobianDet l1 l2 0 b c = 0 := by
  rw [localChartJacobianFactor]
  grind

/-- Cleared quotient-rule numerator for d(6 I3^2 / I2^3). -/
theorem shapeChainRuleNumerator
    (q2 q3 dq2 dq3 : Rat) :
    (12*q3*dq3)*q2^3 - (6*q3^2)*(3*q2^2*dq2)
      =
    q2^2 * (12*q2*q3*dq3 - 18*q3^2*dq2) := by
  grind

inductive GlobalOrbitStatus where
  | unproven
deriving DecidableEq, Repr

inductive SourceDecompositionStatus where
  | inconclusiveMissingTypedEvolutionLaw
deriving DecidableEq, Repr

def globalOrbitStatus : GlobalOrbitStatus := .unproven
def sourceDecompositionStatus : SourceDecompositionStatus :=
  .inconclusiveMissingTypedEvolutionLaw

theorem globalSeparationNotPromoted :
    globalOrbitStatus = .unproven := rfl

theorem sourceDecompositionNotPromoted :
    sourceDecompositionStatus =
      .inconclusiveMissingTypedEvolutionLaw := rfl

end PR270PillarT
