# G08-D frozen targets (v1) — measurable confidence inversion and certified optimization

Frozen before any proof compile of this unit. Snapshot: `raw/FROZEN_TARGETS_v1.snapshot.md`,
UTC time in `raw/FROZEN_TARGETS_v1.written_utc`. Sources: `SOURCE_RECOVERY.md`.
Toolchain: Lean 4.31.0, mathlib `fabf563a7c95a166b8d7b6efca11c8b4dc9d911f`
(Lake project `/home/cosmosapjw/lean_oracles/viii_oracle`).

Two modules: `lean/G08DCertificates.lean` (imports `Mathlib`, `G08CFourWay`) and
`lean/G08DInversion.lean` (imports `Mathlib`, `G08BGaussianLaw`, `G08DCertificates`).
Reused, imported unchanged: `ProjectionBridge`, `G08AWhitening`, `G08ACorollaries`,
`G08BGaussianLaw`, `G08CFourWay` (hashes in SOURCE_RECOVERY §4).

Common binders: `{Θ : Type u} {P : Type v} {Y : Type w}`; `open MeasureTheory G08C`
(+ `ProbabilityTheory Matrix WithLp G08BGaussianLaw` in the Gaussian part).
`P` is the physical-parameter type (x of the source), `xmap : Θ → P`, `G : Set P`.
Gaussian part binders: `{n k : ℕ}`, `μ★ := multivariateGaussian (m θs + toLp 2 (F *ᵥ β)) C`,
`Qg W F X m y θ := Qstat W F X (m θ) y`, `qν := threshold (n - F.rank) α`.

Nothing here is a scientific claim. Scientific admission: HOLD.

## Part I — certificates, checker soundness, source-level adapter (`G08DCertificates`)

Definitions (card lean_step 3; source l.120):

