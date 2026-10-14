import Mathlib
import G11AGuarded
import G12DCardClosure
import OscillatoryDerivative

/-!
# G12-E (TEFF-H1): compact moment-null perturbation, general measure part

Targets are frozen in `../FROZEN_TARGETS.md` (T1, T2, T3, T3b, T4, T4b, T4c).

* `m + 1` disjoint `ContDiffBump`s on a positive energy patch `[E1, E2]`, `0 < E1`;
* a nonzero kernel vector of the `m × (m+1)` moment matrix gives a C^∞ compactly supported
  `q ≠ 0` annihilating every retained moment (smoothness comes from the bumps, not from the
  kernel);
* one family `f_n(x, z) = g(z.1) + a sin(n x) q(z.1)` with amplitude `a` chosen before `n`:
  common-envelope admissibility, fixed retained moments, a uniform static Bregman divergence
  bound (reviewed `G11A.Dext` / domain-guarded `G11A.finite_budget_stat`), and
  `∂_x f_n(0, z) = a n q(z.1)` (reviewed `CAS12C04.hasDerivAt_constant_q`).

`q` depends only on the momentum (energy) variable, never on `x`.
Reviewed imports are unchanged.  Scientific admission is not claimed.
-/

open MeasureTheory Set Filter Topology
open scoped ENNReal

noncomputable section

namespace G12E

open G11A

/-! ## Cells and bumps -/

/-- Width of each of the `m + 1` cells of `[E1, E2]`. -/
def cellWidth (E1 E2 : ℝ) (m : ℕ) : ℝ := (E2 - E1) / (m + 1)

/-- Midpoint of cell `i`. -/
def cellCenter (E1 E2 : ℝ) (m : ℕ) (i : Fin (m + 1)) : ℝ :=
  E1 + ((i : ℝ) + 1 / 2) * cellWidth E1 E2 m

theorem cellWidth_pos {E1 E2 : ℝ} (h : E1 < E2) (m : ℕ) : 0 < cellWidth E1 E2 m :=
  div_pos (sub_pos.2 h) (by positivity)

theorem cellWidth_mul {E1 E2 : ℝ} (m : ℕ) :
    ((m : ℝ) + 1) * cellWidth E1 E2 m = E2 - E1 := by
  have hm : (m : ℝ) + 1 ≠ 0 := by positivity
  unfold cellWidth
  field_simp

/-- Smooth bump of cell `i`: `rIn = width/4`, `rOut = width/2`. -/
def cellBump {E1 E2 : ℝ} (h : E1 < E2) (m : ℕ) (i : Fin (m + 1)) :
    ContDiffBump (cellCenter E1 E2 m i) where
  rIn := cellWidth E1 E2 m / 4
  rOut := cellWidth E1 E2 m / 2
  rIn_pos := by have := cellWidth_pos h m; positivity
  rIn_lt_rOut := by have := cellWidth_pos h m; linarith

/-- The bump functions `ψ_i`. -/
def psi {E1 E2 : ℝ} (h : E1 < E2) (m : ℕ) (i : Fin (m + 1)) : ℝ → ℝ := ⇑(cellBump h m i)

/-- The profile `q_c = Σ_i c_i ψ_i`. -/
def qOf {E1 E2 : ℝ} (h : E1 < E2) (m : ℕ) (c : Fin (m + 1) → ℝ) : ℝ → ℝ :=
  fun E => ∑ i, c i * psi h m i E

/-- The positive compact momentum patch `{z | z.1 ∈ [E1, E2]}`. -/
def patchE {Ω : Type*} (E1 E2 : ℝ) : Set (ℝ × Ω) := Prod.fst ⁻¹' Icc E1 E2

/-- The spacetime family `f_n(x, z) = g(z.1) + a sin(n x) q(z.1)`; `q` does not depend on `x`. -/
def family {Ω : Type*} (g q : ℝ → ℝ) (a : ℝ) (n : ℕ) (x : ℝ) : ℝ × Ω → ℝ :=
  fun z => g z.1 + a * Real.sin ((n : ℝ) * x) * q z.1

/-- Admissibility at one spacetime point: closed statistics domain and common envelope. -/
def Admissible {Ω : Type*} (s : Stat) (F : ℝ → ℝ) (f : ℝ × Ω → ℝ) : Prop :=
  ∀ z : ℝ × Ω, 0 < z.1 → f z ∈ cdom s ∧ f z ≤ F z.1

section Bumps

variable {E1 E2 : ℝ} (h : E1 < E2) (m : ℕ)

theorem psi_support (i : Fin (m + 1)) :
    Function.support (psi h m i) =
      Metric.ball (cellCenter E1 E2 m i) (cellWidth E1 E2 m / 2) :=
  (cellBump h m i).support_eq

