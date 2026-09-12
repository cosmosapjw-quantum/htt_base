import Mathlib

/- Host-authored supporting algebra. This is not a formalization of generic
probability coverage, the radiation hierarchy, or production Python code. -/
namespace R8D
theorem p1_s (t q g d : ℝ) (ht : t ≠ 0) :
    (-q+g+3*d/7)/t = -q/t+g/t+3*d/(7*t) := by
  field_simp
  <;> ring
theorem p1_w (t cd c e : ℝ) (ht : t ≠ 0) :
    (3*cd/t+c-6*e/(5*t))/t = 3*cd/t^2+c/t-6*e/(5*t^2) := by
  field_simp
  <;> ring
theorem fixture_norms : (1:ℚ)^2+2^2+1^2+2^2+1^2+2^2+1^2+2^2=20 := by norm_num
theorem allocation : (1:ℚ)-4*(1/80)=19/20 := by norm_num
theorem sets (a b c : Prop) : (a ∧ (b ∨ c)) ↔ ((a ∧ b) ∨ (a ∧ c)) := by tauto
def v : Fin 8 → ℚ := ![0,0,0,0,0,0,0,1]
theorem ray_fixture : v 0=0 ∧ v 1=0 ∧ v 2=0 ∧ v 3=0 ∧ v 7=1 := by norm_num [v]
theorem ray_preserves (rx rv t : ℝ) (h : rv=0) : rx+t*rv=rx := by simp [h]
theorem constraint_ray (ax av b t : ℝ) (hx : ax≤b) (hv : av≤0) (ht : 0≤t) : ax+t*av≤b := by
  have : t*av≤0 := mul_nonpos_of_nonneg_of_nonpos ht hv
  linarith
theorem support_upper (c z rem rho n hrem : ℝ) (hz : z≤rho*n) (hr : rem≤hrem) :
    c+z+rem≤c+rho*n+hrem := by linarith
theorem support_attained (c rho n hrem : ℝ) : c+rho*n+hrem=c+rho*n+hrem := rfl
#print axioms p1_s
#print axioms p1_w
#print axioms fixture_norms
#print axioms allocation
#print axioms sets
#print axioms ray_fixture
#print axioms ray_preserves
#print axioms constraint_ray
#print axioms support_upper
end R8D
