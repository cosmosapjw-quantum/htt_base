import G13BBoundaryMinimax

/-!
# G13-C: principal moment extremizer for every real `p > 4`

Imports, unchanged: the reviewed G13-B source `G13BBoundaryMinimax.lean` (sha256 6d9a9d68…c6af1),
which itself imports the reviewed G13-A source `MeasureExtremizerBridge.lean` (sha256 a64f6c3c…fda12)
and the reviewed C04 source `CAS-13/lean/Main.lean` (sha256 5be0cd66…da97).

Route (Mathlib has no general Chebyshev-system theorem, so the needed special theorem is proved):

* T1  `W(1,y³,y⁴,y^p) = 12 p (p-3)(p-4) y^(p+1)` for `y > 0`, lower-order Wronskians, and the identity
  `(p y^(p-3))'' · 12 y⁶ = W`; hence `W > 0` on `(0,∞)` implies strict convexity of `p y^(p-3)`.
* T2  generalized Rolle: with that convexity, the Hermite interpolant in span{1,y³,y⁴} of `y^p`
  (simple node `A`, double node `U`) is a minorant on `[a,∞)` (`A=a<U=u`) and a majorant on `(0,b]`
  (`A=b>U=d`), for every real `p` satisfying the hypothesis.
* T3  the hypothesis holds for every real `p > 4` (through the Wronskian).
* T4  integration against every measure of the same retained-moment class; attainment by the
  principal two-point measures; exact range by mixtures.
* T5  C04 minimax, the G13-B boundary branches lifted to every real `p`, closed region.

The `p = 5, 6` polynomial certificates of G13-A are not used. No scientific admission is asserted.
-/

noncomputable section
open MeasureTheory Set

namespace CAS13G13C
open CAS13MeasureComposition CAS13G13B

/-! ## Definitions (frozen) -/

/-- Wronskian of `n` real functions: det of `(deriv^[i] (f j) y)`. -/
def wronskian {n : ℕ} (f : Fin n → ℝ → ℝ) (y : ℝ) : ℝ :=
  (Matrix.of fun i j : Fin n => deriv^[(i : ℕ)] (f j) y).det

/-- The moment system {1, y³, y⁴, y^p}. -/
def powerSystem (p : ℝ) : Fin 4 → ℝ → ℝ :=
  ![fun _ => 1, fun x => x ^ 3, fun x => x ^ 4, fun x => x ^ p]

/-- Reduced derivative factor of the residual `y^p − (c0 + c3 y³ + c4 y⁴)`. -/
def reducedH (p c3 c4 y : ℝ) : ℝ := p * y ^ (p - 3) - 3 * c3 - 4 * c4 * y

/-- Determinant of the Hermite system (simple node `A`, double node `U`). -/
def interpDet (A U : ℝ) : ℝ := 3 * (U ^ 4 - A ^ 4) - 4 * U * (U ^ 3 - A ^ 3)

def interpC3 (A U p : ℝ) : ℝ :=
  (p * U ^ (p - 3) * (U ^ 4 - A ^ 4) - 4 * U * (U ^ p - A ^ p)) / interpDet A U

def interpC4 (A U p : ℝ) : ℝ :=
  (3 * (U ^ p - A ^ p) - (U ^ 3 - A ^ 3) * (p * U ^ (p - 3))) / interpDet A U

def interpC0 (A U p : ℝ) : ℝ := A ^ p - interpC3 A U p * A ^ 3 - interpC4 A U p * A ^ 4

/-- Hermite interpolant of `y^p` in span{1,y³,y⁴}: value at `A`, value and slope at `U`. -/
def interp (A U p y : ℝ) : ℝ := hermite (interpC0 A U p) (interpC3 A U p) (interpC4 A U p) y

/-- Exact attained range of the real-exponent moment over a class of measures. -/
def RSharpInterval (F : Set (Measure ℝ)) (p : ℝ) (L U : ℝ) : Prop :=
  (∀ μ ∈ F, L ≤ rmoment μ p ∧ rmoment μ p ≤ U) ∧
  (∃ μ ∈ F, rmoment μ p = L) ∧ (∃ μ ∈ F, rmoment μ p = U) ∧
  (fun μ => rmoment μ p) '' F = Icc L U

/-- C04 relative minimax lifted to a class of measures, real exponent. -/
def RFibreMinimax (F : Set (Measure ℝ)) (p : ℝ) (L U : ℝ) : Prop :=
  (∀ μ ∈ F, |(grstatTau L U - rmoment μ p) / rmoment μ p| ≤ grstatEps L U) ∧
  (∃ μ ∈ F, |(grstatTau L U - rmoment μ p) / rmoment μ p| = grstatEps L U) ∧
  (∀ t : ℝ, ∃ μ ∈ F, grstatEps L U ≤ |(t - rmoment μ p) / rmoment μ p|)

/-! ## T1: real-power smoothness and Wronskian-sequence positivity -/

theorem rpow_shift {y : ℝ} (hy : 0 < y) (q : ℝ) (n : ℕ) : y ^ (q + n) = y ^ q * y ^ n := by
  rw [Real.rpow_add hy, Real.rpow_natCast]

theorem wronskian_one (y : ℝ) : wronskian ![fun _ : ℝ => (1 : ℝ)] y = 1 := by
  unfold wronskian
  simp

theorem wronskian_two (y : ℝ) :
    wronskian ![fun _ : ℝ => (1 : ℝ), fun x : ℝ => x ^ 3] y = 3 * y ^ 2 := by
  unfold wronskian
  rw [Matrix.det_fin_two]
  simp [iter_deriv_pow]

theorem wronskian_three (y : ℝ) :
    wronskian ![fun _ : ℝ => (1 : ℝ), fun x : ℝ => x ^ 3, fun x : ℝ => x ^ 4] y = 12 * y ^ 4 := by
  unfold wronskian
  rw [Matrix.det_fin_three]
  simp [iter_deriv_pow, Finset.prod_range_succ]
  ring

theorem wronskian_power_system (p : ℝ) {y : ℝ} (hy : 0 < y) :
    wronskian (powerSystem p) y = 12 * p * (p - 3) * (p - 4) * y ^ (p + 1) := by
  unfold wronskian powerSystem
  rw [Matrix.det_succ_column_zero]
  simp [Fin.sum_univ_succ, Matrix.det_fin_three, iter_deriv_pow, Finset.prod_range_succ,
    Real.iter_deriv_rpow_const, descPochhammer_succ_right, Fin.succAbove]
  have e1 : y ^ (p - 1) = y ^ (p - 3) * y ^ 2 := by
    rw [← rpow_shift hy]; congr 1; push_cast; ring
  have e2 : y ^ (p - 2) = y ^ (p - 3) * y ^ 1 := by
    rw [← rpow_shift hy]; congr 1; push_cast; ring
  have e3 : y ^ (p + 1) = y ^ (p - 3) * y ^ 4 := by
    rw [← rpow_shift hy]; congr 1; push_cast; ring
  rw [e1, e2, e3]
  ring

