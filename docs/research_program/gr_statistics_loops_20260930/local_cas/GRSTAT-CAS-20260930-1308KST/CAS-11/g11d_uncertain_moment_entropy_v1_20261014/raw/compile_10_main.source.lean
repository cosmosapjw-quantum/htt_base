import Mathlib
import G11CWeightedEllipsoid

/-!
G11-D (GR-CAS-11): uncertain moment matching and measured entropy inputs, combined
conservatively.  Supplement TEFF_POSITIVE_BRIDGE (A6) (lines 108-116), acquisition
protocol (line 104), nested-improvement rule (line 106), photon envelope (A5)
(lines 93-102).  Targets are frozen in `../FROZEN_TARGETS.md`; sources in
`../SOURCE_RECOVERY.md`.

* D1: ∫ K δ = ∫ (K - c·φ) δ + c·Δm, with Δm NOT removed; the (A6) norm is the L²(W) norm.
* D2: deterministic residual bound ⊕ support function of a declared moment-error set;
  box support function; joint (all-channel) form e - BΔm ∈ (A4)-ellipsoid; exact
  matching (S = {0}) reduces to reviewed G11-C.
* D3: span enlargement decreases the distance; combination with a refined budget only
  under explicit common-envelope and nested-budget premises; discharge of the refined
  budget from reviewed `G11A.nested_budget` under its own exact-matching hypotheses.
* D4: input witnesses for W ((A5) ⇒ (A2), FD universal envelope, Planck instance on ν);
  negative control: no ε from a fixed reference plus matched moments; necessity of the
  support term.
* D5: coverage by the union bound over declared failure events (no independence).

Imported modules are used unchanged.
-/

open MeasureTheory Set Filter Topology Matrix
open scoped ENNReal

namespace G11D

open G11A G11B G11C

section General

variable {X : Type*} [MeasurableSpace X]

/-! ## Definitions -/

/-- Δm_a = ∫ φ_a (f - g) dμ: the TRUE retained-moment mismatch of the pair (f, g). -/
noncomputable def dm {m : ℕ} (μ : Measure X) (φ : Fin m → X → ℝ) (f g : X → ℝ) : Fin m → ℝ :=
  fun a => ∫ x, φ a x * (f x - g x) ∂μ

/-- Symmetric support function σ_S(c) = sup_{d ∈ S} |c · d| (used only under `BddAbove`). -/
noncomputable def suppAbs {m : ℕ} (S : Set (Fin m → ℝ)) (c : Fin m → ℝ) : ℝ :=
  sSup ((fun d => |c ⬝ᵥ d|) '' S)

/-- The per-moment box {d | |d_a| ≤ r_a ∀ a}. -/
def box {m : ℕ} (r : Fin m → ℝ) : Set (Fin m → ℝ) := {d | ∀ a, |d a| ≤ r a}

/-! ## D1: split identity without removing Δm -/

theorem moment_split (μ : Measure X) (W : X → ℝ) (hWm : Measurable W)
    (hWpos : ∀ᵐ x ∂μ, 0 < W x) (f g : X → ℝ) (hz : MemLp (zfun f g W) 2 (wmeas μ W))
    {m : ℕ} (φ : Fin m → X → ℝ) (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W))
    {k : X → ℝ} (hk : MemLp k 2 (wmeas μ W)) (c : Fin m → ℝ) :
    Integrable (fun x => (k x - ∑ a, c a * φ a x) * (f x - g x)) μ ∧
      ∫ x, k x * (f x - g x) ∂μ =
        ∫ x, (k x - ∑ a, c a * φ a x) * (f x - g x) ∂μ + c ⬝ᵥ dm μ φ f g ∧
      ∫ x, (k x - ∑ a, c a * φ a x) * (f x - g x) ∂μ =
        inner ℝ (hk.toLp k - ∑ a, c a • (hφ a).toLp (φ a)) (hz.toLp (zfun f g W)) := by
  have hkI := kernel_moment_integrable μ W hWm hWpos f g hz hk
  have hφI := fun a => kernel_moment_integrable μ W hWm hWpos f g hz (hφ a)
  have hfun : (fun x => (k x - ∑ a, c a * φ a x) * (f x - g x)) =
      fun x => k x * (f x - g x) - ∑ a, c a * (φ a x * (f x - g x)) := by
    funext x
    rw [sub_mul, Finset.sum_mul]
    congr 1
    exact Finset.sum_congr rfl fun a _ => by ring
  have hsumI : Integrable (fun x => ∑ a, c a * (φ a x * (f x - g x))) μ :=
    integrable_finsetSum _ fun a _ => (hφI a).1.const_mul (c a)
  have hI : Integrable (fun x => (k x - ∑ a, c a * φ a x) * (f x - g x)) μ := by
    rw [hfun]
    exact hkI.1.sub hsumI
  have hint : ∫ x, (k x - ∑ a, c a * φ a x) * (f x - g x) ∂μ =
      ∫ x, k x * (f x - g x) ∂μ - c ⬝ᵥ dm μ φ f g := by
    rw [hfun, integral_sub hkI.1 hsumI,
      integral_finsetSum _ fun a _ => (hφI a).1.const_mul (c a)]
    congr 1
    simp only [dotProduct, dm]
    exact Finset.sum_congr rfl fun a _ => integral_const_mul (c a) _
  have hlin : inner ℝ (hk.toLp k - ∑ a, c a • (hφ a).toLp (φ a)) (hz.toLp (zfun f g W)) =
      ∫ x, k x * (f x - g x) ∂μ - c ⬝ᵥ dm μ φ f g := by
    rw [inner_sub_left, sum_inner, ← hkI.2]
    congr 1
    simp only [dotProduct, dm]
    refine Finset.sum_congr rfl fun a _ => ?_
    rw [real_inner_smul_left, ← (hφI a).2]
  refine ⟨hI, by rw [hint]; ring, by rw [hint, hlin]⟩

