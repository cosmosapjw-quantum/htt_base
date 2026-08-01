/-
  PR-270 Pillar-T CAS axis — mathlib-backed Lean 4 formalization.

  The contract is stated over real trace-free symmetric 3x3 tensors.  This
  file therefore works over `ℝ` directly; it does not substitute a rational
  test domain for the declared real domain.  It proves:

  * the shear discriminant identity, normalized-shape bound, and strata;
  * Cayley-Hamilton plus the all-power trace-free recurrence;
  * Krylov/Vandermonde, Gram, and the exact cyclicity criterion;
  * the determinant of the actual sparse 14-coordinate Jacobian, assembled
    from the analytic derivative blocks of the registered moment map;
  * principal and refusal fixtures using theorem-producing normalization; and
  * the cleared-denominator quotient-rule core of VT-T13.

  Global orbit separation and the full 1+3 source decomposition remain typed
  nonpromotion states.  Nothing here promotes family identification.
-/

import Mathlib

namespace PR270PillarT

noncomputable section

structure Vec3 where
  x : ℝ
  y : ℝ
  z : ℝ

structure Mat3 where
  m00 : ℝ
  m01 : ℝ
  m02 : ℝ
  m10 : ℝ
  m11 : ℝ
  m12 : ℝ
  m20 : ℝ
  m21 : ℝ
  m22 : ℝ

@[ext]
theorem Vec3.extensionality {u v : Vec3}
    (hx : u.x = v.x) (hy : u.y = v.y) (hz : u.z = v.z) : u = v := by
  cases u
  cases v
  simp_all

@[ext]
theorem Mat3.extensionality {A B : Mat3}
    (h00 : A.m00 = B.m00) (h01 : A.m01 = B.m01)
    (h02 : A.m02 = B.m02) (h10 : A.m10 = B.m10)
    (h11 : A.m11 = B.m11) (h12 : A.m12 = B.m12)
    (h20 : A.m20 = B.m20) (h21 : A.m21 = B.m21)
    (h22 : A.m22 = B.m22) : A = B := by
  cases A
  cases B
  simp_all

def dot (u v : Vec3) : ℝ :=
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

def mscale (a : ℝ) (A : Mat3) : Mat3 :=
  ⟨a*A.m00, a*A.m01, a*A.m02,
   a*A.m10, a*A.m11, a*A.m12,
   a*A.m20, a*A.m21, a*A.m22⟩

def ident : Mat3 :=
  ⟨1, 0, 0, 0, 1, 0, 0, 0, 1⟩

def trace (A : Mat3) : ℝ := A.m00 + A.m11 + A.m22
def tr2 (A : Mat3) : ℝ := trace (mm A A)
def tr3 (A : Mat3) : ℝ := trace (mm (mm A A) A)

def det (A : Mat3) : ℝ :=
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

def stf (a b d e f : ℝ) : Mat3 :=
  ⟨a, d, e, d, b, f, e, f, -a-b⟩

def stfQ2 (a b d e f : ℝ) : ℝ :=
  a*a + b*b + a*b + d*d + e*e + f*f

def stfQ3 (a b d e f : ℝ) : ℝ :=
  -a*a*b - a*b*b - a*f*f + d*d*(a+b) + 2*d*e*f - b*e*e

theorem stf_tr2_half (a b d e f : ℝ) :
    tr2 (stf a b d e f) / 2 = stfQ2 a b d e f := by
  simp [tr2, trace, mm, stf, stfQ2]
  ring

theorem stf_tr3_third (a b d e f : ℝ) :
    tr3 (stf a b d e f) / 3 = stfQ3 a b d e f := by
  simp [tr3, trace, mm, stf, stfQ3]
  ring

/-- VT-T6: Cayley-Hamilton over the declared real STF domain. -/
theorem cayleyHamiltonSTF (a b d e f : ℝ) :
    mm (mm (stf a b d e f) (stf a b d e f)) (stf a b d e f)
      =
    madd
      (mscale (tr2 (stf a b d e f) / 2) (stf a b d e f))
      (mscale (tr3 (stf a b d e f) / 3) ident) := by
  rw [stf_tr2_half, stf_tr3_third]
  apply Mat3.extensionality <;>
    simp [stf, mm, madd, mscale, stfQ2, stfQ3, ident] <;> ring

