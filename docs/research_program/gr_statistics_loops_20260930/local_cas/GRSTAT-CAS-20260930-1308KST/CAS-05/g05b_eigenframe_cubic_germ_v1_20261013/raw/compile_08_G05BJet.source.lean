import Mathlib
import CAS05C03
import G05BCubicDEC

/-!
# G05-B, module 1: first jet of the ACTUAL Einstein tensor of the cubic member

* `Ein_first_jet` (J1): for a `C^3` metric field with `g(0)=η` and `∂g(0)=0`, the actual
  Fréchet derivative of the actual Einstein tensor (G05-A definitions: `fderiv`, matrix inverse,
  Christoffel, CAS-05 Ricci convention) at `0` equals the accepted C03 finite expression
  `CAS05C03.dEinstein` evaluated on the actual third partials of `g` at `0`.
* `thirdJet_gCub` (J2): the actual third partials of `gCub b k = e^{2φ_0}η + H` at `0` are the
  C03 tensor `CAS05C03.J b k` (the conformal baseline has vanishing third jet at `0`).
* `two_jet_preserved` (J3), `dEin_cub`, `dStress_cub` (J4), `dStress_cub_0i` (J5).
-/

namespace G05BJet

open G05AConformalDEC G05BCubicDEC
open scoped Topology

/-- `thirdJet g x y m n d = ∂_m ∂_n ∂_d g_xy (0)` (actual iterated partials). -/
noncomputable def thirdJet (g : (I → ℝ) → I → I → ℝ) (x y m n d : I) : ℝ :=
  pd (fun z => pd (fun w => dg g d x y w) n z) m 0

/-! ## Generic partial-derivative calculus -/

/-- second partial `pd2 F d μ x = ∂_μ ∂_d F (x)`. -/
noncomputable def pd2 (F : (I → ℝ) → ℝ) (d μ : I) (x : I → ℝ) : ℝ :=
  pd (fun y => pd F d y) μ x

theorem pd_congr_nhds {F G : (I → ℝ) → ℝ} {x : I → ℝ} (h : ∀ᶠ y in 𝓝 x, F y = G y) (c : I) :
    pd F c x = pd G c x := by
  unfold pd
  rw [Filter.EventuallyEq.fderiv_eq h]

theorem pd_differentiableAt_of2 {F : (I → ℝ) → ℝ} {x : I → ℝ} (hF : ContDiffAt ℝ 2 F x)
    (d : I) : DifferentiableAt ℝ (fun y => pd F d y) x := by
  unfold pd
  exact ((hF.fderiv_right (m := 1) (by norm_num)).clm_apply contDiffAt_const).differentiableAt
    (by norm_num)

theorem ev_diff2 {F : (I → ℝ) → ℝ} {x : I → ℝ} (hF : ContDiffAt ℝ 2 F x) :
    ∀ᶠ y in 𝓝 x, DifferentiableAt ℝ F y :=
  (hF.eventually (by simp)).mono (fun _ hy => hy.differentiableAt (by norm_num))

theorem pd_contDiffAt_succ {F : (I → ℝ) → ℝ} {x : I → ℝ} {m : ℕ}
    (hF : ContDiffAt ℝ (m + 1) F x) (d : I) : ContDiffAt ℝ m (fun y => pd F d y) x := by
  unfold pd
  exact (hF.fderiv_right (m := m) le_rfl).clm_apply contDiffAt_const

theorem pd_contDiff_succ {F : (I → ℝ) → ℝ} {m : ℕ}
    (hF : ContDiff ℝ (m + 1) F) (d : I) : ContDiff ℝ m (fun y => pd F d y) := by
  unfold pd
  exact (hF.fderiv_right (m := m) le_rfl).clm_apply contDiff_const

theorem pd_sum4 {F : I → (I → ℝ) → ℝ} {x : I → ℝ} (hF : ∀ i, DifferentiableAt ℝ (F i) x)
    (c : I) : pd (fun y => sum4 (fun i => F i y)) c x = sum4 (fun i => pd (F i) c x) := by
  simp only [sum4]
  have h0 := hF 0; have h1 := hF 1; have h2 := hF 2; have h3 := hF 3
  rw [pd_add c (by fun_prop) h3, pd_add c (by fun_prop) h2, pd_add c h0 h1]

theorem pd2_add {F G : (I → ℝ) → ℝ} {x : I → ℝ} (hF : ContDiffAt ℝ 2 F x)
    (hG : ContDiffAt ℝ 2 G x) (d μ : I) :
    pd2 (fun y => F y + G y) d μ x = pd2 F d μ x + pd2 G d μ x := by
  have hev : ∀ᶠ y in 𝓝 x, pd (fun z => F z + G z) d y = pd F d y + pd G d y := by
    filter_upwards [ev_diff2 hF, ev_diff2 hG] with y hFy hGy
    exact pd_add d hFy hGy
  unfold pd2
  rw [pd_congr_nhds hev μ]
  exact pd_add μ (pd_differentiableAt_of2 hF d) (pd_differentiableAt_of2 hG d)

