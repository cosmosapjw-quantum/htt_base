import Mathlib
import G08CFourWay

/-!
# G08-D (part I): verifiable optimization certificates and the source-level decision adapter

Owning source: `statistics/NATIVE_INFERENCE_THEOREMS.md`
(sha256 e215836882047c50a1a5ae6da605d62aa2c553d0de055e279eee3ce35ec8e322), §5 l.105-120
(certification rules l.120), eq. (1)-(2) l.11-21.  Targets frozen in `../FROZEN_TARGETS.md`.
Reused unchanged: `G08CFourWay` (confSet, nullConfSet, Cert, Report, fourWayReport, Bu,
geodesicNull, minkowski).

A raw solver run (`SolverRun`) carries only a status code and numbers; it is never consulted by
the adapter.  Only verified objects (`WitnessCert`, `ExclCert`) can move the report away from
`computationallyUnresolved`.  No probability is used in this file.
-/

namespace G08D

open MeasureTheory G08C

universe u v

/-! ## Definitions -/

/-- Raw optimizer status codes.  A status code is not a mathematical proof. -/
inductive SolverStatus
  | optimal
  | localOptimum
  | noFeasiblePointFound
  | claimedInfeasible
  | claimedLowerBound
  | iterationLimit
  | numericalError
  deriving DecidableEq, Repr

/-- Raw optimizer output: a status code and numbers.  Carries no proof. -/
structure SolverRun (Θ : Type u) where
  status : SolverStatus
  point : Option Θ
  value : Option ℝ
  bound : Option ℝ

section Cert

variable {Θ : Type u} {P : Type v}

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

/-- verified exclusion certificate for `confSet Ω Q q`. -/
inductive ExclCert (Ω : Set Θ) (Q : Θ → ℝ) (q : ℝ) : Type (max u 1)
  | lower (c : LowerBoundCert Ω Q q)
  | cover (c : CoverCert Ω Q q)
  | dual {k : ℕ} (Ω0 : Set Θ) (g : Θ → Fin k → ℝ) (hΩ : Ω = Ω0 ∩ {θ | g θ = 0})
      (c : DualCert Ω0 g Q q)
  | proof (h : confSet Ω Q q = ∅)

/-- transport of a G08-C certificate along a set equality -/
def certCongr {S S' : Set Θ} (h : S = S') : Cert S → Cert S'
  | .feasible θ hθ => .feasible θ (h ▸ hθ)
  | .excluded hS => .excluded (h ▸ hS)
  | .uncertified => .uncertified

/-! ## Soundness of the certificate kinds -/