theorem psi_eq_zero_of_le (i : Fin (m + 1)) {E : ℝ}
    (hE : cellWidth E1 E2 m / 2 ≤ |E - cellCenter E1 E2 m i|) : psi h m i E = 0 := by
  by_contra hne
  have hmem : E ∈ Function.support (psi h m i) := hne
  rw [psi_support, Metric.mem_ball, Real.dist_eq] at hmem
  linarith

theorem psi_eq_one_of_le (i : Fin (m + 1)) {E : ℝ}
    (hE : |E - cellCenter E1 E2 m i| ≤ cellWidth E1 E2 m / 4) : psi h m i E = 1 :=
  (cellBump h m i).one_of_mem_closedBall (by
    rw [Metric.mem_closedBall, Real.dist_eq]; exact hE)

theorem psi_nonneg (i : Fin (m + 1)) (E : ℝ) : 0 ≤ psi h m i E := (cellBump h m i).nonneg

theorem psi_le_one (i : Fin (m + 1)) (E : ℝ) : psi h m i E ≤ 1 := (cellBump h m i).le_one

theorem psi_continuous (i : Fin (m + 1)) : Continuous (psi h m i) := (cellBump h m i).continuous

theorem center_sub (i j : Fin (m + 1)) :
    cellCenter E1 E2 m i - cellCenter E1 E2 m j = ((i : ℝ) - j) * cellWidth E1 E2 m := by
  unfold cellCenter; ring


theorem one_le_abs_fin_sub {i j : Fin (m + 1)} (hij : i ≠ j) : (1 : ℝ) ≤ |(i : ℝ) - j| := by
  rcases lt_or_gt_of_ne hij with hlt | hgt
  · have h1 : (i : ℕ) + 1 ≤ (j : ℕ) := hlt
    have h2 : (i : ℝ) + 1 ≤ (j : ℝ) := by exact_mod_cast h1
    rw [abs_of_neg (by linarith)]
    linarith
  · have h1 : (j : ℕ) + 1 ≤ (i : ℕ) := hgt
    have h2 : (j : ℝ) + 1 ≤ (i : ℝ) := by exact_mod_cast h1
    rw [abs_of_pos (by linarith)]
    linarith

theorem psi_center (i j : Fin (m + 1)) :
    psi h m i (cellCenter E1 E2 m j) = if i = j then 1 else 0 := by
  have hw := cellWidth_pos h m
  split_ifs with hij
  · subst hij
    apply psi_eq_one_of_le
    rw [sub_self, abs_zero]
    positivity
  · apply psi_eq_zero_of_le
    rw [center_sub, abs_mul, abs_of_pos hw]
    have := one_le_abs_fin_sub m (Ne.symm hij)
    nlinarith

theorem psi_zero_near_other {i j : Fin (m + 1)} (hij : i ≠ j) {E : ℝ}
    (hE : |E - cellCenter E1 E2 m i| ≤ cellWidth E1 E2 m / 4) : psi h m j E = 0 := by
  apply psi_eq_zero_of_le
  have hw := cellWidth_pos h m
  have hc : |cellCenter E1 E2 m i - cellCenter E1 E2 m j| = |(i : ℝ) - j| * cellWidth E1 E2 m := by
    rw [center_sub, abs_mul, abs_of_pos hw]
  have h1 := one_le_abs_fin_sub m hij
  have htri := abs_sub_le (cellCenter E1 E2 m i) E (cellCenter E1 E2 m j)
  rw [abs_sub_comm (cellCenter E1 E2 m i) E] at htri
  nlinarith

theorem psi_support_subset (i : Fin (m + 1)) : Function.support (psi h m i) ⊆ Ioo E1 E2 := by
  intro E hE
  rw [psi_support, Metric.mem_ball, Real.dist_eq, abs_lt] at hE
  have hw := cellWidth_pos h m
  have hmul := cellWidth_mul (E1 := E1) (E2 := E2) m
  have hi0 : (0 : ℝ) ≤ (i : ℝ) := Nat.cast_nonneg _
  have him : (i : ℝ) + 1 ≤ (m : ℝ) + 1 := by
    have : (i : ℕ) + 1 ≤ m + 1 := i.isLt
    exact_mod_cast this
  unfold cellCenter at hE
  constructor <;> nlinarith

theorem psi_eq_zero_outside (i : Fin (m + 1)) {E : ℝ} (hE : E ∉ Ioo E1 E2) : psi h m i E = 0 := by
  by_contra hne
  exact hE (psi_support_subset h m i hne)

