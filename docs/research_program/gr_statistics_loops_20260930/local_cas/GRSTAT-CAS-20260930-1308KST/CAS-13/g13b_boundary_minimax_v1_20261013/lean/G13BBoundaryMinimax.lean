import MeasureExtremizerBridge
import Main

/-!
# G13-B: feasibility boundary, same-prior energy-only interval, fibre nesting, C04 minimax

Imports, unchanged: the reviewed G13-A source `MeasureExtremizerBridge.lean`
(sha256 a64f6c3c…fda12) and the reviewed C04 source `CAS-13/lean/Main.lean` (sha256 5be0cd66…da97).

* Boundary data are handled by direct moment rigidity of actual measures (Dirac collapse on the
  lower curve, endpoint collapse on the chord); no interior node formula is evaluated at `u = a`
  or `d = b`.
* Energy-only comparisons always use the same support `[a,b]` and the same retained `m4`.
* Sharpness of the interior interval is claimed only for `p = 5, 6` (G13-A certificates);
  for real `p > 4` only the energy-only interval and endpoint-value nesting are claimed.
* No scientific admission is asserted.
-/

noncomputable section
open MeasureTheory Set

namespace CAS13G13B
open CAS13MeasureComposition

/-! ## Definitions -/

/-- Upper chord of the moment region; verbatim right-hand side of S121 / `StrictInterior.upper`. -/
def chord (a b m3 : ℝ) : ℝ := a ^ 4 + (m3 - a ^ 3) * (b ^ 4 - a ^ 4) / (b ^ 3 - a ^ 3)

/-- Closure of the S121 feasible region. -/
def ClosedRegion (a b m3 m4 : ℝ) : Prop :=
  a ^ 3 ≤ m3 ∧ m3 ≤ b ^ 3 ∧ m3 ^ ((4 : ℝ) / 3) ≤ m4 ∧ m4 ≤ chord a b m3

/-- Number–energy fibre of the common support prior `[a,b]`. -/
def NEFibre (a b m3 m4 : ℝ) : Set (Measure ℝ) :=
  {μ | IsProbabilityMeasure μ ∧ (∀ᵐ x ∂μ, x ∈ Icc a b) ∧ moment μ 3 = m3 ∧ moment μ 4 = m4}

/-- Energy-only fibre of the same support prior `[a,b]`. -/
def EFibre (a b m4 : ℝ) : Set (Measure ℝ) :=
  {μ | IsProbabilityMeasure μ ∧ (∀ᵐ x ∂μ, x ∈ Icc a b) ∧ moment μ 4 = m4}

/-- Real-exponent moment (`Real.rpow`). -/
def rmoment (μ : Measure ℝ) (p : ℝ) : ℝ := ∫ x, x ^ p ∂μ

/-- S126 lower endpoint. -/
def energyLower (m4 p : ℝ) : ℝ := m4 ^ (p / 4)

/-- S126 upper endpoint. -/
def energyUpper (a b m4 p : ℝ) : ℝ :=
  ((b ^ 4 - m4) * a ^ p + (m4 - a ^ 4) * b ^ p) / (b ^ 4 - a ^ 4)

def energyWeight (a b m4 : ℝ) : ℝ := (m4 - a ^ 4) / (b ^ 4 - a ^ 4)

/-- S122 lower node condition (verbatim G13-A form). -/
def LowerNode (a b m3 m4 u : ℝ) : Prop :=
  CAS13C02.positiveCubeRoot m3 < u ∧ u < b ∧
    (u ^ 4 - a ^ 4) / (u ^ 3 - a ^ 3) = (m4 - a ^ 4) / (m3 - a ^ 3)

/-- S122 upper node condition (verbatim G13-A form). -/
def UpperNode (a b m3 m4 d : ℝ) : Prop :=
  a < d ∧ d < CAS13C02.positiveCubeRoot m3 ∧
    (b ^ 4 - d ^ 4) / (b ^ 3 - d ^ 3) = (b ^ 4 - m4) / (b ^ 3 - m3)

/-- S124 `L_p`. -/
def lowerEnd (a m3 u p : ℝ) : ℝ :=
  (1 - CAS13C02.lowerWeight a m3 u) * a ^ p + CAS13C02.lowerWeight a m3 u * u ^ p

/-- S124 `U_p`. -/
def upperEnd (b m3 d p : ℝ) : ℝ :=
  (1 - CAS13C02.upperWeight b m3 d) * d ^ p + CAS13C02.upperWeight b m3 d * b ^ p

/-- Sharp attained interval of the `p`-th moment over a class of measures (exact range). -/
def SharpInterval (F : Set (Measure ℝ)) (p : ℕ) (L U : ℝ) : Prop :=
  (∀ μ ∈ F, L ≤ moment μ p ∧ moment μ p ≤ U) ∧
  (∃ μ ∈ F, moment μ p = L) ∧ (∃ μ ∈ F, moment μ p = U) ∧
  (fun μ => moment μ p) '' F = Icc L U

/-- C04 relative minimax lifted to a class of measures. -/
def FibreMinimax (F : Set (Measure ℝ)) (p : ℕ) (L U : ℝ) : Prop :=
  (∀ μ ∈ F, |(grstatTau L U - moment μ p) / moment μ p| ≤ grstatEps L U) ∧
  (∃ μ ∈ F, |(grstatTau L U - moment μ p) / moment μ p| = grstatEps L U) ∧
  (∀ t : ℝ, ∃ μ ∈ F, grstatEps L U ≤ |(t - moment μ p) / moment μ p|)

/-- Convex mixture of two measures (weight `θ` on the first). -/
def mix (θ : ℝ) (μ ν : Measure ℝ) : Measure ℝ :=
  ENNReal.ofReal θ • μ + ENNReal.ofReal (1 - θ) • ν

/-! ## Helpers -/

theorem integrable_of_Icc {μ : Measure ℝ} [IsFiniteMeasure μ] {a b : ℝ}
    (hs : ∀ᵐ x ∂μ, x ∈ Icc a b) {f : ℝ → ℝ} (hf : Continuous f) : Integrable f μ := by
  obtain ⟨C, hC⟩ := isCompact_Icc.exists_bound_of_continuousOn hf.continuousOn
  exact Integrable.of_bound hf.aestronglyMeasurable C (hs.mono fun x hx => hC x hx)

theorem admissible_of_mem {a b m3 m4 : ℝ} {μ : Measure ℝ} (hμ : μ ∈ NEFibre a b m3 m4)
    (p : ℕ) : Admissible μ a b m3 m4 p := by
  obtain ⟨hP, hs, h3, h4⟩ := hμ
  haveI := hP
  exact ⟨hP, hs, integrable_of_Icc hs (continuous_pow 3), integrable_of_Icc hs (continuous_pow 4),
    integrable_of_Icc hs (continuous_pow p), h3, h4⟩

theorem moment_bounds {a b : ℝ} (ha : 0 ≤ a) {μ : Measure ℝ} [IsProbabilityMeasure μ]
    (hs : ∀ᵐ x ∂μ, x ∈ Icc a b) (n : ℕ) : a ^ n ≤ moment μ n ∧ moment μ n ≤ b ^ n := by
  have hi : Integrable (fun x : ℝ => x ^ n) μ := integrable_of_Icc hs (continuous_pow n)
  constructor
  · have h := integral_mono_ae (integrable_const (a ^ n)) hi
      (hs.mono fun x hx => pow_le_pow_left₀ ha hx.1 n)
    simpa [moment] using h
  · have h := integral_mono_ae hi (integrable_const (b ^ n))
      (hs.mono fun x hx => pow_le_pow_left₀ (ha.trans hx.1) hx.2 n)
    simpa [moment] using h

theorem integral_poly {a b m3 m4 : ℝ} {μ : Measure ℝ} (hμ : μ ∈ NEFibre a b m3 m4)
    (c0 c3 c4 : ℝ) : ∫ x, (c0 + c3 * x ^ 3 + c4 * x ^ 4) ∂μ = c0 + c3 * m3 + c4 * m4 := by
  obtain ⟨hP, hs, h3, h4⟩ := hμ
  haveI := hP
  exact integral_hermite μ (integrable_of_Icc hs (continuous_pow 3))
    (integrable_of_Icc hs (continuous_pow 4)) h3 h4

theorem measure_eq_of_real {μ ν : Measure ℝ} [IsFiniteMeasure μ] [IsFiniteMeasure ν]
    (h : ∀ s, MeasurableSet s → μ.real s = ν.real s) : μ = ν :=
  Measure.ext fun s hs =>
    (ENNReal.toReal_eq_toReal_iff' (measure_ne_top μ s) (measure_ne_top ν s)).1 (by
      simpa [measureReal_def] using h s hs)

