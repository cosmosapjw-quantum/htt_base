# G13-B frozen targets (written before any proof compile)

Frozen by this author (fresh start: no interrupted-attempt FROZEN_TARGETS.md existed; see
SOURCE_RECOVERY.md). Only the import-compile receipts 01–02 and API-probe 03 (`#check` only, no
proof of a target) precede this file. Module `G13BBoundaryMinimax`, namespace `CAS13G13B`,
`import MeasureExtremizerBridge` (G13-A, unchanged) and `import Main` (C04, unchanged);
`open MeasureTheory Set CAS13MeasureComposition`. `moment μ p = ∫ x, x ^ p ∂μ` (p : ℕ) and
`twoDirac w v z = ofReal(1-w)•δ_v + ofReal w•δ_z` are the G13-A definitions.

## Definitions (frozen)

```lean
def chord (a b m3 : ℝ) : ℝ := a ^ 4 + (m3 - a ^ 3) * (b ^ 4 - a ^ 4) / (b ^ 3 - a ^ 3)
def ClosedRegion (a b m3 m4 : ℝ) : Prop :=
  a ^ 3 ≤ m3 ∧ m3 ≤ b ^ 3 ∧ m3 ^ ((4 : ℝ) / 3) ≤ m4 ∧ m4 ≤ chord a b m3
def NEFibre (a b m3 m4 : ℝ) : Set (Measure ℝ) :=
  {μ | IsProbabilityMeasure μ ∧ (∀ᵐ x ∂μ, x ∈ Icc a b) ∧ moment μ 3 = m3 ∧ moment μ 4 = m4}
def EFibre (a b m4 : ℝ) : Set (Measure ℝ) :=
  {μ | IsProbabilityMeasure μ ∧ (∀ᵐ x ∂μ, x ∈ Icc a b) ∧ moment μ 4 = m4}
def rmoment (μ : Measure ℝ) (p : ℝ) : ℝ := ∫ x, x ^ p ∂μ            -- Real.rpow
def energyLower (m4 p : ℝ) : ℝ := m4 ^ (p / 4)                       -- S126
def energyUpper (a b m4 p : ℝ) : ℝ :=
  ((b ^ 4 - m4) * a ^ p + (m4 - a ^ 4) * b ^ p) / (b ^ 4 - a ^ 4)   -- S126
def energyWeight (a b m4 : ℝ) : ℝ := (m4 - a ^ 4) / (b ^ 4 - a ^ 4)
def LowerNode (a b m3 m4 u : ℝ) : Prop :=
  CAS13C02.positiveCubeRoot m3 < u ∧ u < b ∧
    (u ^ 4 - a ^ 4) / (u ^ 3 - a ^ 3) = (m4 - a ^ 4) / (m3 - a ^ 3)          -- S122
def UpperNode (a b m3 m4 d : ℝ) : Prop :=
  a < d ∧ d < CAS13C02.positiveCubeRoot m3 ∧
    (b ^ 4 - d ^ 4) / (b ^ 3 - d ^ 3) = (b ^ 4 - m4) / (b ^ 3 - m3)          -- S122
def lowerEnd (a m3 u p : ℝ) : ℝ :=
  (1 - CAS13C02.lowerWeight a m3 u) * a ^ p + CAS13C02.lowerWeight a m3 u * u ^ p   -- S124 L_p
def upperEnd (b m3 d p : ℝ) : ℝ :=
  (1 - CAS13C02.upperWeight b m3 d) * d ^ p + CAS13C02.upperWeight b m3 d * b ^ p   -- S124 U_p
def SharpInterval (F : Set (Measure ℝ)) (p : ℕ) (L U : ℝ) : Prop :=
  (∀ μ ∈ F, L ≤ moment μ p ∧ moment μ p ≤ U) ∧
  (∃ μ ∈ F, moment μ p = L) ∧ (∃ μ ∈ F, moment μ p = U) ∧
  (fun μ => moment μ p) '' F = Icc L U
def FibreMinimax (F : Set (Measure ℝ)) (p : ℕ) (L U : ℝ) : Prop :=
  (∀ μ ∈ F, |(grstatTau L U - moment μ p) / moment μ p| ≤ grstatEps L U) ∧
  (∃ μ ∈ F, |(grstatTau L U - moment μ p) / moment μ p| = grstatEps L U) ∧
  (∀ t : ℝ, ∃ μ ∈ F, grstatEps L U ≤ |(t - moment μ p) / moment μ p|)
```

