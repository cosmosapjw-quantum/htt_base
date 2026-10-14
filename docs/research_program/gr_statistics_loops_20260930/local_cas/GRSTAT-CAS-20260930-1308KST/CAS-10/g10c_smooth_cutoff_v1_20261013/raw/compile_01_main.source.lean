import Mathlib

/-!
# G10-C: smooth mollified radial cutoff from the C04 finite quintic cutoff

Source: INFORMATION_LIMIT_THEOREMS.md Theorem III construction
(sha256 775b7d151d894dc33e3896e9e00674a8de6e2432c7bf96ad5ee70d64f2b63b1a) and the accepted
C04 quintic (CutoffExtrema.lean sha256 ab2f98d27e4d00694c428258e78a81dd438d38066b5d28c08090fd2c12b7c1f3).

* `q0 a` is the source's finite quintic cutoff on ℝ.  It is `C^2` and **not** `C^3`
  (hence not `C^∞`): `q0_contDiff_two`, `q0_not_contDiff_three`, `q0_not_smooth`.
* `smoothCutoff a ρ = ρ ⋆ qe a` for any nonnegative unit-integral `C^∞` mollifier `ρ`
  supported in `[-a/8, a/8]`; it is `C^∞`, in `[0,1]`, `= 1` on `|r| ≤ a/8`, `= 0` on
  `|r| ≥ 7a/8`, with the *same* derivative bounds `15/(4a)` and `40/(√3 a²)`.
* On `r ≥ -a/8` it coincides with the source's literal convolution `ρ ⋆ q0 a`.
* `x ↦ smoothCutoff a ρ ‖x‖` is `C^∞` on any real inner product space.
-/

namespace G10C

open MeasureTheory Set Filter Topology

/-! ## C04 quintic (verbatim definitions and the C04 bound proofs) -/

noncomputable def F (t : ℝ) : ℝ := 1 - 10*t^3 + 15*t^4 - 6*t^5
noncomputable def Fp (t : ℝ) : ℝ := -30*t^2*(1-t)^2
noncomputable def Fpp (t : ℝ) : ℝ := -60*t*(1-t)*(1-2*t)
noncomputable def Fppp (t : ℝ) : ℝ := -60*(1 - 6*t + 6*t^2)

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

