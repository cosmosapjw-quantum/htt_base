import Mathlib

/-!
# G08-C: the four-way geodesicity decision as finite set-containment implications

Owning source: `docs/research_program/gr_statistics_loops_20260930/statistics/
NATIVE_INFERENCE_THEOREMS.md` (sha256 e215836882047c50a1a5ae6da605d62aa2c553d0de055e279eee3ce35ec8e322),
§5 lines 105-120, eq. (1)-(2) lines 9-23, eq. (7) lines 77-80, N1a lines 96-103,
union rule line 69.  Targets frozen in `FROZEN_TARGETS.md`.

Scope: deterministic set logic only.  No Gaussian law, χ² quantile, measurability,
optimizer certificate or physical interpretation of `G` is proved here.  The size
control statements are conditional on an explicit coverage hypothesis.
-/

noncomputable section

namespace G08C

open MeasureTheory

universe u v w

section Decision

variable {Θ : Type u} {X : Type v}

/-- Eq. (7) at a fixed observation: `Cα = {θ ∈ Ω : Q θ ≤ q}` (non-strict acceptance). -/
def confSet (Ω : Set Θ) (Q : Θ → ℝ) (q : ℝ) : Set Θ := {θ | θ ∈ Ω ∧ Q θ ≤ q}

/-- §5: `Cα,G = {θ ∈ Cα : x(θ) ∈ G}`. -/
def nullConfSet (Ω : Set Θ) (Q : Θ → ℝ) (q : ℝ) (xmap : Θ → X) (G : Set X) : Set Θ :=
  {θ | θ ∈ confSet Ω Q q ∧ xmap θ ∈ G}

/-- Report 1: `Cα` nonempty and `Cα,G` empty. -/
def RejectsGeodesicity (C CG : Set Θ) : Prop := C.Nonempty ∧ CG = ∅

/-- Report 2: both nonempty. -/
def NotExcluded (C CG : Set Θ) : Prop := C.Nonempty ∧ CG.Nonempty

/-- Report 3: `Cα` empty. -/
def ModelIncompatible (C : Set Θ) : Prop := C = ∅

/-- The four mutually distinct reports of §5. -/
inductive Report
  | geodesicityRejected
  | notExcluded
  | modelIncompatible
  | computationallyUnresolved
  deriving DecidableEq, Repr

/-- Certification state of a set (line 120): a feasible point certifies nonemptiness,
a verified proof certifies emptiness, otherwise nothing is certified. -/
inductive Cert (S : Set Θ) : Type u
  | feasible (θ : Θ) (h : θ ∈ S) : Cert S
  | excluded (h : S = ∅) : Cert S
  | uncertified : Cert S

/-- The delivered report from certificates for `Cα` and `Cα,G`. -/
def fourWayReport {C CG : Set Θ} : Cert C → Cert CG → Report
  | .excluded _, _ => .modelIncompatible
  | _, .feasible _ _ => .notExcluded
  | .feasible _ _, .excluded _ => .geodesicityRejected
  | _, _ => .computationallyUnresolved

/-! ### T1 set structure / boundary -/

theorem nullConfSet_subset (Ω : Set Θ) (Q : Θ → ℝ) (q : ℝ) (xmap : Θ → X) (G : Set X) :
    nullConfSet Ω Q q xmap G ⊆ confSet Ω Q q :=
  fun _ h => h.1

theorem mem_confSet_of_eq {Ω : Set Θ} {Q : Θ → ℝ} {q : ℝ} {θ : Θ} (hΩ : θ ∈ Ω) (hq : Q θ = q) :
    θ ∈ confSet Ω Q q :=
  ⟨hΩ, hq.le⟩

theorem confSet_rank_zero (Ω : Set Θ) (Q : Θ → ℝ) (hQ : ∀ θ, Q θ = 0) : confSet Ω Q 0 = Ω := by
  ext θ
  simp [confSet, hQ]

/-! ### T2 semantic disjointness / exhaustiveness -/

