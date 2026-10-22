import Mathlib
import MeasureExtremizerBridge
import PowerJet

/-!
# G13-D: bandpass C³, cubic Taylor certificate and sky/beam cubic error (TEFF Prop. B, B1-B4)

Sources: `supplements/TEFF_POSITIVE_BRIDGE.md` §3 (B1)-(B4), `cas/TEFF_INTERVAL_SPEC.md` §5,
`cas/contracts/CAS-13.json`.  Reused unchanged: G13-A `MeasureExtremizerBridge`
(`CAS13MeasureComposition.hermite/moment/twoDirac/...`) and PR #501 `PowerJet`
(`Cas13C01.*`, power-response jet).

Layers:
* finite jets at `y = 1` and a fencing Taylor step;
* the cubic (B3) and energy-only (B4) certificates for a general three-times
  differentiable response, integrated against an arbitrary probability mixture
  supported in `[1-s,1+s]`, with moment uncertainties, retained-span exactness,
  relative (`ψ_min > 0`) and signed-beam (absolute weight) corollaries and negative controls;
* the band-kernel layer: differentiation under the frequency integral three times for an
  integrable kernel on a compact positive-energy interval and the thermal factor
  `E²/(exp(E/(θy)-η₀)-ξ)`, giving `ψ ∈ C³`, and its connection to the conditional theorem.

No actual calibrated band kernel exists in the repository; it is the named external input
`EXT-G13D-K` (see `SOURCE_RECOVERY.md`). No scientific admission is claimed.
-/

open MeasureTheory Set
open CAS13MeasureComposition (hermite moment twoDirac)

noncomputable section

namespace G13D

/-! ## Coefficients and estimators -/

def c3 (d1 d2 : ℝ) : ℝ := d1 - d2 / 3
def c4 (d1 d2 : ℝ) : ℝ := d2 / 4 - d1 / 2
def c0 (v d1 d2 : ℝ) : ℝ := v - d1 / 2 + d2 / 12

/-- Number–energy estimator (B2). -/
def estimator (v d1 d2 m3 m4 : ℝ) : ℝ := c0 v d1 d2 + c3 d1 d2 * m3 + c4 d1 d2 * m4

def cE0 (v d1 : ℝ) : ℝ := v - d1 / 4
def cE4 (d1 : ℝ) : ℝ := d1 / 4

/-- Energy-only estimator (B4). -/
def energyEstimator (v d1 m4 : ℝ) : ℝ := cE0 v d1 + cE4 d1 * m4

/-! ## T0: jets of the Hermite polynomial at `y = 1` -/

theorem hermite_jets (v d1 d2 : ℝ) :
    hermite (c0 v d1 d2) (c3 d1 d2) (c4 d1 d2) 1 = v ∧
    3 * c3 d1 d2 * 1 ^ 2 + 4 * c4 d1 d2 * 1 ^ 3 = d1 ∧
    6 * c3 d1 d2 * 1 + 12 * c4 d1 d2 * 1 ^ 2 = d2 := by
  simp only [hermite, c0, c3, c4]
  refine ⟨by ring, by ring, by ring⟩

theorem hermite_hasDerivAt (a0 a3 a4 y : ℝ) :
    HasDerivAt (hermite a0 a3 a4) (3 * a3 * y ^ 2 + 4 * a4 * y ^ 3) y := by
  have h := ((hasDerivAt_const y a0).add ((hasDerivAt_pow 3 y).const_mul a3)).add
    ((hasDerivAt_pow 4 y).const_mul a4)
  refine h.congr_deriv ?_
  norm_num
  ring

theorem hermite1_hasDerivAt (a3 a4 y : ℝ) :
    HasDerivAt (fun z : ℝ => 3 * a3 * z ^ 2 + 4 * a4 * z ^ 3)
      (6 * a3 * y + 12 * a4 * y ^ 2) y := by
  have h := ((hasDerivAt_pow 2 y).const_mul (3 * a3)).add ((hasDerivAt_pow 3 y).const_mul (4 * a4))
  refine h.congr_deriv ?_
  norm_num
  ring