theorem mm_assoc (A B C : Mat3) : mm (mm A B) C = mm A (mm B C) := by
  apply Mat3.extensionality <;> simp [mm] <;> ring

theorem mm_ident_right (A : Mat3) : mm A ident = A := by
  apply Mat3.extensionality <;> simp [mm, ident]

theorem mm_add_right (A B C : Mat3) :
    mm A (madd B C) = madd (mm A B) (mm A C) := by
  apply Mat3.extensionality <;> simp [mm, madd] <;> ring

theorem mm_scale_right (A B : Mat3) (r : ℝ) :
    mm A (mscale r B) = mscale r (mm A B) := by
  apply Mat3.extensionality <;> simp [mm, mscale] <;> ring

def mpow (A : Mat3) : ℕ → Mat3
  | 0 => ident
  | n + 1 => mm (mpow A n) A

theorem mpow_add (A : Mat3) (m n : ℕ) :
    mpow A (m + n) = mm (mpow A m) (mpow A n) := by
  induction n with
  | zero =>
      simp [mpow, mm_ident_right]
  | succ n ih =>
      rw [Nat.add_succ, mpow, ih, mpow, mm_assoc]

theorem mpow_three (A : Mat3) :
    mpow A 3 = mm (mm A A) A := by
  simp [mpow, mm, ident]

/-- VT-T6 contraction reduction for every power, not only one fixture. -/
theorem cayleyHamiltonAllPowers (a b d e f : ℝ) (n : ℕ) :
    mpow (stf a b d e f) (n + 3)
      =
    madd
      (mscale
        (tr2 (stf a b d e f) / 2)
        (mpow (stf a b d e f) (n + 1)))
      (mscale
        (tr3 (stf a b d e f) / 3)
        (mpow (stf a b d e f) n)) := by
  let A := stf a b d e f
  have hCH := cayleyHamiltonSTF a b d e f
  calc
    mpow A (n + 3) = mm (mpow A n) (mpow A 3) := by
      rw [mpow_add]
    _ = mm (mpow A n) (mm (mm A A) A) := by rw [mpow_three]
    _ = mm (mpow A n)
        (madd (mscale (tr2 A / 2) A) (mscale (tr3 A / 3) ident)) := by
          rw [hCH]
    _ = madd
        (mscale (tr2 A / 2) (mpow A (n + 1)))
        (mscale (tr3 A / 3) (mpow A n)) := by
          rw [mm_add_right, mm_scale_right, mm_scale_right]
          simp only [mpow, mm_ident_right]

theorem detSquared_eq_gramDet (u v w : Vec3) :
    det (fromCols u v w) * det (fromCols u v w)
      = det (gramMatrix u v w) := by
  simp [det, fromCols, gramMatrix, dot]
  ring

def lambda3 (l1 l2 : ℝ) : ℝ := -l1-l2

def gapPolynomial (l1 l2 : ℝ) : ℝ :=
  (l1-l2) * (l1+2*l2) * (2*l1+l2)

def shearI2 (l1 l2 : ℝ) : ℝ :=
  l1^2 + l2^2 + (lambda3 l1 l2)^2

def shearI3 (l1 l2 : ℝ) : ℝ :=
  l1^3 + l2^3 + (lambda3 l1 l2)^3

def shearDelta (l1 l2 : ℝ) : ℝ :=
  (shearI2 l1 l2)^3 / 2 - 3 * (shearI3 l1 l2)^2

def shearJ2 (l1 l2 : ℝ) : ℝ :=
  6 * (shearI3 l1 l2)^2 / (shearI2 l1 l2)^3

/-- VT-T5: the characteristic discriminant is the squared Vandermonde. -/
theorem discriminantIdentity (l1 l2 : ℝ) :
    shearDelta l1 l2 = (gapPolynomial l1 l2)^2 := by
  simp [shearDelta, shearI2, shearI3, lambda3, gapPolynomial]
  ring

theorem discriminantNonnegative (l1 l2 : ℝ) :
    0 ≤ shearDelta l1 l2 := by
  rw [discriminantIdentity]
  positivity