theorem pd2_sub {F G : (I → ℝ) → ℝ} {x : I → ℝ} (hF : ContDiffAt ℝ 2 F x)
    (hG : ContDiffAt ℝ 2 G x) (d μ : I) :
    pd2 (fun y => F y - G y) d μ x = pd2 F d μ x - pd2 G d μ x := by
  have hev : ∀ᶠ y in 𝓝 x, pd (fun z => F z - G z) d y = pd F d y - pd G d y := by
    filter_upwards [ev_diff2 hF, ev_diff2 hG] with y hFy hGy
    exact pd_sub d hFy hGy
  unfold pd2
  rw [pd_congr_nhds hev μ]
  exact pd_sub μ (pd_differentiableAt_of2 hF d) (pd_differentiableAt_of2 hG d)

theorem pd2_mul {F G : (I → ℝ) → ℝ} {x : I → ℝ} (hF : ContDiffAt ℝ 2 F x)
    (hG : ContDiffAt ℝ 2 G x) (d μ : I) :
    pd2 (fun y => F y * G y) d μ x =
      F x * pd2 G d μ x + pd G d x * pd F μ x + (G x * pd2 F d μ x + pd F d x * pd G μ x) := by
  have hev : ∀ᶠ y in 𝓝 x, pd (fun z => F z * G z) d y = F y * pd G d y + G y * pd F d y := by
    filter_upwards [ev_diff2 hF, ev_diff2 hG] with y hFy hGy
    exact pd_mul d hFy hGy
  have hF1 : DifferentiableAt ℝ F x := hF.differentiableAt (by norm_num)
  have hG1 : DifferentiableAt ℝ G x := hG.differentiableAt (by norm_num)
  have hdF := pd_differentiableAt_of2 hF d
  have hdG := pd_differentiableAt_of2 hG d
  unfold pd2
  rw [pd_congr_nhds hev μ, pd_add μ (by fun_prop) (by fun_prop), pd_mul μ hF1 hdG,
    pd_mul μ hG1 hdF]

theorem pd2_const_mul {F : (I → ℝ) → ℝ} {x : I → ℝ} (k : ℝ) (hF : ContDiffAt ℝ 2 F x)
    (d μ : I) : pd2 (fun y => k * F y) d μ x = k * pd2 F d μ x := by
  have h := pd2_mul (F := fun _ => k) (G := F) contDiffAt_const hF d μ
  have h1 : pd2 (fun _ => k) d μ x = 0 := by
    unfold pd2
    simp only [pd_const]
  rw [h, h1, pd_const, pd_const]
  ring

theorem pd2_sum4 {F : I → (I → ℝ) → ℝ} {x : I → ℝ} (hF : ∀ i, ContDiffAt ℝ 2 (F i) x)
    (d μ : I) : pd2 (fun y => sum4 (fun i => F i y)) d μ x = sum4 (fun i => pd2 (F i) d μ x) := by
  simp only [sum4]
  rw [pd2_add (((hF 0).add (hF 1)).add (hF 2)) (hF 3), pd2_add ((hF 0).add (hF 1)) (hF 2),
    pd2_add (hF 0) (hF 1)]

theorem pd_div_const {F : (I → ℝ) → ℝ} {x : I → ℝ} (k : ℝ) (hF : DifferentiableAt ℝ F x)
    (c : I) : pd (fun y => F y / k) c x = pd F c x / k := by
  have e : (fun y => F y / k) = fun y => F y * k⁻¹ := by funext y; ring
  rw [e, pd_mul c hF (differentiableAt_const _), pd_const]
  ring

/-! ## Metric-field regularity at the origin -/

theorem eta_mul_eta : Matrix.of eta * Matrix.of eta = (1 : Matrix I I ℝ) := by
  ext i j
  simp only [Matrix.mul_apply, Fin.sum_univ_four, Matrix.of_apply, Matrix.one_apply]
  fin_cases i <;> fin_cases j <;> simp [eta, delta, sig]

theorem det_eta_ne : (Matrix.of eta : Matrix I I ℝ).det ≠ 0 :=
  Matrix.det_ne_zero_of_right_inverse eta_mul_eta

theorem dg_contDiff3 {g : (I → ℝ) → I → I → ℝ} (hg : ∀ a c, ContDiff ℝ 3 (fun y => g y a c))
    (c a e : I) : ContDiff ℝ 2 (fun y => dg g c a e y) :=
  pd_contDiff_succ (m := 2) (hg a e) c

section Crit

variable (g : (I → ℝ) → I → I → ℝ) (hg : ∀ a c, ContDiff ℝ 3 (fun y => g y a c))
  (h0 : g 0 = eta) (hcrit : ∀ c a e, dg g c a e 0 = 0)

include h0 in
theorem det0 : (toMat g 0).det ≠ 0 := by
  have : toMat g 0 = Matrix.of eta := by unfold toMat; rw [h0]
  rw [this]; exact det_eta_ne