theorem semantic_trichotomy (C CG : Set Θ) :
    (RejectsGeodesicity C CG ∨ NotExcluded C CG ∨ ModelIncompatible C) ∧
    ¬ (RejectsGeodesicity C CG ∧ NotExcluded C CG) ∧
    ¬ (RejectsGeodesicity C CG ∧ ModelIncompatible C) ∧
    ¬ (NotExcluded C CG ∧ ModelIncompatible C) := by
  unfold RejectsGeodesicity NotExcluded ModelIncompatible
  refine ⟨?_, ?_, ?_, ?_⟩
  · rcases C.eq_empty_or_nonempty with hC | hC
    · exact Or.inr (Or.inr hC)
    · rcases CG.eq_empty_or_nonempty with hG | hG
      · exact Or.inl ⟨hC, hG⟩
      · exact Or.inr (Or.inl ⟨hC, hG⟩)
  · rintro ⟨⟨_, hG⟩, _, hG'⟩
    exact Set.nonempty_iff_ne_empty.mp hG' hG
  · rintro ⟨⟨hC, _⟩, hC'⟩
    exact Set.nonempty_iff_ne_empty.mp hC hC'
  · rintro ⟨⟨hC, _⟩, hC'⟩
    exact Set.nonempty_iff_ne_empty.mp hC hC'

theorem modelIncompatible_null_empty {C CG : Set Θ} (hsub : CG ⊆ C) (h : ModelIncompatible C) :
    CG = ∅ :=
  Set.subset_eq_empty hsub h

/-! ### T3 soundness of delivered reports -/

theorem report_rejected_sound {C CG : Set Θ} (cC : Cert C) (cG : Cert CG)
    (h : fourWayReport cC cG = .geodesicityRejected) : RejectsGeodesicity C CG := by
  cases cC with
  | feasible θ hθ =>
    cases cG with
    | feasible _ _ => simp [fourWayReport] at h
    | excluded hG => exact ⟨⟨θ, hθ⟩, hG⟩
    | uncertified => simp [fourWayReport] at h
  | excluded _ => simp [fourWayReport] at h
  | uncertified => cases cG <;> simp [fourWayReport] at h

theorem report_notExcluded_sound {C CG : Set Θ} (hsub : CG ⊆ C) (cC : Cert C) (cG : Cert CG)
    (h : fourWayReport cC cG = .notExcluded) : NotExcluded C CG := by
  cases cG with
  | feasible θ hθ => exact ⟨⟨θ, hsub hθ⟩, ⟨θ, hθ⟩⟩
  | excluded _ => cases cC <;> simp [fourWayReport] at h
  | uncertified => cases cC <;> simp [fourWayReport] at h

theorem report_incompatible_sound {C CG : Set Θ} (cC : Cert C) (cG : Cert CG)
    (h : fourWayReport cC cG = .modelIncompatible) : ModelIncompatible C := by
  cases cC with
  | excluded hC => exact hC
  | feasible _ _ => cases cG <;> simp [fourWayReport] at h
  | uncertified => cases cG <;> simp [fourWayReport] at h

/-! ### T4 attainability -/

theorem report_complete {C CG : Set Θ} :
    (RejectsGeodesicity C CG →
      ∃ (cC : Cert C) (cG : Cert CG), fourWayReport cC cG = .geodesicityRejected) ∧
    (NotExcluded C CG →
      ∃ (cC : Cert C) (cG : Cert CG), fourWayReport cC cG = .notExcluded) ∧
    (ModelIncompatible C →
      ∃ (cC : Cert C) (cG : Cert CG), fourWayReport cC cG = .modelIncompatible) := by
  refine ⟨?_, ?_, ?_⟩
  · rintro ⟨⟨θ, hθ⟩, hG⟩
    exact ⟨.feasible θ hθ, .excluded hG, rfl⟩
  · rintro ⟨_, ⟨θ, hθ⟩⟩
    exact ⟨.uncertified, .feasible θ hθ, rfl⟩
  · intro hC
    exact ⟨.excluded hC, .uncertified, rfl⟩

theorem report_unresolved_uncertified (C CG : Set Θ) :
    fourWayReport (Cert.uncertified : Cert C) (Cert.uncertified : Cert CG) =
      .computationallyUnresolved :=
  rfl

/-! ### T5 pitfalls (CONF-EMPTYMODEL, CONF-OPTFAIL) -/