/-- The normalized real shape invariant lies in [0,1] whenever I2>0. -/
theorem normalizedShapeBounds (l1 l2 : ℝ)
    (hI2 : 0 < shearI2 l1 l2) :
    0 ≤ shearJ2 l1 l2 ∧ shearJ2 l1 l2 ≤ 1 := by
  have hden : 0 < (shearI2 l1 l2)^3 := pow_pos hI2 3
  have hdisc := discriminantNonnegative l1 l2
  constructor
  · simp [shearJ2]
    positivity
  · rw [shearJ2, div_le_one hden]
    simp [shearDelta] at hdisc
    nlinarith

theorem axisymmetricStratum :
    shearI2 2 (-1) = 6 ∧
    shearI3 2 (-1) = 6 ∧
    shearDelta 2 (-1) = 0 ∧
    shearJ2 2 (-1) = 1 := by
  norm_num [shearI2, shearI3, shearDelta, shearJ2, lambda3]

theorem principalShapeFixture :
    shearI2 (-2) 0 = 8 ∧
    shearI3 (-2) 0 = 0 ∧
    shearDelta (-2) 0 = 256 := by
  norm_num [shearI2, shearI3, shearDelta, lambda3]

def diagAction (l1 l2 : ℝ) (v : Vec3) : Vec3 :=
  ⟨l1*v.x, l2*v.y, (lambda3 l1 l2)*v.z⟩

def krylovDet (l1 l2 : ℝ) (v : Vec3) : ℝ :=
  det (fromCols v (diagAction l1 l2 v)
    (diagAction l1 l2 (diagAction l1 l2 v)))

/-- VT-T7: exact Krylov/Vandermonde factorization. -/
theorem krylovVandermonde (l1 l2 : ℝ) (v : Vec3) :
    krylovDet l1 l2 v =
      -v.x*v.y*v.z*gapPolynomial l1 l2 := by
  cases v
  simp [krylovDet, diagAction, lambda3, gapPolynomial, det, fromCols]
  ring

theorem krylovGram (l1 l2 : ℝ) (v : Vec3) :
    krylovDet l1 l2 v * krylovDet l1 l2 v =
      det (gramMatrix v (diagAction l1 l2 v)
        (diagAction l1 l2 (diagAction l1 l2 v))) := by
  exact detSquared_eq_gramDet _ _ _

/-- Exact simple-spectrum/cyclic-vector criterion, including both boundaries. -/
theorem krylovCyclicIff (l1 l2 : ℝ) (v : Vec3) :
    krylovDet l1 l2 v ≠ 0 ↔
      v.x ≠ 0 ∧ v.y ≠ 0 ∧ v.z ≠ 0 ∧ gapPolynomial l1 l2 ≠ 0 := by
  rw [krylovVandermonde]
  constructor
  · intro h
    refine ⟨?_, ?_, ?_, ?_⟩
    · intro hx
      apply h
      simp [hx]
    · intro hy
      apply h
      simp [hy]
    · intro hz
      apply h
      simp [hz]
    · intro hg
      apply h
      simp [hg]
  · rintro ⟨hx, hy, hz, hg⟩
    exact mul_ne_zero (mul_ne_zero (mul_ne_zero (neg_ne_zero.mpr hx) hy) hz) hg

def principalVector : Vec3 := ⟨1, 1, 1⟩
def noncyclicVector : Vec3 := ⟨1, 0, 1⟩

theorem principalKrylovFixture :
    krylovDet (-2) 0 principalVector = 16 := by
  norm_num [krylovDet, principalVector, diagAction, lambda3, det, fromCols]

theorem principalKrylovGramFixture :
    det (gramMatrix principalVector
      (diagAction (-2) 0 principalVector)
      (diagAction (-2) 0 (diagAction (-2) 0 principalVector))) = 256 := by
  norm_num [principalVector, gramMatrix, diagAction, lambda3, dot, det]

theorem repeatedSpectrumRefusal (v : Vec3) :
    krylovDet 2 (-1) v = 0 := by
  rw [krylovVandermonde]
  norm_num [gapPolynomial]

theorem zeroComponentRefusal :
    krylovDet (-2) 0 noncyclicVector = 0 := by
  norm_num [krylovDet, noncyclicVector, diagAction, lambda3, det, fromCols]

