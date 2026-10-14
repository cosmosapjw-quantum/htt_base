# G06-B frozen targets (GR-CAS-06: fixed P(X) action on the constructed TOV germs; strict DEC persistence)

Frozen BEFORE any proof compile of the targets below (only the unchanged reused
modules were compiled before this file was written).  Lean module
`G06BPXAction` (`lean/G06BPXAction.lean`), namespace `G06BPX`, importing the
reviewed G06-A module `G06ATOV` (which imports `CAS06Bundles` -> `C03Action` ->
`CAS06Foundation`, `CAS06ScalarAccepted`), all compiled unchanged from their
recorded bytes into `raw/imports`.  Source recovery: `SOURCE_RECOVERY.md`.

## 0. Original statement (recovered) and quantifier structure

EF5c / C03 (see SOURCE_RECOVERY.md): fix `Pstar>0`, `q>0`, `0<alpha<1`,
`s=(1+alpha)/(2 alpha)`, `P(X)=Pstar X^s`, `X=-g^{ab}psi_a psi_b/2>0`,
`psi=q x0`, with `Pstar (q^2/2)^s = p0 = alpha eps0` **fixed**.  Family (C04
`family_candidate`): fix `kappa, alpha, eps0, p0, Pstar, q, mu, Lambda`; vary only
`r0` with `F0 = 1 - C r0^2 > 0`, `m0 = mu r0^3`, `nu0 = 0`.  Claim: the stress and
scalar equation obtained by variation hold on each constructed member, the fluid is
`p = P`, `eps = 2 X P_X - P = (2s-1) P = P/alpha`, `eps = eps0 e^{-2 s nu}` (the
density solved by the TOV system), and each member has strict DEC (type-I criterion
`eps > |p|`, `eps > 0`) throughout a sufficiently small open neighbourhood.
`TOV-ACTION Pstar,q cannot vary by member`.

Lean quantifier discipline: theory constants `κ Λ α Pstar q` (and, for the contract
family, `ε0 μ` together with the fixed relation `Pstar (q^2/2)^s = α ε0`) are bound
**before** the `∀` over members; the action `CAS06Action.actionDensity Pstar s`, the
EOS exponent `s = CAS06Scalar.exponent α` and `ψ = scalarGradient q` therefore cannot
depend on the member.  The relation `Pstar (q^2/2)^s = α ε0` is a hypothesis on the
fixed constants only (stated once, outside the member quantifier); it is never solved
by choosing `Pstar` or `q` per member.

General G06-A germs carry an arbitrary lapse normalisation `ν0`; for those the
member-side compatibility condition is `PXMatched Pstar α q ν0 ε0`, i.e.
`P(X(r0)) = α ε0` with `X(r0) = (q^2/2) e^{-2ν0}` (a condition on member data against
fixed constants).  The contract family is the special case `ν0 = 0`, where it reduces
to the fixed relation.  Real powers are manipulated only at `X > 0` (`q ≠ 0`).

## 1. Definitions (frozen)