theorem center_mem_Ioo (i : Fin (m + 1)) : cellCenter E1 E2 m i ∈ Ioo E1 E2 :=
  psi_support_subset h m i (by
    rw [Function.mem_support, psi_center, if_pos rfl]; norm_num)

/-- **T1.** Smooth compactly supported bumps with disjoint supports in the open patch. -/
theorem psi_props (i : Fin (m + 1)) :
    ContDiff ℝ ((⊤ : ℕ∞) : WithTop ℕ∞) (psi h m i) ∧ HasCompactSupport (psi h m i) ∧
    Function.support (psi h m i) ⊆ Ioo E1 E2 ∧
    (∀ E, 0 ≤ psi h m i E ∧ psi h m i E ≤ 1) ∧
    (∀ j, psi h m i (cellCenter E1 E2 m j) = if i = j then 1 else 0) :=
  ⟨(cellBump h m i).contDiff, (cellBump h m i).hasCompactSupport, psi_support_subset h m i,
    fun E => ⟨psi_nonneg h m i E, psi_le_one h m i E⟩, psi_center h m i⟩

variable (c : Fin (m + 1) → ℝ)

theorem qOf_contDiff : ContDiff ℝ ((⊤ : ℕ∞) : WithTop ℕ∞) (qOf h m c) := by
  unfold qOf
  exact ContDiff.sum fun i _ => contDiff_const.mul (cellBump h m i).contDiff

theorem qOf_eq_zero {E : ℝ} (hE : E ∉ Ioo E1 E2) : qOf h m c E = 0 := by
  unfold qOf
  refine Finset.sum_eq_zero fun i _ => ?_
  rw [psi_eq_zero_outside h m i hE, mul_zero]

theorem qOf_eq_zero_of_notMem_Icc {E : ℝ} (hE : E ∉ Icc E1 E2) : qOf h m c E = 0 :=
  qOf_eq_zero h m c fun h' => hE (Ioo_subset_Icc_self h')

theorem qOf_abs_le (E : ℝ) : |qOf h m c E| ≤ ∑ i, |c i| := by
  unfold qOf
  calc |∑ i, c i * psi h m i E| ≤ ∑ i, |c i * psi h m i E| := Finset.abs_sum_le_sum_abs _ _
    _ ≤ ∑ i, |c i| := Finset.sum_le_sum fun i _ => by
        rw [abs_mul, abs_of_nonneg (psi_nonneg h m i E)]
        exact mul_le_of_le_one_right (abs_nonneg _) (psi_le_one h m i E)

theorem qOf_center (i : Fin (m + 1)) : qOf h m c (cellCenter E1 E2 m i) = c i := by
  unfold qOf
  rw [Finset.sum_eq_single i (fun j _ hji => by rw [psi_center, if_neg hji, mul_zero])
    (fun hi => absurd (Finset.mem_univ i) hi), psi_center, if_pos rfl, mul_one]

theorem qOf_core (i : Fin (m + 1)) {E : ℝ}
    (hE : |E - cellCenter E1 E2 m i| ≤ cellWidth E1 E2 m / 4) : qOf h m c E = c i := by
  unfold qOf
  rw [Finset.sum_eq_single i
    (fun j _ hji => by rw [psi_zero_near_other h m (Ne.symm hji) hE, mul_zero])
    (fun hi => absurd (Finset.mem_univ i) hi), psi_eq_one_of_le h m i hE, mul_one]

/-- **T2.** The profile is C^∞, compactly supported in the patch, bounded, and interpolates `c`. -/
theorem q_props :
    ContDiff ℝ ((⊤ : ℕ∞) : WithTop ℕ∞) (qOf h m c) ∧ HasCompactSupport (qOf h m c) ∧
    tsupport (qOf h m c) ⊆ Icc E1 E2 ∧ (∀ E, |qOf h m c E| ≤ ∑ i, |c i|) ∧
    (∀ i, qOf h m c (cellCenter E1 E2 m i) = c i) := by
  refine ⟨qOf_contDiff h m c,
    HasCompactSupport.intro isCompact_Icc fun E hE => qOf_eq_zero_of_notMem_Icc h m c hE,
    ?_, qOf_abs_le h m c, qOf_center h m c⟩
  refine closure_minimal (fun E hE => ?_) isClosed_Icc
  by_contra hne
  exact hE (qOf_eq_zero_of_notMem_Icc h m c hne)

end Bumps

/-! ## Moment matrix and its kernel -/

section Moments

variable {Ω : Type*} [MeasurableSpace Ω]

theorem patchE_measurable (E1 E2 : ℝ) : MeasurableSet (patchE (Ω := Ω) E1 E2) :=
  measurable_fst measurableSet_Icc

