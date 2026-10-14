import Mathlib

/- CAS_CONTRACT.json bc45fb9: finite-measure interval and fixed depth transform. -/
theorem cas07_finite_undefined_interval
    (known undefined exceed : ℝ) (h₁ : 0 ≤ exceed)
    (h₂ : exceed ≤ undefined) :
    known ≤ known + exceed ∧ known + exceed ≤ known + undefined := by
  constructor <;> linarith

def depthTransform (x₀ x₁ x₂ : ℝ) : ℝ × ℝ × ℝ :=
  (x₀, x₁ - x₀, x₂ - x₁)

def depthInverse (y₀ y₁ y₂ : ℝ) : ℝ × ℝ × ℝ :=
  (y₀, y₀ + y₁, y₀ + y₁ + y₂)

theorem cas09_depth_inverse (x₀ x₁ x₂ : ℝ) :
    depthInverse (depthTransform x₀ x₁ x₂).1
      (depthTransform x₀ x₁ x₂).2.1
      (depthTransform x₀ x₁ x₂).2.2 = (x₀, x₁, x₂) := by
  simp [depthTransform, depthInverse]

#print axioms cas07_finite_undefined_interval
#print axioms cas09_depth_inverse