No fibre carries integrability hypotheses: integrability of every continuous function is derived from
the probability + support conditions (helper `admissible_of_mem` proves G13-A's `Admissible`).

## T1 — feasible region and its boundary strata (lean_step 1)

```lean
theorem region_necessary {a b m3 m4 : ℝ} (ha : 0 < a) (hab : a < b) {μ : Measure ℝ}
    (hμ : μ ∈ NEFibre a b m3 m4) : ClosedRegion a b m3 m4
theorem region_exact {a b : ℝ} (ha : 0 < a) (hab : a < b) (m3 m4 : ℝ) :
    (NEFibre a b m3 m4).Nonempty ↔ ClosedRegion a b m3 m4
theorem region_strata {a b m3 m4 : ℝ} (ha : 0 < a) (hab : a < b) (h : ClosedRegion a b m3 m4) :
    CAS13C02.StrictInterior a b m3 m4 ∨ m4 = m3 ^ ((4 : ℝ) / 3) ∨ m4 = chord a b m3
theorem lowerCurve_lt_chord {a b m3 : ℝ} (ha : 0 < a) (hab : a < b)
    (h3 : a ^ 3 < m3) (h3' : m3 < b ^ 3) : m3 ^ ((4 : ℝ) / 3) < chord a b m3
theorem region_corners {a b : ℝ} (ha : 0 < a) (hab : a < b) :
    (a ^ 3) ^ ((4 : ℝ) / 3) = a ^ 4 ∧ chord a b (a ^ 3) = a ^ 4 ∧
    (b ^ 3) ^ ((4 : ℝ) / 3) = b ^ 4 ∧ chord a b (b ^ 3) = b ^ 4
```

## T2 — boundary Dirac collapse / endpoint collapse and boundary extrema (lean_step 2, direct rigidity)

```lean
theorem lower_boundary_dirac_collapse {a b m3 m4 : ℝ} (ha : 0 < a) (hab : a < b)
    {μ : Measure ℝ} (hμ : μ ∈ NEFibre a b m3 m4) (hbd : m4 = m3 ^ ((4 : ℝ) / 3)) :
    μ = Measure.dirac (CAS13C02.positiveCubeRoot m3)
theorem upper_boundary_endpoint_collapse {a b m3 m4 : ℝ} (ha : 0 < a) (hab : a < b)
    {μ : Measure ℝ} (hμ : μ ∈ NEFibre a b m3 m4) (hbd : m4 = chord a b m3) :
    μ = twoDirac (CAS13C02.chordWeight a b m3) a b
theorem lower_boundary_sharp {a b m3 m4 : ℝ} (ha : 0 < a) (hab : a < b)
    (h3 : a ^ 3 ≤ m3) (h3' : m3 ≤ b ^ 3) (hbd : m4 = m3 ^ ((4 : ℝ) / 3)) (p : ℕ) :
    Measure.dirac (CAS13C02.positiveCubeRoot m3) ∈ NEFibre a b m3 m4 ∧
    SharpInterval (NEFibre a b m3 m4) p
      (CAS13C02.positiveCubeRoot m3 ^ p) (CAS13C02.positiveCubeRoot m3 ^ p)
theorem upper_boundary_sharp {a b m3 m4 : ℝ} (ha : 0 < a) (hab : a < b)
    (h3 : a ^ 3 ≤ m3) (h3' : m3 ≤ b ^ 3) (hbd : m4 = chord a b m3) (p : ℕ) :
    twoDirac (CAS13C02.chordWeight a b m3) a b ∈ NEFibre a b m3 m4 ∧
    SharpInterval (NEFibre a b m3 m4) p
      ((1 - CAS13C02.chordWeight a b m3) * a ^ p + CAS13C02.chordWeight a b m3 * b ^ p)
      ((1 - CAS13C02.chordWeight a b m3) * a ^ p + CAS13C02.chordWeight a b m3 * b ^ p)
```
Scope note: T2 holds for every p : ℕ because on the boundary the fibre is a single measure (rigidity);
this is not the interior Chebyshev theorem for general p (G13-C).

## T3 — same-prior energy-only interval, real p > 4 (lean_step 3)

```lean
theorem energy_only_bounds {a b m4 p : ℝ} (ha : 0 < a) (hab : a < b) (hp : 4 < p)
    {μ : Measure ℝ} (hμ : μ ∈ EFibre a b m4) :
    energyLower m4 p ≤ rmoment μ p ∧ rmoment μ p ≤ energyUpper a b m4 p
theorem energy_only_attained {a b m4 p : ℝ} (ha : 0 < a) (hab : a < b) (hp : 4 < p)
    (h4 : a ^ 4 ≤ m4) (h4' : m4 ≤ b ^ 4) :
    Measure.dirac (m4 ^ ((1 : ℝ) / 4)) ∈ EFibre a b m4 ∧
    rmoment (Measure.dirac (m4 ^ ((1 : ℝ) / 4))) p = energyLower m4 p ∧
    twoDirac (energyWeight a b m4) a b ∈ EFibre a b m4 ∧
    rmoment (twoDirac (energyWeight a b m4) a b) p = energyUpper a b m4 p
theorem energy_fibre_nonempty_iff {a b : ℝ} (ha : 0 < a) (hab : a < b) (m4 : ℝ) :
    (EFibre a b m4).Nonempty ↔ a ^ 4 ≤ m4 ∧ m4 ≤ b ^ 4
```

## T4 — same-prior fibre inclusion and interval nesting (lean_step 4)

```lean
theorem fibre_inclusion (a b m3 m4 : ℝ) : NEFibre a b m3 m4 ⊆ EFibre a b m4
theorem endpoint_strict_nesting {a b m3 m4 p u d : ℝ} (h : CAS13C02.StrictInterior a b m3 m4)
    (hp : 4 < p) (hu : LowerNode a b m3 m4 u) (hd : UpperNode a b m3 m4 d) :
    energyLower m4 p < lowerEnd a m3 u p ∧ upperEnd b m3 d p < energyUpper a b m4 p
theorem interval_nesting_p56 {a b m3 m4 u d : ℝ} (h : CAS13C02.StrictInterior a b m3 m4)
    (p : ℕ) (hp : p = 5 ∨ p = 6) (hu : LowerNode a b m3 m4 u) (hd : UpperNode a b m3 m4 d) :
    energyLower m4 p < lowerEnd a m3 u p ∧ lowerEnd a m3 u p ≤ upperEnd b m3 d p ∧
    upperEnd b m3 d p < energyUpper a b m4 p ∧
    Icc (lowerEnd a m3 u p) (upperEnd b m3 d p) ⊆ Icc (energyLower m4 p) (energyUpper a b m4 p) ∧
    (fun μ => rmoment μ p) '' NEFibre a b m3 m4 ⊆ (fun μ => rmoment μ p) '' EFibre a b m4
```
(`p : ℕ` is cast to ℝ in `lowerEnd/upperEnd/energyLower/energyUpper/rmoment`.)
Scope note: for real p > 4 only the endpoint-value nesting is claimed, not L_p ≤ m_p ≤ U_p.

## T5 — composition with C04 minimax including L = U (lean_step 5)

```lean
theorem minimax_degenerate {L : ℝ} (hL : 0 < L) : grstatEps L L = 0 ∧ grstatTau L L = L
theorem fibreMinimax_of_sharpInterval {F : Set (Measure ℝ)} {p : ℕ} {L U : ℝ}
    (hL : 0 < L) (hLU : L ≤ U) (hS : SharpInterval F p L U) : FibreMinimax F p L U
theorem interior_sharp_minimax {a b m3 m4 u d : ℝ} (h : CAS13C02.StrictInterior a b m3 m4)
    (p : ℕ) (hp : p = 5 ∨ p = 6) (hu : LowerNode a b m3 m4 u) (hd : UpperNode a b m3 m4 d) :
    0 < lowerEnd a m3 u p ∧ lowerEnd a m3 u p ≤ upperEnd b m3 d p ∧
    twoDirac (CAS13C02.lowerWeight a m3 u) a u ∈ NEFibre a b m3 m4 ∧
    moment (twoDirac (CAS13C02.lowerWeight a m3 u) a u) p = lowerEnd a m3 u p ∧
    twoDirac (CAS13C02.upperWeight b m3 d) d b ∈ NEFibre a b m3 m4 ∧
    moment (twoDirac (CAS13C02.upperWeight b m3 d) d b) p = upperEnd b m3 d p ∧
    SharpInterval (NEFibre a b m3 m4) p (lowerEnd a m3 u p) (upperEnd b m3 d p) ∧
    FibreMinimax (NEFibre a b m3 m4) p (lowerEnd a m3 u p) (upperEnd b m3 d p)
theorem lower_boundary_minimax {a b m3 m4 : ℝ} (ha : 0 < a) (hab : a < b)
    (h3 : a ^ 3 ≤ m3) (h3' : m3 ≤ b ^ 3) (hbd : m4 = m3 ^ ((4 : ℝ) / 3)) (p : ℕ) :
    FibreMinimax (NEFibre a b m3 m4) p
      (CAS13C02.positiveCubeRoot m3 ^ p) (CAS13C02.positiveCubeRoot m3 ^ p) ∧
    grstatEps (CAS13C02.positiveCubeRoot m3 ^ p) (CAS13C02.positiveCubeRoot m3 ^ p) = 0
theorem upper_boundary_minimax {a b m3 m4 : ℝ} (ha : 0 < a) (hab : a < b)
    (h3 : a ^ 3 ≤ m3) (h3' : m3 ≤ b ^ 3) (hbd : m4 = chord a b m3) (p : ℕ) :
    FibreMinimax (NEFibre a b m3 m4) p
      ((1 - CAS13C02.chordWeight a b m3) * a ^ p + CAS13C02.chordWeight a b m3 * b ^ p)
      ((1 - CAS13C02.chordWeight a b m3) * a ^ p + CAS13C02.chordWeight a b m3 * b ^ p) ∧
    grstatEps ((1 - CAS13C02.chordWeight a b m3) * a ^ p + CAS13C02.chordWeight a b m3 * b ^ p)
      ((1 - CAS13C02.chordWeight a b m3) * a ^ p + CAS13C02.chordWeight a b m3 * b ^ p) = 0
theorem closed_region_sharp_minimax {a b m3 m4 : ℝ} (ha : 0 < a) (hab : a < b)
    (hreg : ClosedRegion a b m3 m4) (p : ℕ) (hp : p = 5 ∨ p = 6) :
    ∃ L U : ℝ, 0 < L ∧ L ≤ U ∧ SharpInterval (NEFibre a b m3 m4) p L U ∧
      FibreMinimax (NEFibre a b m3 m4) p L U ∧
      ((m4 = m3 ^ ((4 : ℝ) / 3) ∨ m4 = chord a b m3) →
        L = U ∧ grstatEps L U = 0 ∧ grstatTau L U = L)
```

## Negative controls / non-vacuity witnesses

```lean
theorem node_ratio_zero_div_zero {a : ℝ} (ha : 0 < a) :
    (a ^ 4 - a ^ 4) / (a ^ 3 - a ^ 3) = 0 ∧ CAS13C02.secant a a = 4 * a / 3 ∧
    (a ^ 4 - a ^ 4) / (a ^ 3 - a ^ 3) ≠ CAS13C02.secant a a          -- N1: 0/0 is junk, not the limit
theorem cross_prior_nesting_fails :
    twoDirac (1 / 2) 1 2 ∈ NEFibre 1 2 (9 / 2) (17 / 2) ∧
    moment (twoDirac (1 / 2) 1 2) 5 = 33 / 2 ∧
    energyUpper 1 2 (17 / 2) 5 = 33 / 2 ∧
    (EFibre 1 (7 / 4) (17 / 2)).Nonempty ∧
    energyUpper 1 (7 / 4) (17 / 2) 5 < 33 / 2                          -- N2: different support breaks nesting
theorem lowerCurve_lt_iff {m3 m4 : ℝ} (hm3 : 0 < m3) (hm4 : 0 < m4) :
    m3 ^ ((4 : ℝ) / 3) < m4 ↔ m3 ^ 4 < m4 ^ 3                          -- rpow-free form used by N3
theorem strictInterior_witness :
    CAS13C02.StrictInterior 1 2 (9 / 2) 8 ∧ (NEFibre 1 2 (9 / 2) 8).Nonempty   -- N3 interior non-vacuity
theorem boundary_witness :
    ClosedRegion 1 2 (9 / 2) (17 / 2) ∧ (17 / 2 : ℝ) = chord 1 2 (9 / 2) ∧
    ¬ CAS13C02.StrictInterior 1 2 (9 / 2) (17 / 2)                     -- N4 L=U branch is reached
```

## Explicitly not targeted

General real p>4 sharpness of [L_p,U_p] (G13-C); weak-limit continuity of interior principal measures;
statistics-factor maps; bandpass kernels (G13-D); scientific admission.
