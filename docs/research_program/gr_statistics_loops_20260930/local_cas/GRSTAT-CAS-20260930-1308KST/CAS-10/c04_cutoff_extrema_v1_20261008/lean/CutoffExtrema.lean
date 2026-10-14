import Mathlib

/-!
Independent Lean axis for GRSTAT-20260930-CAS-10-C04-CUTOFF-EXTREMA-V1.
Input: F(t)=1-10t^3+15t^4-6t^5, real t in [0,1].
The auxiliary exponential and square-root estimates are inputs to a larger
argument, not targets here. This file proves only the finite polynomial facts.
-/

namespace CAS10C04

def F (t : ℝ) : ℝ := 1 - 10*t^3 + 15*t^4 - 6*t^5
def Fp (t : ℝ) : ℝ := -30*t^2*(1-t)^2
def Fpp (t : ℝ) : ℝ := -60*t*(1-t)*(1-2*t)

theorem F_hasDerivAt (t : ℝ) : HasDerivAt F (Fp t) t := by
  have h0 := hasDerivAt_const t (1:ℝ)
  have h3 := HasDerivAt.const_mul (10:ℝ) ((hasDerivAt_id t).pow 3)
  have h4 := HasDerivAt.const_mul (15:ℝ) ((hasDerivAt_id t).pow 4)
  have h5 := HasDerivAt.const_mul (6:ℝ) ((hasDerivAt_id t).pow 5)
  have h := ((h0.sub h3).add h4).sub h5
  change HasDerivAt F
    (0 - 10*((3:ℝ) * id t ^ (3-1) * 1) +
      15*((4:ℝ) * id t ^ (4-1) * 1) -
      6*((5:ℝ) * id t ^ (5-1) * 1)) t at h
  have hval : Fp t =
      0 - 10*((3:ℝ) * id t ^ (3-1) * 1) +
      15*((4:ℝ) * id t ^ (4-1) * 1) -
      6*((5:ℝ) * id t ^ (5-1) * 1) := by
    dsimp [Fp]; ring
  rw [← hval] at h
  exact h

theorem Fp_hasDerivAt (t : ℝ) : HasDerivAt Fp (Fpp t) t := by
  have h2 := HasDerivAt.const_mul (-30:ℝ) ((hasDerivAt_id t).pow 2)
  have h3 := HasDerivAt.const_mul (60:ℝ) ((hasDerivAt_id t).pow 3)
  have h4 := HasDerivAt.const_mul (-30:ℝ) ((hasDerivAt_id t).pow 4)
  have h := (h2.add h3).add h4
  have hfun : ((fun y : ℝ => -30*y^2) + (fun y : ℝ => 60*y^3)) +
      (fun y : ℝ => -30*y^4) = Fp := by
    funext y; dsimp [Fp]; ring
  simp only [Pi.pow_apply, id_eq] at h
  rw [hfun] at h
  have hval : Fpp t =
      -30*(((2:ℕ):ℝ) * id t ^ (2-1) * 1) +
      60*(((3:ℕ):ℝ) * id t ^ (3-1) * 1) +
      -30*(((4:ℕ):ℝ) * id t ^ (4-1) * 1) := by
    dsimp [Fpp]; ring
  simp only [id_eq] at hval
  rw [← hval] at h
  exact h

theorem endpoint_jets :
    F 0 = 1 ∧ F 1 = 0 ∧ Fp 0 = 0 ∧ Fp 1 = 0 ∧
    Fpp 0 = 0 ∧ Fpp 1 = 0 := by
  norm_num [F, Fp, Fpp]

theorem fp_abs_bound (t : ℝ) (ht0 : 0 ≤ t) (ht1 : t ≤ 1) :
    |Fp t| ≤ (15:ℝ)/8 := by
  have hs : 0 ≤ t*(1-t) := mul_nonneg ht0 (by linarith)
  have hq : t*(1-t) ≤ (1:ℝ)/4 := by nlinarith [sq_nonneg (t - 1/2)]
  have hsq : (t*(1-t))^2 ≤ (1/4:ℝ)^2 := by nlinarith
  have hf : Fp t = -30*(t*(1-t))^2 := by unfold Fp; ring
  rw [hf]
  have hneg : -30*(t*(1-t))^2 ≤ 0 := by nlinarith [sq_nonneg (t*(1-t))]
  rw [abs_of_nonpos hneg]
  nlinarith

theorem fp_mid : |Fp (1/2:ℝ)| = (15:ℝ)/8 := by norm_num [Fp]

