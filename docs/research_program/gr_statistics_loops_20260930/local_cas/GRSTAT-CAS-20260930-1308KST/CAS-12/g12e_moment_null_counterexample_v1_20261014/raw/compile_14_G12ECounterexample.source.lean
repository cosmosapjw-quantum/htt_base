import G12EMomentNull

/-!
# G12-E (TEFF-H1): the card measure dν = C E² dE dΩ, growth, final statement

Targets frozen in `../FROZEN_TARGETS.md` (T5–T11).  Uses the reviewed, unchanged
`G11A.nu`, `G11A.dOmega`, `G11A.hess`, `G12D.occupation` and its envelope lemmas.

The final statement `teff_h1_entropy_ball_derivative_unbounded` says: for every finite retained
family integrable on a positive compact patch and every base state strictly inside a common
envelope on the patch, there is one static divergence level `B` such that the spacetime
families that are admissible at every `x`, keep every retained moment, and stay within
divergence `B` at every `x` have unbounded `x`-derivative at `x = 0`, in both the L²(ν) norm
and the horizontal Fisher norm `∫ |∂_x f|² / (f (1 + ξ f)) dν`.
Scientific admission is not claimed.
-/

open MeasureTheory Set Filter Topology
open scoped ENNReal

noncomputable section

namespace G12E

open G11A

/-- Number and energy scores `φ = 1`, `φ = E`. -/
def numberEnergyScores : Fin 2 → ℝ × Sphere2 → ℝ := ![fun _ => 1, fun z => z.1]

instance dOmega_isFiniteMeasure : IsFiniteMeasure dOmega := by
  unfold dOmega; infer_instance

theorem dOmega_univ_ne_zero : dOmega univ ≠ 0 := by
  unfold dOmega
  rw [Measure.toSphere_apply_univ, finrank_euclideanSpace_fin]
  exact mul_ne_zero (by norm_num) (Metric.measure_ball_pos _ _ one_pos).ne'

/-- The radial factor `C E² dE` on `(0, ∞)`. -/
def rad (C : ℝ) : Measure ℝ :=
  (volume.restrict (Ioi (0 : ℝ))).withDensity (fun E => ENNReal.ofReal (C * E ^ 2))

theorem nu_eq (C : ℝ) : nu C = (rad C).prod dOmega := rfl

theorem patchE_eq {E1 E2 : ℝ} : patchE (Ω := Sphere2) E1 E2 = Icc E1 E2 ×ˢ univ := by
  rw [Set.prod_univ]; rfl

/-- **T5.** No mass at `E ≤ 0`; the compact positive patch has finite measure. -/
theorem nu_facts (C : ℝ) :
    nu C {z | z.1 ≤ 0} = 0 ∧ ∀ E1 E2 : ℝ, 0 < E1 → nu C (patchE E1 E2) ≠ ⊤ := by
  constructor
  · have hset : {z : ℝ × Sphere2 | z.1 ≤ 0} = Iic 0 ×ˢ univ := by
      ext z; simp
    rw [hset, nu_eq, Measure.prod_prod]
    have h0 : rad C (Iic 0) = 0 := by
      apply withDensity_absolutelyContinuous
      rw [Measure.restrict_apply measurableSet_Iic]
      simp
    rw [h0, zero_mul]
  · intro E1 E2 hE1
    rw [patchE_eq, nu_eq, Measure.prod_prod]
    refine ENNReal.mul_ne_top ?_ (measure_ne_top _ _)
    rw [rad, withDensity_apply _ measurableSet_Icc]
    refine ne_top_of_le_ne_top (b := ENNReal.ofReal (|C| * E2 ^ 2) * volume (Icc E1 E2)) ?_ ?_
    · exact ENNReal.mul_ne_top ENNReal.ofReal_ne_top
        (by rw [Real.volume_Icc]; exact ENNReal.ofReal_ne_top)
    · calc ∫⁻ E in Icc E1 E2, ENNReal.ofReal (C * E ^ 2) ∂(volume.restrict (Ioi 0))
          ≤ ∫⁻ E in Icc E1 E2, ENNReal.ofReal (|C| * E2 ^ 2) ∂(volume.restrict (Ioi 0)) := by
            refine setLIntegral_mono measurable_const fun E hE => ENNReal.ofReal_le_ofReal ?_
            have hE0 : 0 ≤ E := le_trans hE1.le hE.1
            have hsq : E ^ 2 ≤ E2 ^ 2 := pow_le_pow_left₀ hE0 hE.2 2
            have h1 := mul_nonneg (sub_nonneg.2 (le_abs_self C)) (sq_nonneg E)
            have h2 := mul_nonneg (abs_nonneg C) (sub_nonneg.2 hsq)
            nlinarith
        _ = ENNReal.ofReal (|C| * E2 ^ 2) * (volume.restrict (Ioi 0)) (Icc E1 E2) :=
            setLIntegral_const _ _
        _ ≤ ENNReal.ofReal (|C| * E2 ^ 2) * volume (Icc E1 E2) := by
            gcongr
            exact Measure.restrict_apply_le _ _