```lean
inductive SolverStatus
  | optimal | localOptimum | noFeasiblePointFound | claimedInfeasible
  | claimedLowerBound | iterationLimit | numericalError
  deriving DecidableEq, Repr

/-- Raw optimizer output: a status code and numbers.  Carries no proof. -/
structure SolverRun (Θ : Type u) where
  status : SolverStatus
  point : Option Θ
  value : Option ℝ
  bound : Option ℝ

/-- exact witness: a point of Ω with Q ≤ q ("A feasible point with Q≤q certifies nonemptiness"). -/
structure WitnessCert (Ω : Set Θ) (Q : Θ → ℝ) (q : ℝ) where
  pt : Θ
  mem : pt ∈ Ω
  le : Q pt ≤ q

/-- rigorous lower bound inf_Ω Q ≥ b > q. -/
structure LowerBoundCert (Ω : Set Θ) (Q : Θ → ℝ) (q : ℝ) where
  b : ℝ
  gt : q < b
  bound : ∀ θ ∈ Ω, b ≤ Q θ

/-- certified outer enclosure / interval (branch-and-bound) certificate: cells covering Ω,
each with a strict lower bound on Q over Ω ∩ cell.  The index type is arbitrary. -/
structure CoverCert (Ω : Set Θ) (Q : Θ → ℝ) (q : ℝ) where
  ι : Type
  cell : ι → Set Θ
  covers : Ω ⊆ ⋃ i, cell i
  b : ι → ℝ
  gt : ∀ i, q < b i
  bound : ∀ i, ∀ θ ∈ Ω ∩ cell i, b i ≤ Q θ

/-- Lagrangian dual-bound certificate for the constrained set Ω0 ∩ {g = 0}. -/
structure DualCert (Ω0 : Set Θ) {k : ℕ} (g : Θ → Fin k → ℝ) (Q : Θ → ℝ) (q : ℝ) where
  mult : Fin k → ℝ
  b : ℝ
  gt : q < b
  bound : ∀ θ ∈ Ω0, b ≤ Q θ + ∑ j, mult j * g θ j

/-- verified exclusion certificate for confSet Ω Q q. -/
inductive ExclCert (Ω : Set Θ) (Q : Θ → ℝ) (q : ℝ) : Type (max u 1)
  | lower (c : LowerBoundCert Ω Q q)
  | cover (c : CoverCert Ω Q q)
  | dual {k : ℕ} (Ω0 : Set Θ) (g : Θ → Fin k → ℝ) (hΩ : Ω = Ω0 ∩ {θ | g θ = 0})
      (c : DualCert Ω0 g Q q)
  | proof (h : confSet Ω Q q = ∅)

/-- transport of a G08-C certificate along a set equality -/
def certCongr {S S' : Set Θ} (h : S = S') : Cert S → Cert S'

def WitnessCert.toCert (w : WitnessCert Ω Q q) : Cert (confSet Ω Q q)   -- = .feasible w.pt _
def ExclCert.toCert (e : ExclCert Ω Q q) : Cert (confSet Ω Q q)         -- = .excluded e.sound

/-- one optimization report: raw run + optional verified certificates -/
structure OptReport (Ω : Set Θ) (Q : Θ → ℝ) (q : ℝ) where
  run : SolverRun Θ
  witness : Option (WitnessCert Ω Q q)
  exclusion : Option (ExclCert Ω Q q)

/-- witness first, then exclusion, otherwise uncertified; `run` is never consulted -/
def OptReport.toCert (r : OptReport Ω Q q) : Cert (confSet Ω Q q)

/-- source-level decision adapter: G08-C four-way report from two optimization reports -/
def sourceDecision {Ω : Set Θ} {Q : Θ → ℝ} {q : ℝ} {xmap : Θ → P} {G : Set P}
    (rC : OptReport Ω Q q) (rG : OptReport (Ω ∩ xmap ⁻¹' G) Q q) : Report :=
  fourWayReport rC.toCert (certCongr (nullConfSet_eq_confSet_inter Ω Q q xmap G) rG.toCert)

/-- executable exact-rational witness checker -/
def checkWitness (memΩ : Θ → Bool) (Qq : Θ → ℚ) (qq : ℚ) (θ : Θ) : Bool :=
  memΩ θ && decide (Qq θ ≤ qq)

/-- executable exhaustive exclusion checker on a finite parameter type -/
def checkExclFinite [Fintype Θ] (memΩ : Θ → Bool) (Qq : Θ → ℚ) (qq : ℚ) : Bool :=
  decide (∀ θ, memΩ θ = true → qq < Qq θ)

/-- acceleration norm a(x) = sqrt(g^{ab} A_a A_b), A = 2 c B u (source (1), l.15-17);
g^{ab} = diag(-1,1,1,1) = `minkowski` -/
def accelNorm (cl : ℝ) (x : FirstJet) : ℝ :=
  Real.sqrt (∑ a, ∑ b, minkowski a b * (2 * cl * Bu x a) * (2 * cl * Bu x b))

/-- dual certificate for the concrete geodesic null (2): g θ = Bu (xmap θ) -/
def geodesicDualExcl (Ω : Set Θ) (Q : Θ → ℝ) (q : ℝ) (xmap : Θ → FirstJet)
    (c : DualCert Ω (fun θ => Bu (xmap θ)) Q q) : ExclCert (Ω ∩ xmap ⁻¹' geodesicNull) Q q
```

Theorems (all `Ω : Set Θ`, `Q : Θ → ℝ`, `q : ℝ` implicit/explicit as shown):

