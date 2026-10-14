# G17-D frozen targets (written before any proof compile)

Module `G17DOrbitTilt` (namespace `G17D`), imports `C01` and `PassiveTensorBridge`
unchanged. All C01 symbols (`Vec`, `lorentz`, `gram`, `normal`, `FutureUnit`,
`gamma`, `betaSq`, `beta`, `relativeSpatial`) are used with their accepted
definitions; signature (-,+,+,+), orthonormal coordinates, single event.
`V : Type` is any real module (C04 universe convention).

## T1 equality branch (reverse Lorentz Cauchy-Schwarz equality case)

```lean
theorem null_orthogonal_future_eq_zero (r N : Vec) (hN : FutureUnit N)
    (hrN : lorentz r N = 0) (hrr : lorentz r r = 0) : r = ⟨0, 0, 0, 0⟩
theorem gamma_eq_one_iff (u N : Vec) (hu : FutureUnit u) (hN : FutureUnit N) :
    gamma u N = 1 ↔ u = N
theorem betaSq_eq_zero_iff (u N : Vec) (hu : FutureUnit u) (hN : FutureUnit N) :
    betaSq u N = 0 ↔ u = N
theorem beta_eq_zero_iff (u N : Vec) (hu : FutureUnit u) (hN : FutureUnit N) :
    beta u N = 0 ↔ u = N
theorem betaSq_pos_of_ne (u N : Vec) (hu : FutureUnit u) (hN : FutureUnit N)
    (h : u ≠ N) : 0 < betaSq u N
theorem orbit_tilt_zero_iff (a b c u : Vec) (hG : (gram a b c).PosDef)
    (hu : FutureUnit u) :
    (gamma u (normal a b c) = 1 ↔ u = normal a b c) ∧
    (betaSq u (normal a b c) = 0 ↔ u = normal a b c) ∧
    (beta u (normal a b c) = 0 ↔ u = normal a b c)
```
Quantifiers: universal over all four-coordinate real vectors; hypotheses are exactly
C01's (`PosDef` Gram, future unit `u`); N is the C01-constructed normal, not assumed.
Negative control (future branch is essential, not decorative):
```lean
theorem past_branch_counterexample :
    ∃ u N : Vec, FutureUnit N ∧ lorentz u u = -1 ∧ betaSq u N = 0 ∧ u ≠ N
```

## T2 typed geometric input (no orbit inference)

```lean
structure IndependentOrbitInput where
  X1 X2 X3 : Vec            -- independently supplied orbit generators at the event
  gram_posDef : (gram X1 X2 X3).PosDef
  u : Vec                   -- independently recovered source velocity
  u_future : FutureUnit u
def IndependentOrbitInput.N (I) : Vec := normal I.X1 I.X2 I.X3
theorem gram_posDef_spacelike (a b c : Vec) (hG : (gram a b c).PosDef) :
    0 < lorentz a a ∧ 0 < lorentz b b ∧ 0 < lorentz c c
theorem normal_swap12 (a b c : Vec) (hG : (gram a b c).PosDef) :
    normal b a c = normal a b c     -- future choice independent of epsilon orientation
theorem orbit_input_tilt (I : IndependentOrbitInput) :
    (0 < lorentz I.X1 I.X1 ∧ 0 < lorentz I.X2 I.X2 ∧ 0 < lorentz I.X3 I.X3) ∧
    FutureUnit I.N ∧
    lorentz I.N I.X1 = 0 ∧ lorentz I.N I.X2 = 0 ∧ lorentz I.N I.X3 = 0 ∧
    1 ≤ gamma I.u I.N ∧ betaSq I.u I.N = 1 - (gamma I.u I.N)⁻¹ ^ 2 ∧
    0 ≤ betaSq I.u I.N ∧ betaSq I.u I.N < 1 ∧
    (betaSq I.u I.N = 0 ↔ I.u = I.N)
```
Spacelikeness is derived from Gram positivity (not added as a hypothesis).
Non-vacuity / TILT-BOOST negative control:
```lean
theorem orbit_input_nonvacuous_equality :
    ∃ I : IndependentOrbitInput, I.u = I.N ∧ betaSq I.u I.N = 0
theorem tilt_boost_negative_control :
    ∃ I : IndependentOrbitInput, ∃ o : Vec, FutureUnit o ∧
      gamma I.u I.N = 5/3 ∧ betaSq I.u I.N = 16/25 ∧
      gamma I.u o = 1 ∧ betaSq I.u o = 0 ∧ gamma I.u o ≠ gamma I.u I.N
```
(`o` is the coordinate time axis and also a valid physical observer: neither the
coordinate tilt nor u/o tilt may replace the orbit-normal u/N tilt.)