theorem emptyModel_not_rejected {C CG : Set Θ} (h : ModelIncompatible C) (cC : Cert C)
    (cG : Cert CG) : fourWayReport cC cG ≠ .geodesicityRejected := by
  intro h'
  exact Set.nonempty_iff_ne_empty.mp (report_rejected_sound cC cG h').1 h

theorem emptyModel_report_cases {C CG : Set Θ} (hsub : CG ⊆ C) (h : ModelIncompatible C)
    (cC : Cert C) (cG : Cert CG) :
    fourWayReport cC cG = .modelIncompatible ∨
      fourWayReport cC cG = .computationallyUnresolved := by
  have hC : C = ∅ := h
  cases cC with
  | feasible θ hθ => exact absurd (hC ▸ hθ) (Set.notMem_empty θ)
  | excluded _ => exact Or.inl rfl
  | uncertified =>
    cases cG with
    | feasible θ hθ => exact absurd (hC ▸ hsub hθ) (Set.notMem_empty θ)
    | excluded _ => exact Or.inr rfl
    | uncertified => exact Or.inr rfl

theorem uncertified_null_not_rejected {C CG : Set Θ} (cC : Cert C) :
    fourWayReport cC (Cert.uncertified : Cert CG) ≠ .geodesicityRejected := by
  cases cC <;> simp [fourWayReport]

theorem uncertified_full_not_rejected {C CG : Set Θ} (cG : Cert CG) :
    fourWayReport (Cert.uncertified : Cert C) cG ≠ .geodesicityRejected := by
  cases cG <;> simp [fourWayReport]

/-! ### T6 exclusion certificates -/

theorem confSet_eq_empty_of_lower_bound {Ω : Set Θ} {Q : Θ → ℝ} {q : ℝ}
    (h : ∃ b, q < b ∧ ∀ θ ∈ Ω, b ≤ Q θ) : confSet Ω Q q = ∅ := by
  obtain ⟨b, hqb, hb⟩ := h
  refine Set.eq_empty_iff_forall_notMem.mpr ?_
  rintro θ ⟨hθ, hq⟩
  exact absurd hq (not_le.mpr (lt_of_lt_of_le hqb (hb θ hθ)))

theorem nullConfSet_eq_empty_of_lower_bound {Ω : Set Θ} {Q : Θ → ℝ} {q : ℝ} {xmap : Θ → X}
    {G : Set X} (h : ∃ b, q < b ∧ ∀ θ ∈ Ω, xmap θ ∈ G → b ≤ Q θ) :
    nullConfSet Ω Q q xmap G = ∅ := by
  obtain ⟨b, hqb, hb⟩ := h
  refine Set.eq_empty_iff_forall_notMem.mpr ?_
  rintro θ ⟨⟨hθ, hq⟩, hG⟩
  exact absurd hq (not_le.mpr (lt_of_lt_of_le hqb (hb θ hθ hG)))

theorem nonstrict_bound_inconclusive :
    (∀ θ ∈ Set.Ici (0:ℝ), (0:ℝ) ≤ θ) ∧
    (nullConfSet (Set.Ici (0:ℝ)) (fun θ => θ) 0 id (Set.univ : Set ℝ)).Nonempty ∧
    (∀ θ ∈ Set.Ioi (0:ℝ), (0:ℝ) ≤ θ) ∧
    nullConfSet (Set.Ioi (0:ℝ)) (fun θ => θ) 0 id (Set.univ : Set ℝ) = ∅ ∧
    ¬ ∃ b : ℝ, 0 < b ∧ ∀ θ ∈ Set.Ioi (0:ℝ), id θ ∈ (Set.univ : Set ℝ) → b ≤ θ := by
  refine ⟨fun θ hθ => Set.mem_Ici.mp hθ, ⟨0, ⟨Set.self_mem_Ici, le_refl _⟩, Set.mem_univ _⟩,
    fun θ hθ => le_of_lt (Set.mem_Ioi.mp hθ), ?_, ?_⟩
  · refine Set.eq_empty_iff_forall_notMem.mpr ?_
    rintro θ ⟨⟨hθ, hq⟩, -⟩
    exact absurd hq (not_le.mpr (Set.mem_Ioi.mp hθ))
  · rintro ⟨b, hb, hall⟩
    have h2 := hall (b / 2) (Set.mem_Ioi.mpr (by linarith)) (Set.mem_univ _)
    linarith

/-! ### T7 deterministic N2 event containment -/

variable {Y : Type w}

theorem null_errors_subset_noncoverage (Ω : Set Θ) (Q : Y → Θ → ℝ) (q : ℝ) (xmap : Θ → X)
    (G : Set X) {θs : Θ} (hG : xmap θs ∈ G) :
    {y | RejectsGeodesicity (confSet Ω (Q y) q) (nullConfSet Ω (Q y) q xmap G)} ∪
      {y | ModelIncompatible (confSet Ω (Q y) q)} ⊆ {y | θs ∉ confSet Ω (Q y) q} := by
  intro y hy hθ
  rcases hy with ⟨_, hG0⟩ | hC
  · have hmem : θs ∈ nullConfSet Ω (Q y) q xmap G := ⟨hθ, hG⟩
    rw [hG0] at hmem
    exact Set.notMem_empty θs hmem
  · have hC' : confSet Ω (Q y) q = ∅ := hC
    rw [hC'] at hθ
    exact Set.notMem_empty θs hθ

theorem incompatible_subset_noncoverage (Ω : Set Θ) (Q : Y → Θ → ℝ) (q : ℝ) (θs : Θ) :
    {y | ModelIncompatible (confSet Ω (Q y) q)} ⊆ {y | θs ∉ confSet Ω (Q y) q} := by
  intro y hC hθ
  have hC' : confSet Ω (Q y) q = ∅ := hC
  rw [hC'] at hθ
  exact Set.notMem_empty θs hθ

theorem certified_null_errors_subset (Ω : Set Θ) (Q : Y → Θ → ℝ) (q : ℝ) (xmap : Θ → X)
    (G : Set X) {θs : Θ} (hG : xmap θs ∈ G)
    (cC : ∀ y, Cert (confSet Ω (Q y) q)) (cG : ∀ y, Cert (nullConfSet Ω (Q y) q xmap G)) :
    {y | fourWayReport (cC y) (cG y) = .geodesicityRejected ∨
         fourWayReport (cC y) (cG y) = .modelIncompatible} ⊆ {y | θs ∉ confSet Ω (Q y) q} := by
  intro y hy
  rcases hy with h | h
  · exact null_errors_subset_noncoverage Ω Q q xmap G hG
      (Or.inl (report_rejected_sound (cC y) (cG y) h))
  · exact null_errors_subset_noncoverage Ω Q q xmap G hG
      (Or.inr (report_incompatible_sound (cC y) (cG y) h))

theorem certified_incompatible_subset (Ω : Set Θ) (Q : Y → Θ → ℝ) (q : ℝ) (xmap : Θ → X)
    (G : Set X) (θs : Θ) (cC : ∀ y, Cert (confSet Ω (Q y) q))
    (cG : ∀ y, Cert (nullConfSet Ω (Q y) q xmap G)) :
    {y | fourWayReport (cC y) (cG y) = .modelIncompatible} ⊆ {y | θs ∉ confSet Ω (Q y) q} :=
  fun y h => incompatible_subset_noncoverage Ω Q q θs (report_incompatible_sound (cC y) (cG y) h)

/-! ### T8 size control conditional on an explicit coverage hypothesis -/

theorem size_control_of_coverage [MeasurableSpace Y] (μ : Measure Y) (α : ENNReal)
    (Ω : Set Θ) (Q : Y → Θ → ℝ) (q : ℝ) (xmap : Θ → X) (G : Set X) {θs : Θ}
    (hG : xmap θs ∈ G)
    (cC : ∀ y, Cert (confSet Ω (Q y) q)) (cG : ∀ y, Cert (nullConfSet Ω (Q y) q xmap G))
    (hcov : μ {y | θs ∉ confSet Ω (Q y) q} ≤ α) :
    μ {y | fourWayReport (cC y) (cG y) = .geodesicityRejected ∨
           fourWayReport (cC y) (cG y) = .modelIncompatible} ≤ α :=
  (measure_mono (certified_null_errors_subset Ω Q q xmap G hG cC cG)).trans hcov

theorem incompatible_size_of_coverage [MeasurableSpace Y] (μ : Measure Y) (α : ENNReal)
    (Ω : Set Θ) (Q : Y → Θ → ℝ) (q : ℝ) (xmap : Θ → X) (G : Set X) (θs : Θ)
    (cC : ∀ y, Cert (confSet Ω (Q y) q)) (cG : ∀ y, Cert (nullConfSet Ω (Q y) q xmap G))
    (hcov : μ {y | θs ∉ confSet Ω (Q y) q} ≤ α) :
    μ {y | fourWayReport (cC y) (cG y) = .modelIncompatible} ≤ α :=
  (measure_mono (certified_incompatible_subset Ω Q q xmap G θs cC cG)).trans hcov

/-! ### T9 projection containment (N1a) -/

theorem projection_event_subset {ι : Type*} {β : ι → Type*} (f : ∀ i, Θ → β i)
    (C : Y → Set Θ) (θs : Θ) :
    {y | θs ∈ C y} ⊆ {y | ∀ i, f i θs ∈ f i '' C y} :=
  fun _ hy i => Set.mem_image_of_mem (f i) hy

theorem superset_event_subset {β : Type*} (f : Θ → β) (C : Y → Set Θ) (J : Y → Set β)
    (hJ : ∀ y, f '' C y ⊆ J y) (θs : Θ) : {y | θs ∈ C y} ⊆ {y | f θs ∈ J y} :=
  fun y hy => hJ y (Set.mem_image_of_mem f hy)

theorem interval_event_subset (g : Θ → EReal) (C : Y → Set Θ) (θs : Θ) :
    {y | θs ∈ C y} ⊆ {y | sInf (g '' C y) ≤ g θs ∧ g θs ≤ sSup (g '' C y)} :=
  fun _ hy => ⟨sInf_le (Set.mem_image_of_mem g hy), le_sSup (Set.mem_image_of_mem g hy)⟩

/-! ### T10 union of scenarios / data-dependent domain -/

theorem union_event_subset {ι : Type*} (C : ι → Y → Set Θ) (s0 : ι) (θs : Θ) :
    {y | θs ∈ C s0 y} ⊆ {y | θs ∈ ⋃ s, C s y} :=
  fun _ hy => Set.mem_iUnion.mpr ⟨s0, hy⟩

theorem union_noncoverage_le [MeasurableSpace Y] (μ : Measure Y) {ι : Type*}
    (C : ι → Y → Set Θ) (s0 : ι) (θs : Θ) :
    μ {y | θs ∉ ⋃ s, C s y} ≤ μ {y | θs ∉ C s0 y} :=
  measure_mono fun _ hy h0 => hy (Set.mem_iUnion.mpr ⟨s0, h0⟩)

theorem intersection_negative_control :
    ∃ C : Bool → Unit → Set Unit, () ∈ C true () ∧ () ∉ ⋂ s, C s () := by
  refine ⟨fun b _ => if b then Set.univ else ∅, by simp, ?_⟩
  intro h
  have h0 := Set.mem_iInter.mp h false
  simp at h0

theorem data_domain_split (Ωy : Y → Set Θ) (Q : Y → Θ → ℝ) (q : ℝ) (θs : Θ) :
    {y | θs ∉ confSet (Ωy y) (Q y) q} ⊆ {y | θs ∉ Ωy y} ∪ {y | q < Q y θs} := by
  intro y hy
  by_cases hΩ : θs ∈ Ωy y
  · right
    show q < Q y θs
    by_contra hle
    exact hy ⟨hΩ, not_lt.mp hle⟩
  · left
    exact hΩ

theorem alpha_delta_bound [MeasurableSpace Y] (μ : Measure Y) (α δ : ENNReal)
    (Ωy : Y → Set Θ) (Q : Y → Θ → ℝ) (q : ℝ) (θs : Θ)
    (hδ : μ {y | θs ∉ Ωy y} ≤ δ) (hα : μ {y | q < Q y θs} ≤ α) :
    μ {y | θs ∉ confSet (Ωy y) (Q y) q} ≤ δ + α :=
  (measure_mono (data_domain_split Ωy Q q θs)).trans
    ((measure_union_le _ _).trans (add_le_add hδ hα))

end Decision

/-! ### T11 concrete geodesic null, eq. (1)-(2) -/

/-- Physical first jet `x = (ζ, h0, h1, h2)` (12 components when `h2` is symmetric
trace-free; that restriction belongs to the domain `Ω`, not to `G`). -/
structure FirstJet where
  ζ : Fin 3 → ℝ
  h0 : ℝ
  h1 : Fin 3 → ℝ
  h2 : Matrix (Fin 3) (Fin 3) ℝ

/-- `ζ0 = sqrt(1+|ζ|²)`. -/
def zeta0 (x : FirstJet) : ℝ := Real.sqrt (1 + ∑ i, x.ζ i ^ 2)

/-- `u = (ζ0, ζ)`. -/
def uVec (x : FirstJet) : Fin 4 → ℝ := ![zeta0 x, x.ζ 0, x.ζ 1, x.ζ 2]

/-- `S00 = h0, S0i = -h1i/2, Sij = h2ij` (symmetric lift). -/
def Smat (x : FirstJet) : Matrix (Fin 4) (Fin 4) ℝ :=
  !![x.h0, -x.h1 0 / 2, -x.h1 1 / 2, -x.h1 2 / 2;
     -x.h1 0 / 2, x.h2 0 0, x.h2 0 1, x.h2 0 2;
     -x.h1 1 / 2, x.h2 1 0, x.h2 1 1, x.h2 1 2;
     -x.h1 2 / 2, x.h2 2 0, x.h2 2 1, x.h2 2 2]

/-- Signature `(-,+,+,+)`. -/
def minkowski : Matrix (Fin 4) (Fin 4) ℝ := Matrix.diagonal ![-1, 1, 1, 1]

/-- `S(u,u)`. -/
def SuU (x : FirstJet) : ℝ := ∑ a, ∑ b, Smat x a b * uVec x a * uVec x b

/-- `B = S + S(u,u) g`. -/
def Bmat (x : FirstJet) : Matrix (Fin 4) (Fin 4) ℝ := Smat x + SuU x • minkowski

/-- `(B u)_a = B_ab u^b`. -/
def Bu (x : FirstJet) : Fin 4 → ℝ := fun a => ∑ b, Bmat x a b * uVec x b

/-- Eq. (2): `G = {x : B_ab(x) u^b(x) = 0}`. -/
def geodesicNull : Set FirstJet := {x | Bu x = 0}

def x0 : FirstJet := ⟨0, 0, 0, 0⟩

def xDip : FirstJet := ⟨0, 0, Pi.single 0 1, 0⟩

theorem Bmat_uu_zero (x : FirstJet) :
    ∑ a, ∑ b, Bmat x a b * uVec x a * uVec x b = 0 := by
  have hz : zeta0 x ^ 2 = 1 + ∑ i, x.ζ i ^ 2 := Real.sq_sqrt (by positivity)
  have hsplit : ∑ a, ∑ b, Bmat x a b * uVec x a * uVec x b
      = (∑ a, ∑ b, Smat x a b * uVec x a * uVec x b)
        + SuU x * ∑ a, ∑ b, minkowski a b * uVec x a * uVec x b := by
    simp only [Bmat, Matrix.add_apply, Matrix.smul_apply, smul_eq_mul, add_mul,
      Finset.sum_add_distrib, Finset.mul_sum]
    congr 1
    refine Finset.sum_congr rfl fun a _ => Finset.sum_congr rfl fun b _ => ?_
    ring
  have hg : ∑ a, ∑ b, minkowski a b * uVec x a * uVec x b = -1 := by
    simp [minkowski, Fin.sum_univ_four, Matrix.diagonal_apply, uVec]
    simp [Fin.sum_univ_three] at hz
    linear_combination (-1 : ℝ) * hz
  rw [hsplit, hg]
  unfold SuU
  ring

theorem mem_geodesicNull_of_zeta_zero (x : FirstJet) (hζ : x.ζ = 0) :
    x ∈ geodesicNull ↔ x.h1 = 0 := by
  have hz : zeta0 x = 1 := by simp [zeta0, hζ]
  have hBu : Bu x = ![0, -x.h1 0 / 2, -x.h1 1 / 2, -x.h1 2 / 2] := by
    funext a
    fin_cases a <;>
      simp [Bu, Bmat, SuU, uVec, hz, hζ, Smat, minkowski, Fin.sum_univ_four,
        Matrix.diagonal_apply]
  show Bu x = 0 ↔ x.h1 = 0
  rw [hBu]
  constructor
  · intro h
    have e1 := congrFun h 1
    have e2 := congrFun h 2
    have e3 := congrFun h 3
    simp at e1 e2 e3
    funext i
    fin_cases i <;> simp [e1, e2, e3]
  · intro h
    funext a
    fin_cases a <;> simp [h]

theorem x0_mem_geodesicNull : x0 ∈ geodesicNull :=
  (mem_geodesicNull_of_zeta_zero x0 rfl).mpr rfl

theorem xDip_not_mem_geodesicNull : xDip ∉ geodesicNull := by
  intro h
  have h1 := congrFun ((mem_geodesicNull_of_zeta_zero xDip rfl).mp h) 0
  simp [xDip] at h1

/-! ### T12 non-vacuity of all four reports on the concrete `G` -/

theorem report1_witness :
    RejectsGeodesicity (confSet {xDip} (fun _ => 0) 0)
      (nullConfSet {xDip} (fun _ => 0) 0 id geodesicNull) := by
  refine ⟨⟨xDip, Set.mem_singleton _, le_refl _⟩, ?_⟩
  refine Set.eq_empty_iff_forall_notMem.mpr ?_
  rintro θ ⟨⟨hθ, -⟩, hG⟩
  rw [Set.mem_singleton_iff] at hθ
  subst hθ
  exact xDip_not_mem_geodesicNull hG

theorem report2_witness :
    NotExcluded (confSet {x0} (fun _ => 0) 0) (nullConfSet {x0} (fun _ => 0) 0 id geodesicNull) :=
  ⟨⟨x0, Set.mem_singleton _, le_refl _⟩, ⟨x0, ⟨Set.mem_singleton _, le_refl _⟩, x0_mem_geodesicNull⟩⟩

theorem report3_witness :
    ModelIncompatible (confSet (∅ : Set FirstJet) (fun _ => 0) 0) ∧
    nullConfSet (∅ : Set FirstJet) (fun _ => 0) 0 id geodesicNull = ∅ :=
  ⟨Set.eq_empty_iff_forall_notMem.mpr fun θ h => Set.notMem_empty θ h.1,
   Set.eq_empty_iff_forall_notMem.mpr fun θ h => Set.notMem_empty θ h.1.1⟩

theorem report4_witness :
    RejectsGeodesicity (confSet {xDip} (fun _ => 0) 0)
      (nullConfSet {xDip} (fun _ => 0) 0 id geodesicNull) ∧
    ∃ cC : Cert (confSet {xDip} (fun _ => (0:ℝ)) 0),
      fourWayReport cC
          (Cert.uncertified : Cert (nullConfSet {xDip} (fun _ => (0:ℝ)) 0 id geodesicNull))
        = .computationallyUnresolved :=
  ⟨report1_witness, .feasible xDip ⟨Set.mem_singleton _, le_refl _⟩, rfl⟩

theorem boundary_witness :
    NotExcluded (confSet {x0} (fun _ => 1) 1) (nullConfSet {x0} (fun _ => 1) 1 id geodesicNull) ∧
    {θ : FirstJet | θ ∈ ({x0} : Set FirstJet) ∧ (fun _ => (1:ℝ)) θ < 1} = ∅ :=
  ⟨⟨⟨x0, Set.mem_singleton _, le_refl _⟩,
     ⟨x0, ⟨Set.mem_singleton _, le_refl _⟩, x0_mem_geodesicNull⟩⟩,
   Set.eq_empty_iff_forall_notMem.mpr fun _ h => lt_irrefl _ h.2⟩

end G08C

end