/-!
The registered chart has variables
  (lambda1,lambda2,v0x,v0y,v0z,v1x,...,v3z)
and coordinates
  (I2,I3,m00,m01,m02,m10,...,m32),
where m_jp = v0^T sigma^p vj.

The following five diagonal derivative blocks and four explicit lower blocks
assemble the actual sparse analytic Jacobian.  `Matrix.det_fromBlocks_zero₁₂`
then proves its determinant; the determinant is not introduced as a fitted
product by definition.
-/

def invariantDerivativeBlock (l1 l2 : ℝ) :
    Matrix (Fin 2) (Fin 2) ℝ :=
  !![4*l1 + 2*l2, 2*l1 + 4*l2;
     3*l1^2 - 3*(lambda3 l1 l2)^2,
     3*l2^2 - 3*(lambda3 l1 l2)^2]

def selfMomentDerivativeBlock (l1 l2 a b c : ℝ) :
    Matrix (Fin 3) (Fin 3) ℝ :=
  !![2*a, 2*b, 2*c;
     2*l1*a, 2*l2*b, 2*(lambda3 l1 l2)*c;
     2*l1^2*a, 2*l2^2*b, 2*(lambda3 l1 l2)^2*c]

def momentDerivativeBlock (l1 l2 a b c : ℝ) :
    Matrix (Fin 3) (Fin 3) ℝ :=
  !![a, b, c;
     l1*a, l2*b, (lambda3 l1 l2)*c;
     l1^2*a, l2^2*b, (lambda3 l1 l2)^2*c]

def selfEigenDerivativeBlock (l1 l2 a b c : ℝ) :
    Matrix (Fin 3) (Fin 2) ℝ :=
  !![0, 0;
     a^2-c^2, b^2-c^2;
     2*l1*a^2-2*(lambda3 l1 l2)*c^2,
     2*l2*b^2-2*(lambda3 l1 l2)*c^2]

def crossEigenDerivativeBlock
    (l1 l2 a b c x y z : ℝ) :
    Matrix (Fin 3) (Fin 2) ℝ :=
  !![0, 0;
     a*x-c*z, b*y-c*z;
     2*l1*a*x-2*(lambda3 l1 l2)*c*z,
     2*l2*b*y-2*(lambda3 l1 l2)*c*z]

def crossReferenceDerivativeBlock
    (l1 l2 x y z : ℝ) :
    Matrix (Fin 3) (Fin 3) ℝ :=
  !![x, y, z;
     l1*x, l2*y, (lambda3 l1 l2)*z;
     l1^2*x, l2^2*y, (lambda3 l1 l2)^2*z]

abbrev Chart1 := Fin 2 ⊕ Fin 3
abbrev Chart2 := Chart1 ⊕ Fin 3
abbrev Chart3 := Chart2 ⊕ Fin 3
abbrev Chart4 := Chart3 ⊕ Fin 3

def chartLower1 (l1 l2 a b c x y z : ℝ) :
    Matrix (Fin 3) Chart1 ℝ :=
  fun i j =>
    match j with
    | Sum.inl k => crossEigenDerivativeBlock l1 l2 a b c x y z i k
    | Sum.inr k => crossReferenceDerivativeBlock l1 l2 x y z i k

def chartLower2 (l1 l2 a b c x y z : ℝ) :
    Matrix (Fin 3) Chart2 ℝ :=
  fun i j =>
    match j with
    | Sum.inl k => chartLower1 l1 l2 a b c x y z i k
    | Sum.inr _ => 0

def chartLower3 (l1 l2 a b c x y z : ℝ) :
    Matrix (Fin 3) Chart3 ℝ :=
  fun i j =>
    match j with
    | Sum.inl k => chartLower2 l1 l2 a b c x y z i k
    | Sum.inr _ => 0

def chartJacobian1 (l1 l2 a b c : ℝ) :
    Matrix Chart1 Chart1 ℝ :=
  Matrix.fromBlocks
    (invariantDerivativeBlock l1 l2)
    0
    (selfEigenDerivativeBlock l1 l2 a b c)
    (selfMomentDerivativeBlock l1 l2 a b c)

