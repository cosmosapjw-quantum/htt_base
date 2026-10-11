import Mathlib
import BoostedKernelMembership

/-! Exact kernel-span bridge only. No normalization, rank, or admission claim. -/
namespace G03BBoostedKernelSpan

open G03BBoostedKernelMembership
open scoped BigOperators Matrix

theorem boostedB_mulVec_eq_zero_iff (epsilon chi b2 b3 : Real)
    (he : 0 < epsilon) (h2 : 0 < b2) (h3 : 0 < b3) (v : FourVector) :
    (boostedB epsilon chi b2 b3).mulVec v = 0 ↔ ∃ t : Real, v = t • uChi chi := by
  constructor
  · intro hv
    have hrow1 := congrFun hv (1 : Fin 4)
    have hrow2 := congrFun hv (2 : Fin 4)
    have hrow3 := congrFun hv (3 : Fin 4)
    simp [boostedB, covOuter, rflat, e2flat, e3flat,
      Matrix.mulVec, dotProduct, Fin.sum_univ_succ] at hrow1 hrow2 hrow3
    have hc : Real.cosh chi ≠ 0 := ne_of_gt (Real.cosh_pos chi)
    have he' : epsilon ≠ 0 := ne_of_gt he
    have hv2 : v 2 = 0 := hrow2.resolve_left (ne_of_gt h2)
    have hv3 : v 3 = 0 := hrow3.resolve_left (ne_of_gt h3)
    have hr : -Real.sinh chi * v 0 + Real.cosh chi * v 1 = 0 := by
      have hx : epsilon * Real.cosh chi *
          (-Real.sinh chi * v 0 + Real.cosh chi * v 1) = 0 := by
        nlinarith [hrow1]
      exact (mul_eq_zero.mp hx).resolve_left (mul_ne_zero he' hc)
    refine ⟨v 0 / Real.cosh chi, ?_⟩
    funext i
    fin_cases i
    · simp [uChi, hc]
    · simp [uChi, Pi.smul_apply, smul_eq_mul]
      field_simp
      nlinarith [hr]
    · simp [uChi, hv2]
    · simp [uChi, hv3]
  · rintro ⟨t, rfl⟩
    rw [Matrix.mulVec_smul, boostedB_mulVec_uChi_zero]
    simp

end G03BBoostedKernelSpan

#print axioms G03BBoostedKernelSpan.boostedB_mulVec_eq_zero_iff
