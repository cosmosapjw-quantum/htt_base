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

include hg h0 hcrit in
/-- Second partial of the actual Christoffel symbol at a critical point. -/
theorem dGam_jet (ν a c e μ : I) :
    pd (fun y => dGam g ν a c e y) μ 0 = CAS05C03.ddGamma (thirdJet g) μ ν a c e := by
  have hdg : ∀ c a e, ContDiffAt ℝ 2 (fun y => dg g c a e y) 0 :=
    fun c a e => (dg_contDiff3 hg c a e).contDiffAt
  have hgi : ∀ r, ContDiffAt ℝ 2 (fun y => ginv g y a r) 0 :=
    fun r => (ginv_cd3 g hg h0 a r).of_le (by norm_num)
  have hG : ∀ r, ContDiffAt ℝ 2
      (fun y => dg g c e r y + dg g e c r y - dg g r c e y) 0 := by
    intro r; have := hdg c e r; have := hdg e c r; have := hdg r c e; fun_prop
  have hterm : ∀ r, pd2 (fun y => ginv g y a r * (dg g c e r y + dg g e c r y - dg g r c e y))
      ν μ 0 = eta a r * (thirdJet g e r μ ν c + thirdJet g c r μ ν e - thirdJet g c e μ ν r) := by
    intro r
    rw [pd2_mul (hgi r) (hG r), dginv0 g hg h0 hcrit a r μ, dginv0 g hg h0 hcrit a r ν,
      ginv0 g h0, hcrit c e r, hcrit e c r, hcrit r c e,
      pd2_sub ((hdg c e r).add (hdg e c r)) (hdg r c e), pd2_add (hdg c e r) (hdg e c r)]
    simp only [pd2, thirdJet]
    ring
  change pd2 (fun z => Gam g z a c e) ν μ 0 = _
  have e2 : (fun z => Gam g z a c e) = fun z => (1 / 2 : ℝ) *
      sum4 (fun r => ginv g z a r * (dg g c e r z + dg g e c r z - dg g r c e z)) := rfl
  have hsum : ContDiffAt ℝ 2 (fun z => sum4 (fun r =>
      ginv g z a r * (dg g c e r z + dg g e c r z - dg g r c e z))) 0 := by
    have h0' := hgi 0; have h1' := hgi 1; have h2' := hgi 2; have h3' := hgi 3
    have k0 := hG 0; have k1 := hG 1; have k2 := hG 2; have k3 := hG 3
    unfold sum4; fun_prop
  rw [e2, pd2_const_mul _ hsum,
    pd2_sum4 (F := fun r z => ginv g z a r * (dg g c e r z + dg g e c r z - dg g r c e z))
      (fun r => (hgi r).mul (hG r))]
  simp only [hterm]
  simp only [CAS05C03.ddGamma, CAS05C03.sum4, sum4]
  fin_cases a <;> simp [eta, delta, sig, CAS05C03.sig, CAS05C03.delta]

include hg h0 hcrit in
theorem Ric_jet (μ a i : I) :
    pd (fun y => Ric g y a i) μ 0 = CAS05C03.dRicci (thirdJet g) μ a i := by
  have hdGd := dGam_diff g hg h0
  have hGd : ∀ a i j, DifferentiableAt ℝ (fun y => Gam g y a i j) 0 :=
    fun a i j => (Gam_cd2 g hg h0 a i j).differentiableAt (by norm_num)
  have hGam0 : ∀ a i j, Gam g 0 a i j = 0 := Gam_crit g hcrit
  have hsummand : ∀ c, pd (fun y => dGam g c c i a y - dGam g i c c a y +
      sum4 (fun e => Gam g y c c e * Gam g y e i a - Gam g y c i e * Gam g y e c a)) μ 0 =
      CAS05C03.ddGamma (thirdJet g) μ c c i a - CAS05C03.ddGamma (thirdJet g) μ i c c a := by
    intro c
    have hinner : ∀ e, pd (fun y => Gam g y c c e * Gam g y e i a - Gam g y c i e * Gam g y e c a)
        μ 0 = 0 := by
      intro e
      have a1 := hGd c c e; have a2 := hGd e i a; have a3 := hGd c i e; have a4 := hGd e c a
      rw [pd_sub μ (by fun_prop) (by fun_prop), pd_mul μ a1 a2, pd_mul μ a3 a4]
      simp [hGam0]
    have hsd : DifferentiableAt ℝ (fun y => sum4 (fun e =>
        Gam g y c c e * Gam g y e i a - Gam g y c i e * Gam g y e c a)) 0 := by
      unfold sum4; fun_prop
    have b1 := hdGd c c i a; have b2 := hdGd i c c a
    rw [pd_add μ (by fun_prop) hsd, pd_sub μ b1 b2,
      pd_sum4 (F := fun e y => Gam g y c c e * Gam g y e i a - Gam g y c i e * Gam g y e c a)
        (fun e => by have := hGd c c e; have := hGd e i a; have := hGd c i e;
                     have := hGd e c a; fun_prop)]
    simp only [hinner, sum4, add_zero]
    rw [dGam_jet g hg h0 hcrit, dGam_jet g hg h0 hcrit]
  have e1 : (fun y => Ric g y a i) = fun y => sum4 (fun c => dGam g c c i a y - dGam g i c c a y +
      sum4 (fun e => Gam g y c c e * Gam g y e i a - Gam g y c i e * Gam g y e c a)) := rfl
  rw [e1, pd_sum4 (F := fun c y => dGam g c c i a y - dGam g i c c a y +
      sum4 (fun e => Gam g y c c e * Gam g y e i a - Gam g y c i e * Gam g y e c a))
      (fun c => by
        have := hdGd c c i a; have := hdGd i c c a
        have := hGd; unfold sum4; fun_prop)]
  simp only [hsummand]
  simp only [CAS05C03.dRicci, CAS05C03.sum4, sum4]