theorem wronskian_chain_pos {p y : ℝ} (hp : 4 < p) (hy : 0 < y) :
    0 < wronskian ![fun _ : ℝ => (1 : ℝ)] y ∧
    0 < wronskian ![fun _ : ℝ => (1 : ℝ), fun x : ℝ => x ^ 3] y ∧
    0 < wronskian ![fun _ : ℝ => (1 : ℝ), fun x : ℝ => x ^ 3, fun x : ℝ => x ^ 4] y ∧
    0 < wronskian (powerSystem p) y := by
  refine ⟨by rw [wronskian_one]; norm_num, by rw [wronskian_two]; positivity,
    by rw [wronskian_three]; positivity, ?_⟩
  rw [wronskian_power_system p hy]
  have h1 : 0 < p := by linarith
  have h2 : 0 < p - 3 := by linarith
  have h3 : 0 < p - 4 := by linarith
  have h4 : 0 < y ^ (p + 1) := Real.rpow_pos_of_pos hy _
  exact mul_pos (mul_pos (mul_pos (mul_pos (by norm_num) h1) h2) h3) h4

theorem reduced_deriv1 (p : ℝ) :
    deriv (fun x : ℝ => p * x ^ (p - 3)) = fun x => p * ((p - 3) * x ^ (p - 3 - 1)) := by
  rw [deriv_const_mul_field', Real.deriv_rpow_const']

theorem reduced_deriv2 (p y : ℝ) :
    deriv^[2] (fun x : ℝ => p * x ^ (p - 3)) y =
      p * ((p - 3) * ((p - 3 - 1) * y ^ (p - 3 - 1 - 1))) := by
  show deriv (deriv (fun x : ℝ => p * x ^ (p - 3))) y = _
  rw [reduced_deriv1]
  simp only [deriv_const_mul_field', Real.deriv_rpow_const']

theorem reduced_deriv2_wronskian (p : ℝ) {y : ℝ} (hy : 0 < y) :
    deriv^[2] (fun x : ℝ => p * x ^ (p - 3)) y * (12 * y ^ 6) = wronskian (powerSystem p) y := by
  rw [reduced_deriv2, wronskian_power_system p hy]
  have e : y ^ (p + 1) = y ^ (p - 3 - 1 - 1) * y ^ 6 := by
    rw [← rpow_shift hy]; congr 1; push_cast; ring
  rw [e]
  ring

theorem reduced_convex_of_wronskian_pos {p : ℝ}
    (hW : ∀ y : ℝ, 0 < y → 0 < wronskian (powerSystem p) y) :
    StrictConvexOn ℝ (Ioi 0) (fun x : ℝ => p * x ^ (p - 3)) := by
  refine strictConvexOn_of_deriv2_pos (convex_Ioi 0) ?_ ?_
  · intro x hx
    exact ((Real.hasDerivAt_rpow_const (p := p - 3) (Or.inl (ne_of_gt hx))).const_mul
      p).continuousAt.continuousWithinAt
  · intro x hx
    rw [interior_Ioi] at hx
    have hx0 : 0 < x := hx
    have h := hW x hx0
    rw [← reduced_deriv2_wronskian p hx0] at h
    have h6 : 0 < 12 * x ^ 6 := by positivity
    by_contra hc
    have := mul_nonpos_of_nonpos_of_nonneg (not_lt.1 hc) h6.le
    linarith

theorem hermite_hasDerivAt (c0 c3 c4 y : ℝ) :
    HasDerivAt (hermite c0 c3 c4) (3 * c3 * y ^ 2 + 4 * c4 * y ^ 3) y := by
  have h := ((hasDerivAt_const y c0).add ((hasDerivAt_pow 3 y).const_mul c3)).add
    ((hasDerivAt_pow 4 y).const_mul c4)
  refine h.congr_deriv ?_
  norm_num
  ring

