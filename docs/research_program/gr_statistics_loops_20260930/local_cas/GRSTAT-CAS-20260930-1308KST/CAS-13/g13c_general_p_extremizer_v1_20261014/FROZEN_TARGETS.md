# G13-C frozen targets (written before any proof compile)

Only receipts 01–03 (unchanged-import compiles of C04, G13-A, G13-B) and 04 (API probe
`raw/probes/p01_api.lean`: `#check` of Mathlib/G13-B names and elaboration of the two definitions
`wronskian`, `powerSystem`; no theorem) precede this file.

Module `G13CGeneralPExtremizer`, `import G13BBoundaryMinimax` (unchanged; transitively G13-A and C04
unchanged). Namespace `CAS13G13C`; `open MeasureTheory Set CAS13MeasureComposition CAS13G13B`.
Imported definitions used verbatim: `NEFibre`, `rmoment` (`∫ x, x ^ p ∂μ`, `Real.rpow`), `LowerNode`,
`UpperNode`, `lowerEnd`, `upperEnd`, `chord`, `ClosedRegion`, `energyLower`, `energyUpper`, `SharpInterval`,
`FibreMinimax` (G13-B); `StrictInterior`, `positiveCubeRoot`, `lowerWeight`, `upperWeight`, `chordWeight`
(G13-A `CAS13C02`); `hermite`, `twoDirac`, `moment` (G13-A `CAS13MeasureComposition`); `grstatTau`,
`grstatEps` (C04). In every statement `x ^ p` with `p : ℝ` is `Real.rpow`; `x ^ 3`, `x ^ 4` are `Monoid.npow`.

## Definitions (frozen)

```lean
/-- Wronskian of `n` real functions: det of `(deriv^[i] (f j) y)`. -/
def wronskian {n : ℕ} (f : Fin n → ℝ → ℝ) (y : ℝ) : ℝ :=
  (Matrix.of fun i j : Fin n => deriv^[(i : ℕ)] (f j) y).det
/-- The moment system {1, y³, y⁴, y^p}. -/
def powerSystem (p : ℝ) : Fin 4 → ℝ → ℝ :=
  ![fun _ => 1, fun x => x ^ 3, fun x => x ^ 4, fun x => x ^ p]
/-- Reduced derivative factor of the residual `y^p − (c0 + c3 y³ + c4 y⁴)`. -/
def reducedH (p c3 c4 y : ℝ) : ℝ := p * y ^ (p - 3) - 3 * c3 - 4 * c4 * y
/-- Hermite interpolant of `y^p` in span{1,y³,y⁴}: value at simple node `A`, value+slope at double node `U`. -/
def interpDet (A U : ℝ) : ℝ := 3 * (U ^ 4 - A ^ 4) - 4 * U * (U ^ 3 - A ^ 3)
def interpC3 (A U p : ℝ) : ℝ :=
  (p * U ^ (p - 3) * (U ^ 4 - A ^ 4) - 4 * U * (U ^ p - A ^ p)) / interpDet A U
def interpC4 (A U p : ℝ) : ℝ :=
  (3 * (U ^ p - A ^ p) - (U ^ 3 - A ^ 3) * (p * U ^ (p - 3))) / interpDet A U
def interpC0 (A U p : ℝ) : ℝ := A ^ p - interpC3 A U p * A ^ 3 - interpC4 A U p * A ^ 4
def interp (A U p y : ℝ) : ℝ := hermite (interpC0 A U p) (interpC3 A U p) (interpC4 A U p) y
/-- Exact attained range of the real-exponent moment over a class of measures. -/
def RSharpInterval (F : Set (Measure ℝ)) (p : ℝ) (L U : ℝ) : Prop :=
  (∀ μ ∈ F, L ≤ rmoment μ p ∧ rmoment μ p ≤ U) ∧
  (∃ μ ∈ F, rmoment μ p = L) ∧ (∃ μ ∈ F, rmoment μ p = U) ∧
  (fun μ => rmoment μ p) '' F = Icc L U
/-- C04 relative minimax lifted to a class of measures, real exponent. -/
def RFibreMinimax (F : Set (Measure ℝ)) (p : ℝ) (L U : ℝ) : Prop :=
  (∀ μ ∈ F, |(grstatTau L U - rmoment μ p) / rmoment μ p| ≤ grstatEps L U) ∧
  (∃ μ ∈ F, |(grstatTau L U - rmoment μ p) / rmoment μ p| = grstatEps L U) ∧
  (∀ t : ℝ, ∃ μ ∈ F, grstatEps L U ≤ |(t - rmoment μ p) / rmoment μ p|)
```