| id | name | statement |
|---|---|---|
| C0 | `nullConfSet_eq_confSet_inter` | `(Ω) (Q) (q) (xmap : Θ → P) (G : Set P) : confSet (Ω ∩ xmap ⁻¹' G) Q q = nullConfSet Ω Q q xmap G` |
| C1 | `WitnessCert.sound` | `(w : WitnessCert Ω Q q) : w.pt ∈ confSet Ω Q q` |
| C2 | `LowerBoundCert.sound` | `(c : LowerBoundCert Ω Q q) : confSet Ω Q q = ∅` |
| C3 | `CoverCert.sound` | `(c : CoverCert Ω Q q) : confSet Ω Q q = ∅` |
| C4 | `DualCert.sound` | `{Ω0 : Set Θ} {k : ℕ} {g : Θ → Fin k → ℝ} (c : DualCert Ω0 g Q q) : confSet (Ω0 ∩ {θ \| g θ = 0}) Q q = ∅` |
| C5 | `ExclCert.sound` | `(e : ExclCert Ω Q q) : confSet Ω Q q = ∅` |
| C6 | `witness_excl_incompatible` | `(w : WitnessCert Ω Q q) (e : ExclCert Ω Q q) : False` |
| C7 | `OptReport.toCert_unverified` | `(r : OptReport Ω Q q) (hw : r.witness = none) (he : r.exclusion = none) : r.toCert = Cert.uncertified` |
| C8 | `sourceDecision_run_irrelevant` | `{xmap : Θ → P} {G : Set P} (rC : OptReport Ω Q q) (rG : OptReport (Ω ∩ xmap ⁻¹' G) Q q) (s s' : SolverRun Θ) : sourceDecision { rC with run := s } { rG with run := s' } = sourceDecision rC rG` |
| C9 | `sourceDecision_unverified` | same binders; `(h1 : rC.witness = none) (h2 : rC.exclusion = none) (h3 : rG.witness = none) (h4 : rG.exclusion = none) : sourceDecision rC rG = Report.computationallyUnresolved` |
| C10 | `sourceDecision_rejected_requires_certs` | same binders; `(h : sourceDecision rC rG = Report.geodesicityRejected) : (∃ w, rC.witness = some w) ∧ rG.witness = none ∧ ∃ e, rG.exclusion = some e` |
| C11 | `sourceDecision_no_null_excl` | same binders; `(he : rG.exclusion = none) : sourceDecision rC rG ≠ Report.geodesicityRejected` |
| C12 | `sourceDecision_no_full_excl` | same binders; `(he : rC.exclusion = none) : sourceDecision rC rG ≠ Report.modelIncompatible` |
| C13 | `sourceDecision_sound` | same binders; `(sourceDecision rC rG = Report.geodesicityRejected → RejectsGeodesicity (confSet Ω Q q) (nullConfSet Ω Q q xmap G)) ∧ (sourceDecision rC rG = Report.notExcluded → NotExcluded (confSet Ω Q q) (nullConfSet Ω Q q xmap G)) ∧ (sourceDecision rC rG = Report.modelIncompatible → ModelIncompatible (confSet Ω Q q))` |
| C14 | `checkWitness_sound` | `(memΩ : Θ → Bool) (Qq : Θ → ℚ) (qq : ℚ) (hmem : ∀ θ, memΩ θ = true → θ ∈ Ω) (hQ : ∀ θ, Q θ = (Qq θ : ℝ)) (hq : q = (qq : ℝ)) (θ : Θ) (h : checkWitness memΩ Qq qq θ = true) : θ ∈ confSet Ω Q q` |
| C15 | `checkExclFinite_sound` | `[Fintype Θ] (memΩ) (Qq) (qq) (hmem : ∀ θ ∈ Ω, memΩ θ = true) (hQ : ∀ θ, Q θ = (Qq θ : ℝ)) (hq : q = (qq : ℝ)) (h : checkExclFinite memΩ Qq qq = true) : confSet Ω Q q = ∅` |
| C16 | `checkExclFinite_complete` | `[Fintype Θ] (memΩ) (Qq) (qq) (hmem : ∀ θ, memΩ θ = true ↔ θ ∈ Ω) (hQ) (hq) (h : confSet Ω Q q = ∅) : checkExclFinite memΩ Qq qq = true` |
| C17 | `checkWitness_example` | `checkWitness (fun _ : Fin 3 => true) (fun i => ((i : ℕ) : ℚ)) 1 1 = true` (non-vacuity) |
| C18 | `checkExclFinite_example` | `checkExclFinite (fun i : Fin 3 => decide (1 ≤ (i : ℕ))) (fun i => ((i : ℕ) : ℚ)) (1 / 2) = true` (non-vacuity) |
| C19 | `accelNorm_of_geodesic` | `(cl : ℝ) (x : FirstJet) (hx : x ∈ geodesicNull) : accelNorm cl x = 0` |
| C20 | `accel_lower_bound_excludes` | `{xmap : Θ → P} {G : Set P} (a : P → ℝ) (ha : ∀ x ∈ G, a x = 0) {c : ℝ} (hc : 0 < c) (h : ∀ θ ∈ confSet Ω Q q, c ≤ a (xmap θ)) : nullConfSet Ω Q q xmap G = ∅` |
| C21 | `accel_lower_bound_excludes_geodesic` | `{xmap : Θ → FirstJet} (cl : ℝ) {c : ℝ} (hc : 0 < c) (h : ∀ θ ∈ confSet Ω Q q, c ≤ accelNorm cl (xmap θ)) : nullConfSet Ω Q q xmap geodesicNull = ∅` |
| C22 | `geodesicDual_sound` | `(Ω) (Q) (q) (xmap : Θ → FirstJet) (c : DualCert Ω (fun θ => Bu (xmap θ)) Q q) : nullConfSet Ω Q q xmap geodesicNull = ∅` |
| C23 | `solver_claim_not_proof` (negative control, CONF-OPTFAIL) | `∃ r : OptReport (Set.univ : Set ℝ) (fun θ => θ ^ 2) 0, r.run.status = SolverStatus.claimedInfeasible ∧ (confSet (Set.univ : Set ℝ) (fun θ => θ ^ 2) 0).Nonempty ∧ r.toCert = Cert.uncertified` |
| C24 | `inner_samples_not_exclusion` (negative control) | `∃ (Ω : Set ℝ) (Q : ℝ → ℝ) (q : ℝ) (G : Set ℝ) (s : Finset ℝ), s.Nonempty ∧ (↑s : Set ℝ) ⊆ confSet Ω Q q ∧ (∀ θ ∈ s, θ ∉ G) ∧ (nullConfSet Ω Q q id G).Nonempty` |
| C25 | `zero_excluded_no_positive_bound` (negative control, l.120 last sentence) | `(0 : ℝ) ∉ (id '' confSet (Set.Ioi (0 : ℝ)) (fun _ => 0) 0) ∧ ¬ ∃ c : ℝ, 0 < c ∧ ∀ θ ∈ confSet (Set.Ioi (0 : ℝ)) (fun _ => 0) 0, c ≤ id θ` |

