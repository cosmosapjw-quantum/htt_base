import Mathlib
import G08BGaussianLaw
import G08DCertificates

/-!
# G08-D (part II): measurable confidence inversion, coverage composition, size control

Owning source: `statistics/NATIVE_INFERENCE_THEOREMS.md`
(sha256 e215836882047c50a1a5ae6da605d62aa2c553d0de055e279eee3ce35ec8e322): (7)-(8) l.79-84,
ν=0 rule l.90, N1a l.96-103, N2 l.114-116, certification l.120, union rules l.69 and l.182,
general inversion l.180.  Targets frozen in `../FROZEN_TARGETS.md`.

Reused unchanged: `G08BGaussianLaw` (Qstat, threshold, coverage, coverage_rank_zero,
measurable_Qstat) and `G08CFourWay` (via `G08DCertificates`).

* Measurability: sufficient conditions in the original parameter space (countable Θ, or
  compact / σ-compact Ω with continuity in θ and measurability in y).  A negative control shows
  that measurable sections alone do not make the projection (nonemptiness) event measurable.
* G08-C's conditional size control is made unconditional in the known-C Gaussian case by
  deriving its coverage hypothesis from G08-B (equality, with the measurability proved here).
-/

namespace G08D

open MeasureTheory ProbabilityTheory Matrix WithLp G08C TopologicalSpace

universe u v w

/-! ## Measurability -/

section Measurability

variable {Θ : Type u} {P : Type v} {Y : Type w}

theorem measurableSet_confGraph [MeasurableSpace Y] [MeasurableSpace Θ] {Ω : Set Θ}
    (hΩ : MeasurableSet Ω) {Q : Y → Θ → ℝ} (hQ : Measurable (fun p : Y × Θ => Q p.1 p.2))
    (q : ℝ) : MeasurableSet {p : Y × Θ | p.2 ∈ confSet Ω (Q p.1) q} := by
  have h : {p : Y × Θ | p.2 ∈ confSet Ω (Q p.1) q} =
      Prod.snd ⁻¹' Ω ∩ (fun p : Y × Θ => Q p.1 p.2) ⁻¹' Set.Iic q := by
    ext p
    simp only [confSet, Set.mem_setOf_eq, Set.mem_inter_iff, Set.mem_preimage, Set.mem_Iic]
  rw [h]
  exact (measurable_snd hΩ).inter (hQ measurableSet_Iic)

theorem measurableSet_nullGraph [MeasurableSpace Y] [MeasurableSpace Θ] {Ω : Set Θ}
    (hΩ : MeasurableSet Ω) {Q : Y → Θ → ℝ} (hQ : Measurable (fun p : Y × Θ => Q p.1 p.2))
    (q : ℝ) [MeasurableSpace P] {xmap : Θ → P} (hx : Measurable xmap) {G : Set P}
    (hG : MeasurableSet G) :
    MeasurableSet {p : Y × Θ | p.2 ∈ nullConfSet Ω (Q p.1) q xmap G} := by
  have h : {p : Y × Θ | p.2 ∈ nullConfSet Ω (Q p.1) q xmap G} =
      {p : Y × Θ | p.2 ∈ confSet Ω (Q p.1) q} ∩ Prod.snd ⁻¹' (xmap ⁻¹' G) := by
    ext p
    simp only [nullConfSet, Set.mem_setOf_eq, Set.mem_inter_iff, Set.mem_preimage]
  rw [h]
  exact (measurableSet_confGraph hΩ hQ q).inter (measurable_snd (hx hG))

theorem measurableSet_coverage [MeasurableSpace Y] (Ω : Set Θ) {Q : Y → Θ → ℝ} (q : ℝ)
    (θs : Θ) (hQ : Measurable (fun y => Q y θs)) :
    MeasurableSet {y | θs ∈ confSet Ω (Q y) q} := by
  by_cases hθ : θs ∈ Ω
  · have h : {y | θs ∈ confSet Ω (Q y) q} = (fun y => Q y θs) ⁻¹' Set.Iic q := by
      ext y
      simp [confSet, hθ]
    rw [h]
    exact hQ measurableSet_Iic
  · have h : {y | θs ∈ confSet Ω (Q y) q} = ∅ := by
      ext y
      simp [confSet, hθ]
    rw [h]
    exact MeasurableSet.empty

theorem measurableSet_noncoverage [MeasurableSpace Y] (Ω : Set Θ) {Q : Y → Θ → ℝ} (q : ℝ)
    (θs : Θ) (hQ : Measurable (fun y => Q y θs)) :
    MeasurableSet {y | θs ∉ confSet Ω (Q y) q} :=
  (measurableSet_coverage Ω q θs hQ).compl

