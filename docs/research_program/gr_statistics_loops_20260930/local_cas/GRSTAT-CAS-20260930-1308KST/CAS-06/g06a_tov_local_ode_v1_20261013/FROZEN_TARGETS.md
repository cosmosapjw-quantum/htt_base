# G06-A frozen targets (GR-CAS-06: actual local ODE solution of TOV on the open domain)

Frozen BEFORE any proof attempt of the targets below. Lean module `G06ATOV`
(`lean/G06ATOV.lean`), namespace `G06ATOV`, importing the accepted CAS-06
adopted-successor modules (`CAS06Bundles` -> `C03Action` -> `CAS06Foundation`,
`CAS06ScalarAccepted`) compiled unchanged from their recorded bytes.

## 0. Recovered source (PR #477 history)

PR #477 = `refs/remotes/pr/477` (fetched only), two commits on top of
`f1007dd3` (merge of PR #476):

* `43e3f727` "GRSTAT-CAS-06: Verify scalar calculus and adopt successor inputs"
  introduces
  `.../CAS-06/codex_only_continuation_20261004/NEUTRAL_SUCCESSOR_CANDIDATE.json`
  (sha256 `87e986d6...b55f4`) and `OWNER_ADOPTION.json` (sha256 `e4b49f69...47d4`,
  status `OWNER_ADOPTED_DEFINITIONS_FRAME_INPUTS`).
* `1a375536` "GRSTAT-CAS-06: Verify owner-adopted finite TOV and action components"
  introduces `.../adopted_successor_v1/ADMITTED_INPUTS.json`
  (sha256 `711de321...793eb`) and the accepted Lean sources
  (`CAS06Foundation.lean`, `CAS06Bundles.lean`, `C03Action.lean`,
  `CAS06ScalarAccepted.lean`); aggregate `CAS_4AXIS_PASS`
  (`ADJUDICATION_STDOUT_REPAIRED.json`).

Defining text (`ADMITTED_INPUTS.json` -> `definitions.C01`, identical in
`NEUTRAL_SUCCESSOR_CANDIDATE.json`):

* metric: `g=diag(-exp(2nu(r)),1/F(r),r^2,r^2 sin(theta)^2), F=1-2m(r)/r-Lambda r^2/3`
  (chart `(x0,r,theta,phi)`, `r>0, 0<theta<pi`; branch `F>0`).
* TOV system: `mprime=kappa r^2epsilon/2; nuprime=(m+kappa alpha epsilon r^3/2-Lambda r^3/3)/(r^2F); epsilonprime=-(1+alpha)epsilon nuprime/alpha`.
* fixed causal EOS: `p=alpha epsilon`, `0<alpha<1` (assumptions
  `c>0,kappa>0,epsilon0>0,0<alpha<1,p0=alpha epsilon0`; `cs^2/c^2=alpha` in C03).
* domain: "Each radial jet is evaluated where r>0,F>0,epsilon>0,0<theta<pi";
  singular loci excluded: `TOV-DUST alpha0`, `TOV-HORIZON F0=0`, `TOV-CENTER r0=0`.
* `analytic_obligations_not_assumptions[0]`: "Local smooth ODE existence on r>0,F>0,epsilon>0" — the obligation addressed here.

Lean counterparts in the accepted sources (reused, not redefined):
`CAS06Adopted.massLapse m Λ r := 1 - 2 * m r / r - Λ * r ^ 2 / 3`,
`CAS06Adopted.tovNuFunction m p F κ Λ s := (m s + (κ / 2) * (p s * s ^ 3) - (Λ / 3) * s ^ 3) / (s ^ 2 * F s)`
(used with `p := fun s => α * ε s`, `F := massLapse m Λ`),
`CAS06Bundles.C01TOVEinstein`, `CAS06Bundles.C01CoordinateRiemann`,
`CAS06Bundles.C01TOVNuSecond`, theorem `CAS06Bundles.C01_TOV_metric_bundle`.

Real-power / log conditions: the TOV system with the linear EOS `p=alpha epsilon`
contains no real power or logarithm (the real power `X^s` belongs to the C03 action,
not to the ODE). The only denominators are `r^2 F` and `alpha`; `nu` enters the
metric only through `exp(2 nu)`, which is total. The constant `c` does not enter
the TOV system.

## 1. Definitions (frozen)

```lean
abbrev State := ℝ × ℝ × ℝ × ℝ           -- (r, m, ν, ε)

def lapse (Λ r m : ℝ) : ℝ := 1 - 2 * m / r - Λ * r ^ 2 / 3

def nuRHS (κ Λ α r m ε : ℝ) : ℝ :=
  (m + (κ / 2) * ((α * ε) * r ^ 3) - (Λ / 3) * r ^ 3) / (r ^ 2 * lapse Λ r m)

/-- autonomous form of the TOV system, independent variable carried as r' = 1 -/
def tovField (κ Λ α : ℝ) (y : State) : State :=
  (1, κ * y.1 ^ 2 * y.2.2.2 / 2, nuRHS κ Λ α y.1 y.2.1 y.2.2.2,
    -(1 + α) * y.2.2.2 * nuRHS κ Λ α y.1 y.2.1 y.2.2.2 / α)

structure AdmissibleParams (κ α : ℝ) : Prop where
  kappa_pos : 0 < κ
  alpha_pos : 0 < α
  alpha_lt_one : α < 1

/-- T1 open admissible domain: r > 0, F > 0, ε > 0 (strict). -/
def TOVDomain (Λ : ℝ) (y : State) : Prop :=
  0 < y.1 ∧ 0 < lapse Λ y.1 y.2.1 ∧ 0 < y.2.2.2

def IsTOVSolutionOn (κ Λ α : ℝ) (m ν ε : ℝ → ℝ) (I : Set ℝ) : Prop :=
  ∀ r ∈ I, TOVDomain Λ (r, m r, ν r, ε r) ∧
    HasDerivAt m (κ * r ^ 2 * ε r / 2) r ∧
    HasDerivAt ν (CAS06Adopted.tovNuFunction m (fun s => α * ε s)
      (CAS06Adopted.massLapse m Λ) κ Λ r) r ∧
    HasDerivAt ε (-(1 + α) * ε r * CAS06Adopted.tovNuFunction m (fun s => α * ε s)
      (CAS06Adopted.massLapse m Λ) κ Λ r / α) r
```

Faithfulness bridges (definitional): `lapse Λ r (m r) = CAS06Adopted.massLapse m Λ r`,
`nuRHS κ Λ α r (m r) (ε r) = CAS06Adopted.tovNuFunction m (fun s => α * ε s) (CAS06Adopted.massLapse m Λ) κ Λ r`.

## 2. Targets (frozen signatures)

```lean
-- T1 open domain, strict positivity, excluded loci
theorem T1_isOpen_domain (Λ : ℝ) : IsOpen {y : State | TOVDomain Λ y}
theorem T1_excludes_center {Λ : ℝ} {y : State} (h : y.1 = 0) : ¬ TOVDomain Λ y
theorem T1_excludes_horizon {Λ : ℝ} {y : State} (h : lapse Λ y.1 y.2.1 = 0) : ¬ TOVDomain Λ y
theorem T1_excludes_nonpositive_density {Λ : ℝ} {y : State} (h : y.2.2.2 ≤ 0) : ¬ TOVDomain Λ y
theorem T1_excludes_dust {κ α : ℝ} (h : AdmissibleParams κ α) : α ≠ 0
theorem T1_denominator_pos {Λ : ℝ} {y : State} (h : TOVDomain Λ y) :
    0 < y.1 ^ 2 * lapse Λ y.1 y.2.1

-- T2 smoothness (every finite order and ∞) and local Lipschitz on the open domain
theorem T2_contDiffAt (n : ℕ∞) {κ Λ α : ℝ} (hα : α ≠ 0) {y : State}
    (hy : TOVDomain Λ y) : ContDiffAt ℝ n (tovField κ Λ α) y
theorem T2_locally_lipschitz {κ Λ α : ℝ} (hα : α ≠ 0) {y : State}
    (hy : TOVDomain Λ y) :
    ∃ K : NNReal, ∃ U ∈ 𝓝 y, LipschitzOnWith K (tovField κ Λ α) U

-- T3 local existence for every admissible datum at r0 > 0
theorem T3_local_existence {κ Λ α : ℝ} (hp : AdmissibleParams κ α)
    {r0 m0 ν0 ε0 : ℝ} (hdat : TOVDomain Λ (r0, m0, ν0, ε0)) :
    ∃ δ > 0, ∃ m ν ε : ℝ → ℝ, m r0 = m0 ∧ ν r0 = ν0 ∧ ε r0 = ε0 ∧
      IsTOVSolutionOn κ Λ α m ν ε (Set.Ioo (r0 - δ) (r0 + δ))

-- T4 uniqueness on any common open interval inside the domain
theorem T4_uniqueness {κ Λ α : ℝ} (hp : AdmissibleParams κ α) {a b r0 : ℝ}
    (hr0 : r0 ∈ Set.Ioo a b) {m₁ ν₁ ε₁ m₂ ν₂ ε₂ : ℝ → ℝ}
    (h₁ : IsTOVSolutionOn κ Λ α m₁ ν₁ ε₁ (Set.Ioo a b))
    (h₂ : IsTOVSolutionOn κ Λ α m₂ ν₂ ε₂ (Set.Ioo a b))
    (hm : m₁ r0 = m₂ r0) (hν : ν₁ r0 = ν₂ r0) (hε : ε₁ r0 = ε₂ r0) :
    Set.EqOn m₁ m₂ (Set.Ioo a b) ∧ Set.EqOn ν₁ ν₂ (Set.Ioo a b) ∧
      Set.EqOn ε₁ ε₂ (Set.Ioo a b)

-- T5 the actual solution substituted into the static metric satisfies every
-- independent Einstein equation G + Λ g = κ T, T = diag(ε, αε, αε, αε) (orthonormal),
-- all off-diagonal components zero; plus the metric-derived coordinate Riemann table.
theorem T5_einstein_on_solution {κ Λ α : ℝ} (hp : AdmissibleParams κ α)
    {m ν ε : ℝ → ℝ} {I : Set ℝ} (hI : IsOpen I)
    (hsol : IsTOVSolutionOn κ Λ α m ν ε I) {r θ : ℝ} (hr : r ∈ I)
    (hθ0 : 0 < θ) (hθπ : θ < Real.pi) :
    CAS06Bundles.C01TOVEinstein ν m ε κ Λ α r θ
theorem T5_riemann_on_solution {κ Λ α : ℝ} (hp : AdmissibleParams κ α)
    {m ν ε : ℝ → ℝ} {I : Set ℝ} (hI : IsOpen I)
    (hsol : IsTOVSolutionOn κ Λ α m ν ε I) {r θ : ℝ} (hr : r ∈ I)
    (hθ0 : 0 < θ) (hθπ : θ < Real.pi) :
    ∃ Frr : ℝ, HasDerivAt (deriv (CAS06Adopted.massLapse m Λ)) Frr r ∧
      CAS06Bundles.C01CoordinateRiemann ν (CAS06Adopted.massLapse m Λ) r θ
        (CAS06Bundles.C01TOVNuSecond m ε κ Λ α r) Frr

-- Capstone: actual solution + interval witness + uniqueness + Einstein equations
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
        Set.EqOn ε' ε (Set.Ioo (r0 - δ) (r0 + δ)))
```

Not claimed: global regular-star existence; center `r=0` regularity; maximal
interval; EOS physical admissibility beyond the recovered statement; historical
four-axis acceptance; scientific admission. `r=0`, `F=0`, `ε≤0`, `α=0` are not in
the admissible interior.