/-- A kernel integrable on the patch times a bounded measurable profile vanishing off the patch. -/
theorem integrable_mul_patch (μ : Measure (ℝ × Ω)) (φ : ℝ × Ω → ℝ) (u : ℝ → ℝ)
    {E1 E2 K : ℝ} (hφ : IntegrableOn φ (patchE E1 E2) μ) (hu : Measurable u)
    (hb : ∀ E, |u E| ≤ K) (hz : ∀ E ∉ Icc E1 E2, u E = 0) :
    Integrable (fun z => φ z * u z.1) μ := by
  have hi := hφ.integrable_indicator (patchE_measurable E1 E2)
  have h2 : Integrable (fun z => (patchE E1 E2).indicator φ z * u z.1) μ :=
    hi.mul_bdd (hu.comp measurable_fst).aestronglyMeasurable
      (ae_of_all _ fun z => by rw [Real.norm_eq_abs]; exact hb z.1)
  refine h2.congr (ae_of_all _ fun z => ?_)
  by_cases hz' : z ∈ patchE (Ω := Ω) E1 E2
  · simp only [indicator_of_mem hz']
  · have h0 : u z.1 = 0 := hz _ hz'
    simp only [indicator_of_notMem hz', h0, mul_zero]

/-- Bounded measurable functions vanishing off the patch are integrable when the patch is finite. -/
theorem integrable_of_bdd_patch (μ : Measure (ℝ × Ω)) {E1 E2 M : ℝ} (f : ℝ × Ω → ℝ)
    (hμP : μ (patchE E1 E2) ≠ ⊤) (hm : AEStronglyMeasurable f μ) (hb : ∀ z, |f z| ≤ M)
    (hz : ∀ z : ℝ × Ω, z.1 ∉ Icc E1 E2 → f z = 0) : Integrable f μ := by
  have hon : IntegrableOn f (patchE E1 E2) μ :=
    Measure.integrableOn_of_bounded hμP hm (M := M)
      (ae_of_all _ fun z => by rw [Real.norm_eq_abs]; exact hb z)
  have hind := hon.integrable_indicator (patchE_measurable E1 E2)
  refine hind.congr (ae_of_all _ fun z => ?_)
  by_cases hz' : z ∈ patchE (Ω := Ω) E1 E2
  · simp only [indicator_of_mem hz']
  · simp only [indicator_of_notMem hz', hz z hz']

/-- The `m × (m+1)` moment matrix `M_{j i} = ∫ φ_j ψ_i dμ`. -/
def momentMatrix (μ : Measure (ℝ × Ω)) {m : ℕ} (φ : Fin m → ℝ × Ω → ℝ) {E1 E2 : ℝ}
    (h : E1 < E2) : Matrix (Fin m) (Fin (m + 1)) ℝ :=
  fun j i => ∫ z, φ j z * psi h m i z.1 ∂μ

/-- **T3.** A nonzero kernel vector gives a nonzero smooth profile annihilating every retained
moment. -/
theorem moment_null_exists (μ : Measure (ℝ × Ω)) {m : ℕ} (φ : Fin m → ℝ × Ω → ℝ)
    {E1 E2 : ℝ} (h : E1 < E2) (hφ : ∀ j, IntegrableOn (φ j) (patchE E1 E2) μ) :
    ∃ c : Fin (m + 1) → ℝ, c ≠ 0 ∧ (∃ E0 ∈ Ioo E1 E2, qOf h m c E0 ≠ 0) ∧
      ∀ j, Integrable (fun z => φ j z * qOf h m c z.1) μ ∧
        ∫ z, φ j z * qOf h m c z.1 ∂μ = 0 := by
  classical
  have hker : LinearMap.ker (Matrix.mulVecLin (momentMatrix μ φ h)) ≠ ⊥ :=
    LinearMap.ker_ne_bot_of_finrank_lt (by simp)
  obtain ⟨c, hc, hc0⟩ := (Submodule.ne_bot_iff _).1 hker
  have hMc : ∀ j, ∑ i, momentMatrix μ φ h j i * c i = 0 := by
    intro j
    have := congrFun (LinearMap.mem_ker.1 hc) j
    simpa [Matrix.mulVecLin_apply, Matrix.mulVec, dotProduct] using this
  have hpsi_int : ∀ j i, Integrable (fun z => φ j z * psi h m i z.1) μ := fun j i =>
    integrable_mul_patch μ (φ j) (psi h m i) (hφ j) (psi_continuous h m i).measurable
      (K := 1) (fun E => by
        rw [abs_of_nonneg (psi_nonneg h m i E)]; exact psi_le_one h m i E)
      (fun E hE => psi_eq_zero_outside h m i fun h' => hE (Ioo_subset_Icc_self h'))
  refine ⟨c, hc0, ?_, fun j => ⟨?_, ?_⟩⟩
  · obtain ⟨i, hi⟩ : ∃ i, c i ≠ 0 := by
      by_contra hall
      push_neg at hall
      exact hc0 (funext hall)
    exact ⟨cellCenter E1 E2 m i, center_mem_Ioo h m i, by rw [qOf_center]; exact hi⟩
  · exact integrable_mul_patch μ (φ j) (qOf h m c) (hφ j)
      (qOf_contDiff h m c).continuous.measurable (qOf_abs_le h m c)
      (fun E hE => qOf_eq_zero_of_notMem_Icc h m c hE)
  · have hsum : (fun z => φ j z * qOf h m c z.1) =
        fun z => ∑ i, c i * (φ j z * psi h m i z.1) := by
      funext z
      unfold qOf
      rw [Finset.mul_sum]
      exact Finset.sum_congr rfl fun i _ => by ring
    rw [hsum, integral_finsetSum _ (fun i _ => (hpsi_int j i).const_mul (c i))]
    simp_rw [integral_const_mul]
    rw [← hMc j]
    exact Finset.sum_congr rfl fun i _ => mul_comm _ _

end Moments

/-! ## Momentum-space lift -/

/-- **T3b.** The energy profile lifts to a C^∞ compactly supported function on momentum space
`ℝ³`, supported in the positive shell `E1 ≤ ‖p‖ ≤ E2`. -/
theorem momentum_lift (q : ℝ → ℝ) {E1 E2 : ℝ} (hq : ContDiff ℝ ((⊤ : ℕ∞) : WithTop ℕ∞) q)
    (hE1 : 0 < E1) (hz : ∀ E ∉ Icc E1 E2, q E = 0) :
    ContDiff ℝ ((⊤ : ℕ∞) : WithTop ℕ∞) (fun p : EuclideanSpace ℝ (Fin 3) => q ‖p‖) ∧
    HasCompactSupport (fun p : EuclideanSpace ℝ (Fin 3) => q ‖p‖) ∧
    ∀ p : EuclideanSpace ℝ (Fin 3), q ‖p‖ ≠ 0 → E1 ≤ ‖p‖ ∧ ‖p‖ ≤ E2 := by
  have hsupp : ∀ p : EuclideanSpace ℝ (Fin 3), q ‖p‖ ≠ 0 → E1 ≤ ‖p‖ ∧ ‖p‖ ≤ E2 := by
    intro p hp
    by_contra hc
    exact hp (hz _ hc)
  refine ⟨?_, ?_, hsupp⟩
  · rw [contDiff_iff_contDiffAt]
    intro p
    by_cases hp : p = 0
    · subst hp
      have hev : (fun p : EuclideanSpace ℝ (Fin 3) => q ‖p‖) =ᶠ[𝓝 0] fun _ => 0 := by
        filter_upwards [Metric.ball_mem_nhds (0 : EuclideanSpace ℝ (Fin 3)) hE1] with p hp
        apply hz
        rw [mem_ball_zero_iff] at hp
        intro hmem
        exact absurd hmem.1 (not_le.2 hp)
      exact contDiffAt_const.congr_of_eventuallyEq hev
    · exact hq.comp_contDiffAt p (contDiffAt_norm ℝ hp)
  · refine HasCompactSupport.intro (isCompact_closedBall (0 : EuclideanSpace ℝ (Fin 3)) E2) ?_
    intro p hp
    by_contra hne
    exact hp (mem_closedBall_zero_iff.2 (hsupp p hne).2)

/-! ## Statistics helpers -/

theorem mem_dom_of_lt (s : Stat) {y Fv : ℝ} (hy : 0 < y) (hyF : y < Fv) (hF : Fv ∈ cdom s) :
    y ∈ dom s := by
  cases s
  · exact hy
  · exact hy
  · exact ⟨hy, lt_of_lt_of_le hyF hF.2⟩

theorem hS'_continuousOn (s : Stat) : ContinuousOn (hS' s) (dom s) := by
  intro y hy
  obtain ⟨h0, h1⟩ := dom_pos s hy
  apply ContinuousAt.continuousWithinAt
  unfold hS'
  apply ContinuousAt.log
  · exact continuousAt_id.div (continuousAt_const.add (continuousAt_const.mul continuousAt_id))
      h1.ne'
  · exact (div_pos h0 h1).ne'

theorem hess_pos (s : Stat) {y : ℝ} (hy : y ∈ dom s) : 0 < hess s y := by
  obtain ⟨h0, h1⟩ := dom_pos s hy
  unfold hess
  exact one_div_pos.2 (mul_pos h0 h1)

/-! ## Main counterexample on a general measure -/

section Main

variable {Ω : Type*} [MeasurableSpace Ω]

/-- **T4b.** Absolute retained moments are unchanged when `φ g` is integrable. -/
theorem moments_equal (μ : Measure (ℝ × Ω)) (φ : ℝ × Ω → ℝ) (g q : ℝ → ℝ) (a : ℝ)
    (hφg : Integrable (fun z => φ z * g z.1) μ) (hφq : Integrable (fun z => φ z * q z.1) μ)
    (h0 : ∫ z, φ z * q z.1 ∂μ = 0) (n : ℕ) (x : ℝ) :
    ∫ z, φ z * family g q a n x z ∂μ = ∫ z, φ z * g z.1 ∂μ := by
  have hfun : (fun z => φ z * family g q a n x z) =
      fun z => φ z * g z.1 + (a * Real.sin ((n : ℝ) * x)) * (φ z * q z.1) := by
    funext z; simp only [family]; ring
  rw [hfun, integral_add hφg (hφq.const_mul _), integral_const_mul, h0, mul_zero, add_zero]

/-- **T4c.** Differentiating the observable integral in `x` (exact: the `x`-dependence is the
scalar `sin (n x)`). For a retained kernel the right side vanishes. -/
theorem observable_derivative (μ : Measure (ℝ × Ω)) (K : ℝ × Ω → ℝ) (g q : ℝ → ℝ) (a : ℝ)
    (n : ℕ) (x : ℝ) :
    HasDerivAt (fun t => ∫ z, K z * (family g q a n t z - g z.1) ∂μ)
      (a * n * Real.cos (n * x) * ∫ z, K z * q z.1 ∂μ) x := by
  have hfun : (fun t => ∫ z, K z * (family g q a n t z - g z.1) ∂μ) =
      fun t => a * Real.sin ((n : ℝ) * t) * ∫ z, K z * q z.1 ∂μ := by
    funext t
    rw [← integral_const_mul]
    congr 1
    funext z
    simp only [family]
    ring
  rw [hfun]
  have hd := ((CAS12C04.hasDerivAt_sin_frequency (n : ℝ) x).const_mul a).mul_const
    (∫ z, K z * q z.1 ∂μ)
  convert hd using 1
  ring

/-- **T4.** One admissible family, fixed retained moments, uniform static divergence, and
`∂_x f_n(0, z) = a n q(z.1)`. -/
theorem moment_null_counterexample (μ : Measure (ℝ × Ω)) (s : Stat) {m : ℕ}
    (φ : Fin m → ℝ × Ω → ℝ) (g F : ℝ → ℝ) {E1 E2 : ℝ} (hE1 : 0 < E1) (hE12 : E1 < E2)
    (hμ0 : μ {z | z.1 ≤ 0} = 0) (hμP : μ (patchE E1 E2) ≠ ⊤)
    (hφ : ∀ j, IntegrableOn (φ j) (patchE E1 E2) μ)
    (hgm : Measurable g) (hgc : ContinuousOn g (Icc E1 E2)) (hFc : ContinuousOn F (Icc E1 E2))
    (hgdom : ∀ E, 0 < E → g E ∈ dom s) (hgF : ∀ E, 0 < E → g E ≤ F E)
    (hFcdom : ∀ E, 0 < E → F E ∈ cdom s) (hslack : ∀ E ∈ Icc E1 E2, g E < F E) :
    ∃ q : ℝ → ℝ, ∃ a B : ℝ,
      ContDiff ℝ ((⊤ : ℕ∞) : WithTop ℕ∞) q ∧ HasCompactSupport q ∧ tsupport q ⊆ Icc E1 E2 ∧
      (∃ E0 ∈ Ioo E1 E2, q E0 ≠ 0) ∧
      (∀ j, Integrable (fun z => φ j z * q z.1) μ ∧ ∫ z, φ j z * q z.1 ∂μ = 0) ∧
      0 < a ∧ 0 ≤ B ∧
      ∀ (n : ℕ) (x : ℝ),
        Admissible (Ω := Ω) s F (family g q a n x) ∧
        (∀ z : ℝ × Ω, 0 < z.1 → family g q a n x z ∈ dom s) ∧
        (∀ j, ∫ z, φ j z * (family g q a n x z - g z.1) ∂μ = 0) ∧
        Dext μ (hS s) (hS' s) (family g q a n x) (fun z => g z.1) ≤ ENNReal.ofReal B ∧
        Dfin μ (hS s) (hS' s) (family g q a n x) (fun z => g z.1) ≤ B ∧
        ∀ z, HasDerivAt (fun t => family g q a n t z) (a * n * q z.1) 0 := by
  -- the moment-null profile
  obtain ⟨c, -, hne, hmomc⟩ := moment_null_exists μ φ hE12 hφ
  obtain ⟨hqcd, hqcs, hqts, hqb, -⟩ := q_props hE12 m c
  set q := qOf hE12 m c with hqdef
  have hqc : Continuous q := hqcd.continuous
  have hqm : Measurable q := hqc.measurable
  have hq0 : ∀ E ∉ Icc E1 E2, q E = 0 := fun E hE => qOf_eq_zero_of_notMem_Icc hE12 m c hE
  -- margin on the compact patch
  have hpatch_pos : ∀ E ∈ Icc E1 E2, 0 < E := fun E hE => lt_of_lt_of_le hE1 hE.1
  have hd : ContinuousOn (fun E => min (g E) (F E - g E)) (Icc E1 E2) := hgc.min (hFc.sub hgc)
  obtain ⟨Es, hEs, hmin⟩ := isCompact_Icc.exists_isMinOn (nonempty_Icc.2 hE12.le) hd
  set δ := min (g Es) (F Es - g Es) with hδdef
  have hδ : 0 < δ :=
    lt_min (dom_pos s (hgdom Es (hpatch_pos Es hEs))).1 (sub_pos.2 (hslack Es hEs))
  have hδg : ∀ E ∈ Icc E1 E2, δ ≤ g E := fun E hE => (hmin hE).trans (min_le_left _ _)
  have hδF : ∀ E ∈ Icc E1 E2, δ ≤ F E - g E := fun E hE => (hmin hE).trans (min_le_right _ _)
  -- amplitude chosen before n
  set Q := ∑ i, |c i| + 1 with hQdef
  have hQ : 0 < Q := by positivity
  have hqQ : ∀ E, |q E| ≤ Q := fun E => by have := hqb E; linarith
  obtain ⟨a, ha, haQ⟩ : ∃ a : ℝ, 0 < a ∧ a * Q = δ / 2 :=
    ⟨δ / (2 * Q), by positivity, by field_simp⟩
  have hamp : ∀ (n : ℕ) (x E : ℝ), |a * Real.sin ((n : ℝ) * x) * q E| ≤ δ / 2 := by
    intro n x E
    rw [abs_mul, abs_mul, abs_of_pos ha]
    have h1 := Real.abs_sin_le_one ((n : ℝ) * x)
    have h2 := hqQ E
    calc a * |Real.sin ((n : ℝ) * x)| * |q E| ≤ a * 1 * Q := by
          gcongr
      _ = δ / 2 := by rw [mul_one, haQ]
  -- pointwise admissibility and regular domain
  have key : ∀ (n : ℕ) (x : ℝ) (z : ℝ × Ω), 0 < z.1 →
      family g q a n x z ∈ dom s ∧ family g q a n x z ≤ F z.1 := by
    intro n x z hz
    by_cases hzP : z.1 ∈ Icc E1 E2
    · have hb := abs_le.1 (hamp n x z.1)
      have hg := hδg z.1 hzP
      have hF := hδF z.1 hzP
      have hlt : family g q a n x z < F z.1 := by simp only [family]; linarith
      refine ⟨mem_dom_of_lt s (by simp only [family]; linarith) hlt (hFcdom z.1 hz), hlt.le⟩
    · have hfz : family g q a n x z = g z.1 := by simp only [family, hq0 z.1 hzP, mul_zero, add_zero]
      rw [hfz]
      exact ⟨hgdom z.1 hz, hgF z.1 hz⟩
  have hpos_ae : ∀ᵐ z ∂μ, 0 < z.1 := by
    rw [ae_iff]
    simpa [not_lt] using hμ0
  -- uniform Bregman bound on the compact parameter set
  have hΦ : ContinuousOn
      (fun p : ℝ × ℝ => bregDens (hS s) (hS' s) (g p.1 + p.2 * q p.1) (g p.1))
      (Icc E1 E2 ×ˢ Icc (-a) a) := by
    have hg1 : ContinuousOn (fun p : ℝ × ℝ => g p.1) (Icc E1 E2 ×ˢ Icc (-a) a) :=
      hgc.comp continuousOn_fst fun p hp => hp.1
    have hu : ContinuousOn (fun p : ℝ × ℝ => g p.1 + p.2 * q p.1) (Icc E1 E2 ×ˢ Icc (-a) a) :=
      hg1.add (continuousOn_snd.mul (hqc.comp_continuousOn continuousOn_fst))
    have hh' : ContinuousOn (fun p : ℝ × ℝ => hS' s (g p.1)) (Icc E1 E2 ×ˢ Icc (-a) a) :=
      (hS'_continuousOn s).comp hg1 fun p hp => hgdom _ (hpatch_pos _ hp.1)
    unfold bregDens
    exact (((continuous_hS s).comp_continuousOn hu).sub
      ((continuous_hS s).comp_continuousOn hg1)).sub (hh'.mul (hu.sub hg1))
  obtain ⟨Mb, hMb⟩ := (isCompact_Icc.prod isCompact_Icc).exists_bound_of_continuousOn hΦ
  set B := max Mb 0 * (μ (patchE E1 E2)).toReal with hBdef
  have hB0 : 0 ≤ B := mul_nonneg (le_max_right _ _) ENNReal.toReal_nonneg
  have hDext : ∀ (n : ℕ) (x : ℝ),
      Dext μ (hS s) (hS' s) (family g q a n x) (fun z => g z.1) ≤ ENNReal.ofReal B := by
    intro n x
    unfold Dext
    calc ∫⁻ z, ENNReal.ofReal (bregDens (hS s) (hS' s) (family g q a n x z) (g z.1)) ∂μ
        ≤ ∫⁻ z, (patchE E1 E2).indicator (fun _ => ENNReal.ofReal (max Mb 0)) z ∂μ := by
          refine lintegral_mono fun z => ?_
          by_cases hz : z ∈ patchE (Ω := Ω) E1 E2
          · rw [indicator_of_mem hz]
            apply ENNReal.ofReal_le_ofReal
            have hT : a * Real.sin ((n : ℝ) * x) ∈ Icc (-a) a :=
              ⟨by nlinarith [Real.neg_one_le_sin ((n : ℝ) * x)],
                by nlinarith [Real.sin_le_one ((n : ℝ) * x)]⟩
            have hbd := hMb (z.1, a * Real.sin ((n : ℝ) * x)) ⟨hz, hT⟩
            simp only [Real.norm_eq_abs] at hbd
            show bregDens (hS s) (hS' s) (g z.1 + a * Real.sin ((n : ℝ) * x) * q z.1) (g z.1)
              ≤ max Mb 0
            linarith [le_abs_self (bregDens (hS s) (hS' s)
              (g z.1 + a * Real.sin ((n : ℝ) * x) * q z.1) (g z.1)), le_max_left Mb 0]
          · rw [indicator_of_notMem hz]
            have h0 : q z.1 = 0 := hq0 z.1 hz
            show ENNReal.ofReal (bregDens (hS s) (hS' s)
              (g z.1 + a * Real.sin ((n : ℝ) * x) * q z.1) (g z.1)) ≤ 0
            rw [h0, mul_zero, add_zero]
            simp [bregDens]
      _ = ENNReal.ofReal (max Mb 0) * μ (patchE E1 E2) :=
          lintegral_indicator_const (patchE_measurable E1 E2) _
      _ = ENNReal.ofReal B := by
          rw [hBdef, ENNReal.ofReal_mul (le_max_right _ _), ENNReal.ofReal_toReal hμP]
  have hfm : ∀ (n : ℕ) (x : ℝ), Measurable (family (Ω := Ω) g q a n x) := fun n x =>
    (hgm.comp measurable_fst).add (measurable_const.mul (hqm.comp measurable_fst))
  refine ⟨q, a, B, hqcd, hqcs, hqts, hne, hmomc, ha, hB0, fun n x => ⟨?_, ?_, ?_, hDext n x, ?_, ?_⟩⟩
  · exact fun z hz => ⟨dom_subset_cdom s (key n x z hz).1, (key n x z hz).2⟩
  · exact fun z hz => (key n x z hz).1
  · intro j
    have hfun : (fun z => φ j z * (family g q a n x z - g z.1)) =
        fun z => (a * Real.sin ((n : ℝ) * x)) * (φ j z * q z.1) := by
      funext z; simp only [family]; ring
    rw [hfun, integral_const_mul, (hmomc j).2, mul_zero]
  · have hfd : ∀ᵐ z ∂μ, family g q a n x z ∈ cdom s := by
      filter_upwards [hpos_ae] with z hz using dom_subset_cdom s (key n x z hz).1
    have hgd : ∀ᵐ z ∂μ, (fun z : ℝ × Ω => g z.1) z ∈ dom s := by
      filter_upwards [hpos_ae] with z hz using hgdom z.1 hz
    exact (finite_budget_stat μ s (family g q a n x) (fun z => g z.1) (hfm n x)
      (hgm.comp measurable_fst) hfd hgd hB0 (hDext n x)).2.2
  · intro z
    have hd := CAS12C04.hasDerivAt_constant_q (fun _ => g z.1) 0 a (n : ℝ) (q z.1) 0
      (hasDerivAt_const _ _)
    refine hd.congr_deriv ?_
    simp

end Main

end G12E