theorem moment_split_budget (μ : Measure X) (s : Stat) (f g W : X → ℝ)
    (hf : Measurable f) (hg : Measurable g)
    (hfd : ∀ᵐ x ∂μ, f x ∈ cdom s) (hgd : ∀ᵐ x ∂μ, g x ∈ dom s)
    (hW : WEnvelope μ s W f g) {ε : ℝ} (hε0 : 0 ≤ ε)
    (hε : Dext μ (hS s) (hS' s) f g ≤ ENNReal.ofReal ε)
    {m : ℕ} (φ : Fin m → X → ℝ)
    (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W)) {k : X → ℝ} (hk : MemLp k 2 (wmeas μ W))
    (c : Fin m → ℝ) :
    Integrable (fun x => (k x - ∑ a, c a * φ a x) * (f x - g x)) μ ∧
      ∫ x, k x * (f x - g x) ∂μ =
        ∫ x, (k x - ∑ a, c a * φ a x) * (f x - g x) ∂μ + c ⬝ᵥ dm μ φ f g := by
  have hz := z_memLp μ s f g W hf hg hfd hgd hW hε0 hε
  obtain ⟨h1, h2, -⟩ := moment_split μ W hW.1 hW.2.1 f g hz φ hφ hk c
  exact ⟨h1, h2⟩

theorem coeFn_combo (ν : Measure X) {m : ℕ} (φ : Fin m → X → ℝ)
    (hφ : ∀ a, MemLp (φ a) 2 ν) (c : Fin m → ℝ) :
    ⇑(∑ a, c a • (hφ a).toLp (φ a)) =ᵐ[ν] fun x => ∑ a, c a * φ a x := by
  have key : ∀ t : Finset (Fin m),
      ⇑(∑ a ∈ t, c a • (hφ a).toLp (φ a)) =ᵐ[ν] fun x => ∑ a ∈ t, c a * φ a x := by
    intro t
    induction t using Finset.induction_on with
    | empty =>
      simp only [Finset.sum_empty]
      exact Lp.coeFn_zero
    | insert a t ha ih =>
      simp only [Finset.sum_insert ha]
      filter_upwards [Lp.coeFn_add (c a • (hφ a).toLp (φ a)) (∑ b ∈ t, c b • (hφ b).toLp (φ b)),
        Lp.coeFn_smul (c a) ((hφ a).toLp (φ a)), (hφ a).coeFn_toLp, ih] with x h1 h2 h3 h4
      rw [h1, Pi.add_apply, h2, Pi.smul_apply, h3, h4, smul_eq_mul]
  exact key Finset.univ

theorem combo_norm_sq (μ : Measure X) (W : X → ℝ) (hWm : Measurable W)
    (hW0 : ∀ᵐ x ∂μ, 0 ≤ W x) {m : ℕ} (φ : Fin m → X → ℝ)
    (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W)) {k : X → ℝ} (hk : MemLp k 2 (wmeas μ W))
    (c : Fin m → ℝ) :
    ‖hk.toLp k - ∑ a, c a • (hφ a).toLp (φ a)‖ ^ 2 =
      ∫ x, W x * (k x - ∑ a, c a * φ a x) ^ 2 ∂μ := by
  set v := hk.toLp k - ∑ a, c a • (hφ a).toLp (φ a) with hvdef
  have hv : ⇑v =ᵐ[wmeas μ W] fun x => k x - ∑ a, c a * φ a x := by
    filter_upwards [Lp.coeFn_sub (hk.toLp k) (∑ a, c a • (hφ a).toLp (φ a)), hk.coeFn_toLp,
      coeFn_combo (wmeas μ W) φ hφ c] with x h1 h2 h3
    rw [h1, Pi.sub_apply, h2, h3]
  have hcongr : (fun x => inner ℝ (v x) (v x)) =ᵐ[wmeas μ W]
      fun x => (k x - ∑ a, c a * φ a x) ^ 2 := by
    filter_upwards [hv] with x hx
    rw [hx, real_inner_apply, sq]
  rw [← real_inner_self_eq_norm_sq, L2.inner_def, integral_congr_ae hcongr,
    integral_wmeas μ W hWm hW0]

/-! ## D2: deterministic residual bound ⊕ support function -/