include hg h0 hcrit in
/-- Section form of J1. -/
theorem Ein_first_jet_sec (μ a c : I) :
    pd (fun y => Ein g y a c) μ 0 = CAS05C03.dEinstein (thirdJet g) μ a c := by
  have hRic := Ric_diff g hg h0
  have hRsc := Rsc_diff g hg h0
  have hgd : ∀ a c, DifferentiableAt ℝ (fun y => g y a c) 0 :=
    fun a c => (hg a c).differentiable (by norm_num) 0
  have hgi : ∀ a c, DifferentiableAt ℝ (fun y => ginv g y a c) 0 :=
    fun a c => (ginv_cd3 g hg h0 a c).differentiableAt (by norm_num)
  have hpdg : pd (fun y => g y a c) μ 0 = 0 := hcrit μ a c
  have hRsc_jet : pd (fun y => Rsc g y) μ 0 =
      sum4 (fun a => sum4 (fun c => eta a c * CAS05C03.dRicci (thirdJet g) μ a c)) := by
    have e1 : (fun y => Rsc g y) =
        fun y => sum4 (fun a => sum4 (fun c => ginv g y a c * Ric g y a c)) := rfl
    rw [e1, pd_sum4 (F := fun a y => sum4 (fun c => ginv g y a c * Ric g y a c))
      (fun a => by have := hgi; have := hRic; unfold sum4; fun_prop)]
    congr 1; funext a'
    rw [pd_sum4 (F := fun c y => ginv g y a' c * Ric g y a' c)
      (fun c => by have := hgi a' c; have := hRic a' c; fun_prop)]
    congr 1; funext c'
    rw [pd_mul μ (hgi a' c') (hRic a' c'), dginv0 g hg h0 hcrit, ginv0 g h0,
      Ric_jet g hg h0 hcrit]
    ring
  have e1 : (fun y => Ein g y a c) = fun y => Ric g y a c - g y a c * Rsc g y / 2 := rfl
  have hd2 : DifferentiableAt ℝ (fun y => g y a c * Rsc g y) 0 := by
    have := hgd a c; fun_prop
  rw [e1, pd_sub μ (hRic a c) (by fun_prop), pd_div_const 2 hd2, pd_mul μ (hgd a c) hRsc,
    hpdg, hRsc_jet, Ric_jet g hg h0 hcrit, h0]
  simp only [CAS05C03.dEinstein, CAS05C03.sum4, sum4]
  fin_cases a <;> fin_cases c <;>
    simp [eta, delta, sig, CAS05C03.eta, CAS05C03.sig, CAS05C03.delta] <;> ring

end Crit

/-- **J1.** First jet of the ACTUAL Einstein tensor at a critical point with `g(0)=η`. -/
theorem Ein_first_jet (g : (I → ℝ) → I → I → ℝ)
    (hg : ∀ a c, ContDiff ℝ 3 (fun y => g y a c))
    (h0 : g 0 = eta) (hcrit : ∀ c a e, dg g c a e 0 = 0) (μ a c : I) :
    pd (fun y => Ein g y a c) μ 0 = CAS05C03.dEinstein (thirdJet g) μ a c := by
  exact Ein_first_jet_sec g hg h0 hcrit μ a c

/-! ## Cubic member: third jet, 2-jet, and first jet of the actual stress -/