theorem nullConfSet_eq_confSet_inter (Ω : Set Θ) (Q : Θ → ℝ) (q : ℝ) (xmap : Θ → P)
    (G : Set P) : confSet (Ω ∩ xmap ⁻¹' G) Q q = nullConfSet Ω Q q xmap G := by
  ext θ
  simp only [confSet, nullConfSet, Set.mem_setOf_eq, Set.mem_inter_iff, Set.mem_preimage]
  tauto

variable {Ω : Set Θ} {Q : Θ → ℝ} {q : ℝ}

theorem WitnessCert.sound (w : WitnessCert Ω Q q) : w.pt ∈ confSet Ω Q q :=
  ⟨w.mem, w.le⟩

theorem LowerBoundCert.sound (c : LowerBoundCert Ω Q q) : confSet Ω Q q = ∅ :=
  confSet_eq_empty_of_lower_bound ⟨c.b, c.gt, c.bound⟩

theorem CoverCert.sound (c : CoverCert Ω Q q) : confSet Ω Q q = ∅ := by
  refine Set.eq_empty_iff_forall_notMem.mpr ?_
  rintro θ ⟨hθ, hq⟩
  obtain ⟨i, hi⟩ := Set.mem_iUnion.mp (c.covers hθ)
  have h1 := c.bound i θ ⟨hθ, hi⟩
  have h2 := c.gt i
  linarith

theorem DualCert.sound {Ω0 : Set Θ} {k : ℕ} {g : Θ → Fin k → ℝ} (c : DualCert Ω0 g Q q) :
    confSet (Ω0 ∩ {θ | g θ = 0}) Q q = ∅ := by
  refine Set.eq_empty_iff_forall_notMem.mpr ?_
  rintro θ ⟨⟨hθ, hg⟩, hq⟩
  have hg' : g θ = 0 := hg
  have h1 := c.bound θ hθ
  simp only [hg', Pi.zero_apply, mul_zero, Finset.sum_const_zero, add_zero] at h1
  have h2 := c.gt
  linarith

theorem ExclCert.sound (e : ExclCert Ω Q q) : confSet Ω Q q = ∅ := by
  cases e with
  | lower c => exact c.sound
  | cover c => exact c.sound
  | dual Ω0 g hΩ c => subst hΩ; exact c.sound
  | proof h => exact h

theorem witness_excl_incompatible (w : WitnessCert Ω Q q) (e : ExclCert Ω Q q) : False := by
  have h := w.sound
  rw [e.sound] at h
  exact Set.notMem_empty _ h

/-! ## Conversion to G08-C certificates and the adapter -/

def WitnessCert.toCert (w : WitnessCert Ω Q q) : Cert (confSet Ω Q q) :=
  .feasible w.pt w.sound

def ExclCert.toCert (e : ExclCert Ω Q q) : Cert (confSet Ω Q q) :=
  .excluded e.sound

/-- one optimization report: raw run + optional verified certificates -/
structure OptReport (Ω : Set Θ) (Q : Θ → ℝ) (q : ℝ) where
  run : SolverRun Θ
  witness : Option (WitnessCert Ω Q q)
  exclusion : Option (ExclCert Ω Q q)

/-- witness first, then exclusion, otherwise uncertified; `run` is never consulted -/
def OptReport.toCert (r : OptReport Ω Q q) : Cert (confSet Ω Q q) :=
  match r.witness, r.exclusion with
  | some w, _ => w.toCert
  | none, some e => e.toCert
  | none, none => .uncertified

/-- source-level decision adapter: G08-C four-way report from two optimization reports -/
def sourceDecision {Ω : Set Θ} {Q : Θ → ℝ} {q : ℝ} {xmap : Θ → P} {G : Set P}
    (rC : OptReport Ω Q q) (rG : OptReport (Ω ∩ xmap ⁻¹' G) Q q) : Report :=
  fourWayReport rC.toCert (certCongr (nullConfSet_eq_confSet_inter Ω Q q xmap G) rG.toCert)

theorem OptReport.toCert_unverified (r : OptReport Ω Q q) (hw : r.witness = none)
    (he : r.exclusion = none) : r.toCert = Cert.uncertified := by
  unfold OptReport.toCert
  rw [hw, he]

section Adapter

variable {xmap : Θ → P} {G : Set P}

theorem sourceDecision_run_irrelevant (rC : OptReport Ω Q q)
    (rG : OptReport (Ω ∩ xmap ⁻¹' G) Q q) (s s' : SolverRun Θ) :
    sourceDecision { rC with run := s } { rG with run := s' } = sourceDecision rC rG :=
  rfl

theorem sourceDecision_unverified (rC : OptReport Ω Q q) (rG : OptReport (Ω ∩ xmap ⁻¹' G) Q q)
    (h1 : rC.witness = none) (h2 : rC.exclusion = none) (h3 : rG.witness = none)
    (h4 : rG.exclusion = none) : sourceDecision rC rG = Report.computationallyUnresolved := by
  unfold sourceDecision
  rw [rC.toCert_unverified h1 h2, rG.toCert_unverified h3 h4]
  rfl

/-- case analysis of `OptReport.toCert` -/
private theorem toCert_cases (r : OptReport Ω Q q) :
    (∃ w, r.witness = some w ∧ r.toCert = w.toCert) ∨
    (r.witness = none ∧ ∃ e, r.exclusion = some e ∧ r.toCert = e.toCert) ∨
    (r.witness = none ∧ r.exclusion = none ∧ r.toCert = Cert.uncertified) := by
  rcases hw : r.witness with _ | w
  · rcases he : r.exclusion with _ | e
    · exact Or.inr (Or.inr ⟨rfl, rfl, by unfold OptReport.toCert; rw [hw, he]⟩)
    · exact Or.inr (Or.inl ⟨rfl, e, rfl, by unfold OptReport.toCert; rw [hw, he]⟩)
  · exact Or.inl ⟨w, rfl, by unfold OptReport.toCert; rw [hw]⟩

theorem sourceDecision_rejected_requires_certs (rC : OptReport Ω Q q)
    (rG : OptReport (Ω ∩ xmap ⁻¹' G) Q q) (h : sourceDecision rC rG = Report.geodesicityRejected) :
    (∃ w, rC.witness = some w) ∧ rG.witness = none ∧ ∃ e, rG.exclusion = some e := by
  unfold sourceDecision at h
  rcases toCert_cases rC with ⟨w, hw, hC⟩ | ⟨hw, e, he, hC⟩ | ⟨hw, he, hC⟩
  · rcases toCert_cases rG with ⟨w', hw', hG⟩ | ⟨hw', e', he', hG⟩ | ⟨hw', he', hG⟩
    · rw [hC, hG] at h
      simp [WitnessCert.toCert, certCongr, fourWayReport] at h
    · exact ⟨⟨w, hw⟩, hw', e', he'⟩
    · rw [hC, hG] at h
      simp [WitnessCert.toCert, certCongr, fourWayReport] at h
  · rw [hC] at h
    rcases toCert_cases rG with ⟨w', hw', hG⟩ | ⟨hw', e', he', hG⟩ | ⟨hw', he', hG⟩ <;>
      · rw [hG] at h
        simp [WitnessCert.toCert, ExclCert.toCert, certCongr, fourWayReport] at h
  · rw [hC] at h
    rcases toCert_cases rG with ⟨w', hw', hG⟩ | ⟨hw', e', he', hG⟩ | ⟨hw', he', hG⟩ <;>
      · rw [hG] at h
        simp [WitnessCert.toCert, ExclCert.toCert, certCongr, fourWayReport] at h

theorem sourceDecision_no_null_excl (rC : OptReport Ω Q q) (rG : OptReport (Ω ∩ xmap ⁻¹' G) Q q)
    (he : rG.exclusion = none) : sourceDecision rC rG ≠ Report.geodesicityRejected := by
  intro h
  obtain ⟨-, -, e, he'⟩ := sourceDecision_rejected_requires_certs rC rG h
  rw [he] at he'
  exact Option.noConfusion he'

theorem sourceDecision_no_full_excl (rC : OptReport Ω Q q) (rG : OptReport (Ω ∩ xmap ⁻¹' G) Q q)
    (he : rC.exclusion = none) : sourceDecision rC rG ≠ Report.modelIncompatible := by
  intro h
  unfold sourceDecision at h
  rcases toCert_cases rC with ⟨w, hw, hC⟩ | ⟨hw, e, he', hC⟩ | ⟨hw, he', hC⟩
  · rw [hC] at h
    rcases toCert_cases rG with ⟨w', hw', hG⟩ | ⟨hw', e', he'', hG⟩ | ⟨hw', he'', hG⟩ <;>
      · rw [hG] at h
        simp [WitnessCert.toCert, ExclCert.toCert, certCongr, fourWayReport] at h
  · rw [he] at he'
    exact Option.noConfusion he'
  · rw [hC] at h
    rcases toCert_cases rG with ⟨w', hw', hG⟩ | ⟨hw', e', he'', hG⟩ | ⟨hw', he'', hG⟩ <;>
      · rw [hG] at h
        simp [WitnessCert.toCert, ExclCert.toCert, certCongr, fourWayReport] at h

theorem sourceDecision_sound (rC : OptReport Ω Q q) (rG : OptReport (Ω ∩ xmap ⁻¹' G) Q q) :
    (sourceDecision rC rG = Report.geodesicityRejected →
      RejectsGeodesicity (confSet Ω Q q) (nullConfSet Ω Q q xmap G)) ∧
    (sourceDecision rC rG = Report.notExcluded →
      NotExcluded (confSet Ω Q q) (nullConfSet Ω Q q xmap G)) ∧
    (sourceDecision rC rG = Report.modelIncompatible → ModelIncompatible (confSet Ω Q q)) :=
  ⟨report_rejected_sound _ _,
   report_notExcluded_sound (nullConfSet_subset Ω Q q xmap G) _ _,
   report_incompatible_sound _ _⟩

end Adapter

/-! ## Executable exact-rational checkers -/

/-- executable exact-rational witness checker -/
def checkWitness (memΩ : Θ → Bool) (Qq : Θ → ℚ) (qq : ℚ) (θ : Θ) : Bool :=
  memΩ θ && decide (Qq θ ≤ qq)

/-- executable exhaustive exclusion checker on a finite parameter type -/
def checkExclFinite [Fintype Θ] (memΩ : Θ → Bool) (Qq : Θ → ℚ) (qq : ℚ) : Bool :=
  decide (∀ θ, memΩ θ = true → qq < Qq θ)

theorem checkWitness_sound (memΩ : Θ → Bool) (Qq : Θ → ℚ) (qq : ℚ)
    (hmem : ∀ θ, memΩ θ = true → θ ∈ Ω) (hQ : ∀ θ, Q θ = (Qq θ : ℝ)) (hq : q = (qq : ℝ))
    (θ : Θ) (h : checkWitness memΩ Qq qq θ = true) : θ ∈ confSet Ω Q q := by
  simp only [checkWitness, Bool.and_eq_true, decide_eq_true_eq] at h
  refine ⟨hmem θ h.1, ?_⟩
  rw [hQ θ, hq]
  exact_mod_cast h.2

theorem checkExclFinite_sound [Fintype Θ] (memΩ : Θ → Bool) (Qq : Θ → ℚ) (qq : ℚ)
    (hmem : ∀ θ ∈ Ω, memΩ θ = true) (hQ : ∀ θ, Q θ = (Qq θ : ℝ)) (hq : q = (qq : ℝ))
    (h : checkExclFinite memΩ Qq qq = true) : confSet Ω Q q = ∅ := by
  simp only [checkExclFinite, decide_eq_true_eq] at h
  refine Set.eq_empty_iff_forall_notMem.mpr ?_
  rintro θ ⟨hθ, hle⟩
  have h1 := h θ (hmem θ hθ)
  rw [hQ θ, hq] at hle
  have h2 : (Qq θ : ℝ) ≤ (qq : ℝ) := hle
  have h3 : Qq θ ≤ qq := by exact_mod_cast h2
  exact absurd h1 (not_lt.mpr h3)

theorem checkExclFinite_complete [Fintype Θ] (memΩ : Θ → Bool) (Qq : Θ → ℚ) (qq : ℚ)
    (hmem : ∀ θ, memΩ θ = true ↔ θ ∈ Ω) (hQ : ∀ θ, Q θ = (Qq θ : ℝ)) (hq : q = (qq : ℝ))
    (h : confSet Ω Q q = ∅) : checkExclFinite memΩ Qq qq = true := by
  simp only [checkExclFinite, decide_eq_true_eq]
  intro θ hθ
  by_contra hlt
  have hle : Qq θ ≤ qq := not_lt.mp hlt
  have hmemθ : θ ∈ confSet Ω Q q := by
    refine ⟨(hmem θ).mp hθ, ?_⟩
    rw [hQ θ, hq]
    exact_mod_cast hle
  rw [h] at hmemθ
  exact Set.notMem_empty θ hmemθ

theorem checkWitness_example :
    checkWitness (fun _ : Fin 3 => true) (fun i => ((i : ℕ) : ℚ)) 1 1 = true := by
  decide

theorem checkExclFinite_example :
    checkExclFinite (fun i : Fin 3 => decide (1 ≤ (i : ℕ))) (fun i => ((i : ℕ) : ℚ)) (1 / 2) =
      true := by
  decide

/-! ## Acceleration-norm exclusion (l.120 "strictly positive lower bound on Iα") -/

/-- acceleration norm a(x) = sqrt(g^{ab} A_a A_b), A = 2 c B u (source (1), l.15-17);
g^{ab} = diag(-1,1,1,1) = `minkowski` -/
noncomputable def accelNorm (cl : ℝ) (x : FirstJet) : ℝ :=
  Real.sqrt (∑ a, ∑ b, minkowski a b * (2 * cl * Bu x a) * (2 * cl * Bu x b))

theorem accelNorm_of_geodesic (cl : ℝ) (x : FirstJet) (hx : x ∈ geodesicNull) :
    accelNorm cl x = 0 := by
  have h : Bu x = 0 := hx
  simp [accelNorm, h]

theorem accel_lower_bound_excludes {xmap : Θ → P} {G : Set P} (a : P → ℝ)
    (ha : ∀ x ∈ G, a x = 0) {c : ℝ} (hc : 0 < c) (h : ∀ θ ∈ confSet Ω Q q, c ≤ a (xmap θ)) :
    nullConfSet Ω Q q xmap G = ∅ := by
  refine Set.eq_empty_iff_forall_notMem.mpr ?_
  rintro θ ⟨hθ, hG⟩
  have h1 := h θ hθ
  rw [ha _ hG] at h1
  linarith

theorem accel_lower_bound_excludes_geodesic {xmap : Θ → FirstJet} (cl : ℝ) {c : ℝ} (hc : 0 < c)
    (h : ∀ θ ∈ confSet Ω Q q, c ≤ accelNorm cl (xmap θ)) :
    nullConfSet Ω Q q xmap geodesicNull = ∅ :=
  accel_lower_bound_excludes (accelNorm cl) (fun x hx => accelNorm_of_geodesic cl x hx) hc h

/-- dual certificate for the concrete geodesic null (2): g θ = Bu (xmap θ) -/
def geodesicDualExcl (Ω : Set Θ) (Q : Θ → ℝ) (q : ℝ) (xmap : Θ → FirstJet)
    (c : DualCert Ω (fun θ => Bu (xmap θ)) Q q) : ExclCert (Ω ∩ xmap ⁻¹' geodesicNull) Q q :=
  .dual Ω (fun θ => Bu (xmap θ)) rfl c

theorem geodesicDual_sound (Ω : Set Θ) (Q : Θ → ℝ) (q : ℝ) (xmap : Θ → FirstJet)
    (c : DualCert Ω (fun θ => Bu (xmap θ)) Q q) :
    nullConfSet Ω Q q xmap geodesicNull = ∅ := by
  rw [← nullConfSet_eq_confSet_inter]
  exact (geodesicDualExcl Ω Q q xmap c).sound

end Cert

/-! ## Negative controls -/

theorem solver_claim_not_proof :
    ∃ r : OptReport (Set.univ : Set ℝ) (fun θ => θ ^ 2) 0,
      r.run.status = SolverStatus.claimedInfeasible ∧
      (confSet (Set.univ : Set ℝ) (fun θ => θ ^ 2) 0).Nonempty ∧
      r.toCert = Cert.uncertified :=
  ⟨⟨⟨SolverStatus.claimedInfeasible, none, none, none⟩, none, none⟩, rfl,
    ⟨0, Set.mem_univ _, by norm_num⟩, rfl⟩

theorem inner_samples_not_exclusion :
    ∃ (Ω : Set ℝ) (Q : ℝ → ℝ) (q : ℝ) (G : Set ℝ) (s : Finset ℝ),
      s.Nonempty ∧ (↑s : Set ℝ) ⊆ confSet Ω Q q ∧ (∀ θ ∈ s, θ ∉ G) ∧
      (nullConfSet Ω Q q id G).Nonempty := by
  refine ⟨Set.univ, fun _ => 0, 0, {1}, {0}, Finset.singleton_nonempty 0, ?_, ?_, ?_⟩
  · intro θ _
    exact ⟨Set.mem_univ _, le_refl _⟩
  · intro θ hθ
    rw [Finset.mem_singleton] at hθ
    subst hθ
    norm_num
  · exact ⟨1, ⟨Set.mem_univ _, le_refl _⟩, rfl⟩

theorem zero_excluded_no_positive_bound :
    (0 : ℝ) ∉ (id '' confSet (Set.Ioi (0 : ℝ)) (fun _ => 0) 0) ∧
    ¬ ∃ c : ℝ, 0 < c ∧ ∀ θ ∈ confSet (Set.Ioi (0 : ℝ)) (fun _ => 0) 0, c ≤ id θ := by
  refine ⟨?_, ?_⟩
  · rintro ⟨θ, ⟨hθ, -⟩, h0⟩
    have : (0 : ℝ) < θ := hθ
    simp only [id] at h0
    linarith
  · rintro ⟨c, hc, h⟩
    have h2 := h (c / 2) ⟨Set.mem_Ioi.mpr (by linarith), le_refl _⟩
    simp only [id] at h2
    linarith

end G08D
