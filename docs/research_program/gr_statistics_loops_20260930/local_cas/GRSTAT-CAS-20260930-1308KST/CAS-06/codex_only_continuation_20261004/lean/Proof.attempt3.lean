import Mathlib

/-! Scalar calculus subtarget for the frozen C03 contract. The real power uses
    mathlib's positive-real branch, explicitly identified below. -/

namespace CAS06Scalar
noncomputable section

def exponent (alpha : ℝ) : ℝ := (1 + alpha) / (2 * alpha)
def pressure (Pstar s : ℝ) (x : ℝ) : ℝ := Pstar * x ^ s
def first (Pstar s : ℝ) (x : ℝ) : ℝ := Pstar * s * x ^ (s - 1)
def second (Pstar s : ℝ) (x : ℝ) : ℝ := Pstar * s * (s - 1) * x ^ (s - 2)
def energy (Pstar s : ℝ) (x : ℝ) : ℝ := 2 * x * first Pstar s x - pressure Pstar s x
def denominator (Pstar s : ℝ) (x : ℝ) : ℝ :=
  first Pstar s x + 2 * x * second Pstar s x

theorem positive_branch (x s : ℝ) (hx : 0 < x) :
    x ^ s = Real.exp (s * Real.log x) := by
  rw [Real.rpow_def_of_pos hx]
  congr 1
  ring

theorem pressure_hasDerivAt (Pstar s x : ℝ) (hx : 0 < x) :
    HasDerivAt (pressure Pstar s) (first Pstar s x) x := by
  change HasDerivAt (fun y : ℝ => Pstar * y ^ s) (Pstar * s * x ^ (s - 1)) x
  convert (Real.hasDerivAt_rpow_const (p := s) (Or.inl hx.ne')).const_mul Pstar using 1 <;> ring

theorem first_hasDerivAt (Pstar s x : ℝ) (hx : 0 < x) :
    HasDerivAt (first Pstar s) (second Pstar s x) x := by
  change HasDerivAt (fun y : ℝ => Pstar * s * y ^ (s - 1))
    (Pstar * s * (s - 1) * x ^ (s - 2)) x
  convert (Real.hasDerivAt_rpow_const (p := s - 1) (Or.inl hx.ne')).const_mul (Pstar * s) using 1 <;> ring

theorem pressure_deriv (Pstar s x : ℝ) (hx : 0 < x) :
    deriv (pressure Pstar s) x = first Pstar s x :=
  (pressure_hasDerivAt Pstar s x hx).deriv

theorem first_deriv (Pstar s x : ℝ) (hx : 0 < x) :
    deriv (first Pstar s) x = second Pstar s x :=
  (first_hasDerivAt Pstar s x hx).deriv

private theorem shift_one (s x : ℝ) (hx : 0 < x) :
    x * x ^ (s - 1) = x ^ s := by
  have h : x ^ s = x ^ (s - 1) * x := by
    calc
      x ^ s = x ^ ((s - 1) + 1) := by congr 1; ring
      _ = x ^ (s - 1) * x := Real.rpow_add_one hx.ne' _
  rw [h]
  ring

private theorem shift_two (s x : ℝ) (hx : 0 < x) :
    x * x ^ (s - 2) = x ^ (s - 1) := by
  have h : x ^ (s - 1) = x ^ (s - 2) * x := by
    calc
      x ^ (s - 1) = x ^ ((s - 2) + 1) := by congr 1; ring
      _ = x ^ (s - 2) * x := Real.rpow_add_one hx.ne' _
  rw [h]
  ring

theorem energy_identity (Pstar s x : ℝ) (hx : 0 < x) :
    energy Pstar s x = (2 * s - 1) * pressure Pstar s x := by
  unfold energy first pressure
  linear_combination (2 * Pstar * s) * (shift_one s x hx)

theorem denominator_factor (Pstar s x : ℝ) (hx : 0 < x) :
    denominator Pstar s x = Pstar * s * x ^ (s - 1) * (2 * s - 1) := by
  unfold denominator first second
  linear_combination (2 * Pstar * s * (s - 1)) * (shift_two s x hx)

theorem exponent_pos (alpha : ℝ) (ha : 0 < alpha) :
    0 < exponent alpha := by
  unfold exponent
  positivity

theorem exponent_gap_pos (alpha : ℝ) (ha : 0 < alpha) :
    0 < 2 * exponent alpha - 1 := by
  unfold exponent
  have hne : alpha ≠ 0 := ne_of_gt ha
  apply (div_pos (by norm_num : (0 : ℝ) < 1) ha).trans_eq
  field_simp
  ring

theorem denominator_pos (Pstar alpha x : ℝ)
    (hP : 0 < Pstar) (hx : 0 < x) (ha : 0 < alpha) (_ha1 : alpha < 1) :
    0 < denominator Pstar (exponent alpha) x := by
  rw [denominator_factor Pstar (exponent alpha) x hx]
  exact mul_pos (mul_pos (mul_pos hP (exponent_pos alpha ha))
    (Real.rpow_pos_of_pos hx _)) (exponent_gap_pos alpha ha)

theorem ratio_identity (Pstar alpha x : ℝ)
    (hP : 0 < Pstar) (hx : 0 < x) (ha : 0 < alpha) (_ha1 : alpha < 1) :
    first Pstar (exponent alpha) x /
      denominator Pstar (exponent alpha) x = alpha := by
  rw [denominator_factor Pstar (exponent alpha) x hx]
  unfold first exponent
  have hPn : Pstar ≠ 0 := ne_of_gt hP
  have hxn : x ^ ((1 + alpha) / (2 * alpha) - 1) ≠ 0 :=
    ne_of_gt (Real.rpow_pos_of_pos hx _)
  have han : alpha ≠ 0 := ne_of_gt ha
  field_simp
  ring

#print axioms positive_branch
#print axioms pressure_hasDerivAt
#print axioms first_hasDerivAt
#print axioms pressure_deriv
#print axioms first_deriv
#print axioms energy_identity
#print axioms denominator_factor
#print axioms exponent_pos
#print axioms exponent_gap_pos
#print axioms denominator_pos
#print axioms ratio_identity

end CAS06Scalar