```lean
def PXMatched (Pstar α q ν0 ε0 : ℝ) : Prop :=
  Pstar * ((q ^ 2 / 2) * Real.exp (-2 * ν0)) ^ CAS06Scalar.exponent α = α * ε0

def minkowski (a b : Fin 4) : ℝ := if a = b then (if a = 0 then -1 else 1) else 0

/-- orthonormal-frame components of the action stress on the actual metric point -/
def pxFrameStress (Pstar s q : ℝ) (ν F : ℝ → ℝ) (r θ : ℝ) (a b : Fin 4) : ℝ :=
  CAS06Adopted.chartFrameScale (ν r) (F r) r θ a *
  CAS06Adopted.chartFrameScale (ν r) (F r) r θ b *
  CAS06Action.actionStress Pstar s
    (CAS06Action.chartContravariant (ν r) (F r) r θ)
    (CAS06Action.chartCovariant (ν r) (F r) r θ)
    (CAS06Action.scalarGradient q) a b

/-- orthonormal-frame Einstein tensor computed from the metric (accepted CAS-06 definition) -/
def frameEinstein (ν m : ℝ → ℝ) (Λ r θ : ℝ) (a b : Fin 4) : ℝ :=
  CAS06Adopted.chartFrameScale (ν r) (CAS06Adopted.massLapse m Λ r) r θ a *
  CAS06Adopted.chartFrameScale (ν r) (CAS06Adopted.massLapse m Λ r) r θ b *
  CAS06Adopted.chartEinsteinFromMetric ν (CAS06Adopted.massLapse m Λ)
    (deriv ν) (deriv (CAS06Adopted.massLapse m Λ)) r θ a b

/-- Einstein–matter equations G + Λ g = κ T^{P(X)} (all 16 frame components) -/
def PXEinsteinMatter (Pstar s q κ Λ : ℝ) (ν m : ℝ → ℝ) (r θ : ℝ) : Prop :=
  ∀ a b : Fin 4, frameEinstein ν m Λ r θ a b + Λ * minkowski a b =
    κ * pxFrameStress Pstar s q ν (CAS06Adopted.massLapse m Λ) r θ a b

/-- metric variation gives the stress, scalar variation gives the current, at the actual point -/
def PXStressCurrentAt (Pstar s q : ℝ) (ν F : ℝ → ℝ) (r θ : ℝ) : Prop :=
  (∀ H : CAS06Action.Mat4, (∀ a b : Fin 4, H a b = H b a) →
    HasDerivAt (fun t : ℝ => CAS06Action.actionDensity Pstar s
        (CAS06Action.chartContravariant (ν r) (F r) r θ + t • H)
        (CAS06Action.scalarGradient q))
      (-(CAS06Action.volumeDensity (CAS06Action.chartContravariant (ν r) (F r) r θ) / 2) *
        ∑ a : Fin 4, ∑ b : Fin 4, CAS06Action.actionStress Pstar s
          (CAS06Action.chartContravariant (ν r) (F r) r θ)
          (CAS06Action.chartCovariant (ν r) (F r) r θ)
          (CAS06Action.scalarGradient q) a b * H a b) 0) ∧
  (∀ η : Fin 4 → ℝ,
    HasDerivAt (fun t : ℝ => CAS06Action.actionDensity Pstar s
        (CAS06Action.chartContravariant (ν r) (F r) r θ)
        (fun a => CAS06Action.scalarGradient q a + t * η a))
      (-CAS06Action.volumeDensity (CAS06Action.chartContravariant (ν r) (F r) r θ) *
        ∑ a : Fin 4, CAS06Action.actionCurrent Pstar s
          (CAS06Action.chartContravariant (ν r) (F r) r θ)
          (CAS06Action.scalarGradient q) a * η a) 0)

/-- scalar Euler–Lagrange equation ∂_a(√-g J^a)=0 with honest (HasDerivAt) line
    derivatives and a non-zero current (non-vacuity) -/
def PXScalarEquationAt (Pstar s q : ℝ) (ν F : ℝ → ℝ) (r θ : ℝ) : Prop :=
  (∀ (dir : Fin 4) (x : ℝ),
    HasDerivAt (CAS06Action.chartCurrentDensityOnLine Pstar s q ν F r θ dir) 0 x) ∧
  CAS06Action.chartScalarCurrentDivergence Pstar s q ν F r θ = 0 ∧
  CAS06Action.actionCurrent Pstar s (CAS06Action.chartContravariant (ν r) (F r) r θ)
    (CAS06Action.scalarGradient q) 0 ≠ 0

def FutureCausal (k : Fin 4 → ℝ) : Prop :=
  0 < k 0 ∧ k 1 ^ 2 + k 2 ^ 2 + k 3 ^ 2 ≤ k 0 ^ 2
def FutureTimelike (j : Fin 4 → ℝ) : Prop :=
  0 < j 0 ∧ j 1 ^ 2 + j 2 ^ 2 + j 3 ^ 2 < j 0 ^ 2
/-- frame energy flux j^a = -T^a_b k^b (index raised with η) -/
def decFlux (T : Fin 4 → Fin 4 → ℝ) (k : Fin 4 → ℝ) (a : Fin 4) : ℝ :=
  -(minkowski a a * ∑ b : Fin 4, T a b * k b)
def StrictDEC (T : Fin 4 → Fin 4 → ℝ) : Prop :=
  ∀ k : Fin 4 → ℝ, FutureCausal k → FutureTimelike (decFlux T k)

/-- strict DEC of the P(X) stress at the actual point: type-I margin and flux form -/
def PXStrictDECAt (Pstar α q : ℝ) (ν F : ℝ → ℝ) (r θ : ℝ) : Prop :=
  0 < CAS06Action.actionRadialEnergy Pstar (CAS06Scalar.exponent α) ν q r ∧
  |CAS06Action.actionRadialPressure Pstar (CAS06Scalar.exponent α) ν q r| <
    CAS06Action.actionRadialEnergy Pstar (CAS06Scalar.exponent α) ν q r ∧
  CAS06Action.actionRadialEnergy Pstar (CAS06Scalar.exponent α) ν q r -
    |CAS06Action.actionRadialPressure Pstar (CAS06Scalar.exponent α) ν q r| =
    (1 - α) * CAS06Action.actionRadialEnergy Pstar (CAS06Scalar.exponent α) ν q r ∧
  StrictDEC (pxFrameStress Pstar (CAS06Scalar.exponent α) q ν F r θ)

def PXFieldEquationsAt (κ Λ α Pstar q : ℝ) (m ν : ℝ → ℝ) (r θ : ℝ) : Prop :=
  PXStressCurrentAt Pstar (CAS06Scalar.exponent α) q ν (CAS06Adopted.massLapse m Λ) r θ ∧
  PXEinsteinMatter Pstar (CAS06Scalar.exponent α) q κ Λ ν m r θ ∧
  PXScalarEquationAt Pstar (CAS06Scalar.exponent α) q ν (CAS06Adopted.massLapse m Λ) r θ ∧
  PXStrictDECAt Pstar α q ν (CAS06Adopted.massLapse m Λ) r θ

/-- X>0 regularity of Pstar X^s along the actual field, P_X>0, sound-speed ratio α -/
def PXRegularOn (Pstar α q : ℝ) (ν : ℝ → ℝ) (I : Set ℝ) : Prop :=
  ∀ r ∈ I,
    0 < CAS06Action.actionRadialX ν q r ∧
    (∀ n : WithTop ℕ∞, ContDiffAt ℝ n
      (CAS06Scalar.pressure Pstar (CAS06Scalar.exponent α)) (CAS06Action.actionRadialX ν q r)) ∧
    HasDerivAt (CAS06Action.actionRadialPressure Pstar (CAS06Scalar.exponent α) ν q)
      (-(CAS06Action.actionRadialEnergy Pstar (CAS06Scalar.exponent α) ν q r +
        CAS06Action.actionRadialPressure Pstar (CAS06Scalar.exponent α) ν q r) * deriv ν r) r ∧
    0 < CAS06Scalar.first Pstar (CAS06Scalar.exponent α) (CAS06Action.actionRadialX ν q r) ∧
    0 < deriv (CAS06Scalar.pressure Pstar (CAS06Scalar.exponent α)) (CAS06Action.actionRadialX ν q r) +
      2 * CAS06Action.actionRadialX ν q r *
        deriv (deriv (CAS06Scalar.pressure Pstar (CAS06Scalar.exponent α)))
          (CAS06Action.actionRadialX ν q r) ∧
    deriv (CAS06Scalar.pressure Pstar (CAS06Scalar.exponent α)) (CAS06Action.actionRadialX ν q r) /
      (deriv (CAS06Scalar.pressure Pstar (CAS06Scalar.exponent α)) (CAS06Action.actionRadialX ν q r) +
        2 * CAS06Action.actionRadialX ν q r *
          deriv (deriv (CAS06Scalar.pressure Pstar (CAS06Scalar.exponent α)))
            (CAS06Action.actionRadialX ν q r)) = α

/-- the P(X) fluid IS the TOV fluid on the interval, and ε e^{2sν} is constant -/
def PXFluidOn (Pstar α q : ℝ) (ν ε : ℝ → ℝ) (r0 : ℝ) (I : Set ℝ) : Prop :=
  ∀ r ∈ I,
    CAS06Action.actionRadialEnergy Pstar (CAS06Scalar.exponent α) ν q r = ε r ∧
    CAS06Action.actionRadialPressure Pstar (CAS06Scalar.exponent α) ν q r = α * ε r ∧
    ε r * Real.exp (2 * CAS06Scalar.exponent α * ν r) =
      ε r0 * Real.exp (2 * CAS06Scalar.exponent α * ν r0)

/-- uniform strict-DEC margin and X/F positivity on a neighbourhood of the event -/
def PXMarginPersists (Pstar α q : ℝ) (ν F ε : ℝ → ℝ) (r0 : ℝ) (I : Set ℝ) : Prop :=
  ∃ η > 0, ∀ r ∈ Set.Ioo (r0 - η) (r0 + η), r ∈ I ∧
    (1 - α) * ε r0 / 2 <
      CAS06Action.actionRadialEnergy Pstar (CAS06Scalar.exponent α) ν q r -
        |CAS06Action.actionRadialPressure Pstar (CAS06Scalar.exponent α) ν q r| ∧
    CAS06Action.actionRadialX ν q r0 / 2 < CAS06Action.actionRadialX ν q r ∧
    F r0 / 2 < F r
```

