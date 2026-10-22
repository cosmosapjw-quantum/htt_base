# G08-C frozen targets (written before any proof compile)

Source: `statistics/NATIVE_INFERENCE_THEOREMS.md` §5 lines 105-120, eq. (1)-(2)
lines 9-23, eq. (7) lines 77-80, N1a lines 96-103, union rule line 69
(sha256 `e215836882047c50a1a5ae6da605d62aa2c553d0de055e279eee3ce35ec8e322`).
See `SOURCE_RECOVERY.md`. Module `lean/G08CFourWay.lean`, namespace `G08C`.
Lean 4.31.0, mathlib `fabf563a7c95a166b8d7b6efca11c8b4dc9d911f`.

Universes `u v w`; `{Θ : Type u}` complete parameter θ; `{X : Type v}` physical
first jet x; `{Y : Type w}` observation y. All theorems are universally
quantified over Ω, Q, q, x(·), G — this includes the specific Q_y of eq. (7)
and the domains (5)/(6); nothing about Q is assumed.

## Definitions (verbatim transcriptions)

```lean
def confSet (Ω : Set Θ) (Q : Θ → ℝ) (q : ℝ) : Set Θ := {θ | θ ∈ Ω ∧ Q θ ≤ q}           -- (7), non-strict
def nullConfSet (Ω : Set Θ) (Q : Θ → ℝ) (q : ℝ) (xmap : Θ → X) (G : Set X) : Set Θ :=
  {θ | θ ∈ confSet Ω Q q ∧ xmap θ ∈ G}                                                -- Cα,G (l.107)
def RejectsGeodesicity (C CG : Set Θ) : Prop := C.Nonempty ∧ CG = ∅                  -- report 1
def NotExcluded (C CG : Set Θ) : Prop := C.Nonempty ∧ CG.Nonempty                    -- report 2
def ModelIncompatible (C : Set Θ) : Prop := C = ∅                                    -- report 3
inductive Report | geodesicityRejected | notExcluded | modelIncompatible | computationallyUnresolved
inductive Cert (S : Set Θ) : Type u                                                  -- l.120 certificates
  | feasible (θ : Θ) (h : θ ∈ S) | excluded (h : S = ∅) | uncertified
def fourWayReport {C CG : Set Θ} : Cert C → Cert CG → Report
  | .excluded _, _ => .modelIncompatible
  | _, .feasible _ _ => .notExcluded
  | .feasible _ _, .excluded _ => .geodesicityRejected
  | _, _ => .computationallyUnresolved                                               -- report 4
```

Concrete geodesic null (eq. (1)-(2), OPTICAL_THEOREMS (8)-(9)):

```lean
structure FirstJet where (ζ : Fin 3 → ℝ) (h0 : ℝ) (h1 : Fin 3 → ℝ) (h2 : Matrix (Fin 3) (Fin 3) ℝ)
def zeta0 (x : FirstJet) : ℝ := Real.sqrt (1 + ∑ i, x.ζ i ^ 2)
def uVec (x : FirstJet) : Fin 4 → ℝ := ![zeta0 x, x.ζ 0, x.ζ 1, x.ζ 2]
def Smat (x : FirstJet) : Matrix (Fin 4) (Fin 4) ℝ :=
  !![x.h0, -x.h1 0 / 2, -x.h1 1 / 2, -x.h1 2 / 2;
     -x.h1 0 / 2, x.h2 0 0, x.h2 0 1, x.h2 0 2;
     -x.h1 1 / 2, x.h2 1 0, x.h2 1 1, x.h2 1 2;
     -x.h1 2 / 2, x.h2 2 0, x.h2 2 1, x.h2 2 2]
def minkowski : Matrix (Fin 4) (Fin 4) ℝ := Matrix.diagonal ![-1, 1, 1, 1]
def SuU (x : FirstJet) : ℝ := ∑ a, ∑ b, Smat x a b * uVec x a * uVec x b
def Bmat (x : FirstJet) : Matrix (Fin 4) (Fin 4) ℝ := Smat x + SuU x • minkowski
def Bu (x : FirstJet) : Fin 4 → ℝ := fun a => ∑ b, Bmat x a b * uVec x b
def geodesicNull : Set FirstJet := {x | Bu x = 0}
def x0 : FirstJet := ⟨0, 0, 0, 0⟩
def xDip : FirstJet := ⟨0, 0, Pi.single 0 1, 0⟩
```
(The domain restriction "h2 symmetric trace-free" belongs to Ω, not to G.)

## Targets