## T1 — real power smoothness and Wronskian-sequence positivity (lean_step 1)

```lean
theorem wronskian_one (y : ℝ) : wronskian ![fun _ : ℝ => (1 : ℝ)] y = 1
theorem wronskian_two (y : ℝ) : wronskian ![fun _ : ℝ => (1 : ℝ), fun x : ℝ => x ^ 3] y = 3 * y ^ 2
theorem wronskian_three (y : ℝ) :
    wronskian ![fun _ : ℝ => (1 : ℝ), fun x : ℝ => x ^ 3, fun x : ℝ => x ^ 4] y = 12 * y ^ 4
theorem wronskian_power_system (p : ℝ) {y : ℝ} (hy : 0 < y) :
    wronskian (powerSystem p) y = 12 * p * (p - 3) * (p - 4) * y ^ (p + 1)
theorem wronskian_chain_pos {p y : ℝ} (hp : 4 < p) (hy : 0 < y) :
    0 < wronskian ![fun _ : ℝ => (1 : ℝ)] y ∧
    0 < wronskian ![fun _ : ℝ => (1 : ℝ), fun x : ℝ => x ^ 3] y ∧
    0 < wronskian ![fun _ : ℝ => (1 : ℝ), fun x : ℝ => x ^ 3, fun x : ℝ => x ^ 4] y ∧
    0 < wronskian (powerSystem p) y
theorem reduced_deriv2_wronskian (p : ℝ) {y : ℝ} (hy : 0 < y) :
    deriv^[2] (fun x : ℝ => p * x ^ (p - 3)) y * (12 * y ^ 6) = wronskian (powerSystem p) y
theorem reduced_convex_of_wronskian_pos {p : ℝ}
    (hW : ∀ y : ℝ, 0 < y → 0 < wronskian (powerSystem p) y) :
    StrictConvexOn ℝ (Ioi 0) (fun x : ℝ => p * x ^ (p - 3))
theorem residual_hasDerivAt (p c0 c3 c4 : ℝ) {y : ℝ} (hy : 0 < y) :
    HasDerivAt (fun x : ℝ => x ^ p - hermite c0 c3 c4 x) (y ^ 2 * reducedH p c3 c4 y) y
```

## T2 — generalized Rolle / Hermite-remainder sign under the analytic hypothesis (lean_step 2)

The hypothesis `hφ` is the conclusion of `reduced_convex_of_wronskian_pos`; T2 holds for every real p
satisfying it (no `4 < p` used).

```lean
theorem interp_conditions {A U : ℝ} (hA : 0 < A) (hU : 0 < U) (hAU : A ≠ U) (p : ℝ) :
    interp A U p A = A ^ p ∧ interp A U p U = U ^ p ∧
    reducedH p (interpC3 A U p) (interpC4 A U p) U = 0
theorem interp_slope {A U : ℝ} (hA : 0 < A) (hU : 0 < U) (hAU : A ≠ U) (p : ℝ) :
    HasDerivAt (interp A U p) (p * U ^ (p - 1)) U
theorem minorant_of_reduced_convex {p a u : ℝ}
    (hφ : StrictConvexOn ℝ (Ioi 0) (fun x : ℝ => p * x ^ (p - 3)))
    (ha : 0 < a) (hau : a < u) : ∀ y : ℝ, a ≤ y → interp a u p y ≤ y ^ p
theorem majorant_of_reduced_convex {p d b : ℝ}
    (hφ : StrictConvexOn ℝ (Ioi 0) (fun x : ℝ => p * x ^ (p - 3)))
    (hd : 0 < d) (hdb : d < b) : ∀ y : ℝ, 0 < y → y ≤ b → y ^ p ≤ interp b d p y
```

## T3 — support-wide interpolant signs for every real p > 4 (lean_step 3)

`reduced_convex` must be proved through `reduced_convex_of_wronskian_pos` and `wronskian_chain_pos`
(the Wronskian route), so that the chain Wronskian > 0 ⇒ sign ⇒ moment bound is explicit.

```lean
theorem reduced_convex {p : ℝ} (hp : 4 < p) :
    StrictConvexOn ℝ (Ioi 0) (fun x : ℝ => p * x ^ (p - 3))
theorem lower_interp_minorant {p a u : ℝ} (hp : 4 < p) (ha : 0 < a) (hau : a < u) :
    ∀ y : ℝ, a ≤ y → interp a u p y ≤ y ^ p
theorem upper_interp_majorant {p d b : ℝ} (hp : 4 < p) (hd : 0 < d) (hdb : d < b) :
    ∀ y : ℝ, 0 < y → y ≤ b → y ^ p ≤ interp b d p y
```