def chartJacobian2
    (l1 l2 a b c x1 y1 z1 : ℝ) :
    Matrix Chart2 Chart2 ℝ :=
  Matrix.fromBlocks
    (chartJacobian1 l1 l2 a b c)
    0
    (chartLower1 l1 l2 a b c x1 y1 z1)
    (momentDerivativeBlock l1 l2 a b c)

def chartJacobian3
    (l1 l2 a b c x1 y1 z1 x2 y2 z2 : ℝ) :
    Matrix Chart3 Chart3 ℝ :=
  Matrix.fromBlocks
    (chartJacobian2 l1 l2 a b c x1 y1 z1)
    0
    (chartLower2 l1 l2 a b c x2 y2 z2)
    (momentDerivativeBlock l1 l2 a b c)

def localChartJacobian
    (l1 l2 a b c
      x1 y1 z1 x2 y2 z2 x3 y3 z3 : ℝ) :
    Matrix Chart4 Chart4 ℝ :=
  Matrix.fromBlocks
    (chartJacobian3 l1 l2 a b c x1 y1 z1 x2 y2 z2)
    0
    (chartLower3 l1 l2 a b c x3 y3 z3)
    (momentDerivativeBlock l1 l2 a b c)

theorem invariantDerivativeBlockDet (l1 l2 : ℝ) :
    (invariantDerivativeBlock l1 l2).det =
      -6 * gapPolynomial l1 l2 := by
  simp [invariantDerivativeBlock, Matrix.det_fin_two, lambda3, gapPolynomial]
  ring

theorem selfMomentDerivativeBlockDet (l1 l2 a b c : ℝ) :
    (selfMomentDerivativeBlock l1 l2 a b c).det =
      -8*a*b*c*gapPolynomial l1 l2 := by
  simp [selfMomentDerivativeBlock, Matrix.det_fin_three, lambda3,
    gapPolynomial]
  ring

theorem momentDerivativeBlockDet (l1 l2 a b c : ℝ) :
    (momentDerivativeBlock l1 l2 a b c).det =
      -a*b*c*gapPolynomial l1 l2 := by
  simp [momentDerivativeBlock, Matrix.det_fin_three, lambda3, gapPolynomial]
  ring

/-- VT-T8: determinant of the actual 14-coordinate sparse Jacobian. -/
theorem localChartJacobianFactor
    (l1 l2 a b c
      x1 y1 z1 x2 y2 z2 x3 y3 z3 : ℝ) :
    (localChartJacobian l1 l2 a b c
      x1 y1 z1 x2 y2 z2 x3 y3 z3).det =
      -48*a^4*b^4*c^4
        *(l1-l2)^5*(l1+2*l2)^5*(2*l1+l2)^5 := by
  simp only [localChartJacobian, chartJacobian3, chartJacobian2,
    chartJacobian1, Matrix.det_fromBlocks_zero₁₂]
  rw [invariantDerivativeBlockDet, selfMomentDerivativeBlockDet,
    momentDerivativeBlockDet]
  simp [gapPolynomial]
  ring

theorem principalLocalChartJacobian :
    (localChartJacobian (-2) 0 1 1 1
      1 2 4 2 (-1) 3 (-1) 3 2).det = 50331648 := by
  rw [localChartJacobianFactor]
  norm_num

theorem repeatedSpectrumLocalChartRefusal
    (a b c x1 y1 z1 x2 y2 z2 x3 y3 z3 : ℝ) :
    (localChartJacobian 2 (-1) a b c
      x1 y1 z1 x2 y2 z2 x3 y3 z3).det = 0 := by
  rw [localChartJacobianFactor]
  ring

theorem noncyclicLocalChartRefusal
    (l1 l2 b c x1 y1 z1 x2 y2 z2 x3 y3 z3 : ℝ) :
    (localChartJacobian l1 l2 0 b c
      x1 y1 z1 x2 y2 z2 x3 y3 z3).det = 0 := by
  rw [localChartJacobianFactor]
  ring

/-- Cleared quotient-rule numerator for d(6 I3^2 / I2^3). -/
theorem shapeChainRuleNumerator
    (q2 q3 dq2 dq3 : ℝ) :
    (12*q3*dq3)*q2^3 - (6*q3^2)*(3*q2^2*dq2)
      =
    q2^2 * (12*q2*q3*dq3 - 18*q3^2*dq2) := by
  ring

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