theorem rad_ball_pos (C : ℝ) (hC : 0 < C) {E0 r : ℝ} (hr : 0 < r)
    (hball : Metric.ball E0 r ⊆ Ioi 0) : 0 < rad C (Metric.ball E0 r) := by
  have hE0 : 0 < E0 := hball (Metric.mem_ball_self hr)
  have hEr : r ≤ E0 := by
    by_contra hlt
    push_neg at hlt
    have hy : (E0 - r) / 2 ∈ Metric.ball E0 r := by
      rw [Metric.mem_ball, Real.dist_eq, abs_lt]; constructor <;> linarith
    have := hball hy
    simp only [mem_Ioi] at this
    linarith
  have hsub : Metric.ball E0 (r / 2) ⊆ Metric.ball E0 r := Metric.ball_subset_ball (by linarith)
  have hsubpos : Metric.ball E0 (r / 2) ⊆ Ioi 0 := hsub.trans hball
  refine lt_of_lt_of_le ?_ (measure_mono hsub)
  rw [rad, withDensity_apply _ measurableSet_ball, Measure.restrict_restrict measurableSet_ball,
    inter_eq_left.2 hsubpos]
  have hκ : 0 < C * (r / 2) ^ 2 := by positivity
  calc (0 : ℝ≥0∞) < ENNReal.ofReal (C * (r / 2) ^ 2) * volume (Metric.ball E0 (r / 2)) := by
        rw [Real.volume_ball]
        exact ENNReal.mul_pos (ENNReal.ofReal_pos.2 hκ).ne'
          (ENNReal.ofReal_pos.2 (by linarith)).ne'
    _ = ∫⁻ E in Metric.ball E0 (r / 2), ENNReal.ofReal (C * (r / 2) ^ 2) :=
        (setLIntegral_const _ _).symm
    _ ≤ ∫⁻ E in Metric.ball E0 (r / 2), ENNReal.ofReal (C * E ^ 2) := by
        refine setLIntegral_mono (by fun_prop) fun E hE => ENNReal.ofReal_le_ofReal ?_
        rw [Metric.mem_ball, Real.dist_eq, abs_lt] at hE
        have h1 : r / 2 ≤ E := by linarith
        have h2 : (r / 2) ^ 2 ≤ E ^ 2 := pow_le_pow_left₀ (by linarith) h1 2
        exact mul_le_mul_of_nonneg_left h2 hC.le

