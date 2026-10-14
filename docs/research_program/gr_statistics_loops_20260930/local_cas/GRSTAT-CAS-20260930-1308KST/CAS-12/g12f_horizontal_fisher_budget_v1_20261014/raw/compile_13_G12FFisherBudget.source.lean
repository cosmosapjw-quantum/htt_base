import Mathlib
import G11AIntegralBregman

/-!
# G12-F (TEFF-A4 scope line): horizontal Fisher budget ⇒ derivative observable bound

Targets frozen in `../FROZEN_TARGETS.md` (T0–T10).  Source:
`supplements/TEFF_POSITIVE_BRIDGE.md:149-158`, conditions `DECISIONS.json:603-604`.

* `fisherDens d w` is the `[0,∞]`-valued Fisher density `d²/w` with `0/0 = 0` and
  `d/0 = ∞` (`d ≠ 0`); it avoids Lean's junk value `1/0 = 0` in `G11A.hess`, which would
  silently drop zero occupation and FD saturation.
* T1: weighted Cauchy–Schwarz `|∫ K d ρ| ≤ √J √(∫ K² w ρ)` from the extended budget, with
  integrability of `K d ρ` derived, not assumed.
* T5/T6: parallel construction (fixed kernel and measure): derivative under the integral by
  domination, then T1 with `d = 𝒟_X f`.
* T7/T8: general trivialization: exact kernel- and measure-derivative terms, each bounded.
* T9: sharpness/non-vacuity witness; T10: negative controls.

`J` is always a hypothesis on the actual derivative `f' x0` of the family, never a static
functional of `f x0`.  Reviewed imports are unchanged.  Scientific admission is not claimed.
-/

open MeasureTheory Set Filter Topology
open scoped ENNReal

noncomputable section

namespace G12F

open G11A

/-! ## Definitions -/

/-- Extended Fisher density `d²/w` with `0/0 = 0` and `d/0 = ∞` for `d ≠ 0`. -/
def fisherDens (d w : ℝ) : ℝ≥0∞ :=
  if 0 < w then ENNReal.ofReal (d ^ 2 / w) else if d = 0 then 0 else ⊤

/-- Square root of `fisherDens` (auxiliary). -/
def fisherAmp (d w : ℝ) : ℝ≥0∞ :=
  if 0 < w then ENNReal.ofReal (|d| / Real.sqrt w) else if d = 0 then 0 else ⊤

/-- `f (1 + ξ f)`; for BE this is `f (1 + f)`. -/
def statWeight (s : Stat) (f : ℝ) : ℝ := f * (1 + xi s * f)

/-! ## Auxiliary lemmas -/

theorem fisherAmp_sq (d w : ℝ) : fisherAmp d w ^ 2 = fisherDens d w := by
  unfold fisherAmp fisherDens
  split_ifs with h1 h2
  · rw [← ENNReal.ofReal_pow (div_nonneg (abs_nonneg d) (Real.sqrt_nonneg w)), div_pow, sq_abs,
      Real.sq_sqrt h1.le]
  · simp
  · exact ENNReal.top_pow two_ne_zero

theorem measurable_fisherDens {X : Type*} [MeasurableSpace X] {d w : X → ℝ}
    (hd : Measurable d) (hw : Measurable w) : Measurable (fun z => fisherDens (d z) (w z)) := by
  unfold fisherDens
  refine Measurable.ite (measurableSet_lt measurable_const hw) ?_
    (Measurable.ite (measurableSet_eq_fun hd measurable_const) measurable_const measurable_const)
  exact ENNReal.measurable_ofReal.comp ((hd.pow_const 2).div hw)

theorem measurable_fisherAmp {X : Type*} [MeasurableSpace X] {d w : X → ℝ}
    (hd : Measurable d) (hw : Measurable w) : Measurable (fun z => fisherAmp (d z) (w z)) := by
  unfold fisherAmp
  refine Measurable.ite (measurableSet_lt measurable_const hw) ?_
    (Measurable.ite (measurableSet_eq_fun hd measurable_const) measurable_const measurable_const)
  exact ENNReal.measurable_ofReal.comp
    ((continuous_abs.measurable.comp hd).div (Real.continuous_sqrt.measurable.comp hw))

theorem ofReal_rpow_half (x : ℝ) :
    ENNReal.ofReal x ^ (1 / 2 : ℝ) = ENNReal.ofReal (Real.sqrt x) := by
  rcases le_or_lt x 0 with hx | hx
  · rw [ENNReal.ofReal_of_nonpos hx, Real.sqrt_eq_zero'.2 hx, ENNReal.ofReal_zero,
      ENNReal.zero_rpow_of_pos (by norm_num)]
  · rw [ENNReal.ofReal_rpow_of_nonneg hx.le (by norm_num), Real.sqrt_eq_rpow]

/-! ## T0: weights and the bridge to the reviewed G11A Fisher form -/

theorem statWeight_nonneg (s : Stat) {f : ℝ} (hf : f ∈ cdom s) : 0 ≤ statWeight s f := by
  cases s <;> simp only [statWeight, xi, cdom, mem_Ici, mem_Icc] at hf ⊢
  · nlinarith
  · nlinarith
  · nlinarith [mul_nonneg hf.1 (sub_nonneg.2 hf.2)]

