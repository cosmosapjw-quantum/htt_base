/-
R195-A: windowed bulk flow = homogeneous mode + finite-k residual, with the full
cross-window covariance law, typed additive remainders and negative controls.
Frozen targets: ../FROZEN_TARGETS.md.  Sources: ../SOURCE_RECOVERY.md.
No sorry / admit / native_decide / new axioms.
-/
import Mathlib

open MeasureTheory Complex
open scoped ComplexConjugate InnerProductSpace ENNReal

noncomputable section

namespace R195A

/-- PR-187 frame tags (no default frame). -/
inductive Frame | n | u | obs
  deriving DecidableEq

/-- Kinds of typed additive remainder. -/
inductive RemKind | window | selection | calibration
  deriving DecidableEq

section Bulk

variable {Ω E V : Type*} [MeasurableSpace Ω] [MeasurableSpace E]
  [NormedAddCommGroup V] [NormedSpace ℝ V]

/-- Windowed bulk flow: Bochner window integral over a general window measure `ν`. -/
def bulk (ν : Measure E) (W : E → ℝ) (v : Ω → E → V) (ω : Ω) : V :=
  ∫ x, W x • v ω x ∂ν

/-- One window, one projection. -/
def wobs (ν : Measure E) (W : E → ℝ) (L : V →L[ℝ] ℝ) (v : Ω → E → V) (ω : Ω) : ℝ :=
  L (bulk ν W v ω)

/-- T1: exact Bochner decomposition, general normalization branch. -/
theorem bulk_decomposition [CompleteSpace V] {ν : Measure E} {W : E → ℝ} {v u : Ω → E → V}
    {v0 : V} {ω : Ω} (hW : Integrable W ν) (hu : Integrable (fun x => W x • u ω x) ν)
    (hv : ∀ᵐ x ∂ν, v ω x = v0 + u ω x) :
    bulk ν W v ω = (∫ x, W x ∂ν) • v0 + bulk ν W u ω := by
  unfold bulk
  have h1 : (fun x => W x • v ω x) =ᵐ[ν] fun x => W x • v0 + W x • u ω x := by
    filter_upwards [hv] with x hx
    rw [hx, smul_add]
  rw [integral_congr_ae h1, integral_add (hW.smul_const v0) hu, integral_smul_const]

/-- T1n: normalized window. -/
theorem bulk_decomposition_normalized [CompleteSpace V] {ν : Measure E} {W : E → ℝ}
    {v u : Ω → E → V} {v0 : V} {ω : Ω} (hW : Integrable W ν)
    (hu : Integrable (fun x => W x • u ω x) ν) (hv : ∀ᵐ x ∂ν, v ω x = v0 + u ω x)
    (hnorm : ∫ x, W x ∂ν = 1) :
    bulk ν W v ω = v0 + bulk ν W u ω := by
  rw [bulk_decomposition hW hu hv, hnorm, one_smul]