## Part II — measurability, coverage composition, size control (`G08DInversion`)

Measurability (card lean_step 1; pitfall "uncountable union/projection은 자동 measurable이 아니다"):

| id | name | statement |
|---|---|---|
| M1 | `measurableSet_confGraph` | `[MeasurableSpace Y] [MeasurableSpace Θ] {Ω : Set Θ} (hΩ : MeasurableSet Ω) {Q : Y → Θ → ℝ} (hQ : Measurable (fun p : Y × Θ => Q p.1 p.2)) (q : ℝ) : MeasurableSet {p : Y × Θ \| p.2 ∈ confSet Ω (Q p.1) q}` |
| M2 | `measurableSet_nullGraph` | M1 binders + `[MeasurableSpace P] {xmap : Θ → P} (hx : Measurable xmap) {G : Set P} (hG : MeasurableSet G) : MeasurableSet {p : Y × Θ \| p.2 ∈ nullConfSet Ω (Q p.1) q xmap G}` |
| M3 | `measurableSet_coverage` | `[MeasurableSpace Y] (Ω : Set Θ) {Q : Y → Θ → ℝ} (q : ℝ) (θs : Θ) (hQ : Measurable (fun y => Q y θs)) : MeasurableSet {y \| θs ∈ confSet Ω (Q y) q}` |
| M3' | `measurableSet_noncoverage` | same : `MeasurableSet {y \| θs ∉ confSet Ω (Q y) q}` |
| M4 | `measurableSet_nonempty_countable` | `[MeasurableSpace Y] [Countable Θ] (Ω : Set Θ) {Q : Y → Θ → ℝ} (q : ℝ) (hQ : ∀ θ, Measurable (fun y => Q y θ)) : MeasurableSet {y \| (confSet Ω (Q y) q).Nonempty}` |
| M5 | `measurableSet_nonempty_compact` | `[MeasurableSpace Y] [TopologicalSpace Θ] [SecondCountableTopology Θ] {K : Set Θ} (hK : IsCompact K) {Q : Y → Θ → ℝ} (q : ℝ) (hcont : ∀ y, ContinuousOn (Q y) K) (hQ : ∀ θ, Measurable (fun y => Q y θ)) : MeasurableSet {y \| (confSet K (Q y) q).Nonempty}` |
| M6 | `measurableSet_nonempty_sigmaCompact` | `[MeasurableSpace Y] [TopologicalSpace Θ] [SecondCountableTopology Θ] {Ω : Set Θ} (Kn : ℕ → Set Θ) (hK : ∀ i, IsCompact (Kn i)) (hΩ : Ω = ⋃ i, Kn i) {Q : Y → Θ → ℝ} (q : ℝ) (hcont : ∀ y, ContinuousOn (Q y) Ω) (hQ : ∀ θ, Measurable (fun y => Q y θ)) : MeasurableSet {y \| (confSet Ω (Q y) q).Nonempty}` |
| M7 | `measurableSet_null_nonempty_sigmaCompact` | M6 binders + `[T2Space Θ] [TopologicalSpace P] {xmap : Θ → P} (hx : ContinuousOn xmap Ω) {G : Set P} (hG : IsClosed G) : MeasurableSet {y \| (nullConfSet Ω (Q y) q xmap G).Nonempty}` |
| M8 | `measurableSet_reports` | M7 binders : `MeasurableSet {y \| RejectsGeodesicity (confSet Ω (Q y) q) (nullConfSet Ω (Q y) q xmap G)} ∧ MeasurableSet {y \| NotExcluded (confSet Ω (Q y) q) (nullConfSet Ω (Q y) q xmap G)} ∧ MeasurableSet {y \| ModelIncompatible (confSet Ω (Q y) q)}` |
| M9 | `projection_not_auto_measurable` (negative control) | `∃ (m : MeasurableSpace ℝ) (Ω : Set ℝ) (Q : ℝ → ℝ → ℝ) (q : ℝ), (∀ θ, @Measurable ℝ ℝ m _ (fun y => Q y θ)) ∧ (∀ θs, MeasurableSet[m] {y \| θs ∈ confSet Ω (Q y) q}) ∧ ¬ MeasurableSet[m] {y \| (confSet Ω (Q y) q).Nonempty}` |
| M10 | `gaussian_reports_measurable` | `{n k : ℕ} [TopologicalSpace Θ] [SecondCountableTopology Θ] [T2Space Θ] [TopologicalSpace P] (W : Matrix (Fin n) (Fin n) ℝ) (F : Matrix (Fin n) (Fin k) ℝ) (X : Matrix (Fin k) (Fin n) ℝ) (m : Θ → EuclideanSpace ℝ (Fin n)) {Ω : Set Θ} (Kn : ℕ → Set Θ) (hK : ∀ i, IsCompact (Kn i)) (hΩ : Ω = ⋃ i, Kn i) (hm : ContinuousOn m Ω) {xmap : Θ → P} (hx : ContinuousOn xmap Ω) {G : Set P} (hG : IsClosed G) (q : ℝ) :` M8's conclusion with `Q y := fun θ => Qstat W F X (m θ) y` |