theorem measurableSet_nonempty_countable [MeasurableSpace Y] [Countable Θ] (Ω : Set Θ)
    {Q : Y → Θ → ℝ} (q : ℝ) (hQ : ∀ θ, Measurable (fun y => Q y θ)) :
    MeasurableSet {y | (confSet Ω (Q y) q).Nonempty} := by
  have h : {y | (confSet Ω (Q y) q).Nonempty} = ⋃ θ : Θ, {y | θ ∈ confSet Ω (Q y) q} := by
    ext y
    simp only [Set.mem_setOf_eq, Set.mem_iUnion, Set.Nonempty]
  rw [h]
  exact MeasurableSet.iUnion fun θ => measurableSet_coverage Ω q θ (hQ θ)

theorem measurableSet_nonempty_compact [MeasurableSpace Y] [TopologicalSpace Θ]
    [SecondCountableTopology Θ] {K : Set Θ} (hK : IsCompact K) {Q : Y → Θ → ℝ} (q : ℝ)
    (hcont : ∀ y, ContinuousOn (Q y) K) (hQ : ∀ θ, Measurable (fun y => Q y θ)) :
    MeasurableSet {y | (confSet K (Q y) q).Nonempty} := by
  obtain ⟨D, hDc, hDd⟩ := TopologicalSpace.exists_countable_dense K
  have key : {y | (confSet K (Q y) q).Nonempty} =
      ⋂ n : ℕ, ⋃ d ∈ D, {y | Q y (d : Θ) < q + 1 / ((n : ℝ) + 1)} := by
    ext y
    simp only [Set.mem_setOf_eq, Set.mem_iInter, Set.mem_iUnion, exists_prop]
    constructor
    · rintro ⟨θ, hθK, hθq⟩ n
      have hpos : (0 : ℝ) < 1 / ((n : ℝ) + 1) := by positivity
      have hc : Continuous (K.restrict (Q y)) := (hcont y).restrict
      have hU : IsOpen {z : K | K.restrict (Q y) z < q + 1 / ((n : ℝ) + 1)} :=
        isOpen_lt hc continuous_const
      have hne : ({z : K | K.restrict (Q y) z < q + 1 / ((n : ℝ) + 1)}).Nonempty := by
        refine ⟨⟨θ, hθK⟩, ?_⟩
        simp only [Set.mem_setOf_eq, Set.restrict_apply]
        linarith
      obtain ⟨d, hdD, hd⟩ := hDd.exists_mem_open hU hne
      exact ⟨d, hdD, hd⟩
    · intro h
      by_contra hne
      obtain ⟨d0, -, -⟩ := h 0
      obtain ⟨θ0, hθ0K, hmin⟩ := hK.exists_isMinOn ⟨d0.1, d0.2⟩ (hcont y)
      have hgt : q < Q y θ0 := by
        by_contra hle
        exact hne ⟨θ0, hθ0K, not_lt.mp hle⟩
      obtain ⟨n, hn⟩ := exists_nat_one_div_lt (sub_pos.mpr hgt)
      obtain ⟨d, -, hd⟩ := h n
      have h1 := isMinOn_iff.mp hmin d.1 d.2
      linarith
  rw [key]
  exact MeasurableSet.iInter fun n =>
    MeasurableSet.biUnion hDc fun d _ => measurableSet_lt (hQ d.1) measurable_const

theorem measurableSet_nonempty_sigmaCompact [MeasurableSpace Y] [TopologicalSpace Θ]
    [SecondCountableTopology Θ] {Ω : Set Θ} (Kn : ℕ → Set Θ) (hK : ∀ i, IsCompact (Kn i))
    (hΩ : Ω = ⋃ i, Kn i) {Q : Y → Θ → ℝ} (q : ℝ) (hcont : ∀ y, ContinuousOn (Q y) Ω)
    (hQ : ∀ θ, Measurable (fun y => Q y θ)) :
    MeasurableSet {y | (confSet Ω (Q y) q).Nonempty} := by
  have hsub : ∀ i, Kn i ⊆ Ω := fun i => by rw [hΩ]; exact Set.subset_iUnion Kn i
  have h : {y | (confSet Ω (Q y) q).Nonempty} =
      ⋃ i, {y | (confSet (Kn i) (Q y) q).Nonempty} := by
    ext y
    simp only [Set.mem_setOf_eq, Set.mem_iUnion]
    constructor
    · rintro ⟨θ, hθ, hq⟩
      rw [hΩ] at hθ
      obtain ⟨i, hi⟩ := Set.mem_iUnion.mp hθ
      exact ⟨i, θ, hi, hq⟩
    · rintro ⟨i, θ, hi, hq⟩
      exact ⟨θ, hsub i hi, hq⟩
  rw [h]
  exact MeasurableSet.iUnion fun i =>
    measurableSet_nonempty_compact (hK i) q (fun y => (hcont y).mono (hsub i)) hQ