theorem sdelta_comm (a c : I) : sdelta a c = sdelta c a := by
  fin_cases a <;> fin_cases c <;> simp [sdelta, delta]

theorem S_comm (b : ℝ) (k : I → I → ℝ) (i j : I) : S b k i j = S b k j i := by
  unfold S; ring

theorem J_swap12 (b : ℝ) (k : I → I → ℝ) (a c d e f : I) :
    J b k a c d e f = J b k a c e d f := by
  simp only [J, J0i, Jii, sdelta_comm e d, S_comm b k e d]
  split_ifs <;> ring

theorem J_swap23 (b : ℝ) (k : I → I → ℝ) (a c d e f : I) :
    J b k a c d e f = J b k a c d f e := by
  simp only [J, J0i, Jii, sdelta_comm f e, S_comm b k f e]
  split_ifs <;> ring

theorem J_eq (b : ℝ) (k : I → I → ℝ) (a c d e f : I) :
    G05BCubicDEC.J b k a c d e f = CAS05C03.J b k a c d e f := rfl

theorem pd_quad (Q : I → I → ℝ) (c : I) (x : I → ℝ) :
    pd (fun y => sum4 (fun e => sum4 (fun f => Q e f * y e * y f))) c x =
      sum4 (fun f => (Q c f + Q f c) * x f) := by
  simp only [sum4]
  simp (disch := fun_prop) only [pd_add, pd_mul, pd_coord, pd_const]
  fin_cases c <;> simp <;> ring

theorem pd_lin (L : I → ℝ) (c : I) (x : I → ℝ) :
    pd (fun y => sum4 (fun f => L f * y f)) c x = L c := by
  simp only [sum4]
  simp (disch := fun_prop) only [pd_add, pd_mul, pd_coord, pd_const]
  fin_cases c <;> simp

theorem thirdJet_H (b : ℝ) (k : I → I → ℝ) (x y m n d : I) :
    pd (fun z => pd (fun w => pd (fun v => H b k x y v) d w) n z) m 0 = J b k x y m n d := by
  set Q : I → I → ℝ := fun e f =>
    J b k x y d e f / 6 + J b k x y e d f / 6 + J b k x y e f d / 6 with hQ
  have e1 : (fun w => pd (fun v => H b k x y v) d w) =
      fun w => sum4 (fun e => sum4 (fun f => Q e f * w e * w f)) := funext (pd_H b k x y d)
  have e2 : (fun z => pd (fun w => sum4 (fun e => sum4 (fun f => Q e f * w e * w f))) n z) =
      fun z => sum4 (fun f => (Q n f + Q f n) * z f) := funext (pd_quad Q n)
  rw [e1, e2, pd_lin]
  simp only [hQ]
  have s1 := J_swap12 b k x y n m d
  have s2 := J_swap23 b k x y m d n
  have s3 := J_swap12 b k x y d m n
  have s4 := J_swap23 b k x y n d m
  have s5 := J_swap12 b k x y d n m
  linarith

@[fun_prop] theorem hPhi_differentiable (b lam : ℝ) (a c : I) :
    Differentiable ℝ (fun y => hPhi b lam y a c) := by
  unfold hPhi; fun_prop

theorem pd_hPhi0 (b : ℝ) (a c d : I) (y : I → ℝ) : pd (fun z => hPhi b 0 z a c) d y = 0 := by
  have e : (fun z => hPhi b 0 z a c) = fun _ => hPhi b 0 0 a c := by
    funext z; simp [hPhi]
  rw [e, pd_const]

theorem thirdJet_conf (b : ℝ) (x y m n d : I) :
    pd (fun z => pd (fun w => dg (gConf b 0) d x y w) n z) m 0 = 0 := by
  have e1 : (fun w => dg (gConf b 0) d x y w) =
      fun w => 2 * Real.exp (2 * phi b 0 w) * pPhi b 0 w d * eta x y := funext (dg_conf b 0 d x y)
  rw [e1]
  simp (disch := fun_prop) only [pd_mul, pd_exp, pd_const, pd_phi, pd_pPhi]
  simp (disch := fun_prop) only [pd_mul, pd_add, pd_exp, pd_const, pd_phi, pd_pPhi, pd_hPhi0]
  simp [pPhi_origin]

