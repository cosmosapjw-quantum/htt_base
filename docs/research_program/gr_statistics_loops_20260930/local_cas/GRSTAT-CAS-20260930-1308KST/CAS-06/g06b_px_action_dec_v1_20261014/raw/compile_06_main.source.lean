import G06ATOV

/-!
# G06-B: the fixed `P(X)` action on the constructed TOV germs; strict DEC persistence

Recovered source (see `SOURCE_RECOVERY.md`): EF5c / CAS-06 C03 and the C04 family
candidate.  One fixed theory `Pstar > 0`, `q > 0`, `0 < α < 1`,
`s = (1+α)/(2α)`, `P(X) = Pstar X^s`, `X = -g^{ab}ψ_a ψ_b / 2`, `ψ = q x0`,
with `Pstar (q²/2)^s = p0 = α ε0` fixed; the family varies only the member data.

All constants of the theory are bound before the member quantifier in the
capstones.  The constructed metric/scalar pair is the actual G06-A solution
`(m, ν, ε)` (reused unchanged, module `G06ATOV`) together with `ψ = q x0`.
Real powers are only manipulated at `X > 0`.
-/

namespace G06BPX
noncomputable section
open Filter Topology Set

/-! ## Definitions (frozen in `FROZEN_TARGETS.md`) -/

/-- member-side compatibility with the fixed theory: `P(X(r0)) = α ε0`,
    `X(r0) = (q²/2) e^{-2ν0}` -/
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

/-- Einstein–matter equations `G + Λ g = κ T^{P(X)}` (all 16 frame components) -/
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

/-- scalar Euler–Lagrange equation `∂_a(√-g J^a) = 0` with honest (`HasDerivAt`) line
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

/-- frame energy flux `j^a = -T^a_b k^b` (index raised with `η`) -/
def decFlux (T : Fin 4 → Fin 4 → ℝ) (k : Fin 4 → ℝ) (a : Fin 4) : ℝ :=
  -(minkowski a a * ∑ b : Fin 4, T a b * k b)

def StrictDEC (T : Fin 4 → Fin 4 → ℝ) : Prop :=
  ∀ k : Fin 4 → ℝ, FutureCausal k → FutureTimelike (decFlux T k)

/-- strict DEC of the `P(X)` stress at the actual point: type-I margin and flux form -/
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

/-- `X > 0` regularity of `Pstar X^s` along the actual field, `P_X > 0`, sound-speed ratio `α` -/
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

/-- the `P(X)` fluid IS the TOV fluid on the interval, and `ε e^{2sν}` is constant -/
def PXFluidOn (Pstar α q : ℝ) (ν ε : ℝ → ℝ) (r0 : ℝ) (I : Set ℝ) : Prop :=
  ∀ r ∈ I,
    CAS06Action.actionRadialEnergy Pstar (CAS06Scalar.exponent α) ν q r = ε r ∧
    CAS06Action.actionRadialPressure Pstar (CAS06Scalar.exponent α) ν q r = α * ε r ∧
    ε r * Real.exp (2 * CAS06Scalar.exponent α * ν r) =
      ε r0 * Real.exp (2 * CAS06Scalar.exponent α * ν r0)

/-- uniform strict-DEC margin and `X`/`F` positivity on a neighbourhood of the event -/
def PXMarginPersists (Pstar α q : ℝ) (ν F ε : ℝ → ℝ) (r0 : ℝ) (I : Set ℝ) : Prop :=
  ∃ η > 0, ∀ r ∈ Set.Ioo (r0 - η) (r0 + η), r ∈ I ∧
    (1 - α) * ε r0 / 2 <
      CAS06Action.actionRadialEnergy Pstar (CAS06Scalar.exponent α) ν q r -
        |CAS06Action.actionRadialPressure Pstar (CAS06Scalar.exponent α) ν q r| ∧
    CAS06Action.actionRadialX ν q r0 / 2 < CAS06Action.actionRadialX ν q r ∧
    F r0 / 2 < F r

/-! ## Small algebraic helpers -/

theorem fin4_cases (a : Fin 4) : a = 0 ∨ a = 1 ∨ a = 2 ∨ a = 3 := by
  fin_cases a <;> simp

theorem frameScale_sq_0 (ν F r θ : ℝ) :
    CAS06Adopted.chartFrameScale ν F r θ 0 * CAS06Adopted.chartFrameScale ν F r θ 0 =
      (Real.exp (2 * ν))⁻¹ := by
  simp only [CAS06Adopted.chartFrameScale, if_pos rfl]
  rw [← Real.exp_add, ← Real.exp_neg]
  ring_nf

theorem frameScale_sq_1 (ν F r θ : ℝ) (hF : 0 ≤ F) :
    CAS06Adopted.chartFrameScale ν F r θ 1 * CAS06Adopted.chartFrameScale ν F r θ 1 = F := by
  simp only [CAS06Adopted.chartFrameScale, if_pos rfl,
    if_neg (show (1 : Fin 4) ≠ 0 by decide)]
  exact Real.mul_self_sqrt hF

theorem frameScale_sq_2 (ν F r θ : ℝ) :
    CAS06Adopted.chartFrameScale ν F r θ 2 * CAS06Adopted.chartFrameScale ν F r θ 2 =
      (r ^ 2)⁻¹ := by
  simp only [CAS06Adopted.chartFrameScale, if_pos rfl,
    if_neg (show (2 : Fin 4) ≠ 0 by decide), if_neg (show (2 : Fin 4) ≠ 1 by decide)]
  ring

