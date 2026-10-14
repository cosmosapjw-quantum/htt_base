import Mathlib
import Cas03C02

/-!
# Fixed-chi countersequence for CAS-03-C02

This is only the fixed-positive-`chi` limiting statement inherited from the
frozen exact C02 family identity. It does not assert a uniform modulus or any
scientific conclusion.
-/

namespace Cas03FixedChiCountersequence

open Filter Topology

noncomputable def boostedVelocity (chi : ℝ) : Fin 4 → ℝ :=
  ![Real.cosh chi, Real.sinh chi, 0, 0]

def restVelocity : Fin 4 → ℝ :=
  ![1, 0, 0, 0]

theorem family_difference_tendsto_zero
    (chi n1 n2 n3 b2 b3 : ℝ) :
    Tendsto
      (fun epsilon =>
        Cas03C02.familyEvaluation epsilon b2 b3 chi n1 n2 n3 -
          Cas03C02.familyEvaluation epsilon b2 b3 0 n1 n2 n3)
      (𝓝 0) (𝓝 0) := by
  let c : ℝ :=
    Real.sinh chi ^ 2 +
      2 * Real.sinh chi * Real.cosh chi * n1 +
      Real.sinh chi ^ 2 * n1 ^ 2
  have hrewrite :
      (fun epsilon : ℝ =>
        Cas03C02.familyEvaluation epsilon b2 b3 chi n1 n2 n3 -
          Cas03C02.familyEvaluation epsilon b2 b3 0 n1 n2 n3) =
        fun epsilon => epsilon * c := by
    funext epsilon
    simpa [c] using
      Cas03C02.exact_family_difference epsilon b2 b3 chi n1 n2 n3
  rw [hrewrite]
  simpa [mul_comm] using (tendsto_id.const_mul c :
    Tendsto (fun epsilon : ℝ => c * epsilon) (𝓝 0) (𝓝 (c * 0)))

theorem boosted_velocity_ne_rest (chi : ℝ) (hchi : 0 < chi) :
    boostedVelocity chi ≠ restVelocity := by
  intro h
  have hsinh : Real.sinh chi = 0 := by
    have hcomponent := congrFun h 1
    simpa [boostedVelocity, restVelocity] using hcomponent
  exact (ne_of_gt (Real.sinh_pos_iff.mpr hchi)) hsinh

theorem fixed_chi_countersequence
    (chi n1 n2 n3 b2 b3 : ℝ) (hchi : 0 < chi) :
    Tendsto
      (fun epsilon =>
        Cas03C02.familyEvaluation epsilon b2 b3 chi n1 n2 n3 -
          Cas03C02.familyEvaluation epsilon b2 b3 0 n1 n2 n3)
      (𝓝 0) (𝓝 0) ∧
      boostedVelocity chi ≠ restVelocity :=
  ⟨family_difference_tendsto_zero chi n1 n2 n3 b2 b3,
    boosted_velocity_ne_rest chi hchi⟩

#print axioms family_difference_tendsto_zero
#print axioms boosted_velocity_ne_rest
#print axioms fixed_chi_countersequence

end Cas03FixedChiCountersequence