T1 set structure / boundary
```lean
theorem nullConfSet_subset (Ω : Set Θ) (Q : Θ → ℝ) (q : ℝ) (xmap : Θ → X) (G : Set X) :
    nullConfSet Ω Q q xmap G ⊆ confSet Ω Q q
theorem mem_confSet_of_eq {Ω : Set Θ} {Q : Θ → ℝ} {q : ℝ} {θ : Θ} (hΩ : θ ∈ Ω) (hq : Q θ = q) :
    θ ∈ confSet Ω Q q
theorem confSet_rank_zero (Ω : Set Θ) (Q : Θ → ℝ) (hQ : ∀ θ, Q θ = 0) : confSet Ω Q 0 = Ω   -- CONF-RANK0
```
T2 semantic disjointness/exhaustiveness of reports 1-3 and the empty-model trap
```lean
theorem semantic_trichotomy (C CG : Set Θ) :
    (RejectsGeodesicity C CG ∨ NotExcluded C CG ∨ ModelIncompatible C) ∧
    ¬ (RejectsGeodesicity C CG ∧ NotExcluded C CG) ∧
    ¬ (RejectsGeodesicity C CG ∧ ModelIncompatible C) ∧
    ¬ (NotExcluded C CG ∧ ModelIncompatible C)
theorem modelIncompatible_null_empty {C CG : Set Θ} (hsub : CG ⊆ C) (h : ModelIncompatible C) : CG = ∅
```
T3 soundness of delivered reports
```lean
theorem report_rejected_sound {C CG : Set Θ} (cC : Cert C) (cG : Cert CG)
    (h : fourWayReport cC cG = .geodesicityRejected) : RejectsGeodesicity C CG
theorem report_notExcluded_sound {C CG : Set Θ} (hsub : CG ⊆ C) (cC : Cert C) (cG : Cert CG)
    (h : fourWayReport cC cG = .notExcluded) : NotExcluded C CG
theorem report_incompatible_sound {C CG : Set Θ} (cC : Cert C) (cG : Cert CG)
    (h : fourWayReport cC cG = .modelIncompatible) : ModelIncompatible C
```
T4 attainability of each report under its truth state
```lean
theorem report_complete {C CG : Set Θ} :
    (RejectsGeodesicity C CG → ∃ (cC : Cert C) (cG : Cert CG), fourWayReport cC cG = .geodesicityRejected) ∧
    (NotExcluded C CG → ∃ (cC : Cert C) (cG : Cert CG), fourWayReport cC cG = .notExcluded) ∧
    (ModelIncompatible C → ∃ (cC : Cert C) (cG : Cert CG), fourWayReport cC cG = .modelIncompatible)
theorem report_unresolved_uncertified (C CG : Set Θ) :
    fourWayReport (Cert.uncertified : Cert C) (Cert.uncertified : Cert CG) = .computationallyUnresolved
```
T5 pitfalls (CONF-EMPTYMODEL, CONF-OPTFAIL)
```lean
theorem emptyModel_not_rejected {C CG : Set Θ} (h : ModelIncompatible C) (cC : Cert C) (cG : Cert CG) :
    fourWayReport cC cG ≠ .geodesicityRejected
theorem emptyModel_report_cases {C CG : Set Θ} (hsub : CG ⊆ C) (h : ModelIncompatible C) (cC : Cert C) (cG : Cert CG) :
    fourWayReport cC cG = .modelIncompatible ∨ fourWayReport cC cG = .computationallyUnresolved
theorem uncertified_null_not_rejected {C CG : Set Θ} (cC : Cert C) :
    fourWayReport cC (Cert.uncertified : Cert CG) ≠ .geodesicityRejected
theorem uncertified_full_not_rejected {C CG : Set Θ} (cG : Cert CG) :
    fourWayReport (Cert.uncertified : Cert C) cG ≠ .geodesicityRejected
```
T6 exclusion certificates and the non-strict-bound negative control
```lean
theorem confSet_eq_empty_of_lower_bound {Ω : Set Θ} {Q : Θ → ℝ} {q : ℝ}
    (h : ∃ b, q < b ∧ ∀ θ ∈ Ω, b ≤ Q θ) : confSet Ω Q q = ∅
theorem nullConfSet_eq_empty_of_lower_bound {Ω : Set Θ} {Q : Θ → ℝ} {q : ℝ} {xmap : Θ → X} {G : Set X}
    (h : ∃ b, q < b ∧ ∀ θ ∈ Ω, xmap θ ∈ G → b ≤ Q θ) : nullConfSet Ω Q q xmap G = ∅
theorem nonstrict_bound_inconclusive :
    (∀ θ ∈ Set.Ici (0:ℝ), (0:ℝ) ≤ θ) ∧
    (nullConfSet (Set.Ici (0:ℝ)) (fun θ => θ) 0 id (Set.univ : Set ℝ)).Nonempty ∧
    (∀ θ ∈ Set.Ioi (0:ℝ), (0:ℝ) ≤ θ) ∧
    nullConfSet (Set.Ioi (0:ℝ)) (fun θ => θ) 0 id (Set.univ : Set ℝ) = ∅ ∧
    ¬ ∃ b : ℝ, 0 < b ∧ ∀ θ ∈ Set.Ioi (0:ℝ), id θ ∈ (Set.univ : Set ℝ) → b ≤ θ
```
T7 deterministic N2 event containment (null θ*; full-model only for report 3)
```lean
theorem null_errors_subset_noncoverage (Ω : Set Θ) (Q : Y → Θ → ℝ) (q : ℝ) (xmap : Θ → X) (G : Set X)
    {θs : Θ} (hG : xmap θs ∈ G) :
    {y | RejectsGeodesicity (confSet Ω (Q y) q) (nullConfSet Ω (Q y) q xmap G)} ∪
      {y | ModelIncompatible (confSet Ω (Q y) q)} ⊆ {y | θs ∉ confSet Ω (Q y) q}
theorem incompatible_subset_noncoverage (Ω : Set Θ) (Q : Y → Θ → ℝ) (q : ℝ) (θs : Θ) :
    {y | ModelIncompatible (confSet Ω (Q y) q)} ⊆ {y | θs ∉ confSet Ω (Q y) q}
theorem certified_null_errors_subset (Ω : Set Θ) (Q : Y → Θ → ℝ) (q : ℝ) (xmap : Θ → X) (G : Set X)
    {θs : Θ} (hG : xmap θs ∈ G)
    (cC : ∀ y, Cert (confSet Ω (Q y) q)) (cG : ∀ y, Cert (nullConfSet Ω (Q y) q xmap G)) :
    {y | fourWayReport (cC y) (cG y) = .geodesicityRejected ∨
         fourWayReport (cC y) (cG y) = .modelIncompatible} ⊆ {y | θs ∉ confSet Ω (Q y) q}
theorem certified_incompatible_subset (Ω : Set Θ) (Q : Y → Θ → ℝ) (q : ℝ) (xmap : Θ → X) (G : Set X)
    (θs : Θ) (cC : ∀ y, Cert (confSet Ω (Q y) q)) (cG : ∀ y, Cert (nullConfSet Ω (Q y) q xmap G)) :
    {y | fourWayReport (cC y) (cG y) = .modelIncompatible} ⊆ {y | θs ∉ confSet Ω (Q y) q}
```
T8 size control CONDITIONAL on an explicit coverage hypothesis (N1 (8) is not proved here)
```lean
theorem size_control_of_coverage [MeasurableSpace Y] (μ : MeasureTheory.Measure Y) (α : ENNReal)
    (Ω : Set Θ) (Q : Y → Θ → ℝ) (q : ℝ) (xmap : Θ → X) (G : Set X) {θs : Θ} (hG : xmap θs ∈ G)
    (cC : ∀ y, Cert (confSet Ω (Q y) q)) (cG : ∀ y, Cert (nullConfSet Ω (Q y) q xmap G))
    (hcov : μ {y | θs ∉ confSet Ω (Q y) q} ≤ α) :
    μ {y | fourWayReport (cC y) (cG y) = .geodesicityRejected ∨
           fourWayReport (cC y) (cG y) = .modelIncompatible} ≤ α
theorem incompatible_size_of_coverage [MeasurableSpace Y] (μ : MeasureTheory.Measure Y) (α : ENNReal)
    (Ω : Set Θ) (Q : Y → Θ → ℝ) (q : ℝ) (xmap : Θ → X) (G : Set X) (θs : Θ)
    (cC : ∀ y, Cert (confSet Ω (Q y) q)) (cG : ∀ y, Cert (nullConfSet Ω (Q y) q xmap G))
    (hcov : μ {y | θs ∉ confSet Ω (Q y) q} ≤ α) :
    μ {y | fourWayReport (cC y) (cG y) = .modelIncompatible} ≤ α
```
T9 projection containment (N1a)
```lean
theorem projection_event_subset {ι : Type*} {β : ι → Type*} (f : ∀ i, Θ → β i) (C : Y → Set Θ) (θs : Θ) :
    {y | θs ∈ C y} ⊆ {y | ∀ i, f i θs ∈ f i '' C y}
theorem superset_event_subset {β : Type*} (f : Θ → β) (C : Y → Set Θ) (J : Y → Set β)
    (hJ : ∀ y, f '' C y ⊆ J y) (θs : Θ) : {y | θs ∈ C y} ⊆ {y | f θs ∈ J y}
theorem interval_event_subset (g : Θ → EReal) (C : Y → Set Θ) (θs : Θ) :
    {y | θs ∈ C y} ⊆ {y | sInf (g '' C y) ≤ g θs ∧ g θs ≤ sSup (g '' C y)}
```
T10 union of scenarios / data-dependent domain
```lean
theorem union_event_subset {ι : Type*} (C : ι → Y → Set Θ) (s0 : ι) (θs : Θ) :
    {y | θs ∈ C s0 y} ⊆ {y | θs ∈ ⋃ s, C s y}
theorem union_noncoverage_le [MeasurableSpace Y] (μ : MeasureTheory.Measure Y) {ι : Type*}
    (C : ι → Y → Set Θ) (s0 : ι) (θs : Θ) :
    μ {y | θs ∉ ⋃ s, C s y} ≤ μ {y | θs ∉ C s0 y}
theorem intersection_negative_control :
    ∃ C : Bool → Unit → Set Unit, () ∈ C true () ∧ () ∉ ⋂ s, C s ()
theorem data_domain_split (Ωy : Y → Set Θ) (Q : Y → Θ → ℝ) (q : ℝ) (θs : Θ) :
    {y | θs ∉ confSet (Ωy y) (Q y) q} ⊆ {y | θs ∉ Ωy y} ∪ {y | q < Q y θs}
theorem alpha_delta_bound [MeasurableSpace Y] (μ : MeasureTheory.Measure Y) (α δ : ENNReal)
    (Ωy : Y → Set Θ) (Q : Y → Θ → ℝ) (q : ℝ) (θs : Θ)
    (hδ : μ {y | θs ∉ Ωy y} ≤ δ) (hα : μ {y | q < Q y θs} ≤ α) :
    μ {y | θs ∉ confSet (Ωy y) (Q y) q} ≤ δ + α
```
T11 concrete geodesic null and lift sanity
```lean
theorem Bmat_uu_zero (x : FirstJet) : ∑ a, ∑ b, Bmat x a b * uVec x a * uVec x b = 0   -- B(u,u)=0
theorem mem_geodesicNull_of_zeta_zero (x : FirstJet) (hζ : x.ζ = 0) : x ∈ geodesicNull ↔ x.h1 = 0
theorem x0_mem_geodesicNull : x0 ∈ geodesicNull
theorem xDip_not_mem_geodesicNull : xDip ∉ geodesicNull
```
T12 non-vacuity witnesses of all four reports on the concrete G (Θ = X = FirstJet, x = id)
```lean
theorem report1_witness :   -- feasible non-geodesic case
    RejectsGeodesicity (confSet {xDip} (fun _ => 0) 0) (nullConfSet {xDip} (fun _ => 0) 0 id geodesicNull)
theorem report2_witness :   -- feasible geodesic case
    NotExcluded (confSet {x0} (fun _ => 0) 0) (nullConfSet {x0} (fun _ => 0) 0 id geodesicNull)
theorem report3_witness :   -- empty full model: null set also empty, yet report 3, never report 1
    ModelIncompatible (confSet (∅ : Set FirstJet) (fun _ => 0) 0) ∧
    nullConfSet (∅ : Set FirstJet) (fun _ => 0) 0 id geodesicNull = ∅
theorem report4_witness :   -- truth is report-1 but null exclusion uncertified
    RejectsGeodesicity (confSet {xDip} (fun _ => 0) 0) (nullConfSet {xDip} (fun _ => 0) 0 id geodesicNull) ∧
    ∃ cC : Cert (confSet {xDip} (fun _ => (0:ℝ)) 0),
      fourWayReport cC (Cert.uncertified : Cert (nullConfSet {xDip} (fun _ => (0:ℝ)) 0 id geodesicNull))
        = .computationallyUnresolved
theorem boundary_witness :  -- Q = q exactly is accepted; strict acceptance would differ
    NotExcluded (confSet {x0} (fun _ => 1) 1) (nullConfSet {x0} (fun _ => 1) 1 id geodesicNull) ∧
    {θ : FirstJet | θ ∈ ({x0} : Set FirstJet) ∧ (fun _ => (1:ℝ)) θ < 1} = ∅
```

## Faithfulness notes

- N2's hypothesis θ*∈Ω is dropped from T7 (not needed for the set
  containment; it is needed only for coverage (8)). This weakens a
  hypothesis, so T7 is at least as strong as the source containment.
- T8 is conditional on `hcov`, the N1 coverage conclusion; it is not N2's
  unconditional probability bound and is not labelled as such.
- Gaussian law, χ² quantile, measurability, optimizer certificates and the
  physical interpretation of G are outside these targets.
