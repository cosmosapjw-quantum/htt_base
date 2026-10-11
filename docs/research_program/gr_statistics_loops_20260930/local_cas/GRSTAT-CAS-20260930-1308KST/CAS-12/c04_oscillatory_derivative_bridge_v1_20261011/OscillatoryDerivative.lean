import Mathlib

/-!
Pointwise calculus and linear moment algebra for CAS12-C04.
No compact moment-orthogonal function is constructed here. Theorems contain no
integral, no exchange of differentiation and integration, and no norm bound.
-/

namespace CAS12C04

/-- Chain rule for the real oscillation at any real frequency. -/
theorem hasDerivAt_sin_frequency (n x : ℝ) :
    HasDerivAt (fun t : ℝ => Real.sin (n * t)) (n * Real.cos (n * x)) x := by
  convert (hasDerivAt_const_mul n (x := x)).sin using 1
  ring

/-- The product rule retains the derivative of q; q need not be constant. -/
theorem hasDerivAt_oscillatory_perturbation
    (g q : ℝ → ℝ) (g' q' a n x : ℝ)
    (hg : HasDerivAt g g' x) (hq : HasDerivAt q q' x) :
    HasDerivAt (fun t => g t + a * Real.sin (n * t) * q t)
      (g' + a * n * Real.cos (n * x) * q x + a * Real.sin (n * x) * q') x := by
  have h := hg.add (((hasDerivAt_sin_frequency n x).const_mul a).mul hq)
  convert h using 1 <;> first | rfl | ring

/-- The constant-q specialization matches the local algebraic witness. -/
theorem hasDerivAt_constant_q
    (g : ℝ → ℝ) (g' a n q x : ℝ) (hg : HasDerivAt g g' x) :
    HasDerivAt (fun t => g t + a * Real.sin (n * t) * q)
      (g' + a * n * Real.cos (n * x) * q) x := by
  simpa using hasDerivAt_oscillatory_perturbation g (fun _ => q) g' 0 a n x
    hg (hasDerivAt_const x q)

section LinearMoment

variable {V : Type*} [AddCommGroup V] [Module ℝ V]

/-- A linear moment annihilator is closed under every real scalar. -/
theorem moment_scalar_annihilation (M : V →ₗ[ℝ] ℝ) (q : V)
    (hq : M q = 0) (s : ℝ) : M (s • q) = 0 := by
  simp only [map_smul, hq, smul_zero]

/-- Scalar oscillations therefore retain the same zero moment. -/
theorem moment_oscillatory_annihilation (M : V →ₗ[ℝ] ℝ) (q : V)
    (hq : M q = 0) (a n x : ℝ) : M ((a * Real.sin (n * x)) • q) = 0 := by
  exact moment_scalar_annihilation M q hq _

/-- Adding the annihilated oscillatory perturbation preserves the base moment. -/
theorem moment_oscillatory_preservation (M : V →ₗ[ℝ] ℝ) (g q : V)
    (hq : M q = 0) (a n x : ℝ) :
    M (g + (a * Real.sin (n * x)) • q) = M g := by
  rw [map_add, moment_oscillatory_annihilation M q hq a n x, add_zero]

end LinearMoment
end CAS12C04

#print axioms CAS12C04.hasDerivAt_sin_frequency
#print axioms CAS12C04.hasDerivAt_oscillatory_perturbation
#print axioms CAS12C04.hasDerivAt_constant_q
#print axioms CAS12C04.moment_scalar_annihilation
#print axioms CAS12C04.moment_oscillatory_annihilation
#print axioms CAS12C04.moment_oscillatory_preservation
