import CAS06Bundles

/-!
# G06-A: actual local ODE solution of the TOV system on the open domain

Recovered source (PR #477, commit `1a375536`,
`CAS-06/codex_only_continuation_20261004/adopted_successor_v1/ADMITTED_INPUTS.json`,
`definitions.C01`):

* metric `g = diag(-exp(2ν), 1/F, r², r² sin²θ)`, `F = 1 - 2m/r - Λ r²/3`;
* TOV system `m' = κ r² ε / 2`, `ν' = (m + κ α ε r³/2 - Λ r³/3)/(r² F)`,
  `ε' = -(1+α) ε ν' / α`;
* fixed causal EOS `p = α ε`, `0 < α < 1`, `κ > 0`;
* domain `r > 0, F > 0, ε > 0` (no `r = 0`, `F = 0`, `α = 0` member).

The autonomous field below carries `r` as a state variable with `r' = 1`, so the
non-autonomous system is solved by Mathlib's Picard–Lindelöf theorem for a `C¹`
autonomous field.  No global / regular-centre statement is made.
-/

namespace G06ATOV
noncomputable section
open Filter Topology Set

/-- State `(r, m, ν, ε)`. -/
abbrev State := ℝ × ℝ × ℝ × ℝ

def lapse (Λ r m : ℝ) : ℝ := 1 - 2 * m / r - Λ * r ^ 2 / 3

def nuRHS (κ Λ α r m ε : ℝ) : ℝ :=
  (m + (κ / 2) * ((α * ε) * r ^ 3) - (Λ / 3) * r ^ 3) / (r ^ 2 * lapse Λ r m)

/-- autonomous form of the TOV system, independent variable carried as `r' = 1` -/
def tovField (κ Λ α : ℝ) (y : State) : State :=
  (1, κ * y.1 ^ 2 * y.2.2.2 / 2, nuRHS κ Λ α y.1 y.2.1 y.2.2.2,
    -(1 + α) * y.2.2.2 * nuRHS κ Λ α y.1 y.2.1 y.2.2.2 / α)

structure AdmissibleParams (κ α : ℝ) : Prop where
  kappa_pos : 0 < κ
  alpha_pos : 0 < α
  alpha_lt_one : α < 1

/-- T1 open admissible domain: `r > 0`, `F > 0`, `ε > 0` (strict). -/
def TOVDomain (Λ : ℝ) (y : State) : Prop :=
  0 < y.1 ∧ 0 < lapse Λ y.1 y.2.1 ∧ 0 < y.2.2.2

def IsTOVSolutionOn (κ Λ α : ℝ) (m ν ε : ℝ → ℝ) (I : Set ℝ) : Prop :=
  ∀ r ∈ I, TOVDomain Λ (r, m r, ν r, ε r) ∧
    HasDerivAt m (κ * r ^ 2 * ε r / 2) r ∧
    HasDerivAt ν (CAS06Adopted.tovNuFunction m (fun s => α * ε s)
      (CAS06Adopted.massLapse m Λ) κ Λ r) r ∧
    HasDerivAt ε (-(1 + α) * ε r * CAS06Adopted.tovNuFunction m (fun s => α * ε s)
      (CAS06Adopted.massLapse m Λ) κ Λ r / α) r

/-! ## Faithfulness bridges to the accepted CAS-06 definitions -/

theorem lapse_eq_massLapse (m : ℝ → ℝ) (Λ r : ℝ) :
    lapse Λ r (m r) = CAS06Adopted.massLapse m Λ r := rfl

theorem nuRHS_eq_tovNuFunction (m ε : ℝ → ℝ) (κ Λ α r : ℝ) :
    nuRHS κ Λ α r (m r) (ε r) =
      CAS06Adopted.tovNuFunction m (fun s => α * ε s)
        (CAS06Adopted.massLapse m Λ) κ Λ r := rfl

/-! ## T1: open domain -/