## T4 — global extremality and attainment by actual measure integration (lean_step 4)

```lean
theorem interior_real_bounds {a b m3 m4 p u d : ℝ} (h : CAS13C02.StrictInterior a b m3 m4)
    (hp : 4 < p) (hu : LowerNode a b m3 m4 u) (hd : UpperNode a b m3 m4 d)
    {μ : Measure ℝ} (hμ : μ ∈ NEFibre a b m3 m4) :
    lowerEnd a m3 u p ≤ rmoment μ p ∧ rmoment μ p ≤ upperEnd b m3 d p
theorem interior_real_sharp {a b m3 m4 p u d : ℝ} (h : CAS13C02.StrictInterior a b m3 m4)
    (hp : 4 < p) (hu : LowerNode a b m3 m4 u) (hd : UpperNode a b m3 m4 d) :
    0 < lowerEnd a m3 u p ∧ lowerEnd a m3 u p ≤ upperEnd b m3 d p ∧
    twoDirac (CAS13C02.lowerWeight a m3 u) a u ∈ NEFibre a b m3 m4 ∧
    rmoment (twoDirac (CAS13C02.lowerWeight a m3 u) a u) p = lowerEnd a m3 u p ∧
    twoDirac (CAS13C02.upperWeight b m3 d) d b ∈ NEFibre a b m3 m4 ∧
    rmoment (twoDirac (CAS13C02.upperWeight b m3 d) d b) p = upperEnd b m3 d p ∧
    RSharpInterval (NEFibre a b m3 m4) p (lowerEnd a m3 u p) (upperEnd b m3 d p)
```

## T5 — boundary and minimax extended to all real p (lean_step 5)

```lean
theorem rfibreMinimax_of_rsharpInterval {F : Set (Measure ℝ)} {p L U : ℝ}
    (hL : 0 < L) (hLU : L ≤ U) (hS : RSharpInterval F p L U) : RFibreMinimax F p L U
theorem interior_real_sharp_minimax {a b m3 m4 p u d : ℝ} (h : CAS13C02.StrictInterior a b m3 m4)
    (hp : 4 < p) (hu : LowerNode a b m3 m4 u) (hd : UpperNode a b m3 m4 d) :
    RSharpInterval (NEFibre a b m3 m4) p (lowerEnd a m3 u p) (upperEnd b m3 d p) ∧
    RFibreMinimax (NEFibre a b m3 m4) p (lowerEnd a m3 u p) (upperEnd b m3 d p)
theorem interior_real_exists {a b m3 m4 p : ℝ} (h : CAS13C02.StrictInterior a b m3 m4)
    (hp : 4 < p) :
    ∃ u d : ℝ, LowerNode a b m3 m4 u ∧ UpperNode a b m3 m4 d ∧
      (∀ u' : ℝ, LowerNode a b m3 m4 u' → u' = u) ∧ (∀ d' : ℝ, UpperNode a b m3 m4 d' → d' = d) ∧
      RSharpInterval (NEFibre a b m3 m4) p (lowerEnd a m3 u p) (upperEnd b m3 d p) ∧
      RFibreMinimax (NEFibre a b m3 m4) p (lowerEnd a m3 u p) (upperEnd b m3 d p)
theorem interior_real_nesting {a b m3 m4 p u d : ℝ} (h : CAS13C02.StrictInterior a b m3 m4)
    (hp : 4 < p) (hu : LowerNode a b m3 m4 u) (hd : UpperNode a b m3 m4 d) :
    energyLower m4 p < lowerEnd a m3 u p ∧ lowerEnd a m3 u p ≤ upperEnd b m3 d p ∧
    upperEnd b m3 d p < energyUpper a b m4 p ∧
    Icc (lowerEnd a m3 u p) (upperEnd b m3 d p) ⊆ Icc (energyLower m4 p) (energyUpper a b m4 p)
theorem interior_sharp_nat {a b m3 m4 u d : ℝ} (h : CAS13C02.StrictInterior a b m3 m4)
    (p : ℕ) (hp : 4 < p) (hu : LowerNode a b m3 m4 u) (hd : UpperNode a b m3 m4 d) :
    SharpInterval (NEFibre a b m3 m4) p (lowerEnd a m3 u p) (upperEnd b m3 d p) ∧
    FibreMinimax (NEFibre a b m3 m4) p (lowerEnd a m3 u p) (upperEnd b m3 d p)
theorem lower_boundary_rsharp {a b m3 m4 : ℝ} (ha : 0 < a) (hab : a < b)
    (h3 : a ^ 3 ≤ m3) (h3' : m3 ≤ b ^ 3) (hbd : m4 = m3 ^ ((4 : ℝ) / 3)) (p : ℝ) :
    RSharpInterval (NEFibre a b m3 m4) p
      (CAS13C02.positiveCubeRoot m3 ^ p) (CAS13C02.positiveCubeRoot m3 ^ p) ∧
    RFibreMinimax (NEFibre a b m3 m4) p
      (CAS13C02.positiveCubeRoot m3 ^ p) (CAS13C02.positiveCubeRoot m3 ^ p) ∧
    grstatEps (CAS13C02.positiveCubeRoot m3 ^ p) (CAS13C02.positiveCubeRoot m3 ^ p) = 0
theorem upper_boundary_rsharp {a b m3 m4 : ℝ} (ha : 0 < a) (hab : a < b)
    (h3 : a ^ 3 ≤ m3) (h3' : m3 ≤ b ^ 3) (hbd : m4 = chord a b m3) (p : ℝ) :
    RSharpInterval (NEFibre a b m3 m4) p
      ((1 - CAS13C02.chordWeight a b m3) * a ^ p + CAS13C02.chordWeight a b m3 * b ^ p)
      ((1 - CAS13C02.chordWeight a b m3) * a ^ p + CAS13C02.chordWeight a b m3 * b ^ p) ∧
    RFibreMinimax (NEFibre a b m3 m4) p
      ((1 - CAS13C02.chordWeight a b m3) * a ^ p + CAS13C02.chordWeight a b m3 * b ^ p)
      ((1 - CAS13C02.chordWeight a b m3) * a ^ p + CAS13C02.chordWeight a b m3 * b ^ p) ∧
    grstatEps ((1 - CAS13C02.chordWeight a b m3) * a ^ p + CAS13C02.chordWeight a b m3 * b ^ p)
      ((1 - CAS13C02.chordWeight a b m3) * a ^ p + CAS13C02.chordWeight a b m3 * b ^ p) = 0
theorem closed_region_real_sharp_minimax {a b m3 m4 p : ℝ} (ha : 0 < a) (hab : a < b)
    (hreg : ClosedRegion a b m3 m4) (hp : 4 < p) :
    ∃ L U : ℝ, 0 < L ∧ L ≤ U ∧ RSharpInterval (NEFibre a b m3 m4) p L U ∧
      RFibreMinimax (NEFibre a b m3 m4) p L U ∧
      ((m4 = m3 ^ ((4 : ℝ) / 3) ∨ m4 = chord a b m3) →
        L = U ∧ grstatEps L U = 0 ∧ grstatTau L U = L)
```
Scope notes: the boundary theorems hold for every real p (rigidity; the fibre is a single measure);
the interior theorems need `4 < p`. `interior_sharp_nat` re-derives the G13-B ℕ-form for every natural
p ≥ 5 from the real theorem (consistency with G13-B p = 5, 6; not a substitute for the real statement).