/-- T2: full cross-window law in configuration space (no stationarity). -/
theorem cross_window_config {P : Measure Ω} [SFinite P] {ν ν' : Measure E} [SFinite ν]
    [SFinite ν'] {W W' : E → ℝ} {a b : Ω → E → ℝ}
    (hjoint : Integrable
      (fun q : Ω × (E × E) => (W q.2.1 * a q.1 q.2.1) * (W' q.2.2 * b q.1 q.2.2))
      (P.prod (ν.prod ν'))) :
    ∫ ω, bulk ν W a ω * bulk ν' W' b ω ∂P
      = ∫ z, W z.1 * W' z.2 * (∫ ω, a ω z.1 * b ω z.2 ∂P) ∂(ν.prod ν') := by
  have h1 : ∀ ω, bulk ν W a ω * bulk ν' W' b ω
      = ∫ z, (W z.1 * a ω z.1) * (W' z.2 * b ω z.2) ∂(ν.prod ν') := by
    intro ω
    simp only [bulk, smul_eq_mul]
    exact (integral_prod_mul (fun x => W x * a ω x) (fun y => W' y * b ω y)).symm
  simp_rw [h1]
  rw [integral_integral_swap
    (f := fun ω (z : E × E) => (W z.1 * a ω z.1) * (W' z.2 * b ω z.2)) hjoint]
  congr 1
  ext z
  rw [← integral_const_mul]
  congr 1
  ext ω
  ring

/-- T3m: a mean-zero residual field has a mean-zero windowed bulk flow. -/
theorem residual_mean_zero {P : Measure Ω} [SFinite P] {ν : Measure E} [SFinite ν]
    {W : E → ℝ} {a : Ω → E → ℝ}
    (hint : Integrable (fun q : Ω × E => W q.2 * a q.1 q.2) (P.prod ν))
    (hmean : ∀ x, ∫ ω, a ω x ∂P = 0) : ∫ ω, bulk ν W a ω ∂P = 0 := by
  simp only [bulk, smul_eq_mul]
  rw [integral_integral_swap (f := fun ω x => W x * a ω x) hint]
  simp_rw [integral_const_mul, hmean, mul_zero, integral_zero]

/-- T5: typed remainder. -/
structure Rem (fr : Frame) (κ : RemKind) (V : Type*) where
  val : V

/-- T5: observation model with typed additive remainders. -/
structure ObsModel (fr : Frame) (V : Type*) where
  v0 : V
  resid : V
  win : Rem fr .window V
  sel : Rem fr .selection V
  cal : Rem fr .calibration V

/-- Observed value of an observation model. -/
def ObsModel.obs {fr : Frame} {V : Type*} [Add V] (M : ObsModel fr V) : V :=
  M.v0 + M.resid + M.win.val + M.sel.val + M.cal.val

theorem ObsModel.obs_sub_v0 {fr : Frame} {V : Type*} [AddCommGroup V] (M : ObsModel fr V) :
    M.obs - M.v0 = M.resid + (M.win.val + M.sel.val + M.cal.val) := by
  unfold ObsModel.obs
  abel

theorem ObsModel.remainder_bound {fr : Frame} {V : Type*} [NormedAddCommGroup V]
    (M : ObsModel fr V) :
    ‖M.obs - M.v0 - M.resid‖ ≤ ‖M.win.val‖ + ‖M.sel.val‖ + ‖M.cal.val‖ := by
  have : M.obs - M.v0 - M.resid = M.win.val + M.sel.val + M.cal.val := by
    unfold ObsModel.obs
    abel
  rw [this]
  exact norm_add₃_le

theorem bulk_sub_window [CompleteSpace V] {ν : Measure E} {W We : E → ℝ} {u : Ω → E → V}
    {ω : Ω} (hu : Integrable (fun x => W x • u ω x) ν)
    (hue : Integrable (fun x => We x • u ω x) ν) :
    bulk ν We u ω - bulk ν W u ω = bulk ν (fun x => We x - W x) u ω := by
  unfold bulk
  rw [← integral_sub hue hu]
  congr 1
  ext x
  rw [sub_smul]

/-- T5: finite-window remainder (general normalization). -/
theorem finite_window_remainder [CompleteSpace V] {ν : Measure E} {W We : E → ℝ}
    {v u : Ω → E → V} {v0 : V} {ω : Ω}
    (hW : Integrable W ν) (hWe : Integrable We ν) (hu : Integrable (fun x => W x • u ω x) ν)
    (hue : Integrable (fun x => We x • u ω x) ν) (hv : ∀ᵐ x ∂ν, v ω x = v0 + u ω x) :
    bulk ν We v ω - bulk ν W v ω
      = (∫ x, We x - W x ∂ν) • v0 + bulk ν (fun x => We x - W x) u ω := by
  rw [bulk_decomposition hWe hue hv, bulk_decomposition hW hu hv, integral_sub hWe hW,
    sub_smul, ← bulk_sub_window hu hue]
  abel

/-- T5: finite-window remainder, both windows normalized. -/
theorem finite_window_remainder_normalized [CompleteSpace V] {ν : Measure E} {W We : E → ℝ}
    {v u : Ω → E → V} {v0 : V} {ω : Ω}
    (hW : Integrable W ν) (hWe : Integrable We ν) (hu : Integrable (fun x => W x • u ω x) ν)
    (hue : Integrable (fun x => We x • u ω x) ν) (hv : ∀ᵐ x ∂ν, v ω x = v0 + u ω x)
    (hn : ∫ x, W x ∂ν = 1) (hne : ∫ x, We x ∂ν = 1) :
    bulk ν We v ω - bulk ν W v ω = bulk ν (fun x => We x - W x) u ω := by
  rw [finite_window_remainder hW hWe hu hue hv, integral_sub hWe hW, hn, hne, sub_self,
    zero_smul, zero_add]

/-- T5: the observation model built from a nominal window `W`, the effective window `We`,
and typed selection / calibration remainders. -/
def ObsModel.ofBulk (fr : Frame) (ν : Measure E) (W We : E → ℝ) (v : Ω → E → V) (v0 : V)
    (u : Ω → E → V) (ω : Ω) (s : Rem fr .selection V) (c : Rem fr .calibration V) :
    ObsModel fr V where
  v0 := v0
  resid := bulk ν W u ω
  win := ⟨bulk ν We v ω - bulk ν W v ω⟩
  sel := s
  cal := c

theorem ObsModel.ofBulk_obs [CompleteSpace V] (fr : Frame) {ν : Measure E} {W We : E → ℝ}
    {v u : Ω → E → V} {v0 : V} {ω : Ω} (s : Rem fr .selection V) (c : Rem fr .calibration V)
    (hW : Integrable W ν) (hu : Integrable (fun x => W x • u ω x) ν)
    (hv : ∀ᵐ x ∂ν, v ω x = v0 + u ω x) (hnorm : ∫ x, W x ∂ν = 1) :
    (ObsModel.ofBulk fr ν W We v v0 u ω s c).obs = bulk ν We v ω + s.val + c.val := by
  have h := bulk_decomposition_normalized hW hu hv hnorm
  simp only [ObsModel.obs, ObsModel.ofBulk]
  rw [h]
  abel

/-! ### Amendment A1: operator-valued window (source-declared CF4 estimator structure) -/

/-- Operator-valued windowed bulk flow `∫ W(x) v(x) dν`, `W : E → (V →L V)`. -/
def bulkOp (ν : Measure E) (W : E → V →L[ℝ] V) (v : Ω → E → V) (ω : Ω) : V :=
  ∫ x, W x (v ω x) ∂ν

/-- A1: exact decomposition for an operator-valued window, general normalization. -/
theorem bulkOp_decomposition [CompleteSpace V] {ν : Measure E} {W : E → V →L[ℝ] V}
    {v u : Ω → E → V} {v0 : V} {ω : Ω} (hW : Integrable W ν)
    (hu : Integrable (fun x => W x (u ω x)) ν) (hv : ∀ᵐ x ∂ν, v ω x = v0 + u ω x) :
    bulkOp ν W v ω = (∫ x, W x ∂ν) v0 + bulkOp ν W u ω := by
  unfold bulkOp
  have h1 : (fun x => W x (v ω x)) =ᵐ[ν] fun x => W x v0 + W x (u ω x) := by
    filter_upwards [hv] with x hx
    rw [hx, map_add]
  rw [integral_congr_ae h1, integral_add (hW.apply_continuousLinearMap v0) hu,
    ContinuousLinearMap.integral_apply hW]

/-- A1: operator window normalized to the identity. -/
theorem bulkOp_decomposition_normalized [CompleteSpace V] {ν : Measure E}
    {W : E → V →L[ℝ] V} {v u : Ω → E → V} {v0 : V} {ω : Ω} (hW : Integrable W ν)
    (hu : Integrable (fun x => W x (u ω x)) ν) (hv : ∀ᵐ x ∂ν, v ω x = v0 + u ω x)
    (hnorm : ∫ x, W x ∂ν = ContinuousLinearMap.id ℝ V) :
    bulkOp ν W v ω = v0 + bulkOp ν W u ω := by
  rw [bulkOp_decomposition hW hu hv, hnorm, ContinuousLinearMap.id_apply]

/-! ### T8: joint integrability from uniformly bounded second moments -/

/-- T8: the Fubini hypothesis `hjoint` of T2/T3 follows from joint measurability,
uniformly bounded second moments and window integrability. -/
theorem hjoint_of_second_moments {P : Measure Ω} [SFinite P] {ν ν' : Measure E} [SFinite ν]
    [SFinite ν'] {W W' : E → ℝ} {a b : Ω → E → ℝ} {Ca Cb : ℝ}
    (hWm : Measurable W) (hW'm : Measurable W')
    (ham : Measurable (fun q : Ω × E => a q.1 q.2))
    (hbm : Measurable (fun q : Ω × E => b q.1 q.2))
    (hW : Integrable W ν) (hW' : Integrable W' ν')
    (ha2 : ∀ x, Integrable (fun ω => a ω x ^ 2) P ∧ ∫ ω, a ω x ^ 2 ∂P ≤ Ca)
    (hb2 : ∀ y, Integrable (fun ω => b ω y ^ 2) P ∧ ∫ ω, b ω y ^ 2 ∂P ≤ Cb) :
    Integrable
      (fun q : Ω × (E × E) => (W q.2.1 * a q.1 q.2.1) * (W' q.2.2 * b q.1 q.2.2))
      (P.prod (ν.prod ν')) := by
  set F : Ω × (E × E) → ℝ := fun q => (W q.2.1 * a q.1 q.2.1) * (W' q.2.2 * b q.1 q.2.2)
    with hFdef
  have hA : Measurable (fun q : Ω × (E × E) => a q.1 q.2.1) :=
    ham.comp (measurable_fst.prodMk measurable_snd.fst)
  have hB : Measurable (fun q : Ω × (E × E) => b q.1 q.2.2) :=
    hbm.comp (measurable_fst.prodMk measurable_snd.snd)
  have hFm : Measurable F :=
    ((hWm.comp measurable_snd.fst).mul hA).mul ((hW'm.comp measurable_snd.snd).mul hB)
  -- pointwise bound
  have hpt : ∀ ω (z : E × E), ‖F (ω, z)‖
      ≤ (|W z.1| * |W' z.2|) * ((a ω z.1 ^ 2 + b ω z.2 ^ 2) / 2) := by
    intro ω z
    have hab : |a ω z.1| * |b ω z.2| ≤ (a ω z.1 ^ 2 + b ω z.2 ^ 2) / 2 := by
      nlinarith [sq_nonneg (|a ω z.1| - |b ω z.2|), sq_abs (a ω z.1), sq_abs (b ω z.2)]
    have h0 : 0 ≤ |W z.1| * |W' z.2| := by positivity
    simp only [hFdef, Real.norm_eq_abs, abs_mul]
    calc |W z.1| * |a ω z.1| * (|W' z.2| * |b ω z.2|)
        = (|W z.1| * |W' z.2|) * (|a ω z.1| * |b ω z.2|) := by ring
      _ ≤ (|W z.1| * |W' z.2|) * ((a ω z.1 ^ 2 + b ω z.2 ^ 2) / 2) :=
          mul_le_mul_of_nonneg_left hab h0
  have hsec : ∀ z : E × E, Integrable (fun ω => (|W z.1| * |W' z.2|)
      * ((a ω z.1 ^ 2 + b ω z.2 ^ 2) / 2)) P := fun z =>
    (((ha2 z.1).1.add (hb2 z.2).1).div_const 2).const_mul _
  rw [integrable_prod_iff' hFm.aestronglyMeasurable]
  refine ⟨Filter.Eventually.of_forall fun z => ?_, ?_⟩
  · refine (hsec z).mono' ?_ (Filter.Eventually.of_forall fun ω => hpt ω z)
    exact (hFm.comp (measurable_id.prodMk measurable_const)).aestronglyMeasurable
  · have hg : Integrable (fun z : E × E => (|W z.1| * |W' z.2|) * ((Ca + Cb) / 2))
        (ν.prod ν') := by
      have := (hW.norm.mul_prod hW'.norm).mul_const ((Ca + Cb) / 2)
      simpa [Real.norm_eq_abs] using this
    refine hg.mono' ?_ (Filter.Eventually.of_forall fun z => ?_)
    · exact (hFm.norm.stronglyMeasurable.integral_prod_left').aestronglyMeasurable
    · rw [Real.norm_eq_abs, abs_of_nonneg (integral_nonneg fun ω => norm_nonneg _)]
      calc ∫ ω, ‖F (ω, z)‖ ∂P
          ≤ ∫ ω, (|W z.1| * |W' z.2|) * ((a ω z.1 ^ 2 + b ω z.2 ^ 2) / 2) ∂P :=
            integral_mono_of_nonneg (Filter.Eventually.of_forall fun ω => norm_nonneg _)
              (hsec z) (Filter.Eventually.of_forall fun ω => hpt ω z)
        _ = (|W z.1| * |W' z.2|) * ((∫ ω, a ω z.1 ^ 2 ∂P + ∫ ω, b ω z.2 ^ 2 ∂P) / 2) := by
            rw [integral_const_mul, integral_div, integral_add (ha2 z.1).1 (hb2 z.2).1]
        _ ≤ (|W z.1| * |W' z.2|) * ((Ca + Cb) / 2) := by
            have h0 : 0 ≤ |W z.1| * |W' z.2| := by positivity
            apply mul_le_mul_of_nonneg_left _ h0
            linarith [(ha2 z.1).2, (hb2 z.2).2]

end Bulk

section Spectral

variable {Ω E V : Type*} [MeasurableSpace Ω]
  [NormedAddCommGroup E] [InnerProductSpace ℝ E] [FiniteDimensional ℝ E]
  [MeasurableSpace E] [BorelSpace E]
  [NormedAddCommGroup V] [NormedSpace ℝ V]

/-- Window transfer function `Ŵ(k) = ∫ e^{-i⟨k,x⟩} W(x) dν(x)`. -/
def ft (ν : Measure E) (W : E → ℝ) (k : E) : ℂ :=
  ∫ x, cexp (-((⟪k, x⟫_ℝ : ℂ) * I)) * (W x : ℂ) ∂ν

/-- T1g: homogeneous-mode gain is `Ŵ(0) = ∫ W`. -/
theorem ft_zero (ν : Measure E) (W : E → ℝ) : ft ν W 0 = ((∫ x, W x ∂ν : ℝ) : ℂ) := by
  simp only [ft, inner_zero_left, ofReal_zero, zero_mul, neg_zero, Complex.exp_zero, one_mul]
  exact integral_ofReal

theorem conj_ft (ν : Measure E) (W : E → ℝ) (k : E) :
    conj (ft ν W k) = ∫ x, cexp ((⟪k, x⟫_ℝ : ℂ) * I) * (W x : ℂ) ∂ν := by
  rw [ft, ← integral_conj]
  congr 1
  ext x
  rw [map_mul, conj_ofReal, ← Complex.exp_conj, map_neg, map_mul, conj_ofReal, conj_I]
  congr 2
  ring

/-- T3: covariance / cross-covariance of two windowed bulk flows from the power spectrum. -/
theorem cross_window_spectral {P : Measure Ω} [SFinite P] {ν ν' μ : Measure E}
    [SFinite ν] [SFinite ν'] [SFinite μ] {W W' : E → ℝ} {a b : Ω → E → ℝ} {p : E → ℂ}
    (hW : Integrable W ν) (hW' : Integrable W' ν') (hp : Integrable p μ)
    (hjoint : Integrable
      (fun q : Ω × (E × E) => (W q.2.1 * a q.1 q.2.1) * (W' q.2.2 * b q.1 q.2.2))
      (P.prod (ν.prod ν')))
    (hK : ∀ x y, ((∫ ω, a ω x * b ω y ∂P : ℝ) : ℂ)
      = ∫ k, cexp ((⟪k, x - y⟫_ℝ : ℂ) * I) * p k ∂μ) :
    ((∫ ω, bulk ν W a ω * bulk ν' W' b ω ∂P : ℝ) : ℂ)
      = ∫ k, conj (ft ν W k) * ft ν' W' k * p k ∂μ := by
  rw [cross_window_config hjoint, ← integral_complex_ofReal]
  have h1 : ∀ z : E × E, (((W z.1 * W' z.2 * ∫ ω, a ω z.1 * b ω z.2 ∂P : ℝ)) : ℂ)
      = ∫ k, ((W z.1 : ℂ) * (W' z.2 : ℂ)) * (cexp ((⟪k, z.1 - z.2⟫_ℝ : ℂ) * I) * p k) ∂μ := by
    intro z
    rw [ofReal_mul, ofReal_mul, hK, integral_const_mul]
  simp_rw [h1]
  -- joint integrability on (ν × ν') × μ
  have hWW : Integrable (fun z : E × E => (W z.1 : ℂ) * (W' z.2 : ℂ)) (ν.prod ν') :=
    hW.ofReal.mul_prod hW'.ofReal
  have hG : Integrable (fun q : (E × E) × E => ((W q.1.1 : ℂ) * (W' q.1.2 : ℂ)) * p q.2)
      ((ν.prod ν').prod μ) := hWW.mul_prod hp
  have hF : Integrable (fun q : (E × E) × E =>
      cexp ((⟪q.2, q.1.1 - q.1.2⟫_ℝ : ℂ) * I) * (((W q.1.1 : ℂ) * (W' q.1.2 : ℂ)) * p q.2))
      ((ν.prod ν').prod μ) := by
    refine hG.bdd_mul (c := 1) ?_ ?_
    · exact (Continuous.aestronglyMeasurable (by fun_prop))
    · exact Filter.Eventually.of_forall fun q => (norm_exp_ofReal_mul_I _).le
  have hF' : Integrable (Function.uncurry fun (z : E × E) (k : E) =>
      ((W z.1 : ℂ) * (W' z.2 : ℂ)) * (cexp ((⟪k, z.1 - z.2⟫_ℝ : ℂ) * I) * p k))
      ((ν.prod ν').prod μ) := by
    refine hF.congr (Filter.Eventually.of_forall fun q => ?_)
    simp only [Function.uncurry]
    ring
  rw [integral_integral_swap hF']
  congr 1
  ext k
  rw [conj_ft, ft]
  have h2 : ∀ z : E × E, ((W z.1 : ℂ) * (W' z.2 : ℂ)) * (cexp ((⟪k, z.1 - z.2⟫_ℝ : ℂ) * I) * p k)
      = ((cexp ((⟪k, z.1⟫_ℝ : ℂ) * I) * (W z.1 : ℂ))
          * (cexp (-((⟪k, z.2⟫_ℝ : ℂ) * I)) * (W' z.2 : ℂ))) * p k := by
    intro z
    rw [inner_sub_right, ofReal_sub, sub_mul, sub_eq_add_neg, Complex.exp_add]
    ring
  simp_rw [h2]
  rw [integral_mul_const, integral_prod_mul
    (fun x => cexp ((⟪k, x⟫_ℝ : ℂ) * I) * (W x : ℂ))
    (fun y => cexp (-((⟪k, y⟫_ℝ : ℂ) * I)) * (W' y : ℂ))]

/-- T4: PR-222 multi-window stochastic forward law, generalized: every window `m` has its
projection `L m`; the cross terms for every pair `(m, n)` are kept. -/
theorem multiwindow_forward_law {ι : Type*} [CompleteSpace V] {P : Measure Ω}
    [IsProbabilityMeasure P] {μ : Measure E} [SFinite μ] (ν : ι → Measure E)
    [∀ m, SFinite (ν m)] (W : ι → E → ℝ) (L : ι → V →L[ℝ] ℝ) (v u : Ω → E → V) (v0 : V)
    (pc : ι → ι → E → ℂ)
    (hW : ∀ m, Integrable (W m) (ν m)) (hnorm : ∀ m, ∫ x, W m x ∂(ν m) = 1)
    (hv : ∀ ω m, ∀ᵐ x ∂(ν m), v ω x = v0 + u ω x)
    (hu : ∀ ω m, Integrable (fun x => W m x • u ω x) (ν m))
    (hint1 : ∀ m, Integrable (fun q : Ω × E => W m q.2 * L m (u q.1 q.2)) (P.prod (ν m)))
    (hmean : ∀ m x, ∫ ω, L m (u ω x) ∂P = 0)
    (hjoint : ∀ m n, Integrable (fun q : Ω × (E × E) =>
        (W m q.2.1 * L m (u q.1 q.2.1)) * (W n q.2.2 * L n (u q.1 q.2.2)))
        (P.prod ((ν m).prod (ν n))))
    (hpc : ∀ m n, Integrable (pc m n) μ)
    (hK : ∀ m n x y, ((∫ ω, L m (u ω x) * L n (u ω y) ∂P : ℝ) : ℂ)
        = ∫ k, cexp ((⟪k, x - y⟫_ℝ : ℂ) * I) * pc m n k ∂μ) :
    (∀ m ω, wobs (ν m) (W m) (L m) v ω
        = L m v0 + bulk (ν m) (W m) (fun ω x => L m (u ω x)) ω) ∧
    (∀ m, ∫ ω, wobs (ν m) (W m) (L m) v ω ∂P = L m v0) ∧
    (∀ m n, ((∫ ω, (wobs (ν m) (W m) (L m) v ω - L m v0)
          * (wobs (ν n) (W n) (L n) v ω - L n v0) ∂P : ℝ) : ℂ)
        = ∫ k, conj (ft (ν m) (W m) k) * ft (ν n) (W n) k * pc m n k ∂μ) := by
  have h1 : ∀ m ω, wobs (ν m) (W m) (L m) v ω
      = L m v0 + bulk (ν m) (W m) (fun ω x => L m (u ω x)) ω := by
    intro m ω
    unfold wobs
    rw [bulk_decomposition_normalized (hW m) (hu ω m) (hv ω m) (hnorm m), map_add]
    congr 1
    unfold bulk
    rw [← ContinuousLinearMap.integral_comp_comm _ (hu ω m)]
    congr 1
    ext x
    rw [map_smul, smul_eq_mul]
  refine ⟨h1, ?_, ?_⟩
  · intro m
    simp_rw [h1 m]
    have hb : Integrable (fun ω => bulk (ν m) (W m) (fun ω x => L m (u ω x)) ω) P := by
      have := (hint1 m).integral_prod_left
      simpa [bulk, smul_eq_mul] using this
    rw [integral_add (integrable_const _) hb, integral_const, residual_mean_zero (hint1 m) (hmean m)]
    simp
  · intro m n
    simp_rw [h1, add_sub_cancel_left]
    exact cross_window_spectral (hW m) (hW n) (hpc m n) (hjoint m n) (hK m n)

/-- A2: vector field with matrix cross-spectrum `p i j` and component windows `w i`, `w' j`:
the full cross-window covariance is the double sum of all component cross-spectra. -/
theorem cross_window_spectral_matrix {d : ℕ} {P : Measure Ω} [SFinite P] {ν ν' μ : Measure E}
    [SFinite ν] [SFinite ν'] [SFinite μ] {w w' : Fin d → E → ℝ} {a : Ω → E → Fin d → ℝ}
    {p : Fin d → Fin d → E → ℂ}
    (hw : ∀ i, Integrable (w i) ν) (hw' : ∀ j, Integrable (w' j) ν')
    (hp : ∀ i j, Integrable (p i j) μ)
    (hjoint : ∀ i j, Integrable (fun q : Ω × (E × E) =>
        (w i q.2.1 * a q.1 q.2.1 i) * (w' j q.2.2 * a q.1 q.2.2 j)) (P.prod (ν.prod ν')))
    (hK : ∀ i j x y, ((∫ ω, a ω x i * a ω y j ∂P : ℝ) : ℂ)
        = ∫ k, cexp ((⟪k, x - y⟫_ℝ : ℂ) * I) * p i j k ∂μ) :
    ((∫ ω, (∑ i, bulk ν (w i) (fun ω x => a ω x i) ω)
        * (∑ j, bulk ν' (w' j) (fun ω x => a ω x j) ω) ∂P : ℝ) : ℂ)
      = ∑ i, ∑ j, ∫ k, conj (ft ν (w i) k) * ft ν' (w' j) k * p i j k ∂μ := by
  have hint : ∀ i j, Integrable (fun ω => bulk ν (w i) (fun ω x => a ω x i) ω
      * bulk ν' (w' j) (fun ω x => a ω x j) ω) P := by
    intro i j
    refine ((hjoint i j).integral_prod_left).congr (Filter.Eventually.of_forall fun ω => ?_)
    simp only [bulk, smul_eq_mul]
    exact integral_prod_mul (fun x => w i x * a ω x i) (fun y => w' j y * a ω y j)
  simp_rw [Finset.sum_mul_sum]
  rw [integral_finsetSum _ (fun i _ => integrable_finsetSum _ (fun j _ => hint i j))]
  push_cast
  refine Finset.sum_congr rfl fun i _ => ?_
  rw [integral_finsetSum _ (fun j _ => hint i j)]
  push_cast
  refine Finset.sum_congr rfl fun j _ => ?_
  exact cross_window_spectral (hw i) (hw' j) (hp i j) (hjoint i j) (hK i j)

/-- T6: the spectral carrier excludes `k = 0` when `μ` has no atoms; the constant mode is
carried only by `v0`. -/
theorem spectral_excludes_k0 {μ : Measure E} [NoAtoms μ] (F : E → ℂ) :
    ∫ k, F k ∂μ = ∫ k in ({0}ᶜ : Set E), F k ∂μ := by
  rw [Measure.restrict_eq_self_of_ae_mem]
  exact compl_mem_ae_iff.mpr (measure_singleton 0)

end Spectral

/-! ### Amendment A1 (CF4 instance): the source-declared WLS bulk-flow estimator
`B = A⁻¹ b`, `A = Σ w_i n_i n_iᵀ`, `b = Σ w_i u_i n_i` is an operator-window bulk flow with
windows `W_i = A⁻¹ (w_i n_i n_iᵀ)` summing to the identity. -/

section CF4

variable {V : Type*} [NormedAddCommGroup V] [InnerProductSpace ℝ V]

/-- `G_i = w_i n_i n_iᵀ`. -/
def cf4G {N : ℕ} (w : Fin N → ℝ) (n : Fin N → V) (i : Fin N) : V →L[ℝ] V :=
  w i • (innerSL ℝ (n i)).smulRight (n i)

theorem cf4G_apply {N : ℕ} (w : Fin N → ℝ) (n : Fin N → V) (i : Fin N) (x : V) :
    cf4G w n i x = (w i * ⟪n i, x⟫_ℝ) • n i := by
  simp [cf4G, mul_smul]

/-- A1: the discrete CF4 windows `A⁻¹ G_i` are normalized. -/
theorem cf4_window_normalized {N : ℕ} (w : Fin N → ℝ) (n : Fin N → V) (Ainv : V →L[ℝ] V)
    (hA : Ainv.comp (∑ i, cf4G w n i) = ContinuousLinearMap.id ℝ V) :
    ∑ i, Ainv.comp (cf4G w n i) = ContinuousLinearMap.id ℝ V := by
  rw [← hA, ContinuousLinearMap.comp_finsetSum]

/-- A1: exact decomposition of the source-declared CF4 estimator: radial data
`u_i^obs = ⟪n_i, v(x_i)⟫ + ε_i`, `v(x_i) = v0 + δ_i` gives
`A⁻¹ b = v0 + Σ_i A⁻¹ G_i δ_i + A⁻¹ Σ_i w_i ε_i n_i` (homogeneous mode + finite-k
residual + noise), with no `B/c` substitution. -/
theorem cf4_estimator_decomposition {N : ℕ} (w : Fin N → ℝ) (n : Fin N → V)
    (vel δ : Fin N → V) (ε : Fin N → ℝ) (v0 : V) (Ainv : V →L[ℝ] V)
    (hA : Ainv.comp (∑ i, cf4G w n i) = ContinuousLinearMap.id ℝ V)
    (hv : ∀ i, vel i = v0 + δ i) :
    Ainv (∑ i, (w i * (⟪n i, vel i⟫_ℝ + ε i)) • n i)
      = v0 + ∑ i, (Ainv.comp (cf4G w n i)) (δ i) + Ainv (∑ i, (w i * ε i) • n i) := by
  have h1 : ∀ i, (w i * (⟪n i, vel i⟫_ℝ + ε i)) • n i
      = cf4G w n i v0 + cf4G w n i (δ i) + (w i * ε i) • n i := by
    intro i
    rw [cf4G_apply, cf4G_apply, hv i, inner_add_right, ← add_smul, ← add_smul]
    congr 1
    ring
  simp_rw [h1, Finset.sum_add_distrib, map_add, map_sum]
  have h2 : Ainv (∑ i, cf4G w n i v0) = v0 := by
    have := congrArg (fun T : V →L[ℝ] V => T v0) hA
    simpa [ContinuousLinearMap.sum_apply] using this
  rw [h2]
  simp [ContinuousLinearMap.comp_apply]

end CF4

/-! ## T7 non-vacuity witnesses and negative controls -/

section Witness

/-- Four-point random phase field `a(j, x) = cos(x + jπ/2)`. -/
def aw : Fin 4 → ℝ → ℝ
  | 0, x => Real.cos x
  | 1, x => -Real.sin x
  | 2, x => -Real.cos x
  | 3, x => Real.sin x

/-- Uniform probability on `Fin 4`. -/
def Pw : Measure (Fin 4) := (4 : ℝ≥0∞)⁻¹ • Measure.count

theorem Pw_isProbability : IsProbabilityMeasure Pw := by
  constructor
  simp [Pw, Measure.count_apply_finite]
  rw [ENNReal.inv_mul_cancel] <;> norm_num

theorem integral_Pw (f : Fin 4 → ℝ) : ∫ ω, f ω ∂Pw = (f 0 + f 1 + f 2 + f 3) / 4 := by
  rw [Pw, integral_smul_measure, integral_fintype Integrable.of_finite]
  simp [Fin.sum_univ_four, Measure.real]
  ring

theorem witness_mean_zero : ∀ x, ∫ ω, aw ω x ∂Pw = 0 := by
  intro x
  rw [integral_Pw]
  simp [aw]

theorem witness_cov : ∀ x y, ∫ ω, aw ω x * aw ω y ∂Pw = Real.cos (x - y) / 2 := by
  intro x y
  rw [integral_Pw]
  simp [aw, Real.cos_sub]
  ring

theorem witness_spectral : ∀ x y, ((∫ ω, aw ω x * aw ω y ∂Pw : ℝ) : ℂ)
    = ∫ k, cexp ((⟪k, x - y⟫_ℝ : ℂ) * I) * (1 / 4 : ℂ)
        ∂(Measure.dirac (1 : ℝ) + Measure.dirac (-1)) := by
  intro x y
  rw [witness_cov, integral_add_measure (integrable_dirac enorm_lt_top)
    (integrable_dirac enorm_lt_top), integral_dirac, integral_dirac]
  simp only [Real.inner_apply, one_mul, neg_mul, ofReal_neg]
  have h := Complex.two_cos ((x - y : ℝ) : ℂ)
  rw [neg_mul] at h
  push_cast at h ⊢
  linear_combination h / 4

theorem witness_residual_nonzero (v0 : ℝ) :
    bulk (Measure.dirac (0 : ℝ)) (fun _ => 1) (fun ω x => v0 + aw ω x) (0 : Fin 4) ≠ v0 := by
  simp [bulk, integral_dirac, aw]

theorem witness_residual_variance :
    ∫ ω, (bulk (Measure.dirac (0 : ℝ)) (fun _ => 1) aw ω) ^ 2 ∂Pw = 1 / 2 := by
  simp only [bulk, integral_dirac, one_smul]
  rw [integral_Pw]
  simp [aw]
  norm_num

theorem witness_cross_window :
    ∫ ω, bulk (Measure.dirac (0 : ℝ)) (fun _ => 1) aw ω
        * bulk (Measure.dirac (1 : ℝ)) (fun _ => 1) aw ω ∂Pw = Real.cos 1 / 2
      ∧ 0 < Real.cos 1 / 2 := by
  refine ⟨?_, ?_⟩
  · simp only [bulk, integral_dirac, one_smul]
    rw [integral_Pw]
    simp [aw]
    ring
  · have h : 0 < Real.cos 1 := by
      apply Real.cos_pos_of_mem_Ioo
      constructor
      · linarith [Real.pi_pos]
      · linarith [Real.pi_gt_three]
    linarith

theorem witness_nonidentification :
    bulk (Measure.dirac (0 : ℝ)) 1 (fun ω x => (0 : ℝ) + aw ω x) (0 : Fin 4)
      = bulk (Measure.dirac (0 : ℝ)) 1 (fun ω x => (1 : ℝ) + aw ω x) (1 : Fin 4) := by
  simp [bulk, integral_dirac, aw]

end Witness

end R195A