theorem frameScale_sq_3 (ν F r θ : ℝ) :
    CAS06Adopted.chartFrameScale ν F r θ 3 * CAS06Adopted.chartFrameScale ν F r θ 3 =
      (r ^ 2 * Real.sin θ ^ 2)⁻¹ := by
  simp only [CAS06Adopted.chartFrameScale,
    if_neg (show (3 : Fin 4) ≠ 0 by decide), if_neg (show (3 : Fin 4) ≠ 1 by decide),
    if_neg (show (3 : Fin 4) ≠ 2 by decide)]
  ring

/-! ## T1: `X > 0` regularity of `Pstar X^s` -/

theorem T1_pressure_contDiffAt (Pstar s : ℝ) {x : ℝ} (hx : 0 < x) (n : WithTop ℕ∞) :
    ContDiffAt ℝ n (CAS06Scalar.pressure Pstar s) x := by
  have h : ContDiffAt ℝ n (fun y : ℝ => y ^ s) x :=
    Real.contDiffAt_rpow_const_of_ne hx.ne'
  show ContDiffAt ℝ n (fun y : ℝ => Pstar * y ^ s) x
  exact contDiffAt_const.mul h

theorem T1_first_pos {Pstar α x : ℝ} (hP : 0 < Pstar) (hα : 0 < α) (hx : 0 < x) :
    0 < CAS06Scalar.first Pstar (CAS06Scalar.exponent α) x := by
  unfold CAS06Scalar.first
  exact mul_pos (mul_pos hP (CAS06Scalar.exponent_pos α hα)) (Real.rpow_pos_of_pos hx _)

theorem T1_regular_on {κ Λ α Pstar q : ℝ} (hp : G06ATOV.AdmissibleParams κ α)
    (hP : 0 < Pstar) (hq : q ≠ 0) {m ν ε : ℝ → ℝ} {I : Set ℝ}
    (hsol : G06ATOV.IsTOVSolutionOn κ Λ α m ν ε I) :
    PXRegularOn Pstar α q ν I := by
  intro r hr
  have hν := (hsol r hr).2.2.1
  have hX : 0 < CAS06Action.actionRadialX ν q r := CAS06Action.actionRadialX_pos ν q r hq
  have hsound := CAS06Action.action_sound_ratio Pstar α (CAS06Action.actionRadialX ν q r)
    hP hX hp.alpha_pos hp.alpha_lt_one
  exact ⟨hX, fun n => T1_pressure_contDiffAt _ _ hX n,
    CAS06Action.actionRadialPressure_hasDerivAt Pstar (CAS06Scalar.exponent α) q r ν hq
      hν.differentiableAt,
    T1_first_pos hP hp.alpha_pos hX, hsound.1, hsound.2⟩

/-! ## T2: stress/current identities at the actual metric/scalar pair -/

theorem T2_stress_current_at {Pstar s q : ℝ} {ν F : ℝ → ℝ} {r θ : ℝ}
    (hq : q ≠ 0) (hr : 0 < r) (hF : 0 < F r) (hθ0 : 0 < θ) (hθπ : θ < Real.pi) :
    PXStressCurrentAt Pstar s q ν F r θ := by
  have hs : Real.sin θ ≠ 0 := (Real.sin_pos_of_pos_of_lt_pi hθ0 hθπ).ne'
  have hX : 0 < CAS06Action.kinetic (CAS06Action.chartContravariant (ν r) (F r) r θ)
      (CAS06Action.scalarGradient q) := by
    rw [← CAS06Action.actionRadialX_eq_chart ν F q r θ]
    exact CAS06Action.actionRadialX_pos ν q r hq
  have hGg := CAS06Action.chartInverse_matrix_mul (ν r) (F r) r θ hF.ne' hr.ne' hs
  have hD := CAS06Action.chartContravariant_det_neg (ν r) (F r) r θ hF hr.ne' hs
  refine ⟨?_, ?_⟩
  · intro H hH
    exact CAS06Action.actionDensity_metric_stress_variation Pstar s _ _ H _ hGg hD hX hH
  · intro η
    exact CAS06Action.actionDensity_scalar_hasDerivAt Pstar s _ _ η hX
      (CAS06Action.chartContravariant_symmetric (ν r) (F r) r θ)