/-- **T6.** Positivity of radial integrals under `ν`. -/
theorem radial_integral_pos (C : ℝ) (hC : 0 < C) (w : ℝ → ℝ) {E1 E2 Mw : ℝ}
    (hE1 : 0 < E1) (hwm : Measurable w) (hwb : ∀ E, |w E| ≤ Mw)
    (hw0 : ∀ E ∉ Icc E1 E2, w E = 0) (hwnn : ∀ E, 0 ≤ w E)
    {E0 r : ℝ} (hr : 0 < r) (hball : Metric.ball E0 r ⊆ Ioi 0)
    (hpos : ∀ E ∈ Metric.ball E0 r, 0 < w E) :
    Integrable (fun z : ℝ × Sphere2 => w z.1) (nu C) ∧ 0 < ∫ z, w z.1 ∂nu C := by
  have hint : Integrable (fun z : ℝ × Sphere2 => w z.1) (nu C) :=
    integrable_of_bdd_patch (nu C) (E1 := E1) (E2 := E2) (M := Mw) _
      ((nu_facts C).2 E1 E2 hE1) (hwm.comp measurable_fst).aestronglyMeasurable
      (fun z => hwb z.1) (fun z hz => hw0 z.1 hz)
  refine ⟨hint, (integral_pos_iff_support_of_nonneg (fun z => hwnn z.1) hint).2 ?_⟩
  have hsub : Metric.ball E0 r ×ˢ (univ : Set Sphere2) ⊆
      Function.support (fun z : ℝ × Sphere2 => w z.1) := fun z hz => (hpos z.1 hz.1).ne'
  refine lt_of_lt_of_le ?_ (measure_mono hsub)
  rw [nu_eq, Measure.prod_prod]
  exact ENNReal.mul_pos (rad_ball_pos C hC hr hball).ne' dOmega_univ_ne_zero

theorem exists_ball_ne_zero (q : ℝ → ℝ) (hq : Continuous q) {E0 : ℝ} (hE0pos : 0 < E0)
    (hE0 : q E0 ≠ 0) :
    ∃ r, 0 < r ∧ Metric.ball E0 r ⊆ Ioi 0 ∧ ∀ E ∈ Metric.ball E0 r, q E ≠ 0 := by
  have ho : IsOpen {E : ℝ | q E ≠ 0} := isOpen_ne_fun hq continuous_const
  obtain ⟨ε, hε, hball⟩ := Metric.isOpen_iff.1 ho E0 hE0
  refine ⟨min ε E0, lt_min hε hE0pos, fun E hE => ?_,
    fun E hE => hball (Metric.ball_subset_ball (min_le_left _ _) hE)⟩
  rw [Metric.mem_ball, Real.dist_eq, abs_lt] at hE
  have := min_le_right ε E0
  show 0 < E
  linarith [hE.1]

theorem bound_of_patch (q : ℝ → ℝ) {E1 E2 : ℝ} (hq : Continuous q)
    (hz : ∀ E ∉ Icc E1 E2, q E = 0) : ∃ Q, 0 ≤ Q ∧ ∀ E, |q E| ≤ Q := by
  obtain ⟨Q, hQ⟩ := hq.bounded_above_of_compact_support (HasCompactSupport.intro isCompact_Icc hz)
  exact ⟨max Q 0, le_max_right _ _, fun E =>
    (by simpa [Real.norm_eq_abs] using hQ E : |q E| ≤ Q).trans (le_max_left _ _)⟩

theorem tendsto_sq_mul (K : ℝ) (hK : 0 < K) :
    Tendsto (fun n : ℕ => (n : ℝ) ^ 2 * K) atTop atTop :=
  ((tendsto_pow_atTop two_ne_zero).comp tendsto_natCast_atTop_atTop).atTop_mul_const hK