## T3 passive common coordinate change vs physical observer replacement

```lean
structure TiltConfig (V : Type) [AddCommGroup V] [Module ℝ V] where
  g : V →ₗ[ℝ] V →ₗ[ℝ] ℝ
  u : V
  N : V
def tilt (c : TiltConfig V) : ℝ := -(c.g c.u c.N)
def passiveChange (L : V ≃ₗ[ℝ] V) (c : TiltConfig V) : TiltConfig V :=
  ⟨c.g.compl₁₂ L.symm.toLinearMap L.symm.toLinearMap, L c.u, L c.N⟩
def observerReplacement (u' : V) (c : TiltConfig V) : TiltConfig V := ⟨c.g, u', c.N⟩
theorem passive_tilt_invariant (L : V ≃ₗ[ℝ] V) (c : TiltConfig V) :
    tilt (passiveChange L c) = tilt c
theorem tensor_tilt_invariant_C04 (L : V ≃ₗ[ℝ] V) (T : CAS17C04.Tensor V 0 2) (u N : V) :
    -(CAS17C04.tensorChange L T (pairArgs (L u) (L N))) = -(T (pairArgs u N))
theorem gamma_eq_tilt (u N : Vec) :
    gamma u N = tilt ⟨minkowskiBilin, toFin u, toFin N⟩
theorem observer_replacement_changes_tilt :
    ∃ (c : TiltConfig (Fin 4 → ℝ)) (u' : Fin 4 → ℝ),
      c.g = minkowskiBilin ∧ CAS17C04.minkowski c.u c.u = -1 ∧ 0 < c.u 0 ∧
      CAS17C04.minkowski u' u' = -1 ∧ 0 < u' 0 ∧
      tilt (observerReplacement u' c) ≠ tilt c
theorem observer_replacement_not_passive :
    ∃ (c : TiltConfig (Fin 4 → ℝ)) (u' : Fin 4 → ℝ),
      ∀ L : (Fin 4 → ℝ) ≃ₗ[ℝ] (Fin 4 → ℝ), passiveChange L c ≠ observerReplacement u' c
```
Universal over V, L (arbitrary invertible, not only Lorentz), g, u, N. The "not in
general" clause is an existential counterexample, not a universal non-invariance.

## T4 AB-T6 operational witness (not a theorem identity)

```lean
inductive SupplyStatus | supplied | notSupplied
structure OperationalWitness where abT6Calibration : SupplyStatus
def g17dOperationalWitness : OperationalWitness := ⟨.notSupplied⟩   -- recorded actual status
structure G17DApplication where
  input : IndependentOrbitInput
  ops : OperationalWitness
```
No theorem asserts calibration availability or uses it as a hypothesis. The recorded
value is data (`NOT_SUPPLIED`), reported in AUTHOR_RETURN.json as an operational field.

## Not claimed
Orbit/Bianchi identification of X_i, domain (field-level) statements beyond one event,
uniqueness of the future normal among all unit vectors orthogonal to X_i, C02/C03,
calibration availability, four-axis adjudication, scientific admission.