theorem Fpp_hasDerivAt (t : ℝ) : HasDerivAt Fpp (Fppp t) t := by
  have hf : Fpp = fun y : ℝ => -60*y + 180*y^2 - 120*y^3 := by
    funext y; unfold Fpp; ring
  rw [hf]
  have h1 : HasDerivAt (fun y : ℝ => -60*y) (-60) t := by
    simpa using (hasDerivAt_id' t).const_mul (-60:ℝ)
  have h2 : HasDerivAt (fun y : ℝ => 180*y^2) (180*(2*t)) t := by
    simpa using (hasDerivAt_pow 2 t).const_mul (180:ℝ)
  have h3 : HasDerivAt (fun y : ℝ => 120*y^3) (120*(3*t^2)) t := by
    simpa using (hasDerivAt_pow 3 t).const_mul (120:ℝ)
  have h := (h1.add h2).sub h3
  convert h using 1
  unfold Fppp; ring

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

theorem F_mem (t : ℝ) (ht0 : 0 ≤ t) (ht1 : t ≤ 1) : 0 ≤ F t ∧ F t ≤ 1 := by
  have h1 : F t = (1-t)^3*(1+3*t+6*t^2) := by unfold F; ring
  have h2 : F t = 1 - t^3*(10-15*t+6*t^2) := by unfold F; ring
  have hq : 0 < 10-15*t+6*t^2 := by nlinarith [sq_nonneg (t - 5/4)]
  constructor
  · rw [h1]; apply mul_nonneg
    · exact pow_nonneg (by linarith) 3
    · nlinarith
  · rw [h2]; have : 0 ≤ t^3*(10-15*t+6*t^2) := mul_nonneg (pow_nonneg ht0 3) hq.le
    linarith

/-! ## Clamping to `[0,1]`: the piecewise extension of a polynomial with flat endpoint jets -/

noncomputable def clamp01 (t : ℝ) : ℝ := max 0 (min t 1)

theorem continuous_clamp01 : Continuous clamp01 :=
  continuous_const.max (continuous_id.min continuous_const)

theorem clamp01_mem (t : ℝ) : 0 ≤ clamp01 t ∧ clamp01 t ≤ 1 :=
  ⟨le_max_left _ _, max_le zero_le_one (min_le_right _ _)⟩

theorem clamp01_of_nonpos {t : ℝ} (h : t ≤ 0) : clamp01 t = 0 := by
  unfold clamp01; exact max_eq_left (le_trans (min_le_left _ _) h)

theorem clamp01_of_one_le {t : ℝ} (h : 1 ≤ t) : clamp01 t = 1 := by
  unfold clamp01; rw [min_eq_right h, max_eq_right zero_le_one]

theorem clamp01_of_mem {t : ℝ} (h0 : 0 ≤ t) (h1 : t ≤ 1) : clamp01 t = t := by
  unfold clamp01; rw [min_eq_left h1, max_eq_right h0]

theorem comp_clamp_hasDerivAt (P P' : ℝ → ℝ) (hP : ∀ t, HasDerivAt P (P' t) t)
    (h0 : P' 0 = 0) (h1 : P' 1 = 0) (t : ℝ) :
    HasDerivAt (fun s => P (clamp01 s)) (P' (clamp01 t)) t := by
  rcases lt_trichotomy t 0 with ht | ht | ht
  · have hev : (fun s => P (clamp01 s)) =ᶠ[𝓝 t] fun _ => P 0 := by
      filter_upwards [Iio_mem_nhds ht] with s hs
      rw [clamp01_of_nonpos (le_of_lt hs)]
    rw [clamp01_of_nonpos ht.le, h0]
    exact (hasDerivAt_const t (P 0)).congr_of_eventuallyEq hev
  · subst ht
    rw [clamp01_of_nonpos le_rfl, h0]
    have hl : HasDerivWithinAt (fun s => P (clamp01 s)) 0 (Iic 0) 0 := by
      apply (hasDerivWithinAt_const (0:ℝ) (Iic 0) (P 0)).congr
      · intro s hs; show P (clamp01 s) = P 0; rw [clamp01_of_nonpos hs]
      · show P (clamp01 0) = P 0; rw [clamp01_of_nonpos le_rfl]
    have hr : HasDerivWithinAt (fun s => P (clamp01 s)) 0 (Ici 0) 0 := by
      have h := (hP 0).hasDerivWithinAt (s := Ici 0)
      rw [h0] at h
      apply h.congr_of_eventuallyEq
      · filter_upwards [Icc_mem_nhdsGE (zero_lt_one' ℝ)] with s hs
        rw [clamp01_of_mem hs.1 hs.2]
      · rw [clamp01_of_mem le_rfl zero_le_one]
    have h := hl.union hr
    rw [Iic_union_Ici] at h
    exact hasDerivWithinAt_univ.mp h
  · rcases lt_trichotomy t 1 with ht1 | ht1 | ht1
    · have hev : (fun s => P (clamp01 s)) =ᶠ[𝓝 t] P := by
        filter_upwards [Ioo_mem_nhds ht ht1] with s hs
        rw [clamp01_of_mem hs.1.le hs.2.le]
      rw [clamp01_of_mem ht.le ht1.le]
      exact (hP t).congr_of_eventuallyEq hev
    · subst ht1
      rw [clamp01_of_one_le le_rfl, h1]
      have hr : HasDerivWithinAt (fun s => P (clamp01 s)) 0 (Ici 1) 1 := by
        apply (hasDerivWithinAt_const (1:ℝ) (Ici 1) (P 1)).congr
        · intro s hs; show P (clamp01 s) = P 1; rw [clamp01_of_one_le hs]
        · show P (clamp01 1) = P 1; rw [clamp01_of_one_le le_rfl]
      have hl : HasDerivWithinAt (fun s => P (clamp01 s)) 0 (Iic 1) 1 := by
        have h := (hP 1).hasDerivWithinAt (s := Iic 1)
        rw [h1] at h
        apply h.congr_of_eventuallyEq
        · filter_upwards [Icc_mem_nhdsLE (zero_lt_one' ℝ)] with s hs
          rw [clamp01_of_mem hs.1 hs.2]
        · rw [clamp01_of_mem zero_le_one le_rfl]
      have h := hl.union hr
      rw [Iic_union_Ici] at h
      exact hasDerivWithinAt_univ.mp h
    · have hev : (fun s => P (clamp01 s)) =ᶠ[𝓝 t] fun _ => P 1 := by
        filter_upwards [Ioi_mem_nhds ht1] with s hs
        rw [clamp01_of_one_le (le_of_lt hs)]
      rw [clamp01_of_one_le ht1.le, h1]
      exact (hasDerivAt_const t (P 1)).congr_of_eventuallyEq hev

/-! ## The normalized `C^2` step `G` (= 1 on `t ≤ 0`, `F` on `[0,1]`, 0 on `t ≥ 1`) -/

noncomputable def G (t : ℝ) : ℝ := F (clamp01 t)
noncomputable def Gp (t : ℝ) : ℝ := Fp (clamp01 t)
noncomputable def Gpp (t : ℝ) : ℝ := Fpp (clamp01 t)

theorem G_hasDerivAt (t : ℝ) : HasDerivAt G (Gp t) t :=
  comp_clamp_hasDerivAt F Fp F_hasDerivAt (by norm_num [Fp]) (by norm_num [Fp]) t

theorem Gp_hasDerivAt (t : ℝ) : HasDerivAt Gp (Gpp t) t :=
  comp_clamp_hasDerivAt Fp Fpp Fp_hasDerivAt (by norm_num [Fpp]) (by norm_num [Fpp]) t

theorem continuous_Fpp : Continuous Fpp :=
  continuous_iff_continuousAt.2 fun t => (Fpp_hasDerivAt t).continuousAt

theorem continuous_Gpp : Continuous Gpp := continuous_Fpp.comp continuous_clamp01

theorem deriv_G : deriv G = Gp := funext fun t => (G_hasDerivAt t).deriv
theorem deriv_Gp : deriv Gp = Gpp := funext fun t => (Gp_hasDerivAt t).deriv

theorem G_contDiff_two : ContDiff ℝ 2 G := by
  have h1 : ContDiff ℝ 1 Gp := by
    rw [contDiff_one_iff_deriv, deriv_Gp]
    exact ⟨fun t => (Gp_hasDerivAt t).differentiableAt, continuous_Gpp⟩
  have h2 : ContDiff ℝ (1 + 1) G := by
    rw [contDiff_succ_iff_deriv, deriv_G]
    exact ⟨fun t => (G_hasDerivAt t).differentiableAt, by simp, h1⟩
  exact h2

theorem G_eq_one {t : ℝ} (h : t ≤ 0) : G t = 1 := by
  show F (clamp01 t) = 1; rw [clamp01_of_nonpos h]; norm_num [F]
theorem G_eq_zero {t : ℝ} (h : 1 ≤ t) : G t = 0 := by
  show F (clamp01 t) = 0; rw [clamp01_of_one_le h]; norm_num [F]
theorem G_eq_F {t : ℝ} (h0 : 0 ≤ t) (h1 : t ≤ 1) : G t = F t := by
  show F (clamp01 t) = F t; rw [clamp01_of_mem h0 h1]
theorem Gp_eq_zero {t : ℝ} (h : t ≤ 0) : Gp t = 0 := by
  show Fp (clamp01 t) = 0; rw [clamp01_of_nonpos h]; norm_num [Fp]
theorem Gpp_eq_zero {t : ℝ} (h : t ≤ 0) : Gpp t = 0 := by
  show Fpp (clamp01 t) = 0; rw [clamp01_of_nonpos h]; norm_num [Fpp]

theorem G_mem (t : ℝ) : 0 ≤ G t ∧ G t ≤ 1 :=
  F_mem _ (clamp01_mem t).1 (clamp01_mem t).2
theorem Gp_abs_le (t : ℝ) : |Gp t| ≤ 15/8 :=
  fp_abs_bound _ (clamp01_mem t).1 (clamp01_mem t).2
theorem Gpp_abs_le (t : ℝ) : |Gpp t| ≤ 10/Real.sqrt 3 :=
  fpp_abs_bound _ (clamp01_mem t).1 (clamp01_mem t).2

/-- The step `G` is not `C^3`: its second derivative has one-sided derivatives `0` and
`F'''(0) = -60` at `t = 0`. -/
theorem G_not_contDiff_three : ¬ ContDiff ℝ 3 G := by
  intro h
  have h3 : ContDiff ℝ (2 + 1) G := h
  obtain ⟨-, -, h2⟩ := contDiff_succ_iff_deriv.mp h3
  rw [deriv_G] at h2
  have h2' : ContDiff ℝ (1 + 1) Gp := h2
  obtain ⟨-, -, h1⟩ := contDiff_succ_iff_deriv.mp h2'
  rw [deriv_Gp] at h1
  have hD := ((h1.differentiable one_ne_zero) 0).hasDerivAt
  have hl : HasDerivWithinAt Gpp 0 (Iic 0) 0 := by
    apply (hasDerivWithinAt_const (0:ℝ) (Iic (0:ℝ)) (0:ℝ)).congr
    · intro s hs; exact Gpp_eq_zero hs
    · exact Gpp_eq_zero le_rfl
  have hr : HasDerivWithinAt Gpp (-60) (Ici 0) 0 := by
    have h := (Fpp_hasDerivAt 0).hasDerivWithinAt (s := Ici 0)
    have hv : Fppp 0 = -60 := by norm_num [Fppp]
    rw [hv] at h
    apply h.congr_of_eventuallyEq
    · filter_upwards [Icc_mem_nhdsGE (zero_lt_one' ℝ)] with s hs
      show Fpp (clamp01 s) = Fpp s; rw [clamp01_of_mem hs.1 hs.2]
    · show Fpp (clamp01 0) = Fpp 0; rw [clamp01_of_mem le_rfl zero_le_one]
  have e1 := (uniqueDiffWithinAt_Iic (0:ℝ)).eq_deriv _ hD.hasDerivWithinAt hl
  have e2 := (uniqueDiffWithinAt_Ici (0:ℝ)).eq_deriv _ hD.hasDerivWithinAt hr
  linarith

/-! ## The source's finite quintic cutoff `q0` on ℝ -/

/-- Source: `q0(r)=1` for `r ≤ a/4`, `F(2r/a-1/2)` on `[a/4,3a/4]`, `0` afterwards. -/
noncomputable def q0 (a r : ℝ) : ℝ := G (2*r/a - 1/2)
noncomputable def q0p (a r : ℝ) : ℝ := Gp (2*r/a - 1/2) * (2/a)
noncomputable def q0pp (a r : ℝ) : ℝ := Gpp (2*r/a - 1/2) * (2/a) * (2/a)

theorem arg_le_zero {a r : ℝ} (ha : 0 < a) (hr : r ≤ a/4) : 2*r/a - 1/2 ≤ 0 := by
  have : 2*r/a ≤ 1/2 := by rw [div_le_iff₀ ha]; linarith
  linarith

theorem one_le_arg {a r : ℝ} (ha : 0 < a) (hr : 3*a/4 ≤ r) : 1 ≤ 2*r/a - 1/2 := by
  have : 3/2 ≤ 2*r/a := by rw [le_div_iff₀ ha]; linarith
  linarith

theorem q0_eq_one {a r : ℝ} (ha : 0 < a) (hr : r ≤ a/4) : q0 a r = 1 :=
  G_eq_one (arg_le_zero ha hr)

theorem q0_eq_F {a r : ℝ} (ha : 0 < a) (h1 : a/4 ≤ r) (h2 : r ≤ 3*a/4) :
    q0 a r = F (2*r/a - 1/2) := by
  apply G_eq_F
  · have : 1/2 ≤ 2*r/a := by rw [le_div_iff₀ ha]; linarith
    linarith
  · have : 2*r/a ≤ 3/2 := by rw [div_le_iff₀ ha]; linarith
    linarith

theorem q0_eq_zero {a r : ℝ} (ha : 0 < a) (hr : 3*a/4 ≤ r) : q0 a r = 0 :=
  G_eq_zero (one_le_arg ha hr)

theorem q0p_eq_zero {a r : ℝ} (ha : 0 < a) (hr : r ≤ a/4) : q0p a r = 0 := by
  unfold q0p; rw [Gp_eq_zero (arg_le_zero ha hr)]; ring

theorem q0pp_eq_zero {a r : ℝ} (ha : 0 < a) (hr : r ≤ a/4) : q0pp a r = 0 := by
  unfold q0pp; rw [Gpp_eq_zero (arg_le_zero ha hr)]; ring

theorem q0_mem (a r : ℝ) : 0 ≤ q0 a r ∧ q0 a r ≤ 1 := G_mem _

theorem affine_hasDerivAt (a r : ℝ) : HasDerivAt (fun r : ℝ => 2*r/a - 1/2) (2/a) r := by
  have h := (((hasDerivAt_id' r).const_mul (2:ℝ)).div_const a).sub_const (1/2:ℝ)
  have e : (2:ℝ)*1/a = 2/a := by ring
  rw [e] at h
  exact h

theorem q0_hasDerivAt (a r : ℝ) : HasDerivAt (q0 a) (q0p a r) r :=
  (G_hasDerivAt _).comp r (affine_hasDerivAt a r)

theorem q0p_hasDerivAt (a r : ℝ) : HasDerivAt (q0p a) (q0pp a r) r := by
  have h := ((Gp_hasDerivAt _).comp r (affine_hasDerivAt a r)).mul_const (2/a)
  exact h

theorem deriv_q0 (a : ℝ) : deriv (q0 a) = q0p a := funext fun r => (q0_hasDerivAt a r).deriv
theorem deriv_q0p (a : ℝ) : deriv (q0p a) = q0pp a :=
  funext fun r => (q0p_hasDerivAt a r).deriv

theorem q0p_abs_le {a : ℝ} (ha : 0 < a) (r : ℝ) : |q0p a r| ≤ 15/(4*a) := by
  unfold q0p
  have hc : 0 < 2/a := by positivity
  rw [abs_mul, abs_of_pos hc]
  calc |Gp (2*r/a - 1/2)| * (2/a) ≤ 15/8 * (2/a) :=
        mul_le_mul_of_nonneg_right (Gp_abs_le _) hc.le
    _ = 15/(4*a) := by field_simp; ring

theorem q0pp_abs_le {a : ℝ} (ha : 0 < a) (r : ℝ) :
    |q0pp a r| ≤ 40/(Real.sqrt 3 * a^2) := by
  unfold q0pp
  have hc : 0 < 2/a := by positivity
  have hs := sqrt3_pos
  rw [abs_mul, abs_mul, abs_of_pos hc]
  calc |Gpp (2*r/a - 1/2)| * (2/a) * (2/a) ≤ 10/Real.sqrt 3 * (2/a) * (2/a) := by
        apply mul_le_mul_of_nonneg_right _ hc.le
        exact mul_le_mul_of_nonneg_right (Gpp_abs_le _) hc.le
    _ = 40/(Real.sqrt 3 * a^2) := by field_simp; ring

/-- M3: the source's stated sup bounds for the quintic cutoff itself. -/
theorem q0_deriv_bound {a : ℝ} (ha : 0 < a) (r : ℝ) : |deriv (q0 a) r| ≤ 15/(4*a) := by
  rw [deriv_q0]; exact q0p_abs_le ha r

theorem q0_deriv2_bound {a : ℝ} (ha : 0 < a) (r : ℝ) :
    |deriv (deriv (q0 a)) r| ≤ 40/(Real.sqrt 3 * a^2) := by
  rw [deriv_q0, deriv_q0p]; exact q0pp_abs_le ha r

theorem affine_contDiff (a : ℝ) {n : WithTop ℕ∞} : ContDiff ℝ n (fun r : ℝ => 2*r/a - 1/2) := by
  fun_prop

/-- M3: the quintic cutoff is `C^2`. -/
theorem q0_contDiff_two (a : ℝ) : ContDiff ℝ 2 (q0 a) :=
  G_contDiff_two.comp (affine_contDiff a)

/-- M3: the quintic cutoff is not `C^3`. -/
theorem q0_not_contDiff_three {a : ℝ} (ha : 0 < a) : ¬ ContDiff ℝ 3 (q0 a) := by
  intro h
  apply G_not_contDiff_three
  have hG : G = fun t => q0 a (a*(t+1/2)/2) := by
    funext t; unfold q0; congr 1; field_simp; ring
  rw [hG]
  exact h.comp (by fun_prop)

/-- M3: in particular the finite quintic cutoff is NOT `C^∞`. -/
theorem q0_not_smooth {a : ℝ} (ha : 0 < a) : ¬ ContDiff ℝ (⊤ : ℕ∞) (q0 a) := by
  intro h
  have h3 : ContDiff ℝ ((3 : ℕ) : WithTop ℕ∞) (q0 a) := contDiff_infty.mp h 3
  exact q0_not_contDiff_three ha (by exact_mod_cast h3)

/-! ## Even, compactly supported version `qe` (equal to `q0` on `[-a/4, ∞)`) -/

noncomputable def qe (a r : ℝ) : ℝ := q0 a r * q0 a (-r)
noncomputable def qep (a r : ℝ) : ℝ := q0p a r * q0 a (-r) - q0 a r * q0p a (-r)
noncomputable def qepp (a r : ℝ) : ℝ :=
  q0pp a r * q0 a (-r) - 2 * (q0p a r * q0p a (-r)) + q0 a r * q0pp a (-r)

theorem qe_eq_q0 {a r : ℝ} (ha : 0 < a) (hr : -(a/4) ≤ r) : qe a r = q0 a r := by
  unfold qe; rw [q0_eq_one ha (by linarith)]; ring

theorem qe_eq_one {a r : ℝ} (ha : 0 < a) (hr : |r| ≤ a/4) : qe a r = 1 := by
  have := abs_le.mp hr
  unfold qe; rw [q0_eq_one ha (by linarith), q0_eq_one ha (by linarith)]; ring

theorem qe_eq_zero {a r : ℝ} (ha : 0 < a) (hr : 3*a/4 ≤ |r|) : qe a r = 0 := by
  unfold qe
  rcases le_total 0 r with h | h
  · rw [abs_of_nonneg h] at hr; rw [q0_eq_zero ha hr]; ring
  · rw [abs_of_nonpos h] at hr; rw [q0_eq_zero ha hr]; ring

theorem qe_mem (a r : ℝ) : 0 ≤ qe a r ∧ qe a r ≤ 1 := by
  obtain ⟨h1, h2⟩ := q0_mem a r
  obtain ⟨h3, h4⟩ := q0_mem a (-r)
  unfold qe
  exact ⟨mul_nonneg h1 h3, by nlinarith⟩

theorem qe_contDiff_two (a : ℝ) : ContDiff ℝ 2 (qe a) :=
  (q0_contDiff_two a).mul ((q0_contDiff_two a).comp contDiff_neg)

theorem qe_continuous (a : ℝ) : Continuous (qe a) := (qe_contDiff_two a).continuous

theorem q0_continuous (a : ℝ) : Continuous (q0 a) := (q0_contDiff_two a).continuous

theorem qe_hasCompactSupport {a : ℝ} (ha : 0 < a) : HasCompactSupport (qe a) := by
  apply HasCompactSupport.intro (isCompact_closedBall (0:ℝ) (3*a/4))
  intro x hx
  rw [Metric.mem_closedBall, Real.dist_eq, sub_zero, not_le] at hx
  exact qe_eq_zero ha hx.le

theorem neg_comp_hasDerivAt {f f' : ℝ → ℝ} (hf : ∀ r, HasDerivAt f (f' r) r) (r : ℝ) :
    HasDerivAt (fun y => f (-y)) (-(f' (-r))) r := by
  have h := (hf (-r)).comp r (hasDerivAt_neg r)
  have e : f' (-r) * (-1) = -(f' (-r)) := by ring
  rw [e] at h
  exact h

theorem qe_hasDerivAt (a r : ℝ) : HasDerivAt (qe a) (qep a r) r := by
  have h := (q0_hasDerivAt a r).mul (neg_comp_hasDerivAt (q0_hasDerivAt a) r)
  have e : q0p a r * q0 a (-r) + q0 a r * -(q0p a (-r)) = qep a r := by unfold qep; ring
  rw [e] at h
  exact h

theorem qep_hasDerivAt (a r : ℝ) : HasDerivAt (qep a) (qepp a r) r := by
  have h1 := (q0p_hasDerivAt a r).mul (neg_comp_hasDerivAt (q0_hasDerivAt a) r)
  have h2 := (q0_hasDerivAt a r).mul (neg_comp_hasDerivAt (q0p_hasDerivAt a) r)
  have h := h1.sub h2
  have e : q0pp a r * q0 a (-r) + q0p a r * -(q0p a (-r)) -
      (q0p a r * q0p a (-r) + q0 a r * -(q0pp a (-r))) = qepp a r := by unfold qepp; ring
  rw [e] at h
  exact h

theorem deriv_qe (a : ℝ) : deriv (qe a) = qep a := funext fun r => (qe_hasDerivAt a r).deriv
theorem deriv_qep (a : ℝ) : deriv (qep a) = qepp a := funext fun r => (qep_hasDerivAt a r).deriv

theorem qep_contDiff_one (a : ℝ) : ContDiff ℝ 1 (qep a) := by
  have h : ContDiff ℝ (1 + 1) (qe a) := qe_contDiff_two a
  obtain ⟨-, -, h1⟩ := contDiff_succ_iff_deriv.mp h
  rwa [deriv_qe] at h1

theorem qepp_continuous (a : ℝ) : Continuous (qepp a) := by
  have h := (contDiff_one_iff_deriv.mp (qep_contDiff_one a)).2
  rwa [deriv_qep] at h

theorem qep_abs_le {a : ℝ} (ha : 0 < a) (r : ℝ) : |qep a r| ≤ 15/(4*a) := by
  unfold qep
  rcases le_total 0 r with h | h
  · rw [q0_eq_one ha (by linarith : -r ≤ a/4), q0p_eq_zero ha (by linarith : -r ≤ a/4)]
    simpa using q0p_abs_le ha r
  · rw [q0_eq_one ha (by linarith : r ≤ a/4), q0p_eq_zero ha (by linarith : r ≤ a/4)]
    simpa using q0p_abs_le ha (-r)

theorem qepp_abs_le {a : ℝ} (ha : 0 < a) (r : ℝ) : |qepp a r| ≤ 40/(Real.sqrt 3 * a^2) := by
  unfold qepp
  rcases le_total 0 r with h | h
  · rw [q0_eq_one ha (by linarith : -r ≤ a/4), q0p_eq_zero ha (by linarith : -r ≤ a/4),
      q0pp_eq_zero ha (by linarith : -r ≤ a/4)]
    simpa using q0pp_abs_le ha r
  · rw [q0_eq_one ha (by linarith : r ≤ a/4), q0p_eq_zero ha (by linarith : r ≤ a/4),
      q0pp_eq_zero ha (by linarith : r ≤ a/4)]
    simpa using q0pp_abs_le ha (-r)

/-! ## Mollifier and the smooth cutoff -/

/-- Source: "any nonnegative unit-integral `C^∞` mollifier supported in `[-a/8,a/8]`". -/
def IsMollifier (a : ℝ) (ρ : ℝ → ℝ) : Prop :=
  ContDiff ℝ (⊤ : ℕ∞) ρ ∧ (∀ t, 0 ≤ ρ t) ∧ (∫ t, ρ t = 1) ∧ (∀ t, ρ t ≠ 0 → |t| ≤ a/8)

/-- M0: such a mollifier exists (a normalized `ContDiffBump`). -/
theorem exists_mollifier {a : ℝ} (ha : 0 < a) : ∃ ρ, IsMollifier a ρ := by
  let φ : ContDiffBump (0:ℝ) := ⟨a/16, a/8, by positivity, by linarith⟩
  refine ⟨φ.normed volume, φ.contDiff_normed, fun t => φ.nonneg_normed t,
    φ.integral_normed, ?_⟩
  intro t ht
  have hs : t ∈ Function.support (φ.normed volume) := ht
  rw [φ.support_normed_eq, Metric.mem_ball, Real.dist_eq, sub_zero] at hs
  exact hs.le

/-- The smooth cutoff `q = ρ ⋆ qe`. -/
noncomputable def smoothCutoff (a : ℝ) (ρ : ℝ → ℝ) : ℝ → ℝ :=
  convolution ρ (qe a) (ContinuousLinearMap.mul ℝ ℝ) volume

theorem IsMollifier.continuous {a : ℝ} {ρ : ℝ → ℝ} (hρ : IsMollifier a ρ) : Continuous ρ :=
  hρ.1.continuous

theorem IsMollifier.hasCompactSupport {a : ℝ} {ρ : ℝ → ℝ} (hρ : IsMollifier a ρ) :
    HasCompactSupport ρ := by
  apply HasCompactSupport.intro (isCompact_closedBall (0:ℝ) (a/8))
  intro x hx
  by_contra h
  apply hx
  rw [Metric.mem_closedBall, Real.dist_eq, sub_zero]
  exact hρ.2.2.2 x h

/-- Convolution with a probability density does not increase a uniform bound. -/
theorem conv_abs_le {ρ g : ℝ → ℝ} {B : ℝ} (hρc : Continuous ρ) (hρs : HasCompactSupport ρ)
    (hρ0 : ∀ t, 0 ≤ ρ t) (hρ1 : ∫ t, ρ t = 1) (hB : ∀ t, |g t| ≤ B) (x : ℝ) :
    |convolution ρ g (ContinuousLinearMap.mul ℝ ℝ) volume x| ≤ B := by
  rw [convolution_mul]
  have hint : Integrable (fun t => ρ t * B) := (hρc.integrable_of_hasCompactSupport hρs).mul_const B
  have h := norm_integral_le_of_norm_le hint (Eventually.of_forall fun t => by
    show ‖ρ t * g (x - t)‖ ≤ ρ t * B
    rw [Real.norm_eq_abs, abs_mul, abs_of_nonneg (hρ0 t)]
    exact mul_le_mul_of_nonneg_left (hB _) (hρ0 t))
  rw [Real.norm_eq_abs, integral_mul_const, hρ1, one_mul] at h
  exact h

section Cutoff

variable {a : ℝ} {ρ : ℝ → ℝ}

/-- M1: smoothness. -/
theorem smoothCutoff_contDiff (ha : 0 < a) (hρ : IsMollifier a ρ) :
    ContDiff ℝ (⊤ : ℕ∞) (smoothCutoff a ρ) :=
  hρ.hasCompactSupport.contDiff_convolution_left (ContinuousLinearMap.mul ℝ ℝ) hρ.1
    (qe_continuous a).locallyIntegrable

/-- M1: plateau `q = 1` on `|r| ≤ a/8`. -/
theorem smoothCutoff_plateau (ha : 0 < a) (hρ : IsMollifier a ρ) {r : ℝ} (hr : |r| ≤ a/8) :
    smoothCutoff a ρ r = 1 := by
  unfold smoothCutoff
  rw [convolution_mul]
  have h : ∀ t, ρ t * qe a (r - t) = ρ t := by
    intro t
    by_cases h0 : ρ t = 0
    · rw [h0, zero_mul]
    · have ht := abs_le.mp (hρ.2.2.2 t h0)
      have hr' := abs_le.mp hr
      rw [qe_eq_one ha (abs_le.mpr ⟨by linarith, by linarith⟩), mul_one]
  simp_rw [h]
  exact hρ.2.2.1

/-- M1: support `q = 0` on `|r| ≥ 7a/8`. -/
theorem smoothCutoff_support (ha : 0 < a) (hρ : IsMollifier a ρ) {r : ℝ}
    (hr : 7*a/8 ≤ |r|) : smoothCutoff a ρ r = 0 := by
  unfold smoothCutoff
  rw [convolution_mul]
  have h : ∀ t, ρ t * qe a (r - t) = 0 := by
    intro t
    by_cases h0 : ρ t = 0
    · rw [h0, zero_mul]
    · have ht := hρ.2.2.2 t h0
      have hd := abs_sub_abs_le_abs_sub r t
      rw [qe_eq_zero ha (by linarith), mul_zero]
  simp_rw [h]
  simp

/-- M1: `0 ≤ q ≤ 1`. -/
theorem smoothCutoff_mem (ha : 0 < a) (hρ : IsMollifier a ρ) (r : ℝ) :
    0 ≤ smoothCutoff a ρ r ∧ smoothCutoff a ρ r ≤ 1 := by
  constructor
  · unfold smoothCutoff
    rw [convolution_mul]
    exact integral_nonneg fun t => mul_nonneg (hρ.2.1 t) (qe_mem a _).1
  · have h := conv_abs_le hρ.continuous hρ.hasCompactSupport hρ.2.1 hρ.2.2.1
      (g := qe a) (B := 1) (fun t => by
        rw [abs_of_nonneg (qe_mem a t).1]; exact (qe_mem a t).2) r
    exact le_trans (le_abs_self _) h

theorem deriv_smoothCutoff (ha : 0 < a) (hρ : IsMollifier a ρ) :
    deriv (smoothCutoff a ρ) = convolution ρ (qep a) (ContinuousLinearMap.mul ℝ ℝ) volume := by
  funext x
  have h := (qe_hasCompactSupport ha).hasDerivAt_convolution_right
    (ContinuousLinearMap.mul ℝ ℝ) hρ.continuous.locallyIntegrable
    ((qe_contDiff_two a).of_le (by norm_num)) x
  rw [deriv_qe] at h
  exact h.deriv

theorem deriv_conv_qep (ha : 0 < a) (hρ : IsMollifier a ρ) :
    deriv (convolution ρ (qep a) (ContinuousLinearMap.mul ℝ ℝ) volume) =
      convolution ρ (qepp a) (ContinuousLinearMap.mul ℝ ℝ) volume := by
  funext x
  have hcs : HasCompactSupport (qep a) := by
    have := (qe_hasCompactSupport ha).deriv
    rwa [deriv_qe] at this
  have h := hcs.hasDerivAt_convolution_right
    (ContinuousLinearMap.mul ℝ ℝ) hρ.continuous.locallyIntegrable (qep_contDiff_one a) x
  rw [deriv_qep] at h
  exact h.deriv

/-- M2: first-derivative bound, identical constant `15/(4a)`. -/
theorem smoothCutoff_deriv_bound (ha : 0 < a) (hρ : IsMollifier a ρ) (r : ℝ) :
    |deriv (smoothCutoff a ρ) r| ≤ 15/(4*a) := by
  rw [deriv_smoothCutoff ha hρ]
  exact conv_abs_le hρ.continuous hρ.hasCompactSupport hρ.2.1 hρ.2.2.1 (qep_abs_le ha) r

/-- M2: second-derivative bound, identical constant `40/(√3 a²)`. -/
theorem smoothCutoff_deriv2_bound (ha : 0 < a) (hρ : IsMollifier a ρ) (r : ℝ) :
    |deriv (deriv (smoothCutoff a ρ)) r| ≤ 40/(Real.sqrt 3 * a^2) := by
  rw [deriv_smoothCutoff ha hρ, deriv_conv_qep ha hρ]
  exact conv_abs_le hρ.continuous hρ.hasCompactSupport hρ.2.1 hρ.2.2.1 (qepp_abs_le ha) r

/-- M4: on `r ≥ -a/8` (in particular on the radial domain `r ≥ 0`) the smooth cutoff is the
source's literal convolution `ρ ⋆ q0`, which exists there. -/
theorem smoothCutoff_eq_source (ha : 0 < a) (hρ : IsMollifier a ρ) {r : ℝ} (hr : -(a/8) ≤ r) :
    ConvolutionExistsAt ρ (q0 a) r (ContinuousLinearMap.mul ℝ ℝ) volume ∧
    convolution ρ (q0 a) (ContinuousLinearMap.mul ℝ ℝ) volume r = smoothCutoff a ρ r := by
  refine ⟨hρ.hasCompactSupport.convolutionExists_left (ContinuousLinearMap.mul ℝ ℝ)
    hρ.continuous (q0_continuous a).locallyIntegrable r, ?_⟩
  unfold smoothCutoff
  rw [convolution_mul, convolution_mul]
  congr 1
  funext t
  by_cases h0 : ρ t = 0
  · rw [h0, zero_mul, zero_mul]
  · have ht := abs_le.mp (hρ.2.2.2 t h0)
    rw [qe_eq_q0 ha (by linarith)]

end Cutoff

/-! ## M5: smooth radial extension -/

section Radial

variable {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
variable {a : ℝ} {ρ : ℝ → ℝ}

theorem radial_contDiff (ha : 0 < a) (hρ : IsMollifier a ρ) :
    ContDiff ℝ (⊤ : ℕ∞) (fun x : E => smoothCutoff a ρ ‖x‖) := by
  rw [contDiff_iff_contDiffAt]
  intro x
  by_cases hx : x = 0
  · subst hx
    have hev : (fun y : E => smoothCutoff a ρ ‖y‖) =ᶠ[𝓝 0] fun _ => (1:ℝ) := by
      filter_upwards [Metric.ball_mem_nhds (0:E) (by positivity : (0:ℝ) < a/8)] with y hy
      rw [mem_ball_zero_iff] at hy
      apply smoothCutoff_plateau ha hρ
      rw [abs_of_nonneg (norm_nonneg y)]
      exact hy.le
    exact contDiffAt_const.congr_of_eventuallyEq hev
  · exact (smoothCutoff_contDiff ha hρ).contDiffAt.comp x (contDiffAt_norm ℝ hx)

theorem radial_plateau (ha : 0 < a) (hρ : IsMollifier a ρ) {x : E} (hx : ‖x‖ ≤ a/8) :
    smoothCutoff a ρ ‖x‖ = 1 :=
  smoothCutoff_plateau ha hρ (by rw [abs_of_nonneg (norm_nonneg x)]; exact hx)

theorem radial_support (ha : 0 < a) (hρ : IsMollifier a ρ) {x : E} (hx : 7*a/8 ≤ ‖x‖) :
    smoothCutoff a ρ ‖x‖ = 0 :=
  smoothCutoff_support ha hρ (by rw [abs_of_nonneg (norm_nonneg x)]; exact hx)

theorem radial_ray {n : E} (hn : ‖n‖ = 1) {r : ℝ} (hr : 0 ≤ r) :
    smoothCutoff a ρ ‖r • n‖ = smoothCutoff a ρ r := by
  rw [norm_smul, Real.norm_eq_abs, abs_of_nonneg hr, hn, mul_one]

end Radial

/-! ## Packaged main statement -/

theorem g10c_main {a : ℝ} (ha : 0 < a) :
    ∃ χ : ℝ → ℝ,
      (∃ ρ, IsMollifier a ρ ∧ χ = smoothCutoff a ρ ∧
        ∀ r, -(a/8) ≤ r → χ r = convolution ρ (q0 a) (ContinuousLinearMap.mul ℝ ℝ) volume r) ∧
      ContDiff ℝ (⊤ : ℕ∞) χ ∧
      (∀ r, 0 ≤ χ r ∧ χ r ≤ 1) ∧
      (∀ r, |r| ≤ a/8 → χ r = 1) ∧
      (∀ r, 7*a/8 ≤ |r| → χ r = 0) ∧
      (∀ r, |deriv χ r| ≤ 15/(4*a)) ∧
      (∀ r, |deriv (deriv χ) r| ≤ 40/(Real.sqrt 3 * a^2)) ∧
      (∀ (E : Type) [NormedAddCommGroup E] [InnerProductSpace ℝ E],
        ContDiff ℝ (⊤ : ℕ∞) (fun x : E => χ ‖x‖) ∧
        (∀ x : E, ‖x‖ ≤ a/8 → χ ‖x‖ = 1) ∧
        (∀ x : E, 7*a/8 ≤ ‖x‖ → χ ‖x‖ = 0)) ∧
      ¬ ContDiff ℝ 3 (q0 a) ∧ ContDiff ℝ 2 (q0 a) := by
  obtain ⟨ρ, hρ⟩ := exists_mollifier ha
  refine ⟨smoothCutoff a ρ, ⟨ρ, hρ, rfl, fun r hr => (smoothCutoff_eq_source ha hρ hr).2.symm⟩,
    smoothCutoff_contDiff ha hρ, smoothCutoff_mem ha hρ,
    fun r hr => smoothCutoff_plateau ha hρ hr, fun r hr => smoothCutoff_support ha hρ hr,
    smoothCutoff_deriv_bound ha hρ, smoothCutoff_deriv2_bound ha hρ, ?_,
    q0_not_contDiff_three ha, q0_contDiff_two a⟩
  intro E _ _
  exact ⟨radial_contDiff ha hρ, fun x hx => radial_plateau ha hρ hx,
    fun x hx => radial_support ha hρ hx⟩

end G10C