/-- **T7.** The derivative field `a n q` has unbounded L²(ν) norm and pointwise value. -/
theorem derivative_norm_unbounded (C : ℝ) (hC : 0 < C) (q : ℝ → ℝ) {E1 E2 : ℝ}
    (hq : Continuous q) (hE1 : 0 < E1) (hz : ∀ E ∉ Icc E1 E2, q E = 0)
    (hq0 : ∃ E0, q E0 ≠ 0) (a : ℝ) (ha : a ≠ 0) :
    Tendsto (fun n : ℕ => ∫ z, (a * n * q z.1) ^ 2 ∂nu C) atTop atTop ∧
    ∃ E0, Tendsto (fun n : ℕ => |a * n * q E0|) atTop atTop := by
  obtain ⟨E0, hE0⟩ := hq0
  have hE0mem : E0 ∈ Icc E1 E2 := by
    by_contra hc
    exact hE0 (hz E0 hc)
  have hE0pos : 0 < E0 := lt_of_lt_of_le hE1 hE0mem.1
  obtain ⟨r, hr, hball, hne⟩ := exists_ball_ne_zero q hq hE0pos hE0
  obtain ⟨Q, -, hQ⟩ := bound_of_patch q hq hz
  obtain ⟨-, hI⟩ := radial_integral_pos C hC (fun E => q E ^ 2) (E1 := E1) (E2 := E2)
    (Mw := Q ^ 2) hE1 (hq.measurable.pow_const 2)
    (fun E => by rw [abs_pow]; exact pow_le_pow_left₀ (abs_nonneg _) (hQ E) 2)
    (fun E hE => by rw [hz E hE]; ring) (fun E => sq_nonneg _) hr hball
    (fun E hE => lt_of_le_of_ne (sq_nonneg _) (Ne.symm (pow_ne_zero 2 (hne E hE))))
  have ha2 : 0 < a ^ 2 := lt_of_le_of_ne (sq_nonneg a) (Ne.symm (pow_ne_zero 2 ha))
  constructor
  · refine (tendsto_sq_mul _ (mul_pos ha2 hI)).congr fun n => ?_
    have hfun : (fun z : ℝ × Sphere2 => (a * n * q z.1) ^ 2) =
        fun z => ((n : ℝ) ^ 2 * a ^ 2) * q z.1 ^ 2 := by
      funext z; ring
    rw [hfun, integral_const_mul]
    ring
  · have hpos : 0 < |a| * |q E0| := mul_pos (abs_pos.2 ha) (abs_pos.2 hE0)
    refine ⟨E0, (tendsto_natCast_atTop_atTop.atTop_mul_const hpos).congr fun n => ?_⟩
    rw [abs_mul, abs_mul, Nat.abs_cast]
    ring