theorem thirdJet_gCub (b : ℝ) (k : I → I → ℝ) (x y m n d : I) :
    thirdJet (gCub b k) x y m n d = CAS05C03.J b k x y m n d := by
  have hc : ∀ c a e, ContDiff ℝ 2 (fun y => dg (gConf b 0) c a e y) :=
    fun c a e => dg_contDiff3 (fun a c => gConf_contDiff b 0 a c) c a e
  have hh : ∀ a c e, ContDiff ℝ 2 (fun y => pd (fun z => H b k a c z) e y) :=
    fun a c e => pd_contDiff_succ (m := 2) (H_contDiff b k a c) e
  have e1 : (fun w => dg (gCub b k) d x y w) =
      fun w => dg (gConf b 0) d x y w + pd (fun z => H b k x y z) d w :=
    funext (dg_cub_split b k d x y)
  have e2 : (fun z => pd (fun w => dg (gConf b 0) d x y w + pd (fun z => H b k x y z) d w) n z) =
      fun z => pd (fun w => dg (gConf b 0) d x y w) n z +
        pd (fun w => pd (fun z => H b k x y z) d w) n z := by
    funext z
    exact pd_add n ((hc d x y).differentiable (by norm_num) z)
      ((hh x y d).differentiable (by norm_num) z)
  unfold thirdJet
  rw [e1, e2, pd_add m (((pd_contDiff_succ (m := 1) (hc d x y) n)).differentiable (by norm_num) 0)
      ((pd_contDiff_succ (m := 1) (hh x y d) n).differentiable (by norm_num) 0),
    thirdJet_conf, thirdJet_H, zero_add, J_eq]

/-- **J3.** `j²H = 0`: the cubic member has the 2-jet of `g^(0) = e^{2φ_0}η` at the origin. -/
theorem two_jet_preserved (b : ℝ) (k : I → I → ℝ) :
    gCub b k 0 = gConf b 0 0 ∧
    (∀ c a e, dg (gCub b k) c a e 0 = dg (gConf b 0) c a e 0) ∧
    (∀ d c a e, pd (fun y => dg (gCub b k) c a e y) d 0 =
      pd (fun y => dg (gConf b 0) c a e y) d 0) :=
  ⟨gCub_origin b k, fun c a e => by rw [cub_crit, conf_crit], cub_jet b k⟩

theorem gCub_smooth3 (b : ℝ) (k : I → I → ℝ) (a c : I) :
    ContDiff ℝ 3 (fun y => gCub b k y a c) := gCub_contDiff b k a c

/-- **J4.** All 40 first derivatives of the actual Einstein tensor of the cubic member. -/
theorem dEin_cub (b : ℝ) (k : I → I → ℝ) (μ a c : I) :
    pd (fun y => Ein (gCub b k) y a c) μ 0 = CAS05C03.closedDG b k μ a c := by
  rw [Ein_first_jet (gCub b k) (gCub_smooth3 b k) (gCub_origin_eta b k) (cub_crit b k)]
  have : thirdJet (gCub b k) = CAS05C03.J b k := by
    funext x y m n d; exact thirdJet_gCub b k x y m n d
  rw [this]
  exact CAS05C03.full40_first_Einstein_coefficients b k μ a c

theorem dStress_cub (b : ℝ) (k : I → I → ℝ) (Λ κ : ℝ) (μ a c : I) :
    pd (fun y => stress (gCub b k) Λ κ y a c) μ 0 = CAS05C03.closedDG b k μ a c / κ := by
  have hE := Ein_diff (gCub b k) (gCub_smooth3 b k) (gCub_origin_eta b k) a c
  have hg : DifferentiableAt ℝ (fun y => gCub b k y a c) 0 :=
    (gCub_smooth3 b k a c).differentiable (by norm_num) 0
  have e1 : (fun y => stress (gCub b k) Λ κ y a c) =
      fun y => (Ein (gCub b k) y a c + Λ * gCub b k y a c) / κ := rfl
  have hpdg : pd (fun y => gCub b k y a c) μ 0 = 0 := cub_crit b k μ a c
  rw [e1, pd_div_const κ (by fun_prop), pd_add μ hE (by fun_prop),
    pd_mul μ (differentiableAt_const Λ) hg, hpdg, pd_const, dEin_cub]
  ring

/-- **J5.** The prescribed derivative stress: `∂_0 T_0i(0) = q_i/κ`, `∂_j T_0i(0) = M_ij/κ`. -/
theorem dStress_cub_0i (b : ℝ) (k : I → I → ℝ) (Λ κ : ℝ) (μ i : I) (hi : i ≠ 0) :
    pd (fun y => stress (gCub b k) Λ κ y 0 i) μ 0 =
      (if μ = 0 then q b k i else M b k i μ) / κ := by
  rw [dStress_cub]
  by_cases hμ : μ = 0
  · subst hμ; simp [CAS05C03.closedDG, hi]; rfl
  · simp [CAS05C03.closedDG, hi, hμ]; rfl

end G05BJet
