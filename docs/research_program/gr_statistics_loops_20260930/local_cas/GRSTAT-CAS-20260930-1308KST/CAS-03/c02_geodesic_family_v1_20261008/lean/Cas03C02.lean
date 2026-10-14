import Mathlib

/-!
# CAS-03-C02 exact geodesic-family component

This file formalizes only the frozen finite/local component.  It proves the
exact family difference over `ℝ` and the complete `χ = 0` diagonal kernel
stratification.  It makes no eigenfield, implicit-function, or scientific
claim.
-/

namespace Cas03C02

open scoped Matrix

noncomputable def radialEvaluation (chi n1 : ℝ) : ℝ :=
  Real.sinh chi + Real.cosh chi * n1

noncomputable def familyEvaluation (epsilon b2 b3 chi n1 n2 n3 : ℝ) : ℝ :=
  epsilon * radialEvaluation chi n1 ^ 2 + b2 * n2 ^ 2 + b3 * n3 ^ 2

theorem exact_family_difference
    (epsilon b2 b3 chi n1 n2 n3 : ℝ) :
    familyEvaluation epsilon b2 b3 chi n1 n2 n3 -
        familyEvaluation epsilon b2 b3 0 n1 n2 n3 =
      epsilon *
        (Real.sinh chi ^ 2 +
          2 * Real.sinh chi * Real.cosh chi * n1 +
          Real.sinh chi ^ 2 * n1 ^ 2) := by
  simp [familyEvaluation, radialEvaluation]
  ring_nf
  rw [show Real.cosh chi ^ 2 = 1 + Real.sinh chi ^ 2 by
    nlinarith [Real.cosh_sq_sub_sinh_sq chi]]
  ring

abbrev RestVector := Fin 3 → ℝ

def restCoefficients (epsilon b2 b3 : ℝ) : Fin 3 → ℝ :=
  ![epsilon, b2, b3]

def restBlock (epsilon b2 b3 : ℝ) : Matrix (Fin 3) (Fin 3) ℝ :=
  Matrix.diagonal (restCoefficients epsilon b2 b3)

def restAction (epsilon b2 b3 : ℝ) : RestVector →ₗ[ℝ] RestVector :=
  (restBlock epsilon b2 b3).mulVecLin

noncomputable def zeroCount (epsilon b2 b3 : ℝ) : ℕ :=
  Fintype.card {i : Fin 3 // restCoefficients epsilon b2 b3 i = 0}

theorem rest_action_apply (epsilon b2 b3 : ℝ) (v : RestVector) :
    restAction epsilon b2 b3 v =
      ![epsilon * v 0, b2 * v 1, b3 * v 2] := by
  funext i
  fin_cases i <;>
    simp [restAction, restBlock, restCoefficients, Matrix.mulVec_diagonal]

theorem mem_kernel_iff_zero_mask (epsilon b2 b3 : ℝ) (v : RestVector) :
    v ∈ LinearMap.ker (restAction epsilon b2 b3) ↔
      (epsilon = 0 ∨ v 0 = 0) ∧
      (b2 = 0 ∨ v 1 = 0) ∧
      (b3 = 0 ∨ v 2 = 0) := by
  rw [LinearMap.mem_ker]
  rw [rest_action_apply]
  constructor
  · intro h
    constructor
    · simpa [mul_eq_zero] using congrFun h 0
    constructor
    · simpa [mul_eq_zero] using congrFun h 1
    · simpa [mul_eq_zero] using congrFun h 2
  · rintro ⟨h0, h1, h2⟩
    funext i
    fin_cases i <;> simp_all

theorem kernel_finrank_eq_zeroCount (epsilon b2 b3 : ℝ) :
    Module.finrank ℝ (LinearMap.ker (restAction epsilon b2 b3)) =
      zeroCount epsilon b2 b3 := by
  have hnull :=
    LinearMap.finrank_range_add_finrank_ker (restAction epsilon b2 b3)
  have hrank :
      Module.finrank ℝ (LinearMap.range (restAction epsilon b2 b3)) =
        Fintype.card {i // restCoefficients epsilon b2 b3 i ≠ 0} := by
    change (restBlock epsilon b2 b3).rank = _
    exact Matrix.rank_diagonal (restCoefficients epsilon b2 b3)
  rw [hrank] at hnull
  have hpartition :=
    Fintype.card_subtype_compl
      (fun i : Fin 3 => restCoefficients epsilon b2 b3 i ≠ 0)
  simp only [not_ne_iff, Fintype.card_fin] at hpartition
  have hdim : Module.finrank ℝ RestVector = 3 := by
    simp [RestVector]
  rw [hdim] at hnull
  unfold zeroCount
  omega

theorem kernel_finrank_all_zero :
    Module.finrank ℝ (LinearMap.ker (restAction 0 0 0)) = 3 := by
  rw [kernel_finrank_eq_zeroCount]
  have hc : restCoefficients 0 0 0 = fun _ => 0 := by
    funext i
    fin_cases i <;> rfl
  simp [zeroCount, hc]

theorem kernel_finrank_repeated_nonzero (a : ℝ) (ha : a ≠ 0) :
    Module.finrank ℝ (LinearMap.ker (restAction a a a)) = 0 := by
  rw [kernel_finrank_eq_zeroCount]
  have hc : restCoefficients a a a = fun _ => a := by
    funext i
    fin_cases i <;> rfl
  simp [zeroCount, hc, ha]

theorem kernel_finrank_repeated_nonzero_with_zero (a : ℝ) (ha : a ≠ 0) :
    Module.finrank ℝ (LinearMap.ker (restAction a a 0)) = 1 := by
  rw [kernel_finrank_eq_zeroCount]
  have hp :
      (fun i : Fin 3 => restCoefficients a a 0 i = 0) = (fun i => i = 2) := by
    funext i
    apply propext
    fin_cases i <;> simp [restCoefficients, ha]
  simp [zeroCount, hp]

end Cas03C02

#print axioms Cas03C02.exact_family_difference
#print axioms Cas03C02.rest_action_apply
#print axioms Cas03C02.mem_kernel_iff_zero_mask
#print axioms Cas03C02.kernel_finrank_eq_zeroCount
#print axioms Cas03C02.kernel_finrank_all_zero
#print axioms Cas03C02.kernel_finrank_repeated_nonzero
#print axioms Cas03C02.kernel_finrank_repeated_nonzero_with_zero