theorem measurableSet_null_nonempty_sigmaCompact [MeasurableSpace Y] [TopologicalSpace Θ]
    [SecondCountableTopology Θ] {Ω : Set Θ} (Kn : ℕ → Set Θ) (hK : ∀ i, IsCompact (Kn i))
    (hΩ : Ω = ⋃ i, Kn i) {Q : Y → Θ → ℝ} (q : ℝ) (hcont : ∀ y, ContinuousOn (Q y) Ω)
    (hQ : ∀ θ, Measurable (fun y => Q y θ)) [T2Space Θ] [TopologicalSpace P] {xmap : Θ → P}
    (hx : ContinuousOn xmap Ω) {G : Set P} (hG : IsClosed G) :
    MeasurableSet {y | (nullConfSet Ω (Q y) q xmap G).Nonempty} := by
  have hsub : ∀ i, Kn i ⊆ Ω := fun i => by rw [hΩ]; exact Set.subset_iUnion Kn i
  have hKG : ∀ i, IsCompact (Kn i ∩ xmap ⁻¹' G) := fun i =>
    (hK i).of_isClosed_subset
      ((hx.mono (hsub i)).preimage_isClosed_of_isClosed (hK i).isClosed hG)
      Set.inter_subset_left
  have h : {y | (nullConfSet Ω (Q y) q xmap G).Nonempty} =
      ⋃ i, {y | (confSet (Kn i ∩ xmap ⁻¹' G) (Q y) q).Nonempty} := by
    ext y
    simp only [Set.mem_setOf_eq, Set.mem_iUnion]
    constructor
    · rintro ⟨θ, ⟨hθ, hq⟩, hG'⟩
      rw [hΩ] at hθ
      obtain ⟨i, hi⟩ := Set.mem_iUnion.mp hθ
      exact ⟨i, θ, ⟨hi, hG'⟩, hq⟩
    · rintro ⟨i, θ, ⟨hi, hG'⟩, hq⟩
      exact ⟨θ, ⟨hsub i hi, hq⟩, hG'⟩
  rw [h]
  exact MeasurableSet.iUnion fun i => measurableSet_nonempty_compact (hKG i) q
    (fun y => (hcont y).mono (Set.inter_subset_left.trans (hsub i))) hQ

theorem measurableSet_reports [MeasurableSpace Y] [TopologicalSpace Θ]
    [SecondCountableTopology Θ] {Ω : Set Θ} (Kn : ℕ → Set Θ) (hK : ∀ i, IsCompact (Kn i))
    (hΩ : Ω = ⋃ i, Kn i) {Q : Y → Θ → ℝ} (q : ℝ) (hcont : ∀ y, ContinuousOn (Q y) Ω)
    (hQ : ∀ θ, Measurable (fun y => Q y θ)) [T2Space Θ] [TopologicalSpace P] {xmap : Θ → P}
    (hx : ContinuousOn xmap Ω) {G : Set P} (hG : IsClosed G) :
    MeasurableSet {y | RejectsGeodesicity (confSet Ω (Q y) q) (nullConfSet Ω (Q y) q xmap G)} ∧
    MeasurableSet {y | NotExcluded (confSet Ω (Q y) q) (nullConfSet Ω (Q y) q xmap G)} ∧
    MeasurableSet {y | ModelIncompatible (confSet Ω (Q y) q)} := by
  have hA := measurableSet_nonempty_sigmaCompact Kn hK hΩ q hcont hQ
  have hB := measurableSet_null_nonempty_sigmaCompact Kn hK hΩ q hcont hQ hx hG
  refine ⟨?_, ?_, ?_⟩
  · have h : {y | RejectsGeodesicity (confSet Ω (Q y) q) (nullConfSet Ω (Q y) q xmap G)} =
        {y | (confSet Ω (Q y) q).Nonempty} ∩ {y | (nullConfSet Ω (Q y) q xmap G).Nonempty}ᶜ := by
      ext y
      simp [RejectsGeodesicity, Set.not_nonempty_iff_eq_empty]
    rw [h]
    exact hA.inter hB.compl
  · have h : {y | NotExcluded (confSet Ω (Q y) q) (nullConfSet Ω (Q y) q xmap G)} =
        {y | (confSet Ω (Q y) q).Nonempty} ∩ {y | (nullConfSet Ω (Q y) q xmap G).Nonempty} := by
      ext y
      simp [NotExcluded]
    rw [h]
    exact hA.inter hB
  · have h : {y | ModelIncompatible (confSet Ω (Q y) q)} =
        {y | (confSet Ω (Q y) q).Nonempty}ᶜ := by
      ext y
      simp [ModelIncompatible, Set.not_nonempty_iff_eq_empty]
    rw [h]
    exact hA.compl

/-- countable–cocountable σ-algebra on ℝ (a local definition, not an instance) -/
def ccMeasurableSpace : MeasurableSpace ℝ where
  MeasurableSet' s := s.Countable ∨ sᶜ.Countable
  measurableSet_empty := Or.inl Set.countable_empty
  measurableSet_compl s hs := by
    rcases hs with h | h
    · exact Or.inr (by rwa [compl_compl])
    · exact Or.inl h
  measurableSet_iUnion f hf := by
    by_cases h : ∀ i, (f i).Countable
    · exact Or.inl (Set.countable_iUnion h)
    · push_neg at h
      obtain ⟨i, hi⟩ := h
      exact Or.inr (((hf i).resolve_left hi).mono
        (Set.compl_subset_compl.mpr (Set.subset_iUnion f i)))

theorem projection_not_auto_measurable :
    ∃ (m : MeasurableSpace ℝ) (Ω : Set ℝ) (Q : ℝ → ℝ → ℝ) (q : ℝ),
      (∀ θ, @Measurable ℝ ℝ m _ (fun y => Q y θ)) ∧
      (∀ θs, MeasurableSet[m] {y | θs ∈ confSet Ω (Q y) q}) ∧
      ¬ MeasurableSet[m] {y | (confSet Ω (Q y) q).Nonempty} := by
  classical
  refine ⟨ccMeasurableSpace, Set.Ioi 0, fun y θ => if θ = y then 0 else 1, 0, ?_, ?_, ?_⟩
  · intro θ s _
    by_cases h1 : (1 : ℝ) ∈ s
    · refine Or.inr ((Set.countable_singleton θ).mono ?_)
      intro y hy
      by_contra hne
      apply hy
      show (if θ = y then (0 : ℝ) else 1) ∈ s
      rw [if_neg (fun h => hne (Set.mem_singleton_iff.mpr h.symm))]
      exact h1
    · refine Or.inl ((Set.countable_singleton θ).mono ?_)
      intro y hy
      by_contra hne
      apply h1
      have h2 : (if θ = y then (0 : ℝ) else 1) ∈ s := hy
      rwa [if_neg (fun h => hne (Set.mem_singleton_iff.mpr h.symm))] at h2
  · intro θs
    refine Or.inl ((Set.countable_singleton θs).mono ?_)
    rintro y ⟨-, hle⟩
    by_contra hne
    have hle' : (if θs = y then (0 : ℝ) else 1) ≤ 0 := hle
    rw [if_neg (fun h => hne (Set.mem_singleton_iff.mpr h.symm))] at hle'
    norm_num at hle'
  · intro hmeas
    change MeasurableSet[ccMeasurableSpace]
      {y : ℝ | (confSet (Set.Ioi 0) (fun θ => if θ = y then (0 : ℝ) else 1) 0).Nonempty}
      at hmeas
    have hset : {y : ℝ | (confSet (Set.Ioi 0) (fun θ => if θ = y then (0 : ℝ) else 1) 0).Nonempty}
        = Set.Ioi 0 := by
      ext y
      constructor
      · rintro ⟨θ, hθ, hle⟩
        by_cases h : θ = y
        · subst h
          exact hθ
        · have hle' : (if θ = y then (0 : ℝ) else 1) ≤ 0 := hle
          rw [if_neg h] at hle'
          norm_num at hle'
      · intro hy
        exact ⟨y, hy, by simp⟩
    rw [hset] at hmeas
    have h' : (Set.Ioi (0 : ℝ)).Countable ∨ (Set.Ioi (0 : ℝ))ᶜ.Countable := hmeas
    rcases h' with h | h
    · have h0 := h.measure_zero volume
      rw [Real.volume_Ioi] at h0
      exact ENNReal.top_ne_zero h0
    · rw [Set.compl_Ioi] at h
      have h0 := h.measure_zero volume
      rw [Real.volume_Iic] at h0
      exact ENNReal.top_ne_zero h0

end Measurability

/-! ## General inversion (l.180) -/

section General

variable {Θ : Type u} {Y : Type w}

theorem general_inversion_coverage [MeasurableSpace Y] (μ : Θ → Measure Y) (R : Θ → Set Y)
    (p : ENNReal) (hR : ∀ θ, p ≤ μ θ (R θ)) (θs : Θ) :
    p ≤ μ θs {y | θs ∈ {θ | y ∈ R θ}} :=
  hR θs

theorem general_inversion_projection [MeasurableSpace Y] (μ : Θ → Measure Y) (R : Θ → Set Y)
    (p : ENNReal) (hR : ∀ θ, p ≤ μ θ (R θ)) (θs : Θ) {ι : Type} {β : ι → Type}
    (f : ∀ i, Θ → β i) : p ≤ μ θs {y | ∀ i, f i θs ∈ f i '' {θ | y ∈ R θ}} :=
  (hR θs).trans (measure_mono fun _ hy i => Set.mem_image_of_mem (f i) hy)

end General

/-! ## Known-C Gaussian case: unconditional size control -/

section Gaussian

open G08BGaussianLaw (Qstat threshold coverage coverage_rank_zero measurable_Qstat)

variable {n k : ℕ} {Θ : Type u} {P : Type v}

theorem gaussian_reports_measurable [TopologicalSpace Θ] [SecondCountableTopology Θ]
    [T2Space Θ] [TopologicalSpace P] (W : Matrix (Fin n) (Fin n) ℝ)
    (F : Matrix (Fin n) (Fin k) ℝ) (X : Matrix (Fin k) (Fin n) ℝ)
    (m : Θ → EuclideanSpace ℝ (Fin n)) {Ω : Set Θ} (Kn : ℕ → Set Θ)
    (hK : ∀ i, IsCompact (Kn i)) (hΩ : Ω = ⋃ i, Kn i) (hm : ContinuousOn m Ω) {xmap : Θ → P}
    (hx : ContinuousOn xmap Ω) {G : Set P} (hG : IsClosed G) (q : ℝ) :
    MeasurableSet {y : EuclideanSpace ℝ (Fin n) |
      RejectsGeodesicity (confSet Ω (fun θ => Qstat W F X (m θ) y) q)
        (nullConfSet Ω (fun θ => Qstat W F X (m θ) y) q xmap G)} ∧
    MeasurableSet {y : EuclideanSpace ℝ (Fin n) |
      NotExcluded (confSet Ω (fun θ => Qstat W F X (m θ) y) q)
        (nullConfSet Ω (fun θ => Qstat W F X (m θ) y) q xmap G)} ∧
    MeasurableSet {y : EuclideanSpace ℝ (Fin n) |
      ModelIncompatible (confSet Ω (fun θ => Qstat W F X (m θ) y) q)} := by
  have hcQ : ∀ y : EuclideanSpace ℝ (Fin n),
      Continuous (fun v : EuclideanSpace ℝ (Fin n) => Qstat W F X v y) := by
    intro y
    unfold Qstat
    fun_prop
  exact measurableSet_reports (Q := fun y θ => Qstat W F X (m θ) y) Kn hK hΩ q
    (fun y => (hcQ y).comp_continuousOn hm) (fun θ => measurable_Qstat W F X (m θ)) hx hG

theorem gaussian_noncoverage_eq (Ω : Set Θ) (m : Θ → EuclideanSpace ℝ (Fin n)) (θs : Θ)
    (hθ : θs ∈ Ω) (C W : Matrix (Fin n) (Fin n) ℝ) (F : Matrix (Fin n) (Fin k) ℝ)
    (X : Matrix (Fin k) (Fin n) ℝ) (hC : C.PosDef) (hW : IsUnit W ∧ W * C * Wᵀ = 1)
    (hX : G08AWhitening.IsMoorePenrose (W * F) X) (β : Fin k → ℝ) {α : ℝ} (hα0 : 0 < α)
    (hα1 : α < 1) (hν : 0 < n - F.rank) :
    (multivariateGaussian (m θs + toLp 2 (F *ᵥ β)) C)
      {y | θs ∉ confSet Ω (fun θ => Qstat W F X (m θ) y) (threshold (n - F.rank) α)} =
      ENNReal.ofReal α := by
  have hcov := coverage Ω m θs hθ C W F X hC hW hX β hα0 hα1 hν
  have hmeas : MeasurableSet
      {y | θs ∈ G08BGaussianLaw.confSet Ω m W F X (threshold (n - F.rank) α) y} :=
    measurableSet_coverage (Q := fun y θ => Qstat W F X (m θ) y) Ω _ θs
      (measurable_Qstat W F X (m θs))
  have hset : {y | θs ∉ confSet Ω (fun θ => Qstat W F X (m θ) y) (threshold (n - F.rank) α)} =
      {y | θs ∈ G08BGaussianLaw.confSet Ω m W F X (threshold (n - F.rank) α) y}ᶜ := rfl
  rw [hset, prob_compl_eq_one_sub hmeas, hcov, ← ENNReal.ofReal_one,
    ← ENNReal.ofReal_sub _ (by linarith)]
  congr 1
  ring

theorem gaussian_size_control (Ω : Set Θ) (m : Θ → EuclideanSpace ℝ (Fin n)) (θs : Θ)
    (hθ : θs ∈ Ω) (C W : Matrix (Fin n) (Fin n) ℝ) (F : Matrix (Fin n) (Fin k) ℝ)
    (X : Matrix (Fin k) (Fin n) ℝ) (hC : C.PosDef) (hW : IsUnit W ∧ W * C * Wᵀ = 1)
    (hX : G08AWhitening.IsMoorePenrose (W * F) X) (β : Fin k → ℝ) {α : ℝ} (hα0 : 0 < α)
    (hα1 : α < 1) (hν : 0 < n - F.rank) (xmap : Θ → P) (G : Set P) (hG : xmap θs ∈ G)
    (cC : ∀ y, Cert (confSet Ω (fun θ => Qstat W F X (m θ) y) (threshold (n - F.rank) α)))
    (cG : ∀ y, Cert (nullConfSet Ω (fun θ => Qstat W F X (m θ) y)
      (threshold (n - F.rank) α) xmap G)) :
    (multivariateGaussian (m θs + toLp 2 (F *ᵥ β)) C)
      {y | fourWayReport (cC y) (cG y) = Report.geodesicityRejected ∨
           fourWayReport (cC y) (cG y) = Report.modelIncompatible} ≤ ENNReal.ofReal α :=
  size_control_of_coverage _ _ Ω (fun y θ => Qstat W F X (m θ) y) _ xmap G hG cC cG
    (gaussian_noncoverage_eq Ω m θs hθ C W F X hC hW hX β hα0 hα1 hν).le

theorem gaussian_semantic_size (Ω : Set Θ) (m : Θ → EuclideanSpace ℝ (Fin n)) (θs : Θ)
    (hθ : θs ∈ Ω) (C W : Matrix (Fin n) (Fin n) ℝ) (F : Matrix (Fin n) (Fin k) ℝ)
    (X : Matrix (Fin k) (Fin n) ℝ) (hC : C.PosDef) (hW : IsUnit W ∧ W * C * Wᵀ = 1)
    (hX : G08AWhitening.IsMoorePenrose (W * F) X) (β : Fin k → ℝ) {α : ℝ} (hα0 : 0 < α)
    (hα1 : α < 1) (hν : 0 < n - F.rank) (xmap : Θ → P) (G : Set P) (hG : xmap θs ∈ G) :
    (multivariateGaussian (m θs + toLp 2 (F *ᵥ β)) C)
      {y | RejectsGeodesicity (confSet Ω (fun θ => Qstat W F X (m θ) y) (threshold (n - F.rank) α))
            (nullConfSet Ω (fun θ => Qstat W F X (m θ) y) (threshold (n - F.rank) α) xmap G) ∨
          ModelIncompatible (confSet Ω (fun θ => Qstat W F X (m θ) y)
            (threshold (n - F.rank) α))} ≤ ENNReal.ofReal α := by
  rw [← gaussian_noncoverage_eq Ω m θs hθ C W F X hC hW hX β hα0 hα1 hν]
  exact measure_mono fun y hy =>
    null_errors_subset_noncoverage Ω (fun y θ => Qstat W F X (m θ) y) _ xmap G hG hy

theorem gaussian_incompatible_size (Ω : Set Θ) (m : Θ → EuclideanSpace ℝ (Fin n)) (θs : Θ)
    (hθ : θs ∈ Ω) (C W : Matrix (Fin n) (Fin n) ℝ) (F : Matrix (Fin n) (Fin k) ℝ)
    (X : Matrix (Fin k) (Fin n) ℝ) (hC : C.PosDef) (hW : IsUnit W ∧ W * C * Wᵀ = 1)
    (hX : G08AWhitening.IsMoorePenrose (W * F) X) (β : Fin k → ℝ) {α : ℝ} (hα0 : 0 < α)
    (hα1 : α < 1) (hν : 0 < n - F.rank) (xmap : Θ → P) (G : Set P)
    (cC : ∀ y, Cert (confSet Ω (fun θ => Qstat W F X (m θ) y) (threshold (n - F.rank) α)))
    (cG : ∀ y, Cert (nullConfSet Ω (fun θ => Qstat W F X (m θ) y)
      (threshold (n - F.rank) α) xmap G)) :
    (multivariateGaussian (m θs + toLp 2 (F *ᵥ β)) C)
      {y | fourWayReport (cC y) (cG y) = Report.modelIncompatible} ≤ ENNReal.ofReal α := by
  rw [← gaussian_noncoverage_eq Ω m θs hθ C W F X hC hW hX β hα0 hα1 hν]
  exact measure_mono
    (certified_incompatible_subset Ω (fun y θ => Qstat W F X (m θ) y) _ xmap G θs cC cG)

theorem gaussian_sourceDecision_size (Ω : Set Θ) (m : Θ → EuclideanSpace ℝ (Fin n)) (θs : Θ)
    (hθ : θs ∈ Ω) (C W : Matrix (Fin n) (Fin n) ℝ) (F : Matrix (Fin n) (Fin k) ℝ)
    (X : Matrix (Fin k) (Fin n) ℝ) (hC : C.PosDef) (hW : IsUnit W ∧ W * C * Wᵀ = 1)
    (hX : G08AWhitening.IsMoorePenrose (W * F) X) (β : Fin k → ℝ) {α : ℝ} (hα0 : 0 < α)
    (hα1 : α < 1) (hν : 0 < n - F.rank) (xmap : Θ → P) (G : Set P) (hG : xmap θs ∈ G)
    (rC : ∀ y, OptReport Ω (fun θ => Qstat W F X (m θ) y) (threshold (n - F.rank) α))
    (rG : ∀ y, OptReport (Ω ∩ xmap ⁻¹' G) (fun θ => Qstat W F X (m θ) y)
      (threshold (n - F.rank) α)) :
    (multivariateGaussian (m θs + toLp 2 (F *ᵥ β)) C)
      {y | sourceDecision (rC y) (rG y) = Report.geodesicityRejected ∨
           sourceDecision (rC y) (rG y) = Report.modelIncompatible} ≤ ENNReal.ofReal α :=
  gaussian_size_control Ω m θs hθ C W F X hC hW hX β hα0 hα1 hν xmap G hG
    (fun y => (rC y).toCert)
    (fun y => certCongr (nullConfSet_eq_confSet_inter Ω _ _ xmap G) (rG y).toCert)

theorem gaussian_error_envelope (Ω : Set Θ) (m : Θ → EuclideanSpace ℝ (Fin n)) (θs : Θ)
    (hθ : θs ∈ Ω) (C W : Matrix (Fin n) (Fin n) ℝ) (F : Matrix (Fin n) (Fin k) ℝ)
    (X : Matrix (Fin k) (Fin n) ℝ) (hC : C.PosDef) (hW : IsUnit W ∧ W * C * Wᵀ = 1)
    (hX : G08AWhitening.IsMoorePenrose (W * F) X) (β : Fin k → ℝ) {α : ℝ} (hα0 : 0 < α)
    (hα1 : α < 1) (hν : 0 < n - F.rank) (xmap : Θ → P) (G : Set P) (hG : xmap θs ∈ G)
    (rC : ∀ y, OptReport Ω (fun θ => Qstat W F X (m θ) y) (threshold (n - F.rank) α))
    (rG : ∀ y, OptReport (Ω ∩ xmap ⁻¹' G) (fun θ => Qstat W F X (m θ) y)
      (threshold (n - F.rank) α)) :
    ∃ E, MeasurableSet E ∧ (multivariateGaussian (m θs + toLp 2 (F *ᵥ β)) C) E =
      ENNReal.ofReal α ∧
      {y | sourceDecision (rC y) (rG y) = Report.geodesicityRejected ∨
           sourceDecision (rC y) (rG y) = Report.modelIncompatible} ⊆ E :=
  ⟨{y | θs ∉ confSet Ω (fun θ => Qstat W F X (m θ) y) (threshold (n - F.rank) α)},
    measurableSet_noncoverage (Q := fun y θ => Qstat W F X (m θ) y) Ω _ θs
      (measurable_Qstat W F X (m θs)),
    gaussian_noncoverage_eq Ω m θs hθ C W F X hC hW hX β hα0 hα1 hν,
    certified_null_errors_subset Ω (fun y θ => Qstat W F X (m θ) y) _ xmap G hG
      (fun y => (rC y).toCert)
      (fun y => certCongr (nullConfSet_eq_confSet_inter Ω _ _ xmap G) (rG y).toCert)⟩

theorem gaussian_size_rank_zero (Ω : Set Θ) (m : Θ → EuclideanSpace ℝ (Fin n)) (θs : Θ)
    (hθ : θs ∈ Ω) (C W : Matrix (Fin n) (Fin n) ℝ) (F : Matrix (Fin n) (Fin k) ℝ)
    (X : Matrix (Fin k) (Fin n) ℝ) (hC : C.PosDef) (hW : IsUnit W ∧ W * C * Wᵀ = 1)
    (hX : G08AWhitening.IsMoorePenrose (W * F) X) (β : Fin k → ℝ) (α : ℝ)
    (hν : n - F.rank = 0) (xmap : Θ → P) (G : Set P) (hG : xmap θs ∈ G)
    (cC : ∀ y, Cert (confSet Ω (fun θ => Qstat W F X (m θ) y) (threshold (n - F.rank) α)))
    (cG : ∀ y, Cert (nullConfSet Ω (fun θ => Qstat W F X (m θ) y)
      (threshold (n - F.rank) α) xmap G)) :
    (multivariateGaussian (m θs + toLp 2 (F *ᵥ β)) C)
      {y | fourWayReport (cC y) (cG y) = Report.geodesicityRejected ∨
           fourWayReport (cC y) (cG y) = Report.modelIncompatible} = 0 := by
  have hcov := coverage_rank_zero Ω m θs hθ C W F X hC hW hX β α hν
  have hmeas : MeasurableSet
      {y | θs ∈ G08BGaussianLaw.confSet Ω m W F X (threshold (n - F.rank) α) y} :=
    measurableSet_coverage (Q := fun y θ => Qstat W F X (m θ) y) Ω _ θs
      (measurable_Qstat W F X (m θs))
  have hnc : (multivariateGaussian (m θs + toLp 2 (F *ᵥ β)) C)
      {y | θs ∉ confSet Ω (fun θ => Qstat W F X (m θ) y) (threshold (n - F.rank) α)} = 0 := by
    have hset : {y | θs ∉ confSet Ω (fun θ => Qstat W F X (m θ) y) (threshold (n - F.rank) α)} =
        {y | θs ∈ G08BGaussianLaw.confSet Ω m W F X (threshold (n - F.rank) α) y}ᶜ := rfl
    rw [hset, prob_compl_eq_one_sub hmeas, hcov, tsub_self]
  exact le_antisymm ((measure_mono (certified_null_errors_subset Ω
    (fun y θ => Qstat W F X (m θ) y) _ xmap G hG cC cG)).trans hnc.le) (zero_le _)

theorem gaussian_projection_coverage (Ω : Set Θ) (m : Θ → EuclideanSpace ℝ (Fin n)) (θs : Θ)
    (hθ : θs ∈ Ω) (C W : Matrix (Fin n) (Fin n) ℝ) (F : Matrix (Fin n) (Fin k) ℝ)
    (X : Matrix (Fin k) (Fin n) ℝ) (hC : C.PosDef) (hW : IsUnit W ∧ W * C * Wᵀ = 1)
    (hX : G08AWhitening.IsMoorePenrose (W * F) X) (β : Fin k → ℝ) {α : ℝ} (hα0 : 0 < α)
    (hα1 : α < 1) (hν : 0 < n - F.rank) {ι : Type} {β' : ι → Type} (f : ∀ i, Θ → β' i) :
    ENNReal.ofReal (1 - α) ≤ (multivariateGaussian (m θs + toLp 2 (F *ᵥ β)) C)
      {y | ∀ i, f i θs ∈ f i '' confSet Ω (fun θ => Qstat W F X (m θ) y)
        (threshold (n - F.rank) α)} := by
  rw [← coverage Ω m θs hθ C W F X hC hW hX β hα0 hα1 hν]
  exact measure_mono (projection_event_subset f
    (fun y => confSet Ω (fun θ => Qstat W F X (m θ) y) (threshold (n - F.rank) α)) θs)

theorem gaussian_robust_union_coverage (Ω : Set Θ) (m : Θ → EuclideanSpace ℝ (Fin n)) (θs : Θ)
    (hθ : θs ∈ Ω) (C : Matrix (Fin n) (Fin n) ℝ) (F : Matrix (Fin n) (Fin k) ℝ)
    (hC : C.PosDef) {ι : Type} (S : Set ι) (cs : ι) (hcs : cs ∈ S)
    (Wc : ι → Matrix (Fin n) (Fin n) ℝ) (Xc : ι → Matrix (Fin k) (Fin n) ℝ)
    (hW : IsUnit (Wc cs) ∧ Wc cs * C * (Wc cs)ᵀ = 1)
    (hX : G08AWhitening.IsMoorePenrose (Wc cs * F) (Xc cs)) (β : Fin k → ℝ) {α : ℝ}
    (hα0 : 0 < α) (hα1 : α < 1) (hν : 0 < n - F.rank) :
    ENNReal.ofReal (1 - α) ≤ (multivariateGaussian (m θs + toLp 2 (F *ᵥ β)) C)
      {y | θs ∈ ⋃ c ∈ S, confSet Ω (fun θ => Qstat (Wc c) F (Xc c) (m θ) y)
        (threshold (n - F.rank) α)} := by
  rw [← coverage Ω m θs hθ C (Wc cs) F (Xc cs) hC hW hX β hα0 hα1 hν]
  refine measure_mono fun y hy => ?_
  simp only [Set.mem_setOf_eq, Set.mem_iUnion]
  exact ⟨cs, hcs, hy⟩

theorem gaussian_robust_union_delta (Ω : Set Θ) (m : Θ → EuclideanSpace ℝ (Fin n)) (θs : Θ)
    (hθ : θs ∈ Ω) (C : Matrix (Fin n) (Fin n) ℝ) (F : Matrix (Fin n) (Fin k) ℝ)
    (hC : C.PosDef) {ι : Type} (Sy : EuclideanSpace ℝ (Fin n) → Set ι) (cs : ι)
    (Wc : ι → Matrix (Fin n) (Fin n) ℝ) (Xc : ι → Matrix (Fin k) (Fin n) ℝ)
    (hW : IsUnit (Wc cs) ∧ Wc cs * C * (Wc cs)ᵀ = 1)
    (hX : G08AWhitening.IsMoorePenrose (Wc cs * F) (Xc cs)) (β : Fin k → ℝ) {α : ℝ}
    (hα0 : 0 < α) (hα1 : α < 1) (hν : 0 < n - F.rank) (δ : ENNReal)
    (hδ : (multivariateGaussian (m θs + toLp 2 (F *ᵥ β)) C) {y | cs ∉ Sy y} ≤ δ) :
    (multivariateGaussian (m θs + toLp 2 (F *ᵥ β)) C)
      {y | θs ∉ ⋃ c ∈ Sy y, confSet Ω (fun θ => Qstat (Wc c) F (Xc c) (m θ) y)
        (threshold (n - F.rank) α)} ≤ δ + ENNReal.ofReal α := by
  have hsub : {y | θs ∉ ⋃ c ∈ Sy y, confSet Ω (fun θ => Qstat (Wc c) F (Xc c) (m θ) y)
        (threshold (n - F.rank) α)} ⊆
      {y | cs ∉ Sy y} ∪ {y | θs ∉ confSet Ω (fun θ => Qstat (Wc cs) F (Xc cs) (m θ) y)
        (threshold (n - F.rank) α)} := by
    intro y hy
    by_cases hc : cs ∈ Sy y
    · right
      intro hmem
      exact hy (Set.mem_biUnion hc hmem)
    · left
      exact hc
  calc _ ≤ _ := measure_mono hsub
    _ ≤ _ := measure_union_le _ _
    _ ≤ δ + ENNReal.ofReal α := add_le_add hδ
        (gaussian_noncoverage_eq Ω m θs hθ C (Wc cs) F (Xc cs) hC hW hX β hα0 hα1 hν).le

end Gaussian

end G08D