/-- **T8.** The horizontal Fisher budget `∫ |∂_x f_n|² / (f_n (1 + ξ f_n)) dν` at `x = 0`
diverges on the family. -/
theorem fisher_unbounded (C : ℝ) (hC : 0 < C) (s : Stat) (g q : ℝ → ℝ) {E1 E2 : ℝ}
    (hgm : Measurable g) (hgc : ContinuousOn g (Icc E1 E2))
    (hgdom : ∀ E, 0 < E → g E ∈ dom s) (hq : Continuous q) (hE1 : 0 < E1)
    (hz : ∀ E ∉ Icc E1 E2, q E = 0) (hq0 : ∃ E0, q E0 ≠ 0) (a : ℝ) (ha : a ≠ 0) :
    Tendsto (fun n : ℕ => ∫ z, (a * n * q z.1) ^ 2 *
      hess s (family (Ω := Sphere2) g q a n 0 z) ∂nu C) atTop atTop := by
  obtain ⟨E0, hE0⟩ := hq0
  have hE0mem : E0 ∈ Icc E1 E2 := by
    by_contra hc
    exact hE0 (hz E0 hc)
  have hE0pos : 0 < E0 := lt_of_lt_of_le hE1 hE0mem.1
  obtain ⟨r, hr, hball, hne⟩ := exists_ball_ne_zero q hq hE0pos hE0
  obtain ⟨Q, -, hQ⟩ := bound_of_patch q hq hz
  have hpatch_pos : ∀ E ∈ Icc E1 E2, 0 < E := fun E hE => lt_of_lt_of_le hE1 hE.1
  have hhc : ContinuousOn (fun E => hess s (g E)) (Icc E1 E2) := by
    unfold hess
    refine continuousOn_const.div
      (hgc.mul (continuousOn_const.add (continuousOn_const.mul hgc))) fun E hE => ?_
    obtain ⟨h0, h1⟩ := dom_pos s (hgdom E (hpatch_pos E hE))
    exact (mul_pos h0 h1).ne'
  obtain ⟨H, hH⟩ := isCompact_Icc.exists_bound_of_continuousOn hhc
  have hhm : Measurable (fun E => hess s (g E)) := by
    unfold hess
    exact measurable_const.div (hgm.mul (measurable_const.add (measurable_const.mul hgm)))
  set w : ℝ → ℝ := fun E => q E ^ 2 * hess s (g E) with hw
  have hw0 : ∀ E ∉ Icc E1 E2, w E = 0 := fun E hE => by simp only [hw, hz E hE]; ring
  have hwnn : ∀ E, 0 ≤ w E := by
    intro E
    by_cases hE : E ∈ Icc E1 E2
    · exact mul_nonneg (sq_nonneg _) (hess_pos s (hgdom E (hpatch_pos E hE))).le
    · rw [hw0 E hE]
  have hwb : ∀ E, |w E| ≤ Q ^ 2 * max H 0 := by
    intro E
    by_cases hE : E ∈ Icc E1 E2
    · simp only [hw]
      rw [abs_mul, abs_pow]
      have h1 : |q E| ^ 2 ≤ Q ^ 2 := pow_le_pow_left₀ (abs_nonneg _) (hQ E) 2
      have h2 : |hess s (g E)| ≤ max H 0 :=
        (by simpa [Real.norm_eq_abs] using hH E hE : |hess s (g E)| ≤ H).trans (le_max_left _ _)
      exact mul_le_mul h1 h2 (abs_nonneg _) (sq_nonneg _)
    · rw [hw0 E hE, abs_zero]
      exact mul_nonneg (sq_nonneg _) (le_max_right _ _)
  have hwpos : ∀ E ∈ Metric.ball E0 r, 0 < w E := by
    intro E hE
    have hqE := hne E hE
    have hEmem : E ∈ Icc E1 E2 := by
      by_contra hc
      exact hqE (hz E hc)
    exact mul_pos (lt_of_le_of_ne (sq_nonneg _) (Ne.symm (pow_ne_zero 2 hqE)))
      (hess_pos s (hgdom E (hpatch_pos E hEmem)))
  obtain ⟨-, hI⟩ := radial_integral_pos C hC w hE1 ((hq.measurable.pow_const 2).mul hhm)
    hwb hw0 hwnn hr hball hwpos
  have ha2 : 0 < a ^ 2 := lt_of_le_of_ne (sq_nonneg a) (Ne.symm (pow_ne_zero 2 ha))
  refine (tendsto_sq_mul _ (mul_pos ha2 hI)).congr fun n => ?_
  have hfun : (fun z : ℝ × Sphere2 =>
      (a * n * q z.1) ^ 2 * hess s (family (Ω := Sphere2) g q a n 0 z)) =
      fun z => ((n : ℝ) ^ 2 * a ^ 2) * w z.1 := by
    funext z
    simp only [family, mul_zero, Real.sin_zero, zero_mul, add_zero, hw]
    ring
  rw [hfun, integral_const_mul]
  ring

