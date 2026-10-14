import Mathlib

namespace PORTCAS03VelocityJetRest

/-- Finite velocity-jet contraction, with the physical `c²` scaling explicit. -/
def physicalAcceleration (u : Fin 4 → ℝ) (D : Matrix (Fin 4) (Fin 4) ℝ)
    (c : ℝ) (j : Fin 4) : ℝ :=
  c ^ 2 * ∑ i, u i * D i j

theorem physicalAcceleration_scaling (u : Fin 4 → ℝ)
    (D : Matrix (Fin 4) (Fin 4) ℝ) (c : ℝ) (j : Fin 4) :
    physicalAcceleration u D c j = c ^ 2 * ∑ i, u i * D i j := rfl

/-- The stated row-wise finite rest condition implies the contracted acceleration
is orthogonal to `u` in precisely the scalar contraction appearing below. -/
theorem rest_acceleration (u : Fin 4 → ℝ) (D : Matrix (Fin 4) (Fin 4) ℝ)
    (c : ℝ) (hDu : ∀ i, ∑ j, D i j * u j = 0) :
    ∑ j, u j * physicalAcceleration u D c j = 0 := by
  calc
    ∑ j, u j * physicalAcceleration u D c j =
        c ^ 2 * ∑ i, u i * (∑ j, D i j * u j) := by
      simp_rw [physicalAcceleration, Finset.mul_sum]
      rw [Finset.sum_comm]
      apply Finset.sum_congr rfl
      intro i hi
      apply Finset.sum_congr rfl
      intro j hj
      ring
    _ = 0 := by simp [hDu]

end PORTCAS03VelocityJetRest

#print axioms PORTCAS03VelocityJetRest.physicalAcceleration_scaling
#print axioms PORTCAS03VelocityJetRest.rest_acceleration