/-- One typed object binds every emitted boolean to a compiled theorem. -/
structure AxisProofBundle : Prop where
  vtT5Discriminant :
    ∀ l1 l2 : ℝ, shearDelta l1 l2 = (gapPolynomial l1 l2)^2
  vtT5ShapeBounds :
    ∀ l1 l2 : ℝ, 0 < shearI2 l1 l2 →
      0 ≤ shearJ2 l1 l2 ∧ shearJ2 l1 l2 ≤ 1
  vtT5Axisymmetric : shearJ2 2 (-1) = 1
  vtT6CayleyHamilton :
    ∀ a b d e f : ℝ,
      mm (mm (stf a b d e f) (stf a b d e f)) (stf a b d e f)
        =
      madd
        (mscale (tr2 (stf a b d e f) / 2) (stf a b d e f))
        (mscale (tr3 (stf a b d e f) / 3) ident)
  vtT6AllPowers :
    ∀ (a b d e f : ℝ) (n : ℕ),
      mpow (stf a b d e f) (n + 3)
        =
      madd
        (mscale (tr2 (stf a b d e f) / 2)
          (mpow (stf a b d e f) (n + 1)))
        (mscale (tr3 (stf a b d e f) / 3)
          (mpow (stf a b d e f) n))
  vtT7Vandermonde :
    ∀ (l1 l2 : ℝ) (v : Vec3),
      krylovDet l1 l2 v = -v.x*v.y*v.z*gapPolynomial l1 l2
  vtT7Gram :
    ∀ (l1 l2 : ℝ) (v : Vec3),
      krylovDet l1 l2 v * krylovDet l1 l2 v =
        det (gramMatrix v (diagAction l1 l2 v)
          (diagAction l1 l2 (diagAction l1 l2 v)))
  vtT7Cyclicity :
    ∀ (l1 l2 : ℝ) (v : Vec3),
      krylovDet l1 l2 v ≠ 0 ↔
        v.x ≠ 0 ∧ v.y ≠ 0 ∧ v.z ≠ 0 ∧ gapPolynomial l1 l2 ≠ 0
  vtT8Jacobian :
    ∀ l1 l2 a b c x1 y1 z1 x2 y2 z2 x3 y3 z3 : ℝ,
      (localChartJacobian l1 l2 a b c
        x1 y1 z1 x2 y2 z2 x3 y3 z3).det =
        -48*a^4*b^4*c^4
          *(l1-l2)^5*(l1+2*l2)^5*(2*l1+l2)^5
  vtT8Principal :
    (localChartJacobian (-2) 0 1 1 1
      1 2 4 2 (-1) 3 (-1) 3 2).det = 50331648
  vtT8NoGlobalPromotion : globalOrbitStatus = .unproven
  vtT13ChainRule :
    ∀ q2 q3 dq2 dq3 : ℝ,
      (12*q3*dq3)*q2^3 - (6*q3^2)*(3*q2^2*dq2)
        =
      q2^2 * (12*q2*q3*dq3 - 18*q3^2*dq2)
  vtT13NoSourcePromotion :
    sourceDecompositionStatus =
      .inconclusiveMissingTypedEvolutionLaw

def axisProofBundle : AxisProofBundle where
  vtT5Discriminant := discriminantIdentity
  vtT5ShapeBounds := normalizedShapeBounds
  vtT5Axisymmetric := axisymmetricStratum.2.2.2
  vtT6CayleyHamilton := cayleyHamiltonSTF
  vtT6AllPowers := cayleyHamiltonAllPowers
  vtT7Vandermonde := krylovVandermonde
  vtT7Gram := krylovGram
  vtT7Cyclicity := krylovCyclicIff
  vtT8Jacobian := localChartJacobianFactor
  vtT8Principal := principalLocalChartJacobian
  vtT8NoGlobalPromotion := globalSeparationNotPromoted
  vtT13ChainRule := shapeChainRuleNumerator
  vtT13NoSourcePromotion := sourceDecompositionNotPromoted

#check axisProofBundle

end

end PR270PillarT