## Negative controls / non-vacuity witnesses

```lean
theorem wronskian_negative_exponent {y : ℝ} (hy : 0 < y) : wronskian (powerSystem (-1)) y < 0
theorem minorant_fails_negative_exponent :
    (3 / 2 : ℝ) ^ (-1 : ℝ) < interp 1 2 (-1) (3 / 2)      -- N1: with W<0 the lower-interpolant sign fails
theorem real_witness :
    ∃ u d : ℝ, LowerNode 1 2 (9 / 2) 8 u ∧ UpperNode 1 2 (9 / 2) 8 d ∧
      RSharpInterval (NEFibre 1 2 (9 / 2) 8) (9 / 2)
        (lowerEnd 1 (9 / 2) u (9 / 2)) (upperEnd 2 (9 / 2) d (9 / 2)) ∧
      RFibreMinimax (NEFibre 1 2 (9 / 2) 8) (9 / 2)
        (lowerEnd 1 (9 / 2) u (9 / 2)) (upperEnd 2 (9 / 2) d (9 / 2))   -- N2: non-integer p, interior data
```
N1 shows the analytic hypothesis is not vacuous: for p = −1 (W = −240 < 0) the interpolant at nodes
1 (simple), 2 (double) exceeds y^p at y = 3/2 (exact values 2059/2816 vs 2/3). N2 instantiates the
interior theorem at the G13-B strict-interior witness (a,b,m3,m4) = (1,2,9/2,8) with p = 9/2 ∉ ℕ.

## Explicitly not targeted

Uniqueness of extremal measures; strict non-degeneracy L_p < U_p; the reversed/other-sign regimes
p ≤ 4 as theorems; weak-limit continuity toward the boundary; statistics-factor maps; bandpass kernels
(G13-D); scientific admission.
