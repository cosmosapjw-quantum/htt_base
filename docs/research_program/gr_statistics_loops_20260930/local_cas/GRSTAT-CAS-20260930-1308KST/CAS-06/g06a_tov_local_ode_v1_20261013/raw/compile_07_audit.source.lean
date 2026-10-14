import G06ATOV

/-! G06-A axiom audit.  Each frozen target signature from FROZEN_TARGETS.md is
restated verbatim as an `example` checked against the compiled theorem, then the
axioms of every target are printed. -/

open G06ATOV Filter Topology

example : ∀ (Λ : ℝ), IsOpen {y : State | TOVDomain Λ y} := @T1_isOpen_domain
example : ∀ {Λ : ℝ} {y : State} (h : y.1 = 0), ¬ TOVDomain Λ y := @T1_excludes_center
example : ∀ {Λ : ℝ} {y : State} (h : lapse Λ y.1 y.2.1 = 0), ¬ TOVDomain Λ y :=
  @T1_excludes_horizon
example : ∀ {Λ : ℝ} {y : State} (h : y.2.2.2 ≤ 0), ¬ TOVDomain Λ y :=
  @T1_excludes_nonpositive_density
example : ∀ {κ α : ℝ} (h : AdmissibleParams κ α), α ≠ 0 := @T1_excludes_dust
example : ∀ {Λ : ℝ} {y : State} (h : TOVDomain Λ y), 0 < y.1 ^ 2 * lapse Λ y.1 y.2.1 :=
  @T1_denominator_pos

example : ∀ (n : ℕ∞) {κ Λ α : ℝ} (hα : α ≠ 0) {y : State}
    (hy : TOVDomain Λ y), ContDiffAt ℝ n (tovField κ Λ α) y := @T2_contDiffAt
example : ∀ {κ Λ α : ℝ} (hα : α ≠ 0) {y : State}
    (hy : TOVDomain Λ y),
    ∃ K : NNReal, ∃ U ∈ 𝓝 y, LipschitzOnWith K (tovField κ Λ α) U := @T2_locally_lipschitz

example : ∀ {κ Λ α : ℝ} (hp : AdmissibleParams κ α)
    {r0 m0 ν0 ε0 : ℝ} (hdat : TOVDomain Λ (r0, m0, ν0, ε0)),
    ∃ δ > 0, ∃ m ν ε : ℝ → ℝ, m r0 = m0 ∧ ν r0 = ν0 ∧ ε r0 = ε0 ∧
      IsTOVSolutionOn κ Λ α m ν ε (Set.Ioo (r0 - δ) (r0 + δ)) := @T3_local_existence

example : ∀ {κ Λ α : ℝ} (hp : AdmissibleParams κ α) {a b r0 : ℝ}
    (hr0 : r0 ∈ Set.Ioo a b) {m₁ ν₁ ε₁ m₂ ν₂ ε₂ : ℝ → ℝ}
    (h₁ : IsTOVSolutionOn κ Λ α m₁ ν₁ ε₁ (Set.Ioo a b))
    (h₂ : IsTOVSolutionOn κ Λ α m₂ ν₂ ε₂ (Set.Ioo a b))
    (hm : m₁ r0 = m₂ r0) (hν : ν₁ r0 = ν₂ r0) (hε : ε₁ r0 = ε₂ r0),
    Set.EqOn m₁ m₂ (Set.Ioo a b) ∧ Set.EqOn ν₁ ν₂ (Set.Ioo a b) ∧
      Set.EqOn ε₁ ε₂ (Set.Ioo a b) := @T4_uniqueness

example : ∀ {κ Λ α : ℝ} (hp : AdmissibleParams κ α)
    {m ν ε : ℝ → ℝ} {I : Set ℝ} (hI : IsOpen I)
    (hsol : IsTOVSolutionOn κ Λ α m ν ε I) {r θ : ℝ} (hr : r ∈ I)
    (hθ0 : 0 < θ) (hθπ : θ < Real.pi),
    CAS06Bundles.C01TOVEinstein ν m ε κ Λ α r θ := @T5_einstein_on_solution
example : ∀ {κ Λ α : ℝ} (hp : AdmissibleParams κ α)
    {m ν ε : ℝ → ℝ} {I : Set ℝ} (hI : IsOpen I)
    (hsol : IsTOVSolutionOn κ Λ α m ν ε I) {r θ : ℝ} (hr : r ∈ I)
    (hθ0 : 0 < θ) (hθπ : θ < Real.pi),
    ∃ Frr : ℝ, HasDerivAt (deriv (CAS06Adopted.massLapse m Λ)) Frr r ∧
      CAS06Bundles.C01CoordinateRiemann ν (CAS06Adopted.massLapse m Λ) r θ
        (CAS06Bundles.C01TOVNuSecond m ε κ Λ α r) Frr := @T5_riemann_on_solution

example : ∀ {κ Λ α : ℝ} (hp : AdmissibleParams κ α)
    {r0 m0 ν0 ε0 : ℝ} (hdat : TOVDomain Λ (r0, m0, ν0, ε0)),
    ∃ δ > 0, ∃ m ν ε : ℝ → ℝ, m r0 = m0 ∧ ν r0 = ν0 ∧ ε r0 = ε0 ∧
      IsTOVSolutionOn κ Λ α m ν ε (Set.Ioo (r0 - δ) (r0 + δ)) ∧
      (∀ r ∈ Set.Ioo (r0 - δ) (r0 + δ), ∀ θ, 0 < θ → θ < Real.pi →
        CAS06Bundles.C01TOVEinstein ν m ε κ Λ α r θ) ∧
      (∀ m' ν' ε' : ℝ → ℝ,
        IsTOVSolutionOn κ Λ α m' ν' ε' (Set.Ioo (r0 - δ) (r0 + δ)) →
        m' r0 = m0 → ν' r0 = ν0 → ε' r0 = ε0 →
        Set.EqOn m' m (Set.Ioo (r0 - δ) (r0 + δ)) ∧
        Set.EqOn ν' ν (Set.Ioo (r0 - δ) (r0 + δ)) ∧
        Set.EqOn ε' ε (Set.Ioo (r0 - δ) (r0 + δ))) := @G06A_capstone

-- definitional faithfulness bridges to the accepted CAS-06 symbols
example : ∀ (m : ℝ → ℝ) (Λ r : ℝ), lapse Λ r (m r) = CAS06Adopted.massLapse m Λ r :=
  lapse_eq_massLapse
example : ∀ (m ε : ℝ → ℝ) (κ Λ α r : ℝ), nuRHS κ Λ α r (m r) (ε r) =
    CAS06Adopted.tovNuFunction m (fun s => α * ε s) (CAS06Adopted.massLapse m Λ) κ Λ r :=
  nuRHS_eq_tovNuFunction

#print axioms G06ATOV.T1_isOpen_domain
#print axioms G06ATOV.T1_excludes_center
#print axioms G06ATOV.T1_excludes_horizon
#print axioms G06ATOV.T1_excludes_nonpositive_density
#print axioms G06ATOV.T1_excludes_dust
#print axioms G06ATOV.T1_denominator_pos
#print axioms G06ATOV.T2_contDiffAt
#print axioms G06ATOV.T2_locally_lipschitz
#print axioms G06ATOV.T3_local_existence
#print axioms G06ATOV.T4_uniqueness
#print axioms G06ATOV.T5_einstein_on_solution
#print axioms G06ATOV.T5_riemann_on_solution
#print axioms G06ATOV.G06A_capstone
#print axioms G06ATOV.lapse_eq_massLapse
#print axioms G06ATOV.nuRHS_eq_tovNuFunction