private theorem sqrt3_pos : 0 < Real.sqrt (3:ℝ) := Real.sqrt_pos.2 (by norm_num)
private theorem sqrt3_sq : (Real.sqrt (3:ℝ))^2 = 3 := by norm_num

private theorem cubic_bound (y : ℝ) (hy : 0 ≤ y) (_hy1 : y ≤ 1) :
    y*(1-y^2) ≤ 2*(Real.sqrt (3:ℝ)/3)/3 := by
  let a : ℝ := Real.sqrt 3 / 3
  have ha : 0 < a := by dsimp [a]; positivity
  have ha2 : a^2 = 1/3 := by dsimp [a]; nlinarith [sqrt3_sq]
  have ha3 : a^3 = a/3 := by calc
    a^3 = a*a^2 := by ring
    _ = a/3 := by rw [ha2]; ring
  have hnonneg : 0 ≤ (y-a)^2*(y+2*a) :=
    mul_nonneg (sq_nonneg _) (by linarith)
  change y*(1-y^2) ≤ 2*a/3
  nlinarith [hnonneg]

private theorem cubic_nonneg (y : ℝ) (hy : 0 ≤ y) (hy1 : y ≤ 1) :
    0 ≤ y*(1-y^2) := by
  have hsq : y^2 ≤ 1 := by nlinarith
  exact mul_nonneg hy (by linarith)

private theorem fpp_as_cubic (t : ℝ) :
    Fpp t = 15*(2*t-1)*(1-(2*t-1)^2) := by unfold Fpp; ring

theorem fpp_abs_bound (t : ℝ) (ht0 : 0 ≤ t) (ht1 : t ≤ 1) :
    |Fpp t| ≤ 10/Real.sqrt (3:ℝ) := by
  let r : ℝ := Real.sqrt 3
  let a : ℝ := r/3
  let x : ℝ := 2*t-1
  have hr : 0 < r := sqrt3_pos
  have hr2 : r^2 = 3 := sqrt3_sq
  have htarget : 10/r = 10*a := by
    dsimp [a]
    field_simp
    nlinarith
  have hx0 : -1 ≤ x := by dsimp [x]; linarith
  have hx1 : x ≤ 1 := by dsimp [x]; linarith
  have hf : Fpp t = 15*x*(1-x^2) := by simpa [x] using fpp_as_cubic t
  rw [hf, htarget]
  apply abs_le.mpr
  rcases le_total 0 x with hx | hx
  · have hb := cubic_bound x hx hx1
    have hn := cubic_nonneg x hx hx1
    change x*(1-x^2) ≤ 2*a/3 at hb
    constructor <;> nlinarith
  · have hy0 : 0 ≤ -x := by linarith
    have hy1 : -x ≤ 1 := by linarith
    have hb := cubic_bound (-x) hy0 hy1
    have hn := cubic_nonneg (-x) hy0 hy1
    change (-x)*(1-(-x)^2) ≤ 2*a/3 at hb
    constructor <;> nlinarith

noncomputable def tminus : ℝ := (3 - Real.sqrt 3)/6
noncomputable def tplus : ℝ := (3 + Real.sqrt 3)/6

theorem tminus_mem : 0 ≤ tminus ∧ tminus ≤ 1 := by
  have hp := sqrt3_pos
  have hs := sqrt3_sq
  dsimp [tminus]
  constructor <;> nlinarith

theorem tplus_mem : 0 ≤ tplus ∧ tplus ≤ 1 := by
  have hp := sqrt3_pos
  have hs := sqrt3_sq
  dsimp [tplus]
  constructor <;> nlinarith

theorem fpp_critical_values :
    |Fpp tminus| = 10/Real.sqrt (3:ℝ) ∧
    |Fpp tplus| = 10/Real.sqrt (3:ℝ) := by
  have hr := sqrt3_pos
  have hr2 := sqrt3_sq
  have hm : Fpp tminus = -10*Real.sqrt 3/3 := by
    rw [fpp_as_cubic]
    dsimp [tminus]
    nlinarith
  have hp : Fpp tplus = 10*Real.sqrt 3/3 := by
    rw [fpp_as_cubic]
    dsimp [tplus]
    nlinarith
  rw [hm, hp, abs_of_nonpos (by have := sqrt3_pos; nlinarith),
    abs_of_pos (by have := sqrt3_pos; nlinarith)]
  constructor <;> field_simp <;> nlinarith

theorem rational_margin :
    (25/24:ℝ)*(14/15+9/400) = 1147/1152 ∧ (1147/1152:ℝ) < 1 := by
  norm_num

end CAS10C04