/-- **T9.** Final typed TEFF-H1 statement on `dν = C E² dE dΩ`. -/
theorem teff_h1_entropy_ball_derivative_unbounded (C : ℝ) (hC : 0 < C) (s : Stat)
    {m : ℕ} (φ : Fin m → ℝ × Sphere2 → ℝ) (g F : ℝ → ℝ) {E1 E2 : ℝ}
    (hE1 : 0 < E1) (hE12 : E1 < E2)
    (hφ : ∀ j, IntegrableOn (φ j) (patchE E1 E2) (nu C))
    (hgm : Measurable g) (hgc : ContinuousOn g (Icc E1 E2)) (hFc : ContinuousOn F (Icc E1 E2))
    (hgdom : ∀ E, 0 < E → g E ∈ dom s) (hgF : ∀ E, 0 < E → g E ≤ F E)
    (hFcdom : ∀ E, 0 < E → F E ∈ cdom s) (hslack : ∀ E ∈ Icc E1 E2, g E < F E) :
    ∃ B : ℝ, 0 ≤ B ∧ ∀ M : ℝ, ∃ (f : ℝ → ℝ × Sphere2 → ℝ) (d : ℝ × Sphere2 → ℝ),
      (∀ x, Admissible s F (f x)) ∧
      (∀ x, Dext (nu C) (hS s) (hS' s) (f x) (fun z => g z.1) ≤ ENNReal.ofReal B) ∧
      (∀ x j, ∫ z, φ j z * (f x z - g z.1) ∂nu C = 0) ∧
      (∀ z, HasDerivAt (fun t => f t z) (d z) 0) ∧
      M < ∫ z, d z ^ 2 ∂nu C ∧
      M < ∫ z, d z ^ 2 * hess s (f 0 z) ∂nu C := by
  obtain ⟨q, a, B, hqcd, -, hqts, ⟨E0, -, hqE0⟩, -, ha, hB0, hall⟩ :=
    moment_null_counterexample (nu C) s φ g F hE1 hE12 (nu_facts C).1
      ((nu_facts C).2 E1 E2 hE1) hφ hgm hgc hFc hgdom hgF hFcdom hslack
  have hz : ∀ E ∉ Icc E1 E2, q E = 0 := fun E hE =>
    image_eq_zero_of_notMem_tsupport fun h => hE (hqts h)
  have hL2 := (derivative_norm_unbounded C hC q hqcd.continuous hE1 hz ⟨E0, hqE0⟩ a ha.ne').1
  have hFi := fisher_unbounded C hC s g q hgm hgc hgdom hqcd.continuous hE1 hz ⟨E0, hqE0⟩ a
    ha.ne'
  refine ⟨B, hB0, fun M => ?_⟩
  obtain ⟨N, hN1, hN2⟩ := ((hL2.eventually (eventually_gt_atTop M)).and
    (hFi.eventually (eventually_gt_atTop M))).exists
  exact ⟨fun x => family g q a N x, fun z => a * N * q z.1, fun x => (hall N x).1,
    fun x => (hall N x).2.2.2.1, fun x j => (hall N x).2.2.1 j,
    fun z => (hall N 0).2.2.2.2.2 z, hN1, hN2⟩

/-- **T10.** Non-vacuity: BE photon envelope `F_b = 1/(e^{bE}-1)`, base state
`g = 1/(e^{2bE}-1)`, retained number and energy scores, patch `[1, 2]`. -/
theorem teff_h1_BE_instance (C b : ℝ) (hC : 0 < C) (hb : 0 < b) :
    ∃ B : ℝ, 0 ≤ B ∧ ∀ M : ℝ, ∃ (f : ℝ → ℝ × Sphere2 → ℝ) (d : ℝ × Sphere2 → ℝ),
      (∀ x, Admissible Stat.BE (fun E => G12D.occupation b 0 E) (f x)) ∧
      (∀ x, Dext (nu C) (hS .BE) (hS' .BE) (f x)
          (fun z => G12D.occupation (2 * b) 0 z.1) ≤ ENNReal.ofReal B) ∧
      (∀ x j, ∫ z, numberEnergyScores j z *
          (f x z - G12D.occupation (2 * b) 0 z.1) ∂nu C = 0) ∧
      (∀ z, HasDerivAt (fun t => f t z) (d z) 0) ∧
      M < ∫ z, d z ^ 2 ∂nu C ∧
      M < ∫ z, d z ^ 2 * hess .BE (f 0 z) ∂nu C := by
  have hden : ∀ β E : ℝ, 0 < β → 0 < E → 0 < Real.exp (β * E - 0) - 1 :=
    fun β E hβ hE => G12DClosure.occupation_denominator_pos β 0 E hβ le_rfl hE
  have hb2 : 0 < 2 * b := by positivity
  have hP : nu C (patchE 1 2) ≠ ⊤ := (nu_facts C).2 1 2 one_pos
  refine teff_h1_entropy_ball_derivative_unbounded C hC .BE numberEnergyScores
    (fun E => G12D.occupation (2 * b) 0 E) (fun E => G12D.occupation b 0 E) one_pos one_lt_two
    ?_ ?_ ?_ ?_ ?_ ?_ ?_ ?_
  · intro j
    fin_cases j
    · show IntegrableOn (fun _ : ℝ × Sphere2 => (1 : ℝ)) (patchE 1 2) (nu C)
      exact integrableOn_const hP
    · show IntegrableOn (fun z : ℝ × Sphere2 => z.1) (patchE 1 2) (nu C)
      exact Measure.integrableOn_of_bounded hP measurable_fst.aestronglyMeasurable (M := 2)
        ((ae_restrict_iff' (patchE_measurable 1 2)).2 (ae_of_all _ fun z hz => by
          rw [Real.norm_eq_abs, abs_le]
          have h1 : (1 : ℝ) ≤ z.1 := hz.1
          have h2 : z.1 ≤ 2 := hz.2
          constructor <;> linarith))
  · show Measurable fun E : ℝ => (Real.exp (2 * b * E - 0) - 1)⁻¹
    fun_prop
  · show ContinuousOn (fun E : ℝ => (Real.exp (2 * b * E - 0) - 1)⁻¹) (Icc 1 2)
    exact ContinuousOn.inv₀ (by fun_prop) fun E hE =>
      (hden _ E hb2 (by linarith [hE.1])).ne'
  · show ContinuousOn (fun E : ℝ => (Real.exp (b * E - 0) - 1)⁻¹) (Icc 1 2)
    exact ContinuousOn.inv₀ (by fun_prop) fun E hE =>
      (hden _ E hb (by linarith [hE.1])).ne'
  · intro E hE
    show 0 < (Real.exp (2 * b * E - 0) - 1)⁻¹
    exact inv_pos.2 (hden _ E hb2 hE)
  · intro E hE
    exact (G12D.occupation_envelope (2 * b) 0 b E (by linarith) hb le_rfl hE).2
  · intro E hE
    exact G12D.occupation_nonneg b 0 E hb le_rfl hE
  · intro E hE
    have hE0 : 0 < E := by linarith [hE.1]
    show (Real.exp (2 * b * E - 0) - 1)⁻¹ < (Real.exp (b * E - 0) - 1)⁻¹
    rw [inv_lt_inv₀ (hden _ E hb2 hE0) (hden _ E hb hE0)]
    have hlt : b * E - 0 < 2 * b * E - 0 := by nlinarith [mul_pos hb hE0]
    linarith [Real.exp_lt_exp.2 hlt]

/-- **T11.** Negative control: a single bump does not annihilate the number moment, so the
kernel combination of `moment_null_exists` is needed once `φ = 1` is retained. -/
theorem single_bump_number_moment_pos (C : ℝ) (hC : 0 < C) {E1 E2 : ℝ}
    (hE1 : 0 < E1) (h : E1 < E2) (m : ℕ) (i : Fin (m + 1)) :
    0 < ∫ z, numberEnergyScores 0 z * psi h m i z.1 ∂nu C := by
  have hfun : (fun z : ℝ × Sphere2 => numberEnergyScores 0 z * psi h m i z.1) =
      fun z => psi h m i z.1 := by
    funext z
    show (1 : ℝ) * psi h m i z.1 = psi h m i z.1
    rw [one_mul]
  rw [hfun]
  have hball : Metric.ball (cellCenter E1 E2 m i) (cellWidth E1 E2 m / 2) ⊆ Ioi 0 := by
    rw [← psi_support h m i]
    exact fun E hE => lt_trans hE1 (psi_support_subset h m i hE).1
  exact (radial_integral_pos C hC (psi h m i) (E1 := E1) (E2 := E2) (Mw := 1) hE1
    (psi_continuous h m i).measurable
    (fun E => by rw [abs_of_nonneg (psi_nonneg h m i E)]; exact psi_le_one h m i E)
    (fun E hE => psi_eq_zero_outside h m i fun h' => hE (Ioo_subset_Icc_self h'))
    (psi_nonneg h m i) (by have := cellWidth_pos h m; positivity) hball
    (fun E hE => (cellBump h m i).pos_of_mem_ball hE)).2

end G12E
