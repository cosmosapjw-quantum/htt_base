import Mathlib

/-!
# G03-B: finite covariant boosted-kernel membership

This file formalizes only the finite covariant statement delegated in
`DELEGATION_PACKET.json`.  The matrix is the source equation-(26) boosted
family with covectors represented in the displayed `Fin 4` coordinates.  It
proves that the displayed boosted vector is in the right kernel.  It contains
no uniqueness, rank, or scientific-admission claim.
-/

namespace G03BBoostedKernelMembership

open scoped BigOperators Matrix

abbrev FourVector := Fin 4 -> ℝ
abbrev FourMatrix := Matrix (Fin 4) (Fin 4) ℝ

/-- The covector `(-sinh χ, cosh χ, 0, 0)`. -/
noncomputable def rflat (chi : ℝ) : FourVector :=
  ![-Real.sinh chi, Real.cosh chi, 0, 0]

/-- The second spatial coordinate covector. -/
def e2flat : FourVector := ![0, 0, 1, 0]

/-- The third spatial coordinate covector. -/
def e3flat : FourVector := ![0, 0, 0, 1]

/-- The boosted vector `(cosh χ, sinh χ, 0, 0)`. -/
noncomputable def uChi (chi : ℝ) : FourVector :=
  ![Real.cosh chi, Real.sinh chi, 0, 0]

/-- Covariant outer product, with both displayed factors treated as covectors. -/
def covOuter (x y : FourVector) : FourMatrix := fun i j => x i * y j

/-- Multiplying a finite covariant outer product applies its second factor. -/
theorem covOuter_mulVec_apply (x y u : FourVector) (i : Fin 4) :
    (covOuter x y).mulVec u i = x i * ∑ j : Fin 4, y j * u j := by
  simp only [Matrix.mulVec, dotProduct, covOuter]
  rw [Finset.mul_sum]
  apply Finset.sum_congr rfl
  intro j _
  ring

/--
The covariant boosted family from the delegated source binding:
`ε r♭⊗r♭ + b₂ e²♭⊗e²♭ + b₃ e³♭⊗e³♭`.
-/
noncomputable def boostedB (epsilon chi b2 b3 : ℝ) : FourMatrix :=
  epsilon • covOuter (rflat chi) (rflat chi) +
    b2 • covOuter e2flat e2flat +
    b3 • covOuter e3flat e3flat

/-- The radial covector annihilates the boosted vector. -/
theorem rflat_apply_uChi (chi : ℝ) :
    ∑ j : Fin 4, rflat chi j * uChi chi j = 0 := by
  simp [rflat, uChi, Fin.sum_univ_succ]
  ring

/-- The second spatial covector annihilates the boosted vector. -/
theorem e2flat_apply_uChi (chi : ℝ) :
    ∑ j : Fin 4, e2flat j * uChi chi j = 0 := by
  simp [e2flat, uChi, Fin.sum_univ_succ]

/-- The third spatial covector annihilates the boosted vector. -/
theorem e3flat_apply_uChi (chi : ℝ) :
    ∑ j : Fin 4, e3flat j * uChi chi j = 0 := by
  simp [e3flat, uChi, Fin.sum_univ_succ]

/-- Exact finite covariant kernel membership for all real parameters. -/
theorem boostedB_mulVec_uChi_zero (epsilon chi b2 b3 : ℝ) :
    (boostedB epsilon chi b2 b3).mulVec (uChi chi) = 0 := by
  funext i
  unfold boostedB
  rw [Matrix.add_mulVec, Matrix.add_mulVec,
    Matrix.smul_mulVec, Matrix.smul_mulVec, Matrix.smul_mulVec]
  simp only [Pi.add_apply, Pi.smul_apply, Pi.zero_apply, smul_eq_mul]
  rw [covOuter_mulVec_apply, covOuter_mulVec_apply, covOuter_mulVec_apply]
  rw [rflat_apply_uChi, e2flat_apply_uChi, e3flat_apply_uChi]
  ring

end G03BBoostedKernelMembership

#print axioms G03BBoostedKernelMembership.rflat_apply_uChi
#print axioms G03BBoostedKernelMembership.e2flat_apply_uChi
#print axioms G03BBoostedKernelMembership.e3flat_apply_uChi
#print axioms G03BBoostedKernelMembership.boostedB_mulVec_uChi_zero