theorem residual_hasDerivAt (p c0 c3 c4 : ℝ) {y : ℝ} (hy : 0 < y) :
    HasDerivAt (fun x : ℝ => x ^ p - hermite c0 c3 c4 x) (y ^ 2 * reducedH p c3 c4 y) y := by
  have h1 := Real.hasDerivAt_rpow_const (p := p) (Or.inl hy.ne')
  have h := h1.sub (hermite_hasDerivAt c0 c3 c4 y)
  refine h.congr_deriv ?_
  have e : y ^ (p - 1) = y ^ (p - 3) * y ^ 2 := by
    rw [← rpow_shift hy]; congr 1; push_cast; ring
  rw [e]
  unfold reducedH
  ring

/-! ## T2: generalized Rolle / Hermite-remainder sign -/

theorem interpDet_eq (A U : ℝ) :
    interpDet A U = -((U - A) ^ 2 * (U ^ 2 + 2 * A * U + 3 * A ^ 2)) := by
  unfold interpDet
  ring

theorem interpDet_ne {A U : ℝ} (hA : 0 < A) (hU : 0 < U) (hAU : A ≠ U) : interpDet A U ≠ 0 := by
  rw [interpDet_eq]
  have hne : U - A ≠ 0 := sub_ne_zero.2 (Ne.symm hAU)
  have h1 : 0 < (U - A) ^ 2 := lt_of_le_of_ne (sq_nonneg _) (Ne.symm (pow_ne_zero 2 hne))
  have h2 : 0 < U ^ 2 + 2 * A * U + 3 * A ^ 2 := by positivity
  exact neg_ne_zero.2 (mul_pos h1 h2).ne'

theorem interp_conditions {A U : ℝ} (hA : 0 < A) (hU : 0 < U) (hAU : A ≠ U) (p : ℝ) :
    interp A U p A = A ^ p ∧ interp A U p U = U ^ p ∧
    reducedH p (interpC3 A U p) (interpC4 A U p) U = 0 := by
  have hD := interpDet_ne hA hU hAU
  refine ⟨?_, ?_, ?_⟩
  · unfold interp hermite interpC0
    ring
  · unfold interp hermite interpC0 interpC3 interpC4
    field_simp
    unfold interpDet
    ring
  · unfold reducedH interpC3 interpC4
    field_simp
    unfold interpDet
    ring

theorem interp_slope {A U : ℝ} (hA : 0 < A) (hU : 0 < U) (hAU : A ≠ U) (p : ℝ) :
    HasDerivAt (interp A U p) (p * U ^ (p - 1)) U := by
  have hH := (interp_conditions hA hU hAU p).2.2
  have h := hermite_hasDerivAt (interpC0 A U p) (interpC3 A U p) (interpC4 A U p) U
  refine h.congr_deriv ?_
  have e : U ^ (p - 1) = U ^ (p - 3) * U ^ 2 := by
    rw [← rpow_shift hU]; congr 1; push_cast; ring
  rw [e]
  unfold reducedH at hH
  linear_combination (-(U ^ 2)) * hH

/-- Three-point strict convexity inequality for the reduced factor. -/
theorem reducedH_three {p c3 c4 x y z : ℝ}
    (hφ : StrictConvexOn ℝ (Ioi 0) (fun t : ℝ => p * t ^ (p - 3)))
    (hx : 0 < x) (hxy : x < y) (hyz : y < z) :
    reducedH p c3 c4 y * (z - x) <
      (z - y) * reducedH p c3 c4 x + (y - x) * reducedH p c3 c4 z := by
  have hzx : 0 < z - x := by linarith
  have hθ : 0 < (z - y) / (z - x) := div_pos (by linarith) hzx
  have hθ' : 0 < (y - x) / (z - x) := div_pos (by linarith) hzx
  have hsum : (z - y) / (z - x) + (y - x) / (z - x) = 1 := by
    field_simp
    ring
  have hxm : x ∈ Ioi (0 : ℝ) := hx
  have hzm : z ∈ Ioi (0 : ℝ) := by
    show 0 < z
    linarith
  have hc := hφ.2 hxm hzm (ne_of_lt (by linarith : x < z)) hθ hθ' hsum
  simp only [smul_eq_mul] at hc
  have hpt : (z - y) / (z - x) * x + (y - x) / (z - x) * z = y := by
    field_simp
    ring
  rw [hpt] at hc
  have key := mul_lt_mul_of_pos_right hc hzx
  have e : ((z - y) / (z - x) * (p * x ^ (p - 3)) + (y - x) / (z - x) * (p * z ^ (p - 3))) *
      (z - x) = (z - y) * (p * x ^ (p - 3)) + (y - x) * (p * z ^ (p - 3)) := by
    field_simp
  rw [e] at key
  have e2 : ((z - y) * reducedH p c3 c4 x + (y - x) * reducedH p c3 c4 z) -
      reducedH p c3 c4 y * (z - x) =
      ((z - y) * (p * x ^ (p - 3)) + (y - x) * (p * z ^ (p - 3))) -
        p * y ^ (p - 3) * (z - x) := by
    unfold reducedH
    ring
  linarith

theorem residual_monotoneOn {p c0 c3 c4 : ℝ} {D : Set ℝ} (hD : Convex ℝ D)
    (hpos : ∀ x ∈ D, 0 < x) (hH : ∀ x ∈ interior D, 0 ≤ reducedH p c3 c4 x) :
    MonotoneOn (fun x : ℝ => x ^ p - hermite c0 c3 c4 x) D := by
  refine monotoneOn_of_deriv_nonneg hD ?_ ?_ ?_
  · intro x hx
    exact (residual_hasDerivAt p c0 c3 c4 (hpos x hx)).continuousAt.continuousWithinAt
  · intro x hx
    exact (residual_hasDerivAt p c0 c3 c4
      (hpos x (interior_subset hx))).differentiableAt.differentiableWithinAt
  · intro x hx
    rw [(residual_hasDerivAt p c0 c3 c4 (hpos x (interior_subset hx))).deriv]
    exact mul_nonneg (sq_nonneg x) (hH x hx)

theorem residual_antitoneOn {p c0 c3 c4 : ℝ} {D : Set ℝ} (hD : Convex ℝ D)
    (hpos : ∀ x ∈ D, 0 < x) (hH : ∀ x ∈ interior D, reducedH p c3 c4 x ≤ 0) :
    AntitoneOn (fun x : ℝ => x ^ p - hermite c0 c3 c4 x) D := by
  refine antitoneOn_of_deriv_nonpos hD ?_ ?_ ?_
  · intro x hx
    exact (residual_hasDerivAt p c0 c3 c4 (hpos x hx)).continuousAt.continuousWithinAt
  · intro x hx
    exact (residual_hasDerivAt p c0 c3 c4
      (hpos x (interior_subset hx))).differentiableAt.differentiableWithinAt
  · intro x hx
    rw [(residual_hasDerivAt p c0 c3 c4 (hpos x (interior_subset hx))).deriv]
    exact mul_nonpos_of_nonneg_of_nonpos (sq_nonneg x) (hH x hx)

/-- Rolle step: two zeros of the residual give a zero of the reduced factor strictly between. -/
theorem rolle_reduced {p c0 c3 c4 l r : ℝ} (hl : 0 < l) (hlr : l < r)
    (hgl : hermite c0 c3 c4 l = l ^ p) (hgr : hermite c0 c3 c4 r = r ^ p) :
    ∃ ξ ∈ Ioo l r, reducedH p c3 c4 ξ = 0 := by
  obtain ⟨ξ, hξ, hξ0⟩ := exists_hasDerivAt_eq_zero
    (f := fun x : ℝ => x ^ p - hermite c0 c3 c4 x)
    (f' := fun x => x ^ 2 * reducedH p c3 c4 x) hlr
    (fun x hx => (residual_hasDerivAt p c0 c3 c4
      (hl.trans_le hx.1)).continuousAt.continuousWithinAt)
    (by simp only [hgl, hgr, sub_self])
    (fun x hx => residual_hasDerivAt p c0 c3 c4 (hl.trans hx.1))
  have hξpos : 0 < ξ := hl.trans hξ.1
  refine ⟨ξ, hξ, ?_⟩
  rcases mul_eq_zero.1 hξ0 with h | h
  · exact absurd (pow_eq_zero_iff (n := 2) (by norm_num) |>.1 h) hξpos.ne'
  · exact h

theorem minorant_core {p a u c0 c3 c4 : ℝ}
    (hφ : StrictConvexOn ℝ (Ioi 0) (fun x : ℝ => p * x ^ (p - 3)))
    (ha : 0 < a) (hau : a < u) (hga : hermite c0 c3 c4 a = a ^ p)
    (hgu : hermite c0 c3 c4 u = u ^ p) (hHu : reducedH p c3 c4 u = 0) :
    ∀ y : ℝ, a ≤ y → hermite c0 c3 c4 y ≤ y ^ p := by
  obtain ⟨ξ, hξ, hHξ⟩ := rolle_reduced (p := p) ha hau hga hgu
  have hξpos : 0 < ξ := ha.trans hξ.1
  have huξ : 0 < u - ξ := by linarith [hξ.2]
  have hH1 : ∀ x, 0 < x → x ≤ ξ → 0 ≤ reducedH p c3 c4 x := by
    intro x hx hxξ
    rcases hxξ.lt_or_eq with h | h
    · have := reducedH_three (c3 := c3) (c4 := c4) hφ hx h hξ.2
      rw [hHξ, hHu] at this
      nlinarith
    · rw [h, hHξ]
  have hH2 : ∀ x, ξ ≤ x → x ≤ u → reducedH p c3 c4 x ≤ 0 := by
    intro x h1 h2
    rcases h1.lt_or_eq with h1 | h1
    · rcases h2.lt_or_eq with h2 | h2
      · have := reducedH_three (c3 := c3) (c4 := c4) hφ hξpos h1 h2
        rw [hHξ, hHu] at this
        nlinarith
      · rw [h2, hHu]
    · rw [← h1, hHξ]
  have hH3 : ∀ x, u ≤ x → 0 ≤ reducedH p c3 c4 x := by
    intro x h1
    rcases h1.lt_or_eq with h1 | h1
    · have := reducedH_three (c3 := c3) (c4 := c4) hφ hξpos hξ.2 h1
      rw [hHξ, hHu] at this
      nlinarith
    · rw [← h1, hHu]
  have g_a : (fun x : ℝ => x ^ p - hermite c0 c3 c4 x) a = 0 := by
    simp only [hga, sub_self]
  have g_u : (fun x : ℝ => x ^ p - hermite c0 c3 c4 x) u = 0 := by
    simp only [hgu, sub_self]
  intro y hy
  have hg : 0 ≤ (fun x : ℝ => x ^ p - hermite c0 c3 c4 x) y := by
    rcases le_or_gt y ξ with hyξ | hyξ
    · have hm := residual_monotoneOn (p := p) (c0 := c0) (c3 := c3) (c4 := c4)
        (convex_Icc a ξ) (fun x hx => ha.trans_le hx.1) (fun x hx => by
          rw [interior_Icc] at hx
          exact hH1 x (ha.trans hx.1) hx.2.le)
      have := hm ⟨le_rfl, hξ.1.le⟩ ⟨hy, hyξ⟩ hy
      rw [g_a] at this
      exact this
    · rcases le_or_gt y u with hyu | hyu
      · have hm := residual_antitoneOn (p := p) (c0 := c0) (c3 := c3) (c4 := c4)
          (convex_Icc ξ u) (fun x hx => hξpos.trans_le hx.1) (fun x hx => by
            rw [interior_Icc] at hx
            exact hH2 x hx.1.le hx.2.le)
        have := hm ⟨hyξ.le, hyu⟩ ⟨hξ.2.le, le_rfl⟩ hyu
        rw [g_u] at this
        exact this
      · have hm := residual_monotoneOn (p := p) (c0 := c0) (c3 := c3) (c4 := c4)
          (convex_Ici u) (fun x hx => (ha.trans hau).trans_le hx) (fun x hx => by
            rw [interior_Ici] at hx
            exact hH3 x (le_of_lt hx))
        have := hm self_mem_Ici (le_of_lt hyu : u ≤ y) hyu.le
        rw [g_u] at this
        exact this
  simp only at hg
  linarith

theorem majorant_core {p d b c0 c3 c4 : ℝ}
    (hφ : StrictConvexOn ℝ (Ioi 0) (fun x : ℝ => p * x ^ (p - 3)))
    (hd : 0 < d) (hdb : d < b) (hgd : hermite c0 c3 c4 d = d ^ p)
    (hgb : hermite c0 c3 c4 b = b ^ p) (hHd : reducedH p c3 c4 d = 0) :
    ∀ y : ℝ, 0 < y → y ≤ b → y ^ p ≤ hermite c0 c3 c4 y := by
  obtain ⟨ξ, hξ, hHξ⟩ := rolle_reduced (p := p) hd hdb hgd hgb
  have hξpos : 0 < ξ := hd.trans hξ.1
  have hξd : 0 < ξ - d := by linarith [hξ.1]
  have hH1 : ∀ x, 0 < x → x ≤ d → 0 ≤ reducedH p c3 c4 x := by
    intro x hx hxd
    rcases hxd.lt_or_eq with h | h
    · have := reducedH_three (c3 := c3) (c4 := c4) hφ hx h hξ.1
      rw [hHξ, hHd] at this
      nlinarith
    · rw [h, hHd]
  have hH2 : ∀ x, d ≤ x → x ≤ ξ → reducedH p c3 c4 x ≤ 0 := by
    intro x h1 h2
    rcases h1.lt_or_eq with h1 | h1
    · rcases h2.lt_or_eq with h2 | h2
      · have := reducedH_three (c3 := c3) (c4 := c4) hφ hd h1 h2
        rw [hHξ, hHd] at this
        nlinarith
      · rw [h2, hHξ]
    · rw [← h1, hHd]
  have hH3 : ∀ x, ξ ≤ x → 0 ≤ reducedH p c3 c4 x := by
    intro x h1
    rcases h1.lt_or_eq with h1 | h1
    · have := reducedH_three (c3 := c3) (c4 := c4) hφ hd hξ.1 h1
      rw [hHξ, hHd] at this
      nlinarith
    · rw [← h1, hHξ]
  have g_d : (fun x : ℝ => x ^ p - hermite c0 c3 c4 x) d = 0 := by
    simp only [hgd, sub_self]
  have g_b : (fun x : ℝ => x ^ p - hermite c0 c3 c4 x) b = 0 := by
    simp only [hgb, sub_self]
  intro y hy hyb
  have hg : (fun x : ℝ => x ^ p - hermite c0 c3 c4 x) y ≤ 0 := by
    rcases le_or_gt y d with hyd | hyd
    · have hm := residual_monotoneOn (p := p) (c0 := c0) (c3 := c3) (c4 := c4)
        (convex_Ioc 0 d) (fun x hx => hx.1) (fun x hx => by
          rw [interior_Ioc] at hx
          exact hH1 x hx.1 hx.2.le)
      have := hm ⟨hy, hyd⟩ ⟨hd, le_rfl⟩ hyd
      rw [g_d] at this
      exact this
    · rcases le_or_gt y ξ with hyξ | hyξ
      · have hm := residual_antitoneOn (p := p) (c0 := c0) (c3 := c3) (c4 := c4)
          (convex_Icc d ξ) (fun x hx => hd.trans_le hx.1) (fun x hx => by
            rw [interior_Icc] at hx
            exact hH2 x hx.1.le hx.2.le)
        have := hm ⟨le_rfl, hξ.1.le⟩ ⟨hyd.le, hyξ⟩ hyd.le
        rw [g_d] at this
        exact this
      · have hm := residual_monotoneOn (p := p) (c0 := c0) (c3 := c3) (c4 := c4)
          (convex_Icc ξ b) (fun x hx => hξpos.trans_le hx.1) (fun x hx => by
            rw [interior_Icc] at hx
            exact hH3 x hx.1.le)
        have := hm ⟨hyξ.le, hyb⟩ ⟨hξ.2.le, le_rfl⟩ hyb
        rw [g_b] at this
        exact this
  simp only at hg
  linarith

theorem minorant_of_reduced_convex {p a u : ℝ}
    (hφ : StrictConvexOn ℝ (Ioi 0) (fun x : ℝ => p * x ^ (p - 3)))
    (ha : 0 < a) (hau : a < u) : ∀ y : ℝ, a ≤ y → interp a u p y ≤ y ^ p := by
  obtain ⟨h1, h2, h3⟩ := interp_conditions ha (ha.trans hau) hau.ne p
  exact minorant_core hφ ha hau h1 h2 h3

theorem majorant_of_reduced_convex {p d b : ℝ}
    (hφ : StrictConvexOn ℝ (Ioi 0) (fun x : ℝ => p * x ^ (p - 3)))
    (hd : 0 < d) (hdb : d < b) : ∀ y : ℝ, 0 < y → y ≤ b → y ^ p ≤ interp b d p y := by
  obtain ⟨h1, h2, h3⟩ := interp_conditions (hd.trans hdb) hd hdb.ne' p
  exact majorant_core hφ hd hdb h2 h1 h3

/-! ## T3: every real p > 4, through the Wronskian -/

theorem reduced_convex {p : ℝ} (hp : 4 < p) :
    StrictConvexOn ℝ (Ioi 0) (fun x : ℝ => p * x ^ (p - 3)) :=
  reduced_convex_of_wronskian_pos fun _ hy => (wronskian_chain_pos hp hy).2.2.2

theorem lower_interp_minorant {p a u : ℝ} (hp : 4 < p) (ha : 0 < a) (hau : a < u) :
    ∀ y : ℝ, a ≤ y → interp a u p y ≤ y ^ p :=
  minorant_of_reduced_convex (reduced_convex hp) ha hau

theorem upper_interp_majorant {p d b : ℝ} (hp : 4 < p) (hd : 0 < d) (hdb : d < b) :
    ∀ y : ℝ, 0 < y → y ≤ b → y ^ p ≤ interp b d p y :=
  majorant_of_reduced_convex (reduced_convex hp) hd hdb

/-! ## T4: global extremality and attainment by measure integration -/

theorem integrable_rpow_of_mem {a b m3 m4 p : ℝ} (hp : 0 ≤ p) {μ : Measure ℝ}
    (hμ : μ ∈ NEFibre a b m3 m4) : Integrable (fun x : ℝ => x ^ p) μ := by
  haveI := hμ.1
  exact integrable_of_Icc hμ.2.1 (Real.continuous_rpow_const hp)

theorem rsharpInterval_of_extremes {a b m3 m4 p : ℝ} (hp : 0 ≤ p) {μL μU : Measure ℝ}
    {L U : ℝ} (hL : μL ∈ NEFibre a b m3 m4) (hU : μU ∈ NEFibre a b m3 m4)
    (hmL : rmoment μL p = L) (hmU : rmoment μU p = U)
    (hb : ∀ μ ∈ NEFibre a b m3 m4, L ≤ rmoment μ p ∧ rmoment μ p ≤ U) :
    RSharpInterval (NEFibre a b m3 m4) p L U := by
  refine ⟨hb, ⟨μL, hL, hmL⟩, ⟨μU, hU, hmU⟩, ?_⟩
  ext m
  simp only [mem_image, mem_Icc]
  constructor
  · rintro ⟨μ, hμ, rfl⟩
    exact hb μ hμ
  · rintro ⟨h1, h2⟩
    rcases eq_or_lt_of_le (h1.trans h2) with hLU | hLU
    · exact ⟨μL, hL, by rw [hmL]; linarith⟩
    · have hθ0 : 0 ≤ (U - m) / (U - L) := div_nonneg (by linarith) (by linarith)
      have hθ1 : (U - m) / (U - L) ≤ 1 := (div_le_one (sub_pos.2 hLU)).2 (by linarith)
      obtain ⟨hmem, -⟩ := mix_mem hθ0 hθ1 hL hU
      refine ⟨mix ((U - m) / (U - L)) μL μU, hmem, ?_⟩
      have hne : U - L ≠ 0 := (sub_pos.2 hLU).ne'
      unfold rmoment at hmL hmU ⊢
      rw [integral_mix hθ0 hθ1 (integrable_rpow_of_mem hp hL) (integrable_rpow_of_mem hp hU),
        hmL, hmU]
      field_simp
      ring

theorem interior_real_bounds {a b m3 m4 p u d : ℝ} (h : CAS13C02.StrictInterior a b m3 m4)
    (hp : 4 < p) (hu : LowerNode a b m3 m4 u) (hd : UpperNode a b m3 m4 d)
    {μ : Measure ℝ} (hμ : μ ∈ NEFibre a b m3 m4) :
    lowerEnd a m3 u p ≤ rmoment μ p ∧ rmoment μ p ≤ upperEnd b m3 d p := by
  obtain ⟨hrpos, _, har, hrb, _⟩ := CAS13C02.root_properties h
  have ha := h.a_pos
  have hab := h.a_lt_b
  have hb : 0 < b := ha.trans hab
  have hau : a < u := lt_trans har hu.1
  have hu0 : 0 < u := ha.trans hau
  have hd0 : 0 < d := ha.trans hd.1
  have hdb : d < b := lt_trans hd.2.1 hrb
  obtain ⟨-, -, -, hl3, hl4⟩ := CAS13C02.lower_weight_moments h hu
  obtain ⟨-, -, -, hw3, hw4⟩ := CAS13C02.upper_weight_moments h hd
  have hP := hμ.1
  haveI := hP
  have hs := hμ.2.1
  have hip := integrable_rpow_of_mem (p := p) (by linarith) hμ
  have hi3 : Integrable (fun x : ℝ => x ^ 3) μ := integrable_of_Icc hs (continuous_pow 3)
  have hi4 : Integrable (fun x : ℝ => x ^ 4) μ := integrable_of_Icc hs (continuous_pow 4)
  obtain ⟨hA1, hA2, -⟩ := interp_conditions ha hu0 hau.ne p
  obtain ⟨hB1, hB2, -⟩ := interp_conditions hb hd0 hdb.ne' p
  have hA1' : interpC0 a u p + interpC3 a u p * a ^ 3 + interpC4 a u p * a ^ 4 = a ^ p := hA1
  have hA2' : interpC0 a u p + interpC3 a u p * u ^ 3 + interpC4 a u p * u ^ 4 = u ^ p := hA2
  have hB1' : interpC0 b d p + interpC3 b d p * b ^ 3 + interpC4 b d p * b ^ 4 = b ^ p := hB1
  have hB2' : interpC0 b d p + interpC3 b d p * d ^ 3 + interpC4 b d p * d ^ 4 = d ^ p := hB2
  constructor
  · have hmono := integral_mono_ae
      (integrable_hermite μ (c0 := interpC0 a u p) (c3 := interpC3 a u p)
        (c4 := interpC4 a u p) hi3 hi4) hip
      (hs.mono fun x hx => lower_interp_minorant hp ha hau x hx.1)
    rw [integral_hermite μ hi3 hi4 hμ.2.2.1 hμ.2.2.2] at hmono
    have key : lowerEnd a m3 u p =
        interpC0 a u p + interpC3 a u p * m3 + interpC4 a u p * m4 := by
      unfold lowerEnd
      linear_combination (-(1 - CAS13C02.lowerWeight a m3 u)) * hA1' -
        CAS13C02.lowerWeight a m3 u * hA2' + interpC3 a u p * hl3 + interpC4 a u p * hl4
    unfold rmoment
    linarith
  · have hmono := integral_mono_ae hip
      (integrable_hermite μ (c0 := interpC0 b d p) (c3 := interpC3 b d p)
        (c4 := interpC4 b d p) hi3 hi4)
      (hs.mono fun x hx => upper_interp_majorant hp hd0 hdb x (ha.trans_le hx.1) hx.2)
    rw [integral_hermite μ hi3 hi4 hμ.2.2.1 hμ.2.2.2] at hmono
    have key : upperEnd b m3 d p =
        interpC0 b d p + interpC3 b d p * m3 + interpC4 b d p * m4 := by
      unfold upperEnd
      linear_combination (-(1 - CAS13C02.upperWeight b m3 d)) * hB2' -
        CAS13C02.upperWeight b m3 d * hB1' + interpC3 b d p * hw3 + interpC4 b d p * hw4
    unfold rmoment
    linarith

theorem interior_real_sharp {a b m3 m4 p u d : ℝ} (h : CAS13C02.StrictInterior a b m3 m4)
    (hp : 4 < p) (hu : LowerNode a b m3 m4 u) (hd : UpperNode a b m3 m4 d) :
    0 < lowerEnd a m3 u p ∧ lowerEnd a m3 u p ≤ upperEnd b m3 d p ∧
    twoDirac (CAS13C02.lowerWeight a m3 u) a u ∈ NEFibre a b m3 m4 ∧
    rmoment (twoDirac (CAS13C02.lowerWeight a m3 u) a u) p = lowerEnd a m3 u p ∧
    twoDirac (CAS13C02.upperWeight b m3 d) d b ∈ NEFibre a b m3 m4 ∧
    rmoment (twoDirac (CAS13C02.upperWeight b m3 d) d b) p = upperEnd b m3 d p ∧
    RSharpInterval (NEFibre a b m3 m4) p (lowerEnd a m3 u p) (upperEnd b m3 d p) := by
  obtain ⟨hrpos, _, har, hrb, _⟩ := CAS13C02.root_properties h
  have ha := h.a_pos
  have hab := h.a_lt_b
  have hau : a < u := lt_trans har hu.1
  have hu0 : 0 < u := ha.trans hau
  have hdb : d < b := lt_trans hd.2.1 hrb
  have haI : a ∈ Icc a b := ⟨le_rfl, hab.le⟩
  have hbI : b ∈ Icc a b := ⟨hab.le, le_rfl⟩
  have huI : u ∈ Icc a b := ⟨hau.le, hu.2.1.le⟩
  have hdI : d ∈ Icc a b := ⟨hd.1.le, hdb.le⟩
  obtain ⟨hl0, hl1, _, hl3, hl4⟩ := CAS13C02.lower_weight_moments h hu
  obtain ⟨hu0w, hu1w, _, hu3, hu4⟩ := CAS13C02.upper_weight_moments h hd
  have hmemL : twoDirac (CAS13C02.lowerWeight a m3 u) a u ∈ NEFibre a b m3 m4 :=
    ⟨twoDirac_probability hl0.le hl1.le, twoDirac_supported haI huI,
      by rw [moment_twoDirac 3 hl0.le hl1.le]; exact hl3,
      by rw [moment_twoDirac 4 hl0.le hl1.le]; exact hl4⟩
  have hmemU : twoDirac (CAS13C02.upperWeight b m3 d) d b ∈ NEFibre a b m3 m4 :=
    ⟨twoDirac_probability hu0w.le hu1w.le, twoDirac_supported hdI hbI,
      by rw [moment_twoDirac 3 hu0w.le hu1w.le]; exact hu3,
      by rw [moment_twoDirac 4 hu0w.le hu1w.le]; exact hu4⟩
  have hmL : rmoment (twoDirac (CAS13C02.lowerWeight a m3 u) a u) p = lowerEnd a m3 u p := by
    unfold rmoment
    rw [integral_twoDirac (fun x : ℝ => x ^ p) hl0.le hl1.le]
    rfl
  have hmU : rmoment (twoDirac (CAS13C02.upperWeight b m3 d) d b) p = upperEnd b m3 d p := by
    unfold rmoment
    rw [integral_twoDirac (fun x : ℝ => x ^ p) hu0w.le hu1w.le]
    rfl
  have hbd := fun μ (hμ : μ ∈ NEFibre a b m3 m4) => interior_real_bounds h hp hu hd hμ
  have hLU : lowerEnd a m3 u p ≤ upperEnd b m3 d p := by
    have := (hbd _ hmemU).1
    rwa [hmU] at this
  have hpos : 0 < lowerEnd a m3 u p := by
    unfold lowerEnd
    have h1 : 0 < (1 - CAS13C02.lowerWeight a m3 u) * a ^ p :=
      mul_pos (sub_pos.2 hl1) (Real.rpow_pos_of_pos ha p)
    have h2 : 0 ≤ CAS13C02.lowerWeight a m3 u * u ^ p :=
      mul_nonneg hl0.le (Real.rpow_pos_of_pos hu0 p).le
    linarith
  exact ⟨hpos, hLU, hmemL, hmL, hmemU, hmU,
    rsharpInterval_of_extremes (by linarith) hmemL hmemU hmL hmU hbd⟩

/-! ## T5: minimax, boundary branches for every real p, closed region -/

theorem rfibreMinimax_of_rsharpInterval {F : Set (Measure ℝ)} {p L U : ℝ}
    (hL : 0 < L) (hLU : L ≤ U) (hS : RSharpInterval F p L U) : RFibreMinimax F p L U := by
  obtain ⟨hb, ⟨μL, hμL, hmL⟩, ⟨μU, hμU, hmU⟩, -⟩ := hS
  obtain ⟨c1, c2, -, c4⟩ := grstat_cas13_minimax L U hL hLU
  refine ⟨fun μ hμ => c1 _ (hb μ hμ).1 (hb μ hμ).2, ⟨μL, hμL, by rw [hmL]; exact c2⟩,
    fun t => ?_⟩
  rcases le_max_iff.1 (c4 t) with h | h
  · exact ⟨μL, hμL, by rw [hmL]; exact h⟩
  · exact ⟨μU, hμU, by rw [hmU]; exact h⟩

theorem interior_real_sharp_minimax {a b m3 m4 p u d : ℝ} (h : CAS13C02.StrictInterior a b m3 m4)
    (hp : 4 < p) (hu : LowerNode a b m3 m4 u) (hd : UpperNode a b m3 m4 d) :
    RSharpInterval (NEFibre a b m3 m4) p (lowerEnd a m3 u p) (upperEnd b m3 d p) ∧
    RFibreMinimax (NEFibre a b m3 m4) p (lowerEnd a m3 u p) (upperEnd b m3 d p) := by
  obtain ⟨hpos, hLU, -, -, -, -, hS⟩ := interior_real_sharp h hp hu hd
  exact ⟨hS, rfibreMinimax_of_rsharpInterval hpos hLU hS⟩

theorem interior_real_exists {a b m3 m4 p : ℝ} (h : CAS13C02.StrictInterior a b m3 m4)
    (hp : 4 < p) :
    ∃ u d : ℝ, LowerNode a b m3 m4 u ∧ UpperNode a b m3 m4 d ∧
      (∀ u' : ℝ, LowerNode a b m3 m4 u' → u' = u) ∧ (∀ d' : ℝ, UpperNode a b m3 m4 d' → d' = d) ∧
      RSharpInterval (NEFibre a b m3 m4) p (lowerEnd a m3 u p) (upperEnd b m3 d p) ∧
      RFibreMinimax (NEFibre a b m3 m4) p (lowerEnd a m3 u p) (upperEnd b m3 d p) := by
  obtain ⟨u, hu, huq⟩ := CAS13C02.lower_node_existsUnique h
  obtain ⟨d, hd, hdq⟩ := CAS13C02.upper_node_existsUnique h
  obtain ⟨hS, hM⟩ := interior_real_sharp_minimax h hp hu hd
  exact ⟨u, d, hu, hd, fun u' hu' => huq u' hu', fun d' hd' => hdq d' hd', hS, hM⟩

theorem interior_real_nesting {a b m3 m4 p u d : ℝ} (h : CAS13C02.StrictInterior a b m3 m4)
    (hp : 4 < p) (hu : LowerNode a b m3 m4 u) (hd : UpperNode a b m3 m4 d) :
    energyLower m4 p < lowerEnd a m3 u p ∧ lowerEnd a m3 u p ≤ upperEnd b m3 d p ∧
    upperEnd b m3 d p < energyUpper a b m4 p ∧
    Icc (lowerEnd a m3 u p) (upperEnd b m3 d p) ⊆ Icc (energyLower m4 p) (energyUpper a b m4 p) := by
  obtain ⟨hlo, hhi⟩ := endpoint_strict_nesting h hp hu hd
  obtain ⟨-, hLU, -⟩ := interior_real_sharp h hp hu hd
  exact ⟨hlo, hLU, hhi, Icc_subset_Icc hlo.le hhi.le⟩

theorem rmoment_natCast (μ : Measure ℝ) (n : ℕ) : rmoment μ n = moment μ n := by
  unfold rmoment moment
  simp only [Real.rpow_natCast]

theorem interior_sharp_nat {a b m3 m4 u d : ℝ} (h : CAS13C02.StrictInterior a b m3 m4)
    (p : ℕ) (hp : 4 < p) (hu : LowerNode a b m3 m4 u) (hd : UpperNode a b m3 m4 d) :
    SharpInterval (NEFibre a b m3 m4) p (lowerEnd a m3 u p) (upperEnd b m3 d p) ∧
    FibreMinimax (NEFibre a b m3 m4) p (lowerEnd a m3 u p) (upperEnd b m3 d p) := by
  have hp' : (4 : ℝ) < p := by exact_mod_cast hp
  obtain ⟨hS, hM⟩ := interior_real_sharp_minimax h hp' hu hd
  simp only [RSharpInterval, RFibreMinimax, rmoment_natCast] at hS hM
  exact ⟨hS, hM⟩

theorem rsharpInterval_of_const {F : Set (Measure ℝ)} {p v : ℝ} {μ0 : Measure ℝ}
    (h0 : μ0 ∈ F) (hc : ∀ μ ∈ F, rmoment μ p = v) : RSharpInterval F p v v := by
  refine ⟨fun μ hμ => ⟨(hc μ hμ).ge, (hc μ hμ).le⟩, ⟨μ0, h0, hc μ0 h0⟩, ⟨μ0, h0, hc μ0 h0⟩, ?_⟩
  ext m
  simp only [mem_image, mem_Icc]
  constructor
  · rintro ⟨μ, hμ, rfl⟩
    exact ⟨(hc μ hμ).ge, (hc μ hμ).le⟩
  · rintro ⟨h1, h2⟩
    exact ⟨μ0, h0, by rw [hc μ0 h0]; linarith⟩

theorem lower_boundary_rsharp {a b m3 m4 : ℝ} (ha : 0 < a) (hab : a < b)
    (h3 : a ^ 3 ≤ m3) (h3' : m3 ≤ b ^ 3) (hbd : m4 = m3 ^ ((4 : ℝ) / 3)) (p : ℝ) :
    RSharpInterval (NEFibre a b m3 m4) p
      (CAS13C02.positiveCubeRoot m3 ^ p) (CAS13C02.positiveCubeRoot m3 ^ p) ∧
    RFibreMinimax (NEFibre a b m3 m4) p
      (CAS13C02.positiveCubeRoot m3 ^ p) (CAS13C02.positiveCubeRoot m3 ^ p) ∧
    grstatEps (CAS13C02.positiveCubeRoot m3 ^ p) (CAS13C02.positiveCubeRoot m3 ^ p) = 0 := by
  obtain ⟨hr, -⟩ := cube_root_mem ha hab h3 h3'
  have hmem := (lower_boundary_sharp ha hab h3 h3' hbd 0).1
  have hS : RSharpInterval (NEFibre a b m3 m4) p
      (CAS13C02.positiveCubeRoot m3 ^ p) (CAS13C02.positiveCubeRoot m3 ^ p) :=
    rsharpInterval_of_const hmem fun μ hμ => by
      rw [lower_boundary_dirac_collapse ha hab hμ hbd]
      simp only [rmoment, integral_dirac]
  have hpos : 0 < CAS13C02.positiveCubeRoot m3 ^ p := Real.rpow_pos_of_pos hr p
  exact ⟨hS, rfibreMinimax_of_rsharpInterval hpos le_rfl hS, (minimax_degenerate hpos).1⟩

theorem chord_rvalue_pos {a b m3 : ℝ} (ha : 0 < a) (hab : a < b)
    (h3 : a ^ 3 ≤ m3) (h3' : m3 ≤ b ^ 3) (p : ℝ) :
    0 < (1 - CAS13C02.chordWeight a b m3) * a ^ p + CAS13C02.chordWeight a b m3 * b ^ p := by
  have hD := cube_den_pos ha hab
  have hw0 : 0 ≤ CAS13C02.chordWeight a b m3 := div_nonneg (sub_nonneg.2 h3) hD.le
  have hw1 : CAS13C02.chordWeight a b m3 ≤ 1 := (div_le_one hD).2 (by linarith)
  have hap : 0 < a ^ p := Real.rpow_pos_of_pos ha p
  have hbp : 0 < b ^ p := Real.rpow_pos_of_pos (ha.trans hab) p
  rcases hw1.lt_or_eq with hlt | heq
  · have h1 := mul_pos (sub_pos.2 hlt) hap
    have h2 := mul_nonneg hw0 hbp.le
    linarith
  · rw [heq]
    linarith

theorem upper_boundary_rsharp {a b m3 m4 : ℝ} (ha : 0 < a) (hab : a < b)
    (h3 : a ^ 3 ≤ m3) (h3' : m3 ≤ b ^ 3) (hbd : m4 = chord a b m3) (p : ℝ) :
    RSharpInterval (NEFibre a b m3 m4) p
      ((1 - CAS13C02.chordWeight a b m3) * a ^ p + CAS13C02.chordWeight a b m3 * b ^ p)
      ((1 - CAS13C02.chordWeight a b m3) * a ^ p + CAS13C02.chordWeight a b m3 * b ^ p) ∧
    RFibreMinimax (NEFibre a b m3 m4) p
      ((1 - CAS13C02.chordWeight a b m3) * a ^ p + CAS13C02.chordWeight a b m3 * b ^ p)
      ((1 - CAS13C02.chordWeight a b m3) * a ^ p + CAS13C02.chordWeight a b m3 * b ^ p) ∧
    grstatEps ((1 - CAS13C02.chordWeight a b m3) * a ^ p + CAS13C02.chordWeight a b m3 * b ^ p)
      ((1 - CAS13C02.chordWeight a b m3) * a ^ p + CAS13C02.chordWeight a b m3 * b ^ p) = 0 := by
  have hD := cube_den_pos ha hab
  have hw0 : 0 ≤ CAS13C02.chordWeight a b m3 := div_nonneg (sub_nonneg.2 h3) hD.le
  have hw1 : CAS13C02.chordWeight a b m3 ≤ 1 := (div_le_one hD).2 (by linarith)
  have hmem := (upper_boundary_sharp ha hab h3 h3' hbd 0).1
  have hS : RSharpInterval (NEFibre a b m3 m4) p
      ((1 - CAS13C02.chordWeight a b m3) * a ^ p + CAS13C02.chordWeight a b m3 * b ^ p)
      ((1 - CAS13C02.chordWeight a b m3) * a ^ p + CAS13C02.chordWeight a b m3 * b ^ p) :=
    rsharpInterval_of_const hmem fun μ hμ => by
      rw [upper_boundary_endpoint_collapse ha hab hμ hbd]
      unfold rmoment
      exact integral_twoDirac (fun x : ℝ => x ^ p) hw0 hw1
  have hpos := chord_rvalue_pos ha hab h3 h3' p
  exact ⟨hS, rfibreMinimax_of_rsharpInterval hpos le_rfl hS, (minimax_degenerate hpos).1⟩

theorem closed_region_real_sharp_minimax {a b m3 m4 p : ℝ} (ha : 0 < a) (hab : a < b)
    (hreg : ClosedRegion a b m3 m4) (hp : 4 < p) :
    ∃ L U : ℝ, 0 < L ∧ L ≤ U ∧ RSharpInterval (NEFibre a b m3 m4) p L U ∧
      RFibreMinimax (NEFibre a b m3 m4) p L U ∧
      ((m4 = m3 ^ ((4 : ℝ) / 3) ∨ m4 = chord a b m3) →
        L = U ∧ grstatEps L U = 0 ∧ grstatTau L U = L) := by
  have h3 := hreg.1
  have h3' := hreg.2.1
  rcases region_strata ha hab hreg with hI | hL | hU
  · obtain ⟨u, hu, -⟩ := CAS13C02.lower_node_existsUnique hI
    obtain ⟨d, hd, -⟩ := CAS13C02.upper_node_existsUnique hI
    obtain ⟨hpos, hle, -, -, -, -, hS⟩ := interior_real_sharp hI hp hu hd
    refine ⟨_, _, hpos, hle, hS, rfibreMinimax_of_rsharpInterval hpos hle hS, ?_⟩
    rintro (hb | hb)
    · exfalso
      have := hI.lower
      rw [hb] at this
      exact lt_irrefl _ this
    · exfalso
      have := hI.upper
      rw [hb] at this
      exact lt_irrefl _ this
  · obtain ⟨hr, -⟩ := cube_root_mem ha hab h3 h3'
    have hpos : 0 < CAS13C02.positiveCubeRoot m3 ^ p := Real.rpow_pos_of_pos hr p
    obtain ⟨hS, hM, -⟩ := lower_boundary_rsharp ha hab h3 h3' hL p
    exact ⟨_, _, hpos, le_rfl, hS, hM, fun _ => ⟨rfl, minimax_degenerate hpos⟩⟩
  · have hpos := chord_rvalue_pos ha hab h3 h3' p
    obtain ⟨hS, hM, -⟩ := upper_boundary_rsharp ha hab h3 h3' hU p
    exact ⟨_, _, hpos, le_rfl, hS, hM, fun _ => ⟨rfl, minimax_degenerate hpos⟩⟩

/-! ## Negative controls and non-vacuity witnesses -/

theorem wronskian_negative_exponent {y : ℝ} (hy : 0 < y) :
    wronskian (powerSystem (-1)) y < 0 := by
  rw [wronskian_power_system (-1) hy, show (-1 : ℝ) + 1 = 0 by norm_num, Real.rpow_zero]
  norm_num

theorem minorant_fails_negative_exponent :
    (3 / 2 : ℝ) ^ (-1 : ℝ) < interp 1 2 (-1) (3 / 2) := by
  have e1 : (2 : ℝ) ^ ((-1 : ℝ) - 3) = 1 / 16 := by
    rw [show (-1 : ℝ) - 3 = -((4 : ℕ) : ℝ) by norm_num, Real.rpow_neg (by norm_num),
      Real.rpow_natCast]
    norm_num
  have e2 : (2 : ℝ) ^ (-1 : ℝ) = 1 / 2 := by
    rw [Real.rpow_neg_one]
    norm_num
  have e3 : (3 / 2 : ℝ) ^ (-1 : ℝ) = 2 / 3 := by
    rw [Real.rpow_neg_one]
    norm_num
  unfold interp hermite interpC0 interpC3 interpC4 interpDet
  simp only [e1, e2, e3, Real.one_rpow]
  norm_num

theorem real_witness :
    ∃ u d : ℝ, LowerNode 1 2 (9 / 2) 8 u ∧ UpperNode 1 2 (9 / 2) 8 d ∧
      RSharpInterval (NEFibre 1 2 (9 / 2) 8) (9 / 2)
        (lowerEnd 1 (9 / 2) u (9 / 2)) (upperEnd 2 (9 / 2) d (9 / 2)) ∧
      RFibreMinimax (NEFibre 1 2 (9 / 2) 8) (9 / 2)
        (lowerEnd 1 (9 / 2) u (9 / 2)) (upperEnd 2 (9 / 2) d (9 / 2)) := by
  obtain ⟨hI, -⟩ := strictInterior_witness
  obtain ⟨u, hu, -⟩ := CAS13C02.lower_node_existsUnique hI
  obtain ⟨d, hd, -⟩ := CAS13C02.upper_node_existsUnique hI
  obtain ⟨hS, hM⟩ := interior_real_sharp_minimax hI (by norm_num : (4 : ℝ) < 9 / 2) hu hd
  exact ⟨u, d, hu, hd, hS, hM⟩

end CAS13G13C