theorem T2_frame_stress (Pstar s q : ℝ) (ν F : ℝ → ℝ) (r θ : ℝ)
    (hF : 0 < F r) (hr : 0 < r) (hs : Real.sin θ ≠ 0) :
    ∀ a b : Fin 4, pxFrameStress Pstar s q ν F r θ a b =
      if a = b then
        (if a = 0 then CAS06Action.actionRadialEnergy Pstar s ν q r
         else CAS06Action.actionRadialPressure Pstar s ν q r)
      else 0 := by
  have hK : CAS06Action.kinetic (CAS06Action.chartContravariant (ν r) (F r) r θ)
      (CAS06Action.scalarGradient q) = CAS06Action.actionRadialX ν q r :=
    (CAS06Action.actionRadialX_eq_chart ν F q r θ).symm
  have hXv : CAS06Action.actionRadialX ν q r = q ^ 2 / 2 * Real.exp (-2 * ν r) := rfl
  have he : Real.exp (-ν r) * Real.exp (-ν r) = Real.exp (-2 * ν r) := by
    rw [← Real.exp_add]; ring_nf
  have he2 : Real.exp (-2 * ν r) * Real.exp (2 * ν r) = 1 := by
    rw [← Real.exp_add]; simp
  have hsqF : Real.sqrt (F r) * Real.sqrt (F r) = F r := Real.mul_self_sqrt hF.le
  intro a b
  unfold pxFrameStress CAS06Action.actionStress CAS06Action.actionRadialEnergy
    CAS06Action.actionRadialPressure CAS06Action.actionEnergy
  rw [hK]
  generalize hP1 : CAS06Action.actionFirst Pstar s (CAS06Action.actionRadialX ν q r) = P1
  generalize hP0 : CAS06Action.actionPressure Pstar s (CAS06Action.actionRadialX ν q r) = P0
  rw [hXv]
  rcases fin4_cases a with ha | ha | ha | ha <;> rcases fin4_cases b with hb | hb | hb | hb <;>
    subst ha hb <;>
    simp [CAS06Adopted.chartFrameScale, CAS06Action.scalarGradient,
      CAS06Action.chartCovariant, CAS06Adopted.chartMetric]
  · linear_combination (P1 * q ^ 2 - P0 * Real.exp (2 * ν r)) * he - P0 * he2
  · rw [← mul_assoc, hsqF]; field_simp
  · field_simp
  · field_simp

theorem T2_frame_stress_bridge (Pstar s q : ℝ) (ν F : ℝ → ℝ) (r θ : ℝ) (hν : ν r = 0) :
    ∀ a b : Fin 4, pxFrameStress Pstar s q ν F r θ a b =
      CAS06Action.chartActionStressHat Pstar s q (F r) r θ a b := by
  intro a b
  unfold pxFrameStress CAS06Action.chartActionStressHat
  rw [hν]

/-! ## T3: the `P(X)` fluid is the TOV fluid on the whole interval -/

theorem T3_integrating_factor {α : ℝ} (hα : α ≠ 0) {f ν N : ℝ → ℝ} {I : Set ℝ}
    (hI : IsOpen I) (hIc : IsPreconnected I)
    (hf : ∀ r ∈ I, HasDerivAt f (-(1 + α) * f r * N r / α) r)
    (hν : ∀ r ∈ I, HasDerivAt ν (N r) r) {x y : ℝ} (hx : x ∈ I) (hy : y ∈ I) :
    f x * Real.exp ((1 + α) / α * ν x) = f y * Real.exp ((1 + α) / α * ν y) := by
  have hder : ∀ r ∈ I, HasDerivAt (fun z => f z * Real.exp ((1 + α) / α * ν z)) 0 r := by
    intro r hr
    have h1 := (hf r hr).mul (((hν r hr).const_mul ((1 + α) / α)).exp)
    convert h1 using 1
    ring
  have hdiff : DifferentiableOn ℝ (fun z => f z * Real.exp ((1 + α) / α * ν z)) I :=
    fun r hr => (hder r hr).differentiableAt.differentiableWithinAt
  have hzero : Set.EqOn (deriv (fun z => f z * Real.exp ((1 + α) / α * ν z))) 0 I :=
    fun r hr => (hder r hr).deriv
  exact hI.is_const_of_deriv_eq_zero hIc hdiff hzero hx hy

