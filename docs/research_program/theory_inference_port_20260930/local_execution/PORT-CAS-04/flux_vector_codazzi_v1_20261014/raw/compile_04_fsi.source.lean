import Mathlib

namespace PORTCAS04FluxScalarInverse

noncomputable def betaOfRatio (r : ℝ) : ℝ := 2 * r / (1 + Real.sqrt (1 + 4 * r ^ 2))

theorem flux_denominator_pos (b : ℝ) (hb0 : 0 ≤ b) (hb1 : b < 1) :
    0 < 1 - b ^ 2 := by
  have hp : 0 < (1 - b) * (1 + b) := mul_pos (by linarith) (by linarith)
  nlinarith

theorem flux_sqrt (b : ℝ) (hb0 : 0 ≤ b) (hb1 : b < 1) :
    Real.sqrt (1 + 4 * (b / (1 - b ^ 2)) ^ 2) =
      (1 + b ^ 2) / (1 - b ^ 2) := by
  have hd := flux_denominator_pos b hb0 hb1
  apply (Real.sqrt_eq_iff_eq_sq (by positivity) (by positivity)).mpr
  field_simp
  ring

theorem betaOfRatio_flux (b : ℝ) (hb0 : 0 ≤ b) (hb1 : b < 1) :
    betaOfRatio (b / (1 - b ^ 2)) = b := by
  have hd := flux_denominator_pos b hb0 hb1
  unfold betaOfRatio
  rw [flux_sqrt b hb0 hb1]
  have he : 1 + (1 + b ^ 2) / (1 - b ^ 2) = 2 / (1 - b ^ 2) := by
    field_simp
    ring
  rw [he]
  field_simp

end PORTCAS04FluxScalarInverse

#print axioms PORTCAS04FluxScalarInverse.flux_denominator_pos
#print axioms PORTCAS04FluxScalarInverse.flux_sqrt
#print axioms PORTCAS04FluxScalarInverse.betaOfRatio_flux
