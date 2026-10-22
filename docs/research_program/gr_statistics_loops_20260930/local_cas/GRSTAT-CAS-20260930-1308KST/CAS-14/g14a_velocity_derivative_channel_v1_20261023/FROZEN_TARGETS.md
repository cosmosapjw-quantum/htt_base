# G14-A frozen targets (written before any proof compile)

Card: `HTT_ALL_OBLIGATIONS_20261011/tasks/G14-A.json` (parent GR-CAS-14, PLAN-PR-G14).
Scope: type the velocity-derivative observation channel `J(x)=h∇_xU` and its declared
finite-baseline realization (DOSSIER_POSITIVE_BRIDGE.md Eq. (A1)); derive, separately,
the correction terms between (i) the coordinate derivative, (ii) frame/tetrad-spin
component derivatives, (iii) observer-time proper motion, and the covariant `J`;
separate calibration-witnessed terms from external inputs in a typed contract.

Conventions (CAS COMMON_SPEC.md, P03-A): signature `(-,+,+,+)`, `U=c u`, derivative-first
`D_ab=∇_a u_b`, `Γ x c a d = Γ^c_{ad}(x)`, `∇_a U^c = ∂_a U^c + Γ^c_{ad} U^d`
(`PORTCAS03VelocityJetDecomposition.nablaUp`), `h^a_b = δ^a_b + u^a u_b`
(`projUp`).  `J(x)^b = h^b_c x^a ∇_a U^c`.  Positive norms are declared normed-space
norms (never the Lorentz form).  Reused modules are imported UNCHANGED:
`Main` (CAS-14 PR #487 C01-C03, namespace `CAS14`), `VelocityJetDecomposition` (P03-A),
and its imports `VelocityJetRest`, `PortCas01`.

Namespace `G14A`; `Pt := Fin 4 → ℝ`, `Op := Pt →L[ℝ] Pt`, `V3 := Fin 3 → ℝ`.

## Definitions (typed channel)

```lean
def gammaMat (Γ : Pt → Fin 4 → Fin 4 → Fin 4 → ℝ) (p X : Pt) : Matrix (Fin 4) (Fin 4) ℝ :=
  Matrix.of fun c d => ∑ a, X a * Γ p c a d                     -- (Γ_X)^c_d
noncomputable def gammaOp Γ p X : Op := (Matrix.toLin' (gammaMat Γ p X)).toContinuousLinearMap
noncomputable def coordDeriv (U : Pt → Pt) (p X : Pt) : Pt := fun c => ∑ a, X a * pd (fun y => U y c) p a
noncomputable def covDeriv Γ (U : Pt → Pt) (p X : Pt) : Pt := fun c => ∑ a, X a * nablaUp Γ U p a c
noncomputable def Jchan (g : Pt → Matrix (Fin 4) (Fin 4) ℝ) (u : Pt → Pt) Γ (U : Pt → Pt) (p X : Pt) : Pt :=
  projUp (g p) (u p) *ᵥ covDeriv Γ U p X                           -- J(x) = h ∇_x U
noncomputable def spinOf (E0 : Opˣ) (E' : Op) Γ p X : Op := ↑E0⁻¹ * (E' + gammaOp Γ p X * ↑E0)
noncomputable def transportBack (Π : ℝ → Op) (U : Pt → Pt) (q : ℝ → Pt) (s : ℝ) : Pt :=
  Ring.inverse (Π s) (U (q s))                                    -- P_{q_s→p} U(q_s)
noncomputable def finiteBaselineMap g u (Π : ℝ → Op) U (q : ℝ → Pt) (p : Pt) (s : ℝ) : Pt :=
  projUp (g p) (u p) *ᵥ (s⁻¹ • (transportBack Π U q s - U p))     -- Eq. (A1) quotient
structure TransportGerm Γ (p X : Pt) (Π : ℝ → Op) : Prop where
  base : Π 0 = 1
  deriv : HasDerivAt Π (-(gammaOp Γ p X)) 0                       -- parallel-transport ODE at s=0
```
`Π s` is the forward transport `T_p → T_{q_s}` in coordinate components; the TransportGerm
is exactly the parallel-transport equation `dΠ/ds = -Γ(q̇,·)Π` evaluated at `s=0` with
`Π 0 = 1`.  It is an input (transport rule), not the conclusion.

## T1 coordinate-derivative correction (universal; no metric assumption)
```lean
theorem covDeriv_eq_coordDeriv_add (Γ U p X) :
    covDeriv Γ U p X = coordDeriv U p X + gammaMat Γ p X *ᵥ U p
theorem J_sub_coord (g u Γ U p X) :
    Jchan g u Γ U p X - projUp (g p) (u p) *ᵥ coordDeriv U p X
      = projUp (g p) (u p) *ᵥ (gammaMat Γ p X *ᵥ U p)
```
T1-W (non-vacuity / negative control, Levi-Civita): rotating chart of Minkowski space,
`grot Ω`, the inertial congruence `urot Ω y = (1, Ω y², -Ω y¹, 0)`, and `Γrot Ω` (the
Levi-Civita symbols of `grot Ω` at the origin, held constant in the chart):
```lean
theorem rotating_chart_witness (Ω : ℝ) (hΩ : Ω ≠ 0) :
    MetricCompatibleAt (Γrot Ω) (grot Ω) 0 ∧ (∀ c a d, Γrot Ω 0 c a d = Γrot Ω 0 c d a) ∧
    (∀ y, urot Ω y ⬝ᵥ (grot Ω y *ᵥ urot Ω y) = -1) ∧ FieldDiffAt (grot Ω) (urot Ω) 0 ∧
    (∀ X, covDeriv (Γrot Ω) (urot Ω) 0 X = 0) ∧
    coordDeriv (urot Ω) 0 (Pi.single 1 1) = ![0, 0, -Ω, 0] ∧
    coordDeriv (urot Ω) 0 (Pi.single 1 1) ≠ 0
```
(coordinate derivative shows an apparent rotation while `J = 0`.)

## T2 frame-component derivative and tetrad spin (master)
```lean
theorem frame_components_hasDerivAt {Γ U p X} {E : ℝ → Op} {E' : Op} {E0 : Opˣ} {q : ℝ → Pt}
    (hE0 : E 0 = E0) (hE : HasDerivAt E E' 0) (hq0 : q 0 = p) (hq : HasDerivAt q X 0)
    (hU : ∀ c, DifferentiableAt ℝ (fun y => U y c) p) :
    HasDerivAt (fun s => Ring.inverse (E s) (U (q s)))
      (↑E0⁻¹ (covDeriv Γ U p X) - spinOf E0 E' Γ p X (↑E0⁻¹ (U p))) 0
theorem spinOf_parallel (E0 : Opˣ) (h : E' = -(gammaOp Γ p X * ↑E0)) : spinOf E0 E' Γ p X = 0
theorem spinOf_coordinate : spinOf 1 0 Γ p X = gammaOp Γ p X
theorem coordinate_components_hasDerivAt (hq0 hq hU) :
    HasDerivAt (fun s => U (q s)) (coordDeriv U p X) 0
theorem rest_tetrad_spin_correction (hrest : ↑E0⁻¹ (U p) = c • e0) (…same hyps…) :
    HasDerivAt (fun s => Ring.inverse (E s) (U (q s)))
      (↑E0⁻¹ (covDeriv Γ U p X) - c • spinOf E0 E' Γ p X e0) 0
theorem rotation_spin_rest_free (S : Op) (hS : S e0 = 0) (c : ℝ) : S (c • e0) = 0
theorem boost_spin_witness (c) (hc : c ≠ 0) : boostGen (c • e0) = c • e1 ∧ c • e1 ≠ 0
theorem rotation_spin_nonrest_witness (a v) (hv : v ≠ 0) :
    rotGen ![a, v, 0, 0] = ![0, 0, v, 0] ∧ (![0, 0, v, 0] : Pt) ≠ 0
```
(`boostGen`, `rotGen`: `Matrix.toLin'` of the explicit generators `K₁`, `R₃`.)

## T3 finite-baseline channel (A1), remainder and calibration
```lean
theorem finiteBaseline_tendsto_J (hΠ : TransportGerm Γ p X Π) (hq0 : q 0 = p)
    (hq : HasDerivAt q X 0) (hU : ∀ c, DifferentiableAt ℝ (fun y => U y c) p) :
    Tendsto (finiteBaselineMap g u Π U q p) (𝓝[≠] 0) (𝓝 (Jchan g u Γ U p X))
theorem untransported_baseline_bias (hq0 hq hU) :
    Tendsto (finiteBaselineMap g u (fun _ => 1) U q p) (𝓝[≠] 0)
      (𝓝 (Jchan g u Γ U p X - projUp (g p) (u p) *ᵥ (gammaMat Γ p X *ᵥ U p)))
theorem finiteBaseline_remainder {F} [NormedAddCommGroup F] [NormedSpace ℝ F]
    {f f' : ℝ → F} {s M : ℝ} (hs : 0 < s) (hM : 0 ≤ M)
    (hf : ∀ t ∈ Set.Icc 0 s, HasDerivWithinAt f (f' t) (Set.Icc 0 s) t)
    (hlip : ∀ t ∈ Set.Ico 0 s, ‖f' t - f' 0‖ ≤ M * t) :
    ‖s⁻¹ • (f s - f 0) - f' 0‖ ≤ M * s
theorem calibrated_quotient_tendsto (κ ℓ : ℝ) (hℓ : ℓ ≠ 0) {dU : ℝ → Pt} {J : Pt}
    (h : Tendsto (fun s => s⁻¹ • dU s) (𝓝[≠] 0) (𝓝 J)) :
    Tendsto (fun s => (ℓ * s)⁻¹ • (κ • dU s)) (𝓝[≠] 0) (𝓝 ((κ / ℓ) • J))
theorem miscalibration_changes_limit (κ ℓ) (J : Pt) (hJ : J ≠ 0) (h : κ / ℓ ≠ 1) :
    (κ / ℓ) • J ≠ J
```

## T5 observer-time proper motion (declared flat, instantaneous, low-velocity model)
Model: observer at the origin of a local Euclidean frame, source at relative position
`r t`, light-travel time, aberration, curvature and relativistic velocity factors NOT
modelled (they belong to the remainder `e`).  `dirOf r = (√(r⬝r))⁻¹ • r`.
```lean
theorem direction_hasDerivAt {r : ℝ → V3} {r' n : V3} {D : ℝ} (hD : 0 < D) (hn : n ⬝ᵥ n = 1)
    (hr0 : r 0 = D • n) (hr : HasDerivAt r r' 0) :
    HasDerivAt (fun t => dirOf (r t)) (D⁻¹ • CAS14.P n r') 0
theorem frame_drift_hasDerivAt (R : ℝ → (V3 →L[ℝ] V3)) (Ω : V3) (hR0 : R 0 = 1)
    (hR : HasDerivAt R (-(crossOp Ω)) 0) (…as above…) :
    HasDerivAt (fun t => R t (dirOf (r t))) (D⁻¹ • CAS14.P n r' - Ω ⨯₃ n) 0
def jetV (Jm : Matrix (Fin 3) (Fin 3) ℝ) (x : V3) : V3 := fun j => ∑ i, x i * Jm i j
theorem jet_split (Jm x) : jetV Jm x = symJ Jm *ᵥ x + omegaOf Jm ⨯₃ x
theorem proper_motion_decomposition (hD : 0 < D) (hn : n ⬝ᵥ n = 1) (Jm Ω e) :
    D⁻¹ • CAS14.P n (jetV Jm (D • n) + e) - Ω ⨯₃ n
      = CAS14.P n (symJ Jm *ᵥ n) + (omegaOf Jm - Ω) ⨯₃ n + D⁻¹ • CAS14.P n e
theorem expansion_invisible (ℓ : ℝ) (n) (hn : n ⬝ᵥ n = 1) :
    CAS14.P n (jetV (ℓ • 1) n) = 0 ∧ (ℓ ≠ 0 → jetV (ℓ • 1) n ≠ jetV 0 n)
theorem vorticity_frame_degeneracy (Jm n) :
    CAS14.P n (jetV Jm n) - omegaOf Jm ⨯₃ n = CAS14.P n (jetV (symJ Jm) n) - (0 : V3) ⨯₃ n
theorem noncomoving_unbounded (n Δv : V3) (hΔ : CAS14.P n Δv ≠ 0) (C : ℝ) :
    ∃ D > 0, C < (D⁻¹ • CAS14.P n Δv) ⬝ᵥ (D⁻¹ • CAS14.P n Δv)
theorem vorticity_from_axis_drifts (Jm) :
    (1 / 2 : ℝ) • ∑ i : Fin 3, (Pi.single i 1 : V3) ⨯₃ CAS14.P (Pi.single i 1) (jetV Jm (Pi.single i 1))
      = omegaOf Jm
```

## T6 J correspondence to CAS-14 (reuse of PR #487) and 4D→3D bridge
```lean
theorem residual_eq_cas14 (Jm x) : jetV Jm x - symJ Jm *ᵥ x = -CAS14.W (omegaOf Jm) x
theorem cas14_inverse_recovers_jet_vorticity {ι} [Fintype ι] [DecidableEq ι] (w : ι → ℝ) (x : ι → V3)
    (hx : ∀ i, x i ⬝ᵥ x i = 1) (hw : ∀ i, 0 < w i) (i j : ι) (hij : x i ⨯₃ x j ≠ 0) (Jm) :
    (CAS14.G_equiv w x hx hw i j hij).symm
      (CAS14.b w x (fun k => jetV Jm (x k) - symJ Jm *ᵥ x k)) = omegaOf Jm
theorem J_rest_frame (hg : g p = PortCas01.eta) (hu : u p = PortCas01.e0)
    (hd : FieldDiffAt g u p) (hc : MetricCompatibleAt Γ g p) (c : ℝ) (X : Pt) (hX : X 0 = 0) :
    Jchan g u Γ (fun y => c • u y) p X
      = fun b => if b = 0 then 0 else ∑ a, X a * (c * velJetMatrix Γ g u p a b)
```

## T7 typed calibration contract (G17-D OperationalWitness pattern)
```lean
inductive SupplyStatus | supplied | notSupplied
structure G14ASupplyLedger where
  sourceIdentification transportRule tangentDirections baselineLength clockCalibration
  lengthCalibration nonrotatingFrame opticalSymmetricRate finiteBaselineRemainder : SupplyStatus
def g14aSupplyLedger : G14ASupplyLedger      -- every field `.notSupplied` (recorded, not a theorem)
structure CalibratedDerivativeChannel g u Γ U (p X : Pt) where
  Π : ℝ → Op; q : ℝ → Pt; germ : TransportGerm Γ p X Π; q0 : q 0 = p
  qd : HasDerivAt q X 0; reg : ∀ c, DifferentiableAt ℝ (fun y => U y c) p
theorem CalibratedDerivativeChannel.tendsto_J (ch : CalibratedDerivativeChannel g u Γ U p X) :
    Tendsto (finiteBaselineMap g u ch.Π U ch.q p) (𝓝[≠] 0) (𝓝 (Jchan g u Γ U p X))
theorem channel_nonvacuous (c : ℝ) :
    Nonempty (CalibratedDerivativeChannel gMink uEx Γ0 (fun y => c • uEx y) 0 (Pi.single 1 1))
```
(`channel_nonvacuous` is a synthetic consistency witness only, not a supplied observation.)

## T8 zeroth-order / static data negative control
```lean
theorem zeroth_order_insufficient (c : ℝ) (hc : c ≠ 0) :
    (c • uRest 0 = c • uEx 0) ∧
    Jchan gMink uRest Γ0 (fun y => c • uRest y) 0 (Pi.single 1 1) = 0 ∧
    Jchan gMink uEx Γ0 (fun y => c • uEx y) 0 (Pi.single 1 1) = ![0, 3 * c, 0, 0]
theorem zeroth_order_functional_insufficient {α} (Obs : Pt → Pt → α) (c) (hc : c ≠ 0) :
    Obs 0 (c • uRest 0) = Obs 0 (c • uEx 0) ∧
    Jchan gMink uRest Γ0 (fun y => c • uRest y) 0 (Pi.single 1 1)
      ≠ Jchan gMink uEx Γ0 (fun y => c • uEx y) 0 (Pi.single 1 1)
```

## Boundaries (not strengthened, not claimed)
* No hypothesis anywhere states `proper motion = J`; T5 derives the relation in a declared
  model and exhibits the non-identifications.
* TransportGerm is the ODE at `s=0` only; global existence of parallel transport and
  path-independence are not claimed.  The finite-baseline remainder is a separate bound
  requiring an explicit derivative modulus `M`.
* T1-W's `Γrot` is evaluated at the origin only (constant chart extension); no claim is
  made about the connection away from the origin.
* T5 is the flat, instantaneous, non-relativistic proper-motion model; aberration,
  light-time and curvature terms are external remainder inputs.
* The application (an actual calibrated source/transport/length/clock witness) stays OPEN:
  `g14aSupplyLedger` records NOT_SUPPLIED for every field.
* Allowed axioms: propext, Classical.choice, Quot.sound.