include h0 in
theorem ginv0 (a c : I) : ginv g 0 a c = eta a c := by
  have e : toMat g 0 = Matrix.of eta := by unfold toMat; rw [h0]
  unfold ginv
  rw [e, Matrix.inv_eq_right_inv eta_mul_eta]
  rfl

include hg h0 in
theorem ginv_cd3 (a c : I) : ContDiffAt ℝ 3 (fun y => ginv g y a c) 0 := by
  unfold ginv
  exact contDiffAt_inv_entry (toMat g) (fun i j => hg i j) 0 (det0 g h0) a c

include hg h0 in
theorem ev_ginv_mul (a c : I) :
    ∀ᶠ y in 𝓝 (0 : I → ℝ), sum4 (fun e => ginv g y a e * g y e c) = if a = c then 1 else 0 := by
  have hcont : ContinuousAt (fun y => (toMat g y).det) 0 :=
    (contDiff_det (toMat g) (fun i j => hg i j)).continuous.continuousAt
  filter_upwards [hcont.eventually_ne (det0 g h0)] with y hy
  have hm := Matrix.nonsing_inv_mul (toMat g y) (Ne.isUnit hy)
  have := congrFun (congrFun hm a) c
  simp only [Matrix.mul_apply, Fin.sum_univ_four, Matrix.one_apply] at this
  simp only [sum4, ginv]
  rw [← this]
  rfl

include hg h0 hcrit in
theorem dginv0 (a c μ : I) : pd (fun y => ginv g y a c) μ 0 = 0 := by
  have hev := ev_ginv_mul g hg h0 a c
  have h1 := pd_congr_nhds hev μ
  rw [pd_const] at h1
  have hgi : ∀ e, DifferentiableAt ℝ (fun y => ginv g y a e) 0 :=
    fun e => (ginv_cd3 g hg h0 a e).differentiableAt (by norm_num)
  have hgg : ∀ e, DifferentiableAt ℝ (fun y => g y e c) 0 :=
    fun e => (hg e c).differentiable (by norm_num) 0
  rw [pd_sum4 (F := fun e y => ginv g y a e * g y e c) (fun e => by have := hgi e; have := hgg e; fun_prop)] at h1
  simp only [sum4] at h1
  rw [pd_mul μ (hgi 0) (hgg 0), pd_mul μ (hgi 1) (hgg 1), pd_mul μ (hgi 2) (hgg 2),
    pd_mul μ (hgi 3) (hgg 3)] at h1
  have hz : ∀ e, pd (fun y => g y e c) μ 0 = 0 := fun e => hcrit μ e c
  simp only [hz, h0] at h1
  fin_cases c <;> simp [eta, delta, sig] at h1 ⊢ <;> linarith

include hg h0 in
theorem Gam_cd2 (a i j : I) : ContDiffAt ℝ 2 (fun y => Gam g y a i j) 0 := by
  have h1 : ∀ a c, ContDiffAt ℝ 2 (fun y => ginv g y a c) 0 :=
    fun a c => (ginv_cd3 g hg h0 a c).of_le (by norm_num)
  have h2 : ∀ c a e, ContDiffAt ℝ 2 (fun y => dg g c a e y) 0 :=
    fun c a e => (dg_contDiff3 hg c a e).contDiffAt
  unfold Gam sum4
  fun_prop

include hg h0 in
theorem dGam_diff (d a i j : I) : DifferentiableAt ℝ (fun y => dGam g d a i j y) 0 := by
  unfold dGam
  exact pd_differentiableAt_of2 (Gam_cd2 g hg h0 a i j) d

include hg h0 in
theorem Ric_diff (a i : I) : DifferentiableAt ℝ (fun y => Ric g y a i) 0 := by
  have h1 := dGam_diff g hg h0
  have h2 : ∀ a i j, DifferentiableAt ℝ (fun y => Gam g y a i j) 0 :=
    fun a i j => (Gam_cd2 g hg h0 a i j).differentiableAt (by norm_num)
  unfold Ric sum4
  fun_prop

include hg h0 in
theorem Rsc_diff : DifferentiableAt ℝ (fun y => Rsc g y) 0 := by
  have h1 := Ric_diff g hg h0
  have h2 : ∀ a c, DifferentiableAt ℝ (fun y => ginv g y a c) 0 :=
    fun a c => (ginv_cd3 g hg h0 a c).differentiableAt (by norm_num)
  unfold Rsc sum4
  fun_prop

include hg h0 in
theorem Ein_diff (a c : I) : DifferentiableAt ℝ (fun y => Ein g y a c) 0 := by
  have h1 := Ric_diff g hg h0 a c
  have h2 := Rsc_diff g hg h0
  have h3 : DifferentiableAt ℝ (fun y => g y a c) 0 := (hg a c).differentiable (by norm_num) 0
  unfold Ein
  fun_prop

/-- Second partial of the actual Christoffel symbol at a critical point. -/
theorem dGam_jet (ν a c e μ : I) :
    pd (fun y => dGam g ν a c e y) μ 0 = CAS05C03.ddGamma (thirdJet g) μ ν a c e := by
  sorry

end Crit

end G05BJet