theorem px_energy_hasDerivAt {Pstar α q : ℝ} (hα : 0 < α) (hq : q ≠ 0) {ν : ℝ → ℝ}
    {r N : ℝ} (hν : HasDerivAt ν N r) :
    HasDerivAt (CAS06Action.actionRadialEnergy Pstar (CAS06Scalar.exponent α) ν q)
      (-(1 + α) * CAS06Action.actionRadialEnergy Pstar (CAS06Scalar.exponent α) ν q r *
        N / α) r := by
  have hfun : CAS06Action.actionRadialEnergy Pstar (CAS06Scalar.exponent α) ν q =
      fun y => α⁻¹ * CAS06Action.actionRadialPressure Pstar (CAS06Scalar.exponent α) ν q y := by
    funext y
    have h := CAS06Action.action_barotropic_identity Pstar α (CAS06Action.actionRadialX ν q y)
      (CAS06Action.actionRadialX_pos ν q y hq) hα
    unfold CAS06Action.actionRadialPressure CAS06Action.actionRadialEnergy
    rw [h, ← mul_assoc, inv_mul_cancel₀ hα.ne', one_mul]
  have hP := CAS06Action.actionRadialPressure_hasDerivAt Pstar (CAS06Scalar.exponent α) q r ν
    hq hν.differentiableAt
  have hPval : CAS06Action.actionRadialPressure Pstar (CAS06Scalar.exponent α) ν q r =
      α * CAS06Action.actionRadialEnergy Pstar (CAS06Scalar.exponent α) ν q r :=
    CAS06Action.action_barotropic_identity Pstar α _ (CAS06Action.actionRadialX_pos ν q r hq) hα
  rw [hPval, hν.deriv] at hP
  have h2 := (hP.const_mul α⁻¹).congr_of_eventuallyEq (Filter.EventuallyEq.of_eq hfun)
  convert h2 using 1
  ring

theorem T3_fluid_identification {κ Λ α Pstar q : ℝ} (hp : G06ATOV.AdmissibleParams κ α)
    (hq : q ≠ 0) {m ν ε : ℝ → ℝ} {I : Set ℝ} (hI : IsOpen I) (hIc : IsPreconnected I)
    (hsol : G06ATOV.IsTOVSolutionOn κ Λ α m ν ε I) {r0 : ℝ} (hr0 : r0 ∈ I)
    (hmatch : PXMatched Pstar α q (ν r0) (ε r0)) :
    PXFluidOn Pstar α q ν ε r0 I := by
  have hα := hp.alpha_pos
  have hνd : ∀ r ∈ I, HasDerivAt ν
      ((fun z => CAS06Adopted.tovNuFunction m (fun s => α * ε s)
        (CAS06Adopted.massLapse m Λ) κ Λ z) r) r := fun r hr => (hsol r hr).2.2.1
  have hεd : ∀ r ∈ I, HasDerivAt ε
      (-(1 + α) * ε r * (fun z => CAS06Adopted.tovNuFunction m (fun s => α * ε s)
        (CAS06Adopted.massLapse m Λ) κ Λ z) r / α) r := fun r hr => (hsol r hr).2.2.2
  have hEd : ∀ r ∈ I, HasDerivAt
      (CAS06Action.actionRadialEnergy Pstar (CAS06Scalar.exponent α) ν q)
      (-(1 + α) * CAS06Action.actionRadialEnergy Pstar (CAS06Scalar.exponent α) ν q r *
        (fun z => CAS06Adopted.tovNuFunction m (fun s => α * ε s)
          (CAS06Adopted.massLapse m Λ) κ Λ z) r / α) r :=
    fun r hr => px_energy_hasDerivAt hα hq (hνd r hr)
  have hk : 2 * CAS06Scalar.exponent α = (1 + α) / α := by
    unfold CAS06Scalar.exponent; field_simp
  have hE0 : CAS06Action.actionRadialEnergy Pstar (CAS06Scalar.exponent α) ν q r0 = ε r0 := by
    have hbar := CAS06Action.action_barotropic_identity Pstar α
      (CAS06Action.actionRadialX ν q r0) (CAS06Action.actionRadialX_pos ν q r0 hq) hα
    have h : α * CAS06Action.actionRadialEnergy Pstar (CAS06Scalar.exponent α) ν q r0 =
        α * ε r0 := by
      unfold CAS06Action.actionRadialEnergy
      rw [← hbar]
      exact hmatch
    exact mul_left_cancel₀ hα.ne' h
  intro r hr
  have h1 := T3_integrating_factor hα.ne' hI hIc hEd hνd hr hr0
  have h2 := T3_integrating_factor hα.ne' hI hIc hεd hνd hr hr0
  have hexp : 0 < Real.exp ((1 + α) / α * ν r) := Real.exp_pos _
  have hEr : CAS06Action.actionRadialEnergy Pstar (CAS06Scalar.exponent α) ν q r = ε r := by
    have h3 : CAS06Action.actionRadialEnergy Pstar (CAS06Scalar.exponent α) ν q r *
        Real.exp ((1 + α) / α * ν r) = ε r * Real.exp ((1 + α) / α * ν r) := by
      rw [h1, h2, hE0]
    exact mul_right_cancel₀ hexp.ne' h3
  refine ⟨hEr, ?_, ?_⟩
  · rw [← hEr]
    exact CAS06Action.action_barotropic_identity Pstar α _
      (CAS06Action.actionRadialX_pos ν q r hq) hα
  · rw [hk]
    exact h2

theorem T3_matched_closed_form {Pstar α q ν0 ε0 : ℝ} (hα : 0 < α) (hq : q ≠ 0) :
    PXMatched Pstar α q ν0 ε0 ↔
      ε0 = Pstar * (q ^ 2 / 2) ^ CAS06Scalar.exponent α / α *
        Real.exp (-2 * CAS06Scalar.exponent α * ν0) := by
  have hq2 : 0 ≤ q ^ 2 / 2 := by positivity
  have hpow : ((q ^ 2 / 2) * Real.exp (-2 * ν0)) ^ CAS06Scalar.exponent α =
      (q ^ 2 / 2) ^ CAS06Scalar.exponent α *
        Real.exp (-2 * CAS06Scalar.exponent α * ν0) := by
    rw [Real.mul_rpow hq2 (Real.exp_pos _).le, ← Real.exp_mul,
      show -2 * ν0 * CAS06Scalar.exponent α = -2 * CAS06Scalar.exponent α * ν0 by ring]
  unfold PXMatched
  rw [hpow, div_mul_eq_mul_div, eq_div_iff hα.ne']
  constructor <;> intro h <;> linear_combination -h

/-! ## T4: same-pair field equations -/

theorem T4_einstein_matter {κ Λ α Pstar q : ℝ} (hp : G06ATOV.AdmissibleParams κ α)
    {m ν ε : ℝ → ℝ} {I : Set ℝ} (hI : IsOpen I)
    (hsol : G06ATOV.IsTOVSolutionOn κ Λ α m ν ε I) {r θ : ℝ} (hr : r ∈ I)
    (hθ0 : 0 < θ) (hθπ : θ < Real.pi)
    (hE : CAS06Action.actionRadialEnergy Pstar (CAS06Scalar.exponent α) ν q r = ε r)
    (hPr : CAS06Action.actionRadialPressure Pstar (CAS06Scalar.exponent α) ν q r = α * ε r) :
    PXEinsteinMatter Pstar (CAS06Scalar.exponent α) q κ Λ ν m r θ := by
  have hEin := G06ATOV.T5_einstein_on_solution hp hI hsol hr hθ0 hθπ
  obtain ⟨hdom, -, -, -⟩ := hsol r hr
  have hs : Real.sin θ ≠ 0 := (Real.sin_pos_of_pos_of_lt_pi hθ0 hθπ).ne'
  have hT := T2_frame_stress Pstar (CAS06Scalar.exponent α) q ν (CAS06Adopted.massLapse m Λ)
    r θ hdom.2.1 hdom.1 hs
  simp only [CAS06Bundles.C01TOVEinstein] at hEin
  obtain ⟨h00, h11, h22, h33, hoff⟩ := hEin
  intro a b
  rw [hT a b]
  by_cases hab : a = b
  · subst hab
    rcases fin4_cases a with ha | ha | ha | ha <;> subst ha
    · rw [if_pos rfl, if_pos rfl]
      unfold frameEinstein minkowski
      rw [frameScale_sq_0, if_pos rfl, if_pos rfl]
      linear_combination h00 - κ * hE
    · rw [if_pos rfl, if_neg (by decide)]
      unfold frameEinstein minkowski
      rw [frameScale_sq_1 _ _ _ _ hdom.2.1.le, if_pos rfl, if_neg (by decide)]
      linear_combination h11 - κ * hPr
    · rw [if_pos rfl, if_neg (by decide)]
      unfold frameEinstein minkowski
      rw [frameScale_sq_2, if_pos rfl, if_neg (by decide)]
      linear_combination h22 - κ * hPr
    · rw [if_pos rfl, if_neg (by decide)]
      unfold frameEinstein minkowski
      rw [frameScale_sq_3, if_pos rfl, if_neg (by decide)]
      linear_combination h33 - κ * hPr
  · rw [if_neg hab]
    unfold frameEinstein minkowski
    rw [hoff a b hab, if_neg hab]
    ring

theorem T4_scalar_equation {Pstar s q : ℝ} {ν F : ℝ → ℝ} {r θ : ℝ}
    (hP : 0 < Pstar) (hs : 0 < s) (hq : q ≠ 0) :
    PXScalarEquationAt Pstar s q ν F r θ := by
  refine ⟨?_, CAS06Action.chart_scalar_current_divergence_zero Pstar s q ν F r θ, ?_⟩
  · intro dir x
    by_cases h0 : dir = 0
    · subst dir
      have hc : CAS06Action.chartCurrentDensityOnLine Pstar s q ν F r θ 0 =
          fun _ : ℝ => CAS06Action.chartCurrentDensityOnLine Pstar s q ν F r θ 0 0 := by
        funext y
        simp [CAS06Action.chartCurrentDensityOnLine]
      rw [hc]
      exact hasDerivAt_const _ _
    · have hz : CAS06Action.chartCurrentDensityOnLine Pstar s q ν F r θ dir =
          fun _ : ℝ => 0 := by
        funext y
        simp [CAS06Action.chartCurrentDensityOnLine,
          CAS06Action.chart_scalar_current_spatial_zero Pstar s (ν _) (F _) _ _ q dir h0]
      rw [hz]
      exact hasDerivAt_const _ _
  · have hX : 0 < CAS06Action.kinetic (CAS06Action.chartContravariant (ν r) (F r) r θ)
        (CAS06Action.scalarGradient q) := by
      rw [CAS06Action.chart_scalar_kinetic]
      have hq2 : 0 < q ^ 2 := sq_pos_of_ne_zero hq
      positivity
    have hfirst : 0 < CAS06Action.actionFirst Pstar s
        (CAS06Action.kinetic (CAS06Action.chartContravariant (ν r) (F r) r θ)
          (CAS06Action.scalarGradient q)) :=
      mul_pos (mul_pos hP hs) (Real.rpow_pos_of_pos hX _)
    have hsum : ∑ b : Fin 4, CAS06Action.chartContravariant (ν r) (F r) r θ 0 b *
        CAS06Action.scalarGradient q b = -(Real.exp (2 * ν r))⁻¹ * q := by
      simp [Fin.sum_univ_four, CAS06Action.chartContravariant, CAS06Adopted.chartInverse,
        CAS06Action.scalarGradient]
    unfold CAS06Action.actionCurrent
    rw [hsum]
    exact mul_ne_zero hfirst.ne'
      (mul_ne_zero (neg_ne_zero.mpr (inv_ne_zero (Real.exp_pos _).ne')) hq)

/-! ## T5: strict DEC, pointwise and persisting -/

theorem T5_strictDEC_diag {E P : ℝ} (hE : 0 < E) (hP : |P| < E)
    (T : Fin 4 → Fin 4 → ℝ)
    (hT : ∀ a b : Fin 4, T a b = if a = b then (if a = 0 then E else P) else 0) :
    StrictDEC T := by
  intro k hk
  obtain ⟨hk0, hks⟩ := hk
  have hj0 : decFlux T k 0 = E * k 0 := by
    simp [decFlux, minkowski, hT, Fin.sum_univ_four]
  have hj1 : decFlux T k 1 = -(P * k 1) := by
    simp [decFlux, minkowski, hT, Fin.sum_univ_four]
  have hj2 : decFlux T k 2 = -(P * k 2) := by
    simp [decFlux, minkowski, hT, Fin.sum_univ_four]
  have hj3 : decFlux T k 3 = -(P * k 3) := by
    simp [decFlux, minkowski, hT, Fin.sum_univ_four]
  have hPE := abs_lt.mp hP
  have hP2 : P ^ 2 < E ^ 2 := sq_lt_sq' hPE.1 hPE.2
  have f1 : P ^ 2 * (k 1 ^ 2 + k 2 ^ 2 + k 3 ^ 2) ≤ P ^ 2 * k 0 ^ 2 :=
    mul_le_mul_of_nonneg_left hks (sq_nonneg P)
  have f2 : P ^ 2 * k 0 ^ 2 < E ^ 2 * k 0 ^ 2 :=
    mul_lt_mul_of_pos_right hP2 (pow_pos hk0 2)
  unfold FutureTimelike
  rw [hj0, hj1, hj2, hj3]
  exact ⟨mul_pos hE hk0, by nlinarith [f1, f2]⟩

theorem T5_strictDEC_at {κ Λ α Pstar q : ℝ} (hp : G06ATOV.AdmissibleParams κ α)
    {m ν ε : ℝ → ℝ} {I : Set ℝ} (hsol : G06ATOV.IsTOVSolutionOn κ Λ α m ν ε I)
    {r0 : ℝ} (hfluid : PXFluidOn Pstar α q ν ε r0 I) {r θ : ℝ} (hr : r ∈ I)
    (hθ0 : 0 < θ) (hθπ : θ < Real.pi) :
    PXStrictDECAt Pstar α q ν (CAS06Adopted.massLapse m Λ) r θ := by
  obtain ⟨hdom, -, -, -⟩ := hsol r hr
  obtain ⟨hE, hPr, -⟩ := hfluid r hr
  have hε : 0 < ε r := hdom.2.2
  have hα := hp.alpha_pos
  have hα1 := hp.alpha_lt_one
  have hEpos : 0 < CAS06Action.actionRadialEnergy Pstar (CAS06Scalar.exponent α) ν q r := by
    rw [hE]; exact hε
  have habs : |CAS06Action.actionRadialPressure Pstar (CAS06Scalar.exponent α) ν q r| =
      α * ε r := by
    rw [hPr, abs_of_pos (mul_pos hα hε)]
  have hlt : |CAS06Action.actionRadialPressure Pstar (CAS06Scalar.exponent α) ν q r| <
      CAS06Action.actionRadialEnergy Pstar (CAS06Scalar.exponent α) ν q r := by
    rw [habs, hE]; exact mul_lt_of_lt_one_left hε hα1
  have hs : Real.sin θ ≠ 0 := (Real.sin_pos_of_pos_of_lt_pi hθ0 hθπ).ne'
  refine ⟨hEpos, hlt, ?_, ?_⟩
  · rw [habs, hE]; ring
  · exact T5_strictDEC_diag hEpos hlt _
      (T2_frame_stress Pstar _ q ν _ r θ hdom.2.1 hdom.1 hs)

theorem T5_margin_persists {κ Λ α Pstar q : ℝ} (hp : G06ATOV.AdmissibleParams κ α)
    (hq : q ≠ 0) {m ν ε : ℝ → ℝ} {I : Set ℝ} (hI : IsOpen I)
    (hsol : G06ATOV.IsTOVSolutionOn κ Λ α m ν ε I)
    {r0 : ℝ} (hfluid : PXFluidOn Pstar α q ν ε r0 I) (hr0 : r0 ∈ I) :
    PXMarginPersists Pstar α q ν (CAS06Adopted.massLapse m Λ) ε r0 I := by
  obtain ⟨hdom0, hm0, hν0, hε0d⟩ := hsol r0 hr0
  have hα := hp.alpha_pos
  have hα1 := hp.alpha_lt_one
  have hεc : ContinuousAt ε r0 := hε0d.continuousAt
  have hXc : ContinuousAt (CAS06Action.actionRadialX ν q) r0 :=
    (CAS06Action.actionRadialX_hasDerivAt ν q r0 hν0.differentiableAt).continuousAt
  have hFc : ContinuousAt (CAS06Adopted.massLapse m Λ) r0 :=
    (CAS06Adopted.massLapse_derivative (Λ := Λ) hdom0.1.ne' hm0).continuousAt
  have hX0 : 0 < CAS06Action.actionRadialX ν q r0 := CAS06Action.actionRadialX_pos ν q r0 hq
  have hε0 : 0 < ε r0 := hdom0.2.2
  have hF0 : 0 < CAS06Adopted.massLapse m Λ r0 := hdom0.2.1
  have ev1 : ∀ᶠ r in 𝓝 r0, ε r0 / 2 < ε r := hεc.eventually (lt_mem_nhds (by linarith))
  have ev2 : ∀ᶠ r in 𝓝 r0, CAS06Action.actionRadialX ν q r0 / 2 <
      CAS06Action.actionRadialX ν q r := hXc.eventually (lt_mem_nhds (by linarith))
  have ev3 : ∀ᶠ r in 𝓝 r0, CAS06Adopted.massLapse m Λ r0 / 2 <
      CAS06Adopted.massLapse m Λ r := hFc.eventually (lt_mem_nhds (by linarith))
  have ev4 : ∀ᶠ r in 𝓝 r0, r ∈ I := hI.mem_nhds hr0
  obtain ⟨η, hη, hball⟩ := Metric.eventually_nhds_iff_ball.1 (ev4.and (ev1.and (ev2.and ev3)))
  refine ⟨η, hη, fun r hr => ?_⟩
  rw [← Real.ball_eq_Ioo] at hr
  obtain ⟨hrI, h1, h2, h3⟩ := hball r hr
  obtain ⟨hE, hPr, -⟩ := hfluid r hrI
  have hεr : 0 < ε r := (hsol r hrI).1.2.2
  refine ⟨hrI, ?_, h2, h3⟩
  rw [hE, hPr, abs_of_pos (mul_pos hα hεr)]
  nlinarith [mul_pos (sub_pos.2 hα1) (sub_pos.2 h1)]

/-! ## Capstones -/

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
          (Set.Ioo (r0 - δ) (r0 + δ)) := by
  intro r0 m0 ν0 ε0 hdat hmatch
  obtain ⟨δ, hδ, m, ν, ε, hm0, hν0, hε0, hsol⟩ := G06ATOV.T3_local_existence hp hdat
  have hr0 : r0 ∈ Set.Ioo (r0 - δ) (r0 + δ) := ⟨by linarith, by linarith⟩
  have hq0 : q ≠ 0 := hq.ne'
  have hm' : PXMatched Pstar α q (ν r0) (ε r0) := by rw [hν0, hε0]; exact hmatch
  have hfluid := T3_fluid_identification hp hq0 isOpen_Ioo isPreconnected_Ioo hsol hr0 hm'
  refine ⟨δ, hδ, m, ν, ε, hm0, hν0, hε0, hsol, T1_regular_on hp hP hq0 hsol, hfluid, ?_,
    T5_margin_persists hp hq0 isOpen_Ioo hsol hfluid hr0⟩
  intro r hr θ hθ0 hθπ
  obtain ⟨hE, hPr, -⟩ := hfluid r hr
  have hdom := (hsol r hr).1
  exact ⟨T2_stress_current_at hq0 hdom.1 hdom.2.1 hθ0 hθπ,
    T4_einstein_matter hp isOpen_Ioo hsol hr hθ0 hθπ hE hPr,
    T4_scalar_equation hP (CAS06Scalar.exponent_pos α hp.alpha_pos) hq0,
    T5_strictDEC_at hp hsol hfluid hr hθ0 hθπ⟩

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
          (Set.Ioo (r0 - δ) (r0 + δ)) := by
  intro r0 hr0 hF0
  have hα := hp.alpha_pos
  have hε0 : 0 < ε0 := by
    have hq2 : 0 < q ^ 2 / 2 := by positivity
    have h := mul_pos hP (Real.rpow_pos_of_pos hq2 (CAS06Scalar.exponent α))
    rw [hN] at h
    nlinarith
  have hdat : G06ATOV.TOVDomain Λ (r0, μ * r0 ^ 3, 0, ε0) := by
    refine ⟨hr0, ?_, hε0⟩
    show 0 < 1 - 2 * (μ * r0 ^ 3) / r0 - Λ * r0 ^ 2 / 3
    have hrw : 1 - 2 * (μ * r0 ^ 3) / r0 - Λ * r0 ^ 2 / 3 =
        1 - (2 * μ + Λ / 3) * r0 ^ 2 := by
      field_simp
      ring
    rw [hrw]
    exact hF0
  have hmatch : PXMatched Pstar α q 0 ε0 := by
    unfold PXMatched
    rw [mul_zero, Real.exp_zero, mul_one]
    exact hN
  exact G06B_germ_capstone hp hP hq r0 (μ * r0 ^ 3) 0 ε0 hdat hmatch

/-! ## Negative controls, boundary branches, non-vacuity -/

theorem N1_unmatched_breaks_einstein_matter {κ Λ α Pstar q : ℝ}
    (hp : G06ATOV.AdmissibleParams κ α) {m ν ε : ℝ → ℝ} {I : Set ℝ} (hI : IsOpen I)
    (hsol : G06ATOV.IsTOVSolutionOn κ Λ α m ν ε I) {r θ : ℝ} (hr : r ∈ I)
    (hθ0 : 0 < θ) (hθπ : θ < Real.pi)
    (hmis : ¬ PXMatched Pstar α q (ν r) (ε r)) :
    ¬ PXEinsteinMatter Pstar (CAS06Scalar.exponent α) q κ Λ ν m r θ := by
  intro hEM
  have hEin := G06ATOV.T5_einstein_on_solution hp hI hsol hr hθ0 hθπ
  simp only [CAS06Bundles.C01TOVEinstein] at hEin
  obtain ⟨h00, -, -, -, -⟩ := hEin
  obtain ⟨hdom, -, -, -⟩ := hsol r hr
  have hs : Real.sin θ ≠ 0 := (Real.sin_pos_of_pos_of_lt_pi hθ0 hθπ).ne'
  have hT := T2_frame_stress Pstar (CAS06Scalar.exponent α) q ν (CAS06Adopted.massLapse m Λ)
    r θ hdom.2.1 hdom.1 hs
  have h0 := hEM 0 0
  rw [hT 0 0, if_pos rfl, if_pos rfl] at h0
  unfold frameEinstein minkowski at h0
  rw [frameScale_sq_0, if_pos rfl, if_pos rfl] at h0
  have hκ := hp.kappa_pos
  have hα := hp.alpha_pos
  have hEeq : CAS06Action.actionRadialEnergy Pstar (CAS06Scalar.exponent α) ν q r = ε r := by
    have h : κ * CAS06Action.actionRadialEnergy Pstar (CAS06Scalar.exponent α) ν q r =
        κ * ε r := by
      linear_combination h00 - h0
    exact mul_left_cancel₀ hκ.ne' h
  apply hmis
  by_cases hq : q = 0
  · exfalso
    subst hq
    have hs0 : CAS06Scalar.exponent α ≠ 0 := (CAS06Scalar.exponent_pos α hα).ne'
    have hX : CAS06Action.actionRadialX ν 0 r = 0 := by
      unfold CAS06Action.actionRadialX; ring
    have hzero : CAS06Action.actionRadialEnergy Pstar (CAS06Scalar.exponent α) ν 0 r = 0 := by
      unfold CAS06Action.actionRadialEnergy CAS06Action.actionEnergy
        CAS06Action.actionPressure
      rw [hX, Real.zero_rpow hs0]
      ring
    have hε : 0 < ε r := hdom.2.2
    linarith
  · show CAS06Action.actionPressure Pstar (CAS06Scalar.exponent α)
        (CAS06Action.actionRadialX ν q r) = α * ε r
    rw [← hEeq]
    exact CAS06Action.action_barotropic_identity Pstar α _
      (CAS06Action.actionRadialX_pos ν q r hq) hα

theorem N2_zero_gradient_unmatched {Pstar α ν0 ε0 : ℝ} (hα : 0 < α) (hε0 : 0 < ε0) :
    ¬ PXMatched Pstar α 0 ν0 ε0 := by
  intro h
  unfold PXMatched at h
  have hs0 : CAS06Scalar.exponent α ≠ 0 := (CAS06Scalar.exponent_pos α hα).ne'
  rw [show (0 : ℝ) ^ 2 / 2 * Real.exp (-2 * ν0) = 0 by ring, Real.zero_rpow hs0,
    mul_zero] at h
  nlinarith [mul_pos hα hε0]

theorem N3_contract_density_rigidity {Pstar α q ε0 ε0' : ℝ} (hα : 0 < α)
    (h1 : PXMatched Pstar α q 0 ε0) (h2 : PXMatched Pstar α q 0 ε0') : ε0 = ε0' := by
  unfold PXMatched at h1 h2
  have h : α * ε0 = α * ε0' := h1.symm.trans h2
  exact mul_left_cancel₀ hα.ne' h

theorem N3_matched_gauge_exists {Pstar α q ε0 : ℝ} (hP : 0 < Pstar) (hα : 0 < α)
    (hq : q ≠ 0) (hε0 : 0 < ε0) : ∃ ν0 : ℝ, PXMatched Pstar α q ν0 ε0 := by
  set s := CAS06Scalar.exponent α with hsdef
  have hs : 0 < s := CAS06Scalar.exponent_pos α hα
  have hq2 : 0 < q ^ 2 / 2 := by have := sq_pos_of_ne_zero hq; positivity
  set A : ℝ := Pstar * (q ^ 2 / 2) ^ s / α with hA
  have hApos : 0 < A := div_pos (mul_pos hP (Real.rpow_pos_of_pos hq2 _)) hα
  refine ⟨-Real.log (ε0 / A) / (-2 * s), ?_⟩
  rw [T3_matched_closed_form hα hq]
  have hexp : Real.exp (-2 * s * (-Real.log (ε0 / A) / (-2 * s))) = ε0 / A := by
    rw [show -2 * s * (-Real.log (ε0 / A) / (-2 * s)) = Real.log (ε0 / A) by
      field_simp]
    exact Real.exp_log (div_pos hε0 hApos)
  rw [hexp]
  field_simp

theorem W_family_nonvacuous :
    ∃ κ Λ α Pstar q ε0 μ r0 : ℝ, G06ATOV.AdmissibleParams κ α ∧ 0 < Pstar ∧ 0 < q ∧
      Pstar * (q ^ 2 / 2) ^ CAS06Scalar.exponent α = α * ε0 ∧ 0 < ε0 ∧
      0 < r0 ∧ 0 < 1 - (2 * μ + Λ / 3) * r0 ^ 2 ∧
      ∃ δ > 0, ∃ m ν ε : ℝ → ℝ, m r0 = μ * r0 ^ 3 ∧ ν r0 = 0 ∧ ε r0 = ε0 ∧
        ∀ r ∈ Set.Ioo (r0 - δ) (r0 + δ), ∀ θ, 0 < θ → θ < Real.pi →
          PXFieldEquationsAt κ Λ α Pstar q m ν r θ := by
  have hp : G06ATOV.AdmissibleParams 1 (1 / 2) := ⟨by norm_num, by norm_num, by norm_num⟩
  have hpow : 0 < ((1 : ℝ) ^ 2 / 2) ^ CAS06Scalar.exponent (1 / 2) :=
    Real.rpow_pos_of_pos (by norm_num) _
  set ε0 : ℝ := 2 * ((1 : ℝ) ^ 2 / 2) ^ CAS06Scalar.exponent (1 / 2) with hε0def
  have hN : (1 : ℝ) * ((1 : ℝ) ^ 2 / 2) ^ CAS06Scalar.exponent (1 / 2) = 1 / 2 * ε0 := by
    rw [hε0def]; ring
  have hε0 : 0 < ε0 := by rw [hε0def]; positivity
  have hF : (0 : ℝ) < 1 - (2 * 0 + 0 / 3) * 1 ^ 2 := by norm_num
  obtain ⟨δ, hδ, m, ν, ε, hm0, hν0, hε0', -, -, -, hfield, -⟩ :=
    G06B_family_capstone (κ := 1) (Λ := 0) (μ := 0) hp one_pos one_pos hN 1 one_pos hF
  exact ⟨1, 0, 1 / 2, 1, 1, ε0, 0, 1, hp, one_pos, one_pos, hN, hε0, one_pos, hF,
    δ, hδ, m, ν, ε, hm0, hν0, hε0', hfield⟩

end
end G06BPX