Inversion / coverage / size control (card lean_step 2; source l.84, l.101-103, l.114-116, l.180-182):

| id | name | statement |
|---|---|---|
| P1 | `general_inversion_coverage` | `[MeasurableSpace Y] (μ : Θ → Measure Y) (R : Θ → Set Y) (p : ENNReal) (hR : ∀ θ, p ≤ μ θ (R θ)) (θs : Θ) : p ≤ μ θs {y \| θs ∈ {θ \| y ∈ R θ}}` |
| P1' | `general_inversion_projection` | P1 binders + `{ι : Type} {β : ι → Type} (f : ∀ i, Θ → β i) : p ≤ μ θs {y \| ∀ i, f i θs ∈ f i '' {θ \| y ∈ R θ}}` |
| P2 | `gaussian_noncoverage_eq` | `(Ω : Set Θ) (m : Θ → EuclideanSpace ℝ (Fin n)) (θs : Θ) (hθ : θs ∈ Ω) (C W : Matrix (Fin n) (Fin n) ℝ) (F : Matrix (Fin n) (Fin k) ℝ) (X : Matrix (Fin k) (Fin n) ℝ) (hC : C.PosDef) (hW : IsUnit W ∧ W * C * Wᵀ = 1) (hX : G08AWhitening.IsMoorePenrose (W * F) X) (β : Fin k → ℝ) {α : ℝ} (hα0 : 0 < α) (hα1 : α < 1) (hν : 0 < n - F.rank) : (multivariateGaussian (m θs + toLp 2 (F *ᵥ β)) C) {y \| θs ∉ confSet Ω (fun θ => Qstat W F X (m θ) y) (threshold (n - F.rank) α)} = ENNReal.ofReal α` |
| P3 | `gaussian_size_control` | P2 binders + `(xmap : Θ → P) (G : Set P) (hG : xmap θs ∈ G) (cC : ∀ y, Cert (confSet Ω (fun θ => Qstat W F X (m θ) y) (threshold (n - F.rank) α))) (cG : ∀ y, Cert (nullConfSet Ω (fun θ => Qstat W F X (m θ) y) (threshold (n - F.rank) α) xmap G)) : μ★ {y \| fourWayReport (cC y) (cG y) = Report.geodesicityRejected ∨ fourWayReport (cC y) (cG y) = Report.modelIncompatible} ≤ ENNReal.ofReal α` |
| P4 | `gaussian_semantic_size` | P2 binders + `(xmap) (G) (hG : xmap θs ∈ G) : μ★ {y \| RejectsGeodesicity (confSet Ω (Qg y) qν) (nullConfSet Ω (Qg y) qν xmap G) ∨ ModelIncompatible (confSet Ω (Qg y) qν)} ≤ ENNReal.ofReal α` |
| P5 | `gaussian_incompatible_size` | P2 binders (no null) + `(xmap) (G) (cC) (cG) : μ★ {y \| fourWayReport (cC y) (cG y) = Report.modelIncompatible} ≤ ENNReal.ofReal α` |
| P6 | `gaussian_sourceDecision_size` | P2 binders + `(xmap) (G) (hG : xmap θs ∈ G) (rC : ∀ y, OptReport Ω (Qg y) qν) (rG : ∀ y, OptReport (Ω ∩ xmap ⁻¹' G) (Qg y) qν) : μ★ {y \| sourceDecision (rC y) (rG y) = Report.geodesicityRejected ∨ sourceDecision (rC y) (rG y) = Report.modelIncompatible} ≤ ENNReal.ofReal α` |
| P7 | `gaussian_error_envelope` | P6 binders : `∃ E, MeasurableSet E ∧ μ★ E = ENNReal.ofReal α ∧ {y \| sourceDecision (rC y) (rG y) = Report.geodesicityRejected ∨ sourceDecision (rC y) (rG y) = Report.modelIncompatible} ⊆ E` |
| P8 | `gaussian_size_rank_zero` | P2 binders without `hα0 hα1 hν`, with `(α : ℝ) (hν : n - F.rank = 0)` + `(xmap) (G) (hG) (cC) (cG)` : `μ★ {y \| fourWayReport (cC y) (cG y) = Report.geodesicityRejected ∨ fourWayReport (cC y) (cG y) = Report.modelIncompatible} = 0` |
| P9 | `gaussian_projection_coverage` | P2 binders + `{ι : Type} {β' : ι → Type} (f : ∀ i, Θ → β' i) : ENNReal.ofReal (1 - α) ≤ μ★ {y \| ∀ i, f i θs ∈ f i '' confSet Ω (Qg y) qν}` |
| P10 | `gaussian_robust_union_coverage` | `(Ω) (m) (θs) (hθ) (C : Matrix (Fin n) (Fin n) ℝ) (F) (hC : C.PosDef) {ι : Type} (S : Set ι) (cs : ι) (hcs : cs ∈ S) (Wc : ι → Matrix (Fin n) (Fin n) ℝ) (Xc : ι → Matrix (Fin k) (Fin n) ℝ) (hW : IsUnit (Wc cs) ∧ Wc cs * C * (Wc cs)ᵀ = 1) (hX : G08AWhitening.IsMoorePenrose (Wc cs * F) (Xc cs)) (β) {α} (hα0) (hα1) (hν) : ENNReal.ofReal (1 - α) ≤ μ★ {y \| θs ∈ ⋃ c ∈ S, confSet Ω (fun θ => Qstat (Wc c) F (Xc c) (m θ) y) (threshold (n - F.rank) α)}` |
| P11 | `gaussian_robust_union_delta` | P10 binders with `S` replaced by `(Sy : EuclideanSpace ℝ (Fin n) → Set ι)` and `hcs` replaced by `(δ : ENNReal) (hδ : μ★ {y \| cs ∉ Sy y} ≤ δ)` : `μ★ {y \| θs ∉ ⋃ c ∈ Sy y, confSet Ω (fun θ => Qstat (Wc c) F (Xc c) (m θ) y) (threshold (n - F.rank) α)} ≤ δ + ENNReal.ofReal α` |

