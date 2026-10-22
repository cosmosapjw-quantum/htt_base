# G01-B frozen targets (written before any proof compile)

Module `G01BTimelikeFlow` (file `lean/G01BTimelikeFlow.lean`), namespace `G01BTimelikeFlow`,
importing `Mathlib` and `CAS01C04Accepted` (byte copy of the accepted C01-C04 source,
SHA-256 `a24b3499...72e9b7`). Imported names are written with prefix `GRSTATCAS01.`.
Toolchain Lean 4.31.0, Mathlib `fabf563a7c95a166b8d7b6efca11c8b4dc9d911f`.

Scope: **chart level** (the source proof's own normal-coordinate chart, OPTICAL_THEOREMS.md:149).
Quantifiers below are the source's: every admissible pair, every fibre element `W`, every smooth
chart metric with the normal-coordinate facts at the origin, every continuous time orientation
matched to the observer at the origin. Neighbourhood and flow interval are **existential and
depend on all data** (no uniform radius). The flow is **local** (no completeness).

## Definitions (frozen)

```lean
abbrev V := GRSTATCAS01.V          -- Fin 4 → ℝ
abbrev Form := GRSTATCAS01.Form    -- Fin 4 → Fin 4 → ℝ
def eta : Form := fun i j => if i = j then GRSTATCAS01.eps i else 0

structure NormalChartMetric (G : V → Form) (n : WithTop ℕ∞) : Prop where
  contDiff : ContDiff ℝ n G
  symm : ∀ x i j, G x i j = G x j i
  origin : G 0 = eta
  hasFDerivAt_origin : HasFDerivAt G (0 : V →L[ℝ] Form) 0

-- affine candidate v of Eq. (17) is the accepted C04 `GRSTATCAS01.fullSeed u Q c`
noncomputable def normSq (G : V → Form) (u : V) (Q : Form) (c : ℝ) (x : V) : ℝ :=
  -GRSTATCAS01.eval (G x) (GRSTATCAS01.fullSeed u Q c x) (GRSTATCAS01.fullSeed u Q c x)
noncomputable def unitField (G : V → Form) (u : V) (Q : Form) (c : ℝ) (x : V) : V :=
  fun b => GRSTATCAS01.fullSeed u Q c x b / Real.sqrt (normSq G u Q c x)
noncomputable def physField (G : V → Form) (u : V) (Q : Form) (c : ℝ) (x : V) : V :=
  fun b => c * unitField G u Q c x b
def timelikeFutureSet (G : V → Form) (T : V → V) (u : V) (Q : Form) (c : ℝ) : Set V :=
  {x | GRSTATCAS01.eval (G x) (GRSTATCAS01.fullSeed u Q c x) (GRSTATCAS01.fullSeed u Q c x) < 0 ∧
       GRSTATCAS01.eval (G x) (GRSTATCAS01.fullSeed u Q c x) (T x) < 0}

noncomputable def partialD (f : V → ℝ) (x : V) (a : Fin 4) : ℝ := fderiv ℝ f x (Pi.single a 1)
noncomputable def christoffel1 (G : V → Form) (x : V) (e a b : Fin 4) : ℝ :=
  (partialD (fun y => G y e b) x a + partialD (fun y => G y e a) x b
    - partialD (fun y => G y a b) x e) / 2
def lower (G : V → Form) (U : V → V) (x : V) (b : Fin 4) : ℝ := ∑ c, G x b c * U x c
noncomputable def covDerivLower (G : V → Form) (U : V → V) (x : V) (a b : Fin 4) : ℝ :=
  partialD (fun y => lower G U y b) x a - ∑ e, christoffel1 G x e a b * U x e

noncomputable def opticalZ (G : V → Form) (u : V → V) (x y z : ℝ) : ℝ :=
  GRSTATCAS01.eval (G 0) (u 0) (GRSTATCAS01.K x y z)
noncomputable def opticalH (G : V → Form) (U : V → V) (x y z : ℝ) : ℝ :=
  GRSTATCAS01.eval (GRSTATCAS01.symPart (fun a b => covDerivLower G U 0 a b))
    (GRSTATCAS01.K x y z) (GRSTATCAS01.K x y z)
```

## Targets

| ID | Lean name | Exact statement (hypotheses → conclusion) |
|---|---|---|
| T1 | `timelikeFutureSet_isOpen` | `(hG : Continuous G) (hT : Continuous T) : IsOpen (timelikeFutureSet G T u Q c)` |
| T2 | `origin_mem_timelikeFutureSet` | `(hG0 : G 0 = eta) (hT0 : T 0 = GRSTATCAS01.rest) (hu : GRSTATCAS01.g u u = -1) (hfut : 0 < u 0) : (0 : V) ∈ timelikeFutureSet G T u Q c` |
| T3 | `exists_ball_subset_timelikeFutureSet` | T1+T2 hypotheses `: ∃ ε > 0, Metric.ball (0 : V) ε ⊆ timelikeFutureSet G T u Q c` (pointwise inequality persists on an actual positive-radius ball; ε depends on all data) |
| T4 | `unitField_contDiffOn`, `physField_contDiffOn` | `{n : WithTop ℕ∞} (hG : ContDiff ℝ n G) : ContDiffOn ℝ n (unitField G u Q c) (timelikeFutureSet G T u Q c)`; same for `physField` (positive-root normalization genuinely `C^n` on the set; `n = ⊤` is smooth) |
| T5 | `unitField_unit` | `x ∈ timelikeFutureSet G T u Q c → GRSTATCAS01.eval (G x) (unitField G u Q c x) (unitField G u Q c x) = -1` |
| T6 | `unitField_future` | `x ∈ timelikeFutureSet G T u Q c → GRSTATCAS01.eval (G x) (unitField G u Q c x) (T x) < 0` |
| T7 | `unitField_origin` | `(hG0 : G 0 = eta) (hu : GRSTATCAS01.g u u = -1) : unitField G u Q c 0 = u` |
| T8 | `unitField_coordinate_jet` | `(hG0 : G 0 = eta) (hG' : HasFDerivAt G (0 : V →L[ℝ] Form) 0) (hu : GRSTATCAS01.g u u = -1) (hQ : ∀ k, GRSTATCAS01.cov Q u k = 0) : ∀ k b, HasDerivAt (fun t => unitField G u Q c (GRSTATCAS01.coordinateLine k t) b) (GRSTATCAS01.eps b * Q k b / c) 0` (general curved chart; same form as C04) |
| T9 | `jet_agrees_with_C04` | T8 hypotheses `: unitField G u Q c 0 = GRSTATCAS01.fullNormalized u Q c (fun _ => 0) ∧ ∀ k b, ∃ d, HasDerivAt (fun t => unitField G u Q c (GRSTATCAS01.coordinateLine k t) b) d 0 ∧ HasDerivAt (fun t => GRSTATCAS01.fullNormalized u Q c (GRSTATCAS01.coordinateLine k t) b) d 0` (+ `0 < c`); the C04 side is discharged by the imported C04 theorem |
| T10 | `covDeriv_physField_origin` | `{n} (hG : NormalChartMetric G n) (hn : 1 ≤ n) (hc : 0 < c) (hu : GRSTATCAS01.g u u = -1) (hfut : 0 < u 0) (hQ : ∀ k, GRSTATCAS01.cov Q u k = 0) : ∀ a b, covDerivLower G (physField G u Q c) 0 a b = Q a b` (i.e. `∇_a U_b(p) = Q_ab`) |
| T11 | `physField_local_integral_curve` | `{n} (hG : ContDiff ℝ n G) (hn : 1 ≤ n) (hT : Continuous T) : ∀ x0 ∈ timelikeFutureSet G T u Q c, ∃ α : ℝ → V, α 0 = x0 ∧ ∃ ε > 0, ∀ t ∈ Set.Ioo (-ε) ε, HasDerivAt α (physField G u Q c (α t)) t ∧ α t ∈ timelikeFutureSet G T u Q c` |
| T12 | `physField_local_flow` | same hyps `: ∀ x0 ∈ timelikeFutureSet G T u Q c, ∃ α : V → ℝ → V, ∀ᶠ xt in 𝓝 x0 ×ˢ 𝓝 (0:ℝ), α xt.1 0 = xt.1 ∧ HasDerivAt (α xt.1) (physField G u Q c (α xt.1 xt.2)) xt.2` |
| T13 | `physField_integral_curve_unique` | same hyps `: ∀ x0 ∈ timelikeFutureSet G T u Q c, ∀ γ₁ γ₂ : ℝ → V, (∀ᶠ t in 𝓝 0, HasDerivAt γ₁ (physField G u Q c (γ₁ t)) t) → (∀ᶠ t in 𝓝 0, HasDerivAt γ₂ (physField G u Q c (γ₂ t)) t) → γ₁ 0 = x0 → γ₂ 0 = x0 → γ₁ =ᶠ[𝓝 0] γ₂` |
| T14 | `G01B_local_realization` (bundle: SAME field and flow) | `(ζ0 ζ1 ζ2 ζ3 h0 h1x h1y h1z hxx hyy hzz hxy hxz hyz c : ℝ) (W : Form) (G : V → Form) (T : V → V) (n : WithTop ℕ∞) (hshell : ζ0^2 - (ζ1^2 + ζ2^2 + ζ3^2) = 1) (hζ0 : 1 ≤ ζ0) (hSTF : hxx + hyy + hzz = 0) (hc : 0 < c) (hW : GRSTATCAS01.skew W) (hWsp : GRSTATCAS01.spatial W ![ζ0, ζ1, ζ2, ζ3]) (hG : NormalChartMetric G n) (hn : 1 ≤ n) (hT : Continuous T) (hT0 : T 0 = GRSTATCAS01.rest)` → with `u := ![ζ0,ζ1,ζ2,ζ3]`, `S := sourceS h0 h1x h1y h1z hxx hyy hzz hxy hxz hyz`, `Qd := Q (B S u) W u`, `N := timelikeFutureSet G T u Qd c`: `IsOpen N ∧ 0 ∈ N ∧ (∃ ε > 0, ball 0 ε ⊆ N) ∧ ContDiffOn ℝ n (unitField G u Qd c) N ∧ ContDiffOn ℝ n (physField G u Qd c) N ∧ (∀ x ∈ N, eval (G x) (unitField..x) (unitField..x) = -1 ∧ eval (G x) (unitField..x) (T x) < 0) ∧ unitField G u Qd c 0 = u ∧ (∀ k b, HasDerivAt (fun t => unitField G u Qd c (coordinateLine k t) b) (eps b * Qd k b / c) 0) ∧ (∀ a b, covDerivLower G (physField G u Qd c) 0 a b = Qd a b) ∧ (∀ x0 ∈ N, ∃ α : ℝ → V, α 0 = x0 ∧ ∃ ε > 0, ∀ t ∈ Ioo (-ε) ε, HasDerivAt α (physField G u Qd c (α t)) t ∧ α t ∈ N) ∧ (∀ x y z, x*x+y*y+z*z = 1 → opticalZ G (unitField G u Qd c) x y z = ζ0 + ζ1*x + ζ2*y + ζ3*z ∧ opticalH G (physField G u Qd c) x y z = h0 + h1x*x + h1y*y + h1z*z + (hxx*x*x + hyy*y*y + hzz*z*z + 2*hxy*x*y + 2*hxz*x*z + 2*hyz*y*z))` |

## Controls

| ID | Lean name | Statement / role |
|---|---|---|
| N1 | `minkowski_normalChartMetric` | `∀ n, NormalChartMetric (fun _ => eta) n` — non-vacuity witness: hypotheses of T10/T14 are satisfiable |
| N2 | `minkowski_unitField_eq_C04` | `unitField (fun _ => eta) u Q c = GRSTATCAS01.fullNormalized u Q c` — in flat chart the constructed field is literally the accepted C04 field |
| N3 | `no_uniform_radius` | `(c : ℝ) (hc : 0 < c) (T : V → V) : ∀ r > 0, ∃ lam > 0, ¬ (Metric.ball (0:V) r ⊆ timelikeFutureSet (fun _ => eta) T GRSTATCAS01.rest (GRSTATCAS01.Q (GRSTATCAS01.B (GRSTATCAS01.sourceS (lam/3) 0 0 0 (2*lam/3) (-lam/3) (-lam/3) 0 0 0) GRSTATCAS01.rest) (fun _ _ => 0) GRSTATCAS01.rest) c)` — negative control: inside T14's own admissible family (ζ=(1,0,0,0), STF data, W=0, Minkowski chart) no radius works for all members |

## Not targeted (residuals)

R1 existence of normal coordinates matched to the observer tetrad on a Lorentzian manifold;
R2 identification of the chart Christoffel formula with the manifold Levi-Civita connection and of
`T` with a global time orientation; R3 the optical identity (2)=(4) (null geodesics, vertex
Jacobi normalization — G01-A R1/R2); R4 uniform radius, finite-distance remainder, global flow or
completeness (explicitly excluded by the source, OPTICAL_THEOREMS.md:156); R5 Einstein/material
realization. Scientific admission: HOLD.