theorem hermite2_hasDerivAt (a3 a4 y : ℝ) :
    HasDerivAt (fun z : ℝ => 6 * a3 * z + 12 * a4 * z ^ 2) (6 * a3 + 24 * a4 * y) y := by
  have h := ((hasDerivAt_id' y).const_mul (6 * a3)).add ((hasDerivAt_pow 2 y).const_mul (12 * a4))
  refine h.congr_deriv ?_
  norm_num
  ring

/-! ## T1: one fencing (mean-value) Taylor step -/

theorem taylor_step_right {f f' : ℝ → ℝ} {c : ℝ} {n : ℕ} {y : ℝ} (hy : 1 ≤ y)
    (hf : ∀ z ∈ Icc 1 y, HasDerivAt f (f' z) z) (h1 : f 1 = 0)
    (hb : ∀ z ∈ Icc 1 y, |f' z| ≤ c * |z - 1| ^ n) :
    |f y| ≤ c / ((n : ℝ) + 1) * |y - 1| ^ (n + 1) := by
  have hB : ∀ x, HasDerivAt (fun x => c / ((n : ℝ) + 1) * (x - 1) ^ (n + 1))
      (c * (x - 1) ^ n) x := by
    intro x
    have h := (((hasDerivAt_id' x).sub_const 1).pow (n + 1)).const_mul (c / ((n : ℝ) + 1))
    refine h.congr_deriv ?_
    have hn : ((n : ℝ) + 1) ≠ 0 := by positivity
    rw [Nat.add_sub_cancel]
    push_cast
    field_simp
  have key := image_norm_le_of_norm_deriv_right_le_deriv_boundary
    (f := f) (f' := f') (a := 1) (b := y)
    (fun z hz => (hf z hz).continuousAt.continuousWithinAt)
    (fun z hz => (hf z (Ico_subset_Icc_self hz)).hasDerivWithinAt)
    (B := fun x => c / ((n : ℝ) + 1) * (x - 1) ^ (n + 1)) (B' := fun x => c * (x - 1) ^ n)
    (by simp [h1]) hB
    (fun z hz => by
      have := hb z (Ico_subset_Icc_self hz)
      rw [Real.norm_eq_abs]
      rwa [abs_of_nonneg (sub_nonneg.mpr hz.1)] at this)
  have := key (right_mem_Icc.mpr hy)
  rw [Real.norm_eq_abs] at this
  rwa [abs_of_nonneg (sub_nonneg.mpr hy)]

/-- Two-sided step with an explicit target coefficient/exponent (used for chaining). -/
theorem taylor_step' {f f' : ℝ → ℝ} {s c c' : ℝ} {n m : ℕ} (hs : 0 ≤ s)
    (hm : m = n + 1) (hc' : c / ((n : ℝ) + 1) = c')
    (hf : ∀ z ∈ Icc (1 - s) (1 + s), HasDerivAt f (f' z) z) (h1 : f 1 = 0)
    (hb : ∀ z ∈ Icc (1 - s) (1 + s), |f' z| ≤ c * |z - 1| ^ n) :
    ∀ y ∈ Icc (1 - s) (1 + s), |f y| ≤ c' * |y - 1| ^ m := by
  intro y hy
  subst hm hc'
  rcases le_total 1 y with h1y | hy1
  · exact taylor_step_right h1y
      (fun z hz => hf z ⟨by linarith [hz.1], le_trans hz.2 hy.2⟩) h1
      (fun z hz => hb z ⟨by linarith [hz.1], le_trans hz.2 hy.2⟩)
  · have hmem : ∀ t ∈ Icc 1 (2 - y), 2 - t ∈ Icc (1 - s) (1 + s) := fun t ht =>
      ⟨by linarith [ht.2, hy.1], by linarith [ht.1]⟩
    have hg := taylor_step_right (f := fun t => f (2 - t)) (f' := fun t => -f' (2 - t))
      (c := c) (n := n) (y := 2 - y) (by linarith)
      (fun t ht => by
        have h := (hf (2 - t) (hmem t ht)).comp t ((hasDerivAt_id' t).const_sub 2)
        exact h.congr_deriv (by ring))
      (by norm_num [h1])
      (fun t ht => by
        rw [abs_neg]
        have h := hb (2 - t) (hmem t ht)
        rwa [show (2 - t - 1 : ℝ) = -(t - 1) by ring, abs_neg] at h)
    simp only [show (2 - (2 - y) : ℝ) = y by ring,
      show (2 - y - 1 : ℝ) = -(y - 1) by ring, abs_neg] at hg
    exact hg

theorem taylor_step {f f' : ℝ → ℝ} {s c : ℝ} {n : ℕ} (hs : 0 ≤ s)
    (hf : ∀ z ∈ Icc (1 - s) (1 + s), HasDerivAt f (f' z) z) (h1 : f 1 = 0)
    (hb : ∀ z ∈ Icc (1 - s) (1 + s), |f' z| ≤ c * |z - 1| ^ n) :
    ∀ y ∈ Icc (1 - s) (1 + s), |f y| ≤ c / ((n : ℝ) + 1) * |y - 1| ^ (n + 1) :=
  taylor_step' hs rfl rfl hf h1 hb

/-! ## T2: pointwise cubic certificate -/

theorem cubic_pointwise {ψ ψ1 ψ2 ψ3 : ℝ → ℝ} {s0 M : ℝ} (hs0 : 0 ≤ s0)
    (hd : ∀ z ∈ Icc (1 - s0) (1 + s0),
      HasDerivAt ψ (ψ1 z) z ∧ HasDerivAt ψ1 (ψ2 z) z ∧ HasDerivAt ψ2 (ψ3 z) z)
    (hM : ∀ z ∈ Icc (1 - s0) (1 + s0),
      |ψ3 z - 6 * c3 (ψ1 1) (ψ2 1) - 24 * c4 (ψ1 1) (ψ2 1) * z| ≤ M) :
    ∀ y ∈ Icc (1 - s0) (1 + s0),
      |ψ y - hermite (c0 (ψ 1) (ψ1 1) (ψ2 1)) (c3 (ψ1 1) (ψ2 1)) (c4 (ψ1 1) (ψ2 1)) y|
        ≤ M / 6 * |y - 1| ^ 3 := by
  obtain ⟨j0, j1, j2⟩ := hermite_jets (ψ 1) (ψ1 1) (ψ2 1)
  set a0 := c0 (ψ 1) (ψ1 1) (ψ2 1) with ha0
  set a3 := c3 (ψ1 1) (ψ2 1) with ha3
  set a4 := c4 (ψ1 1) (ψ2 1) with ha4
  -- third-derivative step: |h''| ≤ M |z-1|
  have sA := taylor_step' (f := fun z => ψ2 z - (6 * a3 * z + 12 * a4 * z ^ 2))
    (f' := fun z => ψ3 z - (6 * a3 + 24 * a4 * z)) (c := M) (c' := M) (n := 0) (m := 1)
    hs0 rfl (by push_cast; ring)
    (fun z hz => (hd z hz).2.2.sub (hermite2_hasDerivAt a3 a4 z))
    (by show ψ2 1 - (6 * a3 * 1 + 12 * a4 * 1 ^ 2) = 0; linarith [j2])
    (fun z hz => by
      rw [pow_zero, mul_one, show ψ3 z - (6 * a3 + 24 * a4 * z) =
        ψ3 z - 6 * a3 - 24 * a4 * z by ring]
      exact hM z hz)
  -- second step: |h'| ≤ M/2 |z-1|^2
  have sB := taylor_step' (f := fun z => ψ1 z - (3 * a3 * z ^ 2 + 4 * a4 * z ^ 3))
    (f' := fun z => ψ2 z - (6 * a3 * z + 12 * a4 * z ^ 2)) (c := M) (c' := M / 2)
    (n := 1) (m := 2) hs0 rfl (by push_cast; ring)
    (fun z hz => (hd z hz).2.1.sub (hermite1_hasDerivAt a3 a4 z))
    (by show ψ1 1 - (3 * a3 * 1 ^ 2 + 4 * a4 * 1 ^ 3) = 0; linarith [j1])
    sA
  -- third step: |h| ≤ M/6 |z-1|^3
  have sC := taylor_step' (f := fun z => ψ z - hermite a0 a3 a4 z)
    (f' := fun z => ψ1 z - (3 * a3 * z ^ 2 + 4 * a4 * z ^ 3)) (c := M / 2) (c' := M / 6)
    (n := 2) (m := 3) hs0 rfl (by push_cast; ring)
    (fun z hz => (hd z hz).1.sub (hermite_hasDerivAt a0 a3 a4 z))
    (by show ψ 1 - hermite a0 a3 a4 1 = 0; linarith [j0])
    sB
  exact sC

/-! ## Integrability on the declared support -/

theorem integrable_of_continuousOn_support {f : ℝ → ℝ} {a b : ℝ} (π : Measure ℝ)
    [IsFiniteMeasure π] (hsupp : ∀ᵐ y ∂π, y ∈ Icc a b) (hf : ContinuousOn f (Icc a b)) :
    Integrable f π := by
  have h := hf.integrableOn_compact (μ := π) isCompact_Icc
  rwa [IntegrableOn, Measure.restrict_eq_self_of_ae_mem hsupp] at h

theorem integrable_pow_of_support {a b : ℝ} (π : Measure ℝ) [IsFiniteMeasure π]
    (hsupp : ∀ᵐ y ∂π, y ∈ Icc a b) (k : ℕ) : Integrable (fun x : ℝ => x ^ k) π :=
  integrable_of_continuousOn_support π hsupp (continuous_pow k).continuousOn

/-! ## T3: mixture integration (B3), moment uncertainty, retained span -/

theorem cubic_mixture {ψ ψ1 ψ2 ψ3 : ℝ → ℝ} {s s0 M : ℝ} (π : Measure ℝ)
    [IsProbabilityMeasure π]
    (hs : 0 ≤ s) (hss0 : s ≤ s0) (hsupp : ∀ᵐ y ∂π, y ∈ Icc (1 - s) (1 + s))
    (hd : ∀ z ∈ Icc (1 - s0) (1 + s0),
      HasDerivAt ψ (ψ1 z) z ∧ HasDerivAt ψ1 (ψ2 z) z ∧ HasDerivAt ψ2 (ψ3 z) z)
    (hM : ∀ z ∈ Icc (1 - s0) (1 + s0),
      |ψ3 z - 6 * c3 (ψ1 1) (ψ2 1) - 24 * c4 (ψ1 1) (ψ2 1) * z| ≤ M) :
    Integrable ψ π ∧
    |(∫ y, ψ y ∂π) - estimator (ψ 1) (ψ1 1) (ψ2 1) (moment π 3) (moment π 4)|
      ≤ s ^ 3 / 6 * M := by
  have hs0 : 0 ≤ s0 := le_trans hs hss0
  have hsub : Icc (1 - s) (1 + s) ⊆ Icc (1 - s0) (1 + s0) := fun z hz =>
    ⟨by linarith [hz.1], by linarith [hz.2]⟩
  have hcont : ContinuousOn ψ (Icc (1 - s) (1 + s)) := fun z hz =>
    (hd z (hsub hz)).1.continuousAt.continuousWithinAt
  have hint : Integrable ψ π := integrable_of_continuousOn_support π hsupp hcont
  refine ⟨hint, ?_⟩
  have h3 := integrable_pow_of_support π hsupp 3
  have h4 := integrable_pow_of_support π hsupp 4
  set a0 := c0 (ψ 1) (ψ1 1) (ψ2 1)
  set a3 := c3 (ψ1 1) (ψ2 1)
  set a4 := c4 (ψ1 1) (ψ2 1)
  have hq : (∫ y, hermite a0 a3 a4 y ∂π) = estimator (ψ 1) (ψ1 1) (ψ2 1) (moment π 3) (moment π 4) :=
    CAS13MeasureComposition.integral_hermite π h3 h4 rfl rfl
  have hqi : Integrable (hermite a0 a3 a4) π := CAS13MeasureComposition.integrable_hermite π h3 h4
  have hM0 : 0 ≤ M := le_trans (abs_nonneg _) (hM 1 ⟨by linarith, by linarith⟩)
  have hpt := cubic_pointwise hs0 hd hM
  rw [← hq, ← integral_sub hint hqi]
  have hbound : ∀ᵐ y ∂π, ‖ψ y - hermite a0 a3 a4 y‖ ≤ s ^ 3 / 6 * M := by
    refine hsupp.mono fun y hy => ?_
    rw [Real.norm_eq_abs]
    have hy1 : |y - 1| ≤ s := abs_le.mpr ⟨by linarith [hy.1], by linarith [hy.2]⟩
    have hp : |y - 1| ^ 3 ≤ s ^ 3 := pow_le_pow_left₀ (abs_nonneg _) hy1 3
    calc |ψ y - hermite a0 a3 a4 y| ≤ M / 6 * |y - 1| ^ 3 := hpt y (hsub hy)
      _ ≤ M / 6 * s ^ 3 := mul_le_mul_of_nonneg_left hp (by positivity)
      _ = s ^ 3 / 6 * M := by ring
  have := norm_integral_le_of_norm_le_const hbound
  rw [probReal_univ, mul_one, Real.norm_eq_abs] at this
  exact this

theorem cubic_mixture_uncertain {ψ ψ1 ψ2 ψ3 : ℝ → ℝ} {s s0 M m3 m4 d3 d4 : ℝ}
    (π : Measure ℝ) [IsProbabilityMeasure π]
    (hs : 0 ≤ s) (hss0 : s ≤ s0) (hsupp : ∀ᵐ y ∂π, y ∈ Icc (1 - s) (1 + s))
    (hd : ∀ z ∈ Icc (1 - s0) (1 + s0),
      HasDerivAt ψ (ψ1 z) z ∧ HasDerivAt ψ1 (ψ2 z) z ∧ HasDerivAt ψ2 (ψ3 z) z)
    (hM : ∀ z ∈ Icc (1 - s0) (1 + s0),
      |ψ3 z - 6 * c3 (ψ1 1) (ψ2 1) - 24 * c4 (ψ1 1) (ψ2 1) * z| ≤ M)
    (h3 : |moment π 3 - m3| ≤ d3) (h4 : |moment π 4 - m4| ≤ d4) :
    |(∫ y, ψ y ∂π) - estimator (ψ 1) (ψ1 1) (ψ2 1) m3 m4|
      ≤ s ^ 3 / 6 * M + |c3 (ψ1 1) (ψ2 1)| * d3 + |c4 (ψ1 1) (ψ2 1)| * d4 := by
  have hmain := (cubic_mixture π hs hss0 hsupp hd hM).2
  set O := ∫ y, ψ y ∂π
  set a3 := c3 (ψ1 1) (ψ2 1)
  set a4 := c4 (ψ1 1) (ψ2 1)
  have e : O - estimator (ψ 1) (ψ1 1) (ψ2 1) m3 m4 =
      (O - estimator (ψ 1) (ψ1 1) (ψ2 1) (moment π 3) (moment π 4)) +
        a3 * (moment π 3 - m3) + a4 * (moment π 4 - m4) := by
    simp only [estimator]; ring
  rw [e]
  calc |(O - estimator (ψ 1) (ψ1 1) (ψ2 1) (moment π 3) (moment π 4)) +
        a3 * (moment π 3 - m3) + a4 * (moment π 4 - m4)|
      ≤ |(O - estimator (ψ 1) (ψ1 1) (ψ2 1) (moment π 3) (moment π 4)) +
        a3 * (moment π 3 - m3)| + |a4 * (moment π 4 - m4)| := abs_add_le _ _
    _ ≤ |O - estimator (ψ 1) (ψ1 1) (ψ2 1) (moment π 3) (moment π 4)| +
        |a3 * (moment π 3 - m3)| + |a4 * (moment π 4 - m4)| := by
      gcongr; exact abs_add_le _ _
    _ ≤ s ^ 3 / 6 * M + |a3| * d3 + |a4| * d4 := by
      rw [abs_mul, abs_mul]
      gcongr

theorem retained_span (a0 a3 a4 : ℝ) (π : Measure ℝ) [IsProbabilityMeasure π]
    (h3 : Integrable (fun x : ℝ => x ^ 3) π) (h4 : Integrable (fun x : ℝ => x ^ 4) π) :
    c0 (hermite a0 a3 a4 1) (3 * a3 + 4 * a4) (6 * a3 + 12 * a4) = a0 ∧
    c3 (3 * a3 + 4 * a4) (6 * a3 + 12 * a4) = a3 ∧
    c4 (3 * a3 + 4 * a4) (6 * a3 + 12 * a4) = a4 ∧
    (∀ z : ℝ, 6 * a3 + 24 * a4 * z - 6 * c3 (3 * a3 + 4 * a4) (6 * a3 + 12 * a4)
        - 24 * c4 (3 * a3 + 4 * a4) (6 * a3 + 12 * a4) * z = 0) ∧
    (∫ y, hermite a0 a3 a4 y ∂π) =
      estimator (hermite a0 a3 a4 1) (3 * a3 + 4 * a4) (6 * a3 + 12 * a4)
        (moment π 3) (moment π 4) := by
  have e0 : c0 (hermite a0 a3 a4 1) (3 * a3 + 4 * a4) (6 * a3 + 12 * a4) = a0 := by
    simp only [c0, hermite]; ring
  have e3 : c3 (3 * a3 + 4 * a4) (6 * a3 + 12 * a4) = a3 := by simp only [c3]; ring
  have e4 : c4 (3 * a3 + 4 * a4) (6 * a3 + 12 * a4) = a4 := by simp only [c4]; ring
  refine ⟨e0, e3, e4, fun z => by rw [e3, e4]; ring, ?_⟩
  rw [CAS13MeasureComposition.integral_hermite π h3 h4 rfl rfl]
  simp only [estimator, e0, e3, e4]

/-! ## T4: energy-only quadratic certificate (B4), same prior and target -/

theorem quartic_hasDerivAt (a b y : ℝ) :
    HasDerivAt (fun z : ℝ => a + b * z ^ 4) (4 * b * y ^ 3) y := by
  have h := (hasDerivAt_const y a).add ((hasDerivAt_pow 4 y).const_mul b)
  refine h.congr_deriv ?_
  norm_num
  ring

theorem quartic1_hasDerivAt (b y : ℝ) :
    HasDerivAt (fun z : ℝ => 4 * b * z ^ 3) (12 * b * y ^ 2) y := by
  have h := (hasDerivAt_pow 3 y).const_mul (4 * b)
  refine h.congr_deriv ?_
  norm_num
  ring

theorem energy_pointwise {ψ ψ1 ψ2 : ℝ → ℝ} {s0 M2 : ℝ} (hs0 : 0 ≤ s0)
    (hd : ∀ z ∈ Icc (1 - s0) (1 + s0), HasDerivAt ψ (ψ1 z) z ∧ HasDerivAt ψ1 (ψ2 z) z)
    (hM : ∀ z ∈ Icc (1 - s0) (1 + s0), |ψ2 z - 3 * ψ1 1 * z ^ 2| ≤ M2) :
    ∀ y ∈ Icc (1 - s0) (1 + s0),
      |ψ y - (cE0 (ψ 1) (ψ1 1) + cE4 (ψ1 1) * y ^ 4)| ≤ M2 / 2 * |y - 1| ^ 2 := by
  set a := cE0 (ψ 1) (ψ1 1)
  set b := cE4 (ψ1 1)
  have sA := taylor_step' (f := fun z => ψ1 z - 4 * b * z ^ 3)
    (f' := fun z => ψ2 z - 12 * b * z ^ 2) (c := M2) (c' := M2) (n := 0) (m := 1)
    hs0 rfl (by push_cast; ring)
    (fun z hz => (hd z hz).2.sub (quartic1_hasDerivAt b z))
    (by simp only [b, cE4]; ring)
    (fun z hz => by
      rw [pow_zero, mul_one, show ψ2 z - 12 * b * z ^ 2 = ψ2 z - 3 * ψ1 1 * z ^ 2 by
        simp only [b, cE4]; ring]
      exact hM z hz)
  have sB := taylor_step' (f := fun z => ψ z - (a + b * z ^ 4))
    (f' := fun z => ψ1 z - 4 * b * z ^ 3) (c := M2) (c' := M2 / 2) (n := 1) (m := 2)
    hs0 rfl (by push_cast; ring)
    (fun z hz => (hd z hz).1.sub (quartic_hasDerivAt a b z))
    (by simp only [a, b, cE0, cE4]; ring)
    sA
  exact sB

theorem energy_mixture {ψ ψ1 ψ2 : ℝ → ℝ} {s s0 M2 : ℝ} (π : Measure ℝ)
    [IsProbabilityMeasure π]
    (hs : 0 ≤ s) (hss0 : s ≤ s0) (hsupp : ∀ᵐ y ∂π, y ∈ Icc (1 - s) (1 + s))
    (hd : ∀ z ∈ Icc (1 - s0) (1 + s0), HasDerivAt ψ (ψ1 z) z ∧ HasDerivAt ψ1 (ψ2 z) z)
    (hM : ∀ z ∈ Icc (1 - s0) (1 + s0), |ψ2 z - 3 * ψ1 1 * z ^ 2| ≤ M2) :
    Integrable ψ π ∧
    |(∫ y, ψ y ∂π) - energyEstimator (ψ 1) (ψ1 1) (moment π 4)| ≤ s ^ 2 / 2 * M2 := by
  have hs0 : 0 ≤ s0 := le_trans hs hss0
  have hsub : Icc (1 - s) (1 + s) ⊆ Icc (1 - s0) (1 + s0) := fun z hz =>
    ⟨by linarith [hz.1], by linarith [hz.2]⟩
  have hcont : ContinuousOn ψ (Icc (1 - s) (1 + s)) := fun z hz =>
    (hd z (hsub hz)).1.continuousAt.continuousWithinAt
  have hint : Integrable ψ π := integrable_of_continuousOn_support π hsupp hcont
  refine ⟨hint, ?_⟩
  have h4 := integrable_pow_of_support π hsupp 4
  set a := cE0 (ψ 1) (ψ1 1)
  set b := cE4 (ψ1 1)
  have hqi : Integrable (fun y : ℝ => a + b * y ^ 4) π := (integrable_const a).add (h4.const_mul b)
  have hq : (∫ y, a + b * y ^ 4 ∂π) = energyEstimator (ψ 1) (ψ1 1) (moment π 4) := by
    rw [integral_add (integrable_const a) (h4.const_mul b), integral_const_mul]
    simp [energyEstimator, a, b, moment]
  have hM0 : 0 ≤ M2 := le_trans (abs_nonneg _) (hM 1 ⟨by linarith, by linarith⟩)
  have hpt := energy_pointwise hs0 hd hM
  rw [← hq, ← integral_sub hint hqi]
  have hbound : ∀ᵐ y ∂π, ‖ψ y - (a + b * y ^ 4)‖ ≤ s ^ 2 / 2 * M2 := by
    refine hsupp.mono fun y hy => ?_
    rw [Real.norm_eq_abs]
    have hy1 : |y - 1| ≤ s := abs_le.mpr ⟨by linarith [hy.1], by linarith [hy.2]⟩
    have hp : |y - 1| ^ 2 ≤ s ^ 2 := pow_le_pow_left₀ (abs_nonneg _) hy1 2
    calc |ψ y - (a + b * y ^ 4)| ≤ M2 / 2 * |y - 1| ^ 2 := hpt y (hsub hy)
      _ ≤ M2 / 2 * s ^ 2 := mul_le_mul_of_nonneg_left hp (by positivity)
      _ = s ^ 2 / 2 * M2 := by ring
  have := norm_integral_le_of_norm_le_const hbound
  rw [probReal_univ, mul_one, Real.norm_eq_abs] at this
  exact this

/-- T4b (negative control, MOM-PRIOR): same two-point prior, same target `y³`. The
number–energy estimator is exact while the energy-only error is exactly quadratic. -/
theorem same_prior_gap {s : ℝ} (hs : 0 < s) (hs1 : s < 1) :
    IsProbabilityMeasure (twoDirac (1/2) (1 - s) (1 + s)) ∧
    (∀ᵐ y ∂twoDirac (1/2) (1 - s) (1 + s), y ∈ Icc (1 - s) (1 + s)) ∧
    (∫ y, y ^ 3 ∂twoDirac (1/2) (1 - s) (1 + s)) =
      estimator 1 3 6 (moment (twoDirac (1/2) (1 - s) (1 + s)) 3)
        (moment (twoDirac (1/2) (1 - s) (1 + s)) 4) ∧
    (∫ y, y ^ 3 ∂twoDirac (1/2) (1 - s) (1 + s)) -
      energyEstimator 1 3 (moment (twoDirac (1/2) (1 - s) (1 + s)) 4) =
        -(3/2 * s ^ 2 + 3/4 * s ^ 4) ∧
    -(3/2 * s ^ 2 + 3/4 * s ^ 4) ≠ 0 := by
  have _hs1 := hs1
  have e3 : moment (twoDirac (1/2) (1 - s) (1 + s)) 3 =
      (1 - 1/2) * (1 - s) ^ 3 + 1/2 * (1 + s) ^ 3 :=
    CAS13MeasureComposition.moment_twoDirac 3 (by norm_num) (by norm_num)
  have e4 : moment (twoDirac (1/2) (1 - s) (1 + s)) 4 =
      (1 - 1/2) * (1 - s) ^ 4 + 1/2 * (1 + s) ^ 4 :=
    CAS13MeasureComposition.moment_twoDirac 4 (by norm_num) (by norm_num)
  have i3 : (∫ y, y ^ 3 ∂twoDirac (1/2) (1 - s) (1 + s)) =
      (1 - 1/2) * (1 - s) ^ 3 + 1/2 * (1 + s) ^ 3 := e3
  refine ⟨CAS13MeasureComposition.twoDirac_probability (by norm_num) (by norm_num),
    CAS13MeasureComposition.twoDirac_supported ⟨le_refl _, by linarith⟩ ⟨by linarith, le_refl _⟩,
    ?_, ?_, ?_⟩
  · rw [i3, e3, e4]; simp only [estimator, c0, c3, c4]; ring
  · rw [i3, e4]; simp only [energyEstimator, cE0, cE4]; ring
  · have : 0 < 3/2 * s ^ 2 + 3/4 * s ^ 4 := by positivity
    intro h; linarith

/-! ## T5: relative bound when `ψ_min > 0` on the support -/

theorem relative_bound {ψ : ℝ → ℝ} {ψmin Ohat B : ℝ} (π : Measure ℝ) [IsProbabilityMeasure π]
    (hint : Integrable ψ π) (hmin : ∀ᵐ y ∂π, ψmin ≤ ψ y) (hpos : 0 < ψmin)
    (herr : |(∫ y, ψ y ∂π) - Ohat| ≤ B) :
    ψmin ≤ ∫ y, ψ y ∂π ∧ |(∫ y, ψ y ∂π) - Ohat| / |∫ y, ψ y ∂π| ≤ B / ψmin := by
  have hO : ψmin ≤ ∫ y, ψ y ∂π := by
    have := integral_mono_ae (integrable_const ψmin) hint hmin
    simpa using this
  refine ⟨hO, ?_⟩
  have hOpos : 0 < |∫ y, ψ y ∂π| := by
    rw [abs_of_pos (lt_of_lt_of_le hpos hO)]; exact lt_of_lt_of_le hpos hO
  have hB : 0 ≤ B := le_trans (abs_nonneg _) herr
  rw [div_le_div_iff₀ hOpos hpos]
  have habs : ψmin ≤ |∫ y, ψ y ∂π| := le_trans hO (le_abs_self _)
  calc |(∫ y, ψ y ∂π) - Ohat| * ψmin ≤ B * ψmin := mul_le_mul_of_nonneg_right herr hpos.le
    _ ≤ B * |∫ y, ψ y ∂π| := mul_le_mul_of_nonneg_left habs hB

theorem relative_cubic {ψ ψ1 ψ2 ψ3 : ℝ → ℝ} {s s0 M ψmin : ℝ} (π : Measure ℝ)
    [IsProbabilityMeasure π]
    (hs : 0 ≤ s) (hss0 : s ≤ s0) (hsupp : ∀ᵐ y ∂π, y ∈ Icc (1 - s) (1 + s))
    (hd : ∀ z ∈ Icc (1 - s0) (1 + s0),
      HasDerivAt ψ (ψ1 z) z ∧ HasDerivAt ψ1 (ψ2 z) z ∧ HasDerivAt ψ2 (ψ3 z) z)
    (hM : ∀ z ∈ Icc (1 - s0) (1 + s0),
      |ψ3 z - 6 * c3 (ψ1 1) (ψ2 1) - 24 * c4 (ψ1 1) (ψ2 1) * z| ≤ M)
    (hmin : ∀ y ∈ Icc (1 - s) (1 + s), ψmin ≤ ψ y) (hpos : 0 < ψmin) :
    |(∫ y, ψ y ∂π) - estimator (ψ 1) (ψ1 1) (ψ2 1) (moment π 3) (moment π 4)| /
      |∫ y, ψ y ∂π| ≤ s ^ 3 / 6 * M / ψmin := by
  obtain ⟨hint, herr⟩ := cubic_mixture π hs hss0 hsupp hd hM
  exact (relative_bound π hint (hsupp.mono fun y hy => hmin y hy) hpos herr).2

/-! ## T6: signed beam / angular weights: absolute-weight integration, no division -/

theorem beam_abs {α : Type*} [MeasurableSpace α] (σ : Measure α) (b O Oh ε : α → ℝ)
    (hO : Integrable (fun ω => b ω * O ω) σ) (hOh : Integrable (fun ω => b ω * Oh ω) σ)
    (hε : Integrable (fun ω => |b ω| * ε ω) σ) (hray : ∀ᵐ ω ∂σ, |O ω - Oh ω| ≤ ε ω) :
    |(∫ ω, b ω * O ω ∂σ) - ∫ ω, b ω * Oh ω ∂σ| ≤ ∫ ω, |b ω| * ε ω ∂σ := by
  rw [← integral_sub hO hOh]
  calc |∫ ω, b ω * O ω - b ω * Oh ω ∂σ| = ‖∫ ω, b ω * O ω - b ω * Oh ω ∂σ‖ :=
        (Real.norm_eq_abs _).symm
    _ ≤ ∫ ω, ‖b ω * O ω - b ω * Oh ω‖ ∂σ := norm_integral_le_integral_norm _
    _ ≤ ∫ ω, |b ω| * ε ω ∂σ := by
      refine integral_mono_ae (hO.sub hOh).norm hε (hray.mono fun ω h => ?_)
      show ‖b ω * O ω - b ω * Oh ω‖ ≤ |b ω| * ε ω
      rw [Real.norm_eq_abs, ← mul_sub, abs_mul]
      exact mul_le_mul_of_nonneg_left h (abs_nonneg _)

theorem beam_uniform {α : Type*} [MeasurableSpace α] (σ : Measure α) (b O Oh : α → ℝ) (ε : ℝ)
    (hO : Integrable (fun ω => b ω * O ω) σ) (hOh : Integrable (fun ω => b ω * Oh ω) σ)
    (hb : Integrable b σ) (hray : ∀ᵐ ω ∂σ, |O ω - Oh ω| ≤ ε) :
    |(∫ ω, b ω * O ω ∂σ) - ∫ ω, b ω * Oh ω ∂σ| ≤ ε * ∫ ω, |b ω| ∂σ := by
  have h := beam_abs σ b O Oh (fun _ => ε) hO hOh (hb.abs.mul_const ε) hray
  rw [integral_mul_const] at h
  linarith [h]

/-- T6b (negative control): for a signed angular weight the true sky observable can vanish
while the absolute error does not, so no relative (division) bound exists. -/
theorem signed_mode_no_relative {δ : ℝ} (hδ : δ ≠ 0) :
    (∫ ω, ω * 1 ∂twoDirac (1/2) (-1) 1) = 0 ∧
    (∫ ω, ω * (1 + δ * ω) ∂twoDirac (1/2) (-1) 1) = δ ∧
    (∀ᵐ ω ∂twoDirac (1/2) (-1) 1, |1 - (1 + δ * ω)| ≤ |δ|) ∧
    ¬ ∃ c : ℝ, |(∫ ω, ω * 1 ∂twoDirac (1/2) (-1) 1) -
        ∫ ω, ω * (1 + δ * ω) ∂twoDirac (1/2) (-1) 1|
        ≤ c * |∫ ω, ω * 1 ∂twoDirac (1/2) (-1) 1| := by
  have e1 : (∫ ω, ω * 1 ∂twoDirac (1/2) (-1) 1) = (1 - 1/2) * ((-1) * 1) + 1/2 * (1 * 1) :=
    CAS13MeasureComposition.integral_twoDirac (fun ω : ℝ => ω * 1) (by norm_num) (by norm_num)
  have e2 : (∫ ω, ω * (1 + δ * ω) ∂twoDirac (1/2) (-1) 1) =
      (1 - 1/2) * ((-1) * (1 + δ * (-1))) + 1/2 * (1 * (1 + δ * 1)) :=
    CAS13MeasureComposition.integral_twoDirac (fun ω : ℝ => ω * (1 + δ * ω))
      (by norm_num) (by norm_num)
  have e1' : (∫ ω, ω * 1 ∂twoDirac (1/2) (-1) 1) = 0 := by rw [e1]; norm_num
  have e2' : (∫ ω, ω * (1 + δ * ω) ∂twoDirac (1/2) (-1) 1) = δ := by rw [e2]; ring
  refine ⟨e1', e2', ?_, ?_⟩
  · refine (CAS13MeasureComposition.twoDirac_supported (a := -1) (b := 1)
      ⟨le_refl _, by norm_num⟩ ⟨by norm_num, le_refl _⟩).mono fun ω hω => ?_
    rw [show (1 - (1 + δ * ω) : ℝ) = -(δ * ω) by ring, abs_neg, abs_mul]
    have hω1 : |ω| ≤ 1 := abs_le.mpr ⟨hω.1, hω.2⟩
    calc |δ| * |ω| ≤ |δ| * 1 := mul_le_mul_of_nonneg_left hω1 (abs_nonneg δ)
      _ = |δ| := mul_one _
  · rintro ⟨c, hc⟩
    rw [e1', e2', abs_zero, mul_zero, zero_sub, abs_neg] at hc
    exact hδ (abs_nonpos_iff.mp hc)

/-! ## T7: extra radial data do not identify an unmeasured angular mode -/

theorem radial_data_do_not_fix_dipole (ψ : ℝ → ℝ) {yN yS : ℝ} (hne : ψ yN ≠ ψ yS) :
    (Measure.dirac yN + Measure.dirac yS : Measure ℝ) = Measure.dirac yS + Measure.dirac yN ∧
    (∀ g : ℝ → ℝ, (∫ y, g y ∂(Measure.dirac yN + Measure.dirac yS)) =
        ∫ y, g y ∂(Measure.dirac yS + Measure.dirac yN)) ∧
    (∫ y, ψ y ∂Measure.dirac yN) - (∫ y, ψ y ∂Measure.dirac yS) ≠
      (∫ y, ψ y ∂Measure.dirac yS) - (∫ y, ψ y ∂Measure.dirac yN) := by
  have hc : (Measure.dirac yN + Measure.dirac yS : Measure ℝ) =
      Measure.dirac yS + Measure.dirac yN := add_comm _ _
  refine ⟨hc, fun g => by rw [hc], ?_⟩
  rw [integral_dirac, integral_dirac]
  intro h
  apply hne
  linarith

theorem radial_witness : (fun y : ℝ => y) (1/2) ≠ (fun y : ℝ => y) (3/2) := by norm_num

/-! ## T8: band-kernel layer — differentiation under the frequency integral -/

def bandIntegral (K : ℝ → ℝ) (E1 E2 : ℝ) (G : ℝ × ℝ → ℝ) (y : ℝ) : ℝ :=
  ∫ E in Icc E1 E2, K E * G (y, E)

/-- Partial derivative in the temperature-ratio variable `y`. -/
def dY (G : ℝ × ℝ → ℝ) : ℝ × ℝ → ℝ := fun p => fderiv ℝ G p (1, 0)

theorem dY_contDiffOn {G : ℝ × ℝ → ℝ} {Ω : Set (ℝ × ℝ)} {m n : WithTop ℕ∞} (hΩ : IsOpen Ω)
    (hG : ContDiffOn ℝ n G Ω) (hmn : m + 1 ≤ n) : ContDiffOn ℝ m (dY G) Ω :=
  (hG.fderiv_of_isOpen hΩ hmn).clm_apply contDiffOn_const

theorem hasDerivAt_slice {G : ℝ × ℝ → ℝ} {Ω : Set (ℝ × ℝ)} (hΩ : IsOpen Ω)
    (hG : ContDiffOn ℝ 1 G Ω) {x E : ℝ} (hp : (x, E) ∈ Ω) :
    HasDerivAt (fun t => G (t, E)) (dY G (x, E)) x := by
  have hdiff : DifferentiableAt ℝ G (x, E) :=
    (hG.differentiableOn one_ne_zero (x, E) hp).differentiableAt (hΩ.mem_nhds hp)
  have hpath : HasDerivAt (fun t : ℝ => (t, E)) ((1 : ℝ), (0 : ℝ)) x :=
    (hasDerivAt_id' x).prodMk (hasDerivAt_const x E)
  exact hdiff.hasFDerivAt.comp_hasDerivAt x hpath

theorem bandIntegral_hasDerivAt {K : ℝ → ℝ} {E1 E2 A B y : ℝ} {G : ℝ × ℝ → ℝ}
    {Ω : Set (ℝ × ℝ)} (hK : IntegrableOn K (Icc E1 E2)) (hΩ : IsOpen Ω)
    (hG : ContDiffOn ℝ 1 G Ω) (hsub : Icc A B ×ˢ Icc E1 E2 ⊆ Ω) (hy : y ∈ Ioo A B) :
    HasDerivAt (bandIntegral K E1 E2 G) (bandIntegral K E1 E2 (dY G) y) y := by
  have hScpt : IsCompact (Icc A B ×ˢ Icc E1 E2) := isCompact_Icc.prod isCompact_Icc
  have hGc : ContinuousOn G (Icc A B ×ˢ Icc E1 E2) := hG.continuousOn.mono hsub
  have hdY : ContDiffOn ℝ 0 (dY G) Ω := dY_contDiffOn hΩ hG (by norm_num)
  have hdYc : ContinuousOn (dY G) (Icc A B ×ˢ Icc E1 E2) := hdY.continuousOn.mono hsub
  obtain ⟨M, hM⟩ := hScpt.exists_bound_of_continuousOn hdYc
  have slice : ∀ {H : ℝ × ℝ → ℝ}, ContinuousOn H (Icc A B ×ˢ Icc E1 E2) →
      ∀ x ∈ Icc A B, ContinuousOn (fun E => H (x, E)) (Icc E1 E2) := by
    intro H hH x hx
    exact hH.comp (Continuous.continuousOn (by fun_prop)) (fun E hE => ⟨hx, hE⟩)
  have hIoo : Ioo A B ∈ nhds y := isOpen_Ioo.mem_nhds hy
  have hmeasK : AEStronglyMeasurable K (volume.restrict (Icc E1 E2)) := hK.aestronglyMeasurable
  have key := hasDerivAt_integral_of_dominated_loc_of_deriv_le (μ := volume.restrict (Icc E1 E2))
    (F := fun x E => K E * G (x, E)) (F' := fun x E => K E * dY G (x, E)) (x₀ := y)
    (bound := fun E => ‖K E‖ * M) hIoo
    (Filter.eventually_of_mem hIoo fun x hx => hmeasK.mul
      ((slice hGc x (Ioo_subset_Icc_self hx)).aestronglyMeasurable measurableSet_Icc))
    (hK.mul_continuousOn (slice hGc y (Ioo_subset_Icc_self hy)) isCompact_Icc)
    (hmeasK.mul ((slice hdYc y (Ioo_subset_Icc_self hy)).aestronglyMeasurable measurableSet_Icc))
    ((ae_restrict_mem measurableSet_Icc).mono fun E hE x hx => by
      rw [norm_mul]
      exact mul_le_mul_of_nonneg_left (hM (x, E) ⟨Ioo_subset_Icc_self hx, hE⟩) (norm_nonneg _))
    (hK.norm.mul_const M)
    ((ae_restrict_mem measurableSet_Icc).mono fun E hE x hx =>
      (hasDerivAt_slice hΩ hG (hsub ⟨Ioo_subset_Icc_self hx, hE⟩)).const_mul (K E))
  exact key.2

theorem contDiffOn_three_of_chain {f f1 f2 f3 : ℝ → ℝ} {U : Set ℝ} (hU : IsOpen U)
    (h : ∀ y ∈ U, HasDerivAt f (f1 y) y ∧ HasDerivAt f1 (f2 y) y ∧ HasDerivAt f2 (f3 y) y)
    (hc : ContinuousOn f3 U) : ContDiffOn ℝ 3 f U := by
  have nω : ∀ k : ℕ, ¬ (((k : ℕ) : WithTop ℕ∞) = ⊤) := fun k => WithTop.natCast_ne_top k
  have d2 : ContDiffOn ℝ 1 f2 U := by
    have e : (1 : WithTop ℕ∞) = ((0 : ℕ) : WithTop ℕ∞) + 1 := by norm_num
    rw [e, contDiffOn_succ_iff_deriv_of_isOpen hU]
    refine ⟨fun y hy => (h y hy).2.2.differentiableAt.differentiableWithinAt,
      fun hh => absurd hh (nω 0), ?_⟩
    have h3 : ContDiffOn ℝ ((0 : ℕ) : WithTop ℕ∞) f3 U := by
      rw [Nat.cast_zero, contDiffOn_zero]; exact hc
    exact h3.congr fun y hy => (h y hy).2.2.deriv
  have d1 : ContDiffOn ℝ 2 f1 U := by
    have e : (2 : WithTop ℕ∞) = ((1 : ℕ) : WithTop ℕ∞) + 1 := by norm_num
    rw [e, contDiffOn_succ_iff_deriv_of_isOpen hU]
    refine ⟨fun y hy => (h y hy).2.1.differentiableAt.differentiableWithinAt,
      fun hh => absurd hh (nω 1), ?_⟩
    exact (by simpa using d2 : ContDiffOn ℝ ((1 : ℕ) : WithTop ℕ∞) f2 U).congr
      fun y hy => (h y hy).2.1.deriv
  have e : (3 : WithTop ℕ∞) = ((2 : ℕ) : WithTop ℕ∞) + 1 := by norm_num
  rw [e, contDiffOn_succ_iff_deriv_of_isOpen hU]
  refine ⟨fun y hy => (h y hy).1.differentiableAt.differentiableWithinAt,
    fun hh => absurd hh (nω 2), ?_⟩
  exact (by simpa using d1 : ContDiffOn ℝ ((2 : ℕ) : WithTop ℕ∞) f1 U).congr
    fun y hy => (h y hy).1.deriv

theorem bandIntegral_C3 {K : ℝ → ℝ} {E1 E2 A B : ℝ} {G : ℝ × ℝ → ℝ} {Ω : Set (ℝ × ℝ)}
    (hK : IntegrableOn K (Icc E1 E2)) (hΩ : IsOpen Ω) (hG : ContDiffOn ℝ 4 G Ω)
    (hsub : Icc A B ×ˢ Icc E1 E2 ⊆ Ω) :
    (∀ y ∈ Ioo A B,
      HasDerivAt (bandIntegral K E1 E2 G) (bandIntegral K E1 E2 (dY G) y) y ∧
      HasDerivAt (bandIntegral K E1 E2 (dY G)) (bandIntegral K E1 E2 (dY (dY G)) y) y ∧
      HasDerivAt (bandIntegral K E1 E2 (dY (dY G)))
        (bandIntegral K E1 E2 (dY (dY (dY G))) y) y) ∧
    ContinuousOn (bandIntegral K E1 E2 (dY (dY (dY G)))) (Ioo A B) ∧
    ContDiffOn ℝ 3 (bandIntegral K E1 E2 G) (Ioo A B) := by
  have g1 : ContDiffOn ℝ 3 (dY G) Ω := dY_contDiffOn hΩ hG (by norm_num)
  have g2 : ContDiffOn ℝ 2 (dY (dY G)) Ω := dY_contDiffOn hΩ g1 (by norm_num)
  have g3 : ContDiffOn ℝ 1 (dY (dY (dY G))) Ω := dY_contDiffOn hΩ g2 (by norm_num)
  have hchain : ∀ y ∈ Ioo A B,
      HasDerivAt (bandIntegral K E1 E2 G) (bandIntegral K E1 E2 (dY G) y) y ∧
      HasDerivAt (bandIntegral K E1 E2 (dY G)) (bandIntegral K E1 E2 (dY (dY G)) y) y ∧
      HasDerivAt (bandIntegral K E1 E2 (dY (dY G)))
        (bandIntegral K E1 E2 (dY (dY (dY G))) y) y := fun y hy =>
    ⟨bandIntegral_hasDerivAt hK hΩ (hG.of_le (by norm_num)) hsub hy,
     bandIntegral_hasDerivAt hK hΩ (g1.of_le (by norm_num)) hsub hy,
     bandIntegral_hasDerivAt hK hΩ (g2.of_le (by norm_num)) hsub hy⟩
  have hcont : ContinuousOn (bandIntegral K E1 E2 (dY (dY (dY G)))) (Ioo A B) := fun y hy =>
    (bandIntegral_hasDerivAt hK hΩ g3 hsub hy).continuousAt.continuousWithinAt
  exact ⟨hchain, hcont, contDiffOn_three_of_chain isOpen_Ioo hchain hcont⟩

/-! ### The thermal factor and the calibrated band response (B1) -/

/-- `E² / (exp(E/(θ y) - η₀) - ξ)` at `p = (y, E)`, with `θ = k_B T_*`. -/
def thermalFactor (θ η0 ξ : ℝ) (p : ℝ × ℝ) : ℝ :=
  p.2 ^ 2 / (Real.exp (p.2 / (θ * p.1) - η0) - ξ)

/-- Open regularity domain of the occupation (positive `y`, `E`, positive denominator). -/
def regDomain (θ η0 ξ : ℝ) : Set (ℝ × ℝ) :=
  {p | 0 < p.1 ∧ 0 < p.2 ∧ ξ < Real.exp (p.2 / (θ * p.1) - η0)}

def bandResponse (C θ η0 ξ : ℝ) (K : ℝ → ℝ) (E1 E2 y : ℝ) : ℝ :=
  C * bandIntegral K E1 E2 (thermalFactor θ η0 ξ) y
def bandResponse1 (C θ η0 ξ : ℝ) (K : ℝ → ℝ) (E1 E2 y : ℝ) : ℝ :=
  C * bandIntegral K E1 E2 (dY (thermalFactor θ η0 ξ)) y
def bandResponse2 (C θ η0 ξ : ℝ) (K : ℝ → ℝ) (E1 E2 y : ℝ) : ℝ :=
  C * bandIntegral K E1 E2 (dY (dY (thermalFactor θ η0 ξ))) y
def bandResponse3 (C θ η0 ξ : ℝ) (K : ℝ → ℝ) (E1 E2 y : ℝ) : ℝ :=
  C * bandIntegral K E1 E2 (dY (dY (dY (thermalFactor θ η0 ξ)))) y

theorem regDomain_isOpen {θ η0 ξ : ℝ} (hθ : 0 < θ) : IsOpen (regDomain θ η0 ξ) := by
  have hs : IsOpen {p : ℝ × ℝ | 0 < p.1 ∧ 0 < p.2} :=
    (isOpen_lt continuous_const continuous_fst).inter (isOpen_lt continuous_const continuous_snd)
  have hc : ContinuousOn (fun p : ℝ × ℝ => Real.exp (p.2 / (θ * p.1) - η0))
      {p : ℝ × ℝ | 0 < p.1 ∧ 0 < p.2} := by
    apply ContinuousOn.rexp
    apply ContinuousOn.sub _ continuousOn_const
    apply ContinuousOn.div continuous_snd.continuousOn
      (continuous_const.mul continuous_fst).continuousOn
    intro p hp
    exact mul_ne_zero hθ.ne' hp.1.ne'
  have := hc.isOpen_inter_preimage hs (isOpen_Ioi (a := ξ))
  convert this using 1
  ext p
  simp [regDomain, and_assoc]

theorem thermalFactor_contDiffOn {θ η0 ξ : ℝ} (hθ : 0 < θ) :
    ContDiffOn ℝ 4 (thermalFactor θ η0 ξ) (regDomain θ η0 ξ) := by
  have hnum : ContDiffOn ℝ 4 (fun p : ℝ × ℝ => p.2 ^ 2) (regDomain θ η0 ξ) :=
    (contDiff_snd.pow 2).contDiffOn
  have harg : ContDiffOn ℝ 4 (fun p : ℝ × ℝ => p.2 / (θ * p.1)) (regDomain θ η0 ξ) :=
    contDiff_snd.contDiffOn.div (contDiff_const.mul contDiff_fst).contDiffOn
      (fun p hp => mul_ne_zero hθ.ne' hp.1.ne')
  have hden : ContDiffOn ℝ 4 (fun p : ℝ × ℝ => Real.exp (p.2 / (θ * p.1) - η0) - ξ)
      (regDomain θ η0 ξ) :=
    (Real.contDiff_exp.comp_contDiffOn (harg.sub contDiffOn_const)).sub contDiffOn_const
  exact hnum.div hden (fun p hp => (sub_pos.mpr hp.2.2).ne')

/-- (B1) form: with `K` vanishing off the compact positive band `[E₁,E₂]`, the `∫₀^∞`
frequency integral equals the compact-band response. -/
theorem bandResponse_B1_form {C θ η0 ξ E1 E2 : ℝ} {K : ℝ → ℝ} (hE1 : 0 < E1)
    (hK0 : ∀ E, E ∉ Icc E1 E2 → K E = 0) (y : ℝ) :
    C * (∫ E in Ioi (0:ℝ), E ^ 2 * K E / (Real.exp (E / (θ * y) - η0) - ξ)) =
      bandResponse C θ η0 ξ K E1 E2 y := by
  unfold bandResponse bandIntegral thermalFactor
  congr 1
  rw [setIntegral_eq_of_subset_of_forall_sdiff_eq_zero measurableSet_Ioi
    (fun E hE => lt_of_lt_of_le hE1 hE.1 : Icc E1 E2 ⊆ Ioi 0)
    (fun E hE => by rw [hK0 E hE.2]; simp)]
  refine setIntegral_congr_fun measurableSet_Icc (fun E _ => ?_)
  simp only
  ring

theorem bandResponse_C3 {C θ η0 ξ E1 E2 A B : ℝ} {K : ℝ → ℝ} (hθ : 0 < θ) (hA : 0 < A)
    (hE1 : 0 < E1) (hK : IntegrableOn K (Icc E1 E2))
    (hreg : ∀ y ∈ Icc A B, ∀ E ∈ Icc E1 E2, ξ < Real.exp (E / (θ * y) - η0)) :
    (∀ y ∈ Ioo A B,
      HasDerivAt (bandResponse C θ η0 ξ K E1 E2) (bandResponse1 C θ η0 ξ K E1 E2 y) y ∧
      HasDerivAt (bandResponse1 C θ η0 ξ K E1 E2) (bandResponse2 C θ η0 ξ K E1 E2 y) y ∧
      HasDerivAt (bandResponse2 C θ η0 ξ K E1 E2) (bandResponse3 C θ η0 ξ K E1 E2 y) y) ∧
    ContinuousOn (bandResponse3 C θ η0 ξ K E1 E2) (Ioo A B) ∧
    ContDiffOn ℝ 3 (bandResponse C θ η0 ξ K E1 E2) (Ioo A B) := by
  have hsub : Icc A B ×ˢ Icc E1 E2 ⊆ regDomain θ η0 ξ := fun p hp =>
    ⟨lt_of_lt_of_le hA hp.1.1, lt_of_lt_of_le hE1 hp.2.1, hreg p.1 hp.1 p.2 hp.2⟩
  obtain ⟨hchain, hcont, hcd⟩ :=
    bandIntegral_C3 hK (regDomain_isOpen hθ) (thermalFactor_contDiffOn hθ) hsub
  refine ⟨fun y hy => ⟨((hchain y hy).1).const_mul C, ((hchain y hy).2.1).const_mul C,
    ((hchain y hy).2.2).const_mul C⟩, continuousOn_const.mul hcont, contDiffOn_const.mul hcd⟩

theorem hreg_of_nonpos_fugacity {θ η0 ξ E1 E2 A B : ℝ} (hθ : 0 < θ) (hA : 0 < A)
    (hE1 : 0 < E1) (hξ : ξ ≤ 1) (hη : η0 ≤ 0) :
    ∀ y ∈ Icc A B, ∀ E ∈ Icc E1 E2, ξ < Real.exp (E / (θ * y) - η0) := by
  intro y hy E hE
  have hy0 : 0 < y := lt_of_lt_of_le hA hy.1
  have hE0 : 0 < E := lt_of_lt_of_le hE1 hE.1
  have hq : 0 < E / (θ * y) := div_pos hE0 (mul_pos hθ hy0)
  have := Real.add_one_le_exp (E / (θ * y) - η0)
  linarith

theorem hreg_of_xi_nonpos {θ η0 ξ E1 E2 A B : ℝ} (hξ : ξ ≤ 0) :
    ∀ y ∈ Icc A B, ∀ E ∈ Icc E1 E2, ξ < Real.exp (E / (θ * y) - η0) :=
  fun _ _ _ _ => lt_of_le_of_lt hξ (Real.exp_pos _)

/-! ## T9: (a) conditional theorem from `ψ ∈ C³`, (b) the actual-kernel-class verification -/

theorem cubic_mixture_of_contDiffOn {ψ : ℝ → ℝ} {A B s s0 M : ℝ} (π : Measure ℝ)
    [IsProbabilityMeasure π] (hψ : ContDiffOn ℝ 3 ψ (Ioo A B)) (hA : A < 1 - s0)
    (hB : 1 + s0 < B)
    (hs : 0 ≤ s) (hss0 : s ≤ s0) (hsupp : ∀ᵐ y ∂π, y ∈ Icc (1 - s) (1 + s))
    (hM : ∀ z ∈ Icc (1 - s0) (1 + s0), |iteratedDeriv 3 ψ z
        - 6 * c3 (deriv ψ 1) (iteratedDeriv 2 ψ 1)
        - 24 * c4 (deriv ψ 1) (iteratedDeriv 2 ψ 1) * z| ≤ M) :
    Integrable ψ π ∧
    |(∫ y, ψ y ∂π) - estimator (ψ 1) (deriv ψ 1) (iteratedDeriv 2 ψ 1) (moment π 3) (moment π 4)|
      ≤ s ^ 3 / 6 * M := by
  have e2 : iteratedDeriv 2 ψ = deriv (deriv ψ) := by rw [iteratedDeriv_succ, iteratedDeriv_one]
  have e3 : iteratedDeriv 3 ψ = deriv (deriv (deriv ψ)) := by rw [iteratedDeriv_succ, e2]
  rw [e2, e3] at hM
  rw [e2]
  have hU : IsOpen (Ioo A B) := isOpen_Ioo
  have nω : ∀ k : ℕ, ¬ (((k : ℕ) : WithTop ℕ∞) = ⊤) := fun k => WithTop.natCast_ne_top k
  have e3' : (3 : WithTop ℕ∞) = ((2 : ℕ) : WithTop ℕ∞) + 1 := by norm_num
  have e2' : (2 : WithTop ℕ∞) = ((1 : ℕ) : WithTop ℕ∞) + 1 := by norm_num
  have e1' : (1 : WithTop ℕ∞) = ((0 : ℕ) : WithTop ℕ∞) + 1 := by norm_num
  rw [e3', contDiffOn_succ_iff_deriv_of_isOpen hU] at hψ
  obtain ⟨hd0, -, hψ1⟩ := hψ
  rw [Nat.cast_ofNat, e2', contDiffOn_succ_iff_deriv_of_isOpen hU] at hψ1
  obtain ⟨hd1, -, hψ2⟩ := hψ1
  rw [Nat.cast_one, e1', contDiffOn_succ_iff_deriv_of_isOpen hU] at hψ2
  obtain ⟨hd2, -, -⟩ := hψ2
  have hsub : Icc (1 - s0) (1 + s0) ⊆ Ioo A B := fun z hz =>
    ⟨lt_of_lt_of_le hA hz.1, lt_of_le_of_lt hz.2 hB⟩
  have hd : ∀ z ∈ Icc (1 - s0) (1 + s0),
      HasDerivAt ψ (deriv ψ z) z ∧ HasDerivAt (deriv ψ) (deriv (deriv ψ) z) z ∧
      HasDerivAt (deriv (deriv ψ)) (deriv (deriv (deriv ψ)) z) z := fun z hz =>
    ⟨((hd0 z (hsub hz)).differentiableAt (hU.mem_nhds (hsub hz))).hasDerivAt,
     ((hd1 z (hsub hz)).differentiableAt (hU.mem_nhds (hsub hz))).hasDerivAt,
     ((hd2 z (hsub hz)).differentiableAt (hU.mem_nhds (hsub hz))).hasDerivAt⟩
  exact cubic_mixture π hs hss0 hsupp hd hM

theorem bandpass_cubic_certificate {C θ η0 ξ E1 E2 A B s s0 M : ℝ} {K : ℝ → ℝ}
    (π : Measure ℝ) [IsProbabilityMeasure π]
    (hθ : 0 < θ) (hA : 0 < A) (hA' : A < 1 - s0) (hB : 1 + s0 < B) (hE1 : 0 < E1)
    (hK : IntegrableOn K (Icc E1 E2))
    (hreg : ∀ y ∈ Icc A B, ∀ E ∈ Icc E1 E2, ξ < Real.exp (E / (θ * y) - η0))
    (hs : 0 ≤ s) (hss0 : s ≤ s0) (hsupp : ∀ᵐ y ∂π, y ∈ Icc (1 - s) (1 + s))
    (hM : ∀ z ∈ Icc (1 - s0) (1 + s0), |bandResponse3 C θ η0 ξ K E1 E2 z
        - 6 * c3 (bandResponse1 C θ η0 ξ K E1 E2 1) (bandResponse2 C θ η0 ξ K E1 E2 1)
        - 24 * c4 (bandResponse1 C θ η0 ξ K E1 E2 1) (bandResponse2 C θ η0 ξ K E1 E2 1) * z|
        ≤ M) :
    ContDiffOn ℝ 3 (bandResponse C θ η0 ξ K E1 E2) (Ioo A B) ∧
    Integrable (bandResponse C θ η0 ξ K E1 E2) π ∧
    |(∫ y, bandResponse C θ η0 ξ K E1 E2 y ∂π) - estimator (bandResponse C θ η0 ξ K E1 E2 1)
        (bandResponse1 C θ η0 ξ K E1 E2 1) (bandResponse2 C θ η0 ξ K E1 E2 1)
        (moment π 3) (moment π 4)| ≤ s ^ 3 / 6 * M := by
  obtain ⟨hchain, -, hcd⟩ := bandResponse_C3 (C := C) hθ hA hE1 hK hreg
  have hsub : Icc (1 - s0) (1 + s0) ⊆ Ioo A B := fun z hz =>
    ⟨lt_of_lt_of_le hA' hz.1, lt_of_le_of_lt hz.2 hB⟩
  exact ⟨hcd, cubic_mixture π hs hss0 hsupp (fun z hz => hchain z (hsub hz)) hM⟩

theorem bandpass_M_exists {C θ η0 ξ E1 E2 A B s0 : ℝ} {K : ℝ → ℝ}
    (hθ : 0 < θ) (hA : 0 < A) (hA' : A < 1 - s0) (hB : 1 + s0 < B) (hE1 : 0 < E1)
    (hK : IntegrableOn K (Icc E1 E2))
    (hreg : ∀ y ∈ Icc A B, ∀ E ∈ Icc E1 E2, ξ < Real.exp (E / (θ * y) - η0)) :
    ∃ M, ∀ z ∈ Icc (1 - s0) (1 + s0), |bandResponse3 C θ η0 ξ K E1 E2 z
        - 6 * c3 (bandResponse1 C θ η0 ξ K E1 E2 1) (bandResponse2 C θ η0 ξ K E1 E2 1)
        - 24 * c4 (bandResponse1 C θ η0 ξ K E1 E2 1) (bandResponse2 C θ η0 ξ K E1 E2 1) * z|
        ≤ M := by
  obtain ⟨-, hcont, -⟩ := bandResponse_C3 (C := C) hθ hA hE1 hK hreg
  have hsub : Icc (1 - s0) (1 + s0) ⊆ Ioo A B := fun z hz =>
    ⟨lt_of_lt_of_le hA' hz.1, lt_of_le_of_lt hz.2 hB⟩
  have hc : ContinuousOn (fun z => bandResponse3 C θ η0 ξ K E1 E2 z
      - 6 * c3 (bandResponse1 C θ η0 ξ K E1 E2 1) (bandResponse2 C θ η0 ξ K E1 E2 1)
      - 24 * c4 (bandResponse1 C θ η0 ξ K E1 E2 1) (bandResponse2 C θ η0 ξ K E1 E2 1) * z)
      (Icc (1 - s0) (1 + s0)) :=
    ((hcont.mono hsub).sub continuousOn_const).sub (continuousOn_const.mul continuousOn_id)
  obtain ⟨M, hM⟩ := isCompact_Icc.exists_bound_of_continuousOn hc
  exact ⟨M, fun z hz => by simpa [Real.norm_eq_abs] using hM z hz⟩

/-- BE photons (`ξ = 1`, B1) with nonpositive common log-fugacity: no extra regularity input. -/
theorem bandpass_cubic_BE {C θ η0 E1 E2 s s0 : ℝ} {K : ℝ → ℝ} (π : Measure ℝ)
    [IsProbabilityMeasure π]
    (hθ : 0 < θ) (hE1 : 0 < E1) (hK : IntegrableOn K (Icc E1 E2)) (hη : η0 ≤ 0)
    (hs : 0 ≤ s) (hss0 : s ≤ s0) (hs0 : s0 < 1) (hsupp : ∀ᵐ y ∂π, y ∈ Icc (1 - s) (1 + s)) :
    (∃ M, ∀ z ∈ Icc (1 - s0) (1 + s0), |bandResponse3 C θ η0 1 K E1 E2 z
        - 6 * c3 (bandResponse1 C θ η0 1 K E1 E2 1) (bandResponse2 C θ η0 1 K E1 E2 1)
        - 24 * c4 (bandResponse1 C θ η0 1 K E1 E2 1) (bandResponse2 C θ η0 1 K E1 E2 1) * z|
        ≤ M) ∧
    (∀ M, (∀ z ∈ Icc (1 - s0) (1 + s0), |bandResponse3 C θ η0 1 K E1 E2 z
        - 6 * c3 (bandResponse1 C θ η0 1 K E1 E2 1) (bandResponse2 C θ η0 1 K E1 E2 1)
        - 24 * c4 (bandResponse1 C θ η0 1 K E1 E2 1) (bandResponse2 C θ η0 1 K E1 E2 1) * z|
        ≤ M) →
      |(∫ y, bandResponse C θ η0 1 K E1 E2 y ∂π) - estimator (bandResponse C θ η0 1 K E1 E2 1)
        (bandResponse1 C θ η0 1 K E1 E2 1) (bandResponse2 C θ η0 1 K E1 E2 1)
        (moment π 3) (moment π 4)| ≤ s ^ 3 / 6 * M) ∧
    (∀ M2, (∀ z ∈ Icc (1 - s0) (1 + s0),
        |bandResponse2 C θ η0 1 K E1 E2 z - 3 * bandResponse1 C θ η0 1 K E1 E2 1 * z ^ 2| ≤ M2) →
      |(∫ y, bandResponse C θ η0 1 K E1 E2 y ∂π) - energyEstimator
        (bandResponse C θ η0 1 K E1 E2 1) (bandResponse1 C θ η0 1 K E1 E2 1) (moment π 4)|
        ≤ s ^ 2 / 2 * M2) := by
  have hA : 0 < (1 - s0) / 2 := by linarith
  have hA' : (1 - s0) / 2 < 1 - s0 := by linarith
  have hB : 1 + s0 < s0 + 2 := by linarith
  have hreg := hreg_of_nonpos_fugacity (ξ := 1) (E2 := E2) (B := s0 + 2) hθ hA hE1 le_rfl hη
  obtain ⟨hchain, -, -⟩ := bandResponse_C3 (C := C) hθ hA hE1 hK hreg
  have hsub : Icc (1 - s0) (1 + s0) ⊆ Ioo ((1 - s0) / 2) (s0 + 2) := fun z hz =>
    ⟨lt_of_lt_of_le hA' hz.1, lt_of_le_of_lt hz.2 hB⟩
  refine ⟨bandpass_M_exists hθ hA hA' hB hE1 hK hreg, fun M hM => ?_, fun M2 hM2 => ?_⟩
  · exact (bandpass_cubic_certificate π hθ hA hA' hB hE1 hK hreg hs hss0 hsupp hM).2.2
  · exact (energy_mixture π hs hss0 hsupp
      (fun z hz => ⟨(hchain z (hsub hz)).1, (hchain z (hsub hz)).2.1⟩) hM2).2

/-- Non-vacuity witness (post-freeze addition): the kernel-class hypotheses of
`bandpass_cubic_BE` are jointly satisfiable by an explicit (non-calibrated) kernel `K ≡ 1`
on `[1,2]` and the mixture `δ₁`; the full chain then yields a finite `M` and the certificate. -/
theorem bandpass_BE_nonvacuous :
    ∃ (K : ℝ → ℝ) (π : Measure ℝ) (_ : IsProbabilityMeasure π),
      IntegrableOn K (Icc 1 2) ∧ (∀ᵐ y ∂π, y ∈ Icc (1 - (1/4 : ℝ)) (1 + 1/4)) ∧
      ∃ M, (∀ z ∈ Icc (1 - (1/2 : ℝ)) (1 + 1/2), |bandResponse3 1 1 0 1 K 1 2 z
          - 6 * c3 (bandResponse1 1 1 0 1 K 1 2 1) (bandResponse2 1 1 0 1 K 1 2 1)
          - 24 * c4 (bandResponse1 1 1 0 1 K 1 2 1) (bandResponse2 1 1 0 1 K 1 2 1) * z| ≤ M) ∧
        |(∫ y, bandResponse 1 1 0 1 K 1 2 y ∂π) - estimator (bandResponse 1 1 0 1 K 1 2 1)
          (bandResponse1 1 1 0 1 K 1 2 1) (bandResponse2 1 1 0 1 K 1 2 1)
          (moment π 3) (moment π 4)| ≤ (1/4 : ℝ) ^ 3 / 6 * M := by
  have hK : IntegrableOn (fun _ : ℝ => (1 : ℝ)) (Icc 1 2) :=
    continuousOn_const.integrableOn_compact isCompact_Icc
  have hsupp : ∀ᵐ y ∂(Measure.dirac (1 : ℝ)), y ∈ Icc (1 - (1/4 : ℝ)) (1 + 1/4) :=
    (ae_dirac_iff measurableSet_Icc).mpr ⟨by norm_num, by norm_num⟩
  obtain ⟨⟨M, hM⟩, hcub, -⟩ := bandpass_cubic_BE (C := 1) (θ := 1) (η0 := 0) (E1 := 1) (E2 := 2)
    (s := 1/4) (s0 := 1/2) (K := fun _ => 1) (Measure.dirac (1 : ℝ)) one_pos one_pos hK le_rfl
    (by norm_num) (by norm_num) (by norm_num) hsupp
  exact ⟨fun _ => 1, Measure.dirac 1, inferInstance, hK, hsupp, M, hM, hcub M hM⟩

/-- MOM-ZEROWIDTH: a zero-width prior (`s = 0`) makes the number–energy estimator exact. -/
theorem zero_width_exact {ψ ψ1 ψ2 ψ3 : ℝ → ℝ} {s0 M : ℝ} (π : Measure ℝ)
    [IsProbabilityMeasure π] (hs0 : 0 ≤ s0) (hsupp : ∀ᵐ y ∂π, y ∈ Icc (1 - 0) (1 + 0))
    (hd : ∀ z ∈ Icc (1 - s0) (1 + s0),
      HasDerivAt ψ (ψ1 z) z ∧ HasDerivAt ψ1 (ψ2 z) z ∧ HasDerivAt ψ2 (ψ3 z) z)
    (hM : ∀ z ∈ Icc (1 - s0) (1 + s0),
      |ψ3 z - 6 * c3 (ψ1 1) (ψ2 1) - 24 * c4 (ψ1 1) (ψ2 1) * z| ≤ M) :
    (∫ y, ψ y ∂π) = estimator (ψ 1) (ψ1 1) (ψ2 1) (moment π 3) (moment π 4) := by
  have h := (cubic_mixture π le_rfl hs0 hsupp hd hM).2
  rw [show ((0 : ℝ) ^ 3 / 6 * M) = 0 by ring] at h
  exact sub_eq_zero.mp (abs_nonpos_iff.mp h)

/-! ## T10: PR #501 connection (power response `ψ = y^p`) -/

theorem power_coeffs (p : ℝ) :
    c0 (Cas13C01.psi p 1) (Cas13C01.dpsi1 p 1) (Cas13C01.dpsi2 p 1) = Cas13C01.c0 p ∧
    c3 (Cas13C01.dpsi1 p 1) (Cas13C01.dpsi2 p 1) = Cas13C01.c3 p ∧
    c4 (Cas13C01.dpsi1 p 1) (Cas13C01.dpsi2 p 1) = Cas13C01.c4 p := by
  simp only [c0, c3, c4, Cas13C01.psi, Cas13C01.dpsi1, Cas13C01.dpsi2, Cas13C01.c0,
    Cas13C01.c3, Cas13C01.c4, Real.one_rpow]
  refine ⟨by ring, by ring, by ring⟩

theorem power_chain {p z : ℝ} (hz : 0 < z) :
    HasDerivAt (Cas13C01.psi p) (Cas13C01.dpsi1 p z) z ∧
    HasDerivAt (Cas13C01.dpsi1 p) (Cas13C01.dpsi2 p z) z ∧
    HasDerivAt (Cas13C01.dpsi2 p) (Cas13C01.dpsi3 p z) z := by
  refine ⟨Real.hasDerivAt_rpow_const (Or.inl hz.ne'), ?_, ?_⟩
  · have h := (Real.hasDerivAt_rpow_const (p := p - 1) (Or.inl hz.ne')).const_mul p
    refine h.congr_deriv ?_
    simp only [Cas13C01.dpsi2]
    rw [show p - 1 - 1 = p - 2 by ring]
    ring
  · have h := (Real.hasDerivAt_rpow_const (p := p - 2) (Or.inl hz.ne')).const_mul (p * (p - 1))
    refine h.congr_deriv ?_
    simp only [Cas13C01.dpsi3]
    rw [show p - 2 - 1 = p - 3 by ring]
    ring

theorem power_cubic_mixture {p s s0 M : ℝ} (π : Measure ℝ) [IsProbabilityMeasure π]
    (hs : 0 ≤ s) (hss0 : s ≤ s0) (hs0 : s0 < 1) (hsupp : ∀ᵐ y ∂π, y ∈ Icc (1 - s) (1 + s))
    (hM : ∀ z ∈ Icc (1 - s0) (1 + s0), |Cas13C01.dpsi3 p z - Cas13C01.dq3 p z| ≤ M) :
    |(∫ y, Cas13C01.psi p y ∂π) -
      (Cas13C01.c0 p + Cas13C01.c3 p * moment π 3 + Cas13C01.c4 p * moment π 4)|
      ≤ s ^ 3 / 6 * M := by
  obtain ⟨h0, h3, h4⟩ := power_coeffs p
  have hd : ∀ z ∈ Icc (1 - s0) (1 + s0),
      HasDerivAt (Cas13C01.psi p) (Cas13C01.dpsi1 p z) z ∧
      HasDerivAt (Cas13C01.dpsi1 p) (Cas13C01.dpsi2 p z) z ∧
      HasDerivAt (Cas13C01.dpsi2 p) (Cas13C01.dpsi3 p z) z := fun z hz =>
    power_chain (by linarith [hz.1])
  have hM' : ∀ z ∈ Icc (1 - s0) (1 + s0), |Cas13C01.dpsi3 p z
      - 6 * c3 (Cas13C01.dpsi1 p 1) (Cas13C01.dpsi2 p 1)
      - 24 * c4 (Cas13C01.dpsi1 p 1) (Cas13C01.dpsi2 p 1) * z| ≤ M := fun z hz => by
    rw [h3, h4]
    have := hM z hz
    simp only [Cas13C01.dq3] at this
    rwa [← sub_sub] at this
  have := (cubic_mixture π hs hss0 hsupp hd hM').2
  simp only [estimator, h0, h3, h4] at this
  exact this

end G13D