theorem T1_isOpen_domain (Λ : ℝ) : IsOpen {y : State | TOVDomain Λ y} := by
  refine isOpen_iff_mem_nhds.2 fun y hy => ?_
  obtain ⟨h1, h2, h3⟩ := hy
  have c1 : ContinuousAt (fun z : State => z.1) y := continuous_fst.continuousAt
  have cm : ContinuousAt (fun z : State => z.2.1) y := by fun_prop
  have c2 : ContinuousAt (fun z : State => lapse Λ z.1 z.2.1) y := by
    unfold lapse
    exact (continuousAt_const.sub ((continuousAt_const.mul cm).div c1 h1.ne')).sub
      (by fun_prop)
  have c3 : ContinuousAt (fun z : State => z.2.2.2) y := by fun_prop
  filter_upwards [c1.preimage_mem_nhds (Ioi_mem_nhds h1),
    c2.preimage_mem_nhds (Ioi_mem_nhds h2),
    c3.preimage_mem_nhds (Ioi_mem_nhds h3)] with z hz1 hz2 hz3
  exact ⟨hz1, hz2, hz3⟩

theorem T1_excludes_center {Λ : ℝ} {y : State} (h : y.1 = 0) : ¬ TOVDomain Λ y :=
  fun hy => (ne_of_gt hy.1) h

theorem T1_excludes_horizon {Λ : ℝ} {y : State} (h : lapse Λ y.1 y.2.1 = 0) :
    ¬ TOVDomain Λ y :=
  fun hy => (ne_of_gt hy.2.1) h

theorem T1_excludes_nonpositive_density {Λ : ℝ} {y : State} (h : y.2.2.2 ≤ 0) :
    ¬ TOVDomain Λ y :=
  fun hy => (not_lt.2 h) hy.2.2

theorem T1_excludes_dust {κ α : ℝ} (h : AdmissibleParams κ α) : α ≠ 0 :=
  h.alpha_pos.ne'

theorem T1_denominator_pos {Λ : ℝ} {y : State} (h : TOVDomain Λ y) :
    0 < y.1 ^ 2 * lapse Λ y.1 y.2.1 :=
  mul_pos (pow_pos h.1 2) h.2.1

/-! ## T2: smoothness and local Lipschitz -/

theorem contDiffAt_lapse (n : ℕ∞) {Λ : ℝ} {y : State} (hr : y.1 ≠ 0) :
    ContDiffAt ℝ n (fun z : State => lapse Λ z.1 z.2.1) y := by
  unfold lapse
  have c1 : ContDiffAt ℝ n (fun z : State => z.1) y := by fun_prop
  have cm : ContDiffAt ℝ n (fun z : State => 2 * z.2.1) y := by fun_prop
  exact (contDiffAt_const.sub (cm.div c1 hr)).sub (by fun_prop)

theorem contDiffAt_nuRHS (n : ℕ∞) {κ Λ α : ℝ} {y : State} (hy : TOVDomain Λ y) :
    ContDiffAt ℝ n (fun z : State => nuRHS κ Λ α z.1 z.2.1 z.2.2.2) y := by
  unfold nuRHS
  have hnum : ContDiffAt ℝ n (fun z : State =>
      z.2.1 + (κ / 2) * ((α * z.2.2.2) * z.1 ^ 3) - (Λ / 3) * z.1 ^ 3) y := by
    fun_prop
  have hden : ContDiffAt ℝ n (fun z : State => z.1 ^ 2 * lapse Λ z.1 z.2.1) y :=
    (by fun_prop : ContDiffAt ℝ n (fun z : State => z.1 ^ 2) y).mul
      (contDiffAt_lapse n hy.1.ne')
  exact hnum.div hden (T1_denominator_pos hy).ne'

theorem T2_contDiffAt (n : ℕ∞) {κ Λ α : ℝ} (hα : α ≠ 0) {y : State}
    (hy : TOVDomain Λ y) : ContDiffAt ℝ n (tovField κ Λ α) y := by
  have hν := contDiffAt_nuRHS (κ := κ) (α := α) n hy
  have hm : ContDiffAt ℝ n (fun z : State => κ * z.1 ^ 2 * z.2.2.2 / 2) y := by
    fun_prop
  have he : ContDiffAt ℝ n (fun z : State =>
      -(1 + α) * z.2.2.2 * nuRHS κ Λ α z.1 z.2.1 z.2.2.2 / α) y :=
    ((by fun_prop : ContDiffAt ℝ n (fun z : State => -(1 + α) * z.2.2.2) y).mul hν).div_const
      α
  have _hα := hα
  exact contDiffAt_const.prodMk (hm.prodMk (hν.prodMk he))

theorem T2_locally_lipschitz {κ Λ α : ℝ} (hα : α ≠ 0) {y : State}
    (hy : TOVDomain Λ y) :
    ∃ K : NNReal, ∃ U ∈ 𝓝 y, LipschitzOnWith K (tovField κ Λ α) U :=
  (T2_contDiffAt 1 hα hy).exists_lipschitzOnWith

/-! ## Generic local uniqueness for a `C¹` autonomous field along curves in a set -/

theorem autonomous_unique_on_Ioo {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    {V : E → E} {D : Set E} (hV : ∀ y ∈ D, ContDiffAt ℝ 1 V y)
    {a b t0 : ℝ} (ht0 : t0 ∈ Ioo a b) {Y₁ Y₂ : ℝ → E}
    (h₁ : ∀ t ∈ Ioo a b, HasDerivAt Y₁ (V (Y₁ t)) t ∧ Y₁ t ∈ D)
    (h₂ : ∀ t ∈ Ioo a b, HasDerivAt Y₂ (V (Y₂ t)) t ∧ Y₂ t ∈ D)
    (heq : Y₁ t0 = Y₂ t0) : EqOn Y₁ Y₂ (Ioo a b) := by
  have hloc : ∀ t ∈ Ioo a b, Y₁ t = Y₂ t → Y₁ =ᶠ[𝓝 t] Y₂ := by
    intro t ht he
    obtain ⟨K, U, hU, hL⟩ := (hV _ (h₁ t ht).2).exists_lipschitzOnWith
    have hIoo : Ioo a b ∈ 𝓝 t := Ioo_mem_nhds ht.1 ht.2
    have hU2 : U ∈ 𝓝 (Y₂ t) := by rw [← he]; exact hU
    have hc1 : Y₁ ⁻¹' U ∈ 𝓝 t := (h₁ t ht).1.continuousAt.preimage_mem_nhds hU
    have hc2 : Y₂ ⁻¹' U ∈ 𝓝 t := (h₂ t ht).1.continuousAt.preimage_mem_nhds hU2
    refine ODE_solution_unique_of_eventually (v := fun _ => V) (s := fun _ => U) (K := K)
      (Filter.Eventually.of_forall fun _ => hL) ?_ ?_ he
    · filter_upwards [hIoo, hc1] with s hs hsU
      exact ⟨(h₁ s hs).1, hsU⟩
    · filter_upwards [hIoo, hc2] with s hs hsU
      exact ⟨(h₂ s hs).1, hsU⟩
  have hu : IsOpen {t : ℝ | ∀ᶠ s in 𝓝 t, Y₁ s = Y₂ s} := isOpen_setOf_eventually_nhds
  have hsub : Ioo a b ⊆ {t : ℝ | ∀ᶠ s in 𝓝 t, Y₁ s = Y₂ s} := by
    refine isPreconnected_Ioo.subset_of_closure_inter_subset hu
      ⟨t0, ht0, hloc t0 ht0 heq⟩ ?_
    rintro t ⟨htc, ht⟩
    apply hloc t ht
    by_contra hne
    have hcont : ContinuousAt (fun s => Y₁ s - Y₂ s) t :=
      (h₁ t ht).1.continuousAt.sub (h₂ t ht).1.continuousAt
    have hev : ∀ᶠ s in 𝓝 t, Y₁ s - Y₂ s ≠ 0 := hcont.eventually_ne (sub_ne_zero.2 hne)
    rw [mem_closure_iff_frequently] at htc
    obtain ⟨s, hs1, hs2⟩ := (htc.and_eventually hev).exists
    have hs1' : ∀ᶠ x in 𝓝 s, Y₁ x = Y₂ x := hs1
    exact hs2 (sub_eq_zero.2 hs1'.self_of_nhds)
  intro t ht
  have ht' : ∀ᶠ x in 𝓝 t, Y₁ x = Y₂ x := hsub ht
  exact ht'.self_of_nhds

/-! ## Lifting a TOV solution triple to a curve of the autonomous field -/

def lift (m ν ε : ℝ → ℝ) (t : ℝ) : State := (t, m t, ν t, ε t)

theorem lift_hasDerivAt {κ Λ α : ℝ} {m ν ε : ℝ → ℝ} {I : Set ℝ}
    (hsol : IsTOVSolutionOn κ Λ α m ν ε I) {t : ℝ} (ht : t ∈ I) :
    HasDerivAt (lift m ν ε) (tovField κ Λ α (lift m ν ε t)) t := by
  obtain ⟨_, hm, hν, hε⟩ := hsol t ht
  exact (hasDerivAt_id' t).prodMk (hm.prodMk (hν.prodMk hε))

theorem hasDerivAt_fst' {F G : Type*} [NormedAddCommGroup F] [NormedSpace ℝ F]
    [NormedAddCommGroup G] [NormedSpace ℝ G] {f : ℝ → F × G} {f' : F × G} {t : ℝ}
    (h : HasDerivAt f f' t) : HasDerivAt (fun s => (f s).1) f'.1 t :=
  (ContinuousLinearMap.fst ℝ F G).hasFDerivAt.comp_hasDerivAt t h

theorem hasDerivAt_snd' {F G : Type*} [NormedAddCommGroup F] [NormedSpace ℝ F]
    [NormedAddCommGroup G] [NormedSpace ℝ G] {f : ℝ → F × G} {f' : F × G} {t : ℝ}
    (h : HasDerivAt f f' t) : HasDerivAt (fun s => (f s).2) f'.2 t :=
  (ContinuousLinearMap.snd ℝ F G).hasFDerivAt.comp_hasDerivAt t h

/-! ## T3: local existence -/

theorem T3_local_existence {κ Λ α : ℝ} (hp : AdmissibleParams κ α)
    {r0 m0 ν0 ε0 : ℝ} (hdat : TOVDomain Λ (r0, m0, ν0, ε0)) :
    ∃ δ > 0, ∃ m ν ε : ℝ → ℝ, m r0 = m0 ∧ ν r0 = ν0 ∧ ε r0 = ε0 ∧
      IsTOVSolutionOn κ Λ α m ν ε (Set.Ioo (r0 - δ) (r0 + δ)) := by
  set V := tovField κ Λ α with hVdef
  have hV : ContDiffAt ℝ 1 V (r0, m0, ν0, ε0) :=
    T2_contDiffAt 1 (T1_excludes_dust hp) hdat
  obtain ⟨Y, hY0, ε1, hε1, hY⟩ :=
    hV.exists_forall_mem_closedBall_exists_eq_forall_mem_Ioo_hasDerivAt₀ r0
  have hr0mem : r0 ∈ Ioo (r0 - ε1) (r0 + ε1) := ⟨by linarith, by linarith⟩
  -- the carried radius equals the independent variable
  have hfst : EqOn (fun t => (Y t).1) id (Ioo (r0 - ε1) (r0 + ε1)) := by
    refine ODE_solution_unique_of_mem_Ioo (v := fun _ _ => (1 : ℝ))
      (s := fun _ => univ) (K := 0) (fun _ _ => (LipschitzWith.const (1 : ℝ)).lipschitzOnWith)
      hr0mem ?_ ?_ ?_
    · intro t ht
      exact ⟨hasDerivAt_fst' (hY t ht), mem_univ _⟩
    · intro t _
      exact ⟨hasDerivAt_id t, mem_univ _⟩
    · simp [hY0]
  -- the solution stays in the open domain near r0
  have hD : {y : State | TOVDomain Λ y} ∈ 𝓝 (Y r0) := by
    rw [hY0]; exact (T1_isOpen_domain Λ).mem_nhds hdat
  have hYc : ContinuousAt Y r0 := (hY r0 hr0mem).continuousAt
  obtain ⟨δ2, hδ2, hball⟩ := Metric.mem_nhds_iff.1 (hYc.preimage_mem_nhds hD)
  refine ⟨min ε1 δ2, lt_min hε1 hδ2, fun t => (Y t).2.1, fun t => (Y t).2.2.1,
    fun t => (Y t).2.2.2, ?_, ?_, ?_, ?_⟩
  · simp [hY0]
  · simp [hY0]
  · simp [hY0]
  intro t ht
  have ht1 : t ∈ Ioo (r0 - ε1) (r0 + ε1) :=
    ⟨by linarith [ht.1, min_le_left ε1 δ2], by linarith [ht.2, min_le_left ε1 δ2]⟩
  have ht2 : t ∈ Metric.ball r0 δ2 := by
    rw [Metric.mem_ball, Real.dist_eq, abs_lt]
    constructor <;> linarith [ht.1, ht.2, min_le_right ε1 δ2]
  have hYt : (Y t).1 = t := hfst ht1
  have hdom : TOVDomain Λ (Y t) := hball ht2
  have hd := hY t ht1
  have hd2 := hasDerivAt_snd' hd
  have hdm := hasDerivAt_fst' hd2
  have hd3 := hasDerivAt_snd' hd2
  have hdν := hasDerivAt_fst' hd3
  have hdε := hasDerivAt_snd' hd3
  refine ⟨?_, ?_, ?_, ?_⟩
  · have hE : Y t = (t, (Y t).2.1, (Y t).2.2.1, (Y t).2.2.2) := Prod.ext hYt rfl
    rw [hE] at hdom; exact hdom
  · refine hdm.congr_deriv ?_
    show κ * (Y t).1 ^ 2 * (Y t).2.2.2 / 2 = _
    rw [hYt]
  · refine hdν.congr_deriv ?_
    show nuRHS κ Λ α (Y t).1 (Y t).2.1 (Y t).2.2.2 = _
    rw [hYt]
    rfl
  · refine hdε.congr_deriv ?_
    show -(1 + α) * (Y t).2.2.2 * nuRHS κ Λ α (Y t).1 (Y t).2.1 (Y t).2.2.2 / α = _
    rw [hYt]
    rfl

/-! ## T4: uniqueness -/

theorem T4_uniqueness {κ Λ α : ℝ} (hp : AdmissibleParams κ α) {a b r0 : ℝ}
    (hr0 : r0 ∈ Set.Ioo a b) {m₁ ν₁ ε₁ m₂ ν₂ ε₂ : ℝ → ℝ}
    (h₁ : IsTOVSolutionOn κ Λ α m₁ ν₁ ε₁ (Set.Ioo a b))
    (h₂ : IsTOVSolutionOn κ Λ α m₂ ν₂ ε₂ (Set.Ioo a b))
    (hm : m₁ r0 = m₂ r0) (hν : ν₁ r0 = ν₂ r0) (hε : ε₁ r0 = ε₂ r0) :
    Set.EqOn m₁ m₂ (Set.Ioo a b) ∧ Set.EqOn ν₁ ν₂ (Set.Ioo a b) ∧
      Set.EqOn ε₁ ε₂ (Set.Ioo a b) := by
  have hV : ∀ y ∈ {y : State | TOVDomain Λ y}, ContDiffAt ℝ 1 (tovField κ Λ α) y :=
    fun y hy => T2_contDiffAt 1 (T1_excludes_dust hp) hy
  have hEq := autonomous_unique_on_Ioo hV hr0
    (fun t ht => ⟨lift_hasDerivAt h₁ ht, (h₁ t ht).1⟩)
    (fun t ht => ⟨lift_hasDerivAt h₂ ht, (h₂ t ht).1⟩)
    (by simp [lift, hm, hν, hε])
  refine ⟨fun t ht => ?_, fun t ht => ?_, fun t ht => ?_⟩
  · exact congrArg (fun y : State => y.2.1) (hEq ht)
  · exact congrArg (fun y : State => y.2.2.1) (hEq ht)
  · exact congrArg (fun y : State => y.2.2.2) (hEq ht)

/-! ## T5: Einstein equations on the actual solution -/

theorem solution_bundle_inputs {κ Λ α : ℝ}
    {m ν ε : ℝ → ℝ} {I : Set ℝ} (hI : IsOpen I)
    (hsol : IsTOVSolutionOn κ Λ α m ν ε I) {r : ℝ} (hr : r ∈ I) :
    (deriv ν =ᶠ[𝓝 r] CAS06Adopted.tovNuFunction m (fun s => α * ε s)
        (CAS06Adopted.massLapse m Λ) κ Λ) ∧
    ∃ Frr : ℝ, HasDerivAt (deriv (CAS06Adopted.massLapse m Λ)) Frr r := by
  have hIr : I ∈ 𝓝 r := hI.mem_nhds hr
  have hr0 : 0 < r := (hsol r hr).1.1
  refine ⟨?_, ?_⟩
  · filter_upwards [hIr] with s hs
    exact (hsol s hs).2.2.1.deriv
  · set G : ℝ → ℝ := fun s =>
      CAS06Adopted.massLapseJet (m s) (κ * s ^ 2 * ε s / 2) Λ s with hG
    have hpos : ∀ᶠ s in 𝓝 r, 0 < s := Ioi_mem_nhds hr0
    have hev : deriv (CAS06Adopted.massLapse m Λ) =ᶠ[𝓝 r] G := by
      filter_upwards [hIr, hpos] with s hs hs0
      exact (CAS06Adopted.massLapse_derivative (Λ := Λ) hs0.ne' (hsol s hs).2.1).deriv
    have hmd : DifferentiableAt ℝ m r := (hsol r hr).2.1.differentiableAt
    have hεd : DifferentiableAt ℝ ε r := (hsol r hr).2.2.2.differentiableAt
    have hGd : DifferentiableAt ℝ G r := by
      simp only [hG, CAS06Adopted.massLapseJet]
      have h1 : DifferentiableAt ℝ (fun s => 2 * (κ * s ^ 2 * ε s / 2)) r := by fun_prop
      have h2 : DifferentiableAt ℝ (fun s => 2 * m s) r := by fun_prop
      have h3 : DifferentiableAt ℝ (fun s : ℝ => s) r := differentiableAt_id
      have h4 : DifferentiableAt ℝ (fun s : ℝ => s ^ 2) r := by fun_prop
      exact (((h1.div h3 hr0.ne').neg).add (h2.div h4 (pow_ne_zero 2 hr0.ne'))).sub
        (by fun_prop)
    exact ⟨deriv G r, hGd.hasDerivAt.congr_of_eventuallyEq hev⟩

theorem T5_einstein_on_solution {κ Λ α : ℝ} (hp : AdmissibleParams κ α)
    {m ν ε : ℝ → ℝ} {I : Set ℝ} (hI : IsOpen I)
    (hsol : IsTOVSolutionOn κ Λ α m ν ε I) {r θ : ℝ} (hr : r ∈ I)
    (hθ0 : 0 < θ) (hθπ : θ < Real.pi) :
    CAS06Bundles.C01TOVEinstein ν m ε κ Λ α r θ := by
  obtain ⟨hνnear, Frr, hFrr⟩ := solution_bundle_inputs hI hsol hr
  obtain ⟨hdom, hm, hν, hε⟩ := hsol r hr
  exact (CAS06Bundles.C01_TOV_metric_bundle hdom.1 hdom.2.1 hdom.2.2 hp.alpha_pos
    hθ0 hθπ hm hε hν hνnear hFrr).2.1

theorem T5_riemann_on_solution {κ Λ α : ℝ} (hp : AdmissibleParams κ α)
    {m ν ε : ℝ → ℝ} {I : Set ℝ} (hI : IsOpen I)
    (hsol : IsTOVSolutionOn κ Λ α m ν ε I) {r θ : ℝ} (hr : r ∈ I)
    (hθ0 : 0 < θ) (hθπ : θ < Real.pi) :
    ∃ Frr : ℝ, HasDerivAt (deriv (CAS06Adopted.massLapse m Λ)) Frr r ∧
      CAS06Bundles.C01CoordinateRiemann ν (CAS06Adopted.massLapse m Λ) r θ
        (CAS06Bundles.C01TOVNuSecond m ε κ Λ α r) Frr := by
  obtain ⟨hνnear, Frr, hFrr⟩ := solution_bundle_inputs hI hsol hr
  obtain ⟨hdom, hm, hν, hε⟩ := hsol r hr
  exact ⟨Frr, hFrr, (CAS06Bundles.C01_TOV_metric_bundle hdom.1 hdom.2.1 hdom.2.2
    hp.alpha_pos hθ0 hθπ hm hε hν hνnear hFrr).1⟩

/-! ## Capstone -/

theorem G06A_capstone {κ Λ α : ℝ} (hp : AdmissibleParams κ α)
    {r0 m0 ν0 ε0 : ℝ} (hdat : TOVDomain Λ (r0, m0, ν0, ε0)) :
    ∃ δ > 0, ∃ m ν ε : ℝ → ℝ, m r0 = m0 ∧ ν r0 = ν0 ∧ ε r0 = ε0 ∧
      IsTOVSolutionOn κ Λ α m ν ε (Set.Ioo (r0 - δ) (r0 + δ)) ∧
      (∀ r ∈ Set.Ioo (r0 - δ) (r0 + δ), ∀ θ, 0 < θ → θ < Real.pi →
        CAS06Bundles.C01TOVEinstein ν m ε κ Λ α r θ) ∧
      (∀ m' ν' ε' : ℝ → ℝ,
        IsTOVSolutionOn κ Λ α m' ν' ε' (Set.Ioo (r0 - δ) (r0 + δ)) →
        m' r0 = m0 → ν' r0 = ν0 → ε' r0 = ε0 →
        Set.EqOn m' m (Set.Ioo (r0 - δ) (r0 + δ)) ∧
        Set.EqOn ν' ν (Set.Ioo (r0 - δ) (r0 + δ)) ∧
        Set.EqOn ε' ε (Set.Ioo (r0 - δ) (r0 + δ))) := by
  obtain ⟨δ, hδ, m, ν, ε, hm0, hν0, hε0, hsol⟩ := T3_local_existence hp hdat
  have hr0 : r0 ∈ Set.Ioo (r0 - δ) (r0 + δ) := ⟨by linarith, by linarith⟩
  refine ⟨δ, hδ, m, ν, ε, hm0, hν0, hε0, hsol, ?_, ?_⟩
  · intro r hr θ hθ0 hθπ
    exact T5_einstein_on_solution hp isOpen_Ioo hsol hr hθ0 hθπ
  · intro m' ν' ε' hsol' hm' hν' hε'
    exact T4_uniqueness hp hr0 hsol' hsol (hm'.trans hm0.symm) (hν'.trans hν0.symm)
      (hε'.trans hε0.symm)

end
end G06ATOV