theorem fisherDens_of_dom (s : Stat) {f : ℝ} (hf : f ∈ dom s) (d : ℝ) :
    fisherDens d (statWeight s f) = ENNReal.ofReal (d ^ 2 * hess s f) := by
  obtain ⟨h1, h2⟩ := dom_pos s hf
  have hw : 0 < statWeight s f := mul_pos h1 h2
  rw [fisherDens, if_pos hw, hess, statWeight, div_eq_mul_one_div]

/-! ## T1: weighted Cauchy–Schwarz -/

theorem weighted_cauchy_schwarz {X : Type*} [MeasurableSpace X] (μ : Measure X)
    (K d w ρ : X → ℝ) (J : ℝ)
    (hK : Measurable K) (hd : Measurable d) (hw : Measurable w) (hρ : Measurable ρ)
    (hw0 : ∀ᵐ z ∂μ, 0 ≤ w z) (hρ0 : ∀ᵐ z ∂μ, 0 ≤ ρ z)
    (hKw : Integrable (fun z => K z ^ 2 * w z * ρ z) μ)
    (hJ : ∫⁻ z, ENNReal.ofReal (ρ z) * fisherDens (d z) (w z) ∂μ ≤ ENNReal.ofReal J) :
    Integrable (fun z => K z * d z * ρ z) μ ∧
      |∫ z, K z * d z * ρ z ∂μ| ≤ Real.sqrt J * Real.sqrt (∫ z, K z ^ 2 * w z * ρ z ∂μ) := by
  set I := ∫ z, K z ^ 2 * w z * ρ z ∂μ with hIdef
  let a : X → ℝ≥0∞ := fun z => ENNReal.ofReal (|K z| * Real.sqrt (w z * ρ z))
  let b : X → ℝ≥0∞ := fun z => ENNReal.ofReal (Real.sqrt (ρ z)) * fisherAmp (d z) (w z)
  have ha_meas : Measurable a := ENNReal.measurable_ofReal.comp
    ((continuous_abs.measurable.comp hK).mul (Real.continuous_sqrt.measurable.comp (hw.mul hρ)))
  have hb_meas : Measurable b :=
    (ENNReal.measurable_ofReal.comp (Real.continuous_sqrt.measurable.comp hρ)).mul
      (measurable_fisherAmp hd hw)
  have ha2 : ∀ᵐ z ∂μ, a z ^ (2 : ℝ) = ENNReal.ofReal (K z ^ 2 * w z * ρ z) := by
    filter_upwards [hw0, hρ0] with z hwz hρz
    rw [ENNReal.rpow_two]
    simp only [a]
    rw [← ENNReal.ofReal_pow (mul_nonneg (abs_nonneg _) (Real.sqrt_nonneg _)), mul_pow, sq_abs,
      Real.sq_sqrt (mul_nonneg hwz hρz)]
    congr 1
    ring
  have hb2 : ∀ᵐ z ∂μ, b z ^ (2 : ℝ) = ENNReal.ofReal (ρ z) * fisherDens (d z) (w z) := by
    filter_upwards [hρ0] with z hρz
    rw [ENNReal.rpow_two]
    simp only [b]
    rw [mul_pow, fisherAmp_sq, ← ENNReal.ofReal_pow (Real.sqrt_nonneg _), Real.sq_sqrt hρz]
  have hnn : 0 ≤ᵐ[μ] (fun z => K z ^ 2 * w z * ρ z) := by
    filter_upwards [hw0, hρ0] with z hwz hρz
    exact mul_nonneg (mul_nonneg (sq_nonneg _) hwz) hρz
  have hA : ∫⁻ z, a z ^ (2 : ℝ) ∂μ = ENNReal.ofReal I := by
    rw [lintegral_congr_ae ha2, hIdef, ofReal_integral_eq_lintegral_ofReal hKw hnn]
  have hB : ∫⁻ z, b z ^ (2 : ℝ) ∂μ ≤ ENNReal.ofReal J := by
    rw [lintegral_congr_ae hb2]; exact hJ
  have hBfin : ∀ᵐ z ∂μ, b z ^ (2 : ℝ) < ⊤ :=
    ae_lt_top (hb_meas.pow_const _) (ne_top_of_le_ne_top ENNReal.ofReal_ne_top hB)
  have hpt : ∀ᵐ z ∂μ, ENNReal.ofReal ‖K z * d z * ρ z‖ ≤ a z * b z := by
    filter_upwards [hw0, hρ0, hBfin] with z hwz hρz hfin
    rw [Real.norm_eq_abs]
    rcases hwz.lt_or_eq with hwpos | hweq
    · simp only [a, b, fisherAmp, if_pos hwpos]
      rw [← ENNReal.ofReal_mul (Real.sqrt_nonneg _),
        ← ENNReal.ofReal_mul (mul_nonneg (abs_nonneg _) (Real.sqrt_nonneg _))]
      apply ENNReal.ofReal_le_ofReal
      have hs : 0 < Real.sqrt (w z) := Real.sqrt_pos.2 hwpos
      have hρs : Real.sqrt (ρ z) * Real.sqrt (ρ z) = ρ z := Real.mul_self_sqrt hρz
      rw [Real.sqrt_mul hwz, abs_mul, abs_mul, abs_of_nonneg hρz]
      have e : |K z| * (Real.sqrt (w z) * Real.sqrt (ρ z)) *
          (Real.sqrt (ρ z) * (|d z| / Real.sqrt (w z))) =
          |K z| * (|d z| / Real.sqrt (w z) * Real.sqrt (w z)) *
            (Real.sqrt (ρ z) * Real.sqrt (ρ z)) := by ring
      rw [e, div_mul_cancel₀ _ hs.ne', hρs]
    · have hw0' : w z = 0 := hweq.symm
      by_cases hdz : d z = 0
      · simp [hdz]
      · by_cases hρz0 : ρ z = 0
        · simp [hρz0]
        · exfalso
          have hρpos : 0 < ρ z := lt_of_le_of_ne hρz (Ne.symm hρz0)
          have hbt : b z = ⊤ := by
            simp only [b, fisherAmp, hw0', lt_self_iff_false, if_false, hdz]
            refine ENNReal.mul_top ?_
            rw [Ne, ENNReal.ofReal_eq_zero, not_le]
            exact Real.sqrt_pos.2 hρpos
          rw [hbt, ENNReal.top_rpow_of_pos (by norm_num)] at hfin
          exact lt_irrefl _ hfin
  have hH := ENNReal.lintegral_mul_le_Lp_mul_Lq μ Real.HolderConjugate.two_two
    ha_meas.aemeasurable hb_meas.aemeasurable
  have hle : ∫⁻ z, ENNReal.ofReal ‖K z * d z * ρ z‖ ∂μ ≤
      ENNReal.ofReal (Real.sqrt I * Real.sqrt J) := by
    calc ∫⁻ z, ENNReal.ofReal ‖K z * d z * ρ z‖ ∂μ ≤ ∫⁻ z, (a * b) z ∂μ :=
          lintegral_mono_ae (by filter_upwards [hpt] with z hz; exact hz)
      _ ≤ (∫⁻ z, a z ^ (2 : ℝ) ∂μ) ^ (1 / (2 : ℝ)) * (∫⁻ z, b z ^ (2 : ℝ) ∂μ) ^ (1 / (2 : ℝ)) :=
          hH
      _ ≤ ENNReal.ofReal I ^ (1 / 2 : ℝ) * ENNReal.ofReal J ^ (1 / 2 : ℝ) := by
          rw [hA]
          exact mul_le_mul_left' (ENNReal.rpow_le_rpow hB (by norm_num)) _
      _ = ENNReal.ofReal (Real.sqrt I * Real.sqrt J) := by
          rw [ofReal_rpow_half, ofReal_rpow_half, ← ENNReal.ofReal_mul (Real.sqrt_nonneg _)]
  have hfin : ∫⁻ z, ENNReal.ofReal ‖K z * d z * ρ z‖ ∂μ < ⊤ :=
    lt_of_le_of_lt hle ENNReal.ofReal_lt_top
  have hint : Integrable (fun z => K z * d z * ρ z) μ :=
    ⟨((hK.mul hd).mul hρ).aestronglyMeasurable, (hasFiniteIntegral_iff_norm _).2 hfin⟩
  refine ⟨hint, ?_⟩
  have h1 := norm_integral_le_lintegral_norm (μ := μ) (fun z => K z * d z * ρ z)
  rw [Real.norm_eq_abs] at h1
  calc |∫ z, K z * d z * ρ z ∂μ| ≤ (∫⁻ z, ENNReal.ofReal ‖K z * d z * ρ z‖ ∂μ).toReal := h1
    _ ≤ (ENNReal.ofReal (Real.sqrt I * Real.sqrt J)).toReal :=
        ENNReal.toReal_mono ENNReal.ofReal_ne_top hle
    _ = Real.sqrt J * Real.sqrt I := by
        rw [ENNReal.toReal_ofReal (mul_nonneg (Real.sqrt_nonneg _) (Real.sqrt_nonneg _))]
        ring

/-! ## T2: real-valued Fisher form ⇒ extended budget -/

theorem real_budget_le {X : Type*} [MeasurableSpace X] (μ : Measure X) (s : Stat)
    (d f ρ : X → ℝ) (J : ℝ)
    (hdom : ∀ᵐ z ∂μ, f z ∈ dom s) (hρ0 : ∀ᵐ z ∂μ, 0 ≤ ρ z)
    (hint : Integrable (fun z => d z ^ 2 * hess s (f z) * ρ z) μ)
    (hle : ∫ z, d z ^ 2 * hess s (f z) * ρ z ∂μ ≤ J) :
    ∫⁻ z, ENNReal.ofReal (ρ z) * fisherDens (d z) (statWeight s (f z)) ∂μ ≤
      ENNReal.ofReal J := by
  have hnn : 0 ≤ᵐ[μ] (fun z => d z ^ 2 * hess s (f z) * ρ z) := by
    filter_upwards [hdom, hρ0] with z hz hρz
    obtain ⟨h1, h2⟩ := dom_pos s hz
    have hh : 0 ≤ hess s (f z) := by
      rw [hess]; exact le_of_lt (one_div_pos.2 (mul_pos h1 h2))
    exact mul_nonneg (mul_nonneg (sq_nonneg _) hh) hρz
  calc ∫⁻ z, ENNReal.ofReal (ρ z) * fisherDens (d z) (statWeight s (f z)) ∂μ
      = ∫⁻ z, ENNReal.ofReal (d z ^ 2 * hess s (f z) * ρ z) ∂μ := by
        apply lintegral_congr_ae
        filter_upwards [hdom, hρ0] with z hz hρz
        rw [fisherDens_of_dom s hz, ← ENNReal.ofReal_mul hρz]
        congr 1
        ring
    _ = ENNReal.ofReal (∫ z, d z ^ 2 * hess s (f z) * ρ z ∂μ) :=
        (ofReal_integral_eq_lintegral_ofReal hint hnn).symm
    _ ≤ ENNReal.ofReal J := ENNReal.ofReal_le_ofReal hle

/-! ## T3: zero weight forces zero derivative a.e. -/

theorem zero_weight_null {X : Type*} [MeasurableSpace X] (μ : Measure X)
    (d w ρ : X → ℝ) (J : ℝ) (hd : Measurable d) (hw : Measurable w) (hρ : Measurable ρ)
    (hJ : ∫⁻ z, ENNReal.ofReal (ρ z) * fisherDens (d z) (w z) ∂μ ≤ ENNReal.ofReal J) :
    ∀ᵐ z ∂μ, w z ≤ 0 → 0 < ρ z → d z = 0 := by
  have hm : Measurable (fun z => ENNReal.ofReal (ρ z) * fisherDens (d z) (w z)) :=
    (ENNReal.measurable_ofReal.comp hρ).mul (measurable_fisherDens hd hw)
  have hfin := ae_lt_top hm (ne_top_of_le_ne_top ENNReal.ofReal_ne_top hJ)
  filter_upwards [hfin] with z hz hwz hρz
  by_contra hdz
  have htop : fisherDens (d z) (w z) = ⊤ := by
    unfold fisherDens
    rw [if_neg (not_lt.2 hwz), if_neg hdz]
  have hne : ENNReal.ofReal (ρ z) ≠ 0 := by
    rw [Ne, ENNReal.ofReal_eq_zero, not_le]; exact hρz
  rw [htop, ENNReal.mul_top hne] at hz
  exact lt_irrefl _ hz

/-! ## T4: zero occupation for admissible differentiable families -/

theorem zero_occupation_derivative (s : Stat) (φ : ℝ → ℝ) (x0 d : ℝ)
    (hφ : ∀ᶠ t in 𝓝 x0, φ t ∈ cdom s) (hd : HasDerivAt φ d x0)
    (h0 : statWeight s (φ x0) = 0) :
    d = 0 ∧ fisherDens d (statWeight s (φ x0)) = 0 := by
  have hx0 : φ x0 ∈ cdom s := hφ.self_of_nhds
  have hd0 : d = 0 := by
    rcases mul_eq_zero.1 h0 with h | h
    · have hmin : IsLocalMin φ x0 := by
        refine hφ.mono fun t ht => ?_
        rw [h]
        cases s <;> simp only [cdom, mem_Ici, mem_Icc] at ht
        · exact ht
        · exact ht
        · exact ht.1
      exact hmin.hasDerivAt_eq_zero hd
    · cases s
      · simp [xi] at h
      · simp only [xi, cdom, mem_Ici] at h hx0
        linarith
      · simp only [xi] at h
        have h1 : φ x0 = 1 := by linarith
        have hmax : IsLocalMax φ x0 := by
          refine hφ.mono fun t ht => ?_
          simp only [cdom, mem_Icc] at ht
          rw [h1]; exact ht.2
        exact hmax.hasDerivAt_eq_zero hd
  refine ⟨hd0, ?_⟩
  rw [h0, hd0]
  simp [fisherDens]

/-! ## T5: parallel construction (fixed kernel, fixed measure density) -/

theorem parallel_derivative_bound {X : Type*} [MeasurableSpace X] (μ : Measure X) (s : Stat)
    (K ρ : X → ℝ) (f f' : ℝ → X → ℝ) (x0 J : ℝ) (bound : X → ℝ) (U : Set ℝ) (hU : U ∈ 𝓝 x0)
    (hF_meas : ∀ᶠ t in 𝓝 x0, AEStronglyMeasurable (fun z => K z * f t z * ρ z) μ)
    (hF_int : Integrable (fun z => K z * f x0 z * ρ z) μ)
    (h_bound : ∀ᵐ z ∂μ, ∀ t ∈ U, |K z * f' t z * ρ z| ≤ bound z)
    (hbound : Integrable bound μ)
    (h_diff : ∀ᵐ z ∂μ, ∀ t ∈ U, HasDerivAt (fun t => f t z) (f' t z) t)
    (hK : Measurable K) (hρ : Measurable ρ) (hf0 : Measurable (f x0)) (hd : Measurable (f' x0))
    (hρ0 : ∀ᵐ z ∂μ, 0 ≤ ρ z) (hcdom : ∀ᵐ z ∂μ, f x0 z ∈ cdom s)
    (hKw : Integrable (fun z => K z ^ 2 * statWeight s (f x0 z) * ρ z) μ)
    (hJ : ∫⁻ z, ENNReal.ofReal (ρ z) * fisherDens (f' x0 z) (statWeight s (f x0 z)) ∂μ ≤
      ENNReal.ofReal J) :
    HasDerivAt (fun t => ∫ z, K z * f t z * ρ z ∂μ) (∫ z, K z * f' x0 z * ρ z ∂μ) x0 ∧
      |∫ z, K z * f' x0 z * ρ z ∂μ| ≤
        Real.sqrt J * Real.sqrt (∫ z, K z ^ 2 * statWeight s (f x0 z) * ρ z ∂μ) := by
  have hderiv := hasDerivAt_integral_of_dominated_loc_of_deriv_le (μ := μ)
    (F := fun t z => K z * f t z * ρ z) (F' := fun t z => K z * f' t z * ρ z) (bound := bound)
    hU hF_meas hF_int ((hK.mul hd).mul hρ).aestronglyMeasurable
    (by filter_upwards [h_bound] with z hz t ht; rw [Real.norm_eq_abs]; exact hz t ht)
    hbound
    (by filter_upwards [h_diff] with z hz t ht; exact ((hz t ht).const_mul (K z)).mul_const (ρ z))
  have hw : Measurable (fun z => statWeight s (f x0 z)) := by
    show Measurable (fun z => f x0 z * (1 + xi s * f x0 z))
    exact hf0.mul (measurable_const.add (measurable_const.mul hf0))
  have hw0 : ∀ᵐ z ∂μ, 0 ≤ statWeight s (f x0 z) := by
    filter_upwards [hcdom] with z hz
    exact statWeight_nonneg s hz
  have hcs := weighted_cauchy_schwarz μ K (f' x0) (fun z => statWeight s (f x0 z)) ρ J
    hK hd hw hρ hw0 hρ0 hKw hJ
  exact ⟨hderiv.2, hcs.2⟩

/-! ## T6: the source statement verbatim (measure `dν`, BE weight `f(1+f)`) -/

theorem teff_a4_derivative_bound_BE {X : Type*} [MeasurableSpace X] (μ : Measure X)
    (K : X → ℝ) (f f' : ℝ → X → ℝ) (x0 J : ℝ) (bound : X → ℝ) (U : Set ℝ) (hU : U ∈ 𝓝 x0)
    (hF_meas : ∀ᶠ t in 𝓝 x0, AEStronglyMeasurable (fun z => K z * f t z) μ)
    (hF_int : Integrable (fun z => K z * f x0 z) μ)
    (h_bound : ∀ᵐ z ∂μ, ∀ t ∈ U, |K z * f' t z| ≤ bound z)
    (hbound : Integrable bound μ)
    (h_diff : ∀ᵐ z ∂μ, ∀ t ∈ U, HasDerivAt (fun t => f t z) (f' t z) t)
    (hK : Measurable K) (hf0 : Measurable (f x0)) (hd : Measurable (f' x0))
    (hnn : ∀ᵐ z ∂μ, 0 ≤ f x0 z)
    (hKw : Integrable (fun z => K z ^ 2 * (f x0 z * (1 + f x0 z))) μ)
    (hJ : ∫⁻ z, fisherDens (f' x0 z) (f x0 z * (1 + f x0 z)) ∂μ ≤ ENNReal.ofReal J) :
    HasDerivAt (fun t => ∫ z, K z * f t z ∂μ) (∫ z, K z * f' x0 z ∂μ) x0 ∧
      |∫ z, K z * f' x0 z ∂μ| ≤
        Real.sqrt J * Real.sqrt (∫ z, K z ^ 2 * (f x0 z * (1 + f x0 z)) ∂μ) := by
  have hderiv := hasDerivAt_integral_of_dominated_loc_of_deriv_le (μ := μ)
    (F := fun t z => K z * f t z) (F' := fun t z => K z * f' t z) (bound := bound)
    hU hF_meas hF_int (hK.mul hd).aestronglyMeasurable
    (by filter_upwards [h_bound] with z hz t ht; rw [Real.norm_eq_abs]; exact hz t ht)
    hbound
    (by filter_upwards [h_diff] with z hz t ht; exact (hz t ht).const_mul (K z))
  have hw : Measurable (fun z => f x0 z * (1 + f x0 z)) := hf0.mul (measurable_const.add hf0)
  have hw0 : ∀ᵐ z ∂μ, 0 ≤ f x0 z * (1 + f x0 z) := by
    filter_upwards [hnn] with z hz
    exact mul_nonneg hz (by linarith)
  have hcs := weighted_cauchy_schwarz μ K (f' x0) (fun z => f x0 z * (1 + f x0 z))
    (fun _ => 1) J hK hd hw measurable_const hw0 (ae_of_all _ (fun _ => zero_le_one))
    (by simpa using hKw) (by simpa using hJ)
  refine ⟨hderiv.2, ?_⟩
  simpa using hcs.2

/-! ## T7: general trivialization — exact kernel and measure derivative terms -/

theorem general_derivative_bound {X : Type*} [MeasurableSpace X] (μ : Measure X) (s : Stat)
    (K K' f f' ρ ρ' : ℝ → X → ℝ) (x0 J : ℝ) (bound : X → ℝ) (U : Set ℝ) (hU : U ∈ 𝓝 x0)
    (hF_meas : ∀ᶠ t in 𝓝 x0, AEStronglyMeasurable (fun z => K t z * f t z * ρ t z) μ)
    (hF_int : Integrable (fun z => K x0 z * f x0 z * ρ x0 z) μ)
    (h_bound : ∀ᵐ z ∂μ, ∀ t ∈ U, |K t z * f' t z * ρ t z + K' t z * f t z * ρ t z +
      K t z * f t z * ρ' t z| ≤ bound z)
    (hbound : Integrable bound μ)
    (hK_diff : ∀ᵐ z ∂μ, ∀ t ∈ U, HasDerivAt (fun t => K t z) (K' t z) t)
    (hf_diff : ∀ᵐ z ∂μ, ∀ t ∈ U, HasDerivAt (fun t => f t z) (f' t z) t)
    (hρ_diff : ∀ᵐ z ∂μ, ∀ t ∈ U, HasDerivAt (fun t => ρ t z) (ρ' t z) t)
    (hKm : Measurable (K x0)) (hK'm : Measurable (K' x0)) (hfm : Measurable (f x0))
    (hdm : Measurable (f' x0)) (hρm : Measurable (ρ x0)) (hρ'm : Measurable (ρ' x0))
    (hρ0 : ∀ᵐ z ∂μ, 0 ≤ ρ x0 z) (hcdom : ∀ᵐ z ∂μ, f x0 z ∈ cdom s)
    (hKw : Integrable (fun z => K x0 z ^ 2 * statWeight s (f x0 z) * ρ x0 z) μ)
    (hJ : ∫⁻ z, ENNReal.ofReal (ρ x0 z) * fisherDens (f' x0 z) (statWeight s (f x0 z)) ∂μ ≤
      ENNReal.ofReal J)
    (hkern : Integrable (fun z => K' x0 z * f x0 z * ρ x0 z) μ) :
    Integrable (fun z => K x0 z * f x0 z * ρ' x0 z) μ ∧
    HasDerivAt (fun t => ∫ z, K t z * f t z * ρ t z ∂μ)
      ((∫ z, K x0 z * f' x0 z * ρ x0 z ∂μ) + (∫ z, K' x0 z * f x0 z * ρ x0 z ∂μ) +
        (∫ z, K x0 z * f x0 z * ρ' x0 z ∂μ)) x0 ∧
    |(∫ z, K x0 z * f' x0 z * ρ x0 z ∂μ) + (∫ z, K' x0 z * f x0 z * ρ x0 z ∂μ) +
        (∫ z, K x0 z * f x0 z * ρ' x0 z ∂μ)| ≤
      Real.sqrt J * Real.sqrt (∫ z, K x0 z ^ 2 * statWeight s (f x0 z) * ρ x0 z ∂μ) +
        |∫ z, K' x0 z * f x0 z * ρ x0 z ∂μ| + |∫ z, K x0 z * f x0 z * ρ' x0 z ∂μ| := by
  have hderiv := hasDerivAt_integral_of_dominated_loc_of_deriv_le (μ := μ)
    (F := fun t z => K t z * f t z * ρ t z)
    (F' := fun t z => K t z * f' t z * ρ t z + K' t z * f t z * ρ t z + K t z * f t z * ρ' t z)
    (bound := bound) hU hF_meas hF_int
    ((((hKm.mul hdm).mul hρm).add ((hK'm.mul hfm).mul hρm)).add
      ((hKm.mul hfm).mul hρ'm)).aestronglyMeasurable
    (by filter_upwards [h_bound] with z hz t ht; rw [Real.norm_eq_abs]; exact hz t ht)
    hbound
    (by
      filter_upwards [hK_diff, hf_diff, hρ_diff] with z hKz hfz hρz t ht
      have h3 := ((hKz t ht).mul (hfz t ht)).mul (hρz t ht)
      convert h3 using 1
      ring)
  obtain ⟨hF'int, hD⟩ := hderiv
  have hw : Measurable (fun z => statWeight s (f x0 z)) := by
    show Measurable (fun z => f x0 z * (1 + xi s * f x0 z))
    exact hfm.mul (measurable_const.add (measurable_const.mul hfm))
  have hw0 : ∀ᵐ z ∂μ, 0 ≤ statWeight s (f x0 z) := by
    filter_upwards [hcdom] with z hz
    exact statWeight_nonneg s hz
  have hcs := weighted_cauchy_schwarz μ (K x0) (f' x0) (fun z => statWeight s (f x0 z)) (ρ x0) J
    hKm hdm hw hρm hw0 hρ0 hKw hJ
  have hBint : Integrable (fun z => K x0 z * f' x0 z * ρ x0 z) μ := hcs.1
  have hCint : Integrable (fun z => K x0 z * f x0 z * ρ' x0 z) μ := by
    have h := (hF'int.sub hBint).sub hkern
    refine h.congr (ae_of_all _ (fun z => ?_))
    simp only [Pi.sub_apply]
    ring
  have e1 : ∫ z, (K x0 z * f' x0 z * ρ x0 z + K' x0 z * f x0 z * ρ x0 z +
      K x0 z * f x0 z * ρ' x0 z) ∂μ =
      ∫ z, (K x0 z * f' x0 z * ρ x0 z + K' x0 z * f x0 z * ρ x0 z) ∂μ +
        ∫ z, K x0 z * f x0 z * ρ' x0 z ∂μ := integral_add (hBint.add hkern) hCint
  have e2 : ∫ z, (K x0 z * f' x0 z * ρ x0 z + K' x0 z * f x0 z * ρ x0 z) ∂μ =
      ∫ z, K x0 z * f' x0 z * ρ x0 z ∂μ + ∫ z, K' x0 z * f x0 z * ρ x0 z ∂μ :=
    integral_add hBint hkern
  refine ⟨hCint, hD.congr_deriv (by rw [← e2]; exact e1), ?_⟩
  have h3 := abs_add_three (∫ z, K x0 z * f' x0 z * ρ x0 z ∂μ)
    (∫ z, K' x0 z * f x0 z * ρ x0 z ∂μ) (∫ z, K x0 z * f x0 z * ρ' x0 z ∂μ)
  linarith [hcs.2]

/-! ## T8: each correction bounded by an occupation envelope -/

theorem general_derivative_bound_envelope {X : Type*} [MeasurableSpace X] (μ : Measure X)
    (s : Stat) (K K' f f' ρ ρ' : ℝ → X → ℝ) (x0 J : ℝ) (bound F : X → ℝ) (U : Set ℝ)
    (hU : U ∈ 𝓝 x0)
    (hF_meas : ∀ᶠ t in 𝓝 x0, AEStronglyMeasurable (fun z => K t z * f t z * ρ t z) μ)
    (hF_int : Integrable (fun z => K x0 z * f x0 z * ρ x0 z) μ)
    (h_bound : ∀ᵐ z ∂μ, ∀ t ∈ U, |K t z * f' t z * ρ t z + K' t z * f t z * ρ t z +
      K t z * f t z * ρ' t z| ≤ bound z)
    (hbound : Integrable bound μ)
    (hK_diff : ∀ᵐ z ∂μ, ∀ t ∈ U, HasDerivAt (fun t => K t z) (K' t z) t)
    (hf_diff : ∀ᵐ z ∂μ, ∀ t ∈ U, HasDerivAt (fun t => f t z) (f' t z) t)
    (hρ_diff : ∀ᵐ z ∂μ, ∀ t ∈ U, HasDerivAt (fun t => ρ t z) (ρ' t z) t)
    (hKm : Measurable (K x0)) (hK'm : Measurable (K' x0)) (hfm : Measurable (f x0))
    (hdm : Measurable (f' x0)) (hρm : Measurable (ρ x0)) (hρ'm : Measurable (ρ' x0))
    (hρ0 : ∀ᵐ z ∂μ, 0 ≤ ρ x0 z) (hcdom : ∀ᵐ z ∂μ, f x0 z ∈ cdom s)
    (hKw : Integrable (fun z => K x0 z ^ 2 * statWeight s (f x0 z) * ρ x0 z) μ)
    (hJ : ∫⁻ z, ENNReal.ofReal (ρ x0 z) * fisherDens (f' x0 z) (statWeight s (f x0 z)) ∂μ ≤
      ENNReal.ofReal J)
    (hkern : Integrable (fun z => K' x0 z * f x0 z * ρ x0 z) μ)
    (henv : ∀ᵐ z ∂μ, |f x0 z| ≤ F z)
    (hI1 : Integrable (fun z => |K' x0 z| * F z * ρ x0 z) μ)
    (hI2 : Integrable (fun z => |K x0 z| * F z * |ρ' x0 z|) μ) :
    |(∫ z, K x0 z * f' x0 z * ρ x0 z ∂μ) + (∫ z, K' x0 z * f x0 z * ρ x0 z ∂μ) +
        (∫ z, K x0 z * f x0 z * ρ' x0 z ∂μ)| ≤
      Real.sqrt J * Real.sqrt (∫ z, K x0 z ^ 2 * statWeight s (f x0 z) * ρ x0 z ∂μ) +
        (∫ z, |K' x0 z| * F z * ρ x0 z ∂μ) + (∫ z, |K x0 z| * F z * |ρ' x0 z| ∂μ) := by
  obtain ⟨-, -, hmain⟩ := general_derivative_bound μ s K K' f f' ρ ρ' x0 J bound U hU hF_meas
    hF_int h_bound hbound hK_diff hf_diff hρ_diff hKm hK'm hfm hdm hρm hρ'm hρ0 hcdom hKw hJ hkern
  have hA : |∫ z, K' x0 z * f x0 z * ρ x0 z ∂μ| ≤ ∫ z, |K' x0 z| * F z * ρ x0 z ∂μ := by
    rw [← Real.norm_eq_abs]
    refine norm_integral_le_of_norm_le hI1 ?_
    filter_upwards [henv, hρ0] with z hz hρz
    rw [Real.norm_eq_abs, abs_mul, abs_mul, abs_of_nonneg hρz]
    exact mul_le_mul_of_nonneg_right (mul_le_mul_of_nonneg_left hz (abs_nonneg _)) hρz
  have hC : |∫ z, K x0 z * f x0 z * ρ' x0 z ∂μ| ≤ ∫ z, |K x0 z| * F z * |ρ' x0 z| ∂μ := by
    rw [← Real.norm_eq_abs]
    refine norm_integral_le_of_norm_le hI2 ?_
    filter_upwards [henv] with z hz
    rw [Real.norm_eq_abs, abs_mul, abs_mul]
    exact mul_le_mul_of_nonneg_right (mul_le_mul_of_nonneg_left hz (abs_nonneg _)) (abs_nonneg _)
  linarith

/-! ## T9: sharpness / non-vacuity witness -/

theorem sharp_witness :
    (∫⁻ z : Unit, ENNReal.ofReal 1 * fisherDens 1 (statWeight .BE 1) ∂(Measure.dirac ()) =
      ENNReal.ofReal (1 / 2)) ∧
    (∫ z : Unit, (1 : ℝ) ^ 2 * statWeight .BE 1 * 1 ∂(Measure.dirac ()) = 2) ∧
    HasDerivAt (fun t : ℝ => ∫ z : Unit, (1 : ℝ) * (1 + t) * 1 ∂(Measure.dirac ())) 1 0 ∧
    |(1 : ℝ)| = Real.sqrt (1 / 2) * Real.sqrt 2 := by
  refine ⟨?_, ?_, ?_, ?_⟩
  · rw [lintegral_dirac]
    norm_num [fisherDens, statWeight, xi]
  · rw [integral_dirac]
    norm_num [statWeight, xi]
  · simp only [integral_dirac, one_mul, mul_one]
    simpa using (hasDerivAt_id (0 : ℝ)).const_add (1 : ℝ)
  · rw [abs_one, ← Real.sqrt_mul (by norm_num)]
    norm_num

/-! ## T10: negative controls -/

theorem junk_hess_control :
    (∫ z : Unit, (1 : ℝ) ^ 2 * hess .BE 0 ∂(Measure.dirac ())) = 0 ∧
    ¬ (|∫ z : Unit, (1 : ℝ) * 1 * 1 ∂(Measure.dirac ())| ≤
        Real.sqrt 0 * Real.sqrt (∫ z : Unit, (1 : ℝ) ^ 2 * statWeight .BE 0 * 1
          ∂(Measure.dirac ()))) ∧
    fisherDens 1 (statWeight .BE 0) = ⊤ := by
  refine ⟨?_, ?_, ?_⟩
  · rw [integral_dirac]
    simp [hess]
  · rw [integral_dirac, integral_dirac]
    norm_num
  · simp [fisherDens, statWeight]

theorem measure_term_necessary :
    HasDerivAt (fun t : ℝ => ∫ z : Unit, (1 : ℝ) * 1 * (1 + t) ∂(Measure.dirac ())) 1 0 ∧
    (∫⁻ z : Unit, ENNReal.ofReal 1 * fisherDens 0 (statWeight .BE 1) ∂(Measure.dirac ()) = 0) ∧
    ¬ (|(1 : ℝ)| ≤ Real.sqrt 0 *
        Real.sqrt (∫ z : Unit, (1 : ℝ) ^ 2 * statWeight .BE 1 * 1 ∂(Measure.dirac ()))) := by
  refine ⟨?_, ?_, ?_⟩
  · simp only [integral_dirac, one_mul]
    simpa using (hasDerivAt_id (0 : ℝ)).const_add (1 : ℝ)
  · rw [lintegral_dirac]
    norm_num [fisherDens, statWeight, xi]
  · norm_num

theorem kernel_term_necessary :
    HasDerivAt (fun t : ℝ => ∫ z : Unit, (1 + t) * 1 * 1 ∂(Measure.dirac ())) 1 0 ∧
    (∫⁻ z : Unit, ENNReal.ofReal 1 * fisherDens 0 (statWeight .BE 1) ∂(Measure.dirac ()) = 0) ∧
    ¬ (|(1 : ℝ)| ≤ Real.sqrt 0 *
        Real.sqrt (∫ z : Unit, (1 : ℝ) ^ 2 * statWeight .BE 1 * 1 ∂(Measure.dirac ()))) := by
  refine ⟨?_, ?_, ?_⟩
  · simp only [integral_dirac, mul_one]
    simpa using (hasDerivAt_id (0 : ℝ)).const_add (1 : ℝ)
  · rw [lintegral_dirac]
    norm_num [fisherDens, statWeight, xi]
  · norm_num

end G12F