Notes on fidelity:
- P2-P9 use exactly G08-B's hypotheses (known PosDef C, whitening W, Moore-Penrose X of WF,
  arbitrary β, 0<α<1, ν>0) and `θs ∈ Ω`. P8 is the source's ν=0 branch (l.90). No hypothesis
  restates a conclusion; `hcov` of G08-C is *derived* (P2), not assumed.
- P3/P6 hold for arbitrary certificate families (no measurability of the adapter is assumed);
  the bound is on the measure (outer measure) of the possibly non-measurable error event. P7
  makes this explicit by exhibiting a measurable envelope of probability exactly α.
- P10/P11 formalize l.182 in the known-C Gaussian case only (S deterministic / S data-dependent
  with miss probability ≤ δ). P11 is an outer-measure union bound; `Sy` need not be measurable.
- M5-M8 are sufficient conditions in the original parameter space (compact / σ-compact Ω,
  continuity in θ, measurability in y). They are not asserted for the source domain (5),
  which is not compact; σ-compactness and closedness of G are explicit hypotheses.
- Executable checkers (C14-C18) are exact over ℚ; real-valued lower-bound/cover/dual
  certificates are Prop-level objects checked by the Lean kernel, not by an executable
  interval-arithmetic routine (not claimed).

## Not claimed

Scientific admission; a concrete solver/certificate file format; replay of any data-run
certificate (no data run exists); executable interval arithmetic over ℝ; closedness of the
concrete `geodesicNull` on `FirstJet` (no topology there) and σ-compactness of the source Ω (5);
estimated-C or selection-aware laws; Wolfram/SymPy/Sage axes; CAS_4AXIS_PASS; any real-data fit.