## 2. Targets (frozen signatures)

```lean
-- T1  X>0 regularity of Pstar X^s (every order incl. ω), P_X > 0
theorem T1_pressure_contDiffAt (Pstar s : ℝ) {x : ℝ} (hx : 0 < x) (n : WithTop ℕ∞) :
    ContDiffAt ℝ n (CAS06Scalar.pressure Pstar s) x
theorem T1_first_pos {Pstar α x : ℝ} (hP : 0 < Pstar) (hα : 0 < α) (hx : 0 < x) :
    0 < CAS06Scalar.first Pstar (CAS06Scalar.exponent α) x
theorem T1_regular_on {κ Λ α Pstar q : ℝ} (hp : G06ATOV.AdmissibleParams κ α)
    (hP : 0 < Pstar) (hq : q ≠ 0) {m ν ε : ℝ → ℝ} {I : Set ℝ}
    (hsol : G06ATOV.IsTOVSolutionOn κ Λ α m ν ε I) :
    PXRegularOn Pstar α q ν I

-- T2  stress/current identities applied at the actual metric/scalar pair
theorem T2_stress_current_at {Pstar s q : ℝ} {ν F : ℝ → ℝ} {r θ : ℝ}
    (hq : q ≠ 0) (hr : 0 < r) (hF : 0 < F r) (hθ0 : 0 < θ) (hθπ : θ < Real.pi) :
    PXStressCurrentAt Pstar s q ν F r θ
theorem T2_frame_stress (Pstar s q : ℝ) (ν F : ℝ → ℝ) (r θ : ℝ)
    (hF : 0 < F r) (hr : 0 < r) (hs : Real.sin θ ≠ 0) :
    ∀ a b : Fin 4, pxFrameStress Pstar s q ν F r θ a b =
      if a = b then
        (if a = 0 then CAS06Action.actionRadialEnergy Pstar s ν q r
         else CAS06Action.actionRadialPressure Pstar s ν q r)
      else 0
theorem T2_frame_stress_bridge (Pstar s q : ℝ) (ν F : ℝ → ℝ) (r θ : ℝ) (hν : ν r = 0) :
    ∀ a b : Fin 4, pxFrameStress Pstar s q ν F r θ a b =
      CAS06Action.chartActionStressHat Pstar s q (F r) r θ a b

-- T3  P(X) fluid = TOV fluid on the whole interval (same ν, ε); closed form of matching
theorem T3_integrating_factor {α : ℝ} (hα : α ≠ 0) {f ν N : ℝ → ℝ} {I : Set ℝ}
    (hI : IsOpen I) (hIc : IsPreconnected I)
    (hf : ∀ r ∈ I, HasDerivAt f (-(1 + α) * f r * N r / α) r)
    (hν : ∀ r ∈ I, HasDerivAt ν (N r) r) {x y : ℝ} (hx : x ∈ I) (hy : y ∈ I) :
    f x * Real.exp ((1 + α) / α * ν x) = f y * Real.exp ((1 + α) / α * ν y)
theorem T3_fluid_identification {κ Λ α Pstar q : ℝ} (hp : G06ATOV.AdmissibleParams κ α)
    (hq : q ≠ 0) {m ν ε : ℝ → ℝ} {I : Set ℝ} (hI : IsOpen I) (hIc : IsPreconnected I)
    (hsol : G06ATOV.IsTOVSolutionOn κ Λ α m ν ε I) {r0 : ℝ} (hr0 : r0 ∈ I)
    (hmatch : PXMatched Pstar α q (ν r0) (ε r0)) :
    PXFluidOn Pstar α q ν ε r0 I
theorem T3_matched_closed_form {Pstar α q ν0 ε0 : ℝ} (hα : 0 < α) (hq : q ≠ 0) :
    PXMatched Pstar α q ν0 ε0 ↔
      ε0 = Pstar * (q ^ 2 / 2) ^ CAS06Scalar.exponent α / α *
        Real.exp (-2 * CAS06Scalar.exponent α * ν0)

-- T4  same-pair field equations: Einstein–matter (all frame components) and scalar equation
theorem T4_einstein_matter {κ Λ α Pstar q : ℝ} (hp : G06ATOV.AdmissibleParams κ α)
    {m ν ε : ℝ → ℝ} {I : Set ℝ} (hI : IsOpen I)
    (hsol : G06ATOV.IsTOVSolutionOn κ Λ α m ν ε I) {r θ : ℝ} (hr : r ∈ I)
    (hθ0 : 0 < θ) (hθπ : θ < Real.pi)
    (hE : CAS06Action.actionRadialEnergy Pstar (CAS06Scalar.exponent α) ν q r = ε r)
    (hPr : CAS06Action.actionRadialPressure Pstar (CAS06Scalar.exponent α) ν q r = α * ε r) :
    PXEinsteinMatter Pstar (CAS06Scalar.exponent α) q κ Λ ν m r θ
theorem T4_scalar_equation {Pstar s q : ℝ} {ν F : ℝ → ℝ} {r θ : ℝ}
    (hP : 0 < Pstar) (hs : 0 < s) (hq : q ≠ 0) :
    PXScalarEquationAt Pstar s q ν F r θ

-- T5  strict DEC (type-I margin and flux form) pointwise, and uniform persistence
theorem T5_strictDEC_diag {E P : ℝ} (hE : 0 < E) (hP : |P| < E)
    (T : Fin 4 → Fin 4 → ℝ)
    (hT : ∀ a b : Fin 4, T a b = if a = b then (if a = 0 then E else P) else 0) :
    StrictDEC T
theorem T5_strictDEC_at {κ Λ α Pstar q : ℝ} (hp : G06ATOV.AdmissibleParams κ α)
    {m ν ε : ℝ → ℝ} {I : Set ℝ} (hsol : G06ATOV.IsTOVSolutionOn κ Λ α m ν ε I)
    {r0 : ℝ} (hfluid : PXFluidOn Pstar α q ν ε r0 I) {r θ : ℝ} (hr : r ∈ I)
    (hθ0 : 0 < θ) (hθπ : θ < Real.pi) :
    PXStrictDECAt Pstar α q ν (CAS06Adopted.massLapse m Λ) r θ
theorem T5_margin_persists {κ Λ α Pstar q : ℝ} (hp : G06ATOV.AdmissibleParams κ α)
    (hq : q ≠ 0) {m ν ε : ℝ → ℝ} {I : Set ℝ} (hI : IsOpen I)
    (hsol : G06ATOV.IsTOVSolutionOn κ Λ α m ν ε I)
    {r0 : ℝ} (hfluid : PXFluidOn Pstar α q ν ε r0 I) (hr0 : r0 ∈ I) :
    PXMarginPersists Pstar α q ν (CAS06Adopted.massLapse m Λ) ε r0 I

-- Capstone (G06-A germs, fixed theory outside the member quantifier)
theorem G06B_germ_capstone {κ Λ α Pstar q : ℝ} (hp : G06ATOV.AdmissibleParams κ α)
    (hP : 0 < Pstar) (hq : 0 < q) :
    ∀ r0 m0 ν0 ε0 : ℝ, G06ATOV.TOVDomain Λ (r0, m0, ν0, ε0) →
      PXMatched Pstar α q ν0 ε0 →
      ∃ δ > 0, ∃ m ν ε : ℝ → ℝ, m r0 = m0 ∧ ν r0 = ν0 ∧ ε r0 = ε0 ∧
        G06ATOV.IsTOVSolutionOn κ Λ α m ν ε (Set.Ioo (r0 - δ) (r0 + δ)) ∧
        PXRegularOn Pstar α q ν (Set.Ioo (r0 - δ) (r0 + δ)) ∧
        PXFluidOn Pstar α q ν ε r0 (Set.Ioo (r0 - δ) (r0 + δ)) ∧
        (∀ r ∈ Set.Ioo (r0 - δ) (r0 + δ), ∀ θ, 0 < θ → θ < Real.pi →
          PXFieldEquationsAt κ Λ α Pstar q m ν r θ) ∧
        PXMarginPersists Pstar α q ν (CAS06Adopted.massLapse m Λ) ε r0
          (Set.Ioo (r0 - δ) (r0 + δ))

-- Capstone (contract family: fixed κ Λ α Pstar q ε0 μ and fixed relation; vary r0 only)
theorem G06B_family_capstone {κ Λ α Pstar q ε0 μ : ℝ} (hp : G06ATOV.AdmissibleParams κ α)
    (hP : 0 < Pstar) (hq : 0 < q)
    (hN : Pstar * (q ^ 2 / 2) ^ CAS06Scalar.exponent α = α * ε0) :
    ∀ r0 : ℝ, 0 < r0 → 0 < 1 - (2 * μ + Λ / 3) * r0 ^ 2 →
      ∃ δ > 0, ∃ m ν ε : ℝ → ℝ, m r0 = μ * r0 ^ 3 ∧ ν r0 = 0 ∧ ε r0 = ε0 ∧
        G06ATOV.IsTOVSolutionOn κ Λ α m ν ε (Set.Ioo (r0 - δ) (r0 + δ)) ∧
        PXRegularOn Pstar α q ν (Set.Ioo (r0 - δ) (r0 + δ)) ∧
        PXFluidOn Pstar α q ν ε r0 (Set.Ioo (r0 - δ) (r0 + δ)) ∧
        (∀ r ∈ Set.Ioo (r0 - δ) (r0 + δ), ∀ θ, 0 < θ → θ < Real.pi →
          PXFieldEquationsAt κ Λ α Pstar q m ν r θ) ∧
        PXMarginPersists Pstar α q ν (CAS06Adopted.massLapse m Λ) ε r0
          (Set.Ioo (r0 - δ) (r0 + δ))

-- Negative controls / boundary branches / non-vacuity
theorem N1_unmatched_breaks_einstein_matter {κ Λ α Pstar q : ℝ}
    (hp : G06ATOV.AdmissibleParams κ α) {m ν ε : ℝ → ℝ} {I : Set ℝ} (hI : IsOpen I)
    (hsol : G06ATOV.IsTOVSolutionOn κ Λ α m ν ε I) {r θ : ℝ} (hr : r ∈ I)
    (hθ0 : 0 < θ) (hθπ : θ < Real.pi)
    (hmis : ¬ PXMatched Pstar α q (ν r) (ε r)) :
    ¬ PXEinsteinMatter Pstar (CAS06Scalar.exponent α) q κ Λ ν m r θ
theorem N2_zero_gradient_unmatched {Pstar α ν0 ε0 : ℝ} (hα : 0 < α) (hε0 : 0 < ε0) :
    ¬ PXMatched Pstar α 0 ν0 ε0
theorem N3_contract_density_rigidity {Pstar α q ε0 ε0' : ℝ} (hα : 0 < α)
    (h1 : PXMatched Pstar α q 0 ε0) (h2 : PXMatched Pstar α q 0 ε0') : ε0 = ε0'
theorem N3_matched_gauge_exists {Pstar α q ε0 : ℝ} (hP : 0 < Pstar) (hα : 0 < α)
    (hq : q ≠ 0) (hε0 : 0 < ε0) : ∃ ν0 : ℝ, PXMatched Pstar α q ν0 ε0
theorem W_family_nonvacuous :
    ∃ κ Λ α Pstar q ε0 μ r0 : ℝ, G06ATOV.AdmissibleParams κ α ∧ 0 < Pstar ∧ 0 < q ∧
      Pstar * (q ^ 2 / 2) ^ CAS06Scalar.exponent α = α * ε0 ∧ 0 < ε0 ∧
      0 < r0 ∧ 0 < 1 - (2 * μ + Λ / 3) * r0 ^ 2 ∧
      ∃ δ > 0, ∃ m ν ε : ℝ → ℝ, m r0 = μ * r0 ^ 3 ∧ ν r0 = 0 ∧ ε r0 = ε0 ∧
        ∀ r ∈ Set.Ioo (r0 - δ) (r0 + δ), ∀ θ, 0 < θ → θ < Real.pi →
          PXFieldEquationsAt κ Λ α Pstar q m ν r θ
```

Assumption notes.  The contract's `C>0` and `B≠0` are used only by C02/C04
(acceleration divergence); they are not needed here and are not assumed (the
family theorem holds for every `r0>0` with `F0>0`).  `c` does not enter.  `κ>0`
and `0<α<1` enter via `AdmissibleParams`.  No hypothesis states a field equation,
the fluid identification, a DEC inequality, or the interval-wide matching; the only
member-side condition is the single-event compatibility `PXMatched` (discharged by
the fixed relation in the contract family).

Not claimed: C^∞ regularity of the solution functions (only the `P(X)` map is C^n/ω
at `X>0`; the solution is differentiable as in G06-A); global/regular-centre stars;
maximal interval; hyperbolicity/UV/global stability (`c_s^2=α` is the finite
derivative ratio only); unique timelike energy frame and normal-coordinate 2-jet
statements (separate obligations); historical four-axis acceptance; scientific
admission.