theorem eq_dirac_of_ae {μ : Measure ℝ} [IsProbabilityMeasure μ] {r : ℝ}
    (h : ∀ᵐ x ∂μ, x = r) : μ = Measure.dirac r := by
  have h0 : μ {x | ¬ x = r} = 0 := ae_iff.1 h
  ext s hs
  by_cases hr : r ∈ s
  · rw [Measure.dirac_apply_of_mem hr, ← prob_compl_eq_zero_iff hs]
    refine measure_mono_null (fun x hx => ?_) h0
    intro hxr
    exact hx (hxr ▸ hr)
  · rw [Measure.dirac_apply' r hs, Set.indicator_of_notMem hr]
    refine measure_mono_null (fun x hx => ?_) h0
    intro hxr
    exact hr (hxr ▸ hx)

theorem cube_rpow {x : ℝ} (hx : 0 ≤ x) : (x ^ 3) ^ ((4 : ℝ) / 3) = x ^ 4 := by
  rw [← Real.rpow_natCast x 3, ← Real.rpow_mul hx,
    show ((3 : ℕ) : ℝ) * (4 / 3) = ((4 : ℕ) : ℝ) by norm_num, Real.rpow_natCast]

theorem rpow_four_div {x : ℝ} (hx : 0 ≤ x) (p : ℝ) : (x ^ 4) ^ (p / 4) = x ^ p := by
  rw [← Real.rpow_natCast x 4, ← Real.rpow_mul hx]
  congr 1
  push_cast
  ring

theorem fibre_cube {a b m3 m4 : ℝ} (ha : 0 < a) {μ : Measure ℝ}
    (hμ : μ ∈ NEFibre a b m3 m4) : a ^ 3 ≤ m3 ∧ m3 ≤ b ^ 3 ∧ a ^ 4 ≤ m4 ∧ m4 ≤ b ^ 4 := by
  obtain ⟨hP, hs, h3, h4⟩ := hμ
  haveI := hP
  obtain ⟨c1, c2⟩ := moment_bounds ha.le hs 3
  obtain ⟨c3, c4⟩ := moment_bounds ha.le hs 4
  rw [h3] at c1 c2
  rw [h4] at c3 c4
  exact ⟨c1, c2, c3, c4⟩

/-! ## Lower curve: Jensen gap and rigidity -/

theorem lower_gap_nonneg {r x : ℝ} (hr : 0 ≤ r) (hx : 0 ≤ x) :
    0 ≤ (x - r) ^ 2 * (3 * x ^ 2 + 2 * r * x + r ^ 2) := by
  have : 0 ≤ 3 * x ^ 2 + 2 * r * x + r ^ 2 := by positivity
  exact mul_nonneg (sq_nonneg _) this

theorem lower_gap_integral {a b m3 m4 r : ℝ} {μ : Measure ℝ} (hμ : μ ∈ NEFibre a b m3 m4) :
    ∫ x, (x - r) ^ 2 * (3 * x ^ 2 + 2 * r * x + r ^ 2) ∂μ = r ^ 4 + (-4 * r) * m3 + 3 * m4 := by
  rw [← integral_poly hμ (r ^ 4) (-4 * r) 3]
  congr 1
  funext x
  ring

theorem lower_ineq_core {a b m3 m4 r : ℝ} (ha : 0 < a) (hr : 0 ≤ r) {μ : Measure ℝ}
    (hμ : μ ∈ NEFibre a b m3 m4) (hr3 : r ^ 3 = m3) : r ^ 4 ≤ m4 := by
  have hs := hμ.2.1
  have hnn : 0 ≤ ∫ x, (x - r) ^ 2 * (3 * x ^ 2 + 2 * r * x + r ^ 2) ∂μ :=
    integral_nonneg_of_ae (hs.mono fun x hx => lower_gap_nonneg hr (ha.le.trans hx.1))
  rw [lower_gap_integral hμ] at hnn
  nlinarith [hr3]

theorem lower_rigid_core {a b m3 m4 r : ℝ} (ha : 0 < a) (hr : 0 < r) {μ : Measure ℝ}
    (hμ : μ ∈ NEFibre a b m3 m4) (hr3 : r ^ 3 = m3) (hr4 : r ^ 4 = m4) :
    ∀ᵐ x ∂μ, x = r := by
  have hP := hμ.1
  have hs := hμ.2.1
  haveI := hP
  have hzero : ∫ x, (x - r) ^ 2 * (3 * x ^ 2 + 2 * r * x + r ^ 2) ∂μ = 0 := by
    rw [lower_gap_integral hμ]
    linear_combination (4 * r) * hr3 - 3 * hr4
  have hnn : 0 ≤ᵐ[μ] fun x => (x - r) ^ 2 * (3 * x ^ 2 + 2 * r * x + r ^ 2) :=
    hs.mono fun x hx => lower_gap_nonneg hr.le (ha.le.trans hx.1)
  have hi : Integrable (fun x => (x - r) ^ 2 * (3 * x ^ 2 + 2 * r * x + r ^ 2)) μ :=
    integrable_of_Icc hs (by fun_prop)
  have hae := (integral_eq_zero_iff_of_nonneg_ae hnn hi).1 hzero
  filter_upwards [hae, hs] with x hx hxs
  have hx0 : 0 < x := ha.trans_le hxs.1
  have hK : 0 < 3 * x ^ 2 + 2 * r * x + r ^ 2 := by positivity
  have h0 : (x - r) ^ 2 * (3 * x ^ 2 + 2 * r * x + r ^ 2) = 0 := hx
  rcases mul_eq_zero.1 h0 with h | h
  · exact sub_eq_zero.1 ((pow_eq_zero_iff two_ne_zero).1 h)
  · exact absurd h hK.ne'

/-! ## Upper chord: chord gap and rigidity -/

theorem chord_gap_factor (a b x : ℝ) :
    (b ^ 3 - a ^ 3) * (x ^ 4 - a ^ 4) - (x ^ 3 - a ^ 3) * (b ^ 4 - a ^ 4) =
      (x - a) * (x - b) * (b - a) *
        (a ^ 2 * b ^ 2 + a ^ 2 * b * x + a ^ 2 * x ^ 2 + a * b ^ 2 * x + a * b * x ^ 2 +
          b ^ 2 * x ^ 2) := by
  ring

theorem chord_gap_nonpos {a b x : ℝ} (ha : 0 < a) (hab : a < b) (hx : x ∈ Icc a b) :
    (b ^ 3 - a ^ 3) * (x ^ 4 - a ^ 4) - (x ^ 3 - a ^ 3) * (b ^ 4 - a ^ 4) ≤ 0 := by
  rw [chord_gap_factor]
  have hb : 0 < b := ha.trans hab
  have hx0 : 0 < x := ha.trans_le hx.1
  have hK : 0 < a ^ 2 * b ^ 2 + a ^ 2 * b * x + a ^ 2 * x ^ 2 + a * b ^ 2 * x + a * b * x ^ 2 +
      b ^ 2 * x ^ 2 := by positivity
  have h1 : (x - a) * (x - b) ≤ 0 :=
    mul_nonpos_of_nonneg_of_nonpos (sub_nonneg.2 hx.1) (sub_nonpos.2 hx.2)
  have h2 : (x - a) * (x - b) * (b - a) ≤ 0 :=
    mul_nonpos_of_nonpos_of_nonneg h1 (sub_nonneg.2 hab.le)
  exact mul_nonpos_of_nonpos_of_nonneg h2 hK.le

theorem chord_gap_integral {a b m3 m4 : ℝ} {μ : Measure ℝ} (hμ : μ ∈ NEFibre a b m3 m4) :
    ∫ x, ((b ^ 3 - a ^ 3) * (x ^ 4 - a ^ 4) - (x ^ 3 - a ^ 3) * (b ^ 4 - a ^ 4)) ∂μ =
      (b ^ 3 - a ^ 3) * (m4 - a ^ 4) - (m3 - a ^ 3) * (b ^ 4 - a ^ 4) := by
  have h := integral_poly hμ (-(b ^ 3 - a ^ 3) * a ^ 4 + a ^ 3 * (b ^ 4 - a ^ 4))
    (-(b ^ 4 - a ^ 4)) (b ^ 3 - a ^ 3)
  calc ∫ x, ((b ^ 3 - a ^ 3) * (x ^ 4 - a ^ 4) - (x ^ 3 - a ^ 3) * (b ^ 4 - a ^ 4)) ∂μ
      = ∫ x, ((-(b ^ 3 - a ^ 3) * a ^ 4 + a ^ 3 * (b ^ 4 - a ^ 4)) + (-(b ^ 4 - a ^ 4)) * x ^ 3
          + (b ^ 3 - a ^ 3) * x ^ 4) ∂μ := by
        congr 1
        funext x
        ring
    _ = _ := by rw [h]; ring

theorem cube_den_pos {a b : ℝ} (ha : 0 < a) (hab : a < b) : 0 < b ^ 3 - a ^ 3 :=
  sub_pos.2 (pow_lt_pow_left₀ hab ha.le (by norm_num))

theorem quartic_den_pos {a b : ℝ} (ha : 0 < a) (hab : a < b) : 0 < b ^ 4 - a ^ 4 :=
  sub_pos.2 (pow_lt_pow_left₀ hab ha.le (by norm_num))

theorem upper_ineq_core {a b m3 m4 : ℝ} (ha : 0 < a) (hab : a < b) {μ : Measure ℝ}
    (hμ : μ ∈ NEFibre a b m3 m4) : m4 ≤ chord a b m3 := by
  have hs := hμ.2.1
  have hnp : ∫ x, ((b ^ 3 - a ^ 3) * (x ^ 4 - a ^ 4) - (x ^ 3 - a ^ 3) * (b ^ 4 - a ^ 4)) ∂μ ≤ 0 :=
    integral_nonpos_of_ae (hs.mono fun x hx => chord_gap_nonpos ha hab hx)
  rw [chord_gap_integral hμ] at hnp
  have hD := cube_den_pos ha hab
  unfold chord
  have : m4 - a ^ 4 ≤ (m3 - a ^ 3) * (b ^ 4 - a ^ 4) / (b ^ 3 - a ^ 3) := by
    rw [le_div_iff₀ hD]
    linarith
  linarith

theorem upper_rigid_core {a b m3 m4 : ℝ} (ha : 0 < a) (hab : a < b) {μ : Measure ℝ}
    (hμ : μ ∈ NEFibre a b m3 m4) (hbd : m4 = chord a b m3) : ∀ᵐ x ∂μ, x = a ∨ x = b := by
  have hP := hμ.1
  have hs := hμ.2.1
  haveI := hP
  have hD := cube_den_pos ha hab
  have hzero : ∫ x, -((b ^ 3 - a ^ 3) * (x ^ 4 - a ^ 4) - (x ^ 3 - a ^ 3) * (b ^ 4 - a ^ 4)) ∂μ
      = 0 := by
    rw [integral_neg, chord_gap_integral hμ, hbd]
    unfold chord
    field_simp
    ring
  have hnn : 0 ≤ᵐ[μ] fun x =>
      -((b ^ 3 - a ^ 3) * (x ^ 4 - a ^ 4) - (x ^ 3 - a ^ 3) * (b ^ 4 - a ^ 4)) :=
    hs.mono fun x hx => neg_nonneg.2 (chord_gap_nonpos ha hab hx)
  have hi : Integrable (fun x =>
      -((b ^ 3 - a ^ 3) * (x ^ 4 - a ^ 4) - (x ^ 3 - a ^ 3) * (b ^ 4 - a ^ 4))) μ :=
    integrable_of_Icc hs (by fun_prop)
  have hae := (integral_eq_zero_iff_of_nonneg_ae hnn hi).1 hzero
  filter_upwards [hae, hs] with x hx hxs
  have hb : 0 < b := ha.trans hab
  have hx0 : 0 < x := ha.trans_le hxs.1
  have hK : 0 < a ^ 2 * b ^ 2 + a ^ 2 * b * x + a ^ 2 * x ^ 2 + a * b ^ 2 * x + a * b * x ^ 2 +
      b ^ 2 * x ^ 2 := by positivity
  have h0 : -((b ^ 3 - a ^ 3) * (x ^ 4 - a ^ 4) - (x ^ 3 - a ^ 3) * (b ^ 4 - a ^ 4)) = 0 := hx
  rw [chord_gap_factor, neg_eq_zero] at h0
  rcases mul_eq_zero.1 h0 with h | h
  · rcases mul_eq_zero.1 h with h' | h'
    · rcases mul_eq_zero.1 h' with h'' | h''
      · exact Or.inl (sub_eq_zero.1 h'')
      · exact Or.inr (sub_eq_zero.1 h'')
    · exact absurd (sub_eq_zero.1 h') hab.ne'
  · exact absurd h hK.ne'

theorem indicator_two_point {a b x : ℝ} (hab : a < b) (ha : 0 < a) (s : Set ℝ)
    (hx : x = a ∨ x = b) :
    s.indicator (1 : ℝ → ℝ) x =
      (s.indicator 1 a - (s.indicator 1 b - s.indicator 1 a) * a ^ 3 / (b ^ 3 - a ^ 3)) +
        ((s.indicator 1 b - s.indicator 1 a) / (b ^ 3 - a ^ 3)) * x ^ 3 + 0 * x ^ 4 := by
  have hD : b ^ 3 - a ^ 3 ≠ 0 := (cube_den_pos ha hab).ne'
  rcases hx with hx | hx
  · rw [hx]
    ring
  · rw [hx]
    field_simp
    ring

/-! ## T1: feasible region -/

theorem region_corners {a b : ℝ} (ha : 0 < a) (hab : a < b) :
    (a ^ 3) ^ ((4 : ℝ) / 3) = a ^ 4 ∧ chord a b (a ^ 3) = a ^ 4 ∧
    (b ^ 3) ^ ((4 : ℝ) / 3) = b ^ 4 ∧ chord a b (b ^ 3) = b ^ 4 := by
  have hb : 0 < b := ha.trans hab
  have hD := (cube_den_pos ha hab).ne'
  refine ⟨cube_rpow ha.le, by simp [chord], cube_rpow hb.le, ?_⟩
  unfold chord
  field_simp
  ring

theorem region_necessary {a b m3 m4 : ℝ} (ha : 0 < a) (hab : a < b) {μ : Measure ℝ}
    (hμ : μ ∈ NEFibre a b m3 m4) : ClosedRegion a b m3 m4 := by
  obtain ⟨c1, c2, -, -⟩ := fibre_cube ha hμ
  have hm3 : 0 < m3 := lt_of_lt_of_le (pow_pos ha 3) c1
  have hr := CAS13C02.positiveCubeRoot_pos hm3
  have hr3 := CAS13C02.positiveCubeRoot_cube hm3.le
  have hr4 := CAS13C02.positiveCubeRoot_fourth hm3.le
  refine ⟨c1, c2, ?_, upper_ineq_core ha hab hμ⟩
  rw [← hr4]
  exact lower_ineq_core ha hr.le hμ hr3

theorem lowerCurve_lt_chord {a b m3 : ℝ} (ha : 0 < a) (hab : a < b)
    (h3 : a ^ 3 < m3) (h3' : m3 < b ^ 3) : m3 ^ ((4 : ℝ) / 3) < chord a b m3 := by
  obtain ⟨hr, hr3, har, hrb⟩ := CAS13C02.root_between ha hab h3 h3'
  have hm3 : 0 < m3 := lt_trans (pow_pos ha 3) h3
  rw [← CAS13C02.positiveCubeRoot_fourth hm3.le]
  have hb : 0 < b := ha.trans hab
  have hD := cube_den_pos ha hab
  set r := CAS13C02.positiveCubeRoot m3 with hrdef
  have hK : 0 < a ^ 2 * b ^ 2 + a ^ 2 * b * r + a ^ 2 * r ^ 2 + a * b ^ 2 * r + a * b * r ^ 2 +
      b ^ 2 * r ^ 2 := by positivity
  have hneg : (b ^ 3 - a ^ 3) * (r ^ 4 - a ^ 4) - (r ^ 3 - a ^ 3) * (b ^ 4 - a ^ 4) < 0 := by
    rw [chord_gap_factor]
    have h1 : (r - a) * (r - b) < 0 := mul_neg_of_pos_of_neg (sub_pos.2 har) (sub_neg.2 hrb)
    have h2 : (r - a) * (r - b) * (b - a) < 0 := mul_neg_of_neg_of_pos h1 (sub_pos.2 hab)
    exact mul_neg_of_neg_of_pos h2 hK
  unfold chord
  rw [← hr3]
  have : r ^ 4 - a ^ 4 < (r ^ 3 - a ^ 3) * (b ^ 4 - a ^ 4) / (b ^ 3 - a ^ 3) := by
    rw [lt_div_iff₀ hD]
    linarith
  linarith

theorem region_strata {a b m3 m4 : ℝ} (ha : 0 < a) (hab : a < b) (h : ClosedRegion a b m3 m4) :
    CAS13C02.StrictInterior a b m3 m4 ∨ m4 = m3 ^ ((4 : ℝ) / 3) ∨ m4 = chord a b m3 := by
  obtain ⟨h1, h2, h3, h4⟩ := h
  rcases eq_or_lt_of_le h3 with h3e | h3l
  · exact Or.inr (Or.inl h3e.symm)
  rcases eq_or_lt_of_le h4 with h4e | h4l
  · exact Or.inr (Or.inr h4e)
  left
  obtain ⟨c1, c2, c3, c4⟩ := region_corners ha hab
  have hm3a : a ^ 3 < m3 := by
    rcases eq_or_lt_of_le h1 with he | hl
    · exfalso
      rw [← he, c1] at h3l
      rw [← he, c2] at h4l
      linarith
    · exact hl
  have hm3b : m3 < b ^ 3 := by
    rcases eq_or_lt_of_le h2 with he | hl
    · exfalso
      rw [he, c3] at h3l
      rw [he, c4] at h4l
      linarith
    · exact hl
  exact ⟨ha, hab, hm3a, hm3b, h3l, h4l⟩

/-! ## T2: boundary collapse and boundary extrema -/

theorem lower_boundary_dirac_collapse {a b m3 m4 : ℝ} (ha : 0 < a) (hab : a < b)
    {μ : Measure ℝ} (hμ : μ ∈ NEFibre a b m3 m4) (hbd : m4 = m3 ^ ((4 : ℝ) / 3)) :
    μ = Measure.dirac (CAS13C02.positiveCubeRoot m3) := by
  have hP := hμ.1
  haveI := hP
  obtain ⟨c1, -, -, -⟩ := fibre_cube ha hμ
  have hm3 : 0 < m3 := lt_of_lt_of_le (pow_pos ha 3) c1
  have hr := CAS13C02.positiveCubeRoot_pos hm3
  have hr3 := CAS13C02.positiveCubeRoot_cube hm3.le
  have hr4 := CAS13C02.positiveCubeRoot_fourth hm3.le
  exact eq_dirac_of_ae (lower_rigid_core ha hr hμ hr3 (hr4.trans hbd.symm))

theorem upper_boundary_endpoint_collapse {a b m3 m4 : ℝ} (ha : 0 < a) (hab : a < b)
    {μ : Measure ℝ} (hμ : μ ∈ NEFibre a b m3 m4) (hbd : m4 = chord a b m3) :
    μ = twoDirac (CAS13C02.chordWeight a b m3) a b := by
  have hae := upper_rigid_core ha hab hμ hbd
  have hP := hμ.1
  haveI := hP
  obtain ⟨c1, c2, -, -⟩ := fibre_cube ha hμ
  have hD := cube_den_pos ha hab
  have hw0 : 0 ≤ CAS13C02.chordWeight a b m3 := div_nonneg (sub_nonneg.2 c1) hD.le
  have hw1 : CAS13C02.chordWeight a b m3 ≤ 1 := (div_le_one hD).2 (by linarith)
  haveI := twoDirac_probability (a := a) (u := b) hw0 hw1
  apply measure_eq_of_real
  intro s hs
  have hcongr : (fun x => s.indicator (1 : ℝ → ℝ) x) =ᵐ[μ] fun x =>
      (s.indicator 1 a - (s.indicator 1 b - s.indicator 1 a) * a ^ 3 / (b ^ 3 - a ^ 3)) +
        ((s.indicator 1 b - s.indicator 1 a) / (b ^ 3 - a ^ 3)) * x ^ 3 + 0 * x ^ 4 :=
    hae.mono fun x hx => indicator_two_point hab ha s hx
  have e1 : μ.real s =
      (s.indicator 1 a - (s.indicator 1 b - s.indicator 1 a) * a ^ 3 / (b ^ 3 - a ^ 3)) +
        ((s.indicator 1 b - s.indicator 1 a) / (b ^ 3 - a ^ 3)) * m3 + 0 * m4 := by
    rw [← integral_indicator_one hs, ← integral_poly hμ]
    exact integral_congr_ae hcongr
  have e2 : (twoDirac (CAS13C02.chordWeight a b m3) a b).real s =
      (1 - CAS13C02.chordWeight a b m3) * s.indicator 1 a +
        CAS13C02.chordWeight a b m3 * s.indicator 1 b := by
    rw [← integral_indicator_one hs]
    exact integral_twoDirac (fun x => s.indicator (1 : ℝ → ℝ) x) hw0 hw1
  rw [e1, e2]
  unfold CAS13C02.chordWeight
  field_simp
  ring

theorem sharpInterval_of_const {F : Set (Measure ℝ)} {p : ℕ} {v : ℝ} {μ0 : Measure ℝ}
    (h0 : μ0 ∈ F) (hc : ∀ μ ∈ F, moment μ p = v) : SharpInterval F p v v := by
  refine ⟨fun μ hμ => ⟨(hc μ hμ).ge, (hc μ hμ).le⟩, ⟨μ0, h0, hc μ0 h0⟩, ⟨μ0, h0, hc μ0 h0⟩, ?_⟩
  ext m
  simp only [mem_image, mem_Icc]
  constructor
  · rintro ⟨μ, hμ, rfl⟩
    exact ⟨(hc μ hμ).ge, (hc μ hμ).le⟩
  · rintro ⟨h1, h2⟩
    exact ⟨μ0, h0, by rw [hc μ0 h0]; linarith⟩

theorem cube_root_mem {a b m3 : ℝ} (ha : 0 < a) (hab : a < b)
    (h3 : a ^ 3 ≤ m3) (h3' : m3 ≤ b ^ 3) :
    0 < CAS13C02.positiveCubeRoot m3 ∧ CAS13C02.positiveCubeRoot m3 ∈ Icc a b := by
  have hm3 : 0 < m3 := lt_of_lt_of_le (pow_pos ha 3) h3
  have hr := CAS13C02.positiveCubeRoot_pos hm3
  have hr3 := CAS13C02.positiveCubeRoot_cube hm3.le
  have hb : 0 < b := ha.trans hab
  refine ⟨hr, ?_, ?_⟩
  · rw [← pow_le_pow_iff_left₀ ha.le hr.le (by norm_num : (3 : ℕ) ≠ 0), hr3]
    exact h3
  · rw [← pow_le_pow_iff_left₀ hr.le hb.le (by norm_num : (3 : ℕ) ≠ 0), hr3]
    exact h3'

theorem lower_boundary_sharp {a b m3 m4 : ℝ} (ha : 0 < a) (hab : a < b)
    (h3 : a ^ 3 ≤ m3) (h3' : m3 ≤ b ^ 3) (hbd : m4 = m3 ^ ((4 : ℝ) / 3)) (p : ℕ) :
    Measure.dirac (CAS13C02.positiveCubeRoot m3) ∈ NEFibre a b m3 m4 ∧
    SharpInterval (NEFibre a b m3 m4) p
      (CAS13C02.positiveCubeRoot m3 ^ p) (CAS13C02.positiveCubeRoot m3 ^ p) := by
  have hm3 : 0 < m3 := lt_of_lt_of_le (pow_pos ha 3) h3
  have hr3 := CAS13C02.positiveCubeRoot_cube hm3.le
  have hr4 := CAS13C02.positiveCubeRoot_fourth hm3.le
  obtain ⟨-, hrI⟩ := cube_root_mem ha hab h3 h3'
  have hmem : Measure.dirac (CAS13C02.positiveCubeRoot m3) ∈ NEFibre a b m3 m4 := by
    refine ⟨inferInstance, (ae_dirac_iff measurableSet_Icc).2 hrI, ?_, ?_⟩
    · simp only [moment, integral_dirac]
      exact hr3
    · simp only [moment, integral_dirac]
      rw [hr4, hbd]
  refine ⟨hmem, sharpInterval_of_const hmem fun μ hμ => ?_⟩
  rw [lower_boundary_dirac_collapse ha hab hμ hbd]
  simp only [moment, integral_dirac]

theorem upper_boundary_sharp {a b m3 m4 : ℝ} (ha : 0 < a) (hab : a < b)
    (h3 : a ^ 3 ≤ m3) (h3' : m3 ≤ b ^ 3) (hbd : m4 = chord a b m3) (p : ℕ) :
    twoDirac (CAS13C02.chordWeight a b m3) a b ∈ NEFibre a b m3 m4 ∧
    SharpInterval (NEFibre a b m3 m4) p
      ((1 - CAS13C02.chordWeight a b m3) * a ^ p + CAS13C02.chordWeight a b m3 * b ^ p)
      ((1 - CAS13C02.chordWeight a b m3) * a ^ p + CAS13C02.chordWeight a b m3 * b ^ p) := by
  have hD := cube_den_pos ha hab
  have hw0 : 0 ≤ CAS13C02.chordWeight a b m3 := div_nonneg (sub_nonneg.2 h3) hD.le
  have hw1 : CAS13C02.chordWeight a b m3 ≤ 1 := (div_le_one hD).2 (by linarith)
  have haI : a ∈ Icc a b := ⟨le_rfl, hab.le⟩
  have hbI : b ∈ Icc a b := ⟨hab.le, le_rfl⟩
  have hmem : twoDirac (CAS13C02.chordWeight a b m3) a b ∈ NEFibre a b m3 m4 := by
    refine ⟨twoDirac_probability hw0 hw1, twoDirac_supported haI hbI, ?_, ?_⟩
    · rw [moment_twoDirac 3 hw0 hw1]
      unfold CAS13C02.chordWeight
      field_simp
      ring
    · rw [moment_twoDirac 4 hw0 hw1, hbd]
      unfold CAS13C02.chordWeight chord
      field_simp
      ring
  refine ⟨hmem, sharpInterval_of_const hmem fun μ hμ => ?_⟩
  rw [upper_boundary_endpoint_collapse ha hab hμ hbd]
  exact moment_twoDirac p hw0 hw1

/-! ## Mixtures and the exact interior range -/

theorem integral_mix {θ : ℝ} (h0 : 0 ≤ θ) (h1 : θ ≤ 1) {μ ν : Measure ℝ} {f : ℝ → ℝ}
    (hμ : Integrable f μ) (hν : Integrable f ν) :
    ∫ x, f x ∂mix θ μ ν = θ * ∫ x, f x ∂μ + (1 - θ) * ∫ x, f x ∂ν := by
  rw [mix, integral_add_measure (hμ.smul_measure ENNReal.ofReal_ne_top)
    (hν.smul_measure ENNReal.ofReal_ne_top)]
  simp only [integral_smul_measure, ENNReal.toReal_ofReal h0,
    ENNReal.toReal_ofReal (sub_nonneg.mpr h1), smul_eq_mul]

theorem mix_mem {a b m3 m4 θ : ℝ} (h0 : 0 ≤ θ) (h1 : θ ≤ 1) {μ ν : Measure ℝ}
    (hμ : μ ∈ NEFibre a b m3 m4) (hν : ν ∈ NEFibre a b m3 m4) :
    mix θ μ ν ∈ NEFibre a b m3 m4 ∧
      ∀ p : ℕ, moment (mix θ μ ν) p = θ * moment μ p + (1 - θ) * moment ν p := by
  obtain ⟨hPμ, hsμ, h3μ, h4μ⟩ := hμ
  obtain ⟨hPν, hsν, h3ν, h4ν⟩ := hν
  haveI := hPμ
  haveI := hPν
  have hmom : ∀ p : ℕ, moment (mix θ μ ν) p = θ * moment μ p + (1 - θ) * moment ν p :=
    fun p => integral_mix h0 h1 (integrable_of_Icc hsμ (continuous_pow p))
      (integrable_of_Icc hsν (continuous_pow p))
  have hP : IsProbabilityMeasure (mix θ μ ν) := by
    constructor
    simp only [mix, Measure.add_apply, Measure.smul_apply, measure_univ, smul_eq_mul, mul_one]
    rw [← ENNReal.ofReal_add h0 (sub_nonneg.mpr h1)]
    simp
  have hs : ∀ᵐ x ∂mix θ μ ν, x ∈ Icc a b := by
    rw [mix, ae_add_measure_iff]
    exact ⟨Measure.ae_smul_measure hsμ _, Measure.ae_smul_measure hsν _⟩
  refine ⟨⟨hP, hs, ?_, ?_⟩, hmom⟩
  · rw [hmom 3, h3μ, h3ν]
    ring
  · rw [hmom 4, h4μ, h4ν]
    ring

theorem sharpInterval_of_extremes {a b m3 m4 : ℝ} {p : ℕ} {μL μU : Measure ℝ} {L U : ℝ}
    (hL : μL ∈ NEFibre a b m3 m4) (hU : μU ∈ NEFibre a b m3 m4)
    (hmL : moment μL p = L) (hmU : moment μU p = U)
    (hb : ∀ μ ∈ NEFibre a b m3 m4, L ≤ moment μ p ∧ moment μ p ≤ U) :
    SharpInterval (NEFibre a b m3 m4) p L U := by
  refine ⟨hb, ⟨μL, hL, hmL⟩, ⟨μU, hU, hmU⟩, ?_⟩
  ext m
  simp only [mem_image, mem_Icc]
  constructor
  · rintro ⟨μ, hμ, rfl⟩
    exact hb μ hμ
  · rintro ⟨h1, h2⟩
    rcases eq_or_lt_of_le (h1.trans h2) with hLU | hLU
    · exact ⟨μL, hL, by rw [hmL]; linarith⟩
    · have hne : U - L ≠ 0 := (sub_pos.2 hLU).ne'
      have hθ0 : 0 ≤ (U - m) / (U - L) := div_nonneg (by linarith) (by linarith)
      have hθ1 : (U - m) / (U - L) ≤ 1 := (div_le_one (sub_pos.2 hLU)).2 (by linarith)
      obtain ⟨hmem, hmom⟩ := mix_mem hθ0 hθ1 hL hU
      refine ⟨mix ((U - m) / (U - L)) μL μU, hmem, ?_⟩
      rw [hmom p, hmL, hmU]
      field_simp
      ring

/-! ## T3: same-prior energy-only interval for real p > 4 -/

theorem chordE_le {a b p x : ℝ} (ha : 0 < a) (hab : a < b) (hp : 4 < p) (hx : x ∈ Icc a b) :
    x ^ p ≤ ((b ^ 4 - x ^ 4) * a ^ p + (x ^ 4 - a ^ 4) * b ^ p) / (b ^ 4 - a ^ 4) := by
  have hb : 0 < b := ha.trans hab
  have hx0 : 0 ≤ x := ha.le.trans hx.1
  have hD := quartic_den_pos ha hab
  have hDne := hD.ne'
  have hα : 0 ≤ (b ^ 4 - x ^ 4) / (b ^ 4 - a ^ 4) :=
    div_nonneg (sub_nonneg.2 (pow_le_pow_left₀ hx0 hx.2 4)) hD.le
  have hβ : 0 ≤ (x ^ 4 - a ^ 4) / (b ^ 4 - a ^ 4) :=
    div_nonneg (sub_nonneg.2 (pow_le_pow_left₀ ha.le hx.1 4)) hD.le
  have hsum : (b ^ 4 - x ^ 4) / (b ^ 4 - a ^ 4) + (x ^ 4 - a ^ 4) / (b ^ 4 - a ^ 4) = 1 := by
    field_simp
    ring
  have hc := (convexOn_rpow (p := p / 4) (by linarith)).2
    (mem_Ici.2 (by positivity : (0 : ℝ) ≤ a ^ 4)) (mem_Ici.2 (by positivity : (0 : ℝ) ≤ b ^ 4))
    hα hβ hsum
  simp only [smul_eq_mul] at hc
  have hpt : (b ^ 4 - x ^ 4) / (b ^ 4 - a ^ 4) * a ^ 4 + (x ^ 4 - a ^ 4) / (b ^ 4 - a ^ 4) * b ^ 4
      = x ^ 4 := by
    field_simp
    ring
  rw [hpt, rpow_four_div hx0, rpow_four_div ha.le, rpow_four_div hb.le] at hc
  calc x ^ p ≤ _ := hc
    _ = _ := by ring

theorem chordE_lt {a b p x : ℝ} (ha : 0 < a) (hab : a < b) (hp : 4 < p) (hx : x ∈ Ioo a b) :
    x ^ p < ((b ^ 4 - x ^ 4) * a ^ p + (x ^ 4 - a ^ 4) * b ^ p) / (b ^ 4 - a ^ 4) := by
  have hb : 0 < b := ha.trans hab
  have hx0 : 0 ≤ x := ha.le.trans hx.1.le
  have hD := quartic_den_pos ha hab
  have hDne := hD.ne'
  have hα : 0 < (b ^ 4 - x ^ 4) / (b ^ 4 - a ^ 4) :=
    div_pos (sub_pos.2 (pow_lt_pow_left₀ hx.2 hx0 (by norm_num))) hD
  have hβ : 0 < (x ^ 4 - a ^ 4) / (b ^ 4 - a ^ 4) :=
    div_pos (sub_pos.2 (pow_lt_pow_left₀ hx.1 ha.le (by norm_num))) hD
  have hsum : (b ^ 4 - x ^ 4) / (b ^ 4 - a ^ 4) + (x ^ 4 - a ^ 4) / (b ^ 4 - a ^ 4) = 1 := by
    field_simp
    ring
  have hne : a ^ 4 ≠ b ^ 4 := (pow_lt_pow_left₀ hab ha.le (by norm_num)).ne
  have hc := (strictConvexOn_rpow (p := p / 4) (by linarith)).2
    (mem_Ici.2 (by positivity : (0 : ℝ) ≤ a ^ 4)) (mem_Ici.2 (by positivity : (0 : ℝ) ≤ b ^ 4))
    hne hα hβ hsum
  simp only [smul_eq_mul] at hc
  have hpt : (b ^ 4 - x ^ 4) / (b ^ 4 - a ^ 4) * a ^ 4 + (x ^ 4 - a ^ 4) / (b ^ 4 - a ^ 4) * b ^ 4
      = x ^ 4 := by
    field_simp
    ring
  rw [hpt, rpow_four_div hx0, rpow_four_div ha.le, rpow_four_div hb.le] at hc
  calc x ^ p < _ := hc
    _ = _ := by ring

theorem energy_only_bounds {a b m4 p : ℝ} (ha : 0 < a) (hab : a < b) (hp : 4 < p)
    {μ : Measure ℝ} (hμ : μ ∈ EFibre a b m4) :
    energyLower m4 p ≤ rmoment μ p ∧ rmoment μ p ≤ energyUpper a b m4 p := by
  obtain ⟨hP, hs, h4⟩ := hμ
  haveI := hP
  have hq : (0 : ℝ) ≤ p / 4 := by linarith
  have hip : Integrable (fun x : ℝ => x ^ p) μ :=
    integrable_of_Icc hs (Real.continuous_rpow_const (by linarith))
  have hi4 : Integrable (fun x : ℝ => x ^ 4) μ := integrable_of_Icc hs (continuous_pow 4)
  constructor
  · have hJ := (convexOn_rpow (p := p / 4) (by linarith)).map_integral_le (μ := μ)
      (f := fun x : ℝ => x ^ 4) (Real.continuous_rpow_const hq).continuousOn isClosed_Ici
      (ae_of_all μ fun x => mem_Ici.2 (by positivity)) hi4
      (integrable_of_Icc hs ((Real.continuous_rpow_const hq).comp (continuous_pow 4)))
    have e1 : (∫ x, x ^ 4 ∂μ) = m4 := h4
    rw [e1] at hJ
    have e2 : (∫ x, (x ^ 4) ^ (p / 4) ∂μ) = ∫ x, x ^ p ∂μ :=
      integral_congr_ae (hs.mono fun x hx => rpow_four_div (ha.le.trans hx.1) p)
    rw [e2] at hJ
    exact hJ
  · have hD := quartic_den_pos ha hab
    have hDne := hD.ne'
    have hpt : ∀ x : ℝ,
        ((b ^ 4 - x ^ 4) * a ^ p + (x ^ 4 - a ^ 4) * b ^ p) / (b ^ 4 - a ^ 4) =
          hermite ((b ^ 4 * a ^ p - a ^ 4 * b ^ p) / (b ^ 4 - a ^ 4)) 0
            ((b ^ p - a ^ p) / (b ^ 4 - a ^ 4)) x := by
      intro x
      unfold hermite
      field_simp
      ring
    have hmono := integral_mono_ae hip
      (integrable_hermite μ (c0 := (b ^ 4 * a ^ p - a ^ 4 * b ^ p) / (b ^ 4 - a ^ 4)) (c3 := 0)
        (c4 := (b ^ p - a ^ p) / (b ^ 4 - a ^ 4))
        (integrable_of_Icc hs (continuous_pow 3)) hi4)
      (hs.mono fun x hx => (chordE_le ha hab hp hx).trans_eq (hpt x))
    rw [integral_hermite μ (integrable_of_Icc hs (continuous_pow 3)) hi4 rfl h4] at hmono
    unfold rmoment energyUpper
    calc ∫ x, x ^ p ∂μ ≤ _ := hmono
      _ = _ := by
        field_simp
        ring

theorem energy_dirac_mem {a b m4 : ℝ} (ha : 0 < a) (hab : a < b)
    (h4 : a ^ 4 ≤ m4) (h4' : m4 ≤ b ^ 4) :
    Measure.dirac (m4 ^ ((1 : ℝ) / 4)) ∈ EFibre a b m4 := by
  have hm4 : 0 ≤ m4 := le_trans (by positivity) h4
  have hb : 0 < b := ha.trans hab
  have hlo : a ≤ m4 ^ ((1 : ℝ) / 4) := by
    have := Real.rpow_le_rpow (by positivity : (0 : ℝ) ≤ a ^ 4) h4 (by norm_num : (0 : ℝ) ≤ 1 / 4)
    rwa [rpow_four_div ha.le, Real.rpow_one] at this
  have hhi : m4 ^ ((1 : ℝ) / 4) ≤ b := by
    have := Real.rpow_le_rpow hm4 h4' (by norm_num : (0 : ℝ) ≤ 1 / 4)
    rwa [rpow_four_div hb.le, Real.rpow_one] at this
  refine ⟨inferInstance, (ae_dirac_iff measurableSet_Icc).2 ⟨hlo, hhi⟩, ?_⟩
  simp only [moment, integral_dirac]
  rw [← Real.rpow_natCast, ← Real.rpow_mul hm4]
  norm_num

theorem energy_only_attained {a b m4 p : ℝ} (ha : 0 < a) (hab : a < b) (hp : 4 < p)
    (h4 : a ^ 4 ≤ m4) (h4' : m4 ≤ b ^ 4) :
    Measure.dirac (m4 ^ ((1 : ℝ) / 4)) ∈ EFibre a b m4 ∧
    rmoment (Measure.dirac (m4 ^ ((1 : ℝ) / 4))) p = energyLower m4 p ∧
    twoDirac (energyWeight a b m4) a b ∈ EFibre a b m4 ∧
    rmoment (twoDirac (energyWeight a b m4) a b) p = energyUpper a b m4 p := by
  have hm4 : 0 ≤ m4 := le_trans (by positivity) h4
  have hD := quartic_den_pos ha hab
  have hDne := hD.ne'
  have hw0 : 0 ≤ energyWeight a b m4 := div_nonneg (sub_nonneg.2 h4) hD.le
  have hw1 : energyWeight a b m4 ≤ 1 := (div_le_one hD).2 (by linarith)
  have haI : a ∈ Icc a b := ⟨le_rfl, hab.le⟩
  have hbI : b ∈ Icc a b := ⟨hab.le, le_rfl⟩
  refine ⟨energy_dirac_mem ha hab h4 h4', ?_, ⟨twoDirac_probability hw0 hw1,
    twoDirac_supported haI hbI, ?_⟩, ?_⟩
  · simp only [rmoment, integral_dirac, energyLower]
    rw [← Real.rpow_mul hm4]
    congr 1
    ring
  · rw [moment_twoDirac 4 hw0 hw1]
    unfold energyWeight
    field_simp
    ring
  · unfold rmoment
    rw [integral_twoDirac (fun x : ℝ => x ^ p) hw0 hw1]
    unfold energyWeight energyUpper
    field_simp
    ring

theorem energy_fibre_nonempty_iff {a b : ℝ} (ha : 0 < a) (hab : a < b) (m4 : ℝ) :
    (EFibre a b m4).Nonempty ↔ a ^ 4 ≤ m4 ∧ m4 ≤ b ^ 4 := by
  constructor
  · rintro ⟨μ, hP, hs, h4⟩
    haveI := hP
    obtain ⟨c1, c2⟩ := moment_bounds ha.le hs 4
    rw [h4] at c1 c2
    exact ⟨c1, c2⟩
  · rintro ⟨h4, h4'⟩
    exact ⟨_, energy_dirac_mem ha hab h4 h4'⟩

/-! ## T4: same-prior fibre inclusion and nesting -/

theorem fibre_inclusion (a b m3 m4 : ℝ) : NEFibre a b m3 m4 ⊆ EFibre a b m4 :=
  fun _ hμ => ⟨hμ.1, hμ.2.1, hμ.2.2.2⟩

theorem endpoint_strict_nesting {a b m3 m4 p u d : ℝ} (h : CAS13C02.StrictInterior a b m3 m4)
    (hp : 4 < p) (hu : LowerNode a b m3 m4 u) (hd : UpperNode a b m3 m4 d) :
    energyLower m4 p < lowerEnd a m3 u p ∧ upperEnd b m3 d p < energyUpper a b m4 p := by
  obtain ⟨hrpos, _, har, hrb, _⟩ := CAS13C02.root_properties h
  have ha := h.a_pos
  have hab := h.a_lt_b
  have hb : 0 < b := ha.trans hab
  have hau : a < u := lt_trans har hu.1
  have hu0 : 0 < u := ha.trans hau
  have hd0 : 0 < d := ha.trans hd.1
  have hdb : d < b := lt_trans hd.2.1 hrb
  obtain ⟨hl0, hl1, _, _, hl4⟩ := CAS13C02.lower_weight_moments h hu
  obtain ⟨hu0w, hu1w, _, _, hu4⟩ := CAS13C02.upper_weight_moments h hd
  constructor
  · have hne : a ^ 4 ≠ u ^ 4 := (pow_lt_pow_left₀ hau ha.le (by norm_num)).ne
    have hc := (strictConvexOn_rpow (p := p / 4) (by linarith)).2
      (mem_Ici.2 (by positivity : (0 : ℝ) ≤ a ^ 4)) (mem_Ici.2 (by positivity : (0 : ℝ) ≤ u ^ 4))
      hne (sub_pos.2 hl1) hl0 (by ring)
    simp only [smul_eq_mul] at hc
    rw [hl4, rpow_four_div ha.le, rpow_four_div hu0.le] at hc
    exact hc
  · have hcd := chordE_lt ha hab hp ⟨hd.1, hdb⟩
    have hD := quartic_den_pos ha hab
    have hDne := hD.ne'
    have hstep : upperEnd b m3 d p <
        (1 - CAS13C02.upperWeight b m3 d) *
          (((b ^ 4 - d ^ 4) * a ^ p + (d ^ 4 - a ^ 4) * b ^ p) / (b ^ 4 - a ^ 4)) +
          CAS13C02.upperWeight b m3 d * b ^ p := by
      unfold upperEnd
      have := mul_lt_mul_of_pos_left hcd (sub_pos.2 hu1w)
      linarith
    refine hstep.trans_eq ?_
    unfold energyUpper
    rw [← hu4]
    field_simp
    ring

theorem interior_p56_bounds {a b m3 m4 u d : ℝ} (h : CAS13C02.StrictInterior a b m3 m4)
    (hu : LowerNode a b m3 m4 u) (hd : UpperNode a b m3 m4 d) (p : ℕ) (hp : p = 5 ∨ p = 6)
    {μ : Measure ℝ} (hμ : μ ∈ NEFibre a b m3 m4) :
    moment (twoDirac (CAS13C02.lowerWeight a m3 u) a u) p ≤ moment μ p ∧
    moment μ p ≤ moment (twoDirac (CAS13C02.upperWeight b m3 d) d b) p := by
  obtain ⟨u', d', hu', hd', hL5, hU5, hL6, hU6⟩ :=
    CAS13MeasureExtremizerBridge.strictInterior_measure_extremizers h
  have huu : u' = u := (CAS13C02.lower_node_existsUnique h).unique hu' hu
  have hdd : d' = d := (CAS13C02.upper_node_existsUnique h).unique hd' hd
  subst huu
  subst hdd
  rcases hp with rfl | rfl
  · obtain ⟨h1, h2, -⟩ := hL5 μ (admissible_of_mem hμ 5)
    obtain ⟨h3, h4, -⟩ := hU5 μ (admissible_of_mem hμ 5)
    exact ⟨by rw [h2]; exact h1, by rw [h4]; exact h3⟩
  · obtain ⟨h1, h2, -⟩ := hL6 μ (admissible_of_mem hμ 6)
    obtain ⟨h3, h4, -⟩ := hU6 μ (admissible_of_mem hμ 6)
    exact ⟨by rw [h2]; exact h1, by rw [h4]; exact h3⟩

/-! ## T5: composition with the C04 minimax -/

theorem minimax_degenerate {L : ℝ} (hL : 0 < L) : grstatEps L L = 0 ∧ grstatTau L L = L := by
  have h2 : L + L ≠ 0 := by positivity
  refine ⟨by simp [grstatEps], ?_⟩
  unfold grstatTau
  field_simp
  ring

theorem fibreMinimax_of_sharpInterval {F : Set (Measure ℝ)} {p : ℕ} {L U : ℝ}
    (hL : 0 < L) (hLU : L ≤ U) (hS : SharpInterval F p L U) : FibreMinimax F p L U := by
  obtain ⟨hb, ⟨μL, hμL, hmL⟩, ⟨μU, hμU, hmU⟩, -⟩ := hS
  obtain ⟨c1, c2, -, c4⟩ := grstat_cas13_minimax L U hL hLU
  refine ⟨fun μ hμ => c1 _ (hb μ hμ).1 (hb μ hμ).2, ⟨μL, hμL, by rw [hmL]; exact c2⟩,
    fun t => ?_⟩
  rcases le_max_iff.1 (c4 t) with h | h
  · exact ⟨μL, hμL, by rw [hmL]; exact h⟩
  · exact ⟨μU, hμU, by rw [hmU]; exact h⟩

theorem interior_sharp_minimax {a b m3 m4 u d : ℝ} (h : CAS13C02.StrictInterior a b m3 m4)
    (p : ℕ) (hp : p = 5 ∨ p = 6) (hu : LowerNode a b m3 m4 u) (hd : UpperNode a b m3 m4 d) :
    0 < lowerEnd a m3 u p ∧ lowerEnd a m3 u p ≤ upperEnd b m3 d p ∧
    twoDirac (CAS13C02.lowerWeight a m3 u) a u ∈ NEFibre a b m3 m4 ∧
    moment (twoDirac (CAS13C02.lowerWeight a m3 u) a u) p = lowerEnd a m3 u p ∧
    twoDirac (CAS13C02.upperWeight b m3 d) d b ∈ NEFibre a b m3 m4 ∧
    moment (twoDirac (CAS13C02.upperWeight b m3 d) d b) p = upperEnd b m3 d p ∧
    SharpInterval (NEFibre a b m3 m4) p (lowerEnd a m3 u p) (upperEnd b m3 d p) ∧
    FibreMinimax (NEFibre a b m3 m4) p (lowerEnd a m3 u p) (upperEnd b m3 d p) := by
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
  have hmL : moment (twoDirac (CAS13C02.lowerWeight a m3 u) a u) p = lowerEnd a m3 u p := by
    rw [moment_twoDirac p hl0.le hl1.le]
    simp only [lowerEnd, Real.rpow_natCast]
  have hmU : moment (twoDirac (CAS13C02.upperWeight b m3 d) d b) p = upperEnd b m3 d p := by
    rw [moment_twoDirac p hu0w.le hu1w.le]
    simp only [upperEnd, Real.rpow_natCast]
  have hb : ∀ μ ∈ NEFibre a b m3 m4,
      lowerEnd a m3 u p ≤ moment μ p ∧ moment μ p ≤ upperEnd b m3 d p := by
    intro μ hμ
    rw [← hmL, ← hmU]
    exact interior_p56_bounds h hu hd p hp hμ
  have hLU : lowerEnd a m3 u p ≤ upperEnd b m3 d p := by
    have := (hb _ hmemU).1
    rwa [hmU] at this
  have hpos : 0 < lowerEnd a m3 u p := by
    simp only [lowerEnd, Real.rpow_natCast]
    have h1 : 0 < (1 - CAS13C02.lowerWeight a m3 u) * a ^ p :=
      mul_pos (sub_pos.2 hl1) (pow_pos ha p)
    have h2 : 0 ≤ CAS13C02.lowerWeight a m3 u * u ^ p := mul_nonneg hl0.le (pow_pos hu0 p).le
    linarith
  have hS := sharpInterval_of_extremes hmemL hmemU hmL hmU hb
  exact ⟨hpos, hLU, hmemL, hmL, hmemU, hmU, hS, fibreMinimax_of_sharpInterval hpos hLU hS⟩

theorem interval_nesting_p56 {a b m3 m4 u d : ℝ} (h : CAS13C02.StrictInterior a b m3 m4)
    (p : ℕ) (hp : p = 5 ∨ p = 6) (hu : LowerNode a b m3 m4 u) (hd : UpperNode a b m3 m4 d) :
    energyLower m4 p < lowerEnd a m3 u p ∧ lowerEnd a m3 u p ≤ upperEnd b m3 d p ∧
    upperEnd b m3 d p < energyUpper a b m4 p ∧
    Icc (lowerEnd a m3 u p) (upperEnd b m3 d p) ⊆ Icc (energyLower m4 p) (energyUpper a b m4 p) ∧
    (fun μ => rmoment μ p) '' NEFibre a b m3 m4 ⊆ (fun μ => rmoment μ p) '' EFibre a b m4 := by
  have hp4 : (4 : ℝ) < p := by rcases hp with rfl | rfl <;> norm_num
  obtain ⟨hlo, hhi⟩ := endpoint_strict_nesting h hp4 hu hd
  obtain ⟨-, hLU, -⟩ := interior_sharp_minimax h p hp hu hd
  refine ⟨hlo, hLU, hhi, Icc_subset_Icc hlo.le hhi.le, ?_⟩
  rintro _ ⟨μ, hμ, rfl⟩
  exact ⟨μ, fibre_inclusion a b m3 m4 hμ, rfl⟩

theorem lower_boundary_minimax {a b m3 m4 : ℝ} (ha : 0 < a) (hab : a < b)
    (h3 : a ^ 3 ≤ m3) (h3' : m3 ≤ b ^ 3) (hbd : m4 = m3 ^ ((4 : ℝ) / 3)) (p : ℕ) :
    FibreMinimax (NEFibre a b m3 m4) p
      (CAS13C02.positiveCubeRoot m3 ^ p) (CAS13C02.positiveCubeRoot m3 ^ p) ∧
    grstatEps (CAS13C02.positiveCubeRoot m3 ^ p) (CAS13C02.positiveCubeRoot m3 ^ p) = 0 := by
  obtain ⟨hr, -⟩ := cube_root_mem ha hab h3 h3'
  have hpos : 0 < CAS13C02.positiveCubeRoot m3 ^ p := pow_pos hr p
  exact ⟨fibreMinimax_of_sharpInterval hpos le_rfl (lower_boundary_sharp ha hab h3 h3' hbd p).2,
    (minimax_degenerate hpos).1⟩

theorem chord_value_pos {a b m3 : ℝ} (ha : 0 < a) (hab : a < b)
    (h3 : a ^ 3 ≤ m3) (h3' : m3 ≤ b ^ 3) (p : ℕ) :
    0 < (1 - CAS13C02.chordWeight a b m3) * a ^ p + CAS13C02.chordWeight a b m3 * b ^ p := by
  have hD := cube_den_pos ha hab
  have hw0 : 0 ≤ CAS13C02.chordWeight a b m3 := div_nonneg (sub_nonneg.2 h3) hD.le
  have hw1 : CAS13C02.chordWeight a b m3 ≤ 1 := (div_le_one hD).2 (by linarith)
  have hab' : a ^ p ≤ b ^ p := pow_le_pow_left₀ ha.le hab.le p
  have hap : 0 < a ^ p := pow_pos ha p
  nlinarith [mul_le_mul_of_nonneg_left hab' hw0]

theorem upper_boundary_minimax {a b m3 m4 : ℝ} (ha : 0 < a) (hab : a < b)
    (h3 : a ^ 3 ≤ m3) (h3' : m3 ≤ b ^ 3) (hbd : m4 = chord a b m3) (p : ℕ) :
    FibreMinimax (NEFibre a b m3 m4) p
      ((1 - CAS13C02.chordWeight a b m3) * a ^ p + CAS13C02.chordWeight a b m3 * b ^ p)
      ((1 - CAS13C02.chordWeight a b m3) * a ^ p + CAS13C02.chordWeight a b m3 * b ^ p) ∧
    grstatEps ((1 - CAS13C02.chordWeight a b m3) * a ^ p + CAS13C02.chordWeight a b m3 * b ^ p)
      ((1 - CAS13C02.chordWeight a b m3) * a ^ p + CAS13C02.chordWeight a b m3 * b ^ p) = 0 := by
  have hpos := chord_value_pos ha hab h3 h3' p
  exact ⟨fibreMinimax_of_sharpInterval hpos le_rfl (upper_boundary_sharp ha hab h3 h3' hbd p).2,
    (minimax_degenerate hpos).1⟩

theorem region_exact {a b : ℝ} (ha : 0 < a) (hab : a < b) (m3 m4 : ℝ) :
    (NEFibre a b m3 m4).Nonempty ↔ ClosedRegion a b m3 m4 := by
  constructor
  · rintro ⟨μ, hμ⟩
    exact region_necessary ha hab hμ
  · intro hreg
    have h3 := hreg.1
    have h3' := hreg.2.1
    rcases region_strata ha hab hreg with hI | hL | hU
    · obtain ⟨u, hu, -⟩ := CAS13C02.lower_node_existsUnique hI
      obtain ⟨d, hd, -⟩ := CAS13C02.upper_node_existsUnique hI
      obtain ⟨-, -, hmem, -⟩ := interior_sharp_minimax hI 5 (Or.inl rfl) hu hd
      exact ⟨_, hmem⟩
    · exact ⟨_, (lower_boundary_sharp ha hab h3 h3' hL 0).1⟩
    · exact ⟨_, (upper_boundary_sharp ha hab h3 h3' hU 0).1⟩

theorem closed_region_sharp_minimax {a b m3 m4 : ℝ} (ha : 0 < a) (hab : a < b)
    (hreg : ClosedRegion a b m3 m4) (p : ℕ) (hp : p = 5 ∨ p = 6) :
    ∃ L U : ℝ, 0 < L ∧ L ≤ U ∧ SharpInterval (NEFibre a b m3 m4) p L U ∧
      FibreMinimax (NEFibre a b m3 m4) p L U ∧
      ((m4 = m3 ^ ((4 : ℝ) / 3) ∨ m4 = chord a b m3) →
        L = U ∧ grstatEps L U = 0 ∧ grstatTau L U = L) := by
  have h3 := hreg.1
  have h3' := hreg.2.1
  rcases region_strata ha hab hreg with hI | hL | hU
  · obtain ⟨u, hu, -⟩ := CAS13C02.lower_node_existsUnique hI
    obtain ⟨d, hd, -⟩ := CAS13C02.upper_node_existsUnique hI
    obtain ⟨hpos, hle, -, -, -, -, hS, hM⟩ := interior_sharp_minimax hI p hp hu hd
    refine ⟨_, _, hpos, hle, hS, hM, ?_⟩
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
    have hpos : 0 < CAS13C02.positiveCubeRoot m3 ^ p := pow_pos hr p
    have hS := (lower_boundary_sharp ha hab h3 h3' hL p).2
    exact ⟨_, _, hpos, le_rfl, hS, fibreMinimax_of_sharpInterval hpos le_rfl hS,
      fun _ => ⟨rfl, minimax_degenerate hpos⟩⟩
  · have hpos := chord_value_pos ha hab h3 h3' p
    have hS := (upper_boundary_sharp ha hab h3 h3' hU p).2
    exact ⟨_, _, hpos, le_rfl, hS, fibreMinimax_of_sharpInterval hpos le_rfl hS,
      fun _ => ⟨rfl, minimax_degenerate hpos⟩⟩

/-! ## Negative controls and non-vacuity witnesses -/

theorem node_ratio_zero_div_zero {a : ℝ} (ha : 0 < a) :
    (a ^ 4 - a ^ 4) / (a ^ 3 - a ^ 3) = 0 ∧ CAS13C02.secant a a = 4 * a / 3 ∧
    (a ^ 4 - a ^ 4) / (a ^ 3 - a ^ 3) ≠ CAS13C02.secant a a := by
  have h1 : (a ^ 4 - a ^ 4) / (a ^ 3 - a ^ 3) = 0 := by simp
  have h2 : CAS13C02.secant a a = 4 * a / 3 := by
    have hden : a ^ 2 + a * a + a ^ 2 ≠ 0 := by positivity
    unfold CAS13C02.secant
    field_simp
    ring
  refine ⟨h1, h2, ?_⟩
  rw [h1, h2]
  have : 0 < 4 * a / 3 := by positivity
  exact this.ne

theorem cross_prior_nesting_fails :
    twoDirac (1 / 2) 1 2 ∈ NEFibre 1 2 (9 / 2) (17 / 2) ∧
    moment (twoDirac (1 / 2) 1 2) 5 = 33 / 2 ∧
    energyUpper 1 2 (17 / 2) 5 = 33 / 2 ∧
    (EFibre 1 (7 / 4) (17 / 2)).Nonempty ∧
    energyUpper 1 (7 / 4) (17 / 2) 5 < 33 / 2 := by
  have hw0 : (0 : ℝ) ≤ 1 / 2 := by norm_num
  have hw1 : (1 / 2 : ℝ) ≤ 1 := by norm_num
  have h5 : (5 : ℝ) = ((5 : ℕ) : ℝ) := by norm_num
  refine ⟨⟨twoDirac_probability hw0 hw1,
      twoDirac_supported (⟨le_rfl, by norm_num⟩ : (1 : ℝ) ∈ Icc 1 2)
        (⟨by norm_num, le_rfl⟩ : (2 : ℝ) ∈ Icc 1 2), ?_, ?_⟩, ?_, ?_, ?_, ?_⟩
  · rw [moment_twoDirac 3 hw0 hw1]; norm_num
  · rw [moment_twoDirac 4 hw0 hw1]; norm_num
  · rw [moment_twoDirac 5 hw0 hw1]; norm_num
  · unfold energyUpper
    rw [h5, Real.rpow_natCast, Real.rpow_natCast]
    norm_num
  · exact (energy_fibre_nonempty_iff (by norm_num) (by norm_num) _).2 ⟨by norm_num, by norm_num⟩
  · unfold energyUpper
    rw [h5, Real.rpow_natCast, Real.rpow_natCast]
    norm_num

theorem lowerCurve_lt_iff {m3 m4 : ℝ} (hm3 : 0 < m3) (hm4 : 0 < m4) :
    m3 ^ ((4 : ℝ) / 3) < m4 ↔ m3 ^ 4 < m4 ^ 3 := by
  have hr := CAS13C02.positiveCubeRoot_pos hm3
  have hr3 := CAS13C02.positiveCubeRoot_cube hm3.le
  rw [← CAS13C02.positiveCubeRoot_fourth hm3.le,
    ← pow_lt_pow_iff_left₀ (by positivity) hm4.le (by norm_num : (3 : ℕ) ≠ 0)]
  have e : (CAS13C02.positiveCubeRoot m3 ^ 4) ^ 3 = (CAS13C02.positiveCubeRoot m3 ^ 3) ^ 4 := by
    ring
  rw [e, hr3]

theorem strictInterior_witness :
    CAS13C02.StrictInterior 1 2 (9 / 2) 8 ∧ (NEFibre 1 2 (9 / 2) 8).Nonempty := by
  have hI : CAS13C02.StrictInterior 1 2 (9 / 2) 8 := by
    refine ⟨by norm_num, by norm_num, by norm_num, by norm_num, ?_, by norm_num⟩
    rw [lowerCurve_lt_iff (by norm_num) (by norm_num)]
    norm_num
  refine ⟨hI, ?_⟩
  obtain ⟨u, hu, -⟩ := CAS13C02.lower_node_existsUnique hI
  obtain ⟨d, hd, -⟩ := CAS13C02.upper_node_existsUnique hI
  obtain ⟨-, -, hmem, -⟩ := interior_sharp_minimax hI 5 (Or.inl rfl) hu hd
  exact ⟨_, hmem⟩

theorem boundary_witness :
    ClosedRegion 1 2 (9 / 2) (17 / 2) ∧ (17 / 2 : ℝ) = chord 1 2 (9 / 2) ∧
    ¬ CAS13C02.StrictInterior 1 2 (9 / 2) (17 / 2) := by
  have hc : (17 / 2 : ℝ) = chord 1 2 (9 / 2) := by unfold chord; norm_num
  refine ⟨region_necessary (by norm_num) (by norm_num) cross_prior_nesting_fails.1, hc, ?_⟩
  intro h
  have := h.upper
  norm_num at this

end CAS13G13B