theorem uncertain_bound (μ : Measure X) (s : Stat) (f g W : X → ℝ)
    (hf : Measurable f) (hg : Measurable g)
    (hfd : ∀ᵐ x ∂μ, f x ∈ cdom s) (hgd : ∀ᵐ x ∂μ, g x ∈ dom s)
    (hW : WEnvelope μ s W f g) {ε : ℝ} (hε0 : 0 ≤ ε)
    (hε : Dext μ (hS s) (hS' s) f g ≤ ENNReal.ofReal ε)
    {m : ℕ} (φ : Fin m → X → ℝ)
    (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W)) {k : X → ℝ} (hk : MemLp k 2 (wmeas μ W))
    (S : Set (Fin m → ℝ)) (hS : dm μ φ f g ∈ S) (c : Fin m → ℝ) {σ : ℝ}
    (hσ : ∀ d ∈ S, |c ⬝ᵥ d| ≤ σ) :
    |∫ x, k x * (f x - g x) ∂μ| ≤
      Real.sqrt (2 * ε) * ‖hk.toLp k - ∑ a, c a • (hφ a).toLp (φ a)‖ + σ := by
  have hz := z_memLp μ s f g W hf hg hfd hgd hW hε0 hε
  have hzn := (z_norm_sq μ s f g W hf hg hfd hgd hW hε0 hε).2
  obtain ⟨-, h1, h2⟩ := moment_split μ W hW.1 hW.2.1 f g hz φ hφ hk c
  set z := hz.toLp (zfun f g W) with hzdef
  set v := hk.toLp k - ∑ a, c a • (hφ a).toLp (φ a) with hvdef
  have hzs : ‖z‖ ≤ Real.sqrt (2 * ε) := by
    have := Real.abs_le_sqrt hzn
    rwa [abs_norm] at this
  rw [h1, h2]
  calc |inner ℝ v z + c ⬝ᵥ dm μ φ f g| ≤ |inner ℝ v z| + |c ⬝ᵥ dm μ φ f g| := abs_add_le _ _
    _ ≤ ‖v‖ * ‖z‖ + σ := add_le_add (abs_real_inner_le_norm _ _) (hσ _ hS)
    _ ≤ ‖v‖ * Real.sqrt (2 * ε) + σ := by gcongr
    _ = Real.sqrt (2 * ε) * ‖v‖ + σ := by ring

theorem uncertain_bound_supp (μ : Measure X) (s : Stat) (f g W : X → ℝ)
    (hf : Measurable f) (hg : Measurable g)
    (hfd : ∀ᵐ x ∂μ, f x ∈ cdom s) (hgd : ∀ᵐ x ∂μ, g x ∈ dom s)
    (hW : WEnvelope μ s W f g) {ε : ℝ} (hε0 : 0 ≤ ε)
    (hε : Dext μ (hS s) (hS' s) f g ≤ ENNReal.ofReal ε)
    {m : ℕ} (φ : Fin m → X → ℝ)
    (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W)) {k : X → ℝ} (hk : MemLp k 2 (wmeas μ W))
    (S : Set (Fin m → ℝ)) (hS : dm μ φ f g ∈ S) :
    ∀ c : Fin m → ℝ, BddAbove ((fun d => |c ⬝ᵥ d|) '' S) →
      |∫ x, k x * (f x - g x) ∂μ| ≤
        Real.sqrt (2 * ε) * ‖hk.toLp k - ∑ a, c a • (hφ a).toLp (φ a)‖ + suppAbs S c := by
  intro c hb
  exact uncertain_bound μ s f g W hf hg hfd hgd hW hε0 hε φ hφ hk S hS c
    (fun d hd => le_csSup hb ⟨d, hd, rfl⟩)

theorem box_support {m : ℕ} (r : Fin m → ℝ) (hr : ∀ a, 0 ≤ r a) (c : Fin m → ℝ) :
    BddAbove ((fun d => |c ⬝ᵥ d|) '' box r) ∧ suppAbs (box r) c = ∑ a, |c a| * r a := by
  have hub : ∀ d ∈ box r, |c ⬝ᵥ d| ≤ ∑ a, |c a| * r a := by
    intro d hd
    calc |c ⬝ᵥ d| = |∑ a, c a * d a| := rfl
      _ ≤ ∑ a, |c a * d a| := Finset.abs_sum_le_sum_abs _ _
      _ ≤ ∑ a, |c a| * r a := Finset.sum_le_sum fun a _ => by
          rw [abs_mul]
          exact mul_le_mul_of_nonneg_left (hd a) (abs_nonneg _)
  have hbdd : BddAbove ((fun d => |c ⬝ᵥ d|) '' box r) := by
    refine ⟨∑ a, |c a| * r a, ?_⟩
    rintro _ ⟨d, hd, rfl⟩
    exact hub d hd
  have h0 : (0 : Fin m → ℝ) ∈ box r := fun a => by simpa using hr a
  refine ⟨hbdd, le_antisymm ?_ ?_⟩
  · refine csSup_le ⟨_, 0, h0, rfl⟩ ?_
    rintro _ ⟨d, hd, rfl⟩
    exact hub d hd
  · set dstar : Fin m → ℝ := fun a => if 0 ≤ c a then r a else -r a with hdstar
    have hmem : dstar ∈ box r := by
      intro a
      simp only [hdstar]
      split_ifs
      · rw [abs_of_nonneg (hr a)]
      · rw [abs_neg, abs_of_nonneg (hr a)]
    have hval : c ⬝ᵥ dstar = ∑ a, |c a| * r a := by
      simp only [dotProduct, hdstar]
      refine Finset.sum_congr rfl fun a _ => ?_
      split_ifs with h
      · rw [abs_of_nonneg h]
      · rw [abs_of_neg (not_le.1 h)]
        ring
    have hnn : 0 ≤ ∑ a, |c a| * r a :=
      Finset.sum_nonneg fun a _ => mul_nonneg (abs_nonneg _) (hr a)
    calc ∑ a, |c a| * r a = |c ⬝ᵥ dstar| := by rw [hval, abs_of_nonneg hnn]
      _ ≤ suppAbs (box r) c := le_csSup hbdd ⟨dstar, hmem, rfl⟩

theorem projection_coeffs_exist {m n : ℕ} (μ : Measure X) (W : X → ℝ) (φ : Fin m → X → ℝ)
    (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W)) (K : Fin n → X → ℝ)
    (hK : ∀ j, MemLp (K j) 2 (wmeas μ W)) :
    ∃ B : Matrix (Fin n) (Fin m) ℝ, ∀ j, ∑ b, B j b • (hφ b).toLp (φ b) =
      (retainedSpan μ W φ hφ).starProjection ((hK j).toLp (K j)) := by
  have h : ∀ j, ∃ cj : Fin m → ℝ, ∑ b, cj b • (hφ b).toLp (φ b) =
      (retainedSpan μ W φ hφ).starProjection ((hK j).toLp (K j)) := fun j =>
    (Submodule.mem_span_range_iff_exists_fun ℝ).1
      (starProj_mem (retainedSpan μ W φ hφ) ((hK j).toLp (K j)))
  choose B hB using h
  exact ⟨fun j b => B j b, hB⟩

theorem uncertain_joint (μ : Measure X) (s : Stat) (f g W : X → ℝ)
    (hf : Measurable f) (hg : Measurable g)
    (hfd : ∀ᵐ x ∂μ, f x ∈ cdom s) (hgd : ∀ᵐ x ∂μ, g x ∈ dom s)
    (hW : WEnvelope μ s W f g) {ε : ℝ} (hε0 : 0 ≤ ε)
    (hε : Dext μ (hS s) (hS' s) f g ≤ ENNReal.ofReal ε)
    {m n : ℕ} (φ : Fin m → X → ℝ)
    (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W)) (K : Fin n → X → ℝ)
    (hK : ∀ j, MemLp (K j) 2 (wmeas μ W)) (B : Matrix (Fin n) (Fin m) ℝ)
    (hB : ∀ j, ∑ b, B j b • (hφ b).toLp (φ b) =
      (retainedSpan μ W φ hφ).starProjection ((hK j).toLp (K j))) :
    (∀ a : Fin n → ℝ, |a ⬝ᵥ (evec μ K f g - B *ᵥ dm μ φ f g)| ≤
        Real.sqrt (2 * ε * (a ⬝ᵥ (gramR μ W φ hφ K hK *ᵥ a)))) ∧
      evec μ K f g - B *ᵥ dm μ φ f g ∈ LinearMap.range (gramR μ W φ hφ K hK).toLin' ∧
      (evec μ K f g - B *ᵥ dm μ φ f g) ⬝ᵥ
          (CAS11C02.spectralPinvMatrix (gramR μ W φ hφ K hK)
            (gramR_posSemidef μ W φ hφ K hK).isHermitian *ᵥ (evec μ K f g - B *ᵥ dm μ φ f g))
        ≤ 2 * ε := by
  have hz := z_memLp μ s f g W hf hg hfd hgd hW hε0 hε
  have hzn := (z_norm_sq μ s f g W hf hg hfd hgd hW hε0 hε).2
  set z := hz.toLp (zfun f g W) with hzdef
  have he' : ∀ j, (evec μ K f g - B *ᵥ dm μ φ f g) j =
      inner ℝ (residuals μ W φ hφ K hK j) z := by
    intro j
    simp only [Pi.sub_apply, residuals, inner_sub_left]
    rw [← hB j, sum_inner]
    congr 1
    · exact (kernel_moment_integrable μ W hW.1 hW.2.1 f g hz (hK j)).2
    · simp only [mulVec, dotProduct, dm]
      refine Finset.sum_congr rfl fun b _ => ?_
      rw [real_inner_smul_left, (kernel_moment_integrable μ W hW.1 hW.2.1 f g hz (hφ b)).2]
  set e' := evec μ K f g - B *ᵥ dm μ φ f g with he'def
  have hdot : ∀ a : Fin n → ℝ, a ⬝ᵥ e' =
      inner ℝ (∑ j, a j • residuals μ W φ hφ K hK j) z := by
    intro a
    rw [sum_inner, dotProduct]
    refine Finset.sum_congr rfl fun j _ => ?_
    rw [real_inner_smul_left, he' j]
  have hsq : ∀ a : Fin n → ℝ, (a ⬝ᵥ e') ^ 2 ≤ 2 * ε * (a ⬝ᵥ (gramR μ W φ hφ K hK *ᵥ a)) := by
    intro a
    set u := ∑ j, a j • residuals μ W φ hφ K hK j with hudef
    have hcs := CAS11C03.weighted_cauchy_schwarz u z
    rw [real_inner_self_eq_norm_sq, real_inner_self_eq_norm_sq] at hcs
    rw [hdot a, quad_eq_norm_sq μ W φ hφ K hK a, ← sq_abs]
    calc |inner ℝ u z| ^ 2 ≤ ‖u‖ ^ 2 * ‖z‖ ^ 2 := hcs
      _ ≤ ‖u‖ ^ 2 * (2 * ε) := mul_le_mul_of_nonneg_left hzn (sq_nonneg _)
      _ = 2 * ε * ‖u‖ ^ 2 := by ring
  refine ⟨fun a => Real.abs_le_sqrt (hsq a), ?_⟩
  have hR := gramR_posSemidef μ W φ hφ K hK
  rcases Nat.eq_zero_or_pos n with hn | hn
  · subst hn
    have he : e' = 0 := Subsingleton.elim _ _
    refine ⟨he ▸ Submodule.zero_mem _, ?_⟩
    rw [he, zero_dotProduct]
    linarith
  · obtain ⟨-, h1, h2⟩ := CAS11C02.finiteGramForward hn (gramR μ W φ hφ K hK) hR e' ε hε0 hsq
    exact ⟨h1, h2⟩

theorem uncertain_joint_support (μ : Measure X) (s : Stat) (f g W : X → ℝ)
    (hf : Measurable f) (hg : Measurable g)
    (hfd : ∀ᵐ x ∂μ, f x ∈ cdom s) (hgd : ∀ᵐ x ∂μ, g x ∈ dom s)
    (hW : WEnvelope μ s W f g) {ε : ℝ} (hε0 : 0 ≤ ε)
    (hε : Dext μ (hS s) (hS' s) f g ≤ ENNReal.ofReal ε)
    {m n : ℕ} (φ : Fin m → X → ℝ)
    (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W)) (K : Fin n → X → ℝ)
    (hK : ∀ j, MemLp (K j) 2 (wmeas μ W)) (B : Matrix (Fin n) (Fin m) ℝ)
    (hB : ∀ j, ∑ b, B j b • (hφ b).toLp (φ b) =
      (retainedSpan μ W φ hφ).starProjection ((hK j).toLp (K j)))
    (S : Set (Fin m → ℝ)) (hS : dm μ φ f g ∈ S) (a : Fin n → ℝ) {σ : ℝ}
    (hσ : ∀ d ∈ S, |(Bᵀ *ᵥ a) ⬝ᵥ d| ≤ σ) :
    |a ⬝ᵥ evec μ K f g| ≤ Real.sqrt (2 * ε * (a ⬝ᵥ (gramR μ W φ hφ K hK *ᵥ a))) + σ := by
  obtain ⟨hall, -, -⟩ :=
    uncertain_joint μ s f g W hf hg hfd hgd hW hε0 hε φ hφ K hK B hB
  have hsplit : a ⬝ᵥ evec μ K f g =
      a ⬝ᵥ (evec μ K f g - B *ᵥ dm μ φ f g) + (Bᵀ *ᵥ a) ⬝ᵥ dm μ φ f g := by
    rw [Matrix.mulVec_transpose, ← Matrix.dotProduct_mulVec, ← dotProduct_add, sub_add_cancel]
  rw [hsplit]
  exact (abs_add_le _ _).trans (add_le_add (hall a) (hσ _ hS))

theorem exact_matching_special_case (μ : Measure X) (s : Stat) (f g W : X → ℝ)
    (hf : Measurable f) (hg : Measurable g)
    (hfd : ∀ᵐ x ∂μ, f x ∈ cdom s) (hgd : ∀ᵐ x ∂μ, g x ∈ dom s)
    (hW : WEnvelope μ s W f g) {ε : ℝ} (hε0 : 0 ≤ ε)
    (hε : Dext μ (hS s) (hS' s) f g ≤ ENNReal.ofReal ε)
    {m n : ℕ} (φ : Fin m → X → ℝ)
    (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W)) (hS0 : dm μ φ f g ∈ ({0} : Set (Fin m → ℝ)))
    (K : Fin n → X → ℝ) (hK : ∀ j, MemLp (K j) 2 (wmeas μ W)) :
    (∀ a, ∫ x, φ a x * (f x - g x) ∂μ = 0) ∧
      (∀ c : Fin m → ℝ, suppAbs ({0} : Set (Fin m → ℝ)) c = 0) ∧
      (∀ j, |∫ x, K j x * (f x - g x) ∂μ| ≤
        Real.sqrt (2 * ε) *
          Metric.infDist ((hK j).toLp (K j)) (retainedSpan μ W φ hφ : Set (L2W μ W))) ∧
      evec μ K f g ∈ LinearMap.range (gramR μ W φ hφ K hK).toLin' ∧
      evec μ K f g ⬝ᵥ (CAS11C02.spectralPinvMatrix (gramR μ W φ hφ K hK)
          (gramR_posSemidef μ W φ hφ K hK).isHermitian *ᵥ evec μ K f g) ≤ 2 * ε := by
  have h0 : dm μ φ f g = 0 := hS0
  have hmatch : ∀ a, ∫ x, φ a x * (f x - g x) ∂μ = 0 := fun a => congrFun h0 a
  obtain ⟨-, hr, hell⟩ :=
    weighted_residual_ellipsoid μ s f g W hf hg hfd hgd hW hε0 hε φ hφ hmatch K hK
  refine ⟨hmatch, fun c => ?_, fun j => ?_, hr, hell⟩
  · simp [suppAbs, Set.image_singleton]
  · exact single_kernel_dist_bound μ s f g W hf hg hfd hgd hW hε0 hε φ hφ hmatch (hK j)

/-! ## D3: span enlargement; nested budget as a separate premise -/

theorem retainedSpan_mono {m m' : ℕ} (μ : Measure X) (W : X → ℝ) (φ' : Fin m' → X → ℝ)
    (hφ' : ∀ b, MemLp (φ' b) 2 (wmeas μ W)) (ι : Fin m → Fin m') :
    retainedSpan μ W (φ' ∘ ι) (fun a => hφ' (ι a)) ≤ retainedSpan μ W φ' hφ' := by
  unfold retainedSpan
  refine Submodule.span_mono ?_
  rintro _ ⟨a, rfl⟩
  exact ⟨ι a, rfl⟩

theorem infDist_retained_mono {m m' : ℕ} (μ : Measure X) (W : X → ℝ) (φ' : Fin m' → X → ℝ)
    (hφ' : ∀ b, MemLp (φ' b) 2 (wmeas μ W)) (ι : Fin m → Fin m') (k : L2W μ W) :
    Metric.infDist k (retainedSpan μ W φ' hφ' : Set (L2W μ W)) ≤
      Metric.infDist k (retainedSpan μ W (φ' ∘ ι) (fun a => hφ' (ι a)) : Set (L2W μ W)) :=
  Metric.infDist_le_infDist_of_subset (retainedSpan_mono μ W φ' hφ' ι)
    ⟨0, Submodule.zero_mem _⟩

theorem refined_bound (μ : Measure X) (s : Stat) (f g' W : X → ℝ)
    (hf : Measurable f) (hg' : Measurable g')
    (hfd : ∀ᵐ x ∂μ, f x ∈ cdom s) (hg'd : ∀ᵐ x ∂μ, g' x ∈ dom s)
    (hW' : WEnvelope μ s W f g') {ε' ε : ℝ} (hε'0 : 0 ≤ ε')
    (hε' : Dext μ (hS s) (hS' s) f g' ≤ ENNReal.ofReal ε') (hle : ε' ≤ ε)
    {m m' : ℕ} (φ' : Fin m' → X → ℝ) (hφ' : ∀ b, MemLp (φ' b) 2 (wmeas μ W))
    (ι : Fin m → Fin m') (hmatch' : ∀ b, ∫ x, φ' b x * (f x - g' x) ∂μ = 0)
    {k : X → ℝ} (hk : MemLp k 2 (wmeas μ W)) :
    |∫ x, k x * (f x - g' x) ∂μ| ≤
        Real.sqrt (2 * ε') * Metric.infDist (hk.toLp k) (retainedSpan μ W φ' hφ' : Set (L2W μ W)) ∧
      Real.sqrt (2 * ε') * Metric.infDist (hk.toLp k) (retainedSpan μ W φ' hφ' : Set (L2W μ W)) ≤
        Real.sqrt (2 * ε) * Metric.infDist (hk.toLp k)
          (retainedSpan μ W (φ' ∘ ι) (fun a => hφ' (ι a)) : Set (L2W μ W)) := by
  refine ⟨single_kernel_dist_bound μ s f g' W hf hg' hfd hg'd hW' hε'0 hε' φ' hφ' hmatch' hk, ?_⟩
  exact mul_le_mul (Real.sqrt_le_sqrt (by linarith))
    (infDist_retained_mono μ W φ' hφ' ι _) Metric.infDist_nonneg (Real.sqrt_nonneg _)

theorem nested_budget_discharge {m : ℕ} (μ : Measure X) (s : Stat) (f g k : X → ℝ)
    (hf : Measurable f) (hg : Measurable g) (hk : Measurable k)
    (hfd : ∀ᵐ x ∂μ, f x ∈ cdom s) (hgd : ∀ᵐ x ∂μ, g x ∈ dom s) (hkd : ∀ᵐ x ∂μ, k x ∈ dom s)
    {ε : ℝ} (hε0 : 0 ≤ ε) (hε : Dext μ (hS s) (hS' s) f g ≤ ENNReal.ofReal ε)
    (hfk : Integrable (fun x => bregDens (hS s) (hS' s) (f x) (k x)) μ)
    (hkg : Integrable (fun x => bregDens (hS s) (hS' s) (k x) (g x)) μ)
    (φ : Fin m → X → ℝ) (lam : Fin m → ℝ)
    (hspan : ∀ᵐ x ∂μ, hS' s (k x) - hS' s (g x) = ∑ j, lam j * φ j x)
    (hφf : ∀ j, Integrable (fun x => φ j x * f x) μ)
    (hφk : ∀ j, Integrable (fun x => φ j x * k x) μ)
    (hmatch : ∀ j, ∫ x, φ j x * f x ∂μ = ∫ x, φ j x * k x ∂μ) :
    Dext μ (hS s) (hS' s) f k ≤ ENNReal.ofReal ε := by
  obtain ⟨hfgI, -, hDfg⟩ := finite_budget_stat μ s f g hf hg hfd hgd hε0 hε
  have hnest := nested_budget μ f g k hfgI hfk hkg φ lam hspan hφf hφk hmatch (convexOn_hS s)
    (hkd.mono fun x hx => dom_subset_cdom s hx) (hgd.mono fun x hx => dom_subset_cdom s hx)
    (hgd.mono fun x hx => hasDerivAt_hS s hx)
  have hnn : ∀ᵐ x ∂μ, 0 ≤ bregDens (hS s) (hS' s) (f x) (k x) := by
    filter_upwards [hfd, hkd] with x h1 h2 using bregDens_nonneg_stat s h1 h2
  rw [Dext_eq_ofReal μ _ _ f k hfk hnn]
  exact ENNReal.ofReal_le_ofReal (hnest.trans hDfg)

/-! ## D4: input witnesses for W -/

theorem envelope_of_upper (μ : Measure X) (s : Stat) (hs : 0 ≤ xi s) (F f g : X → ℝ)
    (hFm : Measurable F) (hFpos : ∀ᵐ x ∂μ, 0 < F x)
    (hfF : ∀ᵐ x ∂μ, 0 ≤ f x ∧ f x ≤ F x) (hgF : ∀ᵐ x ∂μ, 0 ≤ g x ∧ g x ≤ F x) :
    WEnvelope μ s (fun x => F x * (1 + xi s * F x)) f g := by
  refine ⟨hFm.mul (measurable_const.add (measurable_const.mul hFm)), ?_, ?_⟩
  · filter_upwards [hFpos] with x hx
    have : 0 ≤ xi s * F x := mul_nonneg hs hx.le
    exact mul_pos hx (by linarith)
  · filter_upwards [hfF, hgF] with x hfx hgx z hz
    obtain ⟨hz0, hz1⟩ := uIcc_subset_Icc hfx hgx hz
    have h2 : z * z ≤ F x * F x := mul_le_mul hz1 hz1 hz0 (hz0.trans hz1)
    have h3 : xi s * (z * z) ≤ xi s * (F x * F x) := mul_le_mul_of_nonneg_left h2 hs
    have e1 : z * (1 + xi s * z) = z + xi s * (z * z) := by ring
    have e2 : F x * (1 + xi s * F x) = F x + xi s * (F x * F x) := by ring
    rw [e1, e2]
    linarith

theorem envelope_FD (μ : Measure X) (f g : X → ℝ)
    (hf : ∀ᵐ x ∂μ, f x ∈ cdom .FD) (hg : ∀ᵐ x ∂μ, g x ∈ cdom .FD) :
    WEnvelope μ .FD (fun _ => 1 / 4) f g := by
  refine ⟨measurable_const, Eventually.of_forall fun _ => by norm_num, ?_⟩
  filter_upwards [hf, hg] with x hfx hgx z hz
  have hz' : z ∈ Icc (0 : ℝ) 1 := uIcc_subset_Icc hfx hgx hz
  simp only [xi]
  nlinarith [sq_nonneg (z - 1 / 2)]

end General

/-- The Planck occupation F_b(E) = 1/(e^{bE} − 1) on (E, e) ∈ ℝ × S². -/
noncomputable def planckF (b : ℝ) : ℝ × Sphere2 → ℝ := fun y => 1 / (Real.exp (b * y.1) - 1)

theorem nu_ae_energy_pos (C : ℝ) : ∀ᵐ y ∂nu C, 0 < y.1 := by
  rw [ae_iff]
  have hset : {y : ℝ × Sphere2 | ¬ 0 < y.1} = (Iic (0 : ℝ)) ×ˢ (univ : Set Sphere2) := by
    ext y
    simp
  rw [hset]
  refine le_antisymm ?_ (zero_le _)
  unfold nu
  have hE : ((volume.restrict (Ioi (0 : ℝ))).withDensity
      (fun E => ENNReal.ofReal (C * E ^ 2))) (Iic 0) = 0 := by
    refine withDensity_absolutelyContinuous _ _ ?_
    rw [Measure.restrict_apply measurableSet_Iic]
    have : Iic (0 : ℝ) ∩ Ioi 0 = ∅ := by
      ext x
      simp only [mem_inter_iff, mem_Iic, mem_Ioi, mem_empty_iff_false, iff_false, not_and,
        not_lt]
      exact fun h => h
    rw [this, measure_empty]
  calc _ ≤ _ := Measure.prod_prod_le _ _
    _ = 0 := by rw [hE, zero_mul]

theorem planck_envelope (C b : ℝ) (hb : 0 < b) (f g : ℝ × Sphere2 → ℝ)
    (hfF : ∀ᵐ y ∂nu C, 0 ≤ f y ∧ f y ≤ planckF b y)
    (hgF : ∀ᵐ y ∂nu C, 0 ≤ g y ∧ g y ≤ planckF b y) :
    WEnvelope (nu C) .BE (fun y => planckF b y * (1 + planckF b y)) f g := by
  have hm : Measurable (planckF b) := by
    unfold planckF
    exact measurable_const.div
      ((Real.measurable_exp.comp (measurable_const.mul measurable_fst)).sub measurable_const)
  have hpos : ∀ᵐ y ∂nu C, 0 < planckF b y := by
    filter_upwards [nu_ae_energy_pos C] with y hy
    have h1 : 0 < b * y.1 := mul_pos hb hy
    have h2 : 1 < Real.exp (b * y.1) := by
      linarith [Real.add_one_lt_exp h1.ne']
    exact one_div_pos.2 (by linarith)
  have h := envelope_of_upper (nu C) .BE (by norm_num [xi]) (planckF b) f g hm hpos hfF hgF
  simpa only [xi, one_mul] using h

/-! ## D4: negative controls and non-vacuity -/

theorem eps_not_from_moments (ε : ℝ) :
    ∃ f : Bool → ℝ, Measurable f ∧ (∀ x, f x ∈ cdom .MB) ∧
      (∫ x, (if x then (1:ℝ) else 0) * (f x - 1)
          ∂(Measure.dirac true + Measure.dirac false)) = 0 ∧
      ¬ Dext (Measure.dirac true + Measure.dirac false) (hS .MB) (hS' .MB) f (fun _ => 1)
          ≤ ENNReal.ofReal ε := by
  set L : ℝ := |ε| + 2 with hL
  refine ⟨fun x => if x then 1 else Real.exp L, measurable_of_finite _, ?_, ?_, ?_⟩
  · intro x
    cases x <;> simp [cdom, (Real.exp_pos L).le]
  · have hz : (fun x : Bool => (if x then (1:ℝ) else 0) *
        ((fun x : Bool => if x then (1:ℝ) else Real.exp L) x - 1)) = fun _ => 0 := by
      funext x
      cases x <;> simp
    rw [hz, integral_zero]
  · intro hle
    unfold Dext at hle
    rw [lintegral_add_measure, lintegral_dirac, lintegral_dirac] at hle
    have h1 : bregDens (hS .MB) (hS' .MB) 1 1 = 0 := by simp [bregDens]
    have h2 : bregDens (hS .MB) (hS' .MB) (Real.exp L) 1 = Real.exp L * (L - 1) + 1 := by
      simp only [bregDens, hS, hMB, hS', xi, Real.log_exp, Real.log_one, zero_mul, add_zero,
        div_one, mul_one]
      ring
    simp only [if_true, Bool.false_eq_true, if_false] at hle
    rw [h1, h2, ENNReal.ofReal_zero, zero_add] at hle
    have he : 1 ≤ Real.exp L := Real.one_le_exp (by positivity)
    have hL1 : L - 1 = |ε| + 1 := by rw [hL]; ring
    have hprod : |ε| + 1 ≤ Real.exp L * (L - 1) := by
      rw [hL1]
      nlinarith [abs_nonneg ε]
    have hV : ε < Real.exp L * (L - 1) + 1 := by linarith [le_abs_self ε]
    have hVpos : 0 < Real.exp L * (L - 1) + 1 := by linarith [abs_nonneg ε]
    exact absurd hle (not_le.2 ((ENNReal.ofReal_lt_ofReal_iff hVpos).2 hV))

theorem support_term_necessary :
    ∃ (f g W : Unit → ℝ) (φ : Fin 1 → Unit → ℝ)
      (hφ : ∀ a, MemLp (φ a) 2 (wmeas (Measure.dirac ()) W))
      (k : Unit → ℝ) (hk : MemLp k 2 (wmeas (Measure.dirac ()) W))
      (S : Set (Fin 1 → ℝ)) (c : Fin 1 → ℝ),
      Measurable f ∧ Measurable g ∧
      (∀ᵐ x ∂(Measure.dirac ()), f x ∈ cdom .MB) ∧ (∀ᵐ x ∂(Measure.dirac ()), g x ∈ dom .MB) ∧
      WEnvelope (Measure.dirac ()) .MB W f g ∧
      Dext (Measure.dirac ()) (hS .MB) (hS' .MB) f g ≤ ENNReal.ofReal 1 ∧
      dm (Measure.dirac ()) φ f g ∈ S ∧ dm (Measure.dirac ()) φ f g ≠ 0 ∧
      BddAbove ((fun d => |c ⬝ᵥ d|) '' S) ∧
      |∫ x, k x * (f x - g x) ∂(Measure.dirac ())| =
        Real.sqrt (2 * 1) * ‖hk.toLp k - ∑ a, c a • (hφ a).toLp (φ a)‖ + suppAbs S c ∧
      ¬ |∫ x, k x * (f x - g x) ∂(Measure.dirac ())| ≤
        Real.sqrt (2 * 1) * ‖hk.toLp k - ∑ a, c a • (hφ a).toLp (φ a)‖ := by
  obtain ⟨h1, h2, h3, h4, h5, h6⟩ := witness_budget
  obtain ⟨hbdd, hsupp⟩ := box_support (fun _ : Fin 1 => (1:ℝ)) (fun _ => by norm_num)
    (fun _ => 1)
  have hdm : dm (Measure.dirac ()) (fun (_ : Fin 1) (_ : Unit) => (1:ℝ))
      (fun _ => 2) (fun _ => 1) = fun _ => 1 := by
    funext a
    simp only [dm]
    rw [integral_dirac]
    norm_num
  have hnorm : ‖(memLp_const_dirac 1 2).toLp (fun _ : Unit => (1:ℝ)) -
      ∑ a : Fin 1, (fun _ : Fin 1 => (1:ℝ)) a • (memLp_const_dirac 1 2).toLp
        (fun _ : Unit => (1:ℝ))‖ = 0 := by
    rw [Fin.sum_univ_one, one_smul, sub_self, norm_zero]
  have hint : ∫ x, (fun _ : Unit => (1:ℝ)) x * ((fun _ : Unit => (2:ℝ)) x -
      (fun _ : Unit => (1:ℝ)) x) ∂(Measure.dirac ()) = 1 := by
    rw [integral_dirac]
    norm_num
  refine ⟨fun _ => 2, fun _ => 1, fun _ => 2, fun _ _ => 1, fun _ => memLp_const_dirac 1 2,
    fun _ => 1, memLp_const_dirac 1 2, box (fun _ => 1), fun _ => 1,
    h1, h2, h3, h4, h5, h6, ?_, ?_, hbdd, ?_, ?_⟩
  · rw [hdm]
    intro a
    norm_num
  · rw [hdm]
    intro h
    have := congrFun h 0
    norm_num at this
  · rw [hnorm, hsupp, hint]
    simp
  · rw [hnorm, hint]
    norm_num

/-! ## D5: coverage by the union bound (probabilistic layer, separate) -/

theorem coverage_union {Ω : Type*} [MeasurableSpace Ω] (P : Measure Ω) (good : Ω → Prop)
    (E₁ E₂ E₃ : Set Ω) (himp : ∀ ω, ω ∈ E₁ → ω ∈ E₂ → ω ∈ E₃ → good ω)
    {α₁ α₂ α₃ : ℝ≥0∞} (h₁ : P E₁ᶜ ≤ α₁) (h₂ : P E₂ᶜ ≤ α₂) (h₃ : P E₃ᶜ ≤ α₃) :
    P {ω | ¬ good ω} ≤ α₁ + α₂ + α₃ := by
  have hsub : {ω | ¬ good ω} ⊆ E₁ᶜ ∪ E₂ᶜ ∪ E₃ᶜ := by
    intro ω hω
    by_contra h
    simp only [mem_union, mem_compl_iff, not_or, not_not] at h
    exact hω (himp ω h.1.1 h.1.2 h.2)
  calc P {ω | ¬ good ω} ≤ P (E₁ᶜ ∪ E₂ᶜ ∪ E₃ᶜ) := measure_mono hsub
    _ ≤ P (E₁ᶜ ∪ E₂ᶜ) + P E₃ᶜ := measure_union_le _ _
    _ ≤ P E₁ᶜ + P E₂ᶜ + P E₃ᶜ := add_le_add_left (measure_union_le _ _) _
    _ ≤ α₁ + α₂ + α₃ := add_le_add (add_le_add h₁ h₂) h₃

theorem coverage_union_prob {Ω : Type*} [MeasurableSpace Ω] (P : Measure Ω)
    [IsProbabilityMeasure P] (good : Ω → Prop)
    (E₁ E₂ E₃ : Set Ω) (himp : ∀ ω, ω ∈ E₁ → ω ∈ E₂ → ω ∈ E₃ → good ω)
    {α₁ α₂ α₃ : ℝ≥0∞} (h₁ : P E₁ᶜ ≤ α₁) (h₂ : P E₂ᶜ ≤ α₂) (h₃ : P E₃ᶜ ≤ α₃) :
    1 - (α₁ + α₂ + α₃) ≤ P {ω | good ω} := by
  have h := coverage_union P good E₁ E₂ E₃ himp h₁ h₂ h₃
  have hu : (1 : ℝ≥0∞) ≤ P {ω | good ω} + P {ω | ¬ good ω} := by
    rw [← measure_univ (μ := P)]
    calc P univ ≤ P ({ω | good ω} ∪ {ω | ¬ good ω}) := measure_mono fun ω _ => by
          by_cases hg : good ω
          · exact Or.inl hg
          · exact Or.inr hg
      _ ≤ _ := measure_union_le _ _
  rw [tsub_le_iff_right]
  exact hu.trans (add_le_add_left h _)

section Coverage

variable {X : Type*} [MeasurableSpace X]

theorem uncertain_bound_coverage {Ω : Type*} [MeasurableSpace Ω] (P : Measure Ω)
    (μ : Measure X) (s : Stat) (f W : X → ℝ) (hf : Measurable f)
    (hfd : ∀ᵐ x ∂μ, f x ∈ cdom s)
    (g : Ω → X → ℝ) (hg : ∀ ω, Measurable (g ω)) (hgd : ∀ ω, ∀ᵐ x ∂μ, g ω x ∈ dom s)
    (εhat : Ω → ℝ) (hε0 : ∀ ω, 0 ≤ εhat ω)
    {m : ℕ} (φ : Fin m → X → ℝ) (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W))
    {k : X → ℝ} (hk : MemLp k 2 (wmeas μ W))
    (S : Ω → Set (Fin m → ℝ)) (σ : Ω → (Fin m → ℝ) → ℝ)
    (hσ : ∀ ω c, ∀ d ∈ S ω, |c ⬝ᵥ d| ≤ σ ω c)
    {αW αε αm : ℝ≥0∞}
    (hcovW : P {ω | ¬ WEnvelope μ s W f (g ω)} ≤ αW)
    (hcovε : P {ω | ¬ Dext μ (hS s) (hS' s) f (g ω) ≤ ENNReal.ofReal (εhat ω)} ≤ αε)
    (hcovm : P {ω | dm μ φ f (g ω) ∉ S ω} ≤ αm) :
    P {ω | ¬ ∀ c : Fin m → ℝ, |∫ x, k x * (f x - g ω x) ∂μ| ≤
        Real.sqrt (2 * εhat ω) * ‖hk.toLp k - ∑ a, c a • (hφ a).toLp (φ a)‖ + σ ω c}
      ≤ αW + αε + αm :=
  coverage_union P
    (fun ω => ∀ c : Fin m → ℝ, |∫ x, k x * (f x - g ω x) ∂μ| ≤
        Real.sqrt (2 * εhat ω) * ‖hk.toLp k - ∑ a, c a • (hφ a).toLp (φ a)‖ + σ ω c)
    {ω | WEnvelope μ s W f (g ω)} {ω | Dext μ (hS s) (hS' s) f (g ω) ≤ ENNReal.ofReal (εhat ω)}
    {ω | dm μ φ f (g ω) ∈ S ω}
    (fun ω hW hε hm c => uncertain_bound μ s f (g ω) W hf (hg ω) hfd (hgd ω) hW (hε0 ω) hε
      φ hφ hk (S ω) hm c (hσ ω c))
    hcovW hcovε hcovm

theorem uncertain_bound_coverage_prob {Ω : Type*} [MeasurableSpace Ω] (P : Measure Ω)
    [IsProbabilityMeasure P]
    (μ : Measure X) (s : Stat) (f W : X → ℝ) (hf : Measurable f)
    (hfd : ∀ᵐ x ∂μ, f x ∈ cdom s)
    (g : Ω → X → ℝ) (hg : ∀ ω, Measurable (g ω)) (hgd : ∀ ω, ∀ᵐ x ∂μ, g ω x ∈ dom s)
    (εhat : Ω → ℝ) (hε0 : ∀ ω, 0 ≤ εhat ω)
    {m : ℕ} (φ : Fin m → X → ℝ) (hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W))
    {k : X → ℝ} (hk : MemLp k 2 (wmeas μ W))
    (S : Ω → Set (Fin m → ℝ)) (σ : Ω → (Fin m → ℝ) → ℝ)
    (hσ : ∀ ω c, ∀ d ∈ S ω, |c ⬝ᵥ d| ≤ σ ω c)
    {αW αε αm : ℝ≥0∞}
    (hcovW : P {ω | ¬ WEnvelope μ s W f (g ω)} ≤ αW)
    (hcovε : P {ω | ¬ Dext μ (hS s) (hS' s) f (g ω) ≤ ENNReal.ofReal (εhat ω)} ≤ αε)
    (hcovm : P {ω | dm μ φ f (g ω) ∉ S ω} ≤ αm) :
    1 - (αW + αε + αm) ≤ P {ω | ∀ c : Fin m → ℝ, |∫ x, k x * (f x - g ω x) ∂μ| ≤
        Real.sqrt (2 * εhat ω) * ‖hk.toLp k - ∑ a, c a • (hφ a).toLp (φ a)‖ + σ ω c} :=
  coverage_union_prob P
    (fun ω => ∀ c : Fin m → ℝ, |∫ x, k x * (f x - g ω x) ∂μ| ≤
        Real.sqrt (2 * εhat ω) * ‖hk.toLp k - ∑ a, c a • (hφ a).toLp (φ a)‖ + σ ω c)
    {ω | WEnvelope μ s W f (g ω)} {ω | Dext μ (hS s) (hS' s) f (g ω) ≤ ENNReal.ofReal (εhat ω)}
    {ω | dm μ φ f (g ω) ∈ S ω}
    (fun ω hW hε hm c => uncertain_bound μ s f (g ω) W hf (hg ω) hfd (hgd ω) hW (hε0 ω) hε
      φ hφ hk (S ω) hm c (hσ ω c))
    hcovW hcovε hcovm

end Coverage

end G11D
